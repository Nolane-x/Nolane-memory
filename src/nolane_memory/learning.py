from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Iterable

from .errors import MemoryDependencyStale, MemoryIdentityCollision, MemoryScopeBlocked, MemoryTransitionIncomplete
from .normalize import canonical_json, digest
from .types import Dependency, TemporalCoverageReceipt


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class LearningMixin:
    """Temporal/procedural learning policies whose outputs remain proof-carrying."""

    def _init_learning_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS temporal_coverage_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL,
              evidence_ids_json TEXT NOT NULL, valid_from TEXT NOT NULL, valid_to TEXT NOT NULL,
              coverage_contract TEXT NOT NULL, principal TEXT NOT NULL,
              dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS procedure_learning_proposals(
              proposal_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, procedure_key TEXT NOT NULL,
              principal TEXT NOT NULL, proposal_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consolidation_policies(
              domain_id TEXT NOT NULL, revision INTEGER NOT NULL,
              policy_json TEXT NOT NULL, created_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,revision)
            );
            CREATE TABLE IF NOT EXISTS consolidation_pressure_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, region_id TEXT NOT NULL,
              policy_revision INTEGER NOT NULL, receipt_json TEXT NOT NULL,
              dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )

    def certify_temporal_coverage(
        self, domain_id: str, evidence_ids: Iterable[str], *, valid_from: datetime,
        valid_to: datetime, principal: str, coverage_contract: str | None,
    ) -> TemporalCoverageReceipt:
        start = valid_from if valid_from.tzinfo else valid_from.replace(tzinfo=timezone.utc)
        end = valid_to if valid_to.tzinfo else valid_to.replace(tzinfo=timezone.utc)
        if end <= start:
            raise MemoryTransitionIncomplete("temporal coverage requires a non-empty half-open interval")
        if not coverage_contract:
            raise MemoryTransitionIncomplete(
                "point observations do not prove continuous duration without an explicit coverage contract"
            )
        ids = sorted(set(evidence_ids))
        if not ids:
            raise MemoryTransitionIncomplete("temporal coverage requires source evidence")
        world_times: list[datetime] = []
        deps: list[Dependency] = []
        for eid in ids:
            row = self.db.execute(
                "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, eid)
            ).fetchone()
            if not row:
                raise KeyError(eid)
            if not self._is_allowed(principal, row["allowed_principals_json"]):
                raise MemoryScopeBlocked("temporal coverage source is inaccessible")
            if row["revoked_seq"] is not None or row["deleted_seq"] is not None or row["compromised_seq"] is not None:
                raise MemoryDependencyStale("temporal coverage source is not live")
            if not row["world_time"]:
                raise MemoryTransitionIncomplete("temporal coverage source lacks world-valid time")
            world_times.append(_parse(row["world_time"]))
            deps.append(Dependency("source", eid, self._generation(domain_id, "source", eid)))
        # The explicit contract supplies the continuity semantics, but the retained
        # observations must at least bracket the declared interval.
        if min(world_times) > start or max(world_times) < end:
            raise MemoryTransitionIncomplete("coverage evidence does not bracket the declared interval")
        now = self._clock(); created_at = _iso(now)
        receipt = TemporalCoverageReceipt(
            receipt_id=f"coverage_{uuid.uuid4().hex}", domain_id=domain_id,
            evidence_ids=ids, valid_from=_iso(start), valid_to=_iso(end),
            coverage_contract=coverage_contract, dependencies=deps, created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO temporal_coverage_receipts(receipt_id,domain_id,evidence_ids_json,valid_from,valid_to,coverage_contract,principal,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (receipt.receipt_id, domain_id, canonical_json(ids), receipt.valid_from, receipt.valid_to,
             coverage_contract, principal, canonical_json([asdict(d) for d in deps]), created_at),
        )
        return receipt

    def validate_temporal_coverage(self, receipt_id: str) -> bool:
        row = self.db.execute(
            "SELECT * FROM temporal_coverage_receipts WHERE receipt_id=?", (receipt_id,)
        ).fetchone()
        if not row:
            raise KeyError(receipt_id)
        self.validate_dependencies(
            row["domain_id"], [Dependency(**x) for x in json.loads(row["dependencies_json"])]
        )
        return True

    def temporal_coverage_contains(self, receipt_id: str, at: datetime) -> bool:
        self.validate_temporal_coverage(receipt_id)
        row = self.db.execute(
            "SELECT valid_from,valid_to FROM temporal_coverage_receipts WHERE receipt_id=?", (receipt_id,)
        ).fetchone()
        t = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
        return _parse(row["valid_from"]) <= t.astimezone(timezone.utc) < _parse(row["valid_to"])

    def learn_procedure(
        self, domain_id: str, *, procedure_key: str, principal: str,
        experiences: Iterable[dict[str, Any]],
    ) -> dict[str, Any]:
        dedup: dict[str, dict[str, Any]] = {}
        transient_kinds = {"TRANSIENT", "TRANSIENT_TIMEOUT", "INFRASTRUCTURE_TRANSIENT", "RETRYABLE"}
        for raw in experiences:
            event_id = str(raw.get("event_identity", ""))
            outcome = str(raw.get("outcome", "")).upper()
            applicability = dict(raw.get("applicability") or {})
            if not event_id or outcome not in {"SUCCESS", "FAILURE"}:
                raise MemoryTransitionIncomplete("procedure experiences require event identity and SUCCESS/FAILURE outcome")
            failure_kind = str(raw.get("failure_kind") or ("HYPOTHESIS_RELEVANT" if outcome == "FAILURE" else "NONE")).upper()
            severity = str(raw.get("severity") or "NORMAL").upper()
            reproducer_ref = raw.get("reproducer_ref")
            normalized = {
                "event_identity": event_id, "outcome": outcome, "applicability": applicability,
                "failure_kind": failure_kind, "severity": severity, "reproducer_ref": reproducer_ref,
            }
            previous = dedup.get(event_id)
            if previous is not None and digest(previous) != digest(normalized):
                raise MemoryIdentityCollision("one semantic experience identity has conflicting procedure semantics")
            dedup[event_id] = normalized
        if not dedup:
            raise MemoryTransitionIncomplete("procedure learning requires at least one experience")

        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in dedup.values():
            key = canonical_json(item["applicability"])
            grouped.setdefault(key, []).append(item)
        slices: list[dict[str, Any]] = []
        when_not_to_use: list[dict[str, Any]] = []
        for key in sorted(grouped):
            items = grouped[key]
            successes = sorted(x["event_identity"] for x in items if x["outcome"] == "SUCCESS")
            all_failures = [x for x in items if x["outcome"] == "FAILURE"]
            transient_failures = sorted(x["event_identity"] for x in all_failures if x["failure_kind"] in transient_kinds)
            hypothesis_failures = sorted(x["event_identity"] for x in all_failures if x["failure_kind"] not in transient_kinds)
            protected_failures = sorted(
                x["event_identity"] for x in all_failures if x["severity"] in {"CATASTROPHIC", "CRITICAL"}
            )
            reproducers = {x["event_identity"]: x["reproducer_ref"] for x in all_failures if x.get("reproducer_ref")}
            if successes and hypothesis_failures:
                status = "UNRESOLVED"
            elif hypothesis_failures:
                status = "NEGATIVE_APPLICABILITY"
            elif successes and transient_failures:
                status = "SUPPORTED_WITH_TRANSIENT_FAILURE"
            elif successes:
                status = "SUPPORTED"
            elif transient_failures:
                status = "INSUFFICIENT_TRANSIENT_ONLY"
            else:
                status = "UNRESOLVED"
            applicability = json.loads(key)
            if status in {"NEGATIVE_APPLICABILITY", "UNRESOLVED"}:
                when_not_to_use.append(applicability)
            slices.append({
                "applicability": applicability,
                "success_event_ids": successes,
                "failure_event_ids": sorted(x["event_identity"] for x in all_failures),
                "hypothesis_failure_event_ids": hypothesis_failures,
                "transient_failure_event_ids": transient_failures,
                "protected_failure_event_ids": protected_failures,
                "reproducer_refs": reproducers,
                "success_count": len(successes),
                "failure_count": len(all_failures),
                "status": status,
            })
        if len(slices) == 1:
            only = slices[0]["status"]
            if only == "NEGATIVE_APPLICABILITY":
                generic_status = "UNSUPPORTED"
            elif only == "SUPPORTED_WITH_TRANSIENT_FAILURE":
                generic_status = "SUPPORTED"
            elif only == "INSUFFICIENT_TRANSIENT_ONLY":
                generic_status = "UNRESOLVED"
            else:
                generic_status = only
        else:
            generic_status = "UNRESOLVED" if all(s["status"] == "UNRESOLVED" for s in slices) else "CONDITIONAL"
        proposal_id = f"procedure_{uuid.uuid4().hex}"
        now = self._clock(); created_at = _iso(now)
        proposal = {
            "proposal_id": proposal_id, "domain_id": domain_id, "procedure_key": procedure_key,
            "principal": principal, "unique_event_count": len(dedup), "generic_status": generic_status,
            "slices": slices, "when_not_to_use": when_not_to_use, "created_at": created_at,
        }
        self.db.execute(
            "INSERT INTO procedure_learning_proposals(proposal_id,domain_id,procedure_key,principal,proposal_json,created_at) VALUES(?,?,?,?,?,?)",
            (proposal_id, domain_id, procedure_key, principal, canonical_json(proposal), created_at),
        )
        return proposal

    def register_consolidation_policy(
        self, domain_id: str, *, revision: int, trigger_on_open_debt: bool,
        trigger_on_counterexample: bool, min_active_representations: int,
        max_derivation_depth: int,
    ) -> int:
        if revision < 1 or min_active_representations < 1 or max_derivation_depth < 1:
            raise ValueError("invalid consolidation policy")
        existing = self.db.execute(
            "SELECT revision,policy_json FROM consolidation_policies WHERE domain_id=? ORDER BY revision DESC LIMIT 1",
            (domain_id,),
        ).fetchone()
        policy = {
            "trigger_on_open_debt": bool(trigger_on_open_debt),
            "trigger_on_counterexample": bool(trigger_on_counterexample),
            "min_active_representations": int(min_active_representations),
            "max_derivation_depth": int(max_derivation_depth),
        }
        if existing:
            if revision == int(existing["revision"]) and json.loads(existing["policy_json"]) == policy:
                return revision
            if revision != int(existing["revision"]) + 1:
                raise MemoryTransitionIncomplete("consolidation policy revisions must be contiguous")
        elif revision != 1:
            raise MemoryTransitionIncomplete("first consolidation policy revision must be 1")
        request = {"revision": revision, **policy}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO consolidation_policies(domain_id,revision,policy_json,created_seq) VALUES(?,?,?,?)",
                (domain_id, revision, canonical_json(policy), seq),
            )
            self._bump_generation(cur, domain_id, "consolidation_policy", "global")
            return str(revision)
        self._auto_commit(domain_id, "REGISTER_CONSOLIDATION_POLICY", str(revision), request, mutate)
        return revision

    def _representation_depth(self, domain_id: str, representation_id: str, seen: set[str] | None = None) -> int:
        seen = set() if seen is None else seen
        if representation_id in seen:
            return 0
        seen.add(representation_id)
        row = self.db.execute(
            "SELECT source_representation_ids_json FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if not row:
            return 0
        parents = json.loads(row[0])
        if not parents:
            return 1
        return 1 + max(self._representation_depth(domain_id, p, set(seen)) for p in parents)

    def assess_consolidation_pressure(self, domain_id: str, region_id: str, *, principal: str) -> dict[str, Any]:
        region = self.db.execute(
            "SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)
        ).fetchone()
        if not region:
            raise KeyError(region_id)
        if not self._is_allowed(principal, region["allowed_principals_json"]):
            raise MemoryScopeBlocked("region is inaccessible")
        prow = self.db.execute(
            "SELECT * FROM consolidation_policies WHERE domain_id=? ORDER BY revision DESC LIMIT 1", (domain_id,)
        ).fetchone()
        if not prow:
            raise MemoryTransitionIncomplete("no consolidation policy registered")
        policy = json.loads(prow["policy_json"])
        reps = self.db.execute(
            "SELECT representation_id FROM representations WHERE domain_id=? AND region_id=? AND invalidated_seq IS NULL AND tainted_seq IS NULL",
            (domain_id, region_id),
        ).fetchall()
        active_count = len(reps)
        max_depth = max((self._representation_depth(domain_id, r[0]) for r in reps), default=0)
        counterexamples = int(self.db.execute(
            "SELECT COUNT(*) FROM query_counterexamples WHERE domain_id=? AND region_id=? AND resolved_seq IS NULL",
            (domain_id, region_id),
        ).fetchone()[0])
        open_debt = int(self.db.execute(
            "SELECT COUNT(*) FROM semantic_debts WHERE domain_id=? AND subject_id=? AND outcome IN ('OPEN','ACCEPTED_DEBT','QUARANTINED')",
            (domain_id, region_id),
        ).fetchone()[0])
        reasons: list[str] = []
        if policy["trigger_on_open_debt"] and open_debt:
            reasons.append("OPEN_SEMANTIC_DEBT")
        if policy["trigger_on_counterexample"] and counterexamples:
            reasons.append("UNRESOLVED_COUNTEREXAMPLE")
        if active_count >= int(policy["min_active_representations"]):
            reasons.append("REPRESENTATION_PRESSURE")
        if max_depth >= int(policy["max_derivation_depth"]):
            reasons.append("DERIVATION_DEPTH")
        deps = [
            Dependency("region", region_id, self._generation(domain_id, "region", region_id)),
            Dependency("counterexample", region_id, self._generation(domain_id, "counterexample", region_id)),
            Dependency("consolidation_policy", "global", self._generation(domain_id, "consolidation_policy", "global")),
        ]
        receipt_id = f"pressure_{uuid.uuid4().hex}"; created_at = _iso(self._clock())
        result = {
            "receipt_id": receipt_id, "domain_id": domain_id, "region_id": region_id,
            "policy_revision": int(prow["revision"]), "triggered": bool(reasons), "reasons": reasons,
            "metrics": {"active_representations": active_count, "max_derivation_depth": max_depth,
                        "unresolved_counterexamples": counterexamples, "open_semantic_debt": open_debt},
            "created_at": created_at,
        }
        self.db.execute(
            "INSERT INTO consolidation_pressure_receipts(receipt_id,domain_id,region_id,policy_revision,receipt_json,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (receipt_id, domain_id, region_id, int(prow["revision"]), canonical_json(result),
             canonical_json([asdict(d) for d in deps]), created_at),
        )
        return result
