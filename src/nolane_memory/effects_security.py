from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Iterable

from .errors import (
    MemoryAccessCapabilityDenied,
    MemoryDependencyStale,
    MemoryFlowBlocked,
    MemoryFlowPolicyCurrentnessUnknown,
    MemoryPublicationBlocked,
    MemoryScopeBlocked,
    MemoryTransitionIncomplete,
)
from .normalize import canonical_json, digest
from .types import (
    ActivationGuardReceipt,
    DeclassificationReceipt,
    EffectEvidence,
    EffectTier,
    FlowDecision,
    FrameInformationFlowReceipt,
    Dependency,
    MemoryExposureReceipt,
    PublicationReceipt,
    RecallFrame,
    RecallRole,
    AccessProfileRevision,
    SelfVersionProfileRevision,
)


class EffectsSecurityMixin:
    def _init_effects_security_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS access_profiles(
              domain_id TEXT NOT NULL, principal TEXT NOT NULL,
              capabilities_json TEXT NOT NULL, sink_capabilities_json TEXT NOT NULL,
              revision INTEGER NOT NULL, updated_seq INTEGER NOT NULL, expires_at TEXT,
              PRIMARY KEY(domain_id,principal)
            );
            CREATE TABLE IF NOT EXISTS access_profile_revisions(
              domain_id TEXT NOT NULL, principal TEXT NOT NULL, revision INTEGER NOT NULL,
              predecessor_revision INTEGER, capabilities_json TEXT NOT NULL,
              sink_capabilities_json TEXT NOT NULL, created_seq INTEGER NOT NULL, expires_at TEXT,
              PRIMARY KEY(domain_id,principal,revision)
            );
            CREATE TABLE IF NOT EXISTS declassification_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, representation_id TEXT NOT NULL,
              principal TEXT NOT NULL, sink TEXT NOT NULL, authority_ref TEXT NOT NULL,
              created_seq INTEGER NOT NULL, revoked_seq INTEGER, expires_at TEXT
            );
            CREATE TABLE IF NOT EXISTS flow_policies(
              domain_id TEXT NOT NULL, policy_id TEXT NOT NULL, sink TEXT NOT NULL,
              forbidden_sets_json TEXT NOT NULL, revision INTEGER NOT NULL, updated_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,policy_id)
            );
            CREATE TABLE IF NOT EXISTS flow_receipts(
              flow_receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, frame_id TEXT NOT NULL,
              principal TEXT NOT NULL, sink TEXT NOT NULL, payload_digest TEXT NOT NULL,
              receipt_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory_exposures(
              exposure_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, frame_id TEXT NOT NULL,
              consumer TEXT NOT NULL, task TEXT NOT NULL, regime TEXT NOT NULL, rendering TEXT NOT NULL,
              candidate_representation_ids_json TEXT NOT NULL, selected_representation_ids_json TEXT NOT NULL,
              rendered_representation_ids_json TEXT NOT NULL, referenced_representation_ids_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS effect_evidence(
              effect_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, representation_ids_json TEXT NOT NULL,
              consumer TEXT NOT NULL, task TEXT NOT NULL, regime TEXT NOT NULL, rendering TEXT NOT NULL,
              outcome_dimension TEXT NOT NULL, tier TEXT NOT NULL, effect REAL NOT NULL,
              confidence REAL NOT NULL, created_at TEXT NOT NULL, exposure_id TEXT
            );
            CREATE TABLE IF NOT EXISTS activation_guard_receipts(
              guard_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, frame_id TEXT NOT NULL,
              receipt_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS prospective_triggers(
              trigger_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, event_key TEXT NOT NULL,
              owner TEXT NOT NULL, roles_json TEXT NOT NULL, active INTEGER NOT NULL,
              created_seq INTEGER NOT NULL, revoked_seq INTEGER,
              expires_at TEXT, causal_frontier_json TEXT NOT NULL DEFAULT '{}',
              source_representation_ids_json TEXT NOT NULL DEFAULT '[]',
              reactivated_seq INTEGER, revoke_reason TEXT, reactivation_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS prospective_trigger_events(
              event_id TEXT PRIMARY KEY, trigger_id TEXT NOT NULL, domain_id TEXT NOT NULL,
              event_kind TEXT NOT NULL, principal TEXT NOT NULL, reason TEXT, created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS self_versions(
              domain_id TEXT PRIMARY KEY, profile_id TEXT NOT NULL, metadata_json TEXT NOT NULL,
              revision INTEGER NOT NULL, updated_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS self_version_revisions(
              domain_id TEXT NOT NULL, revision INTEGER NOT NULL, predecessor_revision INTEGER,
              profile_id TEXT NOT NULL, metadata_json TEXT NOT NULL, created_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,revision)
            );
            CREATE TABLE IF NOT EXISTS origin_roots(
              domain_id TEXT NOT NULL, object_kind TEXT NOT NULL, object_id TEXT NOT NULL,
              root_identity TEXT NOT NULL,
              PRIMARY KEY(domain_id,object_kind,object_id,root_identity)
            );
            CREATE TABLE IF NOT EXISTS publication_receipts(
              publication_id TEXT PRIMARY KEY, source_domain TEXT NOT NULL, source_sequence INTEGER NOT NULL,
              destination_domain TEXT NOT NULL, destination_sequence INTEGER NOT NULL,
              source_representation_id TEXT NOT NULL, destination_evidence_id TEXT NOT NULL,
              origin_roots_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS publication_sagas(
              saga_id TEXT PRIMARY KEY,
              source_domain TEXT NOT NULL,
              source_incarnation INTEGER NOT NULL,
              source_sequence INTEGER NOT NULL,
              source_representation_id TEXT NOT NULL,
              source_rep_generation INTEGER NOT NULL,
              destination_domain TEXT NOT NULL,
              principal TEXT NOT NULL,
              operation_id TEXT NOT NULL,
              origin_roots_json TEXT NOT NULL,
              state TEXT NOT NULL,
              reason TEXT,
              destination_evidence_id TEXT,
              destination_sequence INTEGER,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              publication_policy_id TEXT,
              publication_policy_revision INTEGER,
              publication_policy_generation INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        for table, column, ddl in (
            ("access_profiles", "expires_at", "expires_at TEXT"),
            ("access_profile_revisions", "expires_at", "expires_at TEXT"),
            ("declassification_receipts", "expires_at", "expires_at TEXT"),
        ):
            cols = {row[1] for row in self.db.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                self.db.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
        self.db.execute(
            "INSERT OR IGNORE INTO access_profile_revisions(domain_id,principal,revision,predecessor_revision,capabilities_json,sink_capabilities_json,created_seq,expires_at) "
            "SELECT domain_id,principal,revision,CASE WHEN revision>1 THEN revision-1 END,capabilities_json,sink_capabilities_json,updated_seq,expires_at FROM access_profiles"
        )
        self.db.execute(
            "INSERT OR IGNORE INTO self_version_revisions(domain_id,revision,predecessor_revision,profile_id,metadata_json,created_seq) "
            "SELECT domain_id,revision,CASE WHEN revision>1 THEN revision-1 END,profile_id,metadata_json,updated_seq FROM self_versions"
        )

    # ---------- access capability algebra ----------

    def _access_profile_row(self, domain_id: str, principal: str):
        return self.db.execute(
            "SELECT * FROM access_profiles WHERE domain_id=? AND principal=?",
            (domain_id, principal),
        ).fetchone()

    @staticmethod
    def _access_revision_from_row(row) -> AccessProfileRevision:
        return AccessProfileRevision(
            domain_id=row["domain_id"], principal=row["principal"], revision=int(row["revision"]),
            predecessor_revision=None if row["predecessor_revision"] is None else int(row["predecessor_revision"]),
            capabilities=list(json.loads(row["capabilities_json"])),
            sink_capabilities={k: list(v) for k, v in json.loads(row["sink_capabilities_json"]).items()},
            created_seq=int(row["created_seq"]), expires_at=row["expires_at"],
        )

    def get_access_profile_revision(
        self, domain_id: str, principal: str, *, revision: int | None = None, at_seq: int | None = None,
    ) -> AccessProfileRevision:
        if revision is not None and at_seq is not None:
            raise ValueError("choose revision or at_seq, not both")
        if revision is not None:
            row = self.db.execute(
                "SELECT * FROM access_profile_revisions WHERE domain_id=? AND principal=? AND revision=?",
                (domain_id, principal, revision),
            ).fetchone()
        elif at_seq is not None:
            row = self.db.execute(
                "SELECT * FROM access_profile_revisions WHERE domain_id=? AND principal=? AND created_seq<=? ORDER BY revision DESC LIMIT 1",
                (domain_id, principal, at_seq),
            ).fetchone()
        else:
            row = self.db.execute(
                "SELECT * FROM access_profile_revisions WHERE domain_id=? AND principal=? ORDER BY revision DESC LIMIT 1",
                (domain_id, principal),
            ).fetchone()
        if row is None:
            raise KeyError((domain_id, principal, revision, at_seq))
        return self._access_revision_from_row(row)

    def list_access_profile_revisions(self, domain_id: str, principal: str) -> list[AccessProfileRevision]:
        rows = self.db.execute(
            "SELECT * FROM access_profile_revisions WHERE domain_id=? AND principal=? ORDER BY revision",
            (domain_id, principal),
        ).fetchall()
        return [self._access_revision_from_row(row) for row in rows]

    def _expiry_text(self, value) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _row_expired(self, row) -> bool:
        expires_at = row["expires_at"] if "expires_at" in row.keys() else None
        if not expires_at:
            return False
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return now.astimezone(timezone.utc) >= expiry

    def _capability_allowed(self, domain_id: str, principal: str, capability: str, *, sink: str | None = None) -> bool:
        row = self._access_profile_row(domain_id, principal)
        if row is None:
            # Backward-compatible profile: record-level ACL remains authoritative until a host installs an explicit profile.
            return True
        if self._row_expired(row):
            return False
        global_caps = set(json.loads(row["capabilities_json"]))
        if "*" in global_caps or capability in global_caps:
            return True
        if sink is not None:
            sink_caps = json.loads(row["sink_capabilities_json"])
            for key in (sink, "*"):
                if capability in set(sink_caps.get(key, [])) or "*" in set(sink_caps.get(key, [])):
                    return True
        return False

    def _require_capability(self, domain_id: str, principal: str, capability: str, *, sink: str | None = None) -> None:
        if not self._capability_allowed(domain_id, principal, capability, sink=sink):
            raise MemoryAccessCapabilityDenied(f"{principal} lacks {capability} for {sink or domain_id}")

    def set_access_profile(
        self, domain_id: str, principal: str, capabilities: Iterable[str], *,
        sink_capabilities: dict[str, Iterable[str]] | None = None, expires_at=None,
    ) -> int:
        caps = sorted(set(capabilities))
        sinks = {k: sorted(set(v)) for k, v in sorted((sink_capabilities or {}).items())}
        expiry = self._expiry_text(expires_at)
        existing = self._access_profile_row(domain_id, principal)
        if existing and json.loads(existing["capabilities_json"]) == caps and json.loads(existing["sink_capabilities_json"]) == sinks and existing["expires_at"] == expiry:
            return int(existing["revision"])
        revision = 1 if not existing else int(existing["revision"]) + 1
        request = {"principal": principal, "capabilities": caps, "sink_capabilities": sinks, "revision": revision, "expires_at": expiry}
        object_id = f"access:{principal}:r{revision}"
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO access_profile_revisions(domain_id,principal,revision,predecessor_revision,capabilities_json,sink_capabilities_json,created_seq,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                (domain_id, principal, revision, None if revision == 1 else revision - 1, canonical_json(caps), canonical_json(sinks), seq, expiry),
            )
            cur.execute(
                "INSERT INTO access_profiles(domain_id,principal,capabilities_json,sink_capabilities_json,revision,updated_seq,expires_at) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(domain_id,principal) DO UPDATE SET capabilities_json=excluded.capabilities_json,sink_capabilities_json=excluded.sink_capabilities_json,revision=excluded.revision,updated_seq=excluded.updated_seq,expires_at=excluded.expires_at",
                (domain_id, principal, canonical_json(caps), canonical_json(sinks), revision, seq, expiry),
            )
            self._bump_generation(cur, domain_id, "access", "global")
            self._bump_generation(cur, domain_id, "access", principal)
            return object_id
        self._auto_commit(domain_id, "SET_ACCESS_PROFILE", object_id, request, mutate)
        return revision

    # ---------- declassification and composed flow ----------

    def grant_declassification(
        self, domain_id: str, representation_id: str, *, principal: str, sink: str, authority_ref: str, expires_at=None,
    ) -> DeclassificationReceipt:
        row = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, representation_id)).fetchone()
        if not row:
            raise KeyError(representation_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("cannot declassify inaccessible representation")
        receipt_id = f"declass_{uuid.uuid4().hex}"
        expiry = self._expiry_text(expires_at)
        request = {"representation_id": representation_id, "principal": principal, "sink": sink, "authority_ref": authority_ref, "expires_at": expiry}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO declassification_receipts(receipt_id,domain_id,representation_id,principal,sink,authority_ref,created_seq,revoked_seq,expires_at) VALUES(?,?,?,?,?,?,?,NULL,?)",
                (receipt_id, domain_id, representation_id, principal, sink, authority_ref, seq, expiry),
            )
            self._bump_generation(cur, domain_id, "declassification", "global")
            self._bump_generation(cur, domain_id, "declassification", representation_id)
            return receipt_id
        self._auto_commit(domain_id, "GRANT_DECLASSIFICATION", receipt_id, request, mutate)
        row = self.db.execute("SELECT * FROM declassification_receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
        return DeclassificationReceipt(receipt_id, domain_id, representation_id, principal, sink, authority_ref, int(row["created_seq"]), row["revoked_seq"], row["expires_at"])

    def revoke_declassification(self, domain_id: str, receipt_id: str, *, principal: str) -> None:
        row = self.db.execute("SELECT * FROM declassification_receipts WHERE domain_id=? AND receipt_id=?", (domain_id, receipt_id)).fetchone()
        if not row:
            raise KeyError(receipt_id)
        if row["principal"] != principal:
            raise MemoryScopeBlocked("only bound principal may revoke in this reference profile")
        if row["revoked_seq"] is not None:
            return
        request = {"receipt_id": receipt_id, "principal": principal}
        def mutate(cur, seq):
            current = cur.execute("SELECT * FROM declassification_receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
            if current["revoked_seq"] is None:
                cur.execute("UPDATE declassification_receipts SET revoked_seq=? WHERE receipt_id=?", (seq, receipt_id))
                self._bump_generation(cur, domain_id, "declassification", "global")
                self._bump_generation(cur, domain_id, "declassification", current["representation_id"])
            return receipt_id
        self._auto_commit(domain_id, "REVOKE_DECLASSIFICATION", receipt_id, request, mutate)

    def _active_declassification(self, domain_id: str, representation_id: str, principal: str, sink: str):
        rows = self.db.execute(
            "SELECT * FROM declassification_receipts WHERE domain_id=? AND representation_id=? AND principal=? AND (sink=? OR sink='*') AND revoked_seq IS NULL ORDER BY created_seq DESC",
            (domain_id, representation_id, principal, sink),
        ).fetchall()
        return next((row for row in rows if not self._row_expired(row)), None)

    def register_flow_policy(
        self, domain_id: str, policy_id: str, *, sink: str, forbidden_representation_sets: Iterable[set[str]],
    ) -> int:
        normalized = [sorted(set(x)) for x in forbidden_representation_sets]
        normalized.sort()
        existing = self.db.execute("SELECT * FROM flow_policies WHERE domain_id=? AND policy_id=?", (domain_id, policy_id)).fetchone()
        if existing and existing["sink"] == sink and json.loads(existing["forbidden_sets_json"]) == normalized:
            return int(existing["revision"])
        revision = 1 if not existing else int(existing["revision"]) + 1
        request = {"policy_id": policy_id, "sink": sink, "forbidden_sets": normalized, "revision": revision}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO flow_policies(domain_id,policy_id,sink,forbidden_sets_json,revision,updated_seq) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(domain_id,policy_id) DO UPDATE SET sink=excluded.sink,forbidden_sets_json=excluded.forbidden_sets_json,revision=excluded.revision,updated_seq=excluded.updated_seq",
                (domain_id, policy_id, sink, canonical_json(normalized), revision, seq),
            )
            self._bump_generation(cur, domain_id, "flow_policy", "global")
            self._bump_generation(cur, domain_id, "flow_policy", sink)
            return policy_id
        self._auto_commit(domain_id, "REGISTER_FLOW_POLICY", policy_id, request, mutate)
        return revision

    @staticmethod
    def _sink_capability(sink: str) -> str:
        if sink.startswith("tool:"):
            return "DISCLOSE_TO_TOOL"
        if sink.startswith("user"):
            return "DISCLOSE_TO_USER"
        if sink.startswith("model"):
            return "DISCLOSE_TO_MODEL"
        if sink.startswith("export"):
            return "EXPORT"
        return "USE_FOR_LOCAL_REASONING"

    def check_information_flow(
        self, frame, *, principal: str, sink: str, payload: Any, expires_at=None,
    ) -> FrameInformationFlowReceipt:
        if principal != frame.principal:
            raise MemoryScopeBlocked("flow principal differs from frame principal")
        self.validate_dependencies(frame.domain_id, frame.dependencies)
        capability = self._sink_capability(sink)
        global_allowed = self._capability_allowed(frame.domain_id, principal, capability, sink=sink)
        blocked: list[str] = []
        declass_refs: list[str] = []
        policy_checks: list[str] = [f"capability:{capability}"]
        rep_to_roles: dict[str, list[str]] = {}
        declass_expiries: list[datetime] = []
        for fragment in frame.fragments:
            rep_to_roles.setdefault(fragment.representation_id, []).append(fragment.role_id)
            if global_allowed:
                continue
            dec = self._active_declassification(frame.domain_id, fragment.representation_id, principal, sink)
            if dec:
                declass_refs.append(dec["receipt_id"])
                if dec["expires_at"]:
                    declass_expiries.append(datetime.fromisoformat(dec["expires_at"].replace("Z", "+00:00")))
            else:
                blocked.append(fragment.representation_id)

        rep_set = {f.representation_id for f in frame.fragments}
        policy_blocked: set[str] = set()
        for row in self.db.execute(
            "SELECT * FROM flow_policies WHERE domain_id=? AND (sink=? OR sink='*') ORDER BY policy_id",
            (frame.domain_id, sink),
        ).fetchall():
            for forbidden in json.loads(row["forbidden_sets_json"]):
                fset = set(forbidden)
                if fset and fset.issubset(rep_set):
                    policy_checks.append(f"policy:{row['policy_id']}")
                    policy_blocked |= fset
        blocked_set = set(blocked) | policy_blocked
        hard_role_ids = {role.role_id for role in frame.roles if role.hard}
        hard_affected = sorted({
            role_id
            for rep_id in blocked_set
            for role_id in rep_to_roles.get(rep_id, [])
            if role_id in hard_role_ids
        })
        decision = FlowDecision.BLOCK.value if blocked_set else FlowDecision.ALLOW.value
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        expiry_dt = None
        if expires_at is not None:
            expiry_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00")) if isinstance(expires_at, str) else expires_at
            if expiry_dt.tzinfo is None:
                expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        if declass_expiries:
            declass_expiry = min(declass_expiries)
            expiry_dt = declass_expiry if expiry_dt is None else min(expiry_dt, declass_expiry)
        if expiry_dt is not None:
            if self._clock_authority_id is None or self._clock_epoch is None:
                raise MemoryFlowPolicyCurrentnessUnknown("FLOW_POLICY_CURRENTNESS_UNKNOWN: expiring flow lease lacks trusted clock authority")
            if now >= expiry_dt:
                raise MemoryFlowPolicyCurrentnessUnknown("FLOW_POLICY_CURRENTNESS_UNKNOWN: flow lease already expired")

        dependencies: list[Dependency] = [
            Dependency("access", "global", self._generation(frame.domain_id, "access", "global")),
            Dependency("access", principal, self._generation(frame.domain_id, "access", principal)),
            Dependency("declassification", "global", self._generation(frame.domain_id, "declassification", "global")),
            Dependency("flow_policy", "global", self._generation(frame.domain_id, "flow_policy", "global")),
            Dependency("flow_policy", sink, self._generation(frame.domain_id, "flow_policy", sink)),
            Dependency("tool", sink, self._generation(frame.domain_id, "tool", sink)),
            Dependency("regime", "global", self._generation(frame.domain_id, "regime", "global")),
            Dependency("self_version", "global", self._generation(frame.domain_id, "self_version", "global")),
        ]
        for rep_id in sorted(rep_set):
            dependencies.append(Dependency("representation", rep_id, self._generation(frame.domain_id, "representation", rep_id)))

        receipt = FrameInformationFlowReceipt(
            flow_receipt_id=f"flow_{uuid.uuid4().hex}", frame_id=frame.frame_id,
            candidate_payload_digest=digest(payload), principal=principal, sink=sink,
            source_memory_refs=sorted(rep_set), declassification_receipt_refs=sorted(set(declass_refs)),
            blocked_or_rewritten_fragment_refs=sorted(blocked_set), hard_roles_affected=hard_affected,
            decision=decision, policy_checks=policy_checks, procedure_revision="flow-v0.6.3", created_at=created_at,
            dependencies=dependencies, expires_at=self._expiry_text(expiry_dt),
            clock_authority_id=self._clock_authority_id if expiry_dt is not None else None,
            clock_epoch=self._clock_epoch if expiry_dt is not None else None,
        )
        self.db.execute(
            "INSERT INTO flow_receipts(flow_receipt_id,domain_id,frame_id,principal,sink,payload_digest,receipt_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (receipt.flow_receipt_id, frame.domain_id, frame.frame_id, principal, sink,
             receipt.candidate_payload_digest, canonical_json(asdict(receipt)), created_at),
        )
        return receipt

    def validate_information_flow_receipt(
        self, flow_receipt_id: str, *, principal: str, sink: str, payload: Any, cur=None,
    ) -> bool:
        q = cur if cur is not None else self.db
        row = q.execute("SELECT * FROM flow_receipts WHERE flow_receipt_id=?", (flow_receipt_id,)).fetchone()
        if not row:
            raise KeyError(flow_receipt_id)
        data = json.loads(row["receipt_json"])
        if data.get("decision") not in (FlowDecision.ALLOW.value, "ALLOW_WITH_TRANSFORM"):
            raise MemoryFlowBlocked(f"flow receipt is not an ALLOW lease: {data.get('decision')}")
        if principal != data["principal"] or sink != data["sink"]:
            raise MemoryFlowPolicyCurrentnessUnknown("FLOW_POLICY_CURRENTNESS_UNKNOWN: principal/sink binding changed")
        if digest(payload) != data["candidate_payload_digest"]:
            from .errors import ActionArgumentMismatch
            raise ActionArgumentMismatch("final payload differs from information-flow receipt")
        domain_id = row["domain_id"]
        if hasattr(self, "_capability_available") and not self._capability_available(domain_id, "flow_policy_currentness"):
            raise MemoryFlowPolicyCurrentnessUnknown("FLOW_POLICY_CURRENTNESS_UNKNOWN: current policy state unavailable")
        expires = data.get("expires_at")
        if expires is not None:
            if (
                not data.get("clock_authority_id") or not data.get("clock_epoch")
                or self._clock_authority_id != data.get("clock_authority_id")
                or self._clock_epoch != data.get("clock_epoch")
            ):
                raise MemoryFlowPolicyCurrentnessUnknown("FLOW_POLICY_CURRENTNESS_UNKNOWN: clock authority/epoch unavailable or changed")
            now = self._clock()
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if now >= expiry:
                raise MemoryFlowPolicyCurrentnessUnknown("FLOW_POLICY_CURRENTNESS_UNKNOWN: flow lease expired")
        dependencies = [Dependency(**d) for d in data.get("dependencies", [])]
        try:
            self.validate_dependencies(domain_id, dependencies, cur=cur)
        except MemoryDependencyStale as exc:
            raise MemoryFlowPolicyCurrentnessUnknown(f"FLOW_POLICY_CURRENTNESS_UNKNOWN: {exc}") from exc
        return True

    # ---------- origin roots / governed publication ----------

    def get_origin_roots(self, domain_id: str, object_kind: str, object_id: str) -> list[str]:
        return sorted(r[0] for r in self.db.execute(
            "SELECT root_identity FROM origin_roots WHERE domain_id=? AND object_kind=? AND object_id=? ORDER BY root_identity",
            (domain_id, object_kind, object_id),
        ).fetchall())

    def _representation_origin_roots(self, domain_id: str, representation_id: str, visited: set[str] | None = None) -> set[str]:
        seen = set() if visited is None else visited
        if representation_id in seen:
            return set()
        seen.add(representation_id)
        direct = set(self.get_origin_roots(domain_id, "representation", representation_id))
        if direct:
            return direct
        row = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, representation_id)).fetchone()
        if not row:
            return set()
        roots: set[str] = set()
        for eid in json.loads(row["source_evidence_ids_json"]):
            roots.update(self.get_origin_roots(domain_id, "evidence", eid))
        for rid in json.loads(row["source_representation_ids_json"]):
            roots.update(self._representation_origin_roots(domain_id, rid, set(seen)))
        if not roots:
            roots.add(f"opaque-representation:{domain_id}:{representation_id}")
        return roots

    def get_publication_saga(self, saga_id: str) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM publication_sagas WHERE saga_id=?", (saga_id,)).fetchone()
        if not row:
            raise KeyError(saga_id)
        return {
            "saga_id": row["saga_id"],
            "source_domain": row["source_domain"],
            "source_incarnation": int(row["source_incarnation"]),
            "source_sequence": int(row["source_sequence"]),
            "source_representation_id": row["source_representation_id"],
            "source_rep_generation": int(row["source_rep_generation"]),
            "destination_domain": row["destination_domain"],
            "principal": row["principal"],
            "operation_id": row["operation_id"],
            "origin_roots": list(json.loads(row["origin_roots_json"])),
            "state": row["state"],
            "reason": row["reason"],
            "destination_evidence_id": row["destination_evidence_id"],
            "destination_sequence": None if row["destination_sequence"] is None else int(row["destination_sequence"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "publication_policy_id": row["publication_policy_id"],
            "publication_policy_revision": None if row["publication_policy_revision"] is None else int(row["publication_policy_revision"]),
            "publication_policy_generation": int(row["publication_policy_generation"] or 0),
        }

    def prepare_publication(
        self, source_domain: str, destination_domain: str, representation_id: str, *,
        principal: str, operation_id: str,
    ) -> dict[str, Any]:
        """Commit source-side publication intent without pretending cross-domain atomicity."""
        self._require_capability(source_domain, principal, "PUBLISH_TO_DOMAIN", sink=f"domain:{destination_domain}")
        policy = self._active_publication_policy(source_domain, destination_domain) if hasattr(self, "_active_publication_policy") else None
        policy_generation = self._generation(source_domain, "publication_policy", destination_domain)
        if policy is not None:
            allowed = set(json.loads(policy["allowed_principals_json"]))
            if self._row_expired(policy):
                raise MemoryPublicationBlocked("publication policy expired")
            if not bool(policy["allow_transfer"]) or (principal not in allowed and "*" not in allowed):
                raise MemoryPublicationBlocked("publication policy blocks this transfer/principal")
            if not bool(policy["preserve_origin"]):
                raise MemoryPublicationBlocked("reference publication profile requires origin preservation")
        saga_id = f"pub_saga_{digest([source_domain, destination_domain, representation_id, operation_id])[:24]}"
        existing = self.db.execute("SELECT 1 FROM publication_sagas WHERE saga_id=?", (saga_id,)).fetchone()
        if existing:
            return self.get_publication_saga(saga_id)
        rep = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (source_domain, representation_id),
        ).fetchone()
        if rep is not None and hasattr(self, "_representation_sources_live_at_cut"):
            if not self._representation_sources_live_at_cut(source_domain, representation_id, self.head(source_domain).sequence):
                raise MemoryPublicationBlocked("source representation derivation basis is revoked/deleted/compromised")
        if not rep or rep["invalidated_seq"] is not None or rep["tainted_seq"] is not None:
            raise MemoryPublicationBlocked("source representation unavailable")
        if not self._is_allowed(principal, rep["allowed_principals_json"]):
            raise MemoryScopeBlocked("source representation inaccessible")
        roots = sorted(self._representation_origin_roots(source_domain, representation_id))
        now = self._clock()
        if now.tzinfo is None: now = now.replace(tzinfo=timezone.utc)
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        request = {
            "saga_id": saga_id, "destination_domain": destination_domain,
            "representation_id": representation_id, "principal": principal,
            "operation_id": operation_id, "origin_roots": roots,
            "publication_policy_id": None if policy is None else policy["policy_id"],
            "publication_policy_revision": None if policy is None else int(policy["revision"]),
            "publication_policy_generation": policy_generation,
        }
        def mutate(cur, seq):
            head = self._head_row(source_domain, cur)
            rep_current = cur.execute(
                "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
                (source_domain, representation_id),
            ).fetchone()
            if not rep_current or rep_current["invalidated_seq"] is not None or rep_current["tainted_seq"] is not None:
                raise MemoryPublicationBlocked("source changed before publication preparation")
            rep_generation = self._generation(source_domain, "representation", representation_id, cur)
            cur.execute(
                "INSERT INTO publication_sagas(saga_id,source_domain,source_incarnation,source_sequence,source_representation_id,source_rep_generation,destination_domain,principal,operation_id,origin_roots_json,state,reason,destination_evidence_id,destination_sequence,created_at,updated_at,publication_policy_id,publication_policy_revision,publication_policy_generation) VALUES(?,?,?,?,?,?,?,?,?,?,? ,NULL,NULL,NULL,?,?,?,?,?)",
                (saga_id, source_domain, int(head["incarnation"]), seq, representation_id,
                 rep_generation, destination_domain, principal, operation_id,
                 canonical_json(roots), "DEST_PENDING", created_at, created_at,
                 None if policy is None else policy["policy_id"], None if policy is None else int(policy["revision"]), policy_generation),
            )
            self._bump_generation(cur, source_domain, "publication", saga_id)
            return saga_id
        self._auto_commit(source_domain, "PREPARE_PUBLICATION", saga_id, request, mutate)
        return self.get_publication_saga(saga_id)

    def _set_publication_saga_state(self, saga_id: str, state: str, *, reason: str | None = None) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM publication_sagas WHERE saga_id=?", (saga_id,)).fetchone()
        if not row: raise KeyError(saga_id)
        domain = row["source_domain"]
        request = {"saga_id": saga_id, "state": state, "reason": reason}
        def mutate(cur, seq):
            now = self._clock()
            if now.tzinfo is None: now = now.replace(tzinfo=timezone.utc)
            updated = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            cur.execute("UPDATE publication_sagas SET state=?,reason=?,updated_at=? WHERE saga_id=?", (state, reason, updated, saga_id))
            self._bump_generation(cur, domain, "publication", saga_id)
            return saga_id
        self._auto_commit(domain, "UPDATE_PUBLICATION_SAGA", saga_id, request, mutate)
        return self.get_publication_saga(saga_id)

    def complete_publication(
        self, saga_id: str, *, accept: bool, reason: str | None = None,
    ) -> PublicationReceipt | dict[str, Any]:
        saga = self.get_publication_saga(saga_id)
        if saga["state"] == "DEST_ADMITTED":
            row = self.db.execute("SELECT * FROM publication_receipts WHERE publication_id=?", (saga_id,)).fetchone()
            if not row: raise MemoryPublicationBlocked("admitted publication receipt missing")
            return PublicationReceipt(row["publication_id"], row["source_domain"], int(row["source_sequence"]), row["destination_domain"], int(row["destination_sequence"]), row["source_representation_id"], row["destination_evidence_id"], list(json.loads(row["origin_roots_json"])), row["created_at"])
        if saga["state"] != "DEST_PENDING":
            return saga

        source_domain = saga["source_domain"]
        rep_id = saga["source_representation_id"]
        rep = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (source_domain, rep_id)
        ).fetchone()
        current_gen = self._generation(source_domain, "representation", rep_id)
        if (not rep or rep["invalidated_seq"] is not None or rep["tainted_seq"] is not None
                or current_gen != saga["source_rep_generation"]
                or self.head(source_domain).incarnation != saga["source_incarnation"]):
            self._set_publication_saga_state(saga_id, "SOURCE_REVALIDATION_REQUIRED", reason="source dependency changed")
            raise MemoryPublicationBlocked("source publication dependency changed while destination was pending")

        current_policy_generation = self._generation(source_domain, "publication_policy", saga["destination_domain"])
        if current_policy_generation != saga["publication_policy_generation"]:
            self._set_publication_saga_state(saga_id, "SOURCE_REVALIDATION_REQUIRED", reason="publication policy changed")
            raise MemoryPublicationBlocked("publication policy changed while destination was pending")
        if saga["publication_policy_id"] is not None:
            current_policy = self._active_publication_policy(source_domain, saga["destination_domain"])
            allowed = set(json.loads(current_policy["allowed_principals_json"])) if current_policy else set()
            if (not current_policy or current_policy["policy_id"] != saga["publication_policy_id"]
                    or int(current_policy["revision"]) != saga["publication_policy_revision"]
                    or self._row_expired(current_policy)
                    or not bool(current_policy["allow_transfer"])
                    or (saga["principal"] not in allowed and "*" not in allowed)
                    or not bool(current_policy["preserve_origin"])):
                self._set_publication_saga_state(saga_id, "SOURCE_REVALIDATION_REQUIRED", reason="publication policy no longer authorizes transfer")
                raise MemoryPublicationBlocked("publication policy no longer authorizes transfer")

        if not accept:
            return self._set_publication_saga_state(saga_id, "DEST_REJECTED", reason=reason or "destination rejected")

        destination_domain = saga["destination_domain"]
        principal = saga["principal"]
        dst_head = self._head_row(destination_domain)
        capture = self.capture_evidence(
            domain_id=destination_domain, operation_id=saga["operation_id"],
            expected_seq=int(dst_head["sequence"]), writer_epoch=int(dst_head["writer_epoch"]),
            source_event_identity=f"publication:{source_domain}:{saga['source_sequence']}:{rep_id}",
            content=json.loads(rep["payload_json"]), principal=principal,
            allowed_principals=json.loads(rep["allowed_principals_json"]),
            origin_roots=saga["origin_roots"],
        )
        self.add_causal_edge(source_domain, saga["source_sequence"], destination_domain, capture.commit_seq)
        now = self._clock()
        if now.tzinfo is None: now = now.replace(tzinfo=timezone.utc)
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        request = {"saga_id": saga_id, "destination_evidence_id": capture.object_id, "destination_sequence": capture.commit_seq}
        def mutate(cur, seq):
            # Revalidate again at the source-side completion linearization point.
            current = cur.execute("SELECT * FROM representations WHERE representation_id=?", (rep_id,)).fetchone()
            if not current or current["invalidated_seq"] is not None or current["tainted_seq"] is not None or self._generation(source_domain, "representation", rep_id, cur) != saga["source_rep_generation"]:
                raise MemoryPublicationBlocked("source changed before publication completion receipt")
            cur.execute(
                "UPDATE publication_sagas SET state='DEST_ADMITTED',destination_evidence_id=?,destination_sequence=?,updated_at=? WHERE saga_id=?",
                (capture.object_id, capture.commit_seq, created_at, saga_id),
            )
            cur.execute(
                "INSERT OR REPLACE INTO publication_receipts(publication_id,source_domain,source_sequence,destination_domain,destination_sequence,source_representation_id,destination_evidence_id,origin_roots_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (saga_id, source_domain, saga["source_sequence"], destination_domain, capture.commit_seq,
                 rep_id, capture.object_id, canonical_json(saga["origin_roots"]), created_at),
            )
            self._bump_generation(cur, source_domain, "publication", saga_id)
            return saga_id
        self._auto_commit(source_domain, "COMPLETE_PUBLICATION", saga_id, request, mutate)
        return PublicationReceipt(saga_id, source_domain, saga["source_sequence"], destination_domain,
                                  capture.commit_seq, rep_id, capture.object_id, saga["origin_roots"], created_at)

    def publish_representation(
        self, source_domain: str, destination_domain: str, representation_id: str, *,
        principal: str, operation_id: str,
    ) -> PublicationReceipt:
        saga = self.prepare_publication(
            source_domain, destination_domain, representation_id,
            principal=principal, operation_id=operation_id,
        )
        result = self.complete_publication(saga["saga_id"], accept=True)
        if not isinstance(result, PublicationReceipt):
            raise MemoryPublicationBlocked(f"publication did not reach destination admission: {result['state']}")
        return result

    # ---------- consumer-scoped effect evidence / interference ----------

    @staticmethod
    def _stable_unique_ids(values: Iterable[str]) -> list[str]:
        seen: set[str] = set(); out: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value); out.append(value)
        return out

    def record_memory_exposure(
        self, domain_id: str, *, frame_id: str, consumer: str, task: str, regime: str, rendering: str,
        candidate_representation_ids: Iterable[str], selected_representation_ids: Iterable[str],
        rendered_representation_ids: Iterable[str], referenced_representation_ids: Iterable[str],
    ) -> MemoryExposureReceipt:
        frame = self.db.execute("SELECT 1 FROM frames WHERE domain_id=? AND frame_id=?", (domain_id, frame_id)).fetchone()
        if not frame:
            raise KeyError(frame_id)
        candidate = self._stable_unique_ids(candidate_representation_ids)
        selected = self._stable_unique_ids(selected_representation_ids)
        rendered = self._stable_unique_ids(rendered_representation_ids)
        referenced = self._stable_unique_ids(referenced_representation_ids)
        if not set(selected).issubset(candidate):
            raise MemoryTransitionIncomplete("selected memory was not in candidate exposure set")
        if not set(rendered).issubset(selected):
            raise MemoryTransitionIncomplete("rendered memory was not selected")
        if not set(referenced).issubset(rendered):
            raise MemoryTransitionIncomplete("referenced memory was not rendered")
        for rep_id in candidate:
            if not self.db.execute("SELECT 1 FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, rep_id)).fetchone():
                raise KeyError(rep_id)
        now=self._clock()
        if now.tzinfo is None: now=now.replace(tzinfo=timezone.utc)
        created_at=now.astimezone(timezone.utc).isoformat().replace("+00:00","Z")
        receipt=MemoryExposureReceipt(
            exposure_id=f"exposure_{uuid.uuid4().hex}", domain_id=domain_id, frame_id=frame_id,
            consumer=consumer, task=task, regime=regime, rendering=rendering,
            candidate_representation_ids=candidate, selected_representation_ids=selected,
            rendered_representation_ids=rendered, referenced_representation_ids=referenced, created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO memory_exposures(exposure_id,domain_id,frame_id,consumer,task,regime,rendering,candidate_representation_ids_json,selected_representation_ids_json,rendered_representation_ids_json,referenced_representation_ids_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (receipt.exposure_id,domain_id,frame_id,consumer,task,regime,rendering,canonical_json(candidate),canonical_json(selected),canonical_json(rendered),canonical_json(referenced),created_at),
        )
        return receipt

    def get_memory_exposure(self, exposure_id: str) -> MemoryExposureReceipt:
        row=self.db.execute("SELECT * FROM memory_exposures WHERE exposure_id=?",(exposure_id,)).fetchone()
        if not row: raise KeyError(exposure_id)
        return MemoryExposureReceipt(
            row["exposure_id"],row["domain_id"],row["frame_id"],row["consumer"],row["task"],row["regime"],row["rendering"],
            json.loads(row["candidate_representation_ids_json"]),json.loads(row["selected_representation_ids_json"]),
            json.loads(row["rendered_representation_ids_json"]),json.loads(row["referenced_representation_ids_json"]),row["created_at"]
        )

    def record_effect_evidence(
        self, domain_id: str, representation_ids: Iterable[str], *, consumer: str, task: str,
        regime: str, rendering: str, outcome_dimension: str, tier: EffectTier | str,
        effect: float, confidence: float, exposure_id: str | None = None,
    ) -> EffectEvidence:
        tier_value = tier.value if isinstance(tier, EffectTier) else str(tier)
        if tier_value not in {x.value for x in EffectTier}:
            raise ValueError(f"unknown effect tier {tier_value!r}")
        if not -1.0 <= float(effect) <= 1.0:
            raise ValueError("effect must be within [-1, 1]")
        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence must be within [0, 1]")
        rep_ids = sorted(set(representation_ids))
        for rep_id in rep_ids:
            row = self.db.execute(
                "SELECT 1 FROM representations WHERE domain_id=? AND representation_id=?",
                (domain_id, rep_id),
            ).fetchone()
            if not row:
                raise KeyError(rep_id)
        if exposure_id is not None:
            exposure = self.get_memory_exposure(exposure_id)
            if exposure.domain_id != domain_id or (exposure.consumer, exposure.task, exposure.regime, exposure.rendering) != (consumer, task, regime, rendering):
                raise MemoryTransitionIncomplete("effect evidence scope does not match memory exposure")
            if not set(rep_ids).issubset(set(exposure.rendered_representation_ids)):
                raise MemoryTransitionIncomplete("effect evidence names memory that was not rendered in exposure")
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        effect_id = f"effect_{uuid.uuid4().hex}"
        self.db.execute(
            "INSERT INTO effect_evidence(effect_id,domain_id,representation_ids_json,consumer,task,regime,rendering,outcome_dimension,tier,effect,confidence,created_at,exposure_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (effect_id, domain_id, canonical_json(rep_ids), consumer, task, regime, rendering,
             outcome_dimension, tier_value, float(effect), float(confidence), created_at, exposure_id),
        )
        return EffectEvidence(
            effect_id, domain_id, rep_ids, consumer, task, regime, rendering, outcome_dimension,
            tier_value, float(effect), float(confidence), created_at, exposure_id,
        )

    def _strong_negative_effect_representations(
        self, domain_id: str, *, consumer: str, task: str, regime: str, rendering: str,
    ) -> set[str]:
        # Conservative reference profile: only paired/controlled interventions with high
        # confidence can inhibit an optional representation. E0/E1/E2 remain evidence,
        # but never become a veto in this profile.
        rows = self.db.execute(
            "SELECT * FROM effect_evidence WHERE domain_id=? AND consumer=? AND task=? AND regime=? AND rendering=? AND tier IN ('E3','E4') AND effect<0 AND confidence>=0.8",
            (domain_id, consumer, task, regime, rendering),
        ).fetchall()
        harmful: set[str] = set()
        for row in rows:
            harmful.update(json.loads(row["representation_ids_json"]))
        return harmful

    def apply_interference_guard(
        self, frame: RecallFrame, *, consumer: str, task: str, regime: str, rendering: str,
    ) -> tuple[RecallFrame, ActivationGuardReceipt]:
        self.validate_dependencies(frame.domain_id, frame.dependencies)
        if hasattr(self, "_capability_available") and not self._capability_available(frame.domain_id, "effect_ledger"):
            now = self._clock()
            if now.tzinfo is None: now = now.replace(tzinfo=timezone.utc)
            created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            receipt = ActivationGuardReceipt(
                guard_id=f"guard_{uuid.uuid4().hex}", frame_id=frame.frame_id, consumer=consumer, task=task,
                regime=regime, rendering=rendering, inhibited_optional_representation_ids=[], blocked_hard_role_ids=[],
                decision="DEGRADED_EFFECT_LEDGER_UNAVAILABLE", created_at=created_at,
            )
            self.db.execute(
                "INSERT INTO activation_guard_receipts(guard_id,domain_id,frame_id,receipt_json,created_at) VALUES(?,?,?,?,?)",
                (receipt.guard_id, frame.domain_id, frame.frame_id, canonical_json(asdict(receipt)), created_at),
            )
            return frame, receipt
        harmful = self._strong_negative_effect_representations(
            frame.domain_id, consumer=consumer, task=task, regime=regime, rendering=rendering,
        )
        hard_role_ids = {r.role_id for r in frame.roles if r.hard}
        inhibited: list[str] = []
        blocked_hard: list[str] = []
        kept = []
        for fragment in frame.fragments:
            if fragment.representation_id not in harmful:
                kept.append(fragment)
                continue
            if fragment.role_id in hard_role_ids:
                # Effect evidence cannot erase a hard semantic role. Keep the witness and
                # expose the conflict so a host can prefer another rendering/witness later.
                kept.append(fragment)
                blocked_hard.append(fragment.role_id)
            else:
                inhibited.append(fragment.representation_id)
        guarded = RecallFrame(
            frame_id=f"guarded_{uuid.uuid4().hex}", domain_id=frame.domain_id, principal=frame.principal,
            cut=frame.cut, fragments=kept, dependencies=list(frame.dependencies),
            sufficiency=frame.sufficiency, token_cost=sum(f.token_cost for f in kept), roles=list(frame.roles),
        )
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        created_at = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        receipt = ActivationGuardReceipt(
            guard_id=f"guard_{uuid.uuid4().hex}", frame_id=frame.frame_id, consumer=consumer,
            task=task, regime=regime, rendering=rendering,
            inhibited_optional_representation_ids=sorted(inhibited),
            blocked_hard_role_ids=sorted(set(blocked_hard)),
            decision="HARD_ROLE_PRESERVED" if blocked_hard else ("OPTIONAL_INHIBITED" if inhibited else "NO_CHANGE"),
            created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO activation_guard_receipts(guard_id,domain_id,frame_id,receipt_json,created_at) VALUES(?,?,?,?,?)",
            (receipt.guard_id, frame.domain_id, frame.frame_id, canonical_json(asdict(receipt)), created_at),
        )
        return guarded, receipt

    # ---------- prospective memory and self-version ----------

    @staticmethod
    def _normalize_expiry(expires_at) -> str | None:
        if expires_at is None:
            return None
        if isinstance(expires_at, str):
            dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        else:
            dt = expires_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _prospective_source_live(self, domain_id: str, representation_id: str) -> bool:
        row = self.db.execute(
            "SELECT invalidated_seq,tainted_seq FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        return bool(row and row["invalidated_seq"] is None and row["tainted_seq"] is None)

    def _prospective_frontier_covered(self, frontier: dict[str, int]) -> bool:
        for authority_domain, required_sequence in frontier.items():
            row = self.db.execute(
                "SELECT sequence FROM domains WHERE domain_id=?", (authority_domain,)
            ).fetchone()
            if not row or int(row["sequence"]) < int(required_sequence):
                return False
        return True

    def _prospective_status_from_row(self, row) -> str:
        if not bool(row["active"]) or row["revoked_seq"] is not None:
            return "REVOKED"
        expiry = row["expires_at"]
        if expiry is not None:
            now = self._clock()
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            expires = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if now.astimezone(timezone.utc) >= expires:
                return "EXPIRED"
        source_ids = list(json.loads(row["source_representation_ids_json"] or "[]"))
        if any(not self._prospective_source_live(row["domain_id"], rid) for rid in source_ids):
            return "SOURCE_STALE"
        frontier = dict(json.loads(row["causal_frontier_json"] or "{}"))
        if not self._prospective_frontier_covered(frontier):
            return "FRONTIER_BLOCKED"
        return "ACTIVE"

    def register_prospective_trigger(
        self, domain_id: str, event_key: str, *, owner: str, roles: Iterable[RecallRole],
        expires_at=None, causal_frontier: dict[str, int] | None = None,
        source_representation_ids: Iterable[str] | None = None,
    ) -> str:
        unique: dict[tuple[str, str, str, bool], RecallRole] = {}
        for role in roles:
            unique[(role.role_id, role.region_id, role.query_family, role.hard)] = role
        normalized = [asdict(r) for r in sorted(unique.values(), key=lambda r: (r.role_id, r.region_id, r.query_family, r.hard))]
        expiry = self._normalize_expiry(expires_at)
        frontier = {str(k): int(v) for k, v in sorted((causal_frontier or {}).items())}
        source_ids = sorted(set(source_representation_ids or []))
        for rid in source_ids:
            if not self._prospective_source_live(domain_id, rid):
                raise MemoryDependencyStale(f"prospective source {rid!r} is unavailable")
        trigger_id = f"trigger_{digest([domain_id, event_key, owner, normalized, expiry, frontier, source_ids])[:24]}"
        existing = self.db.execute("SELECT * FROM prospective_triggers WHERE trigger_id=?", (trigger_id,)).fetchone()
        if existing:
            # CREATE is idempotent only. Revocation is sticky until an explicit
            # REACTIVATE transition, avoiding cancellation resurrection.
            return trigger_id
        request = {
            "event_key": event_key, "owner": owner, "roles": normalized, "expires_at": expiry,
            "causal_frontier": frontier, "source_representation_ids": source_ids,
        }
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO prospective_triggers(trigger_id,domain_id,event_key,owner,roles_json,active,created_seq,revoked_seq,expires_at,causal_frontier_json,source_representation_ids_json,reactivated_seq,revoke_reason,reactivation_reason) "
                "VALUES(?,?,?,?,?,1,?,NULL,?,?,?,NULL,NULL,NULL)",
                (trigger_id, domain_id, event_key, owner, canonical_json(normalized), seq, expiry,
                 canonical_json(frontier), canonical_json(source_ids)),
            )
            cur.execute(
                "INSERT INTO prospective_trigger_events(event_id,trigger_id,domain_id,event_kind,principal,reason,created_seq) VALUES(?,?,?,?,?,?,?)",
                (f"pte_{uuid.uuid4().hex}", trigger_id, domain_id, "REGISTER", owner, None, seq),
            )
            self._bump_generation(cur, domain_id, "hard_obligation", "global")
            self._bump_generation(cur, domain_id, "prospective_trigger", trigger_id)
            return trigger_id
        self._auto_commit(domain_id, "REGISTER_PROSPECTIVE_TRIGGER", trigger_id, request, mutate)
        return trigger_id

    def get_prospective_trigger(self, trigger_id: str) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM prospective_triggers WHERE trigger_id=?", (trigger_id,)).fetchone()
        if not row:
            raise KeyError(trigger_id)
        return {
            "trigger_id": row["trigger_id"], "domain_id": row["domain_id"], "event_key": row["event_key"],
            "owner": row["owner"], "roles": json.loads(row["roles_json"]),
            "expires_at": row["expires_at"], "causal_frontier": json.loads(row["causal_frontier_json"] or "{}"),
            "source_representation_ids": json.loads(row["source_representation_ids_json"] or "[]"),
            "created_seq": int(row["created_seq"]), "revoked_seq": row["revoked_seq"],
            "reactivated_seq": row["reactivated_seq"], "status": self._prospective_status_from_row(row),
        }

    def revoke_prospective_trigger(self, domain_id: str, trigger_id: str, *, principal: str, reason: str) -> str:
        row = self.db.execute("SELECT * FROM prospective_triggers WHERE domain_id=? AND trigger_id=?", (domain_id, trigger_id)).fetchone()
        if not row:
            raise KeyError(trigger_id)
        if row["owner"] not in (principal, "*"):
            raise MemoryScopeBlocked("only trigger owner may revoke prospective memory")
        if row["revoked_seq"] is not None or not bool(row["active"]):
            return trigger_id
        request = {"trigger_id": trigger_id, "principal": principal, "reason": reason}
        def mutate(cur, seq):
            current = cur.execute("SELECT active,revoked_seq FROM prospective_triggers WHERE trigger_id=?", (trigger_id,)).fetchone()
            if current["revoked_seq"] is None and bool(current["active"]):
                cur.execute("UPDATE prospective_triggers SET active=0,revoked_seq=?,revoke_reason=? WHERE trigger_id=?", (seq, reason, trigger_id))
                cur.execute(
                    "INSERT INTO prospective_trigger_events(event_id,trigger_id,domain_id,event_kind,principal,reason,created_seq) VALUES(?,?,?,?,?,?,?)",
                    (f"pte_{uuid.uuid4().hex}", trigger_id, domain_id, "REVOKE", principal, reason, seq),
                )
                self._bump_generation(cur, domain_id, "hard_obligation", "global")
                self._bump_generation(cur, domain_id, "prospective_trigger", trigger_id)
            return trigger_id
        self._auto_commit(domain_id, "REVOKE_PROSPECTIVE_TRIGGER", trigger_id, request, mutate)
        return trigger_id

    def reactivate_prospective_trigger(self, domain_id: str, trigger_id: str, *, principal: str, reason: str) -> str:
        row = self.db.execute("SELECT * FROM prospective_triggers WHERE domain_id=? AND trigger_id=?", (domain_id, trigger_id)).fetchone()
        if not row:
            raise KeyError(trigger_id)
        if row["owner"] not in (principal, "*"):
            raise MemoryScopeBlocked("only trigger owner may reactivate prospective memory")
        if bool(row["active"]) and row["revoked_seq"] is None:
            return trigger_id
        # Reauthorization never overrides expiry, lost source lineage, or an unmet
        # causal frontier. Those are semantic eligibility conditions, not ACL bits.
        shadow = dict(row)
        shadow["active"] = 1; shadow["revoked_seq"] = None
        class _Row(dict):
            __getattr__ = dict.__getitem__
        if self._prospective_status_from_row(_Row(shadow)) != "ACTIVE":
            raise MemoryDependencyStale("prospective trigger cannot be reactivated under current dependencies")
        request = {"trigger_id": trigger_id, "principal": principal, "reason": reason}
        def mutate(cur, seq):
            cur.execute(
                "UPDATE prospective_triggers SET active=1,revoked_seq=NULL,reactivated_seq=?,reactivation_reason=? WHERE trigger_id=?",
                (seq, reason, trigger_id),
            )
            cur.execute(
                "INSERT INTO prospective_trigger_events(event_id,trigger_id,domain_id,event_kind,principal,reason,created_seq) VALUES(?,?,?,?,?,?,?)",
                (f"pte_{uuid.uuid4().hex}", trigger_id, domain_id, "REACTIVATE", principal, reason, seq),
            )
            self._bump_generation(cur, domain_id, "hard_obligation", "global")
            self._bump_generation(cur, domain_id, "prospective_trigger", trigger_id)
            return trigger_id
        self._auto_commit(domain_id, "REACTIVATE_PROSPECTIVE_TRIGGER", trigger_id, request, mutate)
        return trigger_id

    def fire_prospective_triggers(self, domain_id: str, event_key: str, *, principal: str) -> list[RecallRole]:
        rows = self.db.execute(
            "SELECT * FROM prospective_triggers WHERE domain_id=? AND event_key=? ORDER BY trigger_id",
            (domain_id, event_key),
        ).fetchall()
        unique: dict[tuple[str, str, str, bool], RecallRole] = {}
        for row in rows:
            if row["owner"] not in (principal, "*") or self._prospective_status_from_row(row) != "ACTIVE":
                continue
            for obj in json.loads(row["roles_json"]):
                role = RecallRole(**obj)
                unique[(role.role_id, role.region_id, role.query_family, role.hard)] = role
        return sorted(unique.values(), key=lambda r: (r.role_id, r.region_id, r.query_family, r.hard))

    @staticmethod
    def _self_version_revision_from_row(row) -> SelfVersionProfileRevision:
        return SelfVersionProfileRevision(
            domain_id=row["domain_id"], revision=int(row["revision"]),
            predecessor_revision=None if row["predecessor_revision"] is None else int(row["predecessor_revision"]),
            profile_id=row["profile_id"], metadata=dict(json.loads(row["metadata_json"])),
            created_seq=int(row["created_seq"]),
        )

    def get_self_version_revision(
        self, domain_id: str, *, revision: int | None = None, at_seq: int | None = None,
    ) -> SelfVersionProfileRevision:
        if revision is not None and at_seq is not None:
            raise ValueError("choose revision or at_seq, not both")
        if revision is not None:
            row = self.db.execute(
                "SELECT * FROM self_version_revisions WHERE domain_id=? AND revision=?", (domain_id, revision)
            ).fetchone()
        elif at_seq is not None:
            row = self.db.execute(
                "SELECT * FROM self_version_revisions WHERE domain_id=? AND created_seq<=? ORDER BY revision DESC LIMIT 1",
                (domain_id, at_seq),
            ).fetchone()
        else:
            row = self.db.execute(
                "SELECT * FROM self_version_revisions WHERE domain_id=? ORDER BY revision DESC LIMIT 1", (domain_id,)
            ).fetchone()
        if row is None:
            raise KeyError((domain_id, revision, at_seq))
        return self._self_version_revision_from_row(row)

    def list_self_version_revisions(self, domain_id: str) -> list[SelfVersionProfileRevision]:
        return [self._self_version_revision_from_row(row) for row in self.db.execute(
            "SELECT * FROM self_version_revisions WHERE domain_id=? ORDER BY revision", (domain_id,)
        ).fetchall()]

    def _self_version_at_seq(self, domain_id: str, seq: int | None = None) -> str | None:
        try:
            return self.get_self_version_revision(domain_id, at_seq=seq).profile_id if seq is not None else self.get_self_version_revision(domain_id).profile_id
        except KeyError:
            return None

    def set_self_version(self, domain_id: str, profile_id: str, metadata: dict[str, Any]) -> str:
        existing = self.db.execute("SELECT * FROM self_versions WHERE domain_id=?", (domain_id,)).fetchone()
        if existing and existing["profile_id"] == profile_id and json.loads(existing["metadata_json"]) == metadata:
            return profile_id
        revision = 1 if not existing else int(existing["revision"]) + 1
        request = {"profile_id": profile_id, "metadata": metadata, "revision": revision}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO self_version_revisions(domain_id,revision,predecessor_revision,profile_id,metadata_json,created_seq) VALUES(?,?,?,?,?,?)",
                (domain_id, revision, None if revision == 1 else revision - 1, profile_id, canonical_json(metadata), seq),
            )
            cur.execute(
                "INSERT INTO self_versions(domain_id,profile_id,metadata_json,revision,updated_seq) VALUES(?,?,?,?,?) "
                "ON CONFLICT(domain_id) DO UPDATE SET profile_id=excluded.profile_id,metadata_json=excluded.metadata_json,revision=excluded.revision,updated_seq=excluded.updated_seq",
                (domain_id, profile_id, canonical_json(metadata), revision, seq),
            )
            self._bump_generation(cur, domain_id, "self_version", "global")
            self._bump_generation(cur, domain_id, "effect_profile", "global")
            return profile_id
        self._auto_commit(domain_id, "SET_SELF_VERSION", profile_id, request, mutate)
        return profile_id

