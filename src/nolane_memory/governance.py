from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from typing import Any, Iterable

from .errors import MemoryIdentityCollision, MemoryScopeBlocked, MemoryTransitionIncomplete
from .normalize import canonical_json, digest
from .types import (Dependency, EvidenceIndependenceReceipt, HistoricalJudgement, OriginBindingReceipt, RecallCut, RecoverabilityCertificate, SupportBundleReceipt)


class GovernanceMixin:
    """Canonical/audit ownership surfaces that should not be hidden in projections."""

    def _init_governance_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS historical_judgements(
              judgement_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              claim_revision_id TEXT NOT NULL,
              principal TEXT NOT NULL,
              judgement TEXT NOT NULL,
              reason TEXT NOT NULL,
              cut_json TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transformation_contracts(
              profile_id TEXT NOT NULL,
              revision INTEGER NOT NULL,
              transform_kind TEXT NOT NULL,
              protected_dimensions_json TEXT NOT NULL,
              forbidden_loss_json TEXT NOT NULL,
              contract_digest TEXT NOT NULL,
              PRIMARY KEY(profile_id, revision)
            );
            CREATE TABLE IF NOT EXISTS source_compromises(
              compromise_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              evidence_id TEXT NOT NULL,
              reason TEXT NOT NULL,
              principal TEXT NOT NULL,
              created_seq INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS origin_bindings(
              binding_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              evidence_id TEXT NOT NULL,
              origin_identity TEXT NOT NULL,
              transport_channel TEXT NOT NULL,
              external_identity TEXT,
              authority_class TEXT NOT NULL,
              common_mode_group TEXT,
              raw_evidence_digest TEXT NOT NULL,
              scope_ceiling_json TEXT NOT NULL,
              binder_procedure TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              revoked_seq INTEGER,
              revocation_reason TEXT,
              UNIQUE(domain_id,evidence_id,origin_identity)
            );
            CREATE INDEX IF NOT EXISTS origin_binding_evidence_idx
              ON origin_bindings(domain_id,evidence_id,created_seq);
            CREATE TABLE IF NOT EXISTS evidence_independence_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, payload_json TEXT NOT NULL,
              dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS support_bundle_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, logical_id TEXT NOT NULL,
              payload_json TEXT NOT NULL, dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recoverability_certificates(
              certificate_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, representation_id TEXT NOT NULL,
              query_family TEXT NOT NULL, payload_json TEXT NOT NULL, dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS integrity_authority_profiles(
              domain_id TEXT NOT NULL, profile_id TEXT NOT NULL, revision INTEGER NOT NULL, issuer TEXT NOT NULL,
              subject_ids_json TEXT NOT NULL, operations_json TEXT NOT NULL, accepted_authority_classes_json TEXT NOT NULL,
              enabled INTEGER NOT NULL, created_seq INTEGER NOT NULL, expires_at TEXT,
              PRIMARY KEY(domain_id,profile_id,revision)
            );
            CREATE TABLE IF NOT EXISTS publication_policies(
              source_domain TEXT NOT NULL, destination_domain TEXT NOT NULL, policy_id TEXT NOT NULL,
              revision INTEGER NOT NULL, issuer TEXT NOT NULL, allow_transfer INTEGER NOT NULL,
              allowed_principals_json TEXT NOT NULL, preserve_origin INTEGER NOT NULL, created_seq INTEGER NOT NULL, expires_at TEXT,
              PRIMARY KEY(source_domain,destination_domain,policy_id,revision)
            );
            """
        )
        for table, column, ddl in (
            ("integrity_authority_profiles", "expires_at", "expires_at TEXT"),
            ("publication_policies", "expires_at", "expires_at TEXT"),
        ):
            cols = {row[1] for row in self.db.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                self.db.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

    def get_origin_bindings(self, domain_id: str, evidence_id: str) -> list[OriginBindingReceipt]:
        rows = self.db.execute(
            "SELECT * FROM origin_bindings WHERE domain_id=? AND evidence_id=? ORDER BY origin_identity,binding_id",
            (domain_id, evidence_id),
        ).fetchall()
        return [
            OriginBindingReceipt(
                binding_id=row["binding_id"], domain_id=row["domain_id"], evidence_id=row["evidence_id"],
                origin_identity=row["origin_identity"], transport_channel=row["transport_channel"],
                external_identity=row["external_identity"], authority_class=row["authority_class"],
                common_mode_group=row["common_mode_group"], raw_evidence_digest=row["raw_evidence_digest"],
                scope_ceiling=list(json.loads(row["scope_ceiling_json"])), binder_procedure=row["binder_procedure"],
                created_seq=int(row["created_seq"]), revoked_seq=None if row["revoked_seq"] is None else int(row["revoked_seq"]),
                revocation_reason=row["revocation_reason"],
            )
            for row in rows
        ]

    def revoke_origin_binding(
        self, domain_id: str, binding_id: str, *, principal: str, reason: str,
    ) -> str:
        row = self.db.execute(
            "SELECT b.*,e.allowed_principals_json FROM origin_bindings b "
            "JOIN evidence e ON e.evidence_id=b.evidence_id WHERE b.domain_id=? AND b.binding_id=?",
            (domain_id, binding_id),
        ).fetchone()
        if not row:
            raise KeyError(binding_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("origin binding is not visible to principal")
        request = {"binding_id": binding_id, "principal": principal, "reason": reason}

        def mutate(cur, seq):
            current = cur.execute(
                "SELECT revoked_seq,revocation_reason,evidence_id FROM origin_bindings WHERE binding_id=?",
                (binding_id,),
            ).fetchone()
            if current["revoked_seq"] is None:
                cur.execute(
                    "UPDATE origin_bindings SET revoked_seq=?,revocation_reason=? WHERE binding_id=?",
                    (seq, reason, binding_id),
                )
                self._bump_generation(cur, domain_id, "origin", current["evidence_id"])
                self._bump_generation(cur, domain_id, "origin", "global")
            elif current["revocation_reason"] != reason:
                raise MemoryIdentityCollision("origin binding revocation is immutable")
            return binding_id

        self._auto_commit(domain_id, "REVOKE_ORIGIN_BINDING", binding_id, request, mutate)
        return binding_id

    def record_historical_judgement(
        self, domain_id: str, *, claim_revision_id: str, principal: str,
        judgement: str, reason: str,
    ) -> HistoricalJudgement:
        claim = self.db.execute(
            "SELECT * FROM claims WHERE domain_id=? AND claim_revision_id=?",
            (domain_id, claim_revision_id),
        ).fetchone()
        if not claim:
            raise KeyError(claim_revision_id)
        if not self._is_allowed(principal, claim["allowed_principals_json"]):
            raise MemoryScopeBlocked("claim is not visible to judgement principal")
        basis_cut = self.head(domain_id)
        judgement_id = f"judgement_{uuid.uuid4().hex}"
        now = self._clock()
        created_at = self._utc_text(now) if hasattr(self, "_utc_text") else now.isoformat()
        request = {
            "claim_revision_id": claim_revision_id,
            "principal": principal,
            "judgement": judgement,
            "reason": reason,
            "basis_cut": asdict(basis_cut),
        }
        box: dict[str, HistoricalJudgement] = {}
        def mutate(cur, seq):
            obj = HistoricalJudgement(
                judgement_id, domain_id, claim_revision_id, principal, judgement,
                reason, basis_cut, seq, created_at,
            )
            cur.execute(
                "INSERT INTO historical_judgements(judgement_id,domain_id,claim_revision_id,principal,judgement,reason,cut_json,created_seq,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (judgement_id, domain_id, claim_revision_id, principal, judgement, reason,
                 canonical_json(asdict(basis_cut)), seq, created_at),
            )
            box["value"] = obj
            return judgement_id
        self._auto_commit(domain_id, "RECORD_HISTORICAL_JUDGEMENT", judgement_id, request, mutate)
        return box["value"]

    def list_historical_judgements(self, domain_id: str, *, principal: str) -> list[HistoricalJudgement]:
        out: list[HistoricalJudgement] = []
        rows = self.db.execute(
            "SELECT h.*,c.allowed_principals_json FROM historical_judgements h "
            "JOIN claims c ON c.claim_revision_id=h.claim_revision_id WHERE h.domain_id=? ORDER BY h.created_seq",
            (domain_id,),
        ).fetchall()
        for row in rows:
            if not self._is_allowed(principal, row["allowed_principals_json"]):
                continue
            out.append(HistoricalJudgement(
                row["judgement_id"], row["domain_id"], row["claim_revision_id"],
                row["principal"], row["judgement"], row["reason"],
                RecallCut(**json.loads(row["cut_json"])), int(row["created_seq"]), row["created_at"],
            ))
        return out

    def judgement_as_of(
        self, domain_id: str, logical_id: str, at, *, principal: str,
    ) -> HistoricalJudgement | None:
        at_text = self._utc_text(at) if hasattr(self, "_utc_text") else at.astimezone().isoformat()
        row = self.db.execute(
            "SELECT h.*,c.allowed_principals_json FROM historical_judgements h "
            "JOIN claims c ON c.claim_revision_id=h.claim_revision_id "
            "WHERE h.domain_id=? AND c.logical_id=? AND h.created_at<=? "
            "ORDER BY h.created_at DESC,h.created_seq DESC LIMIT 1",
            (domain_id, logical_id, at_text),
        ).fetchone()
        if row is None:
            return None
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("historical judgement is not visible to principal")
        return HistoricalJudgement(
            row["judgement_id"], row["domain_id"], row["claim_revision_id"],
            row["principal"], row["judgement"], row["reason"],
            RecallCut(**json.loads(row["cut_json"])), int(row["created_seq"]), row["created_at"],
        )

    def evaluate_evidence_independence(self, domain_id: str, evidence_ids: Iterable[str]) -> dict[str, Any]:
        ids = sorted(set(evidence_ids))
        roots_by_id: dict[str, set[str]] = {}
        modes_by_id: dict[str, set[str]] = {}
        binding_unknown = False
        for eid in ids:
            row = self.db.execute(
                "SELECT 1 FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, eid)
            ).fetchone()
            if not row:
                raise KeyError(eid)
            roots_by_id[eid] = set(self.get_origin_roots(domain_id, "evidence", eid))
            bindings = self.get_origin_bindings(domain_id, eid)
            if not bindings or any(b.revoked_seq is not None or not b.common_mode_group for b in bindings):
                binding_unknown = True
            modes_by_id[eid] = {b.common_mode_group for b in bindings if b.revoked_seq is None and b.common_mode_group}
        all_modes = sorted(set().union(*modes_by_id.values()) if modes_by_id else set())
        if any(not roots_by_id[eid] for eid in ids) or binding_unknown:
            dependence = "UNKNOWN_DEPENDENCE"
        else:
            # Connected components over shared roots OR common-mode failure groups.
            # Distinct mirrors/providers that share one upstream failure mode are not
            # independent evidence merely because their origin labels differ.
            remaining = set(ids)
            components = 0
            while remaining:
                seed = remaining.pop(); component = {seed}; frontier = [seed]
                while frontier:
                    cur = frontier.pop()
                    overlaps = {
                        x for x in remaining
                        if (roots_by_id[x] & roots_by_id[cur]) or (modes_by_id[x] & modes_by_id[cur])
                    }
                    remaining -= overlaps; component |= overlaps; frontier.extend(overlaps)
                components += 1
            dependence = "INDEPENDENT" if components == len(ids) else "DEPENDENT"
            return {
                "evidence_ids": ids,
                "independent_root_count": components,
                "dependence": dependence,
                "root_origins": sorted(set().union(*roots_by_id.values()) if roots_by_id else set()),
                "common_mode_groups": all_modes,
            }
        return {
            "evidence_ids": ids,
            "independent_root_count": 0,
            "dependence": dependence,
            "root_origins": sorted(set().union(*roots_by_id.values()) if roots_by_id else set()),
            "common_mode_groups": all_modes,
        }

    def claim_support_bundle(self, domain_id: str, logical_id: str) -> dict[str, Any]:
        claim = self._current_claim(domain_id, logical_id)
        paths = []
        for prow in self.db.execute(
            "SELECT path_id FROM justification_paths WHERE claim_revision_id=? ORDER BY path_id",
            (claim["claim_revision_id"],),
        ).fetchall():
            ids = [r[0] for r in self.db.execute(
                "SELECT evidence_id FROM justification_members WHERE path_id=? ORDER BY evidence_id", (prow[0],)
            ).fetchall()]
            live = []
            for eid in ids:
                e = self.db.execute(
                    "SELECT revoked_seq,deleted_seq,compromised_seq FROM evidence WHERE evidence_id=?", (eid,)
                ).fetchone()
                if e and e["revoked_seq"] is None and e["deleted_seq"] is None and e["compromised_seq"] is None:
                    live.append(eid)
            paths.append({"evidence_ids": ids, "live": len(live) == len(ids) and bool(ids)})
        live_ids = sorted({eid for p in paths if p["live"] for eid in p["evidence_ids"]})
        independence = self.evaluate_evidence_independence(domain_id, live_ids) if live_ids else {
            "evidence_ids": [], "independent_root_count": 0, "dependence": "NO_LIVE_SUPPORT", "root_origins": []
        }
        return {
            "claim_revision_id": claim["claim_revision_id"],
            "live_paths": paths,
            "supported": any(p["live"] for p in paths),
            "independence": independence,
        }

    def issue_evidence_independence_receipt(
        self, domain_id: str, evidence_ids: Iterable[str]
    ) -> EvidenceIndependenceReceipt:
        result = self.evaluate_evidence_independence(domain_id, evidence_ids)
        ids = list(result["evidence_ids"])
        deps: list[Dependency] = []
        for eid in ids:
            deps.append(Dependency("source", eid, self._generation(domain_id, "source", eid)))
            deps.append(Dependency("origin", eid, self._generation(domain_id, "origin", eid)))
        now = self._clock(); created_at = self._utc_text(now) if hasattr(self, "_utc_text") else now.isoformat()
        receipt = EvidenceIndependenceReceipt(
            receipt_id=f"independence_{uuid.uuid4().hex}", domain_id=domain_id, evidence_ids=ids,
            dependence=result["dependence"], independent_root_count=int(result["independent_root_count"]),
            root_origins=list(result.get("root_origins", [])), common_mode_groups=list(result.get("common_mode_groups", [])),
            dependencies=deps, created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO evidence_independence_receipts(receipt_id,domain_id,payload_json,dependencies_json,created_at) VALUES(?,?,?,?,?)",
            (receipt.receipt_id, domain_id, canonical_json(asdict(receipt)), canonical_json([asdict(d) for d in deps]), created_at),
        )
        return receipt

    def validate_evidence_independence_receipt(self, receipt_id: str) -> bool:
        row = self.db.execute("SELECT * FROM evidence_independence_receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
        if not row: raise KeyError(receipt_id)
        self.validate_dependencies(row["domain_id"], [Dependency(**d) for d in json.loads(row["dependencies_json"])])
        return True

    def issue_claim_support_bundle_receipt(self, domain_id: str, logical_id: str) -> SupportBundleReceipt:
        bundle = self.claim_support_bundle(domain_id, logical_id)
        live_ids = sorted({eid for path in bundle["live_paths"] if path["live"] for eid in path["evidence_ids"]})
        independence = self.issue_evidence_independence_receipt(domain_id, live_ids) if live_ids else None
        deps = [Dependency("claim", logical_id, self._generation(domain_id, "claim", logical_id))]
        all_ids = sorted({eid for path in bundle["live_paths"] for eid in path["evidence_ids"]})
        for eid in all_ids:
            deps.append(Dependency("source", eid, self._generation(domain_id, "source", eid)))
            deps.append(Dependency("origin", eid, self._generation(domain_id, "origin", eid)))
        now=self._clock(); created_at=self._utc_text(now) if hasattr(self,"_utc_text") else now.isoformat()
        receipt=SupportBundleReceipt(
            receipt_id=f"support_{uuid.uuid4().hex}", domain_id=domain_id, logical_id=logical_id,
            claim_revision_id=bundle["claim_revision_id"], live_paths=list(bundle["live_paths"]),
            supported=bool(bundle["supported"]), independence_receipt_id=None if independence is None else independence.receipt_id,
            dependencies=deps, created_at=created_at,
        )
        self.db.execute(
            "INSERT INTO support_bundle_receipts(receipt_id,domain_id,logical_id,payload_json,dependencies_json,created_at) VALUES(?,?,?,?,?,?)",
            (receipt.receipt_id,domain_id,logical_id,canonical_json(asdict(receipt)),canonical_json([asdict(d) for d in deps]),created_at),
        )
        return receipt

    def validate_claim_support_bundle_receipt(self, receipt_id: str) -> bool:
        row=self.db.execute("SELECT * FROM support_bundle_receipts WHERE receipt_id=?",(receipt_id,)).fetchone()
        if not row: raise KeyError(receipt_id)
        self.validate_dependencies(row["domain_id"],[Dependency(**d) for d in json.loads(row["dependencies_json"])])
        payload=json.loads(row["payload_json"]); child=payload.get("independence_receipt_id")
        if child: self.validate_evidence_independence_receipt(child)
        return True

    def certify_recoverability(
        self, domain_id: str, representation_id: str, *, query_family: str
    ) -> RecoverabilityCertificate:
        rep=self.db.execute("SELECT * FROM representations WHERE domain_id=? AND representation_id=?",(domain_id,representation_id)).fetchone()
        if not rep: raise KeyError(representation_id)
        requirements=self._family_requirements(query_family)
        loss=json.loads(rep["loss_json"]); exact={"PRESERVED_EXACT","PRESERVED_NORMALIZED"}
        missing={d for d in requirements if loss.get(d,"UNKNOWN") not in exact}
        source_ids=list(json.loads(rep["source_representation_ids_json"]))
        witnesses=[]
        for sid in source_ids:
            if all(self._source_can_supply_dimension(self.db.cursor(),domain_id,sid,d) for d in missing): witnesses.append(sid)
        if not missing: status="IN_REPRESENTATION"
        elif witnesses: status="SOURCE_REHYDRATABLE"
        else: status="IRRECOVERABLE_UNDER_CURRENT_RETENTION"
        deps=[Dependency("representation",representation_id,self._generation(domain_id,"representation",representation_id)), Dependency("query_family",query_family,self._generation(domain_id,"query_family",query_family))]
        for sid in source_ids: deps.append(Dependency("representation",sid,self._generation(domain_id,"representation",sid)))
        now=self._clock(); created_at=self._utc_text(now) if hasattr(self,"_utc_text") else now.isoformat()
        cert=RecoverabilityCertificate(f"recover_{uuid.uuid4().hex}",domain_id,representation_id,query_family,status,sorted(witnesses),deps,created_at)
        self.db.execute(
            "INSERT INTO recoverability_certificates(certificate_id,domain_id,representation_id,query_family,payload_json,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (cert.certificate_id,domain_id,representation_id,query_family,canonical_json(asdict(cert)),canonical_json([asdict(d) for d in deps]),created_at),
        )
        return cert

    def validate_recoverability_certificate(self, certificate_id: str) -> bool:
        row=self.db.execute("SELECT * FROM recoverability_certificates WHERE certificate_id=?",(certificate_id,)).fetchone()
        if not row: raise KeyError(certificate_id)
        self.validate_dependencies(row["domain_id"],[Dependency(**d) for d in json.loads(row["dependencies_json"])])
        return True

    def register_integrity_authority_profile(
        self, domain_id: str, *, profile_id: str, revision: int, issuer: str,
        subject_ids: set[str], operations: set[str], accepted_authority_classes: set[str], enabled: bool = True, expires_at=None,
    ) -> int:
        if revision < 1 or not profile_id or not issuer or not subject_ids or not operations or not accepted_authority_classes:
            raise ValueError("integrity authority profile is incomplete")
        latest=self.db.execute(
            "SELECT revision,subject_ids_json,operations_json,accepted_authority_classes_json,enabled,issuer,expires_at FROM integrity_authority_profiles WHERE domain_id=? AND profile_id=? ORDER BY revision DESC LIMIT 1",
            (domain_id,profile_id),
        ).fetchone()
        expiry=self._expiry_text(expires_at) if hasattr(self,"_expiry_text") else None
        payload={"subject_ids":sorted(subject_ids),"operations":sorted(operations),"accepted_authority_classes":sorted(accepted_authority_classes),"enabled":bool(enabled),"issuer":issuer,"expires_at":expiry}
        if latest:
            old={"subject_ids":json.loads(latest["subject_ids_json"]),"operations":json.loads(latest["operations_json"]),"accepted_authority_classes":json.loads(latest["accepted_authority_classes_json"]),"enabled":bool(latest["enabled"]),"issuer":latest["issuer"],"expires_at":latest["expires_at"]}
            if revision==int(latest["revision"]) and old==payload: return revision
            if revision!=int(latest["revision"])+1: raise MemoryTransitionIncomplete("integrity authority profile revisions must be contiguous")
        elif revision!=1: raise MemoryTransitionIncomplete("first integrity authority profile revision must be 1")
        request={"profile_id":profile_id,"revision":revision,**payload}
        def mutate(cur,seq):
            cur.execute(
                "INSERT INTO integrity_authority_profiles(domain_id,profile_id,revision,issuer,subject_ids_json,operations_json,accepted_authority_classes_json,enabled,created_seq,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (domain_id,profile_id,revision,issuer,canonical_json(payload["subject_ids"]),canonical_json(payload["operations"]),canonical_json(payload["accepted_authority_classes"]),int(enabled),seq,expiry),
            )
            self._bump_generation(cur,domain_id,"integrity_authority",profile_id); self._bump_generation(cur,domain_id,"integrity_authority","global")
            return profile_id
        self._auto_commit(domain_id,"REGISTER_INTEGRITY_AUTHORITY_PROFILE",profile_id,request,mutate)
        return revision

    def _enforce_integrity_authority_profiles(self, cur, domain_id: str, logical_id: str, operation: str, support_paths: list[list[str]]) -> None:
        rows=cur.execute(
            "SELECT p.* FROM integrity_authority_profiles p JOIN (SELECT profile_id,MAX(revision) rev FROM integrity_authority_profiles WHERE domain_id=? GROUP BY profile_id) x ON x.profile_id=p.profile_id AND x.rev=p.revision WHERE p.domain_id=?",
            (domain_id,domain_id),
        ).fetchall()
        for profile in rows:
            subjects=set(json.loads(profile["subject_ids_json"])); ops=set(json.loads(profile["operations_json"]))
            if logical_id not in subjects and "*" not in subjects: continue
            if operation not in ops and "*" not in ops: continue
            if not bool(profile["enabled"]) or (hasattr(self,"_row_expired") and self._row_expired(profile)):
                raise MemoryTransitionIncomplete(f"integrity authority profile {profile['profile_id']!r} is revoked or expired")
            accepted=set(json.loads(profile["accepted_authority_classes_json"]))
            for path in support_paths:
                for eid in set(path):
                    classes={r[0] for r in cur.execute(
                        "SELECT authority_class FROM origin_bindings WHERE domain_id=? AND evidence_id=? AND revoked_seq IS NULL",(domain_id,eid)
                    ).fetchall()}
                    if not classes or ("*" not in accepted and not (classes & accepted)):
                        raise MemoryTransitionIncomplete(
                            f"support evidence {eid!r} does not satisfy integrity authority profile {profile['profile_id']!r}"
                        )

    def register_publication_policy(
        self, source_domain: str, destination_domain: str, *, policy_id: str, revision: int, issuer: str,
        allow: bool, allowed_principals: set[str], preserve_origin: bool, expires_at=None,
    ) -> int:
        if revision<1 or not policy_id or not issuer or not allowed_principals:
            raise ValueError("publication policy is incomplete")
        latest=self.db.execute(
            "SELECT * FROM publication_policies WHERE source_domain=? AND destination_domain=? AND policy_id=? ORDER BY revision DESC LIMIT 1",
            (source_domain,destination_domain,policy_id),
        ).fetchone()
        expiry=self._expiry_text(expires_at) if hasattr(self,"_expiry_text") else None
        payload={"allow":bool(allow),"allowed_principals":sorted(allowed_principals),"preserve_origin":bool(preserve_origin),"issuer":issuer,"expires_at":expiry}
        if latest:
            old={"allow":bool(latest["allow_transfer"]),"allowed_principals":json.loads(latest["allowed_principals_json"]),"preserve_origin":bool(latest["preserve_origin"]),"issuer":latest["issuer"],"expires_at":latest["expires_at"]}
            if revision==int(latest["revision"]) and old==payload: return revision
            if revision!=int(latest["revision"])+1: raise MemoryTransitionIncomplete("publication policy revisions must be contiguous")
        elif revision!=1: raise MemoryTransitionIncomplete("first publication policy revision must be 1")
        request={"destination_domain":destination_domain,"policy_id":policy_id,"revision":revision,**payload}
        def mutate(cur,seq):
            cur.execute(
                "INSERT INTO publication_policies(source_domain,destination_domain,policy_id,revision,issuer,allow_transfer,allowed_principals_json,preserve_origin,created_seq,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (source_domain,destination_domain,policy_id,revision,issuer,int(allow),canonical_json(payload["allowed_principals"]),int(preserve_origin),seq,expiry),
            )
            self._bump_generation(cur,source_domain,"publication_policy",destination_domain)
            return policy_id
        self._auto_commit(source_domain,"REGISTER_PUBLICATION_POLICY",policy_id,request,mutate)
        return revision

    def _active_publication_policy(self, source_domain: str, destination_domain: str, cur=None):
        q=cur or self.db
        return q.execute(
            "SELECT * FROM publication_policies WHERE source_domain=? AND destination_domain=? ORDER BY created_seq DESC,revision DESC,policy_id DESC LIMIT 1",
            (source_domain,destination_domain),
        ).fetchone()

    def register_transformation_contract(
        self, profile_id: str, *, revision: int, transform_kind: str,
        protected_dimensions: set[str], forbidden_loss: set[str],
    ) -> str:
        if int(revision) < 1:
            raise MemoryTransitionIncomplete("transformation contract revision must be >= 1")
        contract = {
            "profile_id": profile_id, "revision": int(revision), "transform_kind": transform_kind,
            "protected_dimensions": sorted(protected_dimensions), "forbidden_loss": sorted(forbidden_loss),
        }
        cdigest = digest(contract)
        with self._lock:
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT contract_digest FROM transformation_contracts WHERE profile_id=? AND revision=?",
                    (profile_id, revision),
                ).fetchone()
                if row:
                    if row[0] != cdigest:
                        raise MemoryTransitionIncomplete("transformation contract identity collision")
                    cur.execute("COMMIT")
                    return cdigest
                latest = cur.execute(
                    "SELECT MAX(revision) FROM transformation_contracts WHERE profile_id=?", (profile_id,)
                ).fetchone()[0]
                if latest is None:
                    if int(revision) != 1:
                        raise MemoryTransitionIncomplete("first transformation contract revision must be 1")
                elif int(revision) != int(latest) + 1:
                    raise MemoryTransitionIncomplete(
                        f"transformation contract revision must advance contiguously from {latest} to {int(latest)+1}"
                    )
                affected_domains = {
                    row[0] for row in cur.execute(
                        "SELECT DISTINCT domain_id FROM representations WHERE transform_profile=? "
                        "UNION SELECT DISTINCT domain_id FROM representation_proposals WHERE transform_profile=?",
                        (profile_id, profile_id),
                    ).fetchall()
                }
                cur.execute(
                    "INSERT INTO transformation_contracts(profile_id,revision,transform_kind,protected_dimensions_json,forbidden_loss_json,contract_digest) VALUES(?,?,?,?,?,?)",
                    (profile_id, revision, transform_kind, canonical_json(sorted(protected_dimensions)),
                     canonical_json(sorted(forbidden_loss)), cdigest),
                )
                # The registry is a policy/procedure clock. Any domain that already
                # depends on this profile must observe the revision through Semantic OCC.
                for domain_id in sorted(affected_domains):
                    self._bump_generation(cur, domain_id, "transform_profile", profile_id)
                cur.execute("COMMIT")
                return cdigest
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def _transformation_contract(self, profile_id: str):
        return self.db.execute(
            "SELECT * FROM transformation_contracts WHERE profile_id=? ORDER BY revision DESC LIMIT 1", (profile_id,)
        ).fetchone()

    def compromise_evidence(self, domain_id: str, evidence_id: str, *, principal: str, reason: str) -> str:
        row = self.db.execute(
            "SELECT * FROM evidence WHERE domain_id=? AND evidence_id=?", (domain_id, evidence_id)
        ).fetchone()
        if not row:
            raise KeyError(evidence_id)
        if not self._is_allowed(principal, row["allowed_principals_json"]):
            raise MemoryScopeBlocked("cannot compromise-mark inaccessible evidence")
        compromise_id = f"compromise_{uuid.uuid4().hex}"
        affected = sorted(self._representations_depending_on_evidence(domain_id, evidence_id)) if hasattr(self, "_representations_depending_on_evidence") else []
        request = {"evidence_id": evidence_id, "reason": reason, "principal": principal}
        def mutate(cur, seq):
            current = cur.execute("SELECT compromised_seq FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone()
            if current[0] is None:
                cur.execute("UPDATE evidence SET compromised_seq=?,compromise_reason=? WHERE evidence_id=?", (seq, reason, evidence_id))
                cur.execute(
                    "INSERT INTO source_compromises(compromise_id,domain_id,evidence_id,reason,principal,created_seq) VALUES(?,?,?,?,?,?)",
                    (compromise_id, domain_id, evidence_id, reason, principal, seq),
                )
                for rep_id in affected:
                    rep = cur.execute("SELECT region_id,invalidated_seq FROM representations WHERE representation_id=?", (rep_id,)).fetchone()
                    if rep and rep["invalidated_seq"] is None:
                        cur.execute("UPDATE representations SET invalidated_seq=? WHERE representation_id=?", (seq, rep_id))
                        self._bump_generation(cur, domain_id, "representation", rep_id)
                        self._bump_generation(cur, domain_id, "region", rep["region_id"])
                for prop in cur.execute(
                    "SELECT proposal_id,source_representation_ids_json FROM representation_proposals WHERE domain_id=? AND invalidated_seq IS NULL AND promoted_representation_id IS NULL",
                    (domain_id,),
                ).fetchall():
                    if set(json.loads(prop["source_representation_ids_json"])) & set(affected):
                        cur.execute("UPDATE representation_proposals SET invalidated_seq=? WHERE proposal_id=?", (seq, prop["proposal_id"]))
                self._bump_generation(cur, domain_id, "source", evidence_id)
                self._bump_generation(cur, domain_id, "origin", "global")
                self._bump_generation(cur, domain_id, "query_domain", "global")
            return compromise_id
        self._auto_commit(domain_id, "COMPROMISE_EVIDENCE", compromise_id, request, mutate)
        return compromise_id
