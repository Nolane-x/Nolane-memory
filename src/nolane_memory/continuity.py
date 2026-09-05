from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import timezone
from typing import Any, Iterable

from .errors import MemoryRecallInsufficient, MemoryRecoveryBlocked, MemoryScopeBlocked, MemoryTransitionIncomplete
from .normalize import canonical_json, digest
from .types import (
    ContinuityPin,
    HandoffPacket,
    LossState,
    MemoryErasureClosureReceipt,
    RecallCut,
    RecallRole,
    RecoveryLayerStatus,
    RecoveryResumeAssessment,
    RegimeRevision,
    ReplayForensicAssessment,
)


class ContinuityMixin:
    def _init_continuity_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS continuity_pins(
              pin_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, cut_json TEXT NOT NULL,
              state_digest TEXT NOT NULL, mission_revision TEXT, self_version TEXT,
              environment_revision TEXT, hard_roles_json TEXT NOT NULL,
              verification_blockers_json TEXT NOT NULL, stable_refs_json TEXT NOT NULL,
              payload_digest TEXT NOT NULL, created_seq INTEGER NOT NULL, invalidated_seq INTEGER
            );
            CREATE TABLE IF NOT EXISTS recovery_assessments(
              assessment_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, pin_id TEXT,
              assessment_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS replay_forensic_assessments(
              assessment_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, cut_json TEXT NOT NULL,
              assessment_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS erasure_closure_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, retention_event_id TEXT NOT NULL,
              target_kind TEXT NOT NULL, target_id TEXT NOT NULL, receipt_json TEXT NOT NULL,
              created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runtime_compatibility(
              domain_id TEXT PRIMARY KEY, mission_revision TEXT, environment_revision TEXT,
              schema_revision TEXT NOT NULL DEFAULT 'v0.6.3', updated_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS regime_revisions(
              domain_id TEXT NOT NULL, revision INTEGER NOT NULL, predecessor_revision INTEGER,
              mission_revision TEXT, environment_revision TEXT, schema_revision TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,revision)
            );
            CREATE TABLE IF NOT EXISTS handoff_packets(
              packet_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, principal TEXT NOT NULL,
              packet_json TEXT NOT NULL, created_at TEXT NOT NULL, invalidated_seq INTEGER
            );
            """
        )
        self.db.execute(
            "INSERT OR IGNORE INTO regime_revisions(domain_id,revision,predecessor_revision,mission_revision,environment_revision,schema_revision,created_seq) "
            "SELECT domain_id,1,NULL,mission_revision,environment_revision,schema_revision,updated_seq FROM runtime_compatibility"
        )

    @staticmethod
    def _utc_text(dt) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _regime_revision_from_row(row) -> RegimeRevision:
        return RegimeRevision(
            domain_id=row["domain_id"], revision=int(row["revision"]),
            predecessor_revision=None if row["predecessor_revision"] is None else int(row["predecessor_revision"]),
            mission_revision=row["mission_revision"], environment_revision=row["environment_revision"],
            schema_revision=row["schema_revision"], created_seq=int(row["created_seq"]),
        )

    def get_regime_revision(
        self, domain_id: str, *, revision: int | None = None, at_seq: int | None = None,
    ) -> RegimeRevision:
        if revision is not None and at_seq is not None:
            raise ValueError("choose revision or at_seq, not both")
        if revision is not None:
            row = self.db.execute("SELECT * FROM regime_revisions WHERE domain_id=? AND revision=?", (domain_id, revision)).fetchone()
        elif at_seq is not None:
            row = self.db.execute(
                "SELECT * FROM regime_revisions WHERE domain_id=? AND created_seq<=? ORDER BY revision DESC LIMIT 1",
                (domain_id, at_seq),
            ).fetchone()
        else:
            row = self.db.execute("SELECT * FROM regime_revisions WHERE domain_id=? ORDER BY revision DESC LIMIT 1", (domain_id,)).fetchone()
        if row is None:
            raise KeyError((domain_id, revision, at_seq))
        return self._regime_revision_from_row(row)

    def list_regime_revisions(self, domain_id: str) -> list[RegimeRevision]:
        return [self._regime_revision_from_row(row) for row in self.db.execute(
            "SELECT * FROM regime_revisions WHERE domain_id=? ORDER BY revision", (domain_id,)
        ).fetchall()]

    def set_runtime_compatibility(
        self, domain_id: str, *, mission_revision: str | None, environment_revision: str | None,
        schema_revision: str = "v0.6.3",
    ) -> str:
        existing = self.db.execute("SELECT * FROM runtime_compatibility WHERE domain_id=?", (domain_id,)).fetchone()
        if existing and existing["mission_revision"] == mission_revision and existing["environment_revision"] == environment_revision and existing["schema_revision"] == schema_revision:
            return schema_revision
        current = self.db.execute("SELECT MAX(revision) FROM regime_revisions WHERE domain_id=?", (domain_id,)).fetchone()[0]
        revision = 1 if current is None else int(current) + 1
        request = {"mission_revision": mission_revision, "environment_revision": environment_revision, "schema_revision": schema_revision, "revision": revision}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO regime_revisions(domain_id,revision,predecessor_revision,mission_revision,environment_revision,schema_revision,created_seq) VALUES(?,?,?,?,?,?,?)",
                (domain_id, revision, None if revision == 1 else revision - 1, mission_revision, environment_revision, schema_revision, seq),
            )
            cur.execute(
                "INSERT INTO runtime_compatibility(domain_id,mission_revision,environment_revision,schema_revision,updated_seq) VALUES(?,?,?,?,?) "
                "ON CONFLICT(domain_id) DO UPDATE SET mission_revision=excluded.mission_revision,environment_revision=excluded.environment_revision,schema_revision=excluded.schema_revision,updated_seq=excluded.updated_seq",
                (domain_id, mission_revision, environment_revision, schema_revision, seq),
            )
            self._bump_generation(cur, domain_id, "regime", "global")
            return f"compat:{domain_id}:r{revision}"
        self._auto_commit(domain_id, "SET_RUNTIME_COMPATIBILITY", f"compat:{domain_id}:r{revision}", request, mutate)
        return schema_revision

    def _compatibility_at_seq(self, domain_id: str, seq: int | None = None) -> tuple[str | None, str | None, str]:
        try:
            row = self.get_regime_revision(domain_id, at_seq=seq) if seq is not None else self.get_regime_revision(domain_id)
            return row.mission_revision, row.environment_revision, row.schema_revision
        except KeyError:
            return None, None, "v0.6.3"

    def _current_compatibility(self, domain_id: str) -> tuple[str | None, str | None, str]:
        return self._compatibility_at_seq(domain_id, None)

    def _current_self_version(self, domain_id: str) -> str | None:
        if hasattr(self, "_self_version_at_seq"):
            return self._self_version_at_seq(domain_id)
        row = self.db.execute("SELECT profile_id FROM self_versions WHERE domain_id=?", (domain_id,)).fetchone()
        return row[0] if row else None

    def _ref_exists_and_allowed(self, domain_id: str, ref: str, principal: str, *, at_cut: int | None = None) -> bool:
        e = self.db.execute("SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, ref)).fetchone()
        if e:
            if not self._is_allowed(principal, e["allowed_principals_json"]): return False
            if at_cut is not None and int(e["created_seq"]) > at_cut: return False
            return True
        r = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, ref)).fetchone()
        if r:
            if not self._is_allowed(principal, r["allowed_principals_json"]): return False
            if at_cut is not None and int(r["created_seq"]) > at_cut: return False
            return True
        return False

    def _pin_state_material(self, cut: RecallCut, mission: str | None, self_version: str | None,
                            environment: str | None, roles: list[dict[str, Any]], blockers: list[str], refs: list[str]) -> dict[str, Any]:
        return {
            "cut": asdict(cut), "mission_revision": mission, "self_version": self_version,
            "environment_revision": environment, "hard_roles": roles,
            "verification_blockers": blockers, "stable_refs": refs,
        }

    def create_continuity_pin(
        self, domain_id: str, *, principal: str, hard_roles: Iterable[RecallRole], stable_refs: Iterable[str],
        verification_blockers: Iterable[str] | None = None,
    ) -> ContinuityPin:
        cut = self.head(domain_id)
        roles = sorted(list(hard_roles), key=lambda r: (r.role_id, r.region_id, r.query_family, r.hard))
        refs = sorted(set(stable_refs))
        blockers = sorted(set(verification_blockers or []))
        for ref in refs:
            if not self._ref_exists_and_allowed(domain_id, ref, principal, at_cut=cut.sequence):
                raise MemoryTransitionIncomplete(f"dangling or inaccessible continuity reference {ref}")
        mission, environment, _ = self._current_compatibility(domain_id)
        self_version = self._current_self_version(domain_id)
        role_objs = [asdict(r) for r in roles]
        state_material = self._pin_state_material(cut, mission, self_version, environment, role_objs, blockers, refs)
        state_digest = digest(state_material)
        payload_digest = digest({**state_material, "state_digest": state_digest})
        pin_id = f"pin_{uuid.uuid4().hex}"
        request = {"pin_id": pin_id, "cut": asdict(cut), "state_digest": state_digest, "payload_digest": payload_digest}
        def mutate(cur, seq):
            cur.execute(
                "INSERT INTO continuity_pins(pin_id,domain_id,cut_json,state_digest,mission_revision,self_version,environment_revision,hard_roles_json,verification_blockers_json,stable_refs_json,payload_digest,created_seq,invalidated_seq) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,NULL)",
                (pin_id, domain_id, canonical_json(asdict(cut)), state_digest, mission, self_version, environment,
                 canonical_json(role_objs), canonical_json(blockers), canonical_json(refs), payload_digest, seq),
            )
            self._bump_generation(cur, domain_id, "continuity", "global")
            return pin_id
        receipt = self._auto_commit(domain_id, "CREATE_CONTINUITY_PIN", pin_id, request, mutate)
        return ContinuityPin(pin_id, domain_id, cut, state_digest, mission, self_version, environment, roles, blockers, refs, receipt.commit_seq)

    def _cut_root_valid(self, cut: RecallCut) -> bool:
        if cut.sequence == 0:
            if cut.root != "0" * 64:
                return False
            return not hasattr(self, "_incarnation_at_sequence") or self._incarnation_at_sequence(cut.domain_id, 0) == cut.incarnation
        row = self.db.execute(
            "SELECT root,incarnation FROM journal WHERE domain_id=? AND sequence=?",
            (cut.domain_id, cut.sequence),
        ).fetchone()
        return bool(row and row["root"] == cut.root and int(row["incarnation"]) == int(cut.incarnation))

    def assess_replay(
        self, domain_id: str, cut: RecallCut, *, principal: str,
        required_refs: Iterable[str] | None = None, connector_receipt_ids: Iterable[str] | None = None,
    ) -> ReplayForensicAssessment:
        if cut.domain_id != domain_id:
            raise MemoryTransitionIncomplete("replay cut belongs to another authority domain")
        refs = sorted(set(required_refs or []))
        connectors = sorted(set(connector_receipt_ids or []))
        barriers: list[dict[str, Any]] = []
        unavailable: list[str] = []
        available_modes: list[str] = []
        hermetic = self._cut_root_valid(cut)
        if hermetic:
            available_modes.extend(["EXACT_SEMANTIC_REPLAY", "HISTORICAL_JUDGEMENT_REPLAY"])

        # Current governance barriers do not rewrite the historical cut, but they
        # dominate whether old bytes may become current-usable again.
        barrier_queries = (
            ("RETENTION", "SELECT retention_event_id AS id,created_seq FROM retention_events WHERE domain_id=? AND created_seq>?", (domain_id, cut.sequence)),
            ("SOURCE_COMPROMISE", "SELECT compromise_id AS id,created_seq FROM source_compromises WHERE domain_id=? AND created_seq>?", (domain_id, cut.sequence)),
            ("ORIGIN_REVOKE", "SELECT binding_id AS id,revoked_seq AS created_seq FROM origin_bindings WHERE domain_id=? AND revoked_seq>?", (domain_id, cut.sequence)),
            ("DECLASSIFICATION_REVOKE", "SELECT receipt_id AS id,revoked_seq AS created_seq FROM declassification_receipts WHERE domain_id=? AND revoked_seq>?", (domain_id, cut.sequence)),
            ("ACCESS_POLICY_CHANGE", "SELECT principal AS id,created_seq FROM access_profile_revisions WHERE domain_id=? AND created_seq>?", (domain_id, cut.sequence)),
        )
        for kind, sql, params in barrier_queries:
            for row in self.db.execute(sql, params).fetchall():
                barriers.append({"kind": kind, "id": row["id"], "sequence": int(row["created_seq"])})

        for ref in refs:
            e = self.db.execute("SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, ref)).fetchone()
            if e is not None:
                if e["deleted_seq"] is not None or not self._is_allowed(principal, e["allowed_principals_json"]):
                    unavailable.append(ref)
                continue
            r = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, ref)).fetchone()
            if r is not None:
                if r["invalidated_seq"] is not None or r["tainted_seq"] is not None or not self._is_allowed(principal, r["allowed_principals_json"]):
                    unavailable.append(ref)
                continue
            unavailable.append(ref)

        connector_non_hermetic = False
        for receipt_id in connectors:
            row = self.db.execute(
                "SELECT * FROM connector_query_receipts WHERE domain_id=? AND receipt_id=?",
                (domain_id, receipt_id),
            ).fetchone()
            if row is None:
                connector_non_hermetic = True
                barriers.append({"kind": "CONNECTOR_RECEIPT_MISSING", "id": receipt_id, "sequence": cut.sequence})
                continue
            if row["provider_error"] is not None or row["completeness"] != "COMPLETE" or not row["snapshot_id"]:
                connector_non_hermetic = True
                barriers.append({"kind": "NON_HERMETIC_CONNECTOR", "id": receipt_id, "sequence": cut.sequence})

        if not hermetic:
            current_mode = "NON_HERMETIC_REPLAY"
        elif unavailable:
            current_mode = "UNAVAILABLE_BY_POLICY"
        elif connector_non_hermetic:
            current_mode = "NON_HERMETIC_REPLAY"
        elif barriers:
            current_mode = "RESTORE_BARRIER_REQUIRED"
        else:
            current_mode = "CURRENT_REEVALUATION"
            available_modes.append("CURRENT_REEVALUATION")

        now = self._utc_text(self._clock())
        assessment = ReplayForensicAssessment(
            assessment_id=f"replay_{uuid.uuid4().hex}", domain_id=domain_id, cut=cut,
            available_modes=sorted(set(available_modes)), current_use_mode=current_mode,
            barriers=sorted(barriers, key=lambda b: (b["sequence"], b["kind"], b["id"])),
            unavailable_refs=unavailable, connector_receipt_ids=connectors, created_at=now,
        )
        self.db.execute(
            "INSERT INTO replay_forensic_assessments(assessment_id,domain_id,cut_json,assessment_json,created_at) VALUES(?,?,?,?,?)",
            (assessment.assessment_id, domain_id, canonical_json(asdict(cut)), canonical_json(asdict(assessment)), now),
        )
        return assessment

    def _continuity_pin_from_row(self, row) -> ContinuityPin:
        return ContinuityPin(
            row["pin_id"], row["domain_id"], RecallCut(**json.loads(row["cut_json"])), row["state_digest"],
            row["mission_revision"], row["self_version"], row["environment_revision"],
            [RecallRole(**x) for x in json.loads(row["hard_roles_json"])],
            list(json.loads(row["verification_blockers_json"])), list(json.loads(row["stable_refs_json"])),
            int(row["created_seq"]),
        )

    def select_continuity_pin(
        self, domain_id: str, *, principal: str, pin_ids: Iterable[str] | None = None,
        barrier_ledger_complete: bool = True,
    ) -> ContinuityPin:
        ids = None if pin_ids is None else set(pin_ids)
        rows = self.db.execute(
            "SELECT * FROM continuity_pins WHERE domain_id=? ORDER BY created_seq DESC,pin_id ASC", (domain_id,)
        ).fetchall()
        usable = []
        for row in rows:
            if ids is not None and row["pin_id"] not in ids:
                continue
            assessment = self.assess_recovery(
                domain_id, pin_id=row["pin_id"], principal=principal, barrier_ledger_complete=barrier_ledger_complete
            )
            if assessment.resume_allowed:
                cut = RecallCut(**json.loads(row["cut_json"]))
                usable.append((cut.sequence, int(row["created_seq"]), row["pin_id"], row))
        if not usable:
            raise MemoryRecoveryBlocked("no compatible continuity pin is usable under current governance")
        # Serialized order is never freshness. Highest compatible canonical sequence
        # wins; commit sequence and pin id are deterministic tie-breakers.
        usable.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        return self._continuity_pin_from_row(usable[0][3])

    def assess_recovery(
        self, domain_id: str, *, pin_id: str | None, principal: str, barrier_ledger_complete: bool = True,
    ) -> RecoveryResumeAssessment:
        PASS = RecoveryLayerStatus.PASS.value; BLOCK = RecoveryLayerStatus.BLOCKED.value
        NOT = RecoveryLayerStatus.NOT_EVALUATED.value; OPAQUE = RecoveryLayerStatus.OPAQUE.value
        layers = {
            "R0_STORAGE_INTEGRITY": NOT, "R1_CANONICAL_REPLAY": NOT, "R2_SEMANTIC_COMPATIBILITY": NOT,
            "R3_NON_REVIVAL_BARRIER": NOT, "R4_CONTINUITY_COMPATIBILITY": NOT,
            "R5_ENVIRONMENT_COMPATIBILITY": NOT, "R6_RECALL_SUFFICIENCY": NOT,
        }
        try:
            self.verify_integrity(domain_id); layers["R0_STORAGE_INTEGRITY"] = PASS
            cut_now = self.head(domain_id); layers["R1_CANONICAL_REPLAY"] = PASS
        except Exception:
            cut_now = self.head(domain_id); layers["R0_STORAGE_INTEGRITY"] = OPAQUE
        mission, environment, schema = self._current_compatibility(domain_id)
        layers["R2_SEMANTIC_COMPATIBILITY"] = PASS if schema == "v0.6.3" else BLOCK
        pin_row = self.db.execute("SELECT * FROM continuity_pins WHERE domain_id=? AND pin_id=?", (domain_id, pin_id)).fetchone() if pin_id else None
        roles: list[RecallRole] = []
        if pin_id and not pin_row:
            layers["R3_NON_REVIVAL_BARRIER"] = BLOCK
            layers["R4_CONTINUITY_COMPATIBILITY"] = BLOCK
        elif pin_row:
            pin_cut = RecallCut(**json.loads(pin_row["cut_json"]))
            refs = list(json.loads(pin_row["stable_refs_json"])); blockers = list(json.loads(pin_row["verification_blockers_json"]))
            role_objs = list(json.loads(pin_row["hard_roles_json"])); roles = [RecallRole(**x) for x in role_objs]
            # Any explicit invalidation/erasure after the bound cut is a non-revival barrier.
            layers["R3_NON_REVIVAL_BARRIER"] = BLOCK if pin_row["invalidated_seq"] is not None else PASS
            material = self._pin_state_material(pin_cut, pin_row["mission_revision"], pin_row["self_version"],
                                                pin_row["environment_revision"], role_objs, blockers, refs)
            state_ok = digest(material) == pin_row["state_digest"]
            payload_ok = digest({**material, "state_digest": pin_row["state_digest"]}) == pin_row["payload_digest"]
            refs_ok = all(self._ref_exists_and_allowed(domain_id, ref, principal, at_cut=pin_cut.sequence) for ref in refs)
            cut_ok = self._cut_root_valid(pin_cut)
            mission_ok = pin_row["mission_revision"] == mission
            self_ok = pin_row["self_version"] == self._current_self_version(domain_id)
            layers["R4_CONTINUITY_COMPATIBILITY"] = PASS if state_ok and payload_ok and refs_ok and cut_ok and not blockers and mission_ok and self_ok else BLOCK
            layers["R5_ENVIRONMENT_COMPATIBILITY"] = PASS if pin_row["environment_revision"] == environment else BLOCK
        else:
            layers["R3_NON_REVIVAL_BARRIER"] = PASS
            layers["R4_CONTINUITY_COMPATIBILITY"] = PASS
            layers["R5_ENVIRONMENT_COMPATIBILITY"] = PASS
        if layers["R5_ENVIRONMENT_COMPATIBILITY"] == NOT:
            layers["R5_ENVIRONMENT_COMPATIBILITY"] = BLOCK
        if not barrier_ledger_complete:
            layers["R3_NON_REVIVAL_BARRIER"] = BLOCK
        prerequisite = all(layers[k] == PASS for k in list(layers)[:-1])
        if prerequisite:
            try:
                if roles:
                    self.compile_recall(domain_id, principal, roles, token_budget=100_000)
                layers["R6_RECALL_SUFFICIENCY"] = PASS
            except Exception:
                layers["R6_RECALL_SUFFICIENCY"] = BLOCK
        first = next((k for k, v in layers.items() if v != PASS), None)
        allowed = first is None
        now = self._utc_text(self._clock())
        assessment = RecoveryResumeAssessment(f"recovery_{uuid.uuid4().hex}", domain_id, pin_id, layers, allowed, first, cut_now, now)
        self.db.execute(
            "INSERT INTO recovery_assessments(assessment_id,domain_id,pin_id,assessment_json,created_at) VALUES(?,?,?,?,?)",
            (assessment.assessment_id, domain_id, pin_id, canonical_json(asdict(assessment)), now),
        )
        return assessment

    def _representations_depending_on_evidence(self, domain_id: str, evidence_id: str) -> set[str]:
        direct = set()
        for row in self.db.execute("SELECT representation_id,source_evidence_ids_json FROM representations WHERE domain_id=?", (domain_id,)).fetchall():
            if evidence_id in set(json.loads(row["source_evidence_ids_json"])):
                direct.add(row["representation_id"])
        return direct | self._representation_descendants(domain_id, direct)

    def erase_evidence(self, domain_id: str, evidence_id: str, *, principal: str, policy_ref: str) -> MemoryErasureClosureReceipt:
        if hasattr(self, "_require_capability"):
            self._require_capability(domain_id, principal, "CHANGE_RETENTION")
        row = self.db.execute("SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, evidence_id)).fetchone()
        if not row: raise KeyError(evidence_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]): raise MemoryScopeBlocked("cannot erase inaccessible evidence")
        if row["deleted_seq"] is not None:
            old = self.db.execute("SELECT receipt_json FROM erasure_closure_receipts WHERE domain_id=? AND target_kind='evidence' AND target_id=? ORDER BY created_seq DESC LIMIT 1", (domain_id, evidence_id)).fetchone()
            if old: return MemoryErasureClosureReceipt(**json.loads(old[0]))
        tainted = sorted(self._representations_depending_on_evidence(domain_id, evidence_id))
        pin_ids = []
        for pin in self.db.execute("SELECT * FROM continuity_pins WHERE domain_id=? AND invalidated_seq IS NULL", (domain_id,)).fetchall():
            refs = set(json.loads(pin["stable_refs_json"]))
            if evidence_id in refs or refs.intersection(tainted): pin_ids.append(pin["pin_id"])
        handoff_ids = []
        tainted_set = set(tainted)
        for packet in self.db.execute("SELECT * FROM handoff_packets WHERE domain_id=? AND invalidated_seq IS NULL", (domain_id,)).fetchall():
            payload = json.loads(packet["packet_json"])
            fragment_reps = {f.get("representation_id") for f in payload.get("fragments", [])}
            if fragment_reps.intersection(tainted_set):
                handoff_ids.append(packet["packet_id"])
        retention_event_id = f"ret_{uuid.uuid4().hex}"; receipt_id = f"erase_{uuid.uuid4().hex}"
        request = {"target_kind": "evidence", "target_id": evidence_id, "mode": "HARD_DELETE_BY_POLICY", "policy_ref": policy_ref}
        receipt_box = {}
        def mutate(cur, seq):
            cur.execute("UPDATE evidence SET content_json=?,deleted_seq=?,erasure_policy_ref=? WHERE evidence_id=?", (canonical_json({"__erased__": True}), seq, policy_ref, evidence_id))
            cur.execute("DELETE FROM origin_roots WHERE domain_id=? AND object_kind='evidence' AND object_id=?", (domain_id, evidence_id))
            cur.execute("INSERT INTO retention_events(retention_event_id,domain_id,target_kind,target_id,mode,policy_ref,authority_principal,created_seq) VALUES(?,?,?,?,?,?,?,?)", (retention_event_id, domain_id, "evidence", evidence_id, "HARD_DELETE_BY_POLICY", policy_ref, principal, seq))
            for rep_id in tainted:
                rep = cur.execute("SELECT region_id,tainted_seq FROM representations WHERE representation_id=?", (rep_id,)).fetchone()
                if rep and rep["tainted_seq"] is None:
                    cur.execute("UPDATE representations SET tainted_seq=? WHERE representation_id=?", (seq, rep_id))
                    self._bump_generation(cur, domain_id, "representation", rep_id); self._bump_generation(cur, domain_id, "region", rep["region_id"])
            # Candidate derivatives can carry the same private residue as admitted
            # representations. Erasure closure therefore scrubs and invalidates any
            # pending proposal whose source lineage intersects the tainted cone.
            tainted_set = set(tainted)
            for proposal in cur.execute(
                "SELECT proposal_id,source_representation_ids_json FROM representation_proposals "
                "WHERE domain_id=? AND invalidated_seq IS NULL AND promoted_representation_id IS NULL",
                (domain_id,),
            ).fetchall():
                if tainted_set.intersection(json.loads(proposal["source_representation_ids_json"])):
                    cur.execute(
                        "UPDATE representation_proposals SET payload_json=?,invalidated_seq=? WHERE proposal_id=?",
                        (canonical_json({"__erased__": True}), seq, proposal["proposal_id"]),
                    )
            for pid in pin_ids:
                cur.execute("UPDATE continuity_pins SET invalidated_seq=? WHERE pin_id=? AND invalidated_seq IS NULL", (seq, pid))
            for packet_id in handoff_ids:
                cur.execute("UPDATE handoff_packets SET invalidated_seq=? WHERE packet_id=? AND invalidated_seq IS NULL", (seq, packet_id))
            self._bump_generation(cur, domain_id, "source", evidence_id); self._bump_generation(cur, domain_id, "query_domain", "global")
            self._bump_generation(cur, domain_id, "continuity", "global"); self._bump_generation(cur, domain_id, "erasure", "global")
            surfaces = {
                "canonical_source_availability": "CLOSED", "dependent_representation_closure": "CLOSED",
                "continuity_pin_handoff_closure": "CLOSED", "read_indexes_and_caches": "CLOSED_BY_CANONICAL_FILTER",
                "snapshot_restore_barrier": "CLOSED", "external_publications": "LOCAL_SCOPE_ONLY",
            }
            rec = MemoryErasureClosureReceipt(receipt_id, domain_id, retention_event_id, "evidence", evidence_id,
                surfaces, tainted, sorted(pin_ids), [f"representation:{x}" for x in tainted], "CURRENT_ERASURE_CLOSED", seq,
                sorted(handoff_ids))
            cur.execute("INSERT INTO erasure_closure_receipts(receipt_id,domain_id,retention_event_id,target_kind,target_id,receipt_json,created_seq) VALUES(?,?,?,?,?,?,?)", (receipt_id, domain_id, retention_event_id, "evidence", evidence_id, canonical_json(asdict(rec)), seq))
            receipt_box["receipt"] = rec
            return retention_event_id
        self._auto_commit(domain_id, "ERASE_EVIDENCE", retention_event_id, request, mutate)
        return receipt_box["receipt"]

    def clean_rederive(
        self, domain_id: str, tainted_representation_id: str, *, surviving_evidence_ids: list[str],
        payload: Any, loss: dict[str, LossState | str], principal: str,
    ) -> str:
        old = self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?", (domain_id, tainted_representation_id)).fetchone()
        if not old: raise KeyError(tainted_representation_id)
        if old["tainted_seq"] is None: raise MemoryTransitionIncomplete("clean rederivation requires a tainted predecessor")
        for eid in surviving_evidence_ids:
            e = self.db.execute("SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, eid)).fetchone()
            if not e or e["deleted_seq"] is not None or e["revoked_seq"] is not None:
                raise MemoryTransitionIncomplete(f"surviving source {eid} is unavailable")
        return self.add_representation(
            domain_id, old["region_id"], kind=f"clean:{old['kind']}", payload=payload, loss=loss,
            recoverable=set(), token_cost=int(old["token_cost"]), principal=principal,
            source_representation_ids=[], source_evidence_ids=list(surviving_evidence_ids),
            transform_kind="SOURCE_REBASE", transform_profile=f"clean-rederive:{old['transform_profile']}",
            allowed_principals=json.loads(old["allowed_principals_json"]),
        )

    def create_handoff_packet(
        self, domain_id: str, *, principal: str, hard_roles: list[RecallRole], token_budget: int,
        blockers: Iterable[str] | None = None, advisory_next_action: Any | None = None,
        tool_boundary_digest: str | None = None,
    ) -> HandoffPacket:
        frame = self.compile_recall(domain_id, principal, hard_roles, token_budget)
        mission, _, _ = self._current_compatibility(domain_id)
        self_version = self._current_self_version(domain_id)
        now = self._utc_text(self._clock())
        packet = HandoffPacket(
            f"handoff_{uuid.uuid4().hex}", domain_id, principal, frame.cut, list(frame.fragments),
            sorted(set(blockers or [])), mission, self_version, now, advisory_next_action, tool_boundary_digest,
        )
        self.db.execute("INSERT INTO handoff_packets(packet_id,domain_id,principal,packet_json,created_at,invalidated_seq) VALUES(?,?,?,?,?,NULL)",
                        (packet.packet_id, domain_id, principal, canonical_json(asdict(packet)), now))
        return packet

    def validate_handoff_packet(
        self, packet_id: str, *, principal: str, current_tool_boundary_digest: str | None = None,
    ) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM handoff_packets WHERE packet_id=?", (packet_id,)).fetchone()
        if row is None:
            raise KeyError(packet_id)
        if row["principal"] != principal:
            raise MemoryScopeBlocked("handoff principal mismatch")
        payload = json.loads(row["packet_json"])
        cut = RecallCut(**payload["cut"])
        blocked_by_governance = row["invalidated_seq"] is not None
        refs_live = True
        for fragment in payload.get("fragments", []):
            rep = self.db.execute(
                "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
                (row["domain_id"], fragment["representation_id"]),
            ).fetchone()
            if (not rep or rep["invalidated_seq"] is not None or rep["tainted_seq"] is not None
                    or not self._is_allowed(principal, rep["allowed_principals_json"])):
                refs_live = False
                break
        hard_roles_usable = (not blocked_by_governance and refs_live and self._cut_root_valid(cut))
        mission, _, _ = self._current_compatibility(row["domain_id"])
        self_version = self._current_self_version(row["domain_id"])
        compatibility_ok = payload.get("mission_revision") == mission and payload.get("self_version") == self_version
        blockers = list(payload.get("blockers", []))
        action = payload.get("advisory_next_action")
        bound_tool = payload.get("tool_boundary_digest")
        tool_ok = action is None or bound_tool is None or current_tool_boundary_digest == bound_tool
        advisory_action_usable = bool(action is not None and hard_roles_usable and compatibility_ok and not blockers and tool_ok)
        if blocked_by_governance or not refs_live:
            status = "BLOCKED_BY_GOVERNANCE"
        elif not hard_roles_usable:
            status = "BLOCKED"
        elif not compatibility_ok or blockers or not tool_ok:
            status = "REVALIDATION_REQUIRED"
        else:
            status = "USABLE"
        return {
            "packet_id": packet_id, "status": status, "hard_roles_usable": hard_roles_usable,
            "advisory_action_usable": advisory_action_usable, "blockers": blockers,
            "mission_compatible": compatibility_ok, "tool_boundary_compatible": tool_ok,
            "cut_valid": self._cut_root_valid(cut),
        }
