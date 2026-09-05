from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from typing import Any
from datetime import timezone

from .errors import (
    MemoryAmbiguousSuccessors,
    MemoryDebtTransitionInvalid,
    MemoryDependencyStale,
    MemoryProposalStale,
    MemoryRetentionBlocked,
    MemoryScopeBlocked,
    MemoryTransitionIncomplete,
    MemoryWriteConflict,
)
from .normalize import canonical_json, digest
from .types import (
    DebtOutcome,
    LossState,
    MaintenanceReceipt,
    ProbeCheckpoint,
    QueryCounterexample,
    RepairCause,
    RepairReceipt,
    RepresentationProposal,
    RegionEvolutionReceipt,
    RetentionDecision,
    SemanticDebt,
    Dependency,
    TransitionVerificationReceipt,
    CounterexampleApplicabilityRevision,
)


_OPEN_DEBT_STATES = {
    DebtOutcome.OPEN.value,
    DebtOutcome.NARROWED.value,
    DebtOutcome.PARTIALLY_DISCHARGED.value,
}


class EvolutionMixin:
    def _init_evolution_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS semantic_debts(
              debt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, subject_kind TEXT NOT NULL,
              subject_id TEXT NOT NULL, kind TEXT NOT NULL, severity TEXT NOT NULL,
              consequence TEXT NOT NULL, evidence_needed TEXT NOT NULL, outcome TEXT NOT NULL,
              evidence_ref TEXT, created_seq INTEGER NOT NULL, resolved_seq INTEGER
            );
            CREATE INDEX IF NOT EXISTS debt_subject_idx ON semantic_debts(domain_id,subject_kind,subject_id,outcome);
            CREATE TABLE IF NOT EXISTS query_counterexamples(
              counterexample_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, region_id TEXT NOT NULL,
              representation_id TEXT NOT NULL, query_family TEXT NOT NULL,
              lost_dimensions_json TEXT NOT NULL, source_witness_id TEXT,
              decision_relevance TEXT NOT NULL, cause_type TEXT NOT NULL,
              created_seq INTEGER NOT NULL, resolved_seq INTEGER,
              replacement_representation_id TEXT
            );
            CREATE TABLE IF NOT EXISTS counterexample_applicability_revisions(
              counterexample_id TEXT NOT NULL, domain_id TEXT NOT NULL, revision INTEGER NOT NULL,
              predecessor_revision INTEGER, applicability_json TEXT NOT NULL, status TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              PRIMARY KEY(counterexample_id,revision)
            );
            CREATE TABLE IF NOT EXISTS repair_receipts(
              repair_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, counterexample_id TEXT NOT NULL,
              cause_type TEXT NOT NULL, invalidated_representation_ids_json TEXT NOT NULL,
              replacement_representation_id TEXT, dependency_fanout_json TEXT NOT NULL,
              status TEXT NOT NULL, created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS protected_obligations(
              obligation_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, region_id TEXT NOT NULL,
              query_family TEXT NOT NULL, principal TEXT NOT NULL, created_seq INTEGER NOT NULL,
              UNIQUE(domain_id,region_id,query_family,principal)
            );
            CREATE TABLE IF NOT EXISTS retention_events(
              retention_event_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, target_kind TEXT NOT NULL,
              target_id TEXT NOT NULL, mode TEXT NOT NULL, policy_ref TEXT NOT NULL,
              authority_principal TEXT NOT NULL, created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS retention_decisions(
              decision_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, target_kind TEXT NOT NULL,
              target_id TEXT NOT NULL, status TEXT NOT NULL,
              protected_families_json TEXT NOT NULL, uncovered_families_json TEXT NOT NULL,
              debt_id TEXT, created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS maintenance_receipts(
              maintenance_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, region_id TEXT NOT NULL,
              semantic_digest TEXT NOT NULL, outcome TEXT NOT NULL, created_seq INTEGER NOT NULL,
              UNIQUE(domain_id,region_id,semantic_digest)
            );
            CREATE TABLE IF NOT EXISTS probe_checkpoints(
              checkpoint_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, label TEXT NOT NULL,
              cut_json TEXT NOT NULL, vector_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS legacy_imports(
              import_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, source_kind TEXT NOT NULL,
              source_id TEXT NOT NULL, representation_id TEXT, debt_id TEXT,
              created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS region_evolution(
              evolution_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, kind TEXT NOT NULL,
              predecessor_region_ids_json TEXT NOT NULL, successor_region_ids_json TEXT NOT NULL,
              created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS region_successors(
              domain_id TEXT NOT NULL, predecessor_region_id TEXT NOT NULL, successor_region_id TEXT NOT NULL,
              evolution_id TEXT NOT NULL, created_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,predecessor_region_id,successor_region_id,evolution_id)
            );
            CREATE TABLE IF NOT EXISTS representation_proposals(
              proposal_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, region_id TEXT NOT NULL, kind TEXT NOT NULL,
              payload_json TEXT NOT NULL, payload_digest TEXT NOT NULL, source_representation_ids_json TEXT NOT NULL,
              loss_json TEXT NOT NULL, recoverable_json TEXT NOT NULL, token_cost INTEGER NOT NULL, principal TEXT NOT NULL,
              allowed_principals_json TEXT NOT NULL, transform_kind TEXT NOT NULL, transform_profile TEXT NOT NULL,
              dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL, invalidated_seq INTEGER,
              promoted_representation_id TEXT, promoted_seq INTEGER,
              verification_receipt_id TEXT
            );
            CREATE TABLE IF NOT EXISTS transition_verifications(
              receipt_id TEXT PRIMARY KEY, proposal_id TEXT NOT NULL, domain_id TEXT NOT NULL,
              verifier_ref TEXT NOT NULL, coverage TEXT NOT NULL, preservation TEXT NOT NULL,
              faithfulness TEXT NOT NULL, status TEXT NOT NULL, dependencies_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        cols = {r[1] for r in self.db.execute("PRAGMA table_info(representation_proposals)")}
        if "verification_receipt_id" not in cols:
            self.db.execute("ALTER TABLE representation_proposals ADD COLUMN verification_receipt_id TEXT")

    # ---------- semantic debt ----------

    @staticmethod
    def _debt_from_row(row) -> SemanticDebt:
        return SemanticDebt(
            debt_id=row["debt_id"], domain_id=row["domain_id"], subject_kind=row["subject_kind"],
            subject_id=row["subject_id"], kind=row["kind"], severity=row["severity"],
            consequence=row["consequence"], evidence_needed=row["evidence_needed"],
            outcome=row["outcome"], evidence_ref=row["evidence_ref"],
            created_seq=int(row["created_seq"]), resolved_seq=row["resolved_seq"],
        )

    def _assert_subject_access(self, domain_id: str, subject_kind: str, subject_id: str, principal: str) -> None:
        table = {"region": "regions", "representation": "representations", "evidence": "evidence"}.get(subject_kind)
        id_col = {"region": "region_id", "representation": "representation_id", "evidence": "evidence_id"}.get(subject_kind)
        if not table:
            return
        row = self.db.execute(
            f"SELECT allowed_principals_json FROM {table} WHERE domain_id=? AND {id_col}=?",
            (domain_id, subject_id),
        ).fetchone()
        if row and not self._is_allowed(principal, row[0]):
            raise MemoryScopeBlocked(f"principal cannot access {subject_kind} {subject_id}")

    def create_semantic_debt(
        self, domain_id: str, *, subject_kind: str, subject_id: str, kind: str,
        severity: str, evidence_needed: str, consequence: str, principal: str,
    ) -> SemanticDebt:
        self._assert_subject_access(domain_id, subject_kind, subject_id, principal)
        debt_id = f"debt_{uuid.uuid4().hex}"
        request = {
            "subject_kind": subject_kind, "subject_id": subject_id, "kind": kind,
            "severity": severity, "evidence_needed": evidence_needed,
            "consequence": consequence, "principal": principal,
        }
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO semantic_debts(debt_id,domain_id,subject_kind,subject_id,kind,severity,consequence,evidence_needed,outcome,evidence_ref,created_seq,resolved_seq) VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)",
                (debt_id, domain_id, subject_kind, subject_id, kind, severity, consequence,
                 evidence_needed, DebtOutcome.OPEN.value, None, seq),
            )
            self._bump_generation(cur, domain_id, "semantic_debt", subject_id)
            return debt_id
        self._auto_commit(domain_id, "CREATE_SEMANTIC_DEBT", debt_id, request, mutate)
        return self.get_semantic_debt(debt_id)

    def get_semantic_debt(self, debt_id: str) -> SemanticDebt:
        row = self.db.execute("SELECT * FROM semantic_debts WHERE debt_id=?", (debt_id,)).fetchone()
        if not row:
            raise KeyError(debt_id)
        return self._debt_from_row(row)

    def transition_semantic_debt(
        self, domain_id: str, debt_id: str, outcome: DebtOutcome | str, *,
        evidence_ref: str | None, principal: str,
    ) -> SemanticDebt:
        desired = outcome.value if isinstance(outcome, DebtOutcome) else str(outcome)
        if desired not in {o.value for o in DebtOutcome}:
            raise MemoryDebtTransitionInvalid(f"unknown debt outcome {desired!r}")
        existing = self.get_semantic_debt(debt_id)
        if existing.domain_id != domain_id:
            raise KeyError(debt_id)
        self._assert_subject_access(domain_id, existing.subject_kind, existing.subject_id, principal)
        if existing.outcome not in _OPEN_DEBT_STATES and existing.outcome != desired:
            raise MemoryDebtTransitionInvalid("resolved debt cannot be silently reopened or rewritten")
        if existing.outcome == desired and existing.evidence_ref == evidence_ref:
            return existing
        request = {"debt_id": debt_id, "outcome": desired, "evidence_ref": evidence_ref, "principal": principal}
        def mutate(cur, seq):
            row = cur.execute("SELECT * FROM semantic_debts WHERE debt_id=? AND domain_id=?", (debt_id, domain_id)).fetchone()
            if not row:
                raise KeyError(debt_id)
            current = row["outcome"]
            if current not in _OPEN_DEBT_STATES and current != desired:
                raise MemoryDebtTransitionInvalid("resolved debt cannot be reopened")
            resolved_seq = None if desired in _OPEN_DEBT_STATES else seq
            cur.execute(
                "UPDATE semantic_debts SET outcome=?, evidence_ref=?, resolved_seq=? WHERE debt_id=?",
                (desired, evidence_ref, resolved_seq, debt_id),
            )
            self._bump_generation(cur, domain_id, "semantic_debt", row["subject_id"])
            return debt_id
        self._auto_commit(domain_id, "TRANSITION_SEMANTIC_DEBT", debt_id, request, mutate)
        return self.get_semantic_debt(debt_id)

    # ---------- maintenance fixed point ----------

    def maintenance_fixed_point(self, domain_id: str, region_id: str, normalized_semantics: Any, *, principal: str) -> MaintenanceReceipt:
        region = self.db.execute("SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)).fetchone()
        if not region:
            raise KeyError(region_id)
        if not self._is_allowed(principal, region["allowed_principals_json"]):
            raise MemoryScopeBlocked("inaccessible region")
        sem_digest = digest(normalized_semantics)
        maintenance_id = f"maint_{digest([domain_id, region_id, sem_digest])[:24]}"
        existing = self.db.execute("SELECT * FROM maintenance_receipts WHERE maintenance_id=?", (maintenance_id,)).fetchone()
        if existing:
            return MaintenanceReceipt(
                maintenance_id=existing["maintenance_id"], domain_id=existing["domain_id"],
                region_id=existing["region_id"], semantic_digest=existing["semantic_digest"],
                outcome="FIXED_POINT", created_seq=int(existing["created_seq"]),
            )
        request = {"region_id": region_id, "semantic_digest": sem_digest, "principal": principal}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO maintenance_receipts(maintenance_id,domain_id,region_id,semantic_digest,outcome,created_seq) VALUES(?,?,?,?,?,?)",
                (maintenance_id, domain_id, region_id, sem_digest, "MATERIALIZED", seq),
            )
            return maintenance_id
        self._auto_commit(domain_id, "MAINTENANCE_FIXED_POINT", maintenance_id, request, mutate)
        return MaintenanceReceipt(maintenance_id, domain_id, region_id, sem_digest, "MATERIALIZED", self.head(domain_id).sequence)

    # ---------- query counterexamples / repair ----------

    @staticmethod
    def _counterexample_from_row(row) -> QueryCounterexample:
        return QueryCounterexample(
            counterexample_id=row["counterexample_id"], domain_id=row["domain_id"], region_id=row["region_id"],
            representation_id=row["representation_id"], query_family=row["query_family"],
            lost_dimensions=list(json.loads(row["lost_dimensions_json"])), source_witness_id=row["source_witness_id"],
            decision_relevance=row["decision_relevance"], cause_type=row["cause_type"],
            created_seq=int(row["created_seq"]), resolved_seq=row["resolved_seq"],
            replacement_representation_id=row["replacement_representation_id"],
        )

    def record_query_counterexample(
        self, domain_id: str, *, region_id: str, representation_id: str, query_family: str,
        lost_dimensions: set[str], source_witness_id: str | None, decision_relevance: str,
        cause_type: RepairCause | str, principal: str, applicability: dict[str, Any] | None = None,
    ) -> QueryCounterexample:
        cause = cause_type.value if isinstance(cause_type, RepairCause) else str(cause_type)
        row = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, representation_id)).fetchone()
        if not row or row["region_id"] != region_id:
            raise MemoryTransitionIncomplete("counterexample target does not belong to region")
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("counterexample target inaccessible")
        self._family_requirements(query_family)
        if source_witness_id:
            witness = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, source_witness_id)).fetchone()
            if not witness:
                raise MemoryTransitionIncomplete("counterexample source witness missing")
        ce_id = f"ce_{uuid.uuid4().hex}"
        request = {
            "region_id": region_id, "representation_id": representation_id, "query_family": query_family,
            "lost_dimensions": sorted(lost_dimensions), "source_witness_id": source_witness_id,
            "decision_relevance": decision_relevance, "cause_type": cause, "principal": principal,
            "applicability": dict(applicability or {}),
        }
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO query_counterexamples(counterexample_id,domain_id,region_id,representation_id,query_family,lost_dimensions_json,source_witness_id,decision_relevance,cause_type,created_seq,resolved_seq,replacement_representation_id) VALUES(?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
                (ce_id, domain_id, region_id, representation_id, query_family, canonical_json(sorted(lost_dimensions)),
                 source_witness_id, decision_relevance, cause, seq),
            )
            cur.execute(
                "INSERT INTO counterexample_applicability_revisions(counterexample_id,domain_id,revision,predecessor_revision,applicability_json,status,created_seq) VALUES(?,?,?,?,?,?,?)",
                (ce_id, domain_id, 1, None, canonical_json(dict(applicability or {})), "ACTIVE", seq),
            )
            self._bump_generation(cur, domain_id, "counterexample", region_id)
            return ce_id
        self._auto_commit(domain_id, "RECORD_QUERY_COUNTEREXAMPLE", ce_id, request, mutate)
        return self.get_query_counterexample(ce_id)

    def get_query_counterexample(self, counterexample_id: str) -> QueryCounterexample:
        row = self.db.execute("SELECT * FROM query_counterexamples WHERE counterexample_id=?", (counterexample_id,)).fetchone()
        if not row:
            raise KeyError(counterexample_id)
        return self._counterexample_from_row(row)

    @staticmethod
    def _counterexample_applicability_from_row(row) -> CounterexampleApplicabilityRevision:
        return CounterexampleApplicabilityRevision(
            counterexample_id=row["counterexample_id"], domain_id=row["domain_id"], revision=int(row["revision"]),
            predecessor_revision=None if row["predecessor_revision"] is None else int(row["predecessor_revision"]),
            applicability=dict(json.loads(row["applicability_json"])), status=row["status"], created_seq=int(row["created_seq"]),
        )

    def get_counterexample_applicability(
        self, domain_id: str, counterexample_id: str, *, revision: int | None = None, at_seq: int | None = None,
    ) -> CounterexampleApplicabilityRevision:
        if revision is not None and at_seq is not None:
            raise ValueError("choose revision or at_seq, not both")
        if revision is not None:
            row = self.db.execute(
                "SELECT * FROM counterexample_applicability_revisions WHERE domain_id=? AND counterexample_id=? AND revision=?",
                (domain_id, counterexample_id, revision),
            ).fetchone()
        elif at_seq is not None:
            row = self.db.execute(
                "SELECT * FROM counterexample_applicability_revisions WHERE domain_id=? AND counterexample_id=? AND created_seq<=? ORDER BY revision DESC LIMIT 1",
                (domain_id, counterexample_id, at_seq),
            ).fetchone()
        else:
            row = self.db.execute(
                "SELECT * FROM counterexample_applicability_revisions WHERE domain_id=? AND counterexample_id=? ORDER BY revision DESC LIMIT 1",
                (domain_id, counterexample_id),
            ).fetchone()
        if row is None:
            raise KeyError((domain_id, counterexample_id, revision, at_seq))
        return self._counterexample_applicability_from_row(row)

    def list_counterexample_applicability_revisions(self, domain_id: str, counterexample_id: str) -> list[CounterexampleApplicabilityRevision]:
        return [self._counterexample_applicability_from_row(row) for row in self.db.execute(
            "SELECT * FROM counterexample_applicability_revisions WHERE domain_id=? AND counterexample_id=? ORDER BY revision",
            (domain_id, counterexample_id),
        ).fetchall()]

    def revise_counterexample_applicability(
        self, domain_id: str, counterexample_id: str, *, applicability: dict[str, Any], status: str,
        expected_revision: int, principal: str,
    ) -> CounterexampleApplicabilityRevision:
        if status not in {"ACTIVE", "INACTIVE", "QUARANTINED"}:
            raise MemoryTransitionIncomplete(f"invalid counterexample applicability status {status!r}")
        ce = self.get_query_counterexample(counterexample_id)
        if ce.domain_id != domain_id:
            raise KeyError(counterexample_id)
        self._assert_subject_access(domain_id, "representation", ce.representation_id, principal)
        current = self.get_counterexample_applicability(domain_id, counterexample_id)
        if current.revision != expected_revision:
            raise MemoryWriteConflict(f"expected applicability revision {expected_revision}, current {current.revision}")
        if current.applicability == dict(applicability) and current.status == status:
            return current
        revision = current.revision + 1
        request = {
            "counterexample_id": counterexample_id, "applicability": dict(applicability), "status": status,
            "expected_revision": expected_revision, "principal": principal,
        }
        def mutate(cur, seq):
            row = cur.execute(
                "SELECT revision FROM counterexample_applicability_revisions WHERE domain_id=? AND counterexample_id=? ORDER BY revision DESC LIMIT 1",
                (domain_id, counterexample_id),
            ).fetchone()
            if row is None or int(row["revision"]) != expected_revision:
                raise MemoryWriteConflict("counterexample applicability predecessor changed")
            cur.execute(
                "INSERT INTO counterexample_applicability_revisions(counterexample_id,domain_id,revision,predecessor_revision,applicability_json,status,created_seq) VALUES(?,?,?,?,?,?,?)",
                (counterexample_id, domain_id, revision, expected_revision, canonical_json(dict(applicability)), status, seq),
            )
            self._bump_generation(cur, domain_id, "counterexample", ce.region_id)
            return f"{counterexample_id}:app:r{revision}"
        self._auto_commit(domain_id, "REVISE_COUNTEREXAMPLE_APPLICABILITY", f"{counterexample_id}:app:r{revision}", request, mutate)
        return self.get_counterexample_applicability(domain_id, counterexample_id, revision=revision)

    def _counterexample_applicability_matches(self, domain_id: str, counterexample_id: str, cut_seq: int) -> bool:
        try:
            rev = self.get_counterexample_applicability(domain_id, counterexample_id, at_seq=cut_seq)
        except KeyError:
            return True
        if rev.status != "ACTIVE":
            return False
        app = rev.applicability
        if not app:
            return True
        mission = environment = None
        schema = "v0.6.3"
        if hasattr(self, "_compatibility_at_seq"):
            mission, environment, schema = self._compatibility_at_seq(domain_id, cut_seq)
        self_version = self._self_version_at_seq(domain_id, cut_seq) if hasattr(self, "_self_version_at_seq") else None
        checks = {
            "mission_revision": mission, "environment_revision": environment,
            "schema_revision": schema, "self_version": self_version,
        }
        for key, current in checks.items():
            if key in app and app[key] != current:
                return False
        if "allowed_environments" in app and environment not in set(app["allowed_environments"]):
            return False
        if "allowed_self_versions" in app and self_version not in set(app["allowed_self_versions"]):
            return False
        return True

    def _representation_descendants(self, domain_id: str, seeds: set[str]) -> set[str]:
        rows = self.db.execute(
            "SELECT representation_id,source_representation_ids_json,invalidated_seq FROM representations WHERE domain_id=?",
            (domain_id,),
        ).fetchall()
        reverse: dict[str, set[str]] = {}
        for row in rows:
            for parent in json.loads(row["source_representation_ids_json"]):
                reverse.setdefault(parent, set()).add(row["representation_id"])
        out = set(seeds)
        frontier = list(seeds)
        while frontier:
            parent = frontier.pop()
            for child in reverse.get(parent, ()):
                if child not in out:
                    out.add(child); frontier.append(child)
        return out

    def repair_counterexample(
        self, domain_id: str, counterexample_id: str, *, source_representation_id: str,
        replacement_payload: Any, replacement_loss: dict[str, LossState | str], principal: str,
    ) -> RepairReceipt:
        ce = self.get_query_counterexample(counterexample_id)
        if ce.domain_id != domain_id:
            raise KeyError(counterexample_id)
        if ce.resolved_seq is not None:
            row = self.db.execute("SELECT * FROM repair_receipts WHERE counterexample_id=? ORDER BY created_seq DESC LIMIT 1", (counterexample_id,)).fetchone()
            if row:
                return RepairReceipt(
                    row["repair_id"], row["domain_id"], row["counterexample_id"], row["cause_type"],
                    list(json.loads(row["invalidated_representation_ids_json"])), row["replacement_representation_id"],
                    list(json.loads(row["dependency_fanout_json"])), row["status"], int(row["created_seq"]),
                )
            raise MemoryTransitionIncomplete("counterexample already resolved")
        src = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, source_representation_id)).fetchone()
        if not src or src["invalidated_seq"] is not None:
            raise MemoryTransitionIncomplete("repair source unavailable")
        if not self._is_allowed(principal, src["allowed_principals_json"]):
            raise MemoryScopeBlocked("repair source inaccessible")
        for dim in ce.lost_dimensions:
            if not self._source_can_supply_dimension(self.db.cursor(), domain_id, source_representation_id, dim):
                raise MemoryTransitionIncomplete(f"repair source cannot restore {dim!r}")
        target = self.db.execute("SELECT * FROM representations WHERE representation_id=?", (ce.representation_id,)).fetchone()
        if not target:
            raise MemoryTransitionIncomplete("counterexample target missing")
        cause = ce.cause_type
        seeds = {ce.representation_id}
        fanout: list[str] = []
        if cause == RepairCause.SHARED_TRANSFORM_PROFILE.value:
            profile = target["transform_profile"]
            seeds |= {
                r[0] for r in self.db.execute(
                    "SELECT representation_id FROM representations WHERE domain_id=? AND transform_profile=? AND invalidated_seq IS NULL",
                    (domain_id, profile),
                ).fetchall()
            }
            fanout.append(f"transform_profile:{profile}")
            self.bump_generation(domain_id, "transform_profile", profile)
        elif cause == RepairCause.QUERY_FAMILY_BASIS.value:
            fanout.append(f"query_family:{ce.query_family}")
            self.bump_generation(domain_id, "query_family", ce.query_family)
        else:
            fanout.append(f"region:{ce.region_id}")
        invalidation_set = self._representation_descendants(domain_id, seeds)
        current_ids = {
            r[0] for r in self.db.execute(
                "SELECT representation_id FROM representations WHERE domain_id=? AND invalidated_seq IS NULL",
                (domain_id,),
            ).fetchall()
        }
        invalidation_set &= current_ids
        # Rebase first so an interrupted repair never loses the stronger source route.
        replacement = self.add_representation(
            domain_id, ce.region_id, kind="repaired", payload=replacement_payload,
            loss=replacement_loss, recoverable=set(), token_cost=max(1, int(src["token_cost"])),
            principal=principal, source_representation_ids=[source_representation_id],
            transform_kind="SOURCE_REBASE", transform_profile=f"repair:{cause}",
            allowed_principals=json.loads(target["allowed_principals_json"]),
        )
        for rid in sorted(invalidation_set):
            if rid == replacement:
                continue
            row = self.db.execute("SELECT invalidated_seq FROM representations WHERE representation_id=?", (rid,)).fetchone()
            if row and row[0] is None:
                self.invalidate_representation(domain_id, rid, principal=principal)
        repair_id = f"repair_{uuid.uuid4().hex}"
        request = {
            "counterexample_id": counterexample_id, "source_representation_id": source_representation_id,
            "replacement_representation_id": replacement, "invalidated": sorted(invalidation_set),
            "cause_type": cause, "principal": principal,
        }
        def mutate(cur, seq):
            cur.execute(
                "UPDATE query_counterexamples SET resolved_seq=?, replacement_representation_id=? WHERE counterexample_id=?",
                (seq, replacement, counterexample_id),
            )
            cur.execute(
                "INSERT INTO repair_receipts(repair_id,domain_id,counterexample_id,cause_type,invalidated_representation_ids_json,replacement_representation_id,dependency_fanout_json,status,created_seq) VALUES(?,?,?,?,?,?,?,?,?)",
                (repair_id, domain_id, counterexample_id, cause, canonical_json(sorted(invalidation_set)), replacement,
                 canonical_json(sorted(fanout)), "REPAIRED", seq),
            )
            self._bump_generation(cur, domain_id, "counterexample", ce.region_id)
            return repair_id
        self._auto_commit(domain_id, "REPAIR_COUNTEREXAMPLE", repair_id, request, mutate)
        row = self.db.execute("SELECT * FROM repair_receipts WHERE repair_id=?", (repair_id,)).fetchone()
        return RepairReceipt(
            row["repair_id"], row["domain_id"], row["counterexample_id"], row["cause_type"],
            list(json.loads(row["invalidated_representation_ids_json"])), row["replacement_representation_id"],
            list(json.loads(row["dependency_fanout_json"])), row["status"], int(row["created_seq"]),
        )


    def list_open_semantic_debts(self, domain_id: str, *, subject_id: str | None = None) -> list[SemanticDebt]:
        params: list[Any] = [domain_id, *_OPEN_DEBT_STATES]
        sql = (
            "SELECT * FROM semantic_debts WHERE domain_id=? AND outcome IN (?,?,?)"
        )
        if subject_id is not None:
            sql += " AND subject_id=?"
            params.append(subject_id)
        sql += " ORDER BY created_seq,debt_id"
        return [self._debt_from_row(r) for r in self.db.execute(sql, tuple(params)).fetchall()]

    # ---------- witness-cover retention ----------

    def protect_region_obligation(self, domain_id: str, region_id: str, query_family: str, *, principal: str) -> str:
        region = self.db.execute("SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)).fetchone()
        if not region:
            raise KeyError(region_id)
        if not self._is_allowed(principal, region["allowed_principals_json"]):
            raise MemoryScopeBlocked("cannot protect inaccessible region")
        self._family_requirements(query_family)
        obligation_id = f"obl_{digest([domain_id, region_id, query_family, principal])[:24]}"
        existing = self.db.execute("SELECT obligation_id FROM protected_obligations WHERE obligation_id=?", (obligation_id,)).fetchone()
        if existing:
            return obligation_id
        request = {"region_id": region_id, "query_family": query_family, "principal": principal}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO protected_obligations(obligation_id,domain_id,region_id,query_family,principal,created_seq) VALUES(?,?,?,?,?,?)",
                (obligation_id, domain_id, region_id, query_family, principal, seq),
            )
            self._bump_generation(cur, domain_id, "retention_basis", region_id)
            return obligation_id
        self._auto_commit(domain_id, "PROTECT_REGION_OBLIGATION", obligation_id, request, mutate)
        return obligation_id

    def _source_can_supply_dimension_excluding(self, domain_id: str, representation_id: str, dimension: str, excluded: set[str], visited: set[str] | None = None) -> bool:
        if representation_id in excluded:
            return False
        seen = set() if visited is None else visited
        if representation_id in seen:
            return False
        seen.add(representation_id)
        row = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, representation_id)).fetchone()
        if not row or row["invalidated_seq"] is not None or row["tainted_seq"] is not None:
            return False
        state = json.loads(row["loss_json"]).get(dimension, LossState.UNKNOWN.value)
        if state in {LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value}:
            return True
        if dimension not in set(json.loads(row["recoverable_json"])):
            return False
        return any(
            self._source_can_supply_dimension_excluding(domain_id, sid, dimension, excluded, set(seen))
            for sid in json.loads(row["source_representation_ids_json"])
        )

    def _family_covered_without(self, domain_id: str, region_id: str, family: str, excluded: set[str]) -> bool:
        req = self._family_requirements(family)
        rows = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND region_id=? AND invalidated_seq IS NULL AND tainted_seq IS NULL",
            (domain_id, region_id),
        ).fetchall()
        exact_states = {LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value}
        for row in rows:
            rid = row["representation_id"]
            if rid in excluded:
                continue
            loss = json.loads(row["loss_json"])
            if all(loss.get(dim) in exact_states for dim in req):
                return True
            ok = True
            for dim in req:
                if loss.get(dim) in exact_states:
                    continue
                if not self._source_can_supply_dimension_excluding(domain_id, rid, dim, excluded):
                    ok = False; break
            if ok:
                return True
        return False

    def consider_delete_representation(
        self, domain_id: str, representation_id: str, *, principal: str,
        allow_irreversible: bool = False, policy_ref: str = "retention-policy",
    ) -> RetentionDecision:
        row = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, representation_id)).fetchone()
        if not row:
            raise KeyError(representation_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("cannot delete inaccessible representation")
        region_id = row["region_id"]
        families = sorted({
            r[0] for r in self.db.execute(
                "SELECT query_family FROM protected_obligations WHERE domain_id=? AND region_id=?",
                (domain_id, region_id),
            ).fetchall()
        })
        uncovered = [f for f in families if not self._family_covered_without(domain_id, region_id, f, {representation_id})]
        if uncovered and not allow_irreversible:
            raise MemoryRetentionBlocked(f"deletion would uncover protected families: {', '.join(uncovered)}")

        if row["invalidated_seq"] is None:
            self.invalidate_representation(domain_id, representation_id, principal=principal)
        debt_id = None
        status = "SAFE_DELETE"
        if uncovered:
            status = "IRREVERSIBLE_GAP"
            debt = self.create_semantic_debt(
                domain_id, subject_kind="region", subject_id=region_id,
                kind="SOURCE_RECOVERABILITY_LOST", severity="high",
                evidence_needed="new authorized evidence or policy change",
                consequence=f"protected families irrecoverable: {','.join(uncovered)}",
                principal=principal,
            )
            debt_id = debt.debt_id
        retention_event_id = f"ret_{uuid.uuid4().hex}"
        decision_id = f"retdec_{uuid.uuid4().hex}"
        request = {
            "representation_id": representation_id, "policy_ref": policy_ref,
            "allow_irreversible": allow_irreversible, "uncovered": uncovered, "principal": principal,
        }
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO retention_events(retention_event_id,domain_id,target_kind,target_id,mode,policy_ref,authority_principal,created_seq) VALUES(?,?,?,?,?,?,?,?)",
                (retention_event_id, domain_id, "representation", representation_id,
                 "HARD_DELETE" if allow_irreversible else "DROP_REDUNDANT_WITNESS", policy_ref, principal, seq),
            )
            cur.execute(
                "INSERT INTO retention_decisions(decision_id,domain_id,target_kind,target_id,status,protected_families_json,uncovered_families_json,debt_id,created_seq) VALUES(?,?,?,?,?,?,?,?,?)",
                (decision_id, domain_id, "representation", representation_id, status,
                 canonical_json(families), canonical_json(uncovered), debt_id, seq),
            )
            self._bump_generation(cur, domain_id, "retention", region_id)
            return decision_id
        self._auto_commit(domain_id, "RETENTION_DECISION", decision_id, request, mutate)
        seq = self.head(domain_id).sequence
        return RetentionDecision(decision_id, domain_id, "representation", representation_id, status, families, uncovered, debt_id, seq)

    # ---------- conservative migration / longitudinal probes ----------

    def import_legacy_representation(
        self, domain_id: str, region_id: str, *, source_kind: str, source_id: str,
        payload: Any, dimensions: set[str], principal: str,
    ) -> str:
        rep = self.add_representation(
            domain_id, region_id, kind=source_kind, payload=payload,
            loss={d: LossState.UNKNOWN for d in dimensions}, recoverable=set(), token_cost=max(1, len(canonical_json(payload)) // 4),
            principal=principal, transform_kind="LEGACY_UNKNOWN_TRANSFORM", transform_profile="legacy-unknown",
        )
        debt = self.create_semantic_debt(
            domain_id, subject_kind="representation", subject_id=rep,
            kind="MISSING_LEGACY_PROVENANCE", severity="medium",
            evidence_needed="source lineage and preservation verification",
            consequence="legacy representation cannot claim exactness",
            principal=principal,
        )
        import_id = f"legacy_{digest([domain_id, source_kind, source_id, rep])[:24]}"
        request = {"source_kind": source_kind, "source_id": source_id, "representation_id": rep, "debt_id": debt.debt_id, "principal": principal}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO legacy_imports(import_id,domain_id,source_kind,source_id,representation_id,debt_id,created_seq) VALUES(?,?,?,?,?,?,?)",
                (import_id, domain_id, source_kind, source_id, rep, debt.debt_id, seq),
            )
            return import_id
        self._auto_commit(domain_id, "IMPORT_LEGACY_REPRESENTATION", import_id, request, mutate)
        return rep

    def capture_probe_checkpoint(self, domain_id: str, label: str) -> ProbeCheckpoint:
        cut = self.head(domain_id)
        vector = {
            "evidence_events": int(self.db.execute("SELECT COUNT(*) FROM evidence WHERE domain_id=?", (domain_id,)).fetchone()[0]),
            "current_claims": int(self.db.execute("SELECT COUNT(*) FROM claims WHERE domain_id=? AND superseded_seq IS NULL", (domain_id,)).fetchone()[0]),
            "regions": int(self.db.execute("SELECT COUNT(*) FROM regions WHERE domain_id=? AND invalidated_seq IS NULL", (domain_id,)).fetchone()[0]),
            "current_representations": int(self.db.execute("SELECT COUNT(*) FROM representations WHERE domain_id=? AND invalidated_seq IS NULL AND tainted_seq IS NULL", (domain_id,)).fetchone()[0]),
            "open_debts": int(self.db.execute("SELECT COUNT(*) FROM semantic_debts WHERE domain_id=? AND outcome IN (?,?,?)", (domain_id, *_OPEN_DEBT_STATES)).fetchone()[0]),
            "unresolved_counterexamples": int(self.db.execute("SELECT COUNT(*) FROM query_counterexamples WHERE domain_id=? AND resolved_seq IS NULL", (domain_id,)).fetchone()[0]),
        }
        checkpoint_id = f"probe_{uuid.uuid4().hex}"
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        self.db.execute(
            "INSERT INTO probe_checkpoints(checkpoint_id,domain_id,label,cut_json,vector_json,created_at) VALUES(?,?,?,?,?,?)",
            (checkpoint_id, domain_id, label, canonical_json(asdict(cut)), canonical_json(vector), created_at),
        )
        return ProbeCheckpoint(checkpoint_id, domain_id, label, cut, vector, created_at)

    # ---------- semantic-region evolution ----------

    def split_region(self, domain_id: str, region_id: str, successor_semantic_keys: list[str], *, principal: str) -> RegionEvolutionReceipt:
        old = self.db.execute("SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)).fetchone()
        if not old: raise KeyError(region_id)
        if not self._is_allowed(principal, old["allowed_principals_json"]): raise MemoryScopeBlocked("cannot split inaccessible region")
        keys = sorted(set(successor_semantic_keys))
        if len(keys) < 2: raise ValueError("split requires at least two decision-distinct successors")
        successors = [f"region_{digest([domain_id, key])[:24]}" for key in keys]
        evolution_id = f"region_evo_{uuid.uuid4().hex}"
        request = {"kind": "SPLIT", "predecessors": [region_id], "successor_keys": keys}
        def mutate(cur, seq):
            for key, rid in zip(keys, successors):
                existing = cur.execute("SELECT * FROM regions WHERE domain_id=? AND semantic_key=?", (domain_id, key)).fetchone()
                if existing and existing["region_id"] != rid: raise MemoryTransitionIncomplete("successor identity collision")
                if not existing:
                    cur.execute("INSERT INTO regions(region_id,domain_id,semantic_key,principal,allowed_principals_json,created_seq,invalidated_seq) VALUES(?,?,?,?,?,?,NULL)",
                                (rid, domain_id, key, principal, old["allowed_principals_json"], seq))
                cur.execute("INSERT INTO region_successors(domain_id,predecessor_region_id,successor_region_id,evolution_id,created_seq) VALUES(?,?,?,?,?)",
                            (domain_id, region_id, rid, evolution_id, seq))
                self._bump_generation(cur, domain_id, "region", rid)
            cur.execute("INSERT INTO region_evolution(evolution_id,domain_id,kind,predecessor_region_ids_json,successor_region_ids_json,created_seq) VALUES(?,?,?,?,?,?)",
                        (evolution_id, domain_id, "SPLIT", canonical_json([region_id]), canonical_json(successors), seq))
            self._bump_generation(cur, domain_id, "region", region_id); self._bump_generation(cur, domain_id, "query_domain", "global")
            return evolution_id
        receipt = self._auto_commit(domain_id, "SPLIT_REGION", evolution_id, request, mutate)
        return RegionEvolutionReceipt(evolution_id, domain_id, "SPLIT", [region_id], successors, receipt.commit_seq)

    def merge_regions(self, domain_id: str, predecessor_region_ids: list[str], successor_semantic_key: str, *, principal: str) -> RegionEvolutionReceipt:
        predecessors = sorted(set(predecessor_region_ids))
        if len(predecessors) < 2: raise ValueError("merge requires at least two predecessors")
        rows = []
        for rid in predecessors:
            row = self.db.execute("SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, rid)).fetchone()
            if not row: raise KeyError(rid)
            if not self._is_allowed(principal, row["allowed_principals_json"]): raise MemoryScopeBlocked("cannot merge inaccessible region")
            rows.append(row)
        successor = f"region_{digest([domain_id, successor_semantic_key])[:24]}"; evolution_id = f"region_evo_{uuid.uuid4().hex}"
        allowed = sorted(set.intersection(*(set(json.loads(r["allowed_principals_json"])) for r in rows))) or [principal]
        request = {"kind": "MERGE", "predecessors": predecessors, "successor_key": successor_semantic_key}
        def mutate(cur, seq):
            existing = cur.execute("SELECT * FROM regions WHERE domain_id=? AND semantic_key=?", (domain_id, successor_semantic_key)).fetchone()
            if not existing:
                cur.execute("INSERT INTO regions(region_id,domain_id,semantic_key,principal,allowed_principals_json,created_seq,invalidated_seq) VALUES(?,?,?,?,?,?,NULL)",
                            (successor, domain_id, successor_semantic_key, principal, canonical_json(allowed), seq))
            for rid in predecessors:
                cur.execute("INSERT INTO region_successors(domain_id,predecessor_region_id,successor_region_id,evolution_id,created_seq) VALUES(?,?,?,?,?)",
                            (domain_id, rid, successor, evolution_id, seq))
                self._bump_generation(cur, domain_id, "region", rid)
            cur.execute("INSERT INTO region_evolution(evolution_id,domain_id,kind,predecessor_region_ids_json,successor_region_ids_json,created_seq) VALUES(?,?,?,?,?,?)",
                        (evolution_id, domain_id, "MERGE", canonical_json(predecessors), canonical_json([successor]), seq))
            self._bump_generation(cur, domain_id, "region", successor); self._bump_generation(cur, domain_id, "query_domain", "global")
            return evolution_id
        receipt=self._auto_commit(domain_id,"MERGE_REGIONS",evolution_id,request,mutate)
        return RegionEvolutionReceipt(evolution_id, domain_id, "MERGE", predecessors, [successor], receipt.commit_seq)

    def resolve_current_region(self, domain_id: str, region_id: str) -> str:
        successors = [r[0] for r in self.db.execute(
            "SELECT successor_region_id FROM region_successors WHERE domain_id=? AND predecessor_region_id=? ORDER BY created_seq DESC,successor_region_id",
            (domain_id, region_id)).fetchall()]
        # Keep only successors from the newest evolution for this predecessor.
        newest = self.db.execute("SELECT MAX(created_seq) FROM region_successors WHERE domain_id=? AND predecessor_region_id=?", (domain_id, region_id)).fetchone()[0]
        if newest is None: return region_id
        successors = [r[0] for r in self.db.execute("SELECT successor_region_id FROM region_successors WHERE domain_id=? AND predecessor_region_id=? AND created_seq=? ORDER BY successor_region_id", (domain_id, region_id, newest)).fetchall()]
        if len(successors) == 1: return successors[0]
        raise MemoryAmbiguousSuccessors(f"region {region_id} has current successors {successors}")

    # ---------- Semantic-OCC representation proposals ----------

    def create_representation_proposal(
        self, domain_id: str, region_id: str, *, source_representation_ids: list[str], kind: str, payload: Any,
        loss: dict[str, LossState | str], recoverable: set[str], token_cost: int, principal: str,
        transform_profile: str = "default", transform_kind: str = "PURE",
    ) -> RepresentationProposal:
        region = self.db.execute("SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)).fetchone()
        if not region: raise KeyError(region_id)
        if not self._is_allowed(principal, region["allowed_principals_json"]): raise MemoryScopeBlocked("proposal region inaccessible")
        deps = [Dependency("region", region_id, self._generation(domain_id, "region", region_id)),
                Dependency("access", "global", self._generation(domain_id, "access", "global")),
                Dependency("regime", "global", self._generation(domain_id, "regime", "global")),
                Dependency("transform_profile", transform_profile, self._generation(domain_id, "transform_profile", transform_profile))]
        for sid in sorted(set(source_representation_ids)):
            src = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, sid)).fetchone()
            if not src or src["invalidated_seq"] is not None or src["tainted_seq"] is not None: raise MemoryTransitionIncomplete(f"proposal source unavailable {sid}")
            if not self._is_allowed(principal, src["allowed_principals_json"]): raise MemoryScopeBlocked("proposal source inaccessible")
            deps.append(Dependency("representation", sid, self._generation(domain_id, "representation", sid)))
        loss_norm = {k:(v.value if isinstance(v,LossState) else str(v)) for k,v in loss.items()}
        proposal_id=f"proposal_{uuid.uuid4().hex}"; now=self._clock(); created_at=now.astimezone(timezone.utc).isoformat().replace("+00:00","Z") if now.tzinfo else now.replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z")
        allowed=json.loads(region["allowed_principals_json"])
        self.db.execute("INSERT INTO representation_proposals(proposal_id,domain_id,region_id,kind,payload_json,payload_digest,source_representation_ids_json,loss_json,recoverable_json,token_cost,principal,allowed_principals_json,transform_kind,transform_profile,dependencies_json,created_at,invalidated_seq,promoted_representation_id,promoted_seq,verification_receipt_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
                        (proposal_id,domain_id,region_id,kind,canonical_json(payload),digest(payload),canonical_json(sorted(set(source_representation_ids))),canonical_json(loss_norm),canonical_json(sorted(recoverable)),token_cost,principal,canonical_json(allowed),transform_kind,transform_profile,canonical_json([asdict(d) for d in deps]),created_at))
        return RepresentationProposal(proposal_id,domain_id,region_id,kind,sorted(set(source_representation_ids)),transform_profile,digest(payload),deps,created_at,None)

    def verify_representation_proposal(
        self, domain_id: str, proposal_id: str, *, principal: str, verifier_ref: str,
        coverage: str, preservation: str, faithfulness: str,
    ) -> TransitionVerificationReceipt:
        row = self.db.execute(
            "SELECT * FROM representation_proposals WHERE proposal_id=? AND domain_id=?",
            (proposal_id, domain_id),
        ).fetchone()
        if not row:
            raise KeyError(proposal_id)
        if row["principal"] != principal or not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("proposal verification principal mismatch")
        deps = [Dependency(**x) for x in json.loads(row["dependencies_json"])]
        try:
            self.validate_dependencies(domain_id, deps)
        except MemoryDependencyStale as exc:
            raise MemoryProposalStale(str(exc)) from exc
        values = [str(coverage).upper(), str(preservation).upper(), str(faithfulness).upper()]
        status = "VERIFIED" if values == ["PASS", "PASS", "PASS"] else "INCOMPLETE"
        receipt_id = f"verify_{uuid.uuid4().hex}"
        now = self._clock()
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if now.tzinfo else now.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        self.db.execute(
            "INSERT INTO transition_verifications(receipt_id,proposal_id,domain_id,verifier_ref,coverage,preservation,faithfulness,status,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (receipt_id, proposal_id, domain_id, verifier_ref, values[0], values[1], values[2], status,
             canonical_json([asdict(d) for d in deps]), created_at),
        )
        self.db.execute(
            "UPDATE representation_proposals SET verification_receipt_id=? WHERE proposal_id=?",
            (receipt_id, proposal_id),
        )
        return TransitionVerificationReceipt(
            receipt_id, proposal_id, domain_id, verifier_ref, values[0], values[1], values[2],
            status, deps, created_at,
        )

    def promote_representation_proposal(self, proposal_id: str, *, principal: str) -> str:
        row=self.db.execute("SELECT * FROM representation_proposals WHERE proposal_id=?",(proposal_id,)).fetchone()
        if not row: raise KeyError(proposal_id)
        if row["promoted_representation_id"]: return row["promoted_representation_id"]
        if row["invalidated_seq"] is not None: raise MemoryProposalStale("proposal was invalidated")
        if row["principal"] != principal: raise MemoryScopeBlocked("proposal principal mismatch")
        verification_id = row["verification_receipt_id"]
        if not verification_id:
            raise MemoryTransitionIncomplete("proposal has no transition verification receipt")
        verification = self.db.execute(
            "SELECT * FROM transition_verifications WHERE receipt_id=? AND proposal_id=?",
            (verification_id, proposal_id),
        ).fetchone()
        if not verification or verification["status"] != "VERIFIED":
            raise MemoryTransitionIncomplete("proposal transition verification is incomplete")
        domain_id=row["domain_id"]; deps=[Dependency(**x) for x in json.loads(row["dependencies_json"])]
        verification_deps=[Dependency(**x) for x in json.loads(verification["dependencies_json"])]
        rep_id=f"rep_{digest([proposal_id,row['payload_digest']])[:24]}"
        request={"proposal_id":proposal_id,"payload_digest":row["payload_digest"],"dependency_digest":digest([asdict(d) for d in deps])}
        def mutate(cur,seq):
            try: self.validate_dependencies(domain_id,deps,cur=cur)
            except MemoryDependencyStale as exc: raise MemoryProposalStale(str(exc)) from exc
            try: self.validate_dependencies(domain_id,verification_deps,cur=cur)
            except MemoryDependencyStale as exc: raise MemoryProposalStale(f"verification stale: {exc}") from exc
            current=cur.execute("SELECT * FROM representation_proposals WHERE proposal_id=?",(proposal_id,)).fetchone()
            if current["invalidated_seq"] is not None: raise MemoryProposalStale("proposal invalidated before promotion")
            source_ids=json.loads(current["source_representation_ids_json"]); loss=json.loads(current["loss_json"]); recoverable=set(json.loads(current["recoverable_json"]))
            for sid in source_ids:
                src=cur.execute("SELECT * FROM representations WHERE representation_id=?",(sid,)).fetchone()
                if not src or src["invalidated_seq"] is not None or src["tainted_seq"] is not None: raise MemoryProposalStale(f"source {sid} no longer usable")
            if current["transform_kind"]=="PURE":
                for dim,state in loss.items():
                    if state in (LossState.PRESERVED_EXACT.value,LossState.PRESERVED_NORMALIZED.value) and source_ids and not any(self._source_can_supply_dimension(cur,domain_id,sid,dim) for sid in source_ids):
                        raise MemoryProposalStale(f"proposal lost restoring basis for {dim}")
            cur.execute("INSERT INTO representations(representation_id,domain_id,region_id,kind,payload_json,source_representation_ids_json,transform_kind,loss_json,recoverable_json,token_cost,principal,allowed_principals_json,created_seq,invalidated_seq,source_evidence_ids_json,transform_profile,tainted_seq) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,'[]',?,NULL)",
                        (rep_id,domain_id,current["region_id"],current["kind"],current["payload_json"],current["source_representation_ids_json"],current["transform_kind"],current["loss_json"],current["recoverable_json"],current["token_cost"],principal,current["allowed_principals_json"],seq,current["transform_profile"]))
            cur.execute("UPDATE representation_proposals SET promoted_representation_id=?,promoted_seq=? WHERE proposal_id=?",(rep_id,seq,proposal_id))
            self._bump_generation(cur,domain_id,"representation",rep_id); self._bump_generation(cur,domain_id,"region",current["region_id"]); self._bump_generation(cur,domain_id,"query_domain","global")
            return rep_id
        return self._auto_commit(domain_id,"PROMOTE_REPRESENTATION_PROPOSAL",rep_id,request,mutate).object_id

