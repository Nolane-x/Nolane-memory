from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import timezone
from typing import Any, Iterable

from .errors import (
    MemoryDependencyStale,
    MemoryProposalStale,
    MemoryRecallInsufficient,
    MemoryScopeBlocked,
    MemoryTransitionIncomplete,
)
from .normalize import canonical_json, digest
from .types import (
    Answerability,
    Dependency,
    ExtractionProposal,
    ExtractionVerificationReceipt,
    LossState,
)


class ExtractionMixin:
    """Typed model-extraction proposals and lineage-based explanation rendering."""

    def _init_extraction_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS extraction_proposals(
              proposal_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              source_evidence_id TEXT NOT NULL,
              principal TEXT NOT NULL,
              extractor_revision TEXT NOT NULL,
              extracted_fields_json TEXT NOT NULL,
              extracted_fields_digest TEXT NOT NULL,
              source_handles_json TEXT NOT NULL,
              candidate_types_json TEXT NOT NULL,
              uncertainty_json TEXT NOT NULL,
              high_risk_fields_json TEXT NOT NULL,
              dependencies_json TEXT NOT NULL,
              status TEXT NOT NULL,
              verification_receipt_id TEXT,
              created_at TEXT NOT NULL,
              invalidated_seq INTEGER,
              promoted_representation_id TEXT,
              promoted_seq INTEGER
            );
            CREATE INDEX IF NOT EXISTS extraction_source_idx
              ON extraction_proposals(domain_id,source_evidence_id,status);
            CREATE TABLE IF NOT EXISTS extraction_verifications(
              receipt_id TEXT PRIMARY KEY,
              proposal_id TEXT NOT NULL,
              domain_id TEXT NOT NULL,
              verifier_ref TEXT NOT NULL,
              field_results_json TEXT NOT NULL,
              status TEXT NOT NULL,
              dependencies_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )

    def _extraction_now(self) -> str:
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _extraction_from_row(row) -> ExtractionProposal:
        return ExtractionProposal(
            proposal_id=row["proposal_id"],
            domain_id=row["domain_id"],
            source_evidence_id=row["source_evidence_id"],
            principal=row["principal"],
            extractor_revision=row["extractor_revision"],
            extracted_fields_digest=row["extracted_fields_digest"],
            source_handles=dict(json.loads(row["source_handles_json"])),
            candidate_types=list(json.loads(row["candidate_types_json"])),
            uncertainty=dict(json.loads(row["uncertainty_json"])),
            high_risk_fields=list(json.loads(row["high_risk_fields_json"])),
            dependencies=[Dependency(**d) for d in json.loads(row["dependencies_json"])],
            status=row["status"],
            created_at=row["created_at"],
            promoted_representation_id=row["promoted_representation_id"],
        )

    def propose_extraction(
        self, domain_id: str, *, source_evidence_id: str, principal: str,
        extractor_revision: str, extracted_fields: dict[str, Any], source_handles: dict[str, str],
        candidate_types: Iterable[str], uncertainty: dict[str, float], high_risk_fields: set[str],
    ) -> ExtractionProposal:
        source = self.db.execute(
            "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?",
            (domain_id, source_evidence_id),
        ).fetchone()
        if not source:
            raise KeyError(source_evidence_id)
        if not self._is_allowed(principal, source["allowed_principals_json"]):
            raise MemoryScopeBlocked("extraction source is not visible to principal")
        if any(source[k] is not None for k in ("revoked_seq", "deleted_seq", "compromised_seq")):
            raise MemoryTransitionIncomplete("cannot extract from non-live source evidence")
        fields = dict(extracted_fields)
        handles = dict(source_handles)
        for field in fields:
            if field not in handles:
                raise MemoryTransitionIncomplete(f"extracted field {field!r} has no source handle")
        for field, value in uncertainty.items():
            if float(value) < 0 or float(value) > 1:
                raise MemoryTransitionIncomplete(f"uncertainty for {field!r} must be within [0,1]")
        deps = [
            Dependency("source", source_evidence_id, self._generation(domain_id, "source", source_evidence_id)),
            Dependency("origin", source_evidence_id, self._generation(domain_id, "origin", source_evidence_id)),
            Dependency("origin", "global", self._generation(domain_id, "origin", "global")),
        ]
        proposal_id = f"extract_{uuid.uuid4().hex}"
        created_at = self._extraction_now()
        self.db.execute(
            "INSERT INTO extraction_proposals(proposal_id,domain_id,source_evidence_id,principal,extractor_revision,extracted_fields_json,extracted_fields_digest,source_handles_json,candidate_types_json,uncertainty_json,high_risk_fields_json,dependencies_json,status,verification_receipt_id,created_at,invalidated_seq,promoted_representation_id,promoted_seq) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,? ,NULL,?,NULL,NULL,NULL)",
            (
                proposal_id, domain_id, source_evidence_id, principal, extractor_revision,
                canonical_json(fields), digest(fields), canonical_json(handles),
                canonical_json(sorted(set(candidate_types))), canonical_json(dict(uncertainty)),
                canonical_json(sorted(set(high_risk_fields))), canonical_json([asdict(d) for d in deps]),
                "CANDIDATE", created_at,
            ),
        )
        row = self.db.execute("SELECT * FROM extraction_proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        return self._extraction_from_row(row)

    def verify_extraction_proposal(
        self, domain_id: str, proposal_id: str, *, principal: str,
        verifier_ref: str, field_results: dict[str, str],
    ) -> ExtractionVerificationReceipt:
        row = self.db.execute(
            "SELECT * FROM extraction_proposals WHERE domain_id=? AND proposal_id=?",
            (domain_id, proposal_id),
        ).fetchone()
        if not row:
            raise KeyError(proposal_id)
        if row["principal"] != principal:
            raise MemoryScopeBlocked("extraction proposal principal mismatch")
        deps = [Dependency(**d) for d in json.loads(row["dependencies_json"])]
        try:
            self.validate_dependencies(domain_id, deps)
        except MemoryDependencyStale as exc:
            raise MemoryProposalStale(f"extraction proposal stale: {exc}") from exc
        required = set(json.loads(row["high_risk_fields_json"]))
        normalized = {str(k): str(v).upper() for k, v in field_results.items()}
        if any(normalized.get(field) == "FAIL" for field in required):
            status = "REJECTED"
        elif required and not all(normalized.get(field) == "PASS" for field in required):
            status = "INCOMPLETE"
        elif any(value not in {"PASS", "NOT_APPLICABLE"} for value in normalized.values()):
            status = "INCOMPLETE"
        else:
            status = "VERIFIED"
        receipt_id = f"extract_verify_{uuid.uuid4().hex}"
        created_at = self._extraction_now()
        self.db.execute(
            "INSERT INTO extraction_verifications(receipt_id,proposal_id,domain_id,verifier_ref,field_results_json,status,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (receipt_id, proposal_id, domain_id, verifier_ref, canonical_json(normalized), status,
             canonical_json([asdict(d) for d in deps]), created_at),
        )
        self.db.execute(
            "UPDATE extraction_proposals SET status=?,verification_receipt_id=? WHERE proposal_id=?",
            (status, receipt_id, proposal_id),
        )
        return ExtractionVerificationReceipt(
            receipt_id=receipt_id, proposal_id=proposal_id, domain_id=domain_id,
            verifier_ref=verifier_ref, field_results=normalized, status=status,
            dependencies=deps, created_at=created_at,
        )

    def promote_extraction_to_representation(
        self, proposal_id: str, *, region_id: str, principal: str, kind: str,
        loss: dict[str, LossState | str], recoverable: set[str], token_cost: int,
    ) -> str:
        row = self.db.execute(
            "SELECT * FROM extraction_proposals WHERE proposal_id=?", (proposal_id,)
        ).fetchone()
        if not row:
            raise KeyError(proposal_id)
        if row["promoted_representation_id"]:
            return row["promoted_representation_id"]
        if row["status"] != "VERIFIED" or not row["verification_receipt_id"]:
            raise MemoryTransitionIncomplete("extraction proposal is not verified")
        if row["principal"] != principal:
            raise MemoryScopeBlocked("extraction proposal principal mismatch")
        verification = self.db.execute(
            "SELECT * FROM extraction_verifications WHERE receipt_id=? AND proposal_id=?",
            (row["verification_receipt_id"], proposal_id),
        ).fetchone()
        if not verification or verification["status"] != "VERIFIED":
            raise MemoryTransitionIncomplete("extraction verification is incomplete")
        domain_id = row["domain_id"]
        deps = [Dependency(**d) for d in json.loads(row["dependencies_json"])]
        verification_deps = [Dependency(**d) for d in json.loads(verification["dependencies_json"])]
        loss_norm = {k: (v.value if isinstance(v, LossState) else str(v)) for k, v in loss.items()}
        rep_id = f"rep_{digest([proposal_id, row['extracted_fields_digest'], region_id, kind])[:24]}"
        request = {
            "proposal_id": proposal_id,
            "region_id": region_id,
            "kind": kind,
            "payload_digest": row["extracted_fields_digest"],
            "loss": loss_norm,
            "recoverable": sorted(recoverable),
            "token_cost": int(token_cost),
            "verification_receipt_id": verification["receipt_id"],
        }

        def mutate(cur, seq):
            try:
                self.validate_dependencies(domain_id, deps, cur=cur)
                self.validate_dependencies(domain_id, verification_deps, cur=cur)
            except MemoryDependencyStale as exc:
                raise MemoryProposalStale(f"extraction proposal stale: {exc}") from exc
            current = cur.execute(
                "SELECT * FROM extraction_proposals WHERE proposal_id=?", (proposal_id,)
            ).fetchone()
            if current["invalidated_seq"] is not None:
                raise MemoryProposalStale("extraction proposal was invalidated")
            source = cur.execute(
                "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?",
                (domain_id, current["source_evidence_id"]),
            ).fetchone()
            if not source or any(source[k] is not None for k in ("revoked_seq", "deleted_seq", "compromised_seq")):
                raise MemoryProposalStale("source evidence is no longer live")
            if not self._is_allowed(principal, source["allowed_principals_json"]):
                raise MemoryScopeBlocked("source evidence is no longer visible")
            region = cur.execute(
                "SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)
            ).fetchone()
            if not region or region["invalidated_seq"] is not None:
                raise MemoryProposalStale("target region is unavailable")
            if not self._is_allowed(principal, region["allowed_principals_json"]):
                raise MemoryScopeBlocked("target region is not visible")
            allowed = json.loads(region["allowed_principals_json"])
            cur.execute(
                "INSERT INTO representations(representation_id,domain_id,region_id,kind,payload_json,source_representation_ids_json,transform_kind,loss_json,recoverable_json,token_cost,principal,allowed_principals_json,created_seq,invalidated_seq,source_evidence_ids_json,transform_profile,tainted_seq,hard_dependencies_json,applicability_json) "
                "VALUES(?,?,?,?,?,'[]','PURE',?,?,?,?,?,?,NULL,?,?,NULL,'[]','{}')",
                (
                    rep_id, domain_id, region_id, kind, current["extracted_fields_json"], canonical_json(loss_norm),
                    canonical_json(sorted(recoverable)), int(token_cost), principal, canonical_json(allowed), seq,
                    canonical_json([current["source_evidence_id"]]), current["extractor_revision"],
                ),
            )
            roots = [r[0] for r in cur.execute(
                "SELECT root_identity FROM origin_roots WHERE domain_id=? AND object_kind='evidence' AND object_id=? ORDER BY root_identity",
                (domain_id, current["source_evidence_id"]),
            ).fetchall()]
            for root in roots:
                cur.execute(
                    "INSERT OR IGNORE INTO origin_roots(domain_id,object_kind,object_id,root_identity) VALUES(?,?,?,?)",
                    (domain_id, "representation", rep_id, root),
                )
            cur.execute(
                "UPDATE extraction_proposals SET promoted_representation_id=?,promoted_seq=? WHERE proposal_id=?",
                (rep_id, seq, proposal_id),
            )
            self._bump_generation(cur, domain_id, "representation", rep_id)
            self._bump_generation(cur, domain_id, "region", region_id)
            self._bump_generation(cur, domain_id, "query_domain", "global")
            return rep_id

        return self._auto_commit(domain_id, "PROMOTE_EXTRACTION", rep_id, request, mutate).object_id

    def _lineage_evidence_ids(self, domain_id: str, representation_id: str, seen: set[str] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        if representation_id in seen:
            return set()
        seen.add(representation_id)
        row = self.db.execute(
            "SELECT source_evidence_ids_json,source_representation_ids_json FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if not row:
            return set()
        result = set(json.loads(row["source_evidence_ids_json"]))
        for source_rep in json.loads(row["source_representation_ids_json"]):
            result.update(self._lineage_evidence_ids(domain_id, source_rep, set(seen)))
        return result

    def explain_memory(
        self, domain_id: str, representation_id: str, *, principal: str,
        query_family: str | None = None, consumer: str | None = None, task: str | None = None,
        regime: str | None = None, rendering: str | None = None,
    ) -> dict[str, Any]:
        if hasattr(self, "_require_capability"):
            self._require_capability(domain_id, principal, "READ_EXACT")
        rep = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if not rep:
            raise KeyError(representation_id)
        if not self._is_allowed(principal, rep["allowed_principals_json"]):
            raise MemoryScopeBlocked("representation explanation is outside principal scope")
        extraction = self.db.execute(
            "SELECT * FROM extraction_proposals WHERE domain_id=? AND promoted_representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        evidence_ids = sorted(self._lineage_evidence_ids(domain_id, representation_id))
        visible_evidence: list[str] = []
        origin_roots: set[str] = set()
        authority_classes: set[str] = set()
        source_times: list[dict[str, Any]] = []
        blocked_sources = 0
        for evidence_id in evidence_ids:
            erow = self.db.execute(
                "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, evidence_id)
            ).fetchone()
            if not erow or not self._is_allowed(principal, erow["allowed_principals_json"]):
                blocked_sources += 1
                continue
            visible_evidence.append(evidence_id)
            source_times.append({
                "evidence_id": evidence_id,
                "world_time": erow["world_time"],
                "observed_at": erow["observed_at"],
                "ingested_at": erow["ingested_at"],
                "revoked": erow["revoked_seq"] is not None,
                "deleted": erow["deleted_seq"] is not None,
                "compromised": erow["compromised_seq"] is not None,
            })
            origin_roots.update(self.get_origin_roots(domain_id, "evidence", evidence_id))
            for binding in self.get_origin_bindings(domain_id, evidence_id):
                if binding.revoked_seq is None and ("*" in binding.scope_ceiling or principal in binding.scope_ceiling):
                    authority_classes.add(binding.authority_class)
        counter_sql = (
            "SELECT * FROM query_counterexamples WHERE domain_id=? AND representation_id=? "
            + ("AND query_family=? " if query_family else "")
            + "ORDER BY created_seq,counterexample_id"
        )
        counter_args: tuple[Any, ...] = (domain_id, representation_id, query_family) if query_family else (domain_id, representation_id)
        counters = self.db.execute(counter_sql, counter_args).fetchall()
        counterexamples = [
            {
                "counterexample_id": row["counterexample_id"],
                "query_family": row["query_family"],
                "lost_dimensions": list(json.loads(row["lost_dimensions_json"])),
                "decision_relevance": row["decision_relevance"],
                "cause_type": row["cause_type"],
                "resolved": row["resolved_seq"] is not None,
                "source_witness_id": row["source_witness_id"],
            }
            for row in counters
        ]
        effects: list[dict[str, Any]] = []
        if all(v is not None for v in (consumer, task, regime, rendering)):
            rows = self.db.execute(
                "SELECT * FROM effect_evidence WHERE domain_id=? AND consumer=? AND task=? AND regime=? AND rendering=? ORDER BY created_at,effect_id",
                (domain_id, consumer, task, regime, rendering),
            ).fetchall()
            for row in rows:
                if representation_id in set(json.loads(row["representation_ids_json"])):
                    effects.append({
                        "effect_id": row["effect_id"], "tier": row["tier"], "effect": float(row["effect"]),
                        "confidence": float(row["confidence"]), "outcome_dimension": row["outcome_dimension"],
                    })
        preservation_status = None
        if query_family:
            answer = self.answerability(representation_id, query_family)
            preservation_status = {
                Answerability.EXACT: "EXACT",
                Answerability.BOUNDED: "BOUNDED",
                Answerability.REHYDRATABLE: "SOURCE_REHYDRATABLE",
                Answerability.UNKNOWN: "UNKNOWN",
                Answerability.UNSUPPORTED: "UNSUPPORTED",
            }[answer]
        return {
            "representation": {
                "representation_id": representation_id,
                "region_id": rep["region_id"],
                "kind": rep["kind"],
                "transform_kind": rep["transform_kind"],
                "transform_profile": rep["transform_profile"],
                "extractor_revision": extraction["extractor_revision"] if extraction else None,
                "current_usable": rep["invalidated_seq"] is None and rep["tainted_seq"] is None,
                "applicability": dict(json.loads(rep["applicability_json"] or "{}")),
            },
            "source": {
                "evidence_ids": visible_evidence,
                "scope_blocked_evidence_count": blocked_sources,
                "origin_roots": sorted(origin_roots),
                "authority_classes": sorted(authority_classes),
                "times": source_times,
            },
            "preservation": {
                "query_family": query_family,
                "status": preservation_status,
                "loss": dict(json.loads(rep["loss_json"])),
                "recoverable_dimensions": list(json.loads(rep["recoverable_json"])),
            },
            "counterexamples": counterexamples,
            "effects": effects,
            "access": {"allowed_principals": list(json.loads(rep["allowed_principals_json"]))},
            "invalidation_conditions": {
                "source_evidence_ids": evidence_ids,
                "transform_profile": rep["transform_profile"],
                "query_family": query_family,
                "applicability": dict(json.loads(rep["applicability_json"] or "{}")),
            },
        }
