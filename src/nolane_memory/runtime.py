from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .errors import (
    ActionArgumentMismatch,
    IdempotencyConflict,
    MemoryDependencyStale,
    MemoryFenceBindingMismatch,
    MemoryFenceExpired, MemoryClockAuthorityRequired,
    MemoryFenceReplay,
    MemoryIdentityCollision,
    MemoryIntegrityError,
    MemoryFlowBlocked,
    MemoryFlowPolicyCurrentnessUnknown,
    MemoryUseValidationUnavailable,
    MemoryQueryCapabilityUnsupported,
    MemoryRecallAmbiguous,
    MemoryRecallInsufficient,
    MemoryScopeBlocked,
    MemoryStaleWriter,
    MemoryTransitionIncomplete,
    MemoryViewOverflow,
    MemoryWriteConflict,
)
from .normalize import canonical_json, chain_root, digest
from .evolution import EvolutionMixin
from .effects_security import EffectsSecurityMixin
from .continuity import ContinuityMixin
from .research import ResearchMixin
from .governance import GovernanceMixin
from .extraction import ExtractionMixin
from .learning import LearningMixin
from .types import (
    Answerability,
    CommitReceipt,
    Dependency,
    FrameFragment,
    LossState,
    MemoryUseFence,
    MemoryAuthorityDomainRevision,
    MemoryWriterFenceRevision,
    MemoryWriteIntentRevision,
    PreservationCertificate,
    RecallBoundaryDescriptor,
    RecallCut,
    RecallFrame,
    RecallFrameDependencyManifestRevision,
    RecallObligation,
    RecallRole,
    RecallSufficiencyAssessment,
    RepresentationResolution,
)


GENESIS_ROOT = "0" * 64


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_dt(s: str | None) -> datetime | None:
    if s is None:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _json_load(s: str | None, default: Any = None) -> Any:
    return default if s is None else json.loads(s)


class MemoryRuntime(GovernanceMixin, ExtractionMixin, LearningMixin, EvolutionMixin, EffectsSecurityMixin, ContinuityMixin, ResearchMixin):
    """Deterministic K0-K2 reference runtime with v0.6.3 semantic OCC fencing.

    The implementation is intentionally conservative: correctness state lives in
    SQLite; derived selection is deterministic; no LLM is required for authority.
    """

    def __init__(
        self, path: str, *, clock: Callable[[], datetime] | None = None,
        clock_authority_id: str | None = "runtime-wall", clock_epoch: str | None = None,
    ):
        self.path = str(Path(path))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock or _utcnow
        self._clock_authority_id = clock_authority_id
        self._clock_epoch = (clock_epoch or f"boot_{uuid.uuid4().hex}") if clock_authority_id is not None else None
        self._lock = threading.RLock()
        self._fault_injector: Callable[[str, dict[str, Any]], None] | None = None
        self.db = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self._init_schema()

    def set_fault_injector(self, injector: Callable[[str, dict[str, Any]], None] | None) -> None:
        """Install a deterministic crash/fault hook for transaction-boundary testing.

        Production runtimes leave this unset. The hook is intentionally placed at
        semantic durability boundaries so acceptance tests can prove rollback and
        lost-response reconciliation properties against the real SQLite transaction.
        """
        self._fault_injector = injector

    def _inject_fault(self, point: str, **context: Any) -> None:
        if self._fault_injector is not None:
            self._fault_injector(point, dict(context))

    def close(self) -> None:
        self.db.close()

    def _init_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS domains(
              domain_id TEXT PRIMARY KEY,
              incarnation INTEGER NOT NULL,
              sequence INTEGER NOT NULL,
              root TEXT NOT NULL,
              writer_epoch INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS authority_domain_revisions(
              domain_id TEXT NOT NULL,
              revision INTEGER NOT NULL,
              predecessor_revision INTEGER,
              incarnation INTEGER NOT NULL,
              writer_epoch INTEGER NOT NULL,
              sequence INTEGER NOT NULL,
              root TEXT NOT NULL,
              action TEXT NOT NULL,
              reason TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY(domain_id, revision),
              UNIQUE(domain_id, incarnation)
            );
            CREATE TABLE IF NOT EXISTS writer_fence_revisions(
              domain_id TEXT NOT NULL,
              writer_epoch INTEGER NOT NULL,
              predecessor_epoch INTEGER,
              incarnation INTEGER NOT NULL,
              reason TEXT NOT NULL,
              created_at TEXT NOT NULL,
              created_sequence INTEGER NOT NULL,
              PRIMARY KEY(domain_id, writer_epoch)
            );
            CREATE TABLE IF NOT EXISTS operations(
              domain_id TEXT NOT NULL,
              operation_id TEXT NOT NULL,
              request_digest TEXT NOT NULL,
              receipt_json TEXT NOT NULL,
              PRIMARY KEY(domain_id, operation_id)
            );
            CREATE TABLE IF NOT EXISTS operation_receipts(
              domain_id TEXT NOT NULL,
              incarnation INTEGER NOT NULL,
              operation_id TEXT NOT NULL,
              request_digest TEXT NOT NULL,
              receipt_json TEXT NOT NULL,
              PRIMARY KEY(domain_id, incarnation, operation_id)
            );
            CREATE TABLE IF NOT EXISTS write_intents(
              domain_id TEXT NOT NULL,
              incarnation INTEGER NOT NULL,
              operation_id TEXT NOT NULL,
              request_digest TEXT NOT NULL,
              kind TEXT NOT NULL,
              object_id TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL,
              expires_at TEXT,
              reconciled_at TEXT,
              commit_seq INTEGER,
              receipt_json TEXT,
              last_error TEXT,
              PRIMARY KEY(domain_id, incarnation, operation_id)
            );
            CREATE INDEX IF NOT EXISTS idx_write_intents_status
              ON write_intents(domain_id,incarnation,status);
            CREATE TABLE IF NOT EXISTS incarnation_transitions(
              domain_id TEXT NOT NULL,
              operation_id TEXT NOT NULL,
              request_digest TEXT NOT NULL,
              cut_json TEXT NOT NULL,
              PRIMARY KEY(domain_id, operation_id)
            );
            CREATE TABLE IF NOT EXISTS journal(
              domain_id TEXT NOT NULL,
              sequence INTEGER NOT NULL,
              kind TEXT NOT NULL,
              object_id TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              previous_root TEXT NOT NULL,
              root TEXT NOT NULL,
              writer_epoch INTEGER NOT NULL,
              incarnation INTEGER NOT NULL DEFAULT 1,
              committed_at TEXT NOT NULL,
              PRIMARY KEY(domain_id, sequence)
            );
            CREATE TABLE IF NOT EXISTS evidence(
              evidence_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              source_event_identity TEXT NOT NULL,
              content_json TEXT NOT NULL,
              content_digest TEXT NOT NULL,
              principal TEXT NOT NULL,
              allowed_principals_json TEXT NOT NULL,
              world_time TEXT,
              observed_at TEXT NOT NULL,
              ingested_at TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              revoked_seq INTEGER,
              UNIQUE(domain_id, source_event_identity)
            );
            CREATE TABLE IF NOT EXISTS deliveries(
              domain_id TEXT NOT NULL,
              source_event_identity TEXT NOT NULL,
              delivery_id TEXT NOT NULL,
              seen_at TEXT NOT NULL,
              PRIMARY KEY(domain_id, source_event_identity, delivery_id)
            );
            CREATE TABLE IF NOT EXISTS claims(
              claim_revision_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              logical_id TEXT NOT NULL,
              proposition_json TEXT NOT NULL,
              proposition_digest TEXT NOT NULL,
              principal TEXT NOT NULL,
              allowed_principals_json TEXT NOT NULL,
              valid_from TEXT,
              valid_to TEXT,
              known_from TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              superseded_seq INTEGER,
              UNIQUE(domain_id, logical_id, claim_revision_id)
            );
            CREATE INDEX IF NOT EXISTS claims_current_idx ON claims(domain_id, logical_id, superseded_seq);
            CREATE TABLE IF NOT EXISTS justification_paths(
              path_id TEXT PRIMARY KEY,
              claim_revision_id TEXT NOT NULL,
              FOREIGN KEY(claim_revision_id) REFERENCES claims(claim_revision_id)
            );
            CREATE TABLE IF NOT EXISTS justification_members(
              path_id TEXT NOT NULL,
              evidence_id TEXT NOT NULL,
              PRIMARY KEY(path_id, evidence_id),
              FOREIGN KEY(path_id) REFERENCES justification_paths(path_id),
              FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id)
            );
            CREATE TABLE IF NOT EXISTS regions(
              region_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              semantic_key TEXT NOT NULL,
              principal TEXT NOT NULL,
              allowed_principals_json TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              invalidated_seq INTEGER,
              UNIQUE(domain_id, semantic_key)
            );
            CREATE TABLE IF NOT EXISTS query_families(
              family_id TEXT PRIMARY KEY,
              required_dimensions_json TEXT NOT NULL,
              revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS query_family_revisions(
              family_id TEXT NOT NULL,
              revision INTEGER NOT NULL,
              required_dimensions_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY(family_id,revision)
            );
            CREATE TABLE IF NOT EXISTS applicability_compatibility_profiles(
              revision INTEGER PRIMARY KEY,
              refinements_json TEXT NOT NULL,
              profile_digest TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preservation_certificates(
              certificate_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              representation_id TEXT NOT NULL,
              query_family TEXT NOT NULL,
              query_family_revision INTEGER NOT NULL,
              verifier_ref TEXT NOT NULL,
              status TEXT NOT NULL,
              missing_dimensions_json TEXT NOT NULL,
              dependencies_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS representations(
              representation_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              region_id TEXT NOT NULL,
              kind TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              source_representation_ids_json TEXT NOT NULL,
              transform_kind TEXT NOT NULL,
              loss_json TEXT NOT NULL,
              recoverable_json TEXT NOT NULL,
              token_cost INTEGER NOT NULL,
              principal TEXT NOT NULL,
              allowed_principals_json TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              invalidated_seq INTEGER
            );
            CREATE INDEX IF NOT EXISTS rep_region_idx ON representations(domain_id, region_id, created_seq);
            CREATE TABLE IF NOT EXISTS generations(
              domain_id TEXT NOT NULL,
              dep_class TEXT NOT NULL,
              dep_key TEXT NOT NULL,
              generation INTEGER NOT NULL,
              PRIMARY KEY(domain_id, dep_class, dep_key)
            );
            CREATE TABLE IF NOT EXISTS representation_resolutions(
              resolution_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, principal TEXT NOT NULL,
              role_json TEXT NOT NULL, cut_json TEXT NOT NULL, selected_representation_id TEXT,
              status TEXT NOT NULL, options_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recall_sufficiency_assessments(
              assessment_id TEXT PRIMARY KEY, frame_id TEXT NOT NULL, assessment_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS frame_dependency_manifests(
              manifest_id TEXT PRIMARY KEY, frame_id TEXT NOT NULL, domain_id TEXT NOT NULL, cut_json TEXT NOT NULL,
              dependencies_json TEXT NOT NULL, dependency_digest TEXT NOT NULL, completeness TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS frames(
              frame_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              principal TEXT NOT NULL,
              frame_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fences(
              fence_id TEXT PRIMARY KEY,
              frame_id TEXT NOT NULL,
              domain_id TEXT NOT NULL,
              principal TEXT NOT NULL,
              sink TEXT NOT NULL,
              payload_digest TEXT NOT NULL,
              dependency_digest TEXT NOT NULL,
              dependencies_json TEXT NOT NULL,
              issued_at TEXT NOT NULL,
              expires_at TEXT,
              consumed_at TEXT,
              clock_authority_id TEXT,
              clock_epoch TEXT,
              flow_receipt_id TEXT
            );
            CREATE TABLE IF NOT EXISTS causal_edges(
              src_domain TEXT NOT NULL,
              src_seq INTEGER NOT NULL,
              dst_domain TEXT NOT NULL,
              dst_seq INTEGER NOT NULL,
              PRIMARY KEY(src_domain, src_seq, dst_domain, dst_seq)
            );
            """
        )
        self._init_evolution_schema()
        self._init_effects_security_schema()
        self._init_continuity_schema()
        self._init_research_schema()
        self._init_governance_schema()
        self._init_extraction_schema()
        self._init_learning_schema()
        self._ensure_full_profile_columns()

    def _ensure_full_profile_columns(self) -> None:
        """Idempotent in-place schema hardening for older reference-kernel databases."""
        def ensure(table: str, column: str, ddl: str) -> None:
            cols = {row[1] for row in self.db.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                self.db.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
        ensure("representations", "source_evidence_ids_json", "source_evidence_ids_json TEXT NOT NULL DEFAULT '[]'")
        ensure("representations", "transform_profile", "transform_profile TEXT NOT NULL DEFAULT 'default'")
        ensure("representations", "tainted_seq", "tainted_seq INTEGER")
        ensure("representations", "hard_dependencies_json", "hard_dependencies_json TEXT NOT NULL DEFAULT '[]'")
        ensure("representations", "applicability_json", "applicability_json TEXT NOT NULL DEFAULT '{}'")
        ensure("evidence", "deleted_seq", "deleted_seq INTEGER")
        ensure("evidence", "erasure_policy_ref", "erasure_policy_ref TEXT")
        ensure("evidence", "compromised_seq", "compromised_seq INTEGER")
        ensure("evidence", "compromise_reason", "compromise_reason TEXT")
        ensure("journal", "incarnation", "incarnation INTEGER NOT NULL DEFAULT 1")
        ensure("prospective_triggers", "expires_at", "expires_at TEXT")
        ensure("prospective_triggers", "causal_frontier_json", "causal_frontier_json TEXT NOT NULL DEFAULT '{}'")
        ensure("prospective_triggers", "source_representation_ids_json", "source_representation_ids_json TEXT NOT NULL DEFAULT '[]'")
        ensure("prospective_triggers", "reactivated_seq", "reactivated_seq INTEGER")
        ensure("prospective_triggers", "revoke_reason", "revoke_reason TEXT")
        ensure("prospective_triggers", "reactivation_reason", "reactivation_reason TEXT")
        ensure("effect_evidence", "exposure_id", "exposure_id TEXT")
        ensure("publication_sagas", "publication_policy_id", "publication_policy_id TEXT")
        ensure("publication_sagas", "publication_policy_revision", "publication_policy_revision INTEGER")
        ensure("publication_sagas", "publication_policy_generation", "publication_policy_generation INTEGER NOT NULL DEFAULT 0")
        ensure("access_profiles", "expires_at", "expires_at TEXT")
        ensure("access_profile_revisions", "expires_at", "expires_at TEXT")
        ensure("declassification_receipts", "expires_at", "expires_at TEXT")
        ensure("integrity_authority_profiles", "expires_at", "expires_at TEXT")
        ensure("publication_policies", "expires_at", "expires_at TEXT")
        ensure("negative_query_receipts", "query_domain_id", "query_domain_id TEXT")
        ensure("claims", "applicability_json", "applicability_json TEXT NOT NULL DEFAULT '{}'")
        ensure("fences", "clock_authority_id", "clock_authority_id TEXT")
        ensure("fences", "clock_epoch", "clock_epoch TEXT")
        ensure("fences", "flow_receipt_id", "flow_receipt_id TEXT")
        # Legacy databases may lack the authority-domain history owner. Preserve the
        # current state as a conservative baseline revision instead of inventing past
        # incarnation transitions that were never recorded in this schema.
        self.db.execute(
            "INSERT OR IGNORE INTO authority_domain_revisions(domain_id,revision,predecessor_revision,incarnation,writer_epoch,sequence,root,action,reason,created_at) "
            "SELECT domain_id,1,NULL,incarnation,writer_epoch,sequence,root,'LEGACY_BASELINE','LEGACY_BACKFILL',created_at FROM domains"
        )
        # A writer fence is the immutable history owner; domains.writer_epoch is only
        # the current hot-path mirror. Backfill legacy databases conservatively.
        self.db.execute(
            "INSERT OR IGNORE INTO writer_fence_revisions(domain_id,writer_epoch,predecessor_epoch,incarnation,reason,created_at,created_sequence) "
            "SELECT domain_id,writer_epoch,NULL,incarnation,'LEGACY_BACKFILL',created_at,sequence FROM domains"
        )
        # Older alpha databases used domain-scoped idempotency. Import those receipts
        # into incarnation 1; all new writes are incarnation-scoped to prevent ABA.
        self.db.execute(
            "INSERT OR IGNORE INTO operation_receipts(domain_id,incarnation,operation_id,request_digest,receipt_json) "
            "SELECT domain_id,1,operation_id,request_digest,receipt_json FROM operations"
        )

    # ---------- canonical commit substrate ----------

    def create_domain(self, domain_id: str, *, writer_epoch: int = 1, incarnation: int = 1) -> None:
        now = _iso(self._clock())
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT * FROM domains WHERE domain_id=?", (domain_id,)).fetchone()
                if row:
                    if int(row["writer_epoch"]) != writer_epoch or int(row["incarnation"]) != incarnation:
                        raise MemoryWriteConflict(f"domain {domain_id!r} already exists with different epoch/incarnation")
                    self.db.execute("COMMIT")
                    return
                self.db.execute(
                    "INSERT INTO domains(domain_id,incarnation,sequence,root,writer_epoch,created_at) VALUES(?,?,?,?,?,?)",
                    (domain_id, incarnation, 0, GENESIS_ROOT, writer_epoch, now),
                )
                self.db.execute(
                    "INSERT INTO authority_domain_revisions(domain_id,revision,predecessor_revision,incarnation,writer_epoch,sequence,root,action,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (domain_id, 1, None, incarnation, writer_epoch, 0, GENESIS_ROOT, "CREATE", "DOMAIN_CREATE", now),
                )
                self.db.execute(
                    "INSERT INTO writer_fence_revisions(domain_id,writer_epoch,predecessor_epoch,incarnation,reason,created_at,created_sequence) VALUES(?,?,?,?,?,?,?)",
                    (domain_id, writer_epoch, None, incarnation, "DOMAIN_CREATE", now, 0),
                )
                for dep_class, dep_key in (
                    ("access", "global"), ("policy", "global"), ("regime", "global"),
                    ("tool", "global"), ("hard_obligation", "global"), ("query_domain", "global"),
                    ("incarnation", "global"),
                ):
                    self.db.execute(
                        "INSERT OR IGNORE INTO generations(domain_id,dep_class,dep_key,generation) VALUES(?,?,?,0)",
                        (domain_id, dep_class, dep_key),
                    )
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def _authority_domain_from_row(self, row: sqlite3.Row) -> MemoryAuthorityDomainRevision:
        return MemoryAuthorityDomainRevision(
            domain_id=row["domain_id"], revision=int(row["revision"]),
            predecessor_revision=None if row["predecessor_revision"] is None else int(row["predecessor_revision"]),
            incarnation=int(row["incarnation"]), writer_epoch=int(row["writer_epoch"]),
            sequence=int(row["sequence"]), root=row["root"], action=row["action"],
            reason=row["reason"], created_at=row["created_at"],
        )

    def list_authority_domain_revisions(self, domain_id: str) -> list[MemoryAuthorityDomainRevision]:
        rows = self.db.execute(
            "SELECT * FROM authority_domain_revisions WHERE domain_id=? ORDER BY revision", (domain_id,)
        ).fetchall()
        return [self._authority_domain_from_row(row) for row in rows]

    def authority_domain_revision_at_sequence(self, domain_id: str, sequence: int) -> MemoryAuthorityDomainRevision:
        row = self.db.execute(
            "SELECT * FROM authority_domain_revisions WHERE domain_id=? AND sequence<=? ORDER BY sequence DESC,revision DESC LIMIT 1",
            (domain_id, int(sequence)),
        ).fetchone()
        if row is None:
            raise KeyError((domain_id, sequence))
        return self._authority_domain_from_row(row)

    def _writer_fence_from_row(self, row: sqlite3.Row) -> MemoryWriterFenceRevision:
        return MemoryWriterFenceRevision(
            domain_id=row["domain_id"], writer_epoch=int(row["writer_epoch"]),
            predecessor_epoch=None if row["predecessor_epoch"] is None else int(row["predecessor_epoch"]),
            incarnation=int(row["incarnation"]), reason=row["reason"],
            created_at=row["created_at"], created_sequence=int(row["created_sequence"]),
        )

    def list_writer_fence_revisions(self, domain_id: str) -> list[MemoryWriterFenceRevision]:
        rows = self.db.execute(
            "SELECT * FROM writer_fence_revisions WHERE domain_id=? ORDER BY writer_epoch", (domain_id,)
        ).fetchall()
        return [self._writer_fence_from_row(row) for row in rows]

    def writer_fence_at_epoch(self, domain_id: str, writer_epoch: int) -> MemoryWriterFenceRevision:
        row = self.db.execute(
            "SELECT * FROM writer_fence_revisions WHERE domain_id=? AND writer_epoch=?", (domain_id, writer_epoch)
        ).fetchone()
        if row is None:
            raise KeyError((domain_id, writer_epoch))
        return self._writer_fence_from_row(row)

    def advance_writer_epoch(self, domain_id: str, new_epoch: int, *, reason: str = "WRITER_FAILOVER") -> None:
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self._head_row(domain_id, self.db)
                old_epoch = int(row["writer_epoch"])
                if new_epoch <= old_epoch:
                    raise MemoryStaleWriter("new writer epoch must increase")
                now = _iso(self._clock())
                self.db.execute(
                    "INSERT INTO writer_fence_revisions(domain_id,writer_epoch,predecessor_epoch,incarnation,reason,created_at,created_sequence) VALUES(?,?,?,?,?,?,?)",
                    (domain_id, new_epoch, old_epoch, int(row["incarnation"]), reason, now, int(row["sequence"])),
                )
                self.db.execute("UPDATE domains SET writer_epoch=? WHERE domain_id=?", (new_epoch, domain_id))
                self.db.execute("COMMIT")
            except Exception:
                if self.db.in_transaction:
                    self.db.execute("ROLLBACK")
                raise

    def start_new_incarnation(
        self, domain_id: str, *, principal: str, reason: str, operation_id: str | None = None,
    ) -> RecallCut:
        """Create a new active authority-domain incarnation without time-travel.

        Sequence/root history remains monotonic, but old idempotency receipts and
        projection leases are scoped away by the new incarnation identity.
        """
        with self._lock:
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                op_id = operation_id or f"internal:new-incarnation:{uuid.uuid4().hex}"
                semantic_request = {"principal": principal, "reason": reason}
                semantic_digest = digest(semantic_request)
                previous = cur.execute(
                    "SELECT request_digest,cut_json FROM incarnation_transitions WHERE domain_id=? AND operation_id=?",
                    (domain_id, op_id),
                ).fetchone()
                if previous:
                    if previous["request_digest"] != semantic_digest:
                        raise IdempotencyConflict(
                            f"incarnation transition operation {op_id!r} reused with different semantic request"
                        )
                    cut = RecallCut(**json.loads(previous["cut_json"]))
                    cur.execute("COMMIT")
                    return cut
                head = self._head_row(domain_id, cur)
                old_inc = int(head["incarnation"])
                new_inc = old_inc + 1
                old_epoch = int(head["writer_epoch"])
                new_epoch = old_epoch + 1
                seq = int(head["sequence"]) + 1
                req = {
                    "principal": principal,
                    "reason": reason,
                    "from_incarnation": old_inc,
                    "to_incarnation": new_inc,
                }
                req_digest = digest(req)
                event = {
                    "domain_id": domain_id,
                    "sequence": seq,
                    "kind": "START_NEW_INCARNATION",
                    "object_id": domain_id,
                    "request_digest": req_digest,
                }
                previous_root = head["root"]
                root = chain_root(previous_root, event)
                committed_at = _iso(self._clock())
                cur.execute(
                    "INSERT INTO journal(domain_id,sequence,kind,object_id,payload_json,previous_root,root,writer_epoch,incarnation,committed_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (domain_id, seq, "START_NEW_INCARNATION", domain_id, canonical_json(req),
                     previous_root, root, old_epoch, new_inc, committed_at),
                )
                cur.execute(
                    "UPDATE domains SET incarnation=?,sequence=?,root=?,writer_epoch=? WHERE domain_id=?",
                    (new_inc, seq, root, new_epoch, domain_id),
                )
                latest_domain_revision = cur.execute(
                    "SELECT revision FROM authority_domain_revisions WHERE domain_id=? ORDER BY revision DESC LIMIT 1",
                    (domain_id,),
                ).fetchone()
                predecessor_revision = int(latest_domain_revision["revision"]) if latest_domain_revision else None
                new_domain_revision = 1 if predecessor_revision is None else predecessor_revision + 1
                cur.execute(
                    "INSERT INTO authority_domain_revisions(domain_id,revision,predecessor_revision,incarnation,writer_epoch,sequence,root,action,reason,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (domain_id, new_domain_revision, predecessor_revision, new_inc, new_epoch, seq, root, "NEW_INCARNATION", reason, committed_at),
                )
                cur.execute(
                    "INSERT INTO writer_fence_revisions(domain_id,writer_epoch,predecessor_epoch,incarnation,reason,created_at,created_sequence) VALUES(?,?,?,?,?,?,?)",
                    (domain_id, new_epoch, old_epoch, new_inc, "NEW_INCARNATION", committed_at, seq),
                )
                # A continuity artifact from a previous authority incarnation is history,
                # not a current-resume credential. Invalidate it at the incarnation barrier.
                cur.execute(
                    "UPDATE continuity_pins SET invalidated_seq=COALESCE(invalidated_seq,?) WHERE domain_id=?",
                    (seq, domain_id),
                )
                cur.execute(
                    "UPDATE handoff_packets SET invalidated_seq=COALESCE(invalidated_seq,?) WHERE domain_id=?",
                    (seq, domain_id),
                )
                self._bump_generation(cur, domain_id, "continuity", "global")
                self._bump_generation(cur, domain_id, "incarnation", "global")
                self._bump_generation(cur, domain_id, "hard_obligation", "global")
                self._bump_generation(cur, domain_id, "query_domain", "global")
                cut = RecallCut(domain_id, new_inc, seq, root)
                cur.execute(
                    "INSERT INTO incarnation_transitions(domain_id,operation_id,request_digest,cut_json) VALUES(?,?,?,?)",
                    (domain_id, op_id, semantic_digest, canonical_json(asdict(cut))),
                )
                cur.execute("COMMIT")
                return cut
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def _head_row(self, domain_id: str, cur: sqlite3.Connection | sqlite3.Cursor | None = None) -> sqlite3.Row:
        q = cur or self.db
        row = q.execute("SELECT * FROM domains WHERE domain_id=?", (domain_id,)).fetchone()
        if not row:
            raise MemoryIntegrityError(f"unknown domain {domain_id!r}")
        return row

    def head(self, domain_id: str) -> RecallCut:
        row = self._head_row(domain_id)
        return RecallCut(domain_id, int(row["incarnation"]), int(row["sequence"]), row["root"])

    def verify_integrity(self, domain_id: str) -> bool:
        """Recompute the canonical journal root chain for one authority domain.

        This verifies contiguous commit order, stored previous-root links, request digests,
        per-entry roots, and the domain head root. It deliberately checks canonical history
        rather than derived indexes, which may be rebuilt independently.
        """
        with self._lock:
            cur = self.db.cursor()
            cur.execute("BEGIN")
            try:
                head = self._head_row(domain_id, cur)
                rows = cur.execute(
                    "SELECT * FROM journal WHERE domain_id=? ORDER BY sequence ASC",
                    (domain_id,),
                ).fetchall()
                expected_seq = 1
                previous_root = GENESIS_ROOT
                for row in rows:
                    seq = int(row["sequence"])
                    if seq != expected_seq:
                        raise MemoryIntegrityError(
                            f"journal sequence gap for {domain_id}: expected {expected_seq}, got {seq}"
                        )
                    if row["previous_root"] != previous_root:
                        raise MemoryIntegrityError(
                            f"journal previous-root mismatch at {domain_id}@{seq}"
                        )
                    try:
                        request = json.loads(row["payload_json"])
                    except Exception as exc:
                        raise MemoryIntegrityError(
                            f"journal payload is not canonical JSON at {domain_id}@{seq}"
                        ) from exc
                    event = {
                        "domain_id": domain_id,
                        "sequence": seq,
                        "kind": row["kind"],
                        "object_id": row["object_id"],
                        "request_digest": digest(request),
                    }
                    calculated = chain_root(previous_root, event)
                    if row["root"] != calculated:
                        raise MemoryIntegrityError(f"journal root mismatch at {domain_id}@{seq}")
                    previous_root = calculated
                    expected_seq += 1
                if int(head["sequence"]) != len(rows):
                    raise MemoryIntegrityError(
                        f"domain head sequence {head['sequence']} does not match journal length {len(rows)}"
                    )
                if head["root"] != previous_root:
                    raise MemoryIntegrityError(f"domain head root mismatch for {domain_id}")
                cur.execute("COMMIT")
                return True
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def _receipt_from_json(self, s: str) -> CommitReceipt:
        return CommitReceipt(**json.loads(s))

    def _write_intent_from_row(self, row: sqlite3.Row) -> MemoryWriteIntentRevision:
        return MemoryWriteIntentRevision(
            domain_id=row["domain_id"], incarnation=int(row["incarnation"]),
            operation_id=row["operation_id"], request_digest=row["request_digest"],
            kind=row["kind"], object_id=row["object_id"], status=row["status"],
            created_at=row["created_at"], expires_at=row["expires_at"],
            reconciled_at=row["reconciled_at"],
            commit_seq=None if row["commit_seq"] is None else int(row["commit_seq"]),
            receipt_json=_json_load(row["receipt_json"]), last_error=row["last_error"],
        )

    def prepare_write_intent(
        self, domain_id: str, *, operation_id: str, kind: str, object_id: str,
        request: Any, expires_at: datetime | None = None,
    ) -> MemoryWriteIntentRevision:
        """Persist an immutable producer intent without changing canonical truth.

        Intents deliberately live outside the canonical sequence/root clock: a crash
        before semantic commit leaves a durable retry/reconciliation witness, not a
        partial truth transition. Identity is scoped by domain incarnation.
        """
        req_digest = digest(request)
        expiry = _iso(expires_at)
        with self._lock:
            head = self._head_row(domain_id)
            incarnation = int(head["incarnation"])
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT * FROM write_intents WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (domain_id, incarnation, operation_id),
                ).fetchone()
                if row:
                    if row["request_digest"] != req_digest or row["kind"] != kind or row["object_id"] != object_id:
                        raise IdempotencyConflict(
                            f"write intent {operation_id!r} reused with different semantic request"
                        )
                    if expiry is not None and row["expires_at"] not in (None, expiry):
                        raise IdempotencyConflict(
                            f"write intent {operation_id!r} reused with different expiry contract"
                        )
                    cur.execute("COMMIT")
                    return self._write_intent_from_row(row)
                created_at = _iso(self._clock())
                cur.execute(
                    "INSERT INTO write_intents(domain_id,incarnation,operation_id,request_digest,kind,object_id,status,created_at,expires_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (domain_id, incarnation, operation_id, req_digest, kind, object_id, "PENDING", created_at, expiry),
                )
                row = cur.execute(
                    "SELECT * FROM write_intents WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (domain_id, incarnation, operation_id),
                ).fetchone()
                cur.execute("COMMIT")
                return self._write_intent_from_row(row)
            except Exception:
                if self.db.in_transaction:
                    cur.execute("ROLLBACK")
                raise

    def get_write_intent(
        self, domain_id: str, operation_id: str, *, incarnation: int | None = None,
    ) -> MemoryWriteIntentRevision:
        if incarnation is None:
            incarnation = int(self._head_row(domain_id)["incarnation"])
        row = self.db.execute(
            "SELECT * FROM write_intents WHERE domain_id=? AND incarnation=? AND operation_id=?",
            (domain_id, int(incarnation), operation_id),
        ).fetchone()
        if row is None:
            raise KeyError(operation_id)
        return self._write_intent_from_row(row)

    def list_write_intents(
        self, domain_id: str, *, incarnation: int | None = None, status: str | None = None,
    ) -> list[MemoryWriteIntentRevision]:
        if incarnation is None:
            incarnation = int(self._head_row(domain_id)["incarnation"])
        sql = "SELECT * FROM write_intents WHERE domain_id=? AND incarnation=?"
        args: list[Any] = [domain_id, int(incarnation)]
        if status is not None:
            sql += " AND status=?"; args.append(status)
        sql += " ORDER BY created_at,operation_id"
        return [self._write_intent_from_row(row) for row in self.db.execute(sql, args).fetchall()]

    def reconcile_write_intent(
        self, domain_id: str, operation_id: str, *, incarnation: int | None = None,
    ) -> MemoryWriteIntentRevision:
        with self._lock:
            if incarnation is None:
                incarnation = int(self._head_row(domain_id)["incarnation"])
            cur = self.db.cursor(); cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT * FROM write_intents WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (domain_id, int(incarnation), operation_id),
                ).fetchone()
                if row is None:
                    raise KeyError(operation_id)
                receipt_row = cur.execute(
                    "SELECT request_digest,receipt_json FROM operation_receipts WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (domain_id, int(incarnation), operation_id),
                ).fetchone()
                now = _iso(self._clock())
                if receipt_row is not None:
                    if receipt_row["request_digest"] != row["request_digest"]:
                        raise IdempotencyConflict(f"write intent {operation_id!r} receipt digest mismatch")
                    receipt = self._receipt_from_json(receipt_row["receipt_json"])
                    cur.execute(
                        "UPDATE write_intents SET status='COMMITTED',reconciled_at=?,commit_seq=?,receipt_json=?,last_error=NULL "
                        "WHERE domain_id=? AND incarnation=? AND operation_id=?",
                        (now, receipt.commit_seq, receipt_row["receipt_json"], domain_id, int(incarnation), operation_id),
                    )
                elif row["status"] == "PENDING" and row["expires_at"] is not None:
                    if self._clock() >= (_parse_dt(row["expires_at"]) or self._clock()):
                        cur.execute(
                            "UPDATE write_intents SET status='EXPIRED',reconciled_at=? WHERE domain_id=? AND incarnation=? AND operation_id=?",
                            (now, domain_id, int(incarnation), operation_id),
                        )
                out = cur.execute(
                    "SELECT * FROM write_intents WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (domain_id, int(incarnation), operation_id),
                ).fetchone()
                cur.execute("COMMIT")
                return self._write_intent_from_row(out)
            except Exception:
                if self.db.in_transaction:
                    cur.execute("ROLLBACK")
                raise

    def _commit(
        self,
        *, domain_id: str, operation_id: str, expected_seq: int, writer_epoch: int,
        kind: str, object_id: str, request: Any,
        mutate: Callable[[sqlite3.Cursor, int], str | None],
    ) -> CommitReceipt:
        req_digest = digest(request)
        with self._lock:
            # Durable audit intent is committed independently of canonical truth so
            # pre-commit crashes leave a reconciliation witness rather than a torn write.
            self.prepare_write_intent(
                domain_id, operation_id=operation_id, kind=kind, object_id=object_id, request=request
            )
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                head = self._head_row(domain_id, cur)
                incarnation = int(head["incarnation"])
                existing = cur.execute(
                    "SELECT request_digest,receipt_json FROM operation_receipts WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (domain_id, incarnation, operation_id),
                ).fetchone()
                if existing:
                    if existing["request_digest"] != req_digest:
                        raise IdempotencyConflict(f"operation {operation_id!r} reused with different semantic request")
                    receipt = self._receipt_from_json(existing["receipt_json"])
                    cur.execute(
                        "UPDATE write_intents SET status='COMMITTED',reconciled_at=?,commit_seq=?,receipt_json=?,last_error=NULL "
                        "WHERE domain_id=? AND incarnation=? AND operation_id=?",
                        (_iso(self._clock()), receipt.commit_seq, existing["receipt_json"], domain_id, incarnation, operation_id),
                    )
                    cur.execute("COMMIT")
                    return receipt

                if int(head["writer_epoch"]) != writer_epoch:
                    raise MemoryStaleWriter(
                        f"writer epoch {writer_epoch} != current {head['writer_epoch']} for {domain_id}"
                    )
                if int(head["sequence"]) != expected_seq:
                    raise MemoryWriteConflict(
                        f"expected base {expected_seq}, current {head['sequence']} for {domain_id}"
                    )
                seq = expected_seq + 1
                fault_context = {
                    "domain_id": domain_id, "operation_id": operation_id,
                    "kind": kind, "sequence": seq, "incarnation": incarnation,
                }
                self._inject_fault("before_mutation", **fault_context)
                effective_object = mutate(cur, seq) or object_id
                self._inject_fault("after_mutation_before_journal", **fault_context, object_id=effective_object)
                event = {
                    "domain_id": domain_id,
                    "sequence": seq,
                    "kind": kind,
                    "object_id": effective_object,
                    "request_digest": req_digest,
                }
                previous_root = head["root"]
                root = chain_root(previous_root, event)
                committed_at = _iso(self._clock())
                cur.execute(
                    "INSERT INTO journal(domain_id,sequence,kind,object_id,payload_json,previous_root,root,writer_epoch,incarnation,committed_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (domain_id, seq, kind, effective_object, canonical_json(request), previous_root, root, writer_epoch, incarnation, committed_at),
                )
                cur.execute("UPDATE domains SET sequence=?, root=? WHERE domain_id=?", (seq, root, domain_id))
                self._inject_fault("after_journal_before_receipt", **fault_context, object_id=effective_object, root=root)
                receipt = CommitReceipt(
                    domain_id=domain_id, operation_id=operation_id, request_digest=req_digest,
                    commit_seq=seq, previous_root=previous_root, root=root, object_id=effective_object,
                    kind=kind, committed_at=committed_at,
                    incarnation=incarnation,
                )
                receipt_json = canonical_json(asdict(receipt))
                cur.execute(
                    "INSERT INTO operation_receipts(domain_id,incarnation,operation_id,request_digest,receipt_json) VALUES(?,?,?,?,?)",
                    (domain_id, incarnation, operation_id, req_digest, receipt_json),
                )
                cur.execute(
                    "UPDATE write_intents SET status='COMMITTED',reconciled_at=?,commit_seq=?,receipt_json=?,last_error=NULL "
                    "WHERE domain_id=? AND incarnation=? AND operation_id=?",
                    (committed_at, seq, receipt_json, domain_id, incarnation, operation_id),
                )
                self._inject_fault("after_receipt_before_commit", **fault_context, object_id=effective_object, root=root)
                cur.execute("COMMIT")
                self._inject_fault("after_commit", **fault_context, object_id=effective_object, root=root)
                return receipt
            except Exception as exc:
                if self.db.in_transaction:
                    cur.execute("ROLLBACK")
                # Intent durability is independent from truth durability. Preserve the
                # failure for reconciliation without changing canonical state.
                try:
                    self.db.execute(
                        "UPDATE write_intents SET last_error=? WHERE domain_id=? AND incarnation=(SELECT incarnation FROM domains WHERE domain_id=?) "
                        "AND operation_id=? AND status='PENDING'",
                        (type(exc).__name__, domain_id, domain_id, operation_id),
                    )
                except Exception:
                    pass
                raise

    def _auto_commit(
        self, domain_id: str, kind: str, object_id: str, request: Any,
        mutate: Callable[[sqlite3.Cursor, int], str | None],
    ) -> CommitReceipt:
        head = self._head_row(domain_id)
        return self._commit(
            domain_id=domain_id, operation_id=f"internal:{kind}:{uuid.uuid4().hex}",
            expected_seq=int(head["sequence"]), writer_epoch=int(head["writer_epoch"]),
            kind=kind, object_id=object_id, request=request, mutate=mutate,
        )

    # ---------- K0 evidence / claims ----------

    @staticmethod
    def _normalize_allowed(principal: str, allowed_principals: Iterable[str] | None) -> list[str]:
        vals = sorted(set(allowed_principals or [principal]))
        return vals

    @staticmethod
    def _is_allowed(principal: str, allowed_json: str) -> bool:
        allowed = json.loads(allowed_json)
        return "*" in allowed or principal in allowed

    def capture_evidence(
        self, *, domain_id: str, operation_id: str, expected_seq: int, writer_epoch: int,
        source_event_identity: str, content: Any, principal: str,
        transport_delivery_id: str | None = None,
        world_time: datetime | None = None,
        observed_at: datetime | None = None,
        allowed_principals: Iterable[str] | None = None,
        origin_roots: Iterable[str] | None = None,
        transport_channel: str = "unspecified",
        external_identity: str | None = None,
        source_authority_class: str = "UNSPECIFIED",
        common_mode_group: str | None = None,
        scope_ceiling: Iterable[str] | None = None,
        binder_procedure: str = "capture-v0.6.3",
    ) -> CommitReceipt:
        if not source_event_identity:
            raise MemoryIdentityCollision("source_event_identity is required")
        evidence_id = f"ev_{digest([domain_id, source_event_identity])[:24]}"
        now = self._clock()
        observed = observed_at or now
        allowed = self._normalize_allowed(principal, allowed_principals)
        delivery_id = transport_delivery_id or f"delivery:{operation_id}"
        origin_roots_norm = sorted(set(origin_roots or [f"source:{domain_id}:{source_event_identity}"]))
        scope_ceiling_norm = sorted(set(scope_ceiling or allowed))
        binding_specs = [
            {
                "origin_identity": root,
                "transport_channel": transport_channel,
                "external_identity": external_identity or source_event_identity,
                "authority_class": source_authority_class,
                "common_mode_group": common_mode_group or root,
                "scope_ceiling": scope_ceiling_norm,
                "binder_procedure": binder_procedure,
            }
            for root in origin_roots_norm
        ]
        # The idempotency digest binds caller semantics, not runtime-generated clock values.
        c_digest = digest(content)
        request = {
            "source_event_identity": source_event_identity,
            "transport_delivery_id": delivery_id,
            "content_digest": c_digest,
            "principal": principal,
            "allowed_principals": allowed,
            "world_time": world_time,
            "observed_at": observed_at,
            "origin_roots": origin_roots_norm,
            "origin_bindings": binding_specs,
        }

        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            existing = cur.execute(
                "SELECT * FROM evidence WHERE domain_id=? AND source_event_identity=?",
                (domain_id, source_event_identity),
            ).fetchone()
            if existing:
                if existing["content_digest"] != c_digest:
                    raise MemoryIdentityCollision(
                        f"source event identity {source_event_identity!r} reused with different content"
                    )
                effective_id = existing["evidence_id"]
            else:
                cur.execute(
                    "INSERT INTO evidence(evidence_id,domain_id,source_event_identity,content_json,content_digest,principal,allowed_principals_json,world_time,observed_at,ingested_at,created_seq,revoked_seq) VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)",
                    (evidence_id, domain_id, source_event_identity, canonical_json(content), c_digest, principal,
                     canonical_json(allowed), _iso(world_time), _iso(observed), _iso(now), seq),
                )
                effective_id = evidence_id
                self._bump_generation(cur, domain_id, "source", effective_id)
                self._bump_generation(cur, domain_id, "query_domain", "global")
            cur.execute(
                "INSERT OR IGNORE INTO deliveries(domain_id,source_event_identity,delivery_id,seen_at) VALUES(?,?,?,?)",
                (domain_id, source_event_identity, delivery_id, _iso(now)),
            )
            existing_roots = {r[0] for r in cur.execute(
                "SELECT root_identity FROM origin_roots WHERE domain_id=? AND object_kind='evidence' AND object_id=?",
                (domain_id, effective_id),
            ).fetchall()}
            if existing_roots and existing_roots != set(origin_roots_norm):
                raise MemoryIdentityCollision("source event identity reused with different origin roots")
            for root_identity in origin_roots_norm:
                cur.execute(
                    "INSERT OR IGNORE INTO origin_roots(domain_id,object_kind,object_id,root_identity) VALUES(?,?,?,?)",
                    (domain_id, "evidence", effective_id, root_identity),
                )
            for spec in binding_specs:
                binding_id = f"origin_{digest([domain_id, effective_id, spec['origin_identity']])[:24]}"
                existing_binding = cur.execute(
                    "SELECT * FROM origin_bindings WHERE domain_id=? AND evidence_id=? AND origin_identity=?",
                    (domain_id, effective_id, spec["origin_identity"]),
                ).fetchone()
                if existing_binding:
                    immutable = {
                        "transport_channel": existing_binding["transport_channel"],
                        "external_identity": existing_binding["external_identity"],
                        "authority_class": existing_binding["authority_class"],
                        "common_mode_group": existing_binding["common_mode_group"],
                        "scope_ceiling": list(json.loads(existing_binding["scope_ceiling_json"])),
                        "binder_procedure": existing_binding["binder_procedure"],
                        "raw_evidence_digest": existing_binding["raw_evidence_digest"],
                    }
                    proposed = {
                        "transport_channel": spec["transport_channel"],
                        "external_identity": spec["external_identity"],
                        "authority_class": spec["authority_class"],
                        "common_mode_group": spec["common_mode_group"],
                        "scope_ceiling": spec["scope_ceiling"],
                        "binder_procedure": spec["binder_procedure"],
                        "raw_evidence_digest": c_digest,
                    }
                    if immutable != proposed:
                        raise MemoryIdentityCollision(
                            "source event identity reused with different origin authority binding"
                        )
                else:
                    cur.execute(
                        "INSERT INTO origin_bindings(binding_id,domain_id,evidence_id,origin_identity,transport_channel,external_identity,authority_class,common_mode_group,raw_evidence_digest,scope_ceiling_json,binder_procedure,created_seq,revoked_seq,revocation_reason) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
                        (binding_id, domain_id, effective_id, spec["origin_identity"], spec["transport_channel"],
                         spec["external_identity"], spec["authority_class"], spec["common_mode_group"], c_digest,
                         canonical_json(spec["scope_ceiling"]), spec["binder_procedure"], seq),
                    )
                    self._bump_generation(cur, domain_id, "origin", effective_id)
                    self._bump_generation(cur, domain_id, "origin", "global")
            return effective_id

        return self._commit(
            domain_id=domain_id, operation_id=operation_id, expected_seq=expected_seq,
            writer_epoch=writer_epoch, kind="CAPTURE_EVIDENCE", object_id=evidence_id,
            request=request, mutate=mutate,
        )

    def capture_evidence_batch(
        self, *, domain_id: str, operation_id: str, expected_seq: int, writer_epoch: int,
        principal: str, items: list[dict[str, Any]],
    ) -> CommitReceipt:
        """Atomically capture a semantic batch under one canonical receipt.

        Every member is validated and inserted inside the same transaction. A single
        identity/provenance error aborts the entire batch; retries reconcile through
        the ordinary incarnation-scoped operation receipt.
        """
        if not items:
            raise MemoryTransitionIncomplete("evidence batch cannot be empty")
        prepared: list[dict[str, Any]] = []
        now = self._clock()
        for index, item in enumerate(items):
            sid = str(item.get("source_event_identity") or "")
            if not sid:
                raise MemoryIdentityCollision(f"batch item {index} missing source_event_identity")
            content = item.get("content")
            item_principal = str(item.get("principal", principal))
            allowed = self._normalize_allowed(item_principal, item.get("allowed_principals"))
            roots = sorted(set(item.get("origin_roots") or [f"source:{domain_id}:{sid}"]))
            scope = sorted(set(item.get("scope_ceiling") or allowed))
            observed_at_input = item.get("observed_at")
            observed_at = observed_at_input or now
            c_digest = digest(content)
            prepared.append({
                "source_event_identity": sid,
                "content": content,
                "content_digest": c_digest,
                "principal": item_principal,
                "allowed_principals": allowed,
                "transport_delivery_id": item.get("transport_delivery_id") or f"delivery:{operation_id}:{index}",
                "world_time": item.get("world_time"),
                "observed_at": observed_at,
                "observed_at_input": observed_at_input,
                "origin_roots": roots,
                "transport_channel": str(item.get("transport_channel", "unspecified")),
                "external_identity": item.get("external_identity") or sid,
                "source_authority_class": str(item.get("source_authority_class", "UNSPECIFIED")),
                "common_mode_group": item.get("common_mode_group"),
                "scope_ceiling": scope,
                "binder_procedure": str(item.get("binder_procedure", "capture-batch-v0.6.3")),
            })
        # Bind only caller semantics. Runtime clock values are excluded so a lost
        # response can be retried with the same operation id without digest drift;
        # raw evidence bytes are also excluded so the immutable journal cannot
        # defeat later erasure policy.
        request_items = [
            {
                "source_event_identity": item["source_event_identity"],
                "content_digest": item["content_digest"],
                "principal": item["principal"],
                "allowed_principals": item["allowed_principals"],
                "transport_delivery_id": item["transport_delivery_id"],
                "world_time": item["world_time"],
                "observed_at": item["observed_at_input"],
                "origin_roots": item["origin_roots"],
                "transport_channel": item["transport_channel"],
                "external_identity": item["external_identity"],
                "source_authority_class": item["source_authority_class"],
                "common_mode_group": item["common_mode_group"],
                "scope_ceiling": item["scope_ceiling"],
                "binder_procedure": item["binder_procedure"],
            }
            for item in prepared
        ]
        request = {"principal": principal, "items": request_items}
        batch_id = f"batch_{digest([domain_id, operation_id, request])[:24]}"

        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            for item in prepared:
                sid = item["source_event_identity"]
                evidence_id = f"ev_{digest([domain_id, sid])[:24]}"
                existing = cur.execute(
                    "SELECT * FROM evidence WHERE domain_id=? AND source_event_identity=?",
                    (domain_id, sid),
                ).fetchone()
                if existing:
                    if existing["content_digest"] != item["content_digest"]:
                        raise MemoryIdentityCollision(
                            f"source event identity {sid!r} reused with different content inside batch"
                        )
                    effective_id = existing["evidence_id"]
                else:
                    cur.execute(
                        "INSERT INTO evidence(evidence_id,domain_id,source_event_identity,content_json,content_digest,principal,allowed_principals_json,world_time,observed_at,ingested_at,created_seq,revoked_seq) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)",
                        (evidence_id, domain_id, sid, canonical_json(item["content"]), item["content_digest"],
                         item["principal"], canonical_json(item["allowed_principals"]), _iso(item["world_time"]),
                         _iso(item["observed_at"]), _iso(now), seq),
                    )
                    effective_id = evidence_id
                    self._bump_generation(cur, domain_id, "source", effective_id)
                    self._bump_generation(cur, domain_id, "query_domain", "global")
                cur.execute(
                    "INSERT OR IGNORE INTO deliveries(domain_id,source_event_identity,delivery_id,seen_at) VALUES(?,?,?,?)",
                    (domain_id, sid, item["transport_delivery_id"], _iso(now)),
                )
                existing_roots = {r[0] for r in cur.execute(
                    "SELECT root_identity FROM origin_roots WHERE domain_id=? AND object_kind='evidence' AND object_id=?",
                    (domain_id, effective_id),
                ).fetchall()}
                if existing_roots and existing_roots != set(item["origin_roots"]):
                    raise MemoryIdentityCollision(f"source event identity {sid!r} reused with different origin roots")
                for root in item["origin_roots"]:
                    cur.execute(
                        "INSERT OR IGNORE INTO origin_roots(domain_id,object_kind,object_id,root_identity) VALUES(?,?,?,?)",
                        (domain_id, "evidence", effective_id, root),
                    )
                    binding_id = f"origin_{digest([domain_id, effective_id, root])[:24]}"
                    proposed_common_mode = item["common_mode_group"] or root
                    existing_binding = cur.execute(
                        "SELECT * FROM origin_bindings WHERE domain_id=? AND evidence_id=? AND origin_identity=?",
                        (domain_id, effective_id, root),
                    ).fetchone()
                    if existing_binding:
                        existing_semantics = {
                            "transport_channel": existing_binding["transport_channel"],
                            "external_identity": existing_binding["external_identity"],
                            "authority_class": existing_binding["authority_class"],
                            "common_mode_group": existing_binding["common_mode_group"],
                            "scope_ceiling": list(json.loads(existing_binding["scope_ceiling_json"])),
                            "binder_procedure": existing_binding["binder_procedure"],
                            "raw_evidence_digest": existing_binding["raw_evidence_digest"],
                        }
                        proposed_semantics = {
                            "transport_channel": item["transport_channel"],
                            "external_identity": item["external_identity"],
                            "authority_class": item["source_authority_class"],
                            "common_mode_group": proposed_common_mode,
                            "scope_ceiling": item["scope_ceiling"],
                            "binder_procedure": item["binder_procedure"],
                            "raw_evidence_digest": item["content_digest"],
                        }
                        if existing_semantics != proposed_semantics:
                            raise MemoryIdentityCollision(
                                f"source event identity {sid!r} reused with different origin authority binding"
                            )
                    else:
                        cur.execute(
                            "INSERT INTO origin_bindings(binding_id,domain_id,evidence_id,origin_identity,transport_channel,external_identity,authority_class,common_mode_group,raw_evidence_digest,scope_ceiling_json,binder_procedure,created_seq,revoked_seq,revocation_reason) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
                            (binding_id, domain_id, effective_id, root, item["transport_channel"], item["external_identity"],
                             item["source_authority_class"], proposed_common_mode, item["content_digest"],
                             canonical_json(item["scope_ceiling"]), item["binder_procedure"], seq),
                        )
                        self._bump_generation(cur, domain_id, "origin", effective_id)
                        self._bump_generation(cur, domain_id, "origin", "global")
            return batch_id

        return self._commit(
            domain_id=domain_id, operation_id=operation_id, expected_seq=expected_seq,
            writer_epoch=writer_epoch, kind="CAPTURE_EVIDENCE_BATCH", object_id=batch_id,
            request=request, mutate=mutate,
        )

    def count_evidence(self, domain_id: str) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM evidence WHERE domain_id=?", (domain_id,)).fetchone()[0])

    def count_deliveries(self, domain_id: str, source_event_identity: str) -> int:
        return int(self.db.execute(
            "SELECT COUNT(*) FROM deliveries WHERE domain_id=? AND source_event_identity=?",
            (domain_id, source_event_identity),
        ).fetchone()[0])

    def get_evidence(self, domain_id: str, evidence_id: str, *, principal: str) -> Any:
        if hasattr(self, "_require_capability"):
            self._require_capability(domain_id, principal, "READ_EXACT")
        row = self.db.execute(
            "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, evidence_id)
        ).fetchone()
        if not row:
            raise KeyError(evidence_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked(f"principal {principal!r} cannot read evidence {evidence_id}")
        if row["revoked_seq"] is not None:
            raise MemoryRecallInsufficient(f"evidence {evidence_id} is revoked")
        if row["deleted_seq"] is not None:
            raise MemoryRecallInsufficient(f"evidence {evidence_id} was erased by retention policy")
        return json.loads(row["content_json"])

    def create_claim(
        self, *, domain_id: str, operation_id: str, expected_seq: int, writer_epoch: int,
        logical_id: str, proposition: Any, valid_from: datetime | None, valid_to: datetime | None,
        support_paths: list[list[str]], principal: str,
        allowed_principals: Iterable[str] | None = None, applicability: dict[str, Any] | None = None,
    ) -> CommitReceipt:
        allowed = self._normalize_allowed(principal, allowed_principals)
        applicability = dict(applicability or {})
        prop_digest = digest(proposition)
        revision_id = f"claim_{digest([domain_id, logical_id, prop_digest, expected_seq])[:24]}"
        known_from = self._clock()
        request = {
            "logical_id": logical_id, "proposition": proposition, "valid_from": valid_from,
            "valid_to": valid_to, "support_paths": support_paths, "principal": principal,
            "allowed_principals": allowed, "applicability": applicability,
        }

        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            current = cur.execute(
                "SELECT * FROM claims WHERE domain_id=? AND logical_id=? AND superseded_seq IS NULL ORDER BY created_seq DESC LIMIT 1",
                (domain_id, logical_id),
            ).fetchone()
            if current:
                if current["proposition_digest"] == prop_digest and current["valid_from"] == _iso(valid_from) and current["valid_to"] == _iso(valid_to):
                    return current["claim_revision_id"]
                raise MemoryIdentityCollision(
                    f"logical claim {logical_id!r} already exists with different semantics; use revise_claim"
                )
            # Every support member must exist, but access is not truth authority.
            for path in support_paths:
                if not path:
                    raise MemoryTransitionIncomplete("empty justification AND path is not grounding")
                for ev_id in path:
                    if not cur.execute("SELECT 1 FROM evidence WHERE evidence_id=? AND domain_id=?", (ev_id, domain_id)).fetchone():
                        raise MemoryTransitionIncomplete(f"unknown evidence support {ev_id}")
            if hasattr(self, "_enforce_integrity_authority_profiles"):
                self._enforce_integrity_authority_profiles(cur, domain_id, logical_id, "CREATE_CLAIM", support_paths)
            cur.execute(
                "INSERT INTO claims(claim_revision_id,domain_id,logical_id,proposition_json,proposition_digest,principal,allowed_principals_json,valid_from,valid_to,known_from,created_seq,superseded_seq,applicability_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL,?)",
                (revision_id, domain_id, logical_id, canonical_json(proposition), prop_digest, principal,
                 canonical_json(allowed), _iso(valid_from), _iso(valid_to), _iso(known_from), seq, canonical_json(applicability)),
            )
            for path in support_paths:
                path_id = f"jp_{uuid.uuid4().hex}"
                cur.execute("INSERT INTO justification_paths(path_id,claim_revision_id) VALUES(?,?)", (path_id, revision_id))
                for ev_id in sorted(set(path)):
                    cur.execute("INSERT INTO justification_members(path_id,evidence_id) VALUES(?,?)", (path_id, ev_id))
            self._bump_generation(cur, domain_id, "claim", logical_id)
            self._bump_generation(cur, domain_id, "query_domain", "global")
            return revision_id

        return self._commit(
            domain_id=domain_id, operation_id=operation_id, expected_seq=expected_seq,
            writer_epoch=writer_epoch, kind="CREATE_CLAIM", object_id=revision_id,
            request=request, mutate=mutate,
        )

    def _current_claim(self, domain_id: str, logical_id: str) -> sqlite3.Row:
        row = self.db.execute(
            "SELECT * FROM claims WHERE domain_id=? AND logical_id=? AND superseded_seq IS NULL ORDER BY created_seq DESC LIMIT 1",
            (domain_id, logical_id),
        ).fetchone()
        if not row:
            raise KeyError(logical_id)
        return row

    @staticmethod
    def _claim_row_payload(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "claim_revision_id": row["claim_revision_id"],
            "domain_id": row["domain_id"],
            "logical_id": row["logical_id"],
            "proposition": json.loads(row["proposition_json"]),
            "proposition_digest": row["proposition_digest"],
            "principal": row["principal"],
            "allowed_principals": list(json.loads(row["allowed_principals_json"])),
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
            "known_from": row["known_from"],
            "created_seq": int(row["created_seq"]),
            "superseded_seq": None if row["superseded_seq"] is None else int(row["superseded_seq"]),
            "applicability": json.loads(row["applicability_json"] or "{}"),
        }

    def get_claim_revision(self, domain_id: str, claim_revision_id: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT * FROM claims WHERE domain_id=? AND claim_revision_id=?",
            (domain_id, claim_revision_id),
        ).fetchone()
        if not row:
            raise KeyError(claim_revision_id)
        return self._claim_row_payload(row)

    def revise_claim(
        self, *, domain_id: str, operation_id: str, expected_seq: int, writer_epoch: int,
        logical_id: str, expected_predecessor_revision_id: str, proposition: Any,
        valid_from: datetime | None, valid_to: datetime | None, support_paths: list[list[str]],
        principal: str, allowed_principals: Iterable[str] | None = None, applicability: dict[str, Any] | None = None,
    ) -> CommitReceipt:
        current = self._current_claim(domain_id, logical_id)
        applicability = dict(json.loads(current["applicability_json"] or "{}") if applicability is None else applicability)
        allowed = (
            self._normalize_allowed(principal, allowed_principals)
            if allowed_principals is not None
            else list(json.loads(current["allowed_principals_json"]))
        )
        prop_digest = digest(proposition)
        revision_id = f"claim_{digest([domain_id, logical_id, expected_predecessor_revision_id, prop_digest, _iso(valid_from), _iso(valid_to)])[:24]}"
        known_from = self._clock()
        request = {
            "logical_id": logical_id,
            "expected_predecessor_revision_id": expected_predecessor_revision_id,
            "proposition": proposition,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "support_paths": support_paths,
            "principal": principal,
            "allowed_principals": allowed,
            "applicability": applicability,
        }

        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            predecessor = cur.execute(
                "SELECT * FROM claims WHERE domain_id=? AND logical_id=? AND superseded_seq IS NULL "
                "ORDER BY created_seq DESC LIMIT 1",
                (domain_id, logical_id),
            ).fetchone()
            if not predecessor:
                raise KeyError(logical_id)
            if predecessor["claim_revision_id"] != expected_predecessor_revision_id:
                raise MemoryWriteConflict(
                    f"claim predecessor {expected_predecessor_revision_id!r} is stale; current is {predecessor['claim_revision_id']!r}"
                )
            if not self._is_allowed(principal, predecessor["allowed_principals_json"]):
                raise MemoryScopeBlocked("principal cannot revise inaccessible claim")
            for path in support_paths:
                if not path:
                    raise MemoryTransitionIncomplete("empty justification AND path is not grounding")
                for ev_id in path:
                    evidence = cur.execute(
                        "SELECT revoked_seq,deleted_seq,compromised_seq FROM evidence WHERE evidence_id=? AND domain_id=?",
                        (ev_id, domain_id),
                    ).fetchone()
                    if not evidence:
                        raise MemoryTransitionIncomplete(f"unknown evidence support {ev_id}")
                    if any(evidence[k] is not None for k in ("revoked_seq", "deleted_seq", "compromised_seq")):
                        raise MemoryTransitionIncomplete(f"non-live evidence support {ev_id}")
            if hasattr(self, "_enforce_integrity_authority_profiles"):
                self._enforce_integrity_authority_profiles(cur, domain_id, logical_id, "REVISE_CLAIM", support_paths)
            cur.execute(
                "UPDATE claims SET superseded_seq=? WHERE claim_revision_id=? AND superseded_seq IS NULL",
                (seq, expected_predecessor_revision_id),
            )
            if cur.rowcount != 1:
                raise MemoryWriteConflict("claim predecessor changed during revision")
            cur.execute(
                "INSERT INTO claims(claim_revision_id,domain_id,logical_id,proposition_json,proposition_digest,principal,allowed_principals_json,valid_from,valid_to,known_from,created_seq,superseded_seq,applicability_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL,?)",
                (revision_id, domain_id, logical_id, canonical_json(proposition), prop_digest, principal,
                 canonical_json(allowed), _iso(valid_from), _iso(valid_to), _iso(known_from), seq, canonical_json(applicability)),
            )
            for path in support_paths:
                path_id = f"jp_{uuid.uuid4().hex}"
                cur.execute("INSERT INTO justification_paths(path_id,claim_revision_id) VALUES(?,?)", (path_id, revision_id))
                for ev_id in sorted(set(path)):
                    cur.execute("INSERT INTO justification_members(path_id,evidence_id) VALUES(?,?)", (path_id, ev_id))
            self._bump_generation(cur, domain_id, "claim", logical_id)
            self._bump_generation(cur, domain_id, "query_domain", "global")
            return revision_id

        return self._commit(
            domain_id=domain_id, operation_id=operation_id, expected_seq=expected_seq,
            writer_epoch=writer_epoch, kind="REVISE_CLAIM", object_id=revision_id,
            request=request, mutate=mutate,
        )

    def claim_as_known_by(self, domain_id: str, logical_id: str, at: datetime) -> dict[str, Any] | None:
        t = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
        row = self.db.execute(
            "SELECT * FROM claims WHERE domain_id=? AND logical_id=? AND known_from<=? "
            "ORDER BY known_from DESC, created_seq DESC LIMIT 1",
            (domain_id, logical_id, _iso(t)),
        ).fetchone()
        return None if row is None else self._claim_row_payload(row)

    def _claim_applicability_matches(self, domain_id: str, row: sqlite3.Row, *, at_seq: int | None = None) -> bool:
        app = json.loads(row["applicability_json"] or "{}")
        if not app:
            return True
        if at_seq is not None and hasattr(self, "_compatibility_at_seq"):
            mission, environment, _ = self._compatibility_at_seq(domain_id, at_seq)
        elif hasattr(self, "_current_compatibility"):
            mission, environment, _ = self._current_compatibility(domain_id)
        else:
            mission = environment = None
        self_version = self._self_version_at_seq(domain_id, at_seq) if at_seq is not None and hasattr(self, "_self_version_at_seq") else (self._current_self_version(domain_id) if hasattr(self, "_current_self_version") else None)
        checks = {"mission_revision": mission, "environment_revision": environment, "self_version": self_version}
        for key, current in checks.items():
            if key in app and app[key] != current:
                return False
        if "allowed_environments" in app and environment not in set(app["allowed_environments"]):
            return False
        if "allowed_self_versions" in app and self_version not in set(app["allowed_self_versions"]):
            return False
        return True

    def claim_currently_usable(self, domain_id: str, logical_id: str, *, principal: str) -> bool:
        row = self._current_claim(domain_id, logical_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            return False
        return self.claim_is_supported(domain_id, logical_id) and self._claim_applicability_matches(domain_id, row)

    def rollback_claim_to_revision(
        self, domain_id: str, logical_id: str, target_revision_id: str, *, principal: str, operation_id: str,
    ) -> CommitReceipt:
        target = self.db.execute(
            "SELECT * FROM claims WHERE domain_id=? AND logical_id=? AND claim_revision_id=?",
            (domain_id, logical_id, target_revision_id),
        ).fetchone()
        if target is None:
            raise KeyError(target_revision_id)
        current = self._current_claim(domain_id, logical_id)
        paths = []
        for prow in self.db.execute("SELECT path_id FROM justification_paths WHERE claim_revision_id=? ORDER BY path_id", (target_revision_id,)).fetchall():
            paths.append([r[0] for r in self.db.execute("SELECT evidence_id FROM justification_members WHERE path_id=? ORDER BY evidence_id", (prow["path_id"],)).fetchall()])
        # Rollback is a new semantic revision. Current governance/source liveness is
        # rechecked by revise_claim; an old revision is never simply reactivated.
        head = self._head_row(domain_id)
        return self.revise_claim(
            domain_id=domain_id, operation_id=operation_id, expected_seq=int(head["sequence"]),
            writer_epoch=int(head["writer_epoch"]), logical_id=logical_id,
            expected_predecessor_revision_id=current["claim_revision_id"],
            proposition=json.loads(target["proposition_json"]), valid_from=_parse_dt(target["valid_from"]),
            valid_to=_parse_dt(target["valid_to"]), support_paths=paths, principal=principal,
            allowed_principals=json.loads(target["allowed_principals_json"]),
            applicability=json.loads(target["applicability_json"] or "{}"),
        )

    def claim_valid_at(self, domain_id: str, logical_id: str, at: datetime) -> bool:
        row = self._current_claim(domain_id, logical_id)
        t = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
        start = _parse_dt(row["valid_from"])
        end = _parse_dt(row["valid_to"])
        return (start is None or t >= start) and (end is None or t < end)

    def claim_known_by(self, domain_id: str, logical_id: str, at: datetime) -> bool:
        return self.claim_as_known_by(domain_id, logical_id, at) is not None

    def claim_is_supported(self, domain_id: str, logical_id: str) -> bool:
        """Evaluate OR-of-AND live justification paths without laundering access into truth."""
        claim = self._current_claim(domain_id, logical_id)
        paths = self.db.execute(
            "SELECT path_id FROM justification_paths WHERE claim_revision_id=?",
            (claim["claim_revision_id"],),
        ).fetchall()
        for path in paths:
            members = self.db.execute(
                "SELECT e.revoked_seq,e.deleted_seq,e.compromised_seq FROM justification_members jm JOIN evidence e ON e.evidence_id=jm.evidence_id WHERE jm.path_id=?",
                (path["path_id"],),
            ).fetchall()
            if members and all(m["revoked_seq"] is None and m["deleted_seq"] is None and m["compromised_seq"] is None for m in members):
                return True
        return False

    def revoke_evidence(self, domain_id: str, evidence_id: str, *, principal: str) -> None:
        request = {"evidence_id": evidence_id, "principal": principal}
        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            row = cur.execute(
                "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?",
                (domain_id, evidence_id),
            ).fetchone()
            if not row:
                raise KeyError(evidence_id)
            if not self._is_allowed(principal, row["allowed_principals_json"]):
                raise MemoryScopeBlocked("cannot revoke inaccessible evidence")
            if row["revoked_seq"] is None:
                cur.execute("UPDATE evidence SET revoked_seq=? WHERE evidence_id=?", (seq, evidence_id))
                self._bump_generation(cur, domain_id, "source", evidence_id)
                self._bump_generation(cur, domain_id, "query_domain", "global")
            return evidence_id
        self._auto_commit(domain_id, "REVOKE_EVIDENCE", evidence_id, request, mutate)

    # ---------- generations / semantic OCC substrate ----------

    def _generation(self, domain_id: str, dep_class: str, dep_key: str, cur: sqlite3.Cursor | None = None) -> int:
        q = cur or self.db
        row = q.execute(
            "SELECT generation FROM generations WHERE domain_id=? AND dep_class=? AND dep_key=?",
            (domain_id, dep_class, dep_key),
        ).fetchone()
        return 0 if row is None else int(row[0])

    def _bump_generation(self, cur: sqlite3.Cursor, domain_id: str, dep_class: str, dep_key: str) -> int:
        current = self._generation(domain_id, dep_class, dep_key, cur)
        nxt = current + 1
        cur.execute(
            "INSERT INTO generations(domain_id,dep_class,dep_key,generation) VALUES(?,?,?,?) "
            "ON CONFLICT(domain_id,dep_class,dep_key) DO UPDATE SET generation=excluded.generation",
            (domain_id, dep_class, dep_key, nxt),
        )
        return nxt

    def bump_generation(self, domain_id: str, dep_class: str, dep_key: str = "global") -> None:
        head = self._head_row(domain_id)
        request = {"dep_class": dep_class, "dep_key": dep_key}
        def mutate(cur: sqlite3.Cursor, seq: int) -> None:
            self._bump_generation(cur, domain_id, dep_class, dep_key)
        self._commit(
            domain_id=domain_id, operation_id=f"internal:bump:{dep_class}:{dep_key}:{uuid.uuid4().hex}",
            expected_seq=int(head["sequence"]), writer_epoch=int(head["writer_epoch"]),
            kind="BUMP_GENERATION", object_id=f"{dep_class}:{dep_key}", request=request, mutate=mutate,
        )

    def bump_global_generation(self, domain_id: str, dep_class: str) -> None:
        self.bump_generation(domain_id, dep_class, "global")

    # ---------- K1 representation plane ----------

    def create_region(
        self, domain_id: str, semantic_key: str, *, principal: str,
        allowed_principals: Iterable[str] | None = None,
    ) -> str:
        region_id = f"region_{digest([domain_id, semantic_key])[:24]}"
        allowed = self._normalize_allowed(principal, allowed_principals)
        request = {"semantic_key": semantic_key, "principal": principal, "allowed_principals": allowed}
        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            existing = cur.execute("SELECT * FROM regions WHERE domain_id=? AND semantic_key=?", (domain_id, semantic_key)).fetchone()
            if existing:
                if existing["allowed_principals_json"] != canonical_json(allowed):
                    raise MemoryIdentityCollision("region semantic identity collision")
                return existing["region_id"]
            cur.execute(
                "INSERT INTO regions(region_id,domain_id,semantic_key,principal,allowed_principals_json,created_seq,invalidated_seq) VALUES(?,?,?,?,?,?,NULL)",
                (region_id, domain_id, semantic_key, principal, canonical_json(allowed), seq),
            )
            self._bump_generation(cur, domain_id, "region", region_id)
            return region_id
        return self._auto_commit(domain_id, "CREATE_REGION", region_id, request, mutate).object_id

    def register_query_family(self, family_id: str, required_dimensions: set[str], *, revision: int = 1) -> None:
        payload = canonical_json(sorted(required_dimensions))
        with self._lock:
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute("SELECT * FROM query_families WHERE family_id=?", (family_id,)).fetchone()
                if row:
                    current_revision = int(row["revision"])
                    if current_revision == int(revision):
                        if row["required_dimensions_json"] != payload:
                            raise MemoryIdentityCollision(f"query family {family_id!r} revision collision")
                        cur.execute("COMMIT")
                        return
                    if int(revision) != current_revision + 1:
                        raise MemoryTransitionIncomplete(
                            f"query family revision must advance contiguously from {current_revision} to {current_revision + 1}"
                        )
                    cur.execute(
                        "UPDATE query_families SET required_dimensions_json=?,revision=? WHERE family_id=?",
                        (payload, int(revision), family_id),
                    )
                else:
                    if int(revision) != 1:
                        raise MemoryTransitionIncomplete("first query family revision must be 1")
                    cur.execute(
                        "INSERT INTO query_families(family_id,required_dimensions_json,revision) VALUES(?,?,?)",
                        (family_id, payload, int(revision)),
                    )
                cur.execute(
                    "INSERT INTO query_family_revisions(family_id,revision,required_dimensions_json,created_at) VALUES(?,?,?,?)",
                    (family_id, int(revision), payload, _iso(self._clock())),
                )
                for domain in cur.execute("SELECT domain_id FROM domains ORDER BY domain_id").fetchall():
                    self._bump_generation(cur, domain["domain_id"], "query_family", family_id)
                cur.execute("COMMIT")
            except Exception:
                if self.db.in_transaction:
                    cur.execute("ROLLBACK")
                raise

    def get_query_family_history(self, family_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT * FROM query_family_revisions WHERE family_id=? ORDER BY revision",
            (family_id,),
        ).fetchall()
        return [
            {
                "family_id": row["family_id"],
                "revision": int(row["revision"]),
                "required_dimensions": list(json.loads(row["required_dimensions_json"])),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def register_applicability_compatibility_profile(
        self, *, revision: int, refinements: list[dict[str, str]],
    ) -> int:
        normalized = sorted(
            ({"dimension": str(x["dimension"]), "declared": str(x["declared"]), "requested": str(x["requested"])} for x in refinements),
            key=lambda x: (x["dimension"], x["declared"], x["requested"]),
        )
        payload = {"revision": int(revision), "refinements": normalized}
        pd = digest(payload)
        with self._lock:
            cur=self.db.cursor(); cur.execute("BEGIN IMMEDIATE")
            try:
                same=cur.execute("SELECT profile_digest FROM applicability_compatibility_profiles WHERE revision=?",(int(revision),)).fetchone()
                if same is not None:
                    if same["profile_digest"] != pd:
                        raise MemoryTransitionIncomplete("applicability compatibility revision collision")
                    cur.execute("COMMIT"); return int(revision)
                head=cur.execute("SELECT MAX(revision) FROM applicability_compatibility_profiles").fetchone()[0]
                expected=1 if head is None else int(head)+1
                if int(revision) != expected:
                    raise MemoryTransitionIncomplete(f"applicability compatibility revision must advance contiguously to {expected}")
                cur.execute("INSERT INTO applicability_compatibility_profiles(revision,refinements_json,profile_digest,created_at) VALUES(?,?,?,?)",
                    (int(revision),canonical_json(normalized),pd,_iso(self._clock())))
                for row in cur.execute("SELECT domain_id FROM domains ORDER BY domain_id").fetchall():
                    self._bump_generation(cur,row["domain_id"],"applicability_policy","global")
                cur.execute("COMMIT")
            except Exception:
                if self.db.in_transaction: cur.execute("ROLLBACK")
                raise
        return int(revision)

    def _applicability_values_compatible(self, dimension: str, declared: object, requested: object) -> bool:
        if declared == "*" or declared == requested:
            return True
        row=self.db.execute("SELECT refinements_json FROM applicability_compatibility_profiles ORDER BY revision DESC LIMIT 1").fetchone()
        if row is None:
            return False
        for edge in json.loads(row["refinements_json"]):
            if edge["dimension"] == dimension and edge["declared"] == str(declared) and edge["requested"] == str(requested):
                return True
        return False

    def _family_requirements(self, family_id: str) -> set[str]:
        row = self.db.execute("SELECT required_dimensions_json FROM query_families WHERE family_id=?", (family_id,)).fetchone()
        if not row:
            raise MemoryQueryCapabilityUnsupported(f"unknown query family {family_id!r}")
        return set(json.loads(row[0]))

    def certify_preservation(
        self, domain_id: str, representation_id: str, *, query_family: str, verifier_ref: str,
    ) -> PreservationCertificate:
        rep = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if not rep:
            raise KeyError(representation_id)
        family = self.db.execute(
            "SELECT * FROM query_families WHERE family_id=?", (query_family,)
        ).fetchone()
        if not family:
            raise MemoryQueryCapabilityUnsupported(f"unknown query family {query_family!r}")
        requirements = set(json.loads(family["required_dimensions_json"]))
        loss = json.loads(rep["loss_json"])
        exact_states = {LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value}
        missing = sorted(dim for dim in requirements if loss.get(dim, LossState.UNKNOWN.value) not in exact_states)
        answer = self.answerability(representation_id, query_family)
        status_map = {
            Answerability.EXACT: "EXACT",
            Answerability.BOUNDED: "BOUNDED",
            Answerability.REHYDRATABLE: "SOURCE_REHYDRATABLE",
            Answerability.UNKNOWN: "UNKNOWN",
            Answerability.UNSUPPORTED: "UNSUPPORTED",
        }
        deps = [
            Dependency("representation", representation_id, self._generation(domain_id, "representation", representation_id)),
            Dependency("query_family", query_family, self._generation(domain_id, "query_family", query_family)),
            Dependency("region", rep["region_id"], self._generation(domain_id, "region", rep["region_id"])),
            Dependency("transform_profile", rep["transform_profile"], self._generation(domain_id, "transform_profile", rep["transform_profile"])),
        ]
        certificate = PreservationCertificate(
            certificate_id=f"preserve_{uuid.uuid4().hex}", domain_id=domain_id,
            representation_id=representation_id, query_family=query_family,
            query_family_revision=int(family["revision"]), verifier_ref=verifier_ref,
            status=status_map[answer], missing_dimensions=missing,
            dependencies=deps, created_at=_iso(self._clock()),
        )
        self.db.execute(
            "INSERT INTO preservation_certificates(certificate_id,domain_id,representation_id,query_family,query_family_revision,verifier_ref,status,missing_dimensions_json,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (certificate.certificate_id, domain_id, representation_id, query_family,
             certificate.query_family_revision, verifier_ref, certificate.status,
             canonical_json(missing), canonical_json([asdict(d) for d in deps]), certificate.created_at),
        )
        return certificate

    def validate_preservation_certificate(self, certificate_id: str) -> bool:
        row = self.db.execute(
            "SELECT * FROM preservation_certificates WHERE certificate_id=?", (certificate_id,)
        ).fetchone()
        if not row:
            raise KeyError(certificate_id)
        deps = [Dependency(**x) for x in json.loads(row["dependencies_json"])]
        self.validate_dependencies(row["domain_id"], deps)
        return True

    def _source_can_supply_dimension(
        self, cur: sqlite3.Cursor, domain_id: str, representation_id: str, dimension: str,
        *, visited: set[str] | None = None,
    ) -> bool:
        """Return whether a lineage has a grounded witness for an exact/normalized dimension.

        REHYDRATABLE is a capability claim about a real recovery path, not a producer hint.
        A compact representation may therefore delegate to its source lineage, but a cycle,
        missing source, or lineage that only ever LOST/UNKNOWN the dimension cannot supply it.
        """
        seen = set() if visited is None else visited
        if representation_id in seen:
            return False
        seen.add(representation_id)
        row = cur.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if not row or row["invalidated_seq"] is not None or row["tainted_seq"] is not None:
            return False
        exact_states = {LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value}
        state = json.loads(row["loss_json"]).get(dimension, LossState.UNKNOWN.value)
        if state in exact_states:
            return True
        if dimension not in set(json.loads(row["recoverable_json"])):
            return False
        for source_id in json.loads(row["source_representation_ids_json"]):
            if self._source_can_supply_dimension(
                cur, domain_id, source_id, dimension, visited=set(seen)
            ):
                return True
        return False

    def add_representation(
        self, domain_id: str, region_id: str, *, kind: str, payload: Any,
        loss: dict[str, LossState | str], recoverable: set[str], token_cost: int, principal: str,
        source_representation_ids: list[str] | None = None, transform_kind: str = "PURE",
        transform_profile: str = "default", source_evidence_ids: list[str] | None = None,
        allowed_principals: Iterable[str] | None = None,
        hard_dependencies: list[RecallRole] | None = None,
        applicability: dict[str, Any] | None = None,
    ) -> str:
        if hasattr(self, "_require_capability"):
            self._require_capability(domain_id, principal, "DERIVE")
        if token_cost < 0:
            raise ValueError("token_cost must be >= 0")
        source_ids = list(source_representation_ids or [])
        source_evidence_ids = list(source_evidence_ids or [])
        hard_dependencies = list(hard_dependencies or [])
        applicability = dict(applicability or {})
        allowed = self._normalize_allowed(principal, allowed_principals)
        loss_norm = {k: (v.value if isinstance(v, LossState) else str(v)) for k, v in loss.items()}
        rep_id = f"rep_{uuid.uuid4().hex}"
        request = {
            "region_id": region_id, "kind": kind, "payload_digest": digest(payload), "loss": loss_norm,
            "recoverable": sorted(recoverable), "token_cost": token_cost, "principal": principal,
            "source_representation_ids": source_ids, "source_evidence_ids": source_evidence_ids,
            "transform_kind": transform_kind, "transform_profile": transform_profile,
            "allowed_principals": allowed,
            "hard_dependencies": [asdict(r) for r in hard_dependencies],
            "applicability": applicability,
        }

        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            region = cur.execute("SELECT * FROM regions WHERE domain_id=? AND region_id=?", (domain_id, region_id)).fetchone()
            if not region:
                raise KeyError(region_id)
            if region["invalidated_seq"] is not None:
                raise MemoryTransitionIncomplete("cannot add representation to invalidated region")
            contract = self._transformation_contract(transform_profile) if hasattr(self, "_transformation_contract") else None
            if contract:
                if contract["transform_kind"] != transform_kind:
                    raise MemoryTransitionIncomplete("transform kind violates registered transformation contract")
                forbidden = set(json.loads(contract["forbidden_loss_json"]))
                for dim in forbidden:
                    if loss_norm.get(dim, LossState.UNKNOWN.value) in {LossState.LOST.value, LossState.UNKNOWN.value}:
                        raise MemoryTransitionIncomplete(f"registered transformation contract forbids loss of {dim!r}")
            for sid in source_ids:
                src = cur.execute("SELECT * FROM representations WHERE representation_id=? AND domain_id=?", (sid, domain_id)).fetchone()
                if not src:
                    raise MemoryTransitionIncomplete(f"unknown source representation {sid}")
                if src["region_id"] != region_id:
                    raise MemoryTransitionIncomplete("cross-region pure derivation requires explicit re-grounding profile")

            # A producer may label a field recoverable only when a real source lineage can
            # supply it. This keeps REHYDRATABLE separate from optimistic self-report.
            for dim in recoverable:
                if not source_ids or not any(
                    self._source_can_supply_dimension(cur, domain_id, sid, dim) for sid in source_ids
                ):
                    raise MemoryTransitionIncomplete(
                        f"recoverable dimension {dim!r} has no grounded source witness"
                    )

            # Loss conservation is existential across multi-source PURE transforms: one
            # preserving source is a restoring basis; another lossy source does not erase it.
            # Conversely, if no source lineage can supply the claimed exact dimension, a
            # PURE transform would be manufacturing information.
            if transform_kind == "PURE" and source_ids:
                for dim, state in loss_norm.items():
                    if state in (LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value):
                        if not any(
                            self._source_can_supply_dimension(cur, domain_id, sid, dim) for sid in source_ids
                        ):
                            raise MemoryTransitionIncomplete(
                                f"pure transform cannot restore dimension {dim!r} without restoring basis"
                            )
            for eid in source_evidence_ids:
                erow = cur.execute("SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, eid)).fetchone()
                if not erow or erow["revoked_seq"] is not None or erow["deleted_seq"] is not None:
                    raise MemoryTransitionIncomplete(f"unavailable source evidence {eid}")
                if not self._is_allowed(principal, erow["allowed_principals_json"]):
                    raise MemoryScopeBlocked("cannot derive from inaccessible source evidence")
            cur.execute(
                "INSERT INTO representations(representation_id,domain_id,region_id,kind,payload_json,source_representation_ids_json,transform_kind,loss_json,recoverable_json,token_cost,principal,allowed_principals_json,created_seq,invalidated_seq,source_evidence_ids_json,transform_profile,tainted_seq,hard_dependencies_json,applicability_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,NULL,?,?)",
                (rep_id, domain_id, region_id, kind, canonical_json(payload), canonical_json(source_ids), transform_kind,
                 canonical_json(loss_norm), canonical_json(sorted(recoverable)), token_cost, principal, canonical_json(allowed), seq,
                 canonical_json(source_evidence_ids), transform_profile, canonical_json([asdict(r) for r in hard_dependencies]), canonical_json(applicability)),
            )
            self._bump_generation(cur, domain_id, "representation", rep_id)
            self._bump_generation(cur, domain_id, "region", region_id)
            self._bump_generation(cur, domain_id, "query_domain", "global")
            return rep_id

        return self._auto_commit(domain_id, "ADD_REPRESENTATION", rep_id, request, mutate).object_id

    def answerability(self, representation_id: str, query_family: str) -> Answerability:
        row = self.db.execute("SELECT * FROM representations WHERE representation_id=?", (representation_id,)).fetchone()
        if not row or row["invalidated_seq"] is not None or row["tainted_seq"] is not None:
            return Answerability.UNSUPPORTED
        req = self._family_requirements(query_family)
        loss = json.loads(row["loss_json"])
        recoverable = set(json.loads(row["recoverable_json"]))
        exact_states = {LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value}
        if all(loss.get(d) in exact_states for d in req):
            return Answerability.EXACT
        unknown = any(loss.get(d, LossState.UNKNOWN.value) == LossState.UNKNOWN.value for d in req)
        available = {d for d in req if loss.get(d) in exact_states}

        # Recoverability is a current capability proof, not a durable producer hint.
        # Every missing dimension advertised as recoverable must still have a live,
        # untainted lineage route that can actually supply it now.
        source_ids = list(json.loads(row["source_representation_ids_json"]))
        live_recoverable = {
            d for d in (req - available)
            if d in recoverable and any(
                self._source_can_supply_dimension(self.db.cursor(), row["domain_id"], sid, d)
                for sid in source_ids
            )
        }
        if req.issubset(available | live_recoverable):
            return Answerability.REHYDRATABLE
        if unknown:
            return Answerability.UNKNOWN
        return Answerability.UNSUPPORTED

    def invalidate_representation(self, domain_id: str, representation_id: str, *, principal: str) -> None:
        request = {"representation_id": representation_id, "principal": principal}
        def mutate(cur: sqlite3.Cursor, seq: int) -> str:
            row = cur.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, representation_id)).fetchone()
            if not row:
                raise KeyError(representation_id)
            if not self._is_allowed(principal, row["allowed_principals_json"]):
                raise MemoryScopeBlocked("cannot invalidate inaccessible representation")
            if row["invalidated_seq"] is None:
                cur.execute("UPDATE representations SET invalidated_seq=? WHERE representation_id=?", (seq, representation_id))
                self._bump_generation(cur, domain_id, "representation", representation_id)
                self._bump_generation(cur, domain_id, "region", row["region_id"])
                self._bump_generation(cur, domain_id, "query_domain", "global")
            return representation_id
        self._auto_commit(domain_id, "INVALIDATE_REPRESENTATION", representation_id, request, mutate)

    # ---------- K2 recall plane ----------

    def _representation_sources_live_at_cut(
        self, domain_id: str, representation_id: str, cut_seq: int, *, visited: set[str] | None = None,
    ) -> bool:
        """Current-use liveness of the derivation basis at a pinned historical cut."""
        seen=set() if visited is None else set(visited)
        if representation_id in seen:
            return False
        seen.add(representation_id)
        row=self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id,representation_id),
        ).fetchone()
        if row is None or int(row["created_seq"]) > cut_seq:
            return False
        if row["invalidated_seq"] is not None and int(row["invalidated_seq"]) <= cut_seq:
            return False
        if row["tainted_seq"] is not None and int(row["tainted_seq"]) <= cut_seq:
            return False
        for evidence_id in json.loads(row["source_evidence_ids_json"] or "[]"):
            ev=self.db.execute(
                "SELECT created_seq,revoked_seq,deleted_seq,compromised_seq FROM evidence WHERE domain_id=? AND evidence_id=?",
                (domain_id,evidence_id),
            ).fetchone()
            if ev is None or int(ev["created_seq"]) > cut_seq:
                return False
            for field in ("revoked_seq","deleted_seq","compromised_seq"):
                if ev[field] is not None and int(ev[field]) <= cut_seq:
                    return False
        for source_id in json.loads(row["source_representation_ids_json"] or "[]"):
            if not self._representation_sources_live_at_cut(domain_id,source_id,cut_seq,visited=seen):
                return False
        return True

    def _visible_representations_at_cut(
        self, domain_id: str, region_id: str, principal: str, cut_seq: int, *,
        compatibility_profile: dict[str, str] | None = None, safety_critical_dimensions: set[str] | None = None,
    ) -> list[sqlite3.Row]:
        if hasattr(self, "_capability_allowed"):
            if not self._capability_allowed(domain_id, principal, "DISCOVER"):
                return []
            if not self._capability_allowed(domain_id, principal, "USE_FOR_LOCAL_REASONING"):
                return []
        rows = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND region_id=? AND created_seq<=? AND (invalidated_seq IS NULL OR invalidated_seq>?) AND (tainted_seq IS NULL OR tainted_seq>?) ORDER BY token_cost ASC, created_seq DESC, representation_id ASC",
            (domain_id, region_id, cut_seq, cut_seq, cut_seq),
        ).fetchall()
        return [r for r in rows if self._is_allowed(principal, r["allowed_principals_json"])
                and self._representation_sources_live_at_cut(domain_id, r["representation_id"], cut_seq)
                and self._representation_applicable(
                    domain_id, r, cut_seq=cut_seq, compatibility_profile=compatibility_profile,
                    safety_critical_dimensions=safety_critical_dimensions,
                )]

    def _representation_applicable(
        self, domain_id: str, row: sqlite3.Row, *, cut_seq: int | None = None,
        compatibility_profile: dict[str, str] | None = None, safety_critical_dimensions: set[str] | None = None,
    ) -> bool:
        app = json.loads(row["applicability_json"] or "{}")
        requested = dict(compatibility_profile or {})
        critical = set(safety_critical_dimensions or set())
        if critical and any(dim not in app for dim in critical):
            return False
        if not app and not requested:
            return True
        mission = environment = None
        if cut_seq is not None and hasattr(self, "_compatibility_at_seq"):
            mission, environment, _ = self._compatibility_at_seq(domain_id, cut_seq)
        elif hasattr(self, "_current_compatibility"):
            mission, environment, _ = self._current_compatibility(domain_id)
        if cut_seq is not None and hasattr(self, "_self_version_at_seq"):
            self_version = self._self_version_at_seq(domain_id, cut_seq)
        else:
            self_version = self._current_self_version(domain_id) if hasattr(self, "_current_self_version") else None
        checks = {
            "mission_revision": mission,
            "environment_revision": environment,
            "self_version": self_version,
        }
        checks.update(requested)
        for key, current in checks.items():
            if key in app and not self._applicability_values_compatible(key, app[key], current):
                return False
        if "allowed_environments" in app and environment not in set(app["allowed_environments"]):
            return False
        if "allowed_self_versions" in app and self_version not in set(app["allowed_self_versions"]):
            return False
        return True

    def _counterexample_blocks_representation(
        self, domain_id: str, representation_id: str, query_family: str, cut_seq: int
    ) -> bool:
        """Whether a material counterexample falsifies this route at the pinned cut.

        Counterexamples are scoped to the representation and query family. Resolution
        after the requested cut must not rewrite the historical projection.
        """
        rows = self.db.execute(
            "SELECT counterexample_id FROM query_counterexamples "
            "WHERE domain_id=? AND representation_id=? AND query_family=? "
            "AND created_seq<=? AND (resolved_seq IS NULL OR resolved_seq>?) ORDER BY created_seq,counterexample_id",
            (domain_id, representation_id, query_family, cut_seq, cut_seq),
        ).fetchall()
        for row in rows:
            if not hasattr(self, "_counterexample_applicability_matches") or self._counterexample_applicability_matches(
                domain_id, row["counterexample_id"], cut_seq
            ):
                return True
        return False

    def resolve_representation(
        self, domain_id: str, *, principal: str, role: RecallRole, cut: RecallCut,
    ) -> RepresentationResolution:
        if cut.domain_id != domain_id:
            raise MemoryTransitionIncomplete("representation-resolution cut belongs to a different domain")
        rows = [
            r for r in self._visible_representations_at_cut(domain_id, role.region_id, principal, cut.sequence)
            if not self._counterexample_blocks_representation(domain_id, r["representation_id"], role.query_family, cut.sequence)
        ]
        options: list[dict[str, Any]] = []
        for row in rows:
            status = self.answerability(row["representation_id"], role.query_family)
            options.append({
                "representation_id": row["representation_id"],
                "answerability": status.value,
                "token_cost": int(row["token_cost"]),
                "kind": row["kind"],
                "transform_profile": row["transform_profile"],
            })
        resolved = self._resolve_role(domain_id, principal, role, cut.sequence)
        if resolved is None:
            selected = None; status = "INSUFFICIENT"
        else:
            row, page_faulted = resolved
            selected = row["representation_id"]
            status = "PAGE_FAULT_SOURCE" if page_faulted else "DIRECT_EXACT"
        created_at = _iso(self._clock())
        receipt = RepresentationResolution(
            resolution_id=f"resolution_{uuid.uuid4().hex}", domain_id=domain_id, principal=principal,
            role=role, cut=cut, selected_representation_id=selected, status=status, options=options, created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO representation_resolutions(resolution_id,domain_id,principal,role_json,cut_json,selected_representation_id,status,options_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (receipt.resolution_id, domain_id, principal, canonical_json(asdict(role)), canonical_json(asdict(cut)),
             selected, status, canonical_json(options), created_at),
        )
        return receipt

    def _representation_history_roots(
        self, domain_id: str, representation_id: str, *, visited: set[str] | None = None,
    ) -> frozenset[str]:
        """Return provenance roots for decision-history independence checks.

        Representation multiplicity is not history multiplicity. Descendants inherit
        their source representation/evidence roots; two independently captured raw
        representations remain separate roots unless they explicitly bind the same
        evidence identity. Cycles fail conservatively to the representation identity.
        """
        seen = set() if visited is None else set(visited)
        if representation_id in seen:
            return frozenset({f"rep:{representation_id}"})
        seen.add(representation_id)
        row = self.db.execute(
            "SELECT source_representation_ids_json,source_evidence_ids_json FROM representations "
            "WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if row is None:
            return frozenset({f"rep:{representation_id}"})
        source_reps = list(json.loads(row["source_representation_ids_json"] or "[]"))
        roots: set[str] = set()
        for source_id in source_reps:
            roots.update(self._representation_history_roots(domain_id, source_id, visited=seen))
        for evidence_id in json.loads(row["source_evidence_ids_json"] or "[]"):
            roots.add(f"evidence:{evidence_id}")
        if not roots:
            roots.add(f"rep:{representation_id}")
        return frozenset(roots)

    def _resolve_role(
        self, domain_id: str, principal: str, role: RecallRole, cut_seq: int, *,
        compatibility_profile: dict[str, str] | None = None, safety_critical_dimensions: set[str] | None = None,
    ) -> tuple[sqlite3.Row, bool] | None:
        reps = [
            r for r in self._visible_representations_at_cut(
                domain_id, role.region_id, principal, cut_seq, compatibility_profile=compatibility_profile,
                safety_critical_dimensions=safety_critical_dimensions
            )
            if not self._counterexample_blocks_representation(
                domain_id, r["representation_id"], role.query_family, cut_seq
            )
        ]
        exact = [r for r in reps if self.answerability(r["representation_id"], role.query_family) == Answerability.EXACT]
        # A strong hard-role query may not collapse multiple decision-distinct exact
        # histories into whichever representation happens to be cheapest. Compare the
        # observable query-family dimensions over every currently admissible exact route.
        # Identical copies normalize to one signature; genuinely different signatures
        # force typed ambiguity.
        if role.hard and len(exact) > 1:
            required = sorted(self._family_requirements(role.query_family))
            history_signatures: dict[frozenset[str], set[str]] = {}
            for row in exact:
                if row["kind"] in {"raw", "source", "artifact"} and hasattr(self, "_capability_available"):
                    if not self._capability_available(domain_id, "source_hydration"):
                        continue
                payload = json.loads(row["payload_json"])
                observable = ({k: payload.get(k, "__MISSING__") for k in required}
                              if isinstance(payload, dict) else payload)
                roots = self._representation_history_roots(domain_id, row["representation_id"])
                history_signatures.setdefault(roots, set()).add(canonical_json(observable))
            # Disagreement *within* one lineage is preservation/verification debt, not
            # independent-history ambiguity. Compare one operational signature per
            # independent root set, using the first cost-ordered exact route in that
            # lineage (the same ordering the resolver uses below).
            independent_signatures: set[str] = set()
            seen_roots: set[frozenset[str]] = set()
            for row in exact:
                roots = self._representation_history_roots(domain_id, row["representation_id"])
                if roots in seen_roots:
                    continue
                seen_roots.add(roots)
                payload = json.loads(row["payload_json"])
                observable = ({k: payload.get(k, "__MISSING__") for k in required}
                              if isinstance(payload, dict) else payload)
                independent_signatures.add(canonical_json(observable))
            if len(independent_signatures) > 1:
                raise MemoryRecallAmbiguous(
                    f"decision-distinct independent histories for hard role {role.role_id!r}"
                )
        # Resolve in cost order. A cheap compact representation may trigger a semantic page fault
        # to an exact source instead of pretending the compact bytes answer the obligation.
        for candidate in reps:
            source_tier = candidate["kind"] in {"raw", "source", "artifact"}
            if source_tier and hasattr(self, "_capability_available") and not self._capability_available(domain_id, "source_hydration"):
                continue
            status = self.answerability(candidate["representation_id"], role.query_family)
            if status == Answerability.EXACT:
                return candidate, False
            if status == Answerability.REHYDRATABLE:
                if hasattr(self, "_capability_available") and not self._capability_available(domain_id, "source_hydration"):
                    continue
                if hasattr(self, "_capability_allowed") and not self._capability_allowed(domain_id, principal, "HYDRATE_SOURCE"):
                    continue
                source_ids = set(json.loads(candidate["source_representation_ids_json"]))
                stronger = [r for r in reps if r["representation_id"] in source_ids and self.answerability(r["representation_id"], role.query_family) == Answerability.EXACT]
                if not stronger:
                    stronger = exact
                if stronger:
                    stronger.sort(key=lambda r: (int(r["token_cost"]), r["representation_id"]))
                    return stronger[0], True
        return None

    def compile_recall(
        self, domain_id: str, principal: str, roles: list[RecallRole], token_budget: int,
        *, page_fault_budget: int | None = None, compatibility_profile: dict[str, str] | None = None,
        safety_critical_dimensions: set[str] | None = None,
    ) -> RecallFrame:
        # Strong recall is one cut-consistent read transaction. In WAL mode another writer
        # may commit while this transaction is open, but every nested read on this connection
        # continues to observe the pinned snapshot. The frame is persisted only after the
        # read transaction closes so projection persistence cannot upgrade it into a writer.
        with self._lock:
            cur = self.db.cursor()
            cur.execute("BEGIN")
            try:
                head = self._head_row(domain_id, cur)  # first read pins the SQLite snapshot
                cut = RecallCut(
                    domain_id, int(head["incarnation"]), int(head["sequence"]), head["root"]
                )
                fragments: list[FrameFragment] = []
                dependencies: dict[tuple[str, str], Dependency] = {}
                total = 0
                page_faults = 0
                for role in roles:
                    dependencies[("query_family", role.query_family)] = Dependency(
                        "query_family", role.query_family,
                        self._generation(domain_id, "query_family", role.query_family, cur),
                    )
                    dependencies[("counterexample", role.region_id)] = Dependency(
                        "counterexample", role.region_id,
                        self._generation(domain_id, "counterexample", role.region_id, cur),
                    )
                    resolved = self._resolve_role(
                        domain_id, principal, role, cut.sequence, compatibility_profile=compatibility_profile,
                        safety_critical_dimensions=safety_critical_dimensions,
                    )
                    if resolved is None:
                        if role.hard:
                            raise MemoryRecallInsufficient(f"hard role {role.role_id!r} has no admissible witness")
                        continue
                    row, page_faulted = resolved
                    if page_faulted:
                        page_faults += 1
                        if page_fault_budget is not None and page_faults > page_fault_budget:
                            if role.hard:
                                raise MemoryViewOverflow(
                                    f"hard recall requires {page_faults} semantic page faults, budget is {page_fault_budget}"
                                )
                            continue
                    cost = int(row["token_cost"])
                    if role.hard and total + cost > token_budget:
                        raise MemoryViewOverflow(
                            f"hard recall cover requires {total + cost} tokens, budget is {token_budget}"
                        )
                    if not role.hard and total + cost > token_budget:
                        continue
                    total += cost
                    fragments.append(FrameFragment(
                        role_id=role.role_id, representation_id=row["representation_id"], region_id=row["region_id"],
                        query_family=role.query_family, payload=json.loads(row["payload_json"]),
                        token_cost=cost, page_faulted=page_faulted,
                    ))
                    for dep_class, dep_key in (
                        ("region", row["region_id"]),
                        ("representation", row["representation_id"]),
                        ("transform_profile", row["transform_profile"]),
                    ):
                        dependencies[(dep_class, dep_key)] = Dependency(
                            dep_class, dep_key, self._generation(domain_id, dep_class, dep_key, cur)
                        )
                # Only global guards that materially govern use are included. Unrelated
                # canonical writes do not bump these generations.
                for dep_class in ("access", "policy", "regime", "hard_obligation", "self_version", "incarnation", "applicability_policy"):
                    dependencies[(dep_class, "global")] = Dependency(
                        dep_class, "global", self._generation(domain_id, dep_class, "global", cur)
                    )
                frame = RecallFrame(
                    frame_id=f"frame_{uuid.uuid4().hex}", domain_id=domain_id, principal=principal, cut=cut,
                    fragments=fragments, dependencies=sorted(dependencies.values(), key=lambda d: (d.dep_class, d.dep_key)),
                    sufficiency="SUFFICIENT", token_cost=total, roles=list(roles),
                )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise

        self.db.execute(
            "INSERT INTO frames(frame_id,domain_id,principal,frame_json,created_at) VALUES(?,?,?,?,?)",
            (frame.frame_id, domain_id, principal, canonical_json(asdict(frame)), _iso(self._clock())),
        )
        return frame

    def assess_frame_sufficiency(
        self, frame: RecallFrame, obligation: RecallObligation | None = None,
    ) -> RecallSufficiencyAssessment:
        if obligation is None:
            hard_roles = [r for r in frame.roles if r.hard]
        else:
            hard_roles = list(obligation.hard_roles)
        hard_ids = [r.role_id for r in hard_roles]
        covered_set = {f.role_id for f in frame.fragments}
        covered = [rid for rid in hard_ids if rid in covered_set]
        unresolved = [rid for rid in hard_ids if rid not in covered_set]
        status = "SUFFICIENT" if frame.sufficiency == "SUFFICIENT" and not unresolved else "INSUFFICIENT"
        created_at = _iso(self._clock())
        assessment = RecallSufficiencyAssessment(
            assessment_id=f"suff_{uuid.uuid4().hex}", frame_id=frame.frame_id, status=status,
            hard_role_ids=hard_ids, covered_hard_role_ids=covered, unresolved_hard_role_ids=unresolved,
            token_cost=frame.token_cost, created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO recall_sufficiency_assessments(assessment_id,frame_id,assessment_json,created_at) VALUES(?,?,?,?)",
            (assessment.assessment_id, frame.frame_id, canonical_json(asdict(assessment)), created_at),
        )
        return assessment

    def materialize_frame_dependency_manifest(self, frame: RecallFrame) -> RecallFrameDependencyManifestRevision:
        dependencies = sorted(frame.dependencies, key=lambda d: (d.dep_class, d.dep_key))
        manifest = RecallFrameDependencyManifestRevision(
            manifest_id=f"manifest_{uuid.uuid4().hex}", frame_id=frame.frame_id, domain_id=frame.domain_id, cut=frame.cut,
            dependencies=dependencies, dependency_digest=self._dependency_digest(dependencies),
            completeness="EXACT_EXPLICIT", created_at=_iso(self._clock()),
        )
        self.db.execute(
            "INSERT INTO frame_dependency_manifests(manifest_id,frame_id,domain_id,cut_json,dependencies_json,dependency_digest,completeness,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (manifest.manifest_id, frame.frame_id, frame.domain_id, canonical_json(asdict(frame.cut)),
             canonical_json([asdict(d) for d in dependencies]), manifest.dependency_digest, manifest.completeness, manifest.created_at),
        )
        return manifest

    def validate_frame_dependency_manifest(self, manifest_id: str) -> bool:
        row = self.db.execute("SELECT * FROM frame_dependency_manifests WHERE manifest_id=?", (manifest_id,)).fetchone()
        if row is None:
            raise KeyError(manifest_id)
        deps = [Dependency(**d) for d in json.loads(row["dependencies_json"])]
        if self._dependency_digest(deps) != row["dependency_digest"]:
            raise MemoryDependencyStale("frame dependency manifest digest mismatch")
        self.validate_dependencies(row["domain_id"], deps)
        return True

    def validate_frame(self, frame_id: str) -> bool:
        row = self.db.execute("SELECT * FROM frames WHERE frame_id=?", (frame_id,)).fetchone()
        if not row:
            raise KeyError(frame_id)
        payload = json.loads(row["frame_json"])
        dependencies = [Dependency(**dep) for dep in payload.get("dependencies", [])]
        self.validate_dependencies(row["domain_id"], dependencies)
        if hasattr(self, "_access_profile_row") and hasattr(self, "_row_expired"):
            profile = self._access_profile_row(row["domain_id"], row["principal"])
            if profile is not None and self._row_expired(profile):
                raise MemoryDependencyStale("access profile expired after frame compilation")
        return True

    @staticmethod
    def _role_identity(role: RecallRole) -> tuple[str, str, str]:
        return (role.role_id, role.region_id, role.query_family)

    @staticmethod
    def _force_role(role: RecallRole, hard: bool) -> RecallRole:
        return RecallRole(
            role_id=role.role_id,
            region_id=role.region_id,
            query_family=role.query_family,
            hard=hard,
            temporal_mode=role.temporal_mode,
            use_capability=role.use_capability,
            risk_class=role.risk_class,
            allow_approximation=role.allow_approximation,
        )

    def compile_boundary_recall(
        self, domain_id: str, boundary: RecallBoundaryDescriptor,
    ) -> tuple[RecallFrame, RecallObligation]:
        """Compile consequence-bound hard memory roles to a local fixed point.

        Host-derived roles are authoritative hard obligations. A selected/hydrated
        representation may reveal more hard prerequisites, which are deduplicated by
        semantic role identity. If a concurrent commit upgrades the cut between closure
        passes, the final frame is recomputed at the new cut rather than mixing bytes.
        """
        if boundary.token_budget < 0 or boundary.page_fault_budget < 0 or boundary.role_budget < 1:
            raise ValueError("boundary budgets must be non-negative and role_budget >= 1")

        hard: dict[tuple[str, str, str], RecallRole] = {}
        optional: dict[tuple[str, str, str], RecallRole] = {}
        hard_sources = (
            boundary.explicit_roles
            + boundary.canonical_constraint_roles
            + boundary.action_tool_roles
            + boundary.revalidation_roles
            + boundary.security_roles
        )
        for role in hard_sources:
            forced = self._force_role(role, True)
            hard[self._role_identity(forced)] = forced

        if boundary.prospective_event_keys and hasattr(self, "fire_prospective_triggers"):
            for event_key in boundary.prospective_event_keys:
                for role in self.fire_prospective_triggers(domain_id, event_key=event_key, principal=boundary.principal):
                    forced = self._force_role(role, True)
                    hard[self._role_identity(forced)] = forced

        for role in boundary.optional_roles:
            forced = self._force_role(role, False)
            key = self._role_identity(forced)
            if key not in hard:
                optional[key] = forced

        if len(hard) + len(optional) > boundary.role_budget:
            raise MemoryViewOverflow("recall obligation exceeds role budget")

        iterations = 0
        last_frame: RecallFrame | None = None
        baseline_cut: RecallCut | None = None
        # Cycles collapse because hard is a set keyed by canonical role identity.
        while True:
            iterations += 1
            if iterations > boundary.role_budget + 2:
                raise MemoryViewOverflow("recall obligation closure did not converge within role budget")
            roles = list(hard.values()) + [r for k, r in optional.items() if k not in hard]
            frame = self.compile_recall(
                domain_id, boundary.principal, roles, boundary.token_budget,
                page_fault_budget=boundary.page_fault_budget, compatibility_profile=boundary.compatibility_profile,
                safety_critical_dimensions=boundary.safety_critical_dimensions,
            )
            if baseline_cut is None:
                baseline_cut = frame.cut
            elif frame.cut != baseline_cut:
                # Explicit cut upgrade: the frame is fresh; continue closure from its
                # current exact representations. Keeping already-discovered hard roles
                # is a conservative over-approximation, never a missing dependency.
                baseline_cut = frame.cut
            last_frame = frame

            added = False
            for frag in frame.fragments:
                row = self.db.execute(
                    "SELECT hard_dependencies_json FROM representations WHERE domain_id=? AND representation_id=?",
                    (domain_id, frag.representation_id),
                ).fetchone()
                if not row:
                    continue
                for raw in json.loads(row[0] or "[]"):
                    dep_role = self._force_role(RecallRole(**raw), True)
                    key = self._role_identity(dep_role)
                    if key not in hard:
                        hard[key] = dep_role
                        optional.pop(key, None)
                        added = True
                        if len(hard) + len(optional) > boundary.role_budget:
                            raise MemoryViewOverflow("recall obligation exceeds role budget")
            if not added:
                break

        assert last_frame is not None
        obligation = RecallObligation(
            hard_roles=list(hard.values()),
            optional_roles=[r for k, r in optional.items() if k not in hard],
            closure_iterations=iterations, compatibility_profile=dict(boundary.compatibility_profile),
            safety_critical_dimensions=set(boundary.safety_critical_dimensions),
        )
        return last_frame, obligation

    def _dependency_digest(self, dependencies: list[Dependency]) -> str:
        return digest([asdict(d) for d in sorted(dependencies, key=lambda x: (x.dep_class, x.dep_key))])

    def validate_dependencies(self, domain_id: str, dependencies: list[Dependency], *, cur: sqlite3.Cursor | None = None) -> None:
        for dep in dependencies:
            current = self._generation(domain_id, dep.dep_class, dep.dep_key, cur)
            if current != dep.generation:
                raise MemoryDependencyStale(
                    f"dependency {dep.dep_class}:{dep.dep_key} generation {dep.generation} -> {current}"
                )

    # ---------- v0.6.3 use-time grounding fence ----------

    def issue_use_fence(
        self, frame: RecallFrame, *, principal: str, sink: str, payload: Any,
        expires_at: datetime | None = None,
    ) -> MemoryUseFence:
        if principal != frame.principal:
            raise MemoryFenceBindingMismatch("principal mismatch against frame")
        self.validate_dependencies(frame.domain_id, frame.dependencies)
        # The final payload/sink is a distinct disclosure boundary. A memory-use fence
        # cannot be minted as a bypass around composed information-flow authorization.
        flow = None
        if hasattr(self, "check_information_flow"):
            flow = self.check_information_flow(frame, principal=principal, sink=sink, payload=payload)
            if flow.decision not in ("ALLOW", "ALLOW_WITH_TRANSFORM"):
                raise MemoryFlowBlocked(f"composed payload is not authorized for sink {sink}: {flow.decision}")
        fence_dependencies = list(frame.dependencies)
        # Sink-time governance is intentionally bound here rather than at frame compile.
        # Permission *widening* after recall can be evaluated by the flow gate without
        # invalidating memory adequacy, while later revocation still invalidates use.
        sink_time_deps = [
            Dependency("tool", sink, self._generation(frame.domain_id, "tool", sink)),
            Dependency("declassification", "global", self._generation(frame.domain_id, "declassification", "global")),
            Dependency("flow_policy", "global", self._generation(frame.domain_id, "flow_policy", "global")),
            Dependency("flow_policy", sink, self._generation(frame.domain_id, "flow_policy", sink)),
        ]
        for dep in sink_time_deps:
            if not any(d.dep_class == dep.dep_class and d.dep_key == dep.dep_key for d in fence_dependencies):
                fence_dependencies.append(dep)
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        # Expiring leases are protected time objects. They require an explicit clock
        # authority and boot/authority epoch; an optional caller timestamp is never
        # allowed to erase expiry semantics.
        if expires_at is not None and (self._clock_authority_id is None or self._clock_epoch is None):
            raise MemoryClockAuthorityRequired("CLOCK_AUTHORITY_REQUIRED: expiring fence has no trusted clock authority/epoch")
        # A use fence may never outlive a declassification grant that justified it.
        if flow is not None and getattr(flow, "declassification_receipt_refs", None):
            expiries = []
            for rid in flow.declassification_receipt_refs:
                r = self.db.execute("SELECT expires_at FROM declassification_receipts WHERE receipt_id=?", (rid,)).fetchone()
                if r and r["expires_at"]:
                    expiries.append(_parse_dt(r["expires_at"]))
            expiries = [x for x in expiries if x is not None]
            if expiries:
                policy_expiry = min(expiries)
                expires_at = policy_expiry if expires_at is None else min(expires_at, policy_expiry)
        if expires_at is not None:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now >= expires_at:
                raise MemoryFenceExpired("cannot issue already-expired fence")
        fence = MemoryUseFence(
            fence_id=f"fence_{uuid.uuid4().hex}", frame_id=frame.frame_id, domain_id=frame.domain_id,
            principal=principal, sink=sink, payload_digest=digest(payload),
            dependency_digest=self._dependency_digest(fence_dependencies), issued_at=_iso(now),
            expires_at=_iso(expires_at), consumed=False,
            clock_authority_id=self._clock_authority_id if expires_at is not None else None,
            clock_epoch=self._clock_epoch if expires_at is not None else None,
            flow_receipt_id=None if flow is None else flow.flow_receipt_id,
        )
        self.db.execute(
            "INSERT INTO fences(fence_id,frame_id,domain_id,principal,sink,payload_digest,dependency_digest,dependencies_json,issued_at,expires_at,consumed_at,clock_authority_id,clock_epoch,flow_receipt_id) VALUES(?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)",
            (fence.fence_id, frame.frame_id, frame.domain_id, principal, sink, fence.payload_digest,
             fence.dependency_digest, canonical_json([asdict(d) for d in fence_dependencies]),
             fence.issued_at, fence.expires_at, fence.clock_authority_id, fence.clock_epoch, fence.flow_receipt_id),
        )
        return fence

    def consume_use_fence(self, fence_id: str, *, principal: str, sink: str, payload: Any) -> bool:
        # Use-time dependency validation is correctness-reserved work. Resource
        # pressure may shed optional memory work, never this boundary check.
        pre = self.db.execute("SELECT domain_id FROM fences WHERE fence_id=?", (fence_id,)).fetchone()
        if pre is not None and hasattr(self, "_capability_available") and not self._capability_available(pre["domain_id"], "use_validation"):
            raise MemoryUseValidationUnavailable("USE_VALIDATION_UNAVAILABLE: dependency state cannot be read at use boundary")
        with self._lock:
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute("SELECT * FROM fences WHERE fence_id=?", (fence_id,)).fetchone()
                if not row:
                    raise KeyError(fence_id)
                if row["consumed_at"] is not None:
                    raise MemoryFenceReplay("memory-use fence is single-use")
                if principal != row["principal"] or sink != row["sink"]:
                    raise MemoryFenceBindingMismatch("principal or sink mismatch")
                if digest(payload) != row["payload_digest"]:
                    raise ActionArgumentMismatch("final payload/action arguments differ from validated binding")
                now = self._clock()
                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)
                expiry = _parse_dt(row["expires_at"])
                if expiry is not None:
                    authority = row["clock_authority_id"]
                    epoch = row["clock_epoch"]
                    if (
                        not authority or not epoch or self._clock_authority_id is None or self._clock_epoch is None
                        or authority != self._clock_authority_id or epoch != self._clock_epoch
                    ):
                        raise MemoryClockAuthorityRequired(
                            "CLOCK_AUTHORITY_REQUIRED: fence clock authority/epoch is unavailable or incompatible"
                        )
                    issued = _parse_dt(row["issued_at"])
                    if issued is not None and now < issued:
                        raise MemoryClockAuthorityRequired(
                            "CLOCK_AUTHORITY_REQUIRED: trusted clock moved before the fence issuance point"
                        )
                    if now >= expiry:
                        raise MemoryFenceExpired("memory-use fence expired")
                if row["flow_receipt_id"] is not None and hasattr(self, "validate_information_flow_receipt"):
                    self.validate_information_flow_receipt(
                        row["flow_receipt_id"], principal=principal, sink=sink, payload=payload, cur=cur
                    )
                dependencies = [Dependency(**d) for d in json.loads(row["dependencies_json"])]
                self.validate_dependencies(row["domain_id"], dependencies, cur=cur)
                if self._dependency_digest(dependencies) != row["dependency_digest"]:
                    raise MemoryIntegrityError("fence dependency digest mismatch")
                cur.execute("UPDATE fences SET consumed_at=? WHERE fence_id=?", (_iso(now), fence_id))
                cur.execute("COMMIT")
                return True
            except Exception:
                cur.execute("ROLLBACK")
                raise

    # ---------- causal cut vector helper ----------

    def add_causal_edge(self, src_domain: str, src_seq: int, dst_domain: str, dst_seq: int) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO causal_edges(src_domain,src_seq,dst_domain,dst_seq) VALUES(?,?,?,?)",
            (src_domain, src_seq, dst_domain, dst_seq),
        )

    def _incarnation_at_sequence(self, domain_id: str, seq: int) -> int:
        head = self._head_row(domain_id)
        if seq > int(head["sequence"]):
            from .errors import MemoryCutUnavailable
            raise MemoryCutUnavailable(f"domain {domain_id} has head {head['sequence']}, requested {seq}")
        if seq == 0:
            first = self.db.execute(
                "SELECT kind,incarnation FROM journal WHERE domain_id=? ORDER BY sequence ASC LIMIT 1",
                (domain_id,),
            ).fetchone()
            if first is None:
                return int(head["incarnation"])
            inc = int(first["incarnation"])
            return inc - 1 if first["kind"] == "START_NEW_INCARNATION" else inc
        row = self.db.execute(
            "SELECT incarnation FROM journal WHERE domain_id=? AND sequence=?", (domain_id, seq)
        ).fetchone()
        if row is None:
            from .errors import MemoryCutUnavailable
            raise MemoryCutUnavailable(f"missing historical incarnation for {domain_id}@{seq}")
        return int(row["incarnation"])

    def close_causal_cut(self, seed: dict[str, int]) -> dict[str, RecallCut]:
        target = dict(seed)
        changed = True
        while changed:
            changed = False
            for row in self.db.execute("SELECT * FROM causal_edges").fetchall():
                dst_seq = target.get(row["dst_domain"], 0)
                if dst_seq >= int(row["dst_seq"]):
                    src_req = int(row["src_seq"])
                    if target.get(row["src_domain"], 0) < src_req:
                        target[row["src_domain"]] = src_req
                        changed = True
        result: dict[str, RecallCut] = {}
        for domain_id, seq in target.items():
            head = self._head_row(domain_id)
            if seq > int(head["sequence"]):
                from .errors import MemoryCutUnavailable
                raise MemoryCutUnavailable(f"domain {domain_id} has head {head['sequence']}, requested {seq}")
            if seq == 0:
                root = GENESIS_ROOT
            else:
                jr = self.db.execute("SELECT root FROM journal WHERE domain_id=? AND sequence=?", (domain_id, seq)).fetchone()
                if not jr:
                    from .errors import MemoryCutUnavailable
                    raise MemoryCutUnavailable(f"missing historical root for {domain_id}@{seq}")
                root = jr["root"]
            result[domain_id] = RecallCut(domain_id, self._incarnation_at_sequence(domain_id, seq), seq, root)
        return result
