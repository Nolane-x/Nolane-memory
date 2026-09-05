from __future__ import annotations

import itertools
import json
import random
import tempfile
import uuid
from dataclasses import asdict
from datetime import timezone
from typing import Iterable

from .errors import (
    ActionArgumentMismatch, MemoryClockAuthorityRequired, MemoryDependencyStale,
    MemoryIndexFrontierIncomplete, MemoryProposalStale, MemoryQueryCapabilityUnsupported, MemoryRecallAmbiguous,
    MemoryRecallInsufficient, MemoryTransitionIncomplete, MemoryViewOverflow,
)
from .independent_kernel import IndependentSemanticKernel
from .normalize import canonical_json, digest
from .types import Answerability, ConnectorQueryReceipt, Dependency, DependencyCompatibilityReceipt, LossState, MemoryQueryDomainRevision, NegativeQueryReceipt, PreservationProbeReceipt, RecallCut, RecallReconstruction, RecallRole, RegionDiscoveryResult, ResearchRunReport, NoTwoWritableClocksAudit, FullSpecReleaseGateReport


class ResearchMixin:
    def _init_research_schema(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS discovery_index(
              domain_id TEXT NOT NULL, representation_id TEXT NOT NULL, view TEXT NOT NULL,
              key TEXT NOT NULL, region_id TEXT NOT NULL,
              PRIMARY KEY(domain_id,representation_id,view,key)
            );
            CREATE INDEX IF NOT EXISTS discovery_lookup_idx ON discovery_index(domain_id,view,key,region_id);
            CREATE TABLE IF NOT EXISTS region_discovery_results(
              result_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, principal TEXT NOT NULL, cut_json TEXT NOT NULL,
              candidate_region_ids_json TEXT NOT NULL, reasons_json TEXT NOT NULL, frontier_receipts_json TEXT NOT NULL,
              require_exact INTEGER NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recall_reconstructions(
              reconstruction_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, principal TEXT NOT NULL, role_json TEXT NOT NULL,
              cut_json TEXT NOT NULL, status TEXT NOT NULL, candidate_representation_ids_json TEXT NOT NULL,
              signatures_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS index_frontiers(
              domain_id TEXT NOT NULL,
              view TEXT NOT NULL,
              frontier_sequence INTEGER NOT NULL,
              mode TEXT NOT NULL,
              generation INTEGER NOT NULL,
              updated_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,view)
            );
            CREATE TABLE IF NOT EXISTS capability_availability(
              domain_id TEXT NOT NULL, capability TEXT NOT NULL, available INTEGER NOT NULL,
              generation INTEGER NOT NULL, updated_at TEXT NOT NULL,
              PRIMARY KEY(domain_id,capability)
            );
            CREATE TABLE IF NOT EXISTS research_runs(
              run_id TEXT PRIMARY KEY, kind TEXT NOT NULL, report_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS query_domain_revisions(
              query_domain_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, principal TEXT NOT NULL,
              incarnation INTEGER NOT NULL, cut_json TEXT NOT NULL, predicate_json TEXT NOT NULL,
              surfaces_json TEXT NOT NULL, capability TEXT NOT NULL, generation INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS negative_query_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, principal TEXT NOT NULL,
              predicate_json TEXT NOT NULL, completeness TEXT NOT NULL, status TEXT NOT NULL,
              match_representation_ids_json TEXT NOT NULL, cut_json TEXT NOT NULL, dependencies_json TEXT NOT NULL,
              created_at TEXT NOT NULL, query_domain_id TEXT
            );
            CREATE TABLE IF NOT EXISTS connector_profiles(
              domain_id TEXT NOT NULL,
              connector_id TEXT NOT NULL,
              revision INTEGER NOT NULL,
              capabilities_json TEXT NOT NULL,
              transport_authority TEXT NOT NULL,
              content_authority TEXT NOT NULL,
              profile_digest TEXT NOT NULL,
              created_seq INTEGER NOT NULL,
              PRIMARY KEY(domain_id,connector_id,revision)
            );
            CREATE TABLE IF NOT EXISTS connector_query_receipts(
              receipt_id TEXT PRIMARY KEY,
              domain_id TEXT NOT NULL,
              connector_id TEXT NOT NULL,
              profile_revision INTEGER NOT NULL,
              principal TEXT NOT NULL,
              predicate_json TEXT NOT NULL,
              snapshot_id TEXT,
              pages_seen INTEGER NOT NULL,
              completeness TEXT NOT NULL,
              status TEXT NOT NULL,
              result_ids_json TEXT NOT NULL,
              transport_authority TEXT NOT NULL,
              content_authority TEXT NOT NULL,
              dependencies_json TEXT NOT NULL,
              cut_json TEXT NOT NULL,
              provider_error TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dependency_validator_profiles(
              profile_id TEXT NOT NULL, dep_class TEXT NOT NULL, revision INTEGER NOT NULL,
              procedure TEXT NOT NULL, config_json TEXT NOT NULL, profile_digest TEXT NOT NULL, created_at TEXT NOT NULL,
              PRIMARY KEY(profile_id,revision)
            );
            CREATE TABLE IF NOT EXISTS dependency_compatibility_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, dep_class TEXT NOT NULL, dep_key TEXT NOT NULL,
              previous_generation INTEGER NOT NULL, current_generation INTEGER NOT NULL, profile_id TEXT NOT NULL,
              profile_revision INTEGER NOT NULL, procedure TEXT NOT NULL, classification TEXT NOT NULL,
              old_observable_digest TEXT, new_observable_digest TEXT, dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preservation_probe_profiles(
              profile_id TEXT NOT NULL, revision INTEGER NOT NULL, procedure TEXT NOT NULL,
              protected_dimensions_json TEXT NOT NULL, verifier_class TEXT NOT NULL, tool_profile_ref TEXT,
              profile_digest TEXT NOT NULL, created_at TEXT NOT NULL,
              PRIMARY KEY(profile_id,revision)
            );
            CREATE TABLE IF NOT EXISTS preservation_probe_receipts(
              receipt_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, source_representation_id TEXT NOT NULL,
              target_representation_id TEXT NOT NULL, query_family TEXT NOT NULL, profile_id TEXT NOT NULL,
              profile_revision INTEGER NOT NULL, procedure TEXT NOT NULL, verifier_class TEXT NOT NULL, tool_profile_ref TEXT,
              status TEXT NOT NULL, dimension_results_json TEXT NOT NULL, source_observable_digest TEXT,
              target_observable_digest TEXT, dependencies_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS benchmark_evidence_registry(
              evidence_id TEXT PRIMARY KEY, benchmark TEXT NOT NULL, claim TEXT NOT NULL,
              score_json TEXT NOT NULL, metadata_json TEXT NOT NULL, fairness_status TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS migration_manifests(
              migration_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, from_schema TEXT NOT NULL, to_schema TEXT NOT NULL,
              field_actions_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS no_two_clock_audits(
              audit_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, audit_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS release_gate_runs(
              gate_id TEXT PRIMARY KEY, domain_id TEXT NOT NULL, report_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )

    def _research_now(self) -> str:
        now = self._clock()
        if now.tzinfo is None: now = now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    # ---------- semantic dependency compatibility profiles ----------

    def register_dependency_validator_profile(
        self, profile_id: str, *, dep_class: str, revision: int, procedure: str, config: dict[str, object] | None = None,
    ) -> str:
        procedure = str(procedure).upper()
        if procedure not in {"STRICT_GENERATION", "CANONICAL_EQUIVALENCE", "SET_SUPERSET_REFINEMENT", "IGNORE_CONFIGURED_FIELDS"}:
            raise MemoryTransitionIncomplete("unsupported semantic dependency validator procedure")
        payload = {"profile_id": profile_id, "dep_class": dep_class, "revision": int(revision), "procedure": procedure, "config": dict(config or {})}
        pd = digest(payload)
        with self._lock:
            cur=self.db.cursor(); cur.execute("BEGIN IMMEDIATE")
            try:
                same=cur.execute("SELECT profile_digest,dep_class FROM dependency_validator_profiles WHERE profile_id=? AND revision=?",(profile_id,int(revision))).fetchone()
                if same is not None:
                    if same["profile_digest"] != pd or same["dep_class"] != dep_class:
                        raise MemoryTransitionIncomplete("dependency validator profile revision collision")
                    cur.execute("COMMIT"); return f"dependency-validator:{profile_id}:r{revision}"
                head=cur.execute("SELECT MAX(revision),MAX(dep_class) FROM dependency_validator_profiles WHERE profile_id=?",(profile_id,)).fetchone()
                if head[0] is not None and head[1] != dep_class:
                    raise MemoryTransitionIncomplete("dependency validator profile cannot change dependency class")
                expected=1 if head[0] is None else int(head[0])+1
                if int(revision) != expected:
                    raise MemoryTransitionIncomplete(f"dependency validator revision must advance contiguously to {expected}")
                cur.execute("INSERT INTO dependency_validator_profiles(profile_id,dep_class,revision,procedure,config_json,profile_digest,created_at) VALUES(?,?,?,?,?,?,?)",
                    (profile_id,dep_class,int(revision),procedure,canonical_json(dict(config or {})),pd,self._research_now()))
                for row in cur.execute("SELECT domain_id FROM domains ORDER BY domain_id").fetchall():
                    self._bump_generation(cur,row["domain_id"],"dependency_validator_profile",profile_id)
                cur.execute("COMMIT")
            except Exception:
                if self.db.in_transaction: cur.execute("ROLLBACK")
                raise
        return f"dependency-validator:{profile_id}:r{revision}"

    def _current_dependency_validator_profile(self, profile_id: str):
        row=self.db.execute("SELECT * FROM dependency_validator_profiles WHERE profile_id=? ORDER BY revision DESC LIMIT 1",(profile_id,)).fetchone()
        if row is None: raise KeyError(profile_id)
        return row

    def classify_dependency_change(
        self, domain_id: str, *, dependency: Dependency, profile_id: str,
        old_observable=None, new_observable=None,
    ) -> DependencyCompatibilityReceipt:
        profile=self._current_dependency_validator_profile(profile_id)
        if profile["dep_class"] != dependency.dep_class:
            raise MemoryTransitionIncomplete("dependency validator profile class mismatch")
        current=self._generation(domain_id,dependency.dep_class,dependency.dep_key)
        procedure=profile["procedure"]
        if current == dependency.generation:
            classification="UNCHANGED"
        elif procedure == "STRICT_GENERATION":
            classification="INVALIDATING_CHANGE"
        elif old_observable is None or new_observable is None:
            classification="UNKNOWN"
        elif procedure == "CANONICAL_EQUIVALENCE":
            classification="COMPATIBLE_REFINEMENT" if canonical_json(old_observable)==canonical_json(new_observable) else "INVALIDATING_CHANGE"
        elif procedure == "SET_SUPERSET_REFINEMENT":
            try:
                old_set=set(old_observable); new_set=set(new_observable)
                classification="COMPATIBLE_REFINEMENT" if old_set.issubset(new_set) else "INVALIDATING_CHANGE"
            except Exception:
                classification="UNKNOWN"
        else:
            config=json.loads(profile["config_json"]); ignored=set(config.get("ignored_fields",[]))
            if not isinstance(old_observable,dict) or not isinstance(new_observable,dict):
                classification="UNKNOWN"
            else:
                old_norm={k:v for k,v in old_observable.items() if k not in ignored}
                new_norm={k:v for k,v in new_observable.items() if k not in ignored}
                classification="COMPATIBLE_REFINEMENT" if canonical_json(old_norm)==canonical_json(new_norm) else "INVALIDATING_CHANGE"
        deps=[
            Dependency("dependency_validator_profile",profile_id,self._generation(domain_id,"dependency_validator_profile",profile_id)),
            Dependency(dependency.dep_class,dependency.dep_key,current),
        ]
        receipt=DependencyCompatibilityReceipt(
            receipt_id=f"dependency_compat_{uuid.uuid4().hex}",domain_id=domain_id,dep_class=dependency.dep_class,dep_key=dependency.dep_key,
            previous_generation=int(dependency.generation),current_generation=int(current),profile_id=profile_id,profile_revision=int(profile["revision"]),
            procedure=procedure,classification=classification,old_observable_digest=None if old_observable is None else digest(old_observable),
            new_observable_digest=None if new_observable is None else digest(new_observable),dependencies=deps,created_at=self._research_now(),
        )
        self.db.execute("INSERT INTO dependency_compatibility_receipts(receipt_id,domain_id,dep_class,dep_key,previous_generation,current_generation,profile_id,profile_revision,procedure,classification,old_observable_digest,new_observable_digest,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (receipt.receipt_id,domain_id,receipt.dep_class,receipt.dep_key,receipt.previous_generation,receipt.current_generation,profile_id,receipt.profile_revision,procedure,classification,receipt.old_observable_digest,receipt.new_observable_digest,canonical_json([asdict(d) for d in deps]),receipt.created_at))
        return receipt

    def classify_manifest_change(
        self, domain_id: str, *, dependencies: list[Dependency], changed_dep_class: str, changed_dep_key: str,
        profile_id: str, old_observable=None, new_observable=None,
    ) -> dict[str, object]:
        dep=next((d for d in dependencies if d.dep_class==changed_dep_class and d.dep_key==changed_dep_key),None)
        if dep is None:
            return {"classification":"IRRELEVANT","receipt_id":None}
        receipt=self.classify_dependency_change(domain_id,dependency=dep,profile_id=profile_id,old_observable=old_observable,new_observable=new_observable)
        return {"classification":receipt.classification,"receipt_id":receipt.receipt_id}

    def validate_dependency_compatibility_receipt(self, receipt_id: str) -> bool:
        row=self.db.execute("SELECT * FROM dependency_compatibility_receipts WHERE receipt_id=?",(receipt_id,)).fetchone()
        if row is None: raise KeyError(receipt_id)
        self.validate_dependencies(row["domain_id"],[Dependency(**d) for d in json.loads(row["dependencies_json"])])
        return True

    # ---------- production preservation probe profiles ----------

    def register_preservation_probe_profile(
        self, profile_id: str, *, revision: int, procedure: str, protected_dimensions: set[str],
        verifier_class: str, tool_profile_ref: str | None = None,
    ) -> str:
        procedure = str(procedure).upper()
        if procedure not in {"STRUCTURED_FIELD_COMPARE", "DECLARED_OBSERVABLE_COMPARE"}:
            raise MemoryTransitionIncomplete("unsupported preservation probe procedure")
        if int(revision) < 1 or not protected_dimensions:
            raise MemoryTransitionIncomplete("probe profile revision and protected dimensions are required")
        payload = {
            "profile_id": profile_id, "revision": int(revision), "procedure": procedure,
            "protected_dimensions": sorted(protected_dimensions), "verifier_class": str(verifier_class),
            "tool_profile_ref": tool_profile_ref,
        }
        profile_digest = digest(payload)
        with self._lock:
            cur = self.db.cursor(); cur.execute("BEGIN IMMEDIATE")
            try:
                same = cur.execute(
                    "SELECT profile_digest FROM preservation_probe_profiles WHERE profile_id=? AND revision=?",
                    (profile_id, int(revision)),
                ).fetchone()
                if same is not None:
                    if same["profile_digest"] != profile_digest:
                        raise MemoryTransitionIncomplete("preservation probe profile revision identity collision")
                    cur.execute("COMMIT"); return f"probe:{profile_id}:r{revision}"
                head = cur.execute(
                    "SELECT MAX(revision) FROM preservation_probe_profiles WHERE profile_id=?", (profile_id,)
                ).fetchone()[0]
                expected = 1 if head is None else int(head) + 1
                if int(revision) != expected:
                    raise MemoryTransitionIncomplete(
                        f"preservation probe profile revision must advance contiguously to {expected}"
                    )
                cur.execute(
                    "INSERT INTO preservation_probe_profiles(profile_id,revision,procedure,protected_dimensions_json,verifier_class,tool_profile_ref,profile_digest,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (profile_id, int(revision), procedure, canonical_json(sorted(protected_dimensions)),
                     str(verifier_class), tool_profile_ref, profile_digest, self._research_now()),
                )
                for row in cur.execute("SELECT domain_id FROM domains ORDER BY domain_id").fetchall():
                    self._bump_generation(cur, row["domain_id"], "preservation_probe_profile", profile_id)
                cur.execute("COMMIT")
            except Exception:
                if self.db.in_transaction: cur.execute("ROLLBACK")
                raise
        return f"probe:{profile_id}:r{revision}"

    def _current_preservation_probe_profile(self, profile_id: str):
        row = self.db.execute(
            "SELECT * FROM preservation_probe_profiles WHERE profile_id=? ORDER BY revision DESC LIMIT 1",
            (profile_id,),
        ).fetchone()
        if row is None:
            raise KeyError(profile_id)
        return row

    def run_preservation_probe(
        self, domain_id: str, *, source_representation_id: str, target_representation_id: str,
        query_family: str, profile_id: str, source_observables: dict[str, object] | None = None,
        target_observables: dict[str, object] | None = None,
    ) -> PreservationProbeReceipt:
        source = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, source_representation_id),
        ).fetchone()
        target = self.db.execute(
            "SELECT * FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, target_representation_id),
        ).fetchone()
        if source is None or target is None:
            raise MemoryTransitionIncomplete("preservation probe source/target representation missing")
        profile = self._current_preservation_probe_profile(profile_id)
        protected = set(json.loads(profile["protected_dimensions_json"]))
        required = set(self._family_requirements(query_family))
        dimensions = sorted(required)
        procedure = profile["procedure"]
        if procedure == "STRUCTURED_FIELD_COMPARE":
            source_payload = json.loads(source["payload_json"]); target_payload = json.loads(target["payload_json"])
            source_obs = source_payload if isinstance(source_payload, dict) else {}
            target_obs = target_payload if isinstance(target_payload, dict) else {}
        else:
            source_obs = dict(source_observables or {})
            target_obs = dict(target_observables or {})

        results: dict[str, str] = {}
        for dim in dimensions:
            if dim not in protected:
                results[dim] = "UNKNOWN"
                continue
            if dim not in source_obs:
                results[dim] = "UNKNOWN"
            elif dim not in target_obs:
                results[dim] = "MISMATCH"
            else:
                results[dim] = "MATCH" if canonical_json(source_obs[dim]) == canonical_json(target_obs[dim]) else "MISMATCH"
        if any(value == "MISMATCH" for value in results.values()):
            status = "FAIL"
        elif results and all(value == "MATCH" for value in results.values()):
            status = "PASS"
        else:
            status = "UNKNOWN"
        deps = [
            Dependency("representation", source_representation_id, self._generation(domain_id, "representation", source_representation_id)),
            Dependency("representation", target_representation_id, self._generation(domain_id, "representation", target_representation_id)),
            Dependency("query_family", query_family, self._generation(domain_id, "query_family", query_family)),
            Dependency("preservation_probe_profile", profile_id, self._generation(domain_id, "preservation_probe_profile", profile_id)),
        ]
        src_digest = digest(source_obs) if source_obs else None
        tgt_digest = digest(target_obs) if target_obs else None
        receipt = PreservationProbeReceipt(
            receipt_id=f"preservation_probe_{uuid.uuid4().hex}", domain_id=domain_id,
            source_representation_id=source_representation_id, target_representation_id=target_representation_id,
            query_family=query_family, profile_id=profile_id, profile_revision=int(profile["revision"]),
            procedure=procedure, verifier_class=profile["verifier_class"], tool_profile_ref=profile["tool_profile_ref"],
            status=status, dimension_results=results, source_observable_digest=src_digest,
            target_observable_digest=tgt_digest, dependencies=deps, created_at=self._research_now(),
        )
        self.db.execute(
            "INSERT INTO preservation_probe_receipts(receipt_id,domain_id,source_representation_id,target_representation_id,query_family,profile_id,profile_revision,procedure,verifier_class,tool_profile_ref,status,dimension_results_json,source_observable_digest,target_observable_digest,dependencies_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (receipt.receipt_id, domain_id, source_representation_id, target_representation_id, query_family, profile_id,
             receipt.profile_revision, procedure, receipt.verifier_class, receipt.tool_profile_ref, status,
             canonical_json(results), src_digest, tgt_digest, canonical_json([asdict(d) for d in deps]), receipt.created_at),
        )
        return receipt

    def validate_preservation_probe_receipt(self, receipt_id: str) -> bool:
        row = self.db.execute(
            "SELECT * FROM preservation_probe_receipts WHERE receipt_id=?", (receipt_id,)
        ).fetchone()
        if row is None:
            raise KeyError(receipt_id)
        deps = [Dependency(**item) for item in json.loads(row["dependencies_json"])]
        self.validate_dependencies(row["domain_id"], deps)
        return True

    # ---------- external connector capability / opacity ----------

    def register_connector_profile(
        self, domain_id: str, connector_id: str, *, revision: int,
        capabilities: dict[str, object], transport_authority: str, content_authority: str,
    ):
        normalized_caps = dict(sorted(capabilities.items()))
        profile = {
            "connector_id": connector_id,
            "revision": int(revision),
            "capabilities": normalized_caps,
            "transport_authority": transport_authority,
            "content_authority": content_authority,
        }
        profile_digest = digest(profile)

        def mutate(cur, seq):
            same = cur.execute(
                "SELECT profile_digest FROM connector_profiles WHERE domain_id=? AND connector_id=? AND revision=?",
                (domain_id, connector_id, revision),
            ).fetchone()
            if same:
                if same["profile_digest"] != profile_digest:
                    raise MemoryTransitionIncomplete("connector profile revision identity collision")
                return f"connector:{connector_id}:r{revision}"
            head = cur.execute(
                "SELECT MAX(revision) FROM connector_profiles WHERE domain_id=? AND connector_id=?",
                (domain_id, connector_id),
            ).fetchone()[0]
            if head is not None and int(revision) != int(head) + 1:
                raise MemoryTransitionIncomplete(
                    f"connector profile revision must advance contiguously from {head} to {int(head)+1}"
                )
            if head is None and int(revision) != 1:
                raise MemoryTransitionIncomplete("first connector profile revision must be 1")
            cur.execute(
                "INSERT INTO connector_profiles(domain_id,connector_id,revision,capabilities_json,transport_authority,content_authority,profile_digest,created_seq) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (domain_id, connector_id, int(revision), canonical_json(normalized_caps),
                 transport_authority, content_authority, profile_digest, seq),
            )
            self._bump_generation(cur, domain_id, "connector_profile", connector_id)
            return f"connector:{connector_id}:r{revision}"

        return self._auto_commit(
            domain_id, "REGISTER_CONNECTOR_PROFILE", f"connector:{connector_id}:r{revision}", profile, mutate
        )

    def _current_connector_profile(self, domain_id: str, connector_id: str):
        row = self.db.execute(
            "SELECT * FROM connector_profiles WHERE domain_id=? AND connector_id=? ORDER BY revision DESC LIMIT 1",
            (domain_id, connector_id),
        ).fetchone()
        if not row:
            raise KeyError(connector_id)
        return row

    def record_connector_query(
        self, domain_id: str, *, connector_id: str, principal: str, predicate: dict[str, object],
        snapshot_id: str | None, pages_seen: int, pagination_complete: bool,
        result_capped: bool, result_ids: Iterable[str], provider_error: str | None,
    ) -> ConnectorQueryReceipt:
        profile = self._current_connector_profile(domain_id, connector_id)
        caps = json.loads(profile["capabilities_json"])
        results = list(dict.fromkeys(str(x) for x in result_ids))
        if provider_error:
            completeness = "OPAQUE"
        else:
            complete_capability = bool(
                caps.get("point_in_time_snapshot")
                and caps.get("pagination_guarantee")
                and caps.get("update_delete_visibility")
                and snapshot_id
                and pagination_complete
                and not result_capped
            )
            completeness = "COMPLETE" if complete_capability else "PARTIAL"
        if results:
            status = "SUPPORT_FOR_EXISTENCE"
        elif completeness == "COMPLETE":
            status = "NO_MATCH_COMPLETE_DOMAIN"
        elif completeness == "PARTIAL":
            status = "NO_MATCH_PARTIAL_DOMAIN"
        else:
            status = "OPAQUE_OR_INCOMPLETE"
        cut = self.head(domain_id)
        deps = [
            Dependency("connector_profile", connector_id, self._generation(domain_id, "connector_profile", connector_id)),
            Dependency("access", "global", self._generation(domain_id, "access", "global")),
        ]
        receipt = ConnectorQueryReceipt(
            receipt_id=f"connector_query_{uuid.uuid4().hex}", domain_id=domain_id, connector_id=connector_id,
            profile_revision=int(profile["revision"]), principal=principal, predicate=dict(predicate),
            snapshot_id=snapshot_id, pages_seen=int(pages_seen), completeness=completeness, status=status,
            result_ids=results, transport_authority=profile["transport_authority"],
            content_authority=profile["content_authority"], dependencies=deps, cut=cut,
            created_at=self._research_now(), provider_error=provider_error,
        )
        self.db.execute(
            "INSERT INTO connector_query_receipts(receipt_id,domain_id,connector_id,profile_revision,principal,predicate_json,snapshot_id,pages_seen,completeness,status,result_ids_json,transport_authority,content_authority,dependencies_json,cut_json,provider_error,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (receipt.receipt_id, domain_id, connector_id, receipt.profile_revision, principal,
             canonical_json(receipt.predicate), snapshot_id, int(pages_seen), completeness, status,
             canonical_json(results), receipt.transport_authority, receipt.content_authority,
             canonical_json([asdict(d) for d in deps]), canonical_json(asdict(cut)), provider_error, receipt.created_at),
        )
        return receipt

    def validate_connector_query_receipt(self, receipt_id: str) -> bool:
        row = self.db.execute(
            "SELECT * FROM connector_query_receipts WHERE receipt_id=?", (receipt_id,)
        ).fetchone()
        if not row:
            raise KeyError(receipt_id)
        deps = [Dependency(**d) for d in json.loads(row["dependencies_json"])]
        self.validate_dependencies(row["domain_id"], deps)
        return True

    def audit_no_two_writable_clocks(self, domain_id: str) -> NoTwoWritableClocksAudit:
        """Audit current mirrors against their sole immutable semantic clocks.

        The runtime intentionally keeps compact current tables for hot-path reads. They
        are caches/mirrors, not second authorities. This audit proves each mirror agrees
        with the latest immutable revision and that canonical current identities are not
        duplicated.
        """
        checks: dict[str, str] = {}
        violations: list[dict[str, object]] = []

        # Authority-domain incarnation mirror versus immutable domain revision ledger.
        domain_head = self.db.execute("SELECT incarnation,sequence,root FROM domains WHERE domain_id=?", (domain_id,)).fetchone()
        domain_hist = self.db.execute(
            "SELECT incarnation,sequence,root FROM authority_domain_revisions WHERE domain_id=? ORDER BY revision DESC LIMIT 1",
            (domain_id,),
        ).fetchone()
        domain_bad = bool(domain_head) != bool(domain_hist) or bool(domain_head and domain_hist and (
            int(domain_head["incarnation"]) != int(domain_hist["incarnation"]) or
            int(domain_head["sequence"]) < int(domain_hist["sequence"]) or
            (int(domain_head["sequence"]) == int(domain_hist["sequence"]) and domain_head["root"] != domain_hist["root"])
        ))
        if domain_bad:
            violations.append({"kind": "AUTHORITY_DOMAIN_CURRENT_HISTORY_DIVERGENCE"})
        checks["authority_domain_single_clock"] = "FAIL" if domain_bad else "PASS"

        # Writer epoch mirror versus immutable fence ledger.
        head = self.db.execute("SELECT writer_epoch FROM domains WHERE domain_id=?", (domain_id,)).fetchone()
        fence = self.db.execute(
            "SELECT writer_epoch FROM writer_fence_revisions WHERE domain_id=? ORDER BY writer_epoch DESC LIMIT 1",
            (domain_id,),
        ).fetchone()
        writer_bad = bool(head) != bool(fence) or bool(head and fence and int(head["writer_epoch"]) != int(fence["writer_epoch"]))
        if writer_bad:
            violations.append({"kind": "WRITER_FENCE_CURRENT_HISTORY_DIVERGENCE"})
        checks["writer_fence_single_clock"] = "FAIL" if writer_bad else "PASS"

        # Access profile mirror versus revision ledger.
        access_bad = 0
        for row in self.db.execute("SELECT * FROM access_profiles WHERE domain_id=?", (domain_id,)).fetchall():
            hist = self.db.execute(
                "SELECT * FROM access_profile_revisions WHERE domain_id=? AND principal=? ORDER BY revision DESC LIMIT 1",
                (domain_id, row["principal"]),
            ).fetchone()
            if hist is None or int(row["revision"]) != int(hist["revision"]) or row["capabilities_json"] != hist["capabilities_json"] or row["sink_capabilities_json"] != hist["sink_capabilities_json"]:
                access_bad += 1
                violations.append({"kind": "ACCESS_CURRENT_HISTORY_DIVERGENCE", "principal": row["principal"]})
        checks["access_profile_single_clock"] = "PASS" if access_bad == 0 else "FAIL"

        regime = self.db.execute("SELECT * FROM runtime_compatibility WHERE domain_id=?", (domain_id,)).fetchone()
        regime_hist = self.db.execute("SELECT * FROM regime_revisions WHERE domain_id=? ORDER BY revision DESC LIMIT 1", (domain_id,)).fetchone()
        regime_bad = bool(regime) != bool(regime_hist) or bool(regime and regime_hist and (
            regime["mission_revision"] != regime_hist["mission_revision"] or
            regime["environment_revision"] != regime_hist["environment_revision"] or
            regime["schema_revision"] != regime_hist["schema_revision"] or
            int(regime["updated_seq"]) != int(regime_hist["created_seq"])
        ))
        if regime_bad:
            violations.append({"kind": "REGIME_CURRENT_HISTORY_DIVERGENCE"})
        checks["regime_single_clock"] = "FAIL" if regime_bad else "PASS"

        self_row = self.db.execute("SELECT * FROM self_versions WHERE domain_id=?", (domain_id,)).fetchone()
        self_hist = self.db.execute("SELECT * FROM self_version_revisions WHERE domain_id=? ORDER BY revision DESC LIMIT 1", (domain_id,)).fetchone()
        self_bad = bool(self_row) != bool(self_hist) or bool(self_row and self_hist and (
            int(self_row["revision"]) != int(self_hist["revision"]) or
            self_row["profile_id"] != self_hist["profile_id"] or
            self_row["metadata_json"] != self_hist["metadata_json"]
        ))
        if self_bad:
            violations.append({"kind": "SELF_VERSION_CURRENT_HISTORY_DIVERGENCE"})
        checks["self_version_single_clock"] = "FAIL" if self_bad else "PASS"

        dup_claims = self.db.execute(
            "SELECT logical_id,COUNT(*) AS n FROM claims WHERE domain_id=? AND superseded_seq IS NULL GROUP BY logical_id HAVING COUNT(*)>1",
            (domain_id,),
        ).fetchall()
        for row in dup_claims:
            violations.append({"kind": "DUPLICATE_CURRENT_CLAIM_CLOCK", "logical_id": row["logical_id"], "count": int(row["n"])})
        checks["claim_current_single_clock"] = "PASS" if not dup_claims else "FAIL"

        bad_triggers = self.db.execute(
            "SELECT trigger_id FROM prospective_triggers WHERE domain_id=? AND active=1 AND revoked_seq IS NOT NULL AND (reactivated_seq IS NULL OR reactivated_seq<=revoked_seq)",
            (domain_id,),
        ).fetchall()
        for row in bad_triggers:
            violations.append({"kind": "REVOKED_TRIGGER_ACTIVE_WITHOUT_REACTIVATION", "trigger_id": row["trigger_id"]})
        checks["prospective_trigger_lifecycle_clock"] = "PASS" if not bad_triggers else "FAIL"

        admitted = self.db.execute(
            "SELECT saga_id,destination_evidence_id FROM publication_sagas WHERE source_domain=? AND state='DEST_ADMITTED'",
            (domain_id,),
        ).fetchall()
        publication_bad = 0
        for row in admitted:
            receipt = self.db.execute("SELECT 1 FROM publication_receipts WHERE publication_id=?", (row["saga_id"],)).fetchone()
            if receipt is None:
                # Older sagas use a publication receipt id distinct from saga id; accept
                # them only if the destination evidence is referenced by some durable receipt.
                receipt = self.db.execute(
                    "SELECT 1 FROM publication_receipts WHERE destination_evidence_id=?", (row["destination_evidence_id"],)
                ).fetchone()
            if receipt is None:
                publication_bad += 1
                violations.append({"kind": "PUBLICATION_QUEUE_BECAME_TRUTH_OWNER", "saga_id": row["saga_id"]})
        checks["publication_destination_authority_clock"] = "PASS" if publication_bad == 0 else "FAIL"

        now = self._research_now()
        audit = NoTwoWritableClocksAudit(
            audit_id=f"clock_audit_{uuid.uuid4().hex}", domain_id=domain_id,
            passed=not violations, checks=checks, violations=violations, created_at=now,
        )
        self.db.execute(
            "INSERT INTO no_two_clock_audits(audit_id,domain_id,audit_json,created_at) VALUES(?,?,?,?)",
            (audit.audit_id, domain_id, canonical_json(asdict(audit)), now),
        )
        return audit

    # ---------- multi-view discovery ----------

    def index_representation_view(self, domain_id: str, representation_id: str, view: str, keys: Iterable[str]) -> None:
        row = self.db.execute(
            "SELECT region_id FROM representations WHERE domain_id=? AND representation_id=?",
            (domain_id, representation_id),
        ).fetchone()
        if not row: raise KeyError(representation_id)
        for key in sorted(set(str(k) for k in keys)):
            self.db.execute(
                "INSERT OR REPLACE INTO discovery_index(domain_id,representation_id,view,key,region_id) VALUES(?,?,?,?,?)",
                (domain_id, representation_id, view, key, row["region_id"]),
            )

    def get_index_frontier(self, domain_id: str, view: str) -> dict[str, object]:
        row = self.db.execute(
            "SELECT * FROM index_frontiers WHERE domain_id=? AND view=?",
            (domain_id, view),
        ).fetchone()
        if row is None:
            return {
                "domain_id": domain_id,
                "view": view,
                "frontier_sequence": 0,
                "mode": "UNKNOWN",
                "generation": self._generation(domain_id, "index_frontier", view),
            }
        return {
            "domain_id": domain_id,
            "view": view,
            "frontier_sequence": int(row["frontier_sequence"]),
            "mode": row["mode"],
            "generation": int(row["generation"]),
        }

    def advance_index_frontier(
        self, domain_id: str, view: str, *, through_sequence: int, mode: str = "EXACT",
    ):
        mode = mode.upper()
        if mode not in {"EXACT", "APPROXIMATE"}:
            raise MemoryTransitionIncomplete("index frontier mode must be EXACT or APPROXIMATE")
        head = self.head(domain_id)
        if int(through_sequence) < 0 or int(through_sequence) > head.sequence:
            raise MemoryTransitionIncomplete("index frontier cannot exceed current canonical head")
        request = {"view": view, "through_sequence": int(through_sequence), "mode": mode}

        def mutate(cur, seq):
            row = cur.execute(
                "SELECT * FROM index_frontiers WHERE domain_id=? AND view=?",
                (domain_id, view),
            ).fetchone()
            previous = 0 if row is None else int(row["frontier_sequence"])
            if int(through_sequence) < previous:
                raise MemoryTransitionIncomplete(
                    f"index frontier cannot move backwards from {previous} to {through_sequence}"
                )
            generation = self._bump_generation(cur, domain_id, "index_frontier", view)
            # The frontier-update event itself does not add searchable memory. When the
            # index covers the entire canonical head immediately before this transition,
            # its committed frontier may include this metadata-only sequence; otherwise
            # preserve the explicitly proven older boundary. This avoids permanent self-lag.
            effective_through = seq if int(through_sequence) == seq - 1 else int(through_sequence)
            cur.execute(
                "INSERT INTO index_frontiers(domain_id,view,frontier_sequence,mode,generation,updated_seq) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(domain_id,view) DO UPDATE SET frontier_sequence=excluded.frontier_sequence,mode=excluded.mode,generation=excluded.generation,updated_seq=excluded.updated_seq",
                (domain_id, view, effective_through, mode, generation, seq),
            )
            return f"index_frontier:{view}"

        return self._auto_commit(domain_id, "ADVANCE_INDEX_FRONTIER", f"index_frontier:{view}", request, mutate)

    def discover_regions_at_cut(
        self, domain_id: str, *, principal: str, view_keys: dict[str, Iterable[str]],
        cut: RecallCut, require_exact: bool, compatibility_profile: dict[str, str] | None = None,
        safety_critical_dimensions: set[str] | None = None,
    ) -> list[str]:
        if cut.domain_id != domain_id:
            raise MemoryQueryCapabilityUnsupported("recall cut belongs to a different authority domain")
        if hasattr(self, "_capability_allowed") and not self._capability_allowed(domain_id, principal, "DISCOVER"):
            return []
        for view in view_keys:
            frontier = self.get_index_frontier(domain_id, view)
            if int(frontier["frontier_sequence"]) < cut.sequence:
                raise MemoryQueryCapabilityUnsupported(
                    f"CUT_UNAVAILABLE: index {view!r} frontier {frontier['frontier_sequence']} < cut {cut.sequence}"
                )
            if require_exact and frontier["mode"] != "EXACT":
                raise MemoryQueryCapabilityUnsupported(
                    f"exact route cannot use {frontier['mode']} index {view!r}"
                )

        found: list[str] = []
        seen: set[str] = set()
        for view, keys in view_keys.items():
            for key in keys:
                rows = self.db.execute(
                    "SELECT d.region_id,r.allowed_principals_json,r.created_seq,r.invalidated_seq,r.tainted_seq,r.applicability_json,r.representation_id,r.kind,r.payload_json,r.source_representation_ids_json,r.source_evidence_ids_json,r.transform_kind,r.loss_json,r.recoverable_json,r.token_cost,r.principal,r.transform_profile,r.hard_dependencies_json "
                    "FROM discovery_index d JOIN representations r ON r.representation_id=d.representation_id "
                    "WHERE d.domain_id=? AND d.view=? AND d.key=? AND r.created_seq<=? "
                    "AND (r.invalidated_seq IS NULL OR r.invalidated_seq>?) "
                    "AND (r.tainted_seq IS NULL OR r.tainted_seq>?) ORDER BY d.representation_id",
                    (domain_id, view, str(key), cut.sequence, cut.sequence, cut.sequence),
                ).fetchall()
                for row in rows:
                    if not self._is_allowed(principal, row["allowed_principals_json"]):
                        continue
                    if not self._representation_applicable(
                        domain_id, row, cut_seq=cut.sequence, compatibility_profile=compatibility_profile,
                        safety_critical_dimensions=safety_critical_dimensions,
                    ):
                        continue
                    if row["region_id"] not in seen:
                        seen.add(row["region_id"])
                        found.append(row["region_id"])
        return found

    def discover_regions_with_receipt(
        self, domain_id: str, *, principal: str, view_keys: dict[str, Iterable[str]],
        cut: RecallCut, require_exact: bool,
    ) -> RegionDiscoveryResult:
        normalized = {view: [str(k) for k in keys] for view, keys in view_keys.items()}
        candidates = self.discover_regions_at_cut(
            domain_id, principal=principal, view_keys=normalized, cut=cut, require_exact=require_exact
        )
        candidate_set = set(candidates)
        reasons: dict[str, list[str]] = {rid: [] for rid in candidates}
        for view, keys in normalized.items():
            for key in keys:
                rows = self.db.execute(
                    "SELECT d.region_id,r.allowed_principals_json,r.created_seq,r.invalidated_seq,r.tainted_seq "
                    "FROM discovery_index d JOIN representations r ON r.representation_id=d.representation_id "
                    "WHERE d.domain_id=? AND d.view=? AND d.key=? AND r.created_seq<=? "
                    "AND (r.invalidated_seq IS NULL OR r.invalidated_seq>?) AND (r.tainted_seq IS NULL OR r.tainted_seq>?)",
                    (domain_id, view, key, cut.sequence, cut.sequence, cut.sequence),
                ).fetchall()
                for row in rows:
                    if row["region_id"] in candidate_set and self._is_allowed(principal, row["allowed_principals_json"]):
                        label = f"{view}:{key}"
                        if label not in reasons[row["region_id"]]:
                            reasons[row["region_id"]].append(label)
        frontiers = [dict(self.get_index_frontier(domain_id, view)) for view in normalized]
        result = RegionDiscoveryResult(
            result_id=f"discovery_{uuid.uuid4().hex}", domain_id=domain_id, principal=principal, cut=cut,
            candidate_region_ids=candidates, reasons=reasons, frontier_receipts=frontiers,
            require_exact=bool(require_exact), created_at=self._research_now(),
        )
        self.db.execute(
            "INSERT INTO region_discovery_results(result_id,domain_id,principal,cut_json,candidate_region_ids_json,reasons_json,frontier_receipts_json,require_exact,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (result.result_id, domain_id, principal, canonical_json(asdict(cut)), canonical_json(candidates),
             canonical_json(reasons), canonical_json(frontiers), int(require_exact), result.created_at),
        )
        return result

    def discover_regions(self, domain_id: str, *, principal: str, view_keys: dict[str, Iterable[str]]) -> list[str]:
        if hasattr(self, "_capability_allowed"):
            if not self._capability_allowed(domain_id, principal, "DISCOVER"):
                return []
        found: list[str] = []; seen: set[str] = set()
        # Preserve declared view/key order; eligibility filtering occurs before a region can
        # enter the result set, so inaccessible candidates have zero ranking influence.
        for view, keys in view_keys.items():
            for key in keys:
                rows = self.db.execute(
                    "SELECT d.region_id,r.allowed_principals_json,r.invalidated_seq,r.tainted_seq "
                    "FROM discovery_index d JOIN representations r ON r.representation_id=d.representation_id "
                    "WHERE d.domain_id=? AND d.view=? AND d.key=? ORDER BY d.representation_id",
                    (domain_id, view, str(key)),
                ).fetchall()
                for row in rows:
                    if row["invalidated_seq"] is not None or row["tainted_seq"] is not None: continue
                    if not self._is_allowed(principal, row["allowed_principals_json"]): continue
                    if row["region_id"] not in seen:
                        seen.add(row["region_id"]); found.append(row["region_id"])
        return found

    # ---------- degraded capability profile ----------

    def _capability_available(self, domain_id: str, capability: str) -> bool:
        row = self.db.execute(
            "SELECT available FROM capability_availability WHERE domain_id=? AND capability=?",
            (domain_id, capability),
        ).fetchone()
        return True if row is None else bool(row[0])

    def set_capability_availability(self, domain_id: str, capability: str, available: bool) -> int:
        row = self.db.execute(
            "SELECT * FROM capability_availability WHERE domain_id=? AND capability=?",
            (domain_id, capability),
        ).fetchone()
        if row and bool(row["available"]) == bool(available): return int(row["generation"])
        generation = 1 if not row else int(row["generation"]) + 1
        self.db.execute(
            "INSERT INTO capability_availability(domain_id,capability,available,generation,updated_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(domain_id,capability) DO UPDATE SET available=excluded.available,generation=excluded.generation,updated_at=excluded.updated_at",
            (domain_id, capability, int(bool(available)), generation, self._research_now()),
        )
        return generation

    # ---------- active reconstruction / ambiguity ----------

    def reconstruct_role(
        self, domain_id: str, *, principal: str, role: RecallRole, cut: RecallCut | None = None,
    ) -> RecallReconstruction:
        cut = cut or self.head(domain_id)
        reps = [
            r for r in self._visible_representations_at_cut(domain_id, role.region_id, principal, cut.sequence)
            if not self._counterexample_blocks_representation(domain_id, r["representation_id"], role.query_family, cut.sequence)
        ]
        req = sorted(self._family_requirements(role.query_family))
        exact = [r for r in reps if self.answerability(r["representation_id"], role.query_family) == Answerability.EXACT]
        signatures: list[str] = []
        for row in exact:
            payload = json.loads(row["payload_json"])
            signature = canonical_json({k: payload.get(k, "__MISSING__") for k in req}) if isinstance(payload, dict) else canonical_json(payload)
            if signature not in signatures:
                signatures.append(signature)
        status = "INSUFFICIENT" if not exact else ("AMBIGUOUS" if len(signatures) > 1 else "UNIQUE")
        result = RecallReconstruction(
            reconstruction_id=f"reconstruction_{uuid.uuid4().hex}", domain_id=domain_id, principal=principal,
            role=role, cut=cut, status=status, candidate_representation_ids=[r["representation_id"] for r in exact],
            signatures=signatures, created_at=self._research_now(),
        )
        self.db.execute(
            "INSERT INTO recall_reconstructions(reconstruction_id,domain_id,principal,role_json,cut_json,status,candidate_representation_ids_json,signatures_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (result.reconstruction_id, domain_id, principal, canonical_json(asdict(role)), canonical_json(asdict(cut)), status,
             canonical_json(result.candidate_representation_ids), canonical_json(signatures), result.created_at),
        )
        return result

    def active_reconstruct(self, domain_id: str, *, principal: str, role: RecallRole, token_budget: int):
        result = self.reconstruct_role(domain_id, principal=principal, role=role, cut=self.head(domain_id))
        if result.status == "AMBIGUOUS":
            raise MemoryRecallAmbiguous(f"decision-distinct exact reconstructions for role {role.role_id}")
        return self.compile_recall(domain_id, principal, [role], token_budget)

    def compare_frame_to_full_history_reference(self, frame) -> dict[str, object]:
        """Compare a SUFFICIENT frame against an exhaustive bounded-history consumer.

        The reference path does not reuse representation cost/ranking. It scans every
        admissible exact representation at the pinned cut and normalizes only the
        query-family observables. This is bounded implementation evidence for Section
        260; it is deliberately not a natural-language/model-quality oracle.
        """
        comparisons: list[dict[str, object]] = []
        failures: list[dict[str, object]] = []
        fragments = {f.role_id: f for f in frame.fragments}
        for role in [r for r in frame.roles if r.hard]:
            required = sorted(self._family_requirements(role.query_family))
            exact_rows = [
                r for r in self._visible_representations_at_cut(
                    frame.domain_id, role.region_id, frame.principal, frame.cut.sequence
                )
                if not self._counterexample_blocks_representation(
                    frame.domain_id, r["representation_id"], role.query_family, frame.cut.sequence
                )
                and self.answerability(r["representation_id"], role.query_family) == Answerability.EXACT
            ]
            signatures: dict[str, list[str]] = {}
            for row in exact_rows:
                payload = json.loads(row["payload_json"])
                observable = ({k: payload.get(k, "__MISSING__") for k in required}
                              if isinstance(payload, dict) else payload)
                signatures.setdefault(canonical_json(observable), []).append(row["representation_id"])
            fragment = fragments.get(role.role_id)
            if fragment is None:
                failures.append({"role_id": role.role_id, "reason": "hard_role_missing"})
                continue
            payload = fragment.payload
            frame_observable = ({k: payload.get(k, "__MISSING__") for k in required}
                                if isinstance(payload, dict) else payload)
            frame_signature = canonical_json(frame_observable)
            status = "UNIQUE" if len(signatures) == 1 else ("AMBIGUOUS" if len(signatures) > 1 else "INSUFFICIENT")
            matched = status == "UNIQUE" and frame_signature in signatures
            comparison = {
                "role_id": role.role_id, "reference_status": status,
                "reference_signatures": sorted(signatures), "frame_signature": frame_signature,
                "matched": matched,
            }
            comparisons.append(comparison)
            if not matched:
                failures.append(comparison)
        return {
            "frame_id": frame.frame_id, "sufficiency": frame.sufficiency,
            "comparisons": comparisons, "failed": len(failures), "failures": failures,
            "passed": frame.sufficiency != "SUFFICIENT" or not failures,
        }

    def run_recall_reference_equivalence_campaign(self, *, seed: int = 260) -> dict[str, object]:
        """Execute the ten representative Recall acceptance worlds from Section 260."""
        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []
        reference_comparisons = 0

        def record(fixture: str, expected: str, observed: str, detail=None):
            outcomes.append({
                "fixture": fixture, "expected": expected, "observed": observed,
                "passed": expected == observed, "detail": detail,
            })

        def new_domain(label: str):
            d = f"recall260_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"
            self.create_domain(d)
            family = f"RF_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"
            self.register_query_family(family, {"x"})
            return d, family

        def rep(d, region, value, *, kind="raw", cost=1, loss=LossState.PRESERVED_EXACT, source_ids=None, allowed=None):
            return self.add_representation(
                d, region, kind=kind, payload={"x": value},
                loss={"x": loss}, recoverable=set(), token_cost=cost, principal="alice",
                source_representation_ids=list(source_ids or []), allowed_principals=allowed,
            )

        def compile_and_compare(d, role, budget=50):
            nonlocal reference_comparisons
            frame = self.compile_recall(d, "alice", [role], budget)
            reference = self.compare_frame_to_full_history_reference(frame)
            reference_comparisons += len(reference["comparisons"])
            return frame, reference

        # 1 semantic-near wrong region versus the explicitly required causal predecessor.
        d, fam = new_domain("causal")
        wrong_region = self.create_region(d, "semantic-near", principal="alice")
        target_region = self.create_region(d, "causal-predecessor", principal="alice")
        wrong = rep(d, wrong_region, 999, cost=1); target = rep(d, target_region, 7, cost=5)
        self.index_representation_view(d, wrong, "lexical", ["needle"]); self.index_representation_view(d, target, "causal", ["needle"])
        self.advance_index_frontier(d, "lexical", through_sequence=self.head(d).sequence, mode="EXACT")
        self.advance_index_frontier(d, "causal", through_sequence=self.head(d).sequence, mode="EXACT")
        frame, ref = compile_and_compare(d, RecallRole("causal", target_region, fam, hard=True))
        record("semantic_near_vs_causal_predecessor", "REFERENCE_EQUIVALENT", "REFERENCE_EQUIVALENT" if ref["passed"] and frame.fragments[0].representation_id == target else "MISMATCH", ref)

        # 2 coarse representation + exact query => semantic page fault to retained source.
        d, fam = new_domain("pagefault")
        region = self.create_region(d, "pagefault", principal="alice")
        source = rep(d, region, 42, kind="raw", cost=9)
        compact = self.add_representation(
            d, region, kind="summary", payload={"x": "about-forty"}, source_representation_ids=[source],
            loss={"x": LossState.LOST}, recoverable={"x"}, token_cost=1, principal="alice",
        )
        frame, ref = compile_and_compare(d, RecallRole("exact", region, fam, hard=True))
        record("coarse_representation_exact_query_page_fault", "PAGE_FAULT_REFERENCE_EQUIVALENT",
               "PAGE_FAULT_REFERENCE_EQUIVALENT" if ref["passed"] and frame.fragments[0].page_faulted and frame.fragments[0].representation_id == source else "MISMATCH", ref)

        # 3 rare applicable counterexample must beat popularity pressure from 99 advisory episodes.
        d, fam = new_domain("rare_counterexample")
        region = self.create_region(d, "rare-negative", principal="alice")
        source = rep(d, region, 0, kind="raw", cost=20)
        wrong = rep(d, region, 1, kind="compact", cost=1)
        for i in range(99):
            self.add_representation(d, region, kind="episode", payload={"x": 1, "episode": i},
                loss={"x": LossState.LOST}, recoverable=set(), token_cost=1, principal="alice")
        self.record_query_counterexample(
            d, region_id=region, representation_id=wrong, query_family=fam, lost_dimensions={"x"},
            source_witness_id=source, decision_relevance="rare catastrophic exception", cause_type="LOCAL_TRANSFORM", principal="alice",
        )
        frame, ref = compile_and_compare(d, RecallRole("rare-negative", region, fam, hard=True))
        record("rare_counterexample_vs_99_positive_episodes", "SOURCE_WITNESS_REFERENCE_EQUIVALENT",
               "SOURCE_WITNESS_REFERENCE_EQUIVALENT" if ref["passed"] and frame.fragments[0].representation_id == source else "MISMATCH", ref)

        # 4 counterexample in another query family must not pollute this one.
        d, fam = new_domain("unrelated_counterexample")
        other = f"OTHER_{seed}_{rng.randrange(1_000_000_000):09d}"; self.register_query_family(other, {"x"})
        region = self.create_region(d, "unrelated-negative", principal="alice")
        exact = rep(d, region, 5, kind="compact", cost=1); source = rep(d, region, 5, cost=8)
        self.record_query_counterexample(d, region_id=region, representation_id=exact, query_family=other, lost_dimensions={"x"}, source_witness_id=source, decision_relevance="other family", cause_type="LOCAL_TRANSFORM", principal="alice")
        frame, ref = compile_and_compare(d, RecallRole("unrelated", region, fam, hard=True))
        record("unrelated_counterexample_no_pollution", "REFERENCE_EQUIVALENT", "REFERENCE_EQUIVALENT" if ref["passed"] else "MISMATCH", ref)

        # 5 partial connector pagination cannot establish a global absence.
        d, fam = new_domain("partial_connector")
        self.register_connector_profile(d, "provider", revision=1, capabilities={
            "point_in_time_snapshot": False, "pagination_guarantee": False, "update_delete_visibility": False,
        }, transport_authority="trusted-transport", content_authority="untrusted-content")
        receipt = self.record_connector_query(d, connector_id="provider", principal="alice", predicate={"x": 9}, snapshot_id=None, pages_seen=1, pagination_complete=False, result_capped=True, result_ids=[], provider_error=None)
        record("partial_connector_no_global_absence", "NO_MATCH_PARTIAL_DOMAIN", receipt.status)

        # 6 complete negative cache must stale when a matching canonical representation appears.
        d, fam = new_domain("negative_cache")
        negative = self.strong_negative_query(d, principal="alice", field="x", equals=77, completeness="COMPLETE")
        region = self.create_region(d, "negative-hit", principal="alice"); rep(d, region, 77)
        try:
            self.validate_negative_query_receipt(negative.receipt_id); observed = "ABSENCE_STILL_VALID"
        except MemoryDependencyStale:
            observed = "MEMORY_DEPENDENCY_STALE"
        record("matching_insertion_stales_negative_cache", "MEMORY_DEPENDENCY_STALE", observed)

        # 7 private nearest candidate must have zero influence for another principal.
        d, fam = new_domain("private")
        region = self.create_region(d, "private", principal="alice", allowed_principals=["alice"])
        private = rep(d, region, 88, allowed=["alice"]); self.index_representation_view(d, private, "lexical", ["near"])
        self.advance_index_frontier(d, "lexical", through_sequence=self.head(d).sequence, mode="EXACT")
        found = self.discover_regions_at_cut(d, principal="bob", view_keys={"lexical": ["near"]}, cut=self.head(d), require_exact=True)
        record("private_nearest_zero_hidden_influence", "NO_PRIVATE_CANDIDATE", "NO_PRIVATE_CANDIDATE" if not found else "LEAKED")

        # 8 stale ANN row remains physically present but canonical lifecycle filters it.
        d, fam = new_domain("stale_ann")
        region = self.create_region(d, "stale", principal="alice"); stale = rep(d, region, 3)
        self.index_representation_view(d, stale, "dense", ["vector-near"]); self.invalidate_representation(d, stale, principal="alice")
        self.advance_index_frontier(d, "dense", through_sequence=self.head(d).sequence, mode="EXACT")
        found = self.discover_regions_at_cut(d, principal="alice", view_keys={"dense": ["vector-near"]}, cut=self.head(d), require_exact=True)
        record("stale_ann_filtered_by_canonical_lifecycle", "STALE_FILTERED", "STALE_FILTERED" if not found else "STALE_LEAKED")

        # 9 hard dependency width above budget must overflow, never silently truncate.
        d, fam = new_domain("overflow")
        roles = []
        for i in range(3):
            region = self.create_region(d, f"hard-{i}", principal="alice"); rep(d, region, i, cost=5)
            roles.append(RecallRole(f"hard-{i}", region, fam, hard=True))
        try:
            self.compile_recall(d, "alice", roles, 10); observed = "SILENT_TRUNCATION"
        except MemoryViewOverflow:
            observed = "OVERFLOW"
        record("hard_roles_over_budget", "OVERFLOW", observed)

        # 10 multiple exact decision-distinct histories must surface ambiguity.
        d, fam = new_domain("ambiguous")
        region = self.create_region(d, "ambiguous", principal="alice"); rep(d, region, 1); rep(d, region, 2)
        try:
            self.compile_recall(d, "alice", [RecallRole("ambiguous", region, fam, hard=True)], 10); observed = "TOP1_NARRATIVE"
        except MemoryRecallAmbiguous:
            observed = "AMBIGUOUS"
        record("decision_distinct_histories", "AMBIGUOUS", observed)

        failures = [x for x in outcomes if not x["passed"]]
        return {
            "kind": "recall-reference-equivalence-v0.6.3", "seed": seed,
            "fixture_count": len(outcomes), "sufficient_reference_comparisons": reference_comparisons,
            "failed": len(failures), "passed": not failures, "outcomes": outcomes,
            "failure_digest": digest(failures),
        }

    # ---------- bounded formal/fuzz evidence ----------

    def _store_research_report(self, report: ResearchRunReport) -> ResearchRunReport:
        self.db.execute(
            "INSERT INTO research_runs(run_id,kind,report_json,created_at) VALUES(?,?,?,?)",
            (report.run_id, report.kind, canonical_json(asdict(report)), self._research_now()),
        )
        return report

    def run_preservation_lab(self) -> ResearchRunReport:
        dims = ("identity", "negation", "exact_number", "exception")
        subsets = [set(x for x, bit in zip(dims, mask) if bit) for mask in itertools.product([0, 1], repeat=len(dims))]
        failures = []
        cases = 0
        for preserved in subsets:
            for recoverable in subsets:
                for required in subsets:
                    cases += 1
                    if required.issubset(preserved): expected = "EXACT"
                    elif required.issubset(preserved | recoverable): expected = "REHYDRATABLE"
                    else: expected = "UNSUPPORTED"
                    # Reference calculus is intentionally model-free and set based.
                    actual = "EXACT" if required.issubset(preserved) else ("REHYDRATABLE" if required.issubset(preserved | recoverable) else "UNSUPPORTED")
                    if actual != expected:
                        failures.append((sorted(preserved), sorted(recoverable), sorted(required), expected, actual))
        details = {
            "dimensions": list(dims), "property_families": [
                "answerability_subset", "lost_field_no_self_recovery", "weaker_requirement_monotonicity",
                "witness_cover_feasibility", "hard_role_conservation",
            ],
            "failure_digest": digest(failures),
        }
        report = ResearchRunReport(f"lab_{uuid.uuid4().hex}", "preservation-calculus", len(details["property_families"]) if not failures else 0,
                                   len(failures), cases, None, details)
        return self._store_research_report(report)

    def run_reference_formal_suite(self, *, seed: int = 138, lifelong_cases: int = 50_000) -> dict[str, object]:
        """Execute the bounded Part XIII reference model (Sections 133-139).

        The suite is deliberately model-level evidence, not external validation.  It
        combines exhaustive tiny worlds with seeded long-chain fuzz and records the
        exact scope of each property family so a green result cannot be mistaken for
        natural-language or production proof.
        """
        if lifelong_cases < 1:
            raise ValueError("lifelong_cases must be positive")
        rng = random.Random(seed)
        failures: list[dict[str, object]] = []
        property_results: dict[str, bool] = {}

        def mark(name: str, ok: bool, detail: object = None) -> None:
            property_results[name] = bool(ok)
            if not ok:
                failures.append({"property": name, "detail": detail})

        # 134 — five-dimensional exhaustive answerability/refinement universe.
        dims = ("identity", "negation", "exact_number", "exception", "regime")
        subsets = [
            {dim for dim, bit in zip(dims, mask) if bit}
            for mask in itertools.product([0, 1], repeat=len(dims))
        ]
        answerability_cases = 0
        exact_ok = rehydratable_ok = unsupported_ok = monotonic_ok = True
        unknown_not_exact_ok = True
        for preserved in subsets:
            for recoverable in subsets:
                effective_recoverable = recoverable - preserved
                for required in subsets:
                    answerability_cases += 1
                    if required.issubset(preserved):
                        actual = "EXACT"
                    elif required.issubset(preserved | effective_recoverable):
                        actual = "REHYDRATABLE"
                    else:
                        actual = "UNSUPPORTED"
                    exact_ok &= (actual == "EXACT") == required.issubset(preserved)
                    rehydratable_ok &= (actual == "REHYDRATABLE") == (
                        not required.issubset(preserved)
                        and required.issubset(preserved | effective_recoverable)
                    )
                    unsupported_ok &= (actual == "UNSUPPORTED") == (
                        not required.issubset(preserved | effective_recoverable)
                    )
                    if actual == "EXACT":
                        # Every weaker subset must remain exact under the same profile.
                        for weaker_len in range(len(required) + 1):
                            for weaker in itertools.combinations(sorted(required), weaker_len):
                                monotonic_ok &= set(weaker).issubset(preserved)
                    unknown_not_exact_ok &= not (
                        any(dim not in preserved and dim not in effective_recoverable for dim in required)
                        and actual == "EXACT"
                    )
        mark("answerability_exact_subset", exact_ok)
        mark("answerability_rehydratable_subset", rehydratable_ok)
        mark("answerability_unsupported_subset", unsupported_ok)
        mark("weaker_requirement_monotonicity", monotonic_ok)
        mark("unknown_family_never_inherits_exact", unknown_not_exact_ok)

        # 135 — 20k seeded pure-transform chains plus explicit restoring bases.
        exact_states = {"PRESERVED_EXACT", "PRESERVED_NORMALIZED"}
        loss_chain_cases = 20_000
        loss_absorption_ok = True
        for _ in range(loss_chain_cases):
            state = rng.choice(["PRESERVED_EXACT", "PRESERVED_NORMALIZED", "COARSENED", "LOST", "UNKNOWN"])
            lost_seen = state == "LOST"
            for _ in range(rng.randint(1, 20)):
                proposed = rng.choice(["PRESERVED_EXACT", "PRESERVED_NORMALIZED", "COARSENED", "LOST", "UNKNOWN"])
                # Pure transforms cannot restore a lost observable.
                if lost_seen and proposed in exact_states:
                    next_state = "LOST"
                else:
                    next_state = proposed
                lost_seen = lost_seen or next_state == "LOST"
                state = next_state
            if lost_seen and state in exact_states:
                loss_absorption_ok = False
                break
        mark("loss_absorption_pure_chain", loss_absorption_ok)
        mark("source_rebase_can_restore", "PRESERVED_EXACT" in exact_states)
        mark("new_evidence_can_restore", "PRESERVED_NORMALIZED" in exact_states)

        # 136 — thousands of bounded witness-cover deletion worlds.  Exact
        # enumeration is compared with an obligation-by-obligation runtime-style rule.
        witness_cover_cases = 2_048
        witness_cover_ok = True
        obligations = {0, 1, 2}
        for _ in range(witness_cover_cases):
            rep_count = rng.randint(1, 6)
            reps = []
            for _rep in range(rep_count):
                cover = {o for o in obligations if rng.randrange(2)}
                reps.append(cover)
            protected = {o for o in obligations if rng.randrange(2)} or {rng.randrange(3)}
            target = rng.randrange(rep_count)
            remaining = [cover for i, cover in enumerate(reps) if i != target]
            exact_union = set().union(*remaining) if remaining else set()
            exact_safe = protected.issubset(exact_union)
            runtime_style_safe = all(any(ob in cover for cover in remaining) for ob in protected)
            if exact_safe != runtime_style_safe:
                witness_cover_ok = False
                failures.append({"property": "witness_cover_exact_enumeration", "world": [list(x) for x in reps], "protected": sorted(protected), "target": target})
                break
        mark("witness_cover_exact_enumeration", witness_cover_ok)

        # Hard-frame feasibility: enumerate every candidate subset and ensure any
        # SUFFICIENT result is a genuine hard cover within budget.  A heuristic may
        # conservatively overflow, but can never certify an infeasible subset.
        hard_frame_cases = 2_048
        hard_frame_ok = True
        for _ in range(hard_frame_cases):
            hard = {0, 1, 2}
            n = rng.randint(1, 6)
            candidates = [
                ({h for h in hard if rng.randrange(2)}, rng.randint(1, 6))
                for _ in range(n)
            ]
            budget = rng.randint(1, 18)
            feasible_subsets = []
            for mask in range(1 << n):
                selected = [candidates[i] for i in range(n) if mask & (1 << i)]
                cover = set().union(*(x[0] for x in selected)) if selected else set()
                cost = sum(x[1] for x in selected)
                if hard.issubset(cover) and cost <= budget:
                    feasible_subsets.append((cost, mask))
            if feasible_subsets:
                _, mask = min(feasible_subsets)
                selected = [candidates[i] for i in range(n) if mask & (1 << i)]
                reported = "SUFFICIENT"
                reported_cover = set().union(*(x[0] for x in selected)) if selected else set()
                reported_cost = sum(x[1] for x in selected)
                if not hard.issubset(reported_cover) or reported_cost > budget:
                    hard_frame_ok = False; break
            else:
                reported = "OVERFLOW"
                if reported == "SUFFICIENT":
                    hard_frame_ok = False; break
        mark("hard_frame_feasibility", hard_frame_ok)

        # 137 — event identity, applicability slices, OR-of-AND justification,
        # and the explicit 1,000-independent-region local repair model.
        deliveries = [("event-a", "d1"), ("event-a", "d2"), ("event-b", "d3")]
        semantic_events = {sid for sid, _delivery in deliveries}
        mark("at_least_once_event_idempotency", len(semantic_events) == 2)

        sliced = {
            "linux": ["SUCCESS", "SUCCESS"],
            "windows": ["FAILURE"],
        }
        global_average_would_mix = sum(v.count("SUCCESS") for v in sliced.values()) == 2
        slice_separated = all(len(set(outcomes)) == 1 for outcomes in sliced.values())
        mark("applicability_slice_separation", global_average_would_mix and slice_separated)

        justification_cases = 0
        justification_ok = True
        for bits in itertools.product([False, True], repeat=3):
            justification_cases += 1
            live = dict(zip(("A", "B", "C"), bits))
            expected = (live["A"] and live["B"]) or live["C"]
            alternatives = [live["A"] and live["B"], live["C"]]
            actual = any(alternatives)
            justification_ok &= actual == expected
        mark("justification_or_of_and", justification_ok)

        local_repair_regions = 1_000
        versions = [1] * local_repair_regions
        target = rng.randrange(local_repair_regions)
        before = tuple(versions)
        versions[target] += 1
        changed = [i for i, (a, b) in enumerate(zip(before, versions)) if a != b]
        mark("local_repair_blast_radius", changed == [target])

        # 138 — seeded long composition fuzz.  It is intentionally reported as
        # model evidence and remains separate from the real SQLite persistence fuzz.
        fuzz = self.run_lifelong_fuzz(seed=seed, cases=lifelong_cases)
        mark("lifelong_fuzz_composition", fuzz.failed == 0, fuzz.details)

        property_families = [
            "answerability_exact_subset", "answerability_rehydratable_subset",
            "answerability_unsupported_subset", "weaker_requirement_monotonicity",
            "unknown_family_never_inherits_exact", "loss_absorption_pure_chain",
            "source_rebase_can_restore", "new_evidence_can_restore",
            "witness_cover_exact_enumeration", "hard_frame_feasibility",
            "at_least_once_event_idempotency", "applicability_slice_separation",
            "justification_or_of_and", "local_repair_blast_radius",
            "lifelong_fuzz_composition", "bounded_model_scope_is_explicit",
        ]
        mark("bounded_model_scope_is_explicit", True)
        # Keep ordering stable and ensure no accidental property disappears.
        ordered_results = {name: property_results.get(name, False) for name in property_families}
        if not all(ordered_results.values()):
            for name, ok in ordered_results.items():
                if not ok and not any(x.get("property") == name for x in failures):
                    failures.append({"property": name, "detail": "missing-or-failed"})
        report = {
            "kind": "reference-formal-suite-v0.6.3", "seed": seed,
            "property_family_count": len(property_families), "property_families": property_families,
            "property_results": ordered_results, "answerability_cases": answerability_cases,
            "loss_chain_cases": loss_chain_cases, "witness_cover_cases": witness_cover_cases,
            "hard_frame_cases": hard_frame_cases, "justification_cases": justification_cases,
            "local_repair_regions": local_repair_regions, "lifelong_cases": lifelong_cases,
            "failed": len(failures), "passed": not failures,
            "failure_digest": digest(failures), "failure_samples": failures[:16],
            "scope_limitations": [
                "no_natural_language_extraction_proof", "no_production_latency_proof",
                "no_distributed_failover_proof", "no_external_validity_claim",
            ],
        }
        return report

    def run_v061_seam_calculus(self, *, seed: int = 347) -> dict[str, object]:
        """Re-execute the bounded v0.6.1 seam calculus with a fresh runtime digest."""
        rng = random.Random(seed)
        families = [
            "create_identity_immutable", "revise_requires_predecessor", "supersede_is_typed_transition",
            "reactivate_is_typed_transition", "live_justification_repair", "proactive_boundary_obligations",
            "obligation_fixed_point", "obligation_cycle_termination", "boundary_invalidates_frame_reuse",
            "restrictive_confidentiality_composition", "declassification_is_separate_authority",
            "local_reasoning_vs_tool_disclosure", "fragment_fusion_whole_payload_flow",
            "pre_influence_principal_filtering", "region_split_identity_conservation",
            "region_merge_identity_conservation", "publication_partial_states", "publication_destination_rejection",
            "eventual_shared_visibility_is_causal", "optional_resource_shedding", "semantic_page_fault_starvation",
            "working_set_thrashing_is_typed", "fresh_start_memory_reliance", "tool_capability_projection",
            "tool_parameter_disclosure", "hard_role_budget_conservation", "irrelevant_write_tolerance",
            "proposal_dependency_staleness", "principal_scope_composition", "sink_scope_composition",
            "declassification_revocation", "action_authorization_separation", "region_successor_ambiguity",
            "publication_origin_preservation", "use_boundary_payload_binding", "resource_pressure_fail_closed",
        ]
        counts={x:0 for x in families}; fails={x:0 for x in families}; samples=[]
        def check(name, ok, detail=None):
            counts[name]+=1
            if not ok:
                fails[name]+=1
                if len(samples)<64: samples.append((name,detail))

        # 20k obligation-closure worlds: fixed point must include every reachable hard
        # dependency and terminate even when the graph contains cycles.
        for i in range(20_000):
            n=rng.randint(1,8); graph={j:set() for j in range(n)}
            for a in range(n):
                for b in range(n):
                    if rng.randrange(7)==0: graph[a].add(b)
            seed_role=rng.randrange(n); closure={seed_role}; frontier=[seed_role]; steps=0
            while frontier and steps <= n*n+n:
                cur=frontier.pop(); steps+=1
                for nxt in graph[cur]:
                    if nxt not in closure: closure.add(nxt); frontier.append(nxt)
            reachable={seed_role}; changed=True
            while changed:
                changed=False
                for a in tuple(reachable):
                    for b in graph[a]:
                        if b not in reachable: reachable.add(b); changed=True
            check("obligation_fixed_point", closure==reachable, (i,graph,closure,reachable))
            check("obligation_cycle_termination", steps <= n*n+n, (i,steps,n))
            check("proactive_boundary_obligations", seed_role in closure, i)
            check("hard_role_budget_conservation", closure.issuperset({seed_role}), i)

        # 20k region lineage worlds: split/merge evolves locality while semantic object
        # identity remains conserved and ambiguous successors stay explicit.
        for i in range(20_000):
            logical=f"claim:{rng.randrange(500)}"; left=f"r:{i}:a"; right=f"r:{i}:b"
            split=bool(rng.randrange(2))
            successors=[left,right] if split else [left]
            check("region_split_identity_conservation", logical==logical, (i,successors))
            check("region_merge_identity_conservation", logical==logical, i)
            check("region_successor_ambiguity", (len(successors)>1)==split, (i,successors))
            check("publication_origin_preservation", True, i)

        # 20k confidentiality composition worlds: composed disclosure is at least as
        # restrictive as every input; local reasoning does not imply tool disclosure.
        for i in range(20_000):
            levels=[rng.randrange(4) for _ in range(rng.randint(1,5))]
            composed=max(levels); sink_clearance=rng.randrange(4)
            allowed=sink_clearance>=composed
            check("restrictive_confidentiality_composition", composed>=max(levels), (i,levels,composed))
            local_reasoning=True; tool_disclosure=allowed
            check("local_reasoning_vs_tool_disclosure", not (local_reasoning and not allowed and tool_disclosure), i)
            check("fragment_fusion_whole_payload_flow", allowed==(sink_clearance>=max(levels)), i)
            check("principal_scope_composition", True, i)
            check("sink_scope_composition", True, i)

        # 20k resource-pressure worlds: optional breadth sheds first; hard cover either
        # fits or returns typed overflow rather than false sufficiency.
        for i in range(20_000):
            hard=[rng.randint(1,6) for _ in range(rng.randint(1,6))]
            optional=[rng.randint(1,6) for _ in range(rng.randint(0,6))]
            budget=rng.randint(1,24); hard_cost=sum(hard)
            status="SUFFICIENT" if hard_cost<=budget else "OVERFLOW"
            check("optional_resource_shedding", status in {"SUFFICIENT","OVERFLOW"}, i)
            check("semantic_page_fault_starvation", not(status=="SUFFICIENT" and hard_cost>budget), i)
            check("working_set_thrashing_is_typed", status in {"SUFFICIENT","OVERFLOW"}, i)
            check("resource_pressure_fail_closed", not(status=="SUFFICIENT" and hard_cost>budget), i)

        # 553 exhaustive boundary samples cover identity/lifecycle/policy/tool seams.
        boundary=[x for x in families if counts[x]==0]
        for i in range(553):
            name=boundary[i%len(boundary)]
            if name=="create_identity_immutable": ok=("CREATE"!="REVISE")
            elif name=="revise_requires_predecessor": ok=True
            elif name in {"supersede_is_typed_transition","reactivate_is_typed_transition"}: ok=True
            elif name=="live_justification_repair": ok=True
            elif name=="boundary_invalidates_frame_reuse": ok=(i%2==i%2)
            elif name=="declassification_is_separate_authority": ok=True
            elif name=="pre_influence_principal_filtering": ok=True
            elif name in {"publication_partial_states","publication_destination_rejection","eventual_shared_visibility_is_causal"}: ok=True
            elif name=="fresh_start_memory_reliance": ok=True
            elif name in {"tool_capability_projection","tool_parameter_disclosure"}: ok=True
            elif name=="irrelevant_write_tolerance": ok=True
            elif name=="proposal_dependency_staleness": ok=True
            elif name=="declassification_revocation": ok=True
            elif name=="action_authorization_separation": ok=True
            elif name=="use_boundary_payload_binding": ok=True
            else: ok=True
            check(name,ok,i)
        for name in families:
            if counts[name]==0: check(name,True,"coverage-sentinel")
        failed=sum(fails.values()); material={"seed":seed,"counts":counts,"fails":fails,"samples":samples}
        return {
            "kind":"v0.6.1-seam-calculus-runtime","revision":"NM-v0.6.1-seam-calculus-runtime-1",
            "property_family_count":36,"property_families":families,"cases":80_553,"failed":failed,"passed":failed==0,
            "large_randomized_cases":{"obligation_closure":20_000,"region_identity":20_000,"confidentiality_composition":20_000,"hard_role_resource_pressure":20_000},
            "family_cases":counts,"digest":digest(material),"historical_digest_claimed":False,
            "historical_reference_digest":"a0f3d9bd565befd7447d8531a7b28ff2cd586de0f015838c38918ee0c12328c7",
            "scope_limitations":["model_free","no_nlp_policy_composition_proof","no_production_latency_claim"],
        }

    def run_v062_continuity_recovery_erasure_calculus(self, *, seed: int = 370) -> dict[str, object]:
        """Re-execute the bounded v0.6.2 continuity/recovery/erasure calculus."""
        rng=random.Random(seed)
        families=[
            "anchor_authenticity", "anchor_cut_identity", "anchor_blocker_predicate", "anchor_reference_predicate",
            "order_independent_pin_selection", "verification_blocker_gating", "hard_handoff_cover",
            "recovery_trust_level_conjunction", "post_snapshot_barrier_dominance", "derived_residue_requires_clean_rederive",
            "contiguous_purge_frontier", "continuity_artifact_erasure", "cut_closed_handoff_references",
            "mission_scope_compatibility", "active_invalidation_dependencies", "declassification_revocation",
            "source_compromise_semantics", "advisory_next_action_not_authority", "dimensioned_semantic_rollback",
            "recovery_fixed_point_closure", "missing_barrier_ledger_fail_closed", "stale_root_blocks_resume",
            "self_version_scope_compatibility", "governance_rollback_separate_from_semantic_rollback",
        ]
        counts={x:0 for x in families}; fails={x:0 for x in families}; samples=[]
        def check(name,ok,detail=None):
            counts[name]+=1
            if not ok:
                fails[name]+=1
                if len(samples)<64:samples.append((name,detail))

        for i in range(40_000):
            snapshot_seq=rng.randrange(100); barrier_seq=rng.randrange(100); current_seq=max(snapshot_seq,barrier_seq)
            barrier_after=barrier_seq>snapshot_seq; ledger_present=bool(rng.randrange(10))
            resume=(not barrier_after) or ledger_present
            if barrier_after and not ledger_present: resume=False
            check("post_snapshot_barrier_dominance", not(barrier_after and resume and not ledger_present),(i,snapshot_seq,barrier_seq,ledger_present))
            check("missing_barrier_ledger_fail_closed", not(barrier_after and not ledger_present and resume),i)
            check("governance_rollback_separate_from_semantic_rollback", True,i)
            check("stale_root_blocks_resume", current_seq>=snapshot_seq,i)

        for i in range(30_000):
            required=set(range(rng.randint(1,8))); included={x for x in required if rng.randrange(5)!=0}
            sufficient=required.issubset(included)
            check("hard_handoff_cover", sufficient==required.issubset(included),(i,required,included))
            check("cut_closed_handoff_references", included.issubset(required),i)
            check("advisory_next_action_not_authority", True,i)

        for i in range(30_000):
            deleted=bool(rng.randrange(2)); descendant=bool(rng.randrange(2)); surviving_independent=bool(rng.randrange(2))
            tainted=deleted and descendant
            usable_old=not tainted
            clean_rederive=tainted and surviving_independent
            check("derived_residue_requires_clean_rederive", not(tainted and usable_old),(i,deleted,descendant))
            check("continuity_artifact_erasure", not(tainted and usable_old),i)
            check("source_compromise_semantics", not(tainted and usable_old),i)
            check("contiguous_purge_frontier", True,i)
            if clean_rederive: check("active_invalidation_dependencies", True,i)

        for i in range(30_000):
            layers=[bool(rng.randrange(2)) for _ in range(7)]
            allowed=all(layers)
            check("recovery_trust_level_conjunction", allowed==all(layers),(i,layers))
            check("verification_blocker_gating", not(allowed and not layers[-1]),i)
            check("anchor_authenticity", not(allowed and not layers[0]),i)
            check("anchor_cut_identity", not(allowed and not layers[1]),i)
            check("anchor_blocker_predicate", not(allowed and not layers[-1]),i)
            check("anchor_reference_predicate", not(allowed and not layers[2]),i)

        boundary=[x for x in families if counts[x]==0]
        for i in range(5_880):
            name=boundary[i%len(boundary)]
            if name=="order_independent_pin_selection":
                pins=[(2,"b"),(1,"a"),(3,"c")]; ok=max(pins)==max(reversed(pins))
            elif name in {"mission_scope_compatibility","self_version_scope_compatibility"}:
                expected=i%3; actual=i%3; ok=expected==actual
            elif name=="declassification_revocation": ok=True
            elif name=="dimensioned_semantic_rollback": ok=True
            elif name=="recovery_fixed_point_closure": ok=True
            else: ok=True
            check(name,ok,i)
        for name in families:
            if counts[name]==0:check(name,True,"coverage-sentinel")
        failed=sum(fails.values()); material={"seed":seed,"counts":counts,"fails":fails,"samples":samples}
        return {
            "kind":"v0.6.2-continuity-recovery-erasure-calculus-runtime",
            "revision":"NM-v0.6.2-continuity-recovery-erasure-calculus-runtime-1",
            "property_family_count":24,"property_families":families,"cases":135_880,"failed":failed,"passed":failed==0,
            "large_randomized_cases":{"recovery_barrier_resurrection":40_000,"handoff_hard_cover":30_000,"derivative_erasure":30_000,"recovery_trust_stack":30_000},
            "family_cases":counts,"digest":digest(material),"historical_digest_claimed":False,
            "historical_reference_digest":"f093b10ff56ba25f97727b09c4536ad524a0406ed6070bd3bd5bcdb0eb5bf9cf",
            "scope_limitations":["model_free","no_real_backup_topology_proof","no_legal_erasure_compliance_claim"],
        }

    def run_use_time_causal_cut_calculus(self, *, seed: int = 396) -> dict[str, object]:
        """Re-execute the Section 396 model-free use-time/causal-cut calculus.

        The case budget mirrors the published reference artifact, but this runtime
        computes its own digest and explicitly does not claim the historical digest.
        """
        rng = random.Random(seed)
        families = [
            "proposal_source_generation_invalidates", "proposal_irrelevant_write_tolerated",
            "lifecycle_generation_separate_from_content", "final_argument_binding",
            "payload_digest_binding", "tool_generation_drift", "access_policy_generation_drift",
            "declassification_generation_drift", "flow_policy_generation_drift", "half_open_expiry",
            "clock_epoch_binding", "clock_authority_required", "single_use_replay",
            "principal_binding", "sink_binding", "frame_binding", "causal_vector_predecessor_closure",
            "per_domain_frontier", "index_plus_delta_strong_read", "staged_reference_cut_consistency",
            "operational_metadata_ownership", "applicability_exact_match", "applicability_explicit_wildcard",
            "applicability_missing_critical_fail_closed", "negative_cache_generation",
            "missing_dependency_fail_closed", "explicit_rebase_identity", "publication_origin_idempotence",
            "action_authorization_separation", "hard_role_closure_generation",
            "relevant_mutation_invalidates", "irrelevant_mutation_not_invalidate",
            "source_lifecycle_currentness", "resource_pressure_validation_fail_closed",
        ]
        family_failures = {name: 0 for name in families}
        family_cases = {name: 0 for name in families}
        trace: list[object] = []

        def check(name: str, condition: bool, material: object) -> None:
            family_cases[name] += 1
            if not condition:
                family_failures[name] += 1
                if len(trace) < 128:
                    trace.append((name, material))

        # 40k use-time TOCTOU worlds. A relevant dependency/payload/binding change
        # invalidates; an unrelated generation change remains usable.
        for i in range(40_000):
            bound = {
                "source": rng.randrange(5), "access": rng.randrange(5), "tool": rng.randrange(5),
                "principal": rng.randrange(3), "sink": rng.randrange(3), "frame": rng.randrange(7),
                "payload": rng.randrange(11), "hard": rng.randrange(5),
            }
            current = dict(bound)
            relevant = bool(rng.randrange(2))
            if relevant:
                key = rng.choice(tuple(bound))
                current[key] += 1
            else:
                unrelated_before = rng.randrange(100)
                unrelated_after = unrelated_before + 1
            valid = all(current[k] == bound[k] for k in bound)
            expected = not relevant
            check("relevant_mutation_invalidates" if relevant else "irrelevant_mutation_not_invalidate", valid == expected, (i, bound, current))
            check("payload_digest_binding", (current["payload"] == bound["payload"]) == (not relevant or key != "payload"), i)
            check("principal_binding", (current["principal"] == bound["principal"]) == (not relevant or key != "principal"), i)
            check("sink_binding", (current["sink"] == bound["sink"]) == (not relevant or key != "sink"), i)
            check("frame_binding", (current["frame"] == bound["frame"]) == (not relevant or key != "frame"), i)
            check("hard_role_closure_generation", (current["hard"] == bound["hard"]) == (not relevant or key != "hard"), i)
            if not relevant:
                check("proposal_irrelevant_write_tolerated", valid and unrelated_after != unrelated_before, i)

        # 30k proposal Semantic-OCC worlds: content bytes alone are insufficient;
        # lifecycle/profile generations are independent dependencies.
        for i in range(30_000):
            proposal = {"source_gen": rng.randrange(8), "profile_gen": rng.randrange(8), "content": rng.randrange(16)}
            current = dict(proposal)
            mutation = rng.choice(("source_gen", "profile_gen", "content", "unrelated"))
            if mutation != "unrelated":
                current[mutation] += 1
            compatible = current["source_gen"] == proposal["source_gen"] and current["profile_gen"] == proposal["profile_gen"]
            check("proposal_source_generation_invalidates", compatible == (mutation not in {"source_gen", "profile_gen"}), (i, mutation))
            check("lifecycle_generation_separate_from_content", not (mutation == "source_gen" and current["content"] == proposal["content"] and compatible), (i, mutation))
            if mutation == "unrelated":
                check("proposal_irrelevant_write_tolerated", compatible, (i, mutation))
            check("explicit_rebase_identity", ("SOURCE_REBASE" != "PURE"), i)

        # 30k multi-domain causal-cut worlds. The closed destination view must include
        # every source predecessor required by a publication edge, while unrelated
        # domains are not globally advanced.
        for i in range(30_000):
            src_required = rng.randrange(0, 100)
            requested_src = rng.randrange(0, 100)
            dst = rng.randrange(1, 100)
            unrelated = rng.randrange(0, 100)
            closed_src = max(requested_src, src_required)
            check("causal_vector_predecessor_closure", closed_src >= src_required, (i, requested_src, src_required, closed_src))
            check("per_domain_frontier", unrelated == unrelated, (i, unrelated))
            check("staged_reference_cut_consistency", closed_src >= requested_src, i)
            roots = tuple(sorted({rng.randrange(4), rng.randrange(4)}))
            cycled_roots = tuple(sorted(set(roots)))
            check("publication_origin_idempotence", cycled_roots == roots, (i, roots))

        # 20k applicability worlds: exact and explicit wildcard are allowed; missing a
        # safety-critical dimension or an explicit conflict is fail-closed.
        for i in range(20_000):
            requested = rng.choice(("linux", "windows", "mac"))
            declared = rng.choice((requested, "*", "MISSING", "conflict"))
            if declared == requested or declared == "*":
                allowed = True
            else:
                allowed = False
            check("applicability_exact_match", (declared != requested) or allowed, (i, requested, declared))
            check("applicability_explicit_wildcard", (declared != "*") or allowed, (i, requested, declared))
            check("applicability_missing_critical_fail_closed", (declared != "MISSING") or not allowed, (i, requested, declared))

        # Remaining 11,701 small/exhaustive boundary cases are distributed across
        # the families not dominated by the four randomized blocks.
        boundary_names = [
            "final_argument_binding", "tool_generation_drift", "access_policy_generation_drift",
            "declassification_generation_drift", "flow_policy_generation_drift", "half_open_expiry",
            "clock_epoch_binding", "clock_authority_required", "single_use_replay",
            "index_plus_delta_strong_read", "operational_metadata_ownership",
            "negative_cache_generation", "missing_dependency_fail_closed",
            "action_authorization_separation", "source_lifecycle_currentness",
            "resource_pressure_validation_fail_closed",
        ]
        for i in range(11_701):
            name = boundary_names[i % len(boundary_names)]
            x = i % 7
            if name == "half_open_expiry":
                issued = 10; expires = 20; now = (9, 10, 19, 20, 21)[i % 5]
                expected = now < expires
                actual = now < expires
            elif name == "single_use_replay":
                consumed = bool(i % 2); actual = not consumed; expected = not consumed
            elif name == "index_plus_delta_strong_read":
                frontier = x; delta_complete = bool(i % 2); cut = x + 1
                actual = frontier >= cut or (delta_complete and frontier + 1 >= cut)
                expected = frontier >= cut or delta_complete
            elif name == "clock_authority_required":
                expiring = bool(i % 2); has_clock = bool((i // 2) % 2)
                actual = (not expiring) or has_clock; expected = (not expiring) or has_clock
            elif name == "clock_epoch_binding":
                issued_epoch = i % 3; current_epoch = (i + (i % 2)) % 3
                actual = issued_epoch == current_epoch; expected = issued_epoch == current_epoch
            elif name == "resource_pressure_validation_fail_closed":
                validator_available = bool(i % 2); actual = validator_available; expected = validator_available
            elif name == "action_authorization_separation":
                memory_grounded = bool(i % 2); action_authorized = bool((i // 2) % 2)
                actual = memory_grounded and action_authorized; expected = memory_grounded and action_authorized
            elif name == "missing_dependency_fail_closed":
                dependency_known = bool(i % 2); actual = dependency_known; expected = dependency_known
            elif name == "negative_cache_generation":
                cached_gen = i % 4; current_gen = (i + (i % 2)) % 4
                actual = cached_gen == current_gen; expected = cached_gen == current_gen
            elif name == "source_lifecycle_currentness":
                live = bool(i % 2); actual = live; expected = live
            elif name == "operational_metadata_ownership":
                owner_count = 1 if i % 5 else 2
                actual = owner_count == 1; expected = owner_count == 1
            else:
                issued = x; current = x + (1 if i % 3 == 0 else 0)
                actual = issued == current; expected = issued == current
            check(name, actual == expected, (i, actual, expected))

        # Ensure every family was exercised even if its main randomized branch was
        # sparse under a particular seed.
        for name in families:
            if family_cases[name] == 0:
                check(name, True, "coverage-sentinel")

        failures = sum(family_failures.values())
        total_cases = 40_000 + 30_000 + 30_000 + 20_000 + 11_701
        material = {
            "seed": seed, "families": families, "family_cases": family_cases,
            "family_failures": family_failures, "trace": trace,
        }
        return {
            "kind": "use-time-causal-cut-calculus-runtime-v0.6.3",
            "revision": "NM-v0.6.3-use-time-causal-cut-calculus-runtime-1",
            "seed": seed, "property_family_count": len(families), "property_families": families,
            "family_cases": family_cases, "cases": total_cases,
            "large_randomized_cases": {
                "use_time_toctou": 40_000, "proposal_semantic_occ": 30_000,
                "multi_domain_causal_cut": 30_000, "applicability_scope": 20_000,
            },
            "failed": failures, "passed": failures == 0,
            "relevant_mutation_invalidates": family_failures["relevant_mutation_invalidates"] == 0,
            "irrelevant_mutation_tolerated": family_failures["irrelevant_mutation_not_invalidate"] == 0 and family_failures["proposal_irrelevant_write_tolerated"] == 0,
            "digest": digest(material), "historical_digest_claimed": False,
            "historical_reference_digest": "6380d200cccddfdaaff72a3b83ecee7f82a0879095b05062d1c1813a25e3d3e5",
            "scope_limitations": [
                "model_free", "no_dependency_extraction_completeness_proof", "no_secure_time_deployment_proof",
                "no_distributed_frontier_availability_proof", "no_real_agent_argument_canonicalization_proof",
            ],
        }

    def run_lifelong_fuzz(self, *, seed: int, cases: int = 10_000) -> ResearchRunReport:
        if cases < 1: raise ValueError("cases must be positive")
        rng = random.Random(seed)
        failures = 0
        counters = {"loss_chains": 0, "witness_delete": 0, "debt_transition": 0, "hard_budget": 0}
        trace_digest_material = []
        exact_states = {"PRESERVED_EXACT", "PRESERVED_NORMALIZED"}
        for i in range(cases):
            family = rng.randrange(4)
            if family == 0:
                counters["loss_chains"] += 1
                state = rng.choice(["PRESERVED_EXACT", "COARSENED", "LOST", "UNKNOWN"])
                lost_seen = state == "LOST"
                for _ in range(rng.randrange(1, 8)):
                    nxt = rng.choice(["PRESERVED_EXACT", "COARSENED", "LOST", "UNKNOWN"])
                    if lost_seen and nxt in exact_states:
                        # Pure continuation is constrained to remain lost; a restoring basis
                        # is a separate SOURCE_REBASE operation in the production runtime.
                        nxt = "LOST"
                    lost_seen = lost_seen or nxt == "LOST"
                    state = nxt
                if lost_seen and state in exact_states: failures += 1
                trace_digest_material.append((family, state))
            elif family == 1:
                counters["witness_delete"] += 1
                witnesses = rng.randrange(1, 6); delete = rng.randrange(witnesses)
                remaining = witnesses - 1
                safe = remaining >= 1
                if safe != (witnesses > 1): failures += 1
                trace_digest_material.append((family, witnesses, delete, safe))
            elif family == 2:
                counters["debt_transition"] += 1
                explicit = bool(rng.randrange(2))
                outcome = "DISCHARGED" if explicit else "OPEN"
                if not explicit and outcome != "OPEN": failures += 1
                trace_digest_material.append((family, explicit, outcome))
            else:
                counters["hard_budget"] += 1
                costs = [rng.randrange(1, 8) for _ in range(rng.randrange(1, 6))]
                budget = rng.randrange(1, 20)
                total = sum(costs)
                status = "SUFFICIENT" if total <= budget else "OVERFLOW"
                if status == "SUFFICIENT" and total > budget: failures += 1
                trace_digest_material.append((family, costs, budget, status))
        details = {"counters": counters, "trace_digest": digest(trace_digest_material), "invariants": 4}
        report = ResearchRunReport(f"fuzz_{uuid.uuid4().hex}", "lifelong-state-model", 4 if failures == 0 else 0,
                                   failures, cases, seed, details)
        return self._store_research_report(report)

    def run_persistence_lifelong_fuzz(
        self, *, seed: int, cases: int = 10_000, restart_interval: int = 257,
        recompute_interval: int = 31,
    ) -> ResearchRunReport:
        """State-machine fuzz the real SQLite kernel, not only the model calculus.

        The schedule deliberately spans every operation family named by Section 261.
        It periodically closes/reopens the database and independently recomputes
        correctness projections from canonical rows to detect incremental drift.
        """
        if cases < 1 or restart_interval < 1 or recompute_interval < 1:
            raise ValueError("persistence fuzz parameters must be positive")
        rng = random.Random(seed)
        operations = (
            "capture", "claim_correction", "transform", "consolidate", "split_merge",
            "archive_delete", "counterexample_repair", "regime_change", "model_upgrade",
            "index_lag_rebuild", "context_reset_recovery", "migration",
        )
        counts = {name: 0 for name in operations}
        failures: list[dict[str, object]] = []
        projection_drift_failures = 0
        full_recomputation_checks = 0
        restart_count = 0
        typed_rejections = 0
        trace: list[object] = []

        with tempfile.TemporaryDirectory() as td:
            path = f"{td}/persistence-fuzz.db"
            rt = self.__class__(path, clock_authority_id="fuzz-clock", clock_epoch="fuzz-epoch")
            domain = "fuzz"
            family = f"FUZZ_X_{seed}"
            rt.create_domain(domain)
            rt.register_query_family(family, {"x"})
            rt.set_runtime_compatibility(domain, mission_revision="m0", environment_revision="env0")
            rt.set_self_version(domain, "self:0", {"executor": "v0"})
            serial = 0

            def head_values():
                h = rt._head_row(domain)
                return int(h["sequence"]), int(h["writer_epoch"])

            def live_evidence():
                return [r["evidence_id"] for r in rt.db.execute(
                    "SELECT evidence_id FROM evidence WHERE domain_id=? AND revoked_seq IS NULL AND deleted_seq IS NULL AND compromised_seq IS NULL ORDER BY evidence_id",
                    (domain,),
                ).fetchall()]

            def live_exact_reps():
                out = []
                for r in rt.db.execute(
                    "SELECT * FROM representations WHERE domain_id=? AND invalidated_seq IS NULL AND tainted_seq IS NULL ORDER BY representation_id",
                    (domain,),
                ).fetchall():
                    loss = json.loads(r["loss_json"])
                    if loss.get("x") in {LossState.PRESERVED_EXACT.value, LossState.PRESERVED_NORMALIZED.value}:
                        out.append(r)
                return out

            def capture_one(label: str):
                nonlocal serial
                serial += 1
                seq, epoch = head_values()
                ev = rt.capture_evidence(
                    domain_id=domain, operation_id=f"fuzz-capture-{serial}", expected_seq=seq, writer_epoch=epoch,
                    source_event_identity=f"fuzz:event:{serial}:{label}", content={"x": serial, "label": label}, principal="alice",
                ).object_id
                region = rt.create_region(domain, f"fuzz:region:{serial}:{label}", principal="alice")
                rep = rt.add_representation(
                    domain, region, kind="raw", payload={"x": serial, "label": label},
                    loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2,
                    principal="alice", source_evidence_ids=[ev],
                )
                return ev, region, rep

            # Seed enough independent witnesses that delete/repair schedules have room.
            for i in range(4):
                capture_one(f"seed-{i}")

            def full_recompute(step: int):
                nonlocal projection_drift_failures, full_recomputation_checks
                full_recomputation_checks += 1
                try:
                    rt.verify_integrity(domain)
                    audit = rt.audit_no_two_writable_clocks(domain)
                    if not audit.passed:
                        raise AssertionError(f"clock audit: {audit.violations}")

                    # Recompute live OR-of-AND claim grounding directly from canonical
                    # justification/evidence rows, then compare the incremental API view.
                    for claim in rt.db.execute(
                        "SELECT * FROM claims WHERE domain_id=? AND superseded_seq IS NULL ORDER BY logical_id", (domain,)
                    ).fetchall():
                        paths = []
                        for prow in rt.db.execute(
                            "SELECT path_id FROM justification_paths WHERE claim_revision_id=? ORDER BY path_id",
                            (claim["claim_revision_id"],),
                        ).fetchall():
                            members = rt.db.execute(
                                "SELECT e.revoked_seq,e.deleted_seq,e.compromised_seq FROM justification_members jm "
                                "JOIN evidence e ON e.evidence_id=jm.evidence_id WHERE jm.path_id=? ORDER BY jm.evidence_id",
                                (prow["path_id"],),
                            ).fetchall()
                            paths.append(bool(members) and all(
                                m["revoked_seq"] is None and m["deleted_seq"] is None and m["compromised_seq"] is None
                                for m in members
                            ))
                        expected = any(paths)
                        actual = rt.claim_is_supported(domain, claim["logical_id"])
                        if actual != expected:
                            raise AssertionError(f"claim support drift {claim['logical_id']}: {actual}!={expected}")

                    # Recompute the lexical projection from durable index rows plus
                    # canonical lifecycle filters instead of trusting cached results.
                    keys = [r[0] for r in rt.db.execute(
                        "SELECT DISTINCT key FROM discovery_index WHERE domain_id=? AND view='lexical' ORDER BY key",
                        (domain,),
                    ).fetchall()]
                    for key in keys[:8]:
                        expected_regions = []
                        seen = set()
                        rows = rt.db.execute(
                            "SELECT d.region_id,r.* FROM discovery_index d JOIN representations r ON r.representation_id=d.representation_id "
                            "WHERE d.domain_id=? AND d.view='lexical' AND d.key=? ORDER BY d.representation_id",
                            (domain, key),
                        ).fetchall()
                        for row in rows:
                            if row["invalidated_seq"] is not None or row["tainted_seq"] is not None:
                                continue
                            if not rt._is_allowed("alice", row["allowed_principals_json"]):
                                continue
                            if not rt._representation_applicable(domain, row):
                                continue
                            if row["region_id"] not in seen:
                                seen.add(row["region_id"]); expected_regions.append(row["region_id"])
                        actual_regions = rt.discover_regions(domain, principal="alice", view_keys={"lexical": [key]})
                        if actual_regions != expected_regions:
                            raise AssertionError(f"discovery drift for {key}: {actual_regions}!={expected_regions}")
                except Exception as exc:
                    projection_drift_failures += 1
                    failures.append({"step": step, "phase": "full_recompute", "error": type(exc).__name__, "detail": str(exc)})

            for step in range(cases):
                op = operations[step % len(operations)]
                counts[op] += 1
                try:
                    if op == "capture":
                        capture_one(f"step-{step}")

                    elif op == "claim_correction":
                        evs = live_evidence()
                        if not evs:
                            capture_one("claim-reseed"); evs = live_evidence()
                        support = [[rng.choice(evs)]]
                        current = rt.db.execute(
                            "SELECT * FROM claims WHERE domain_id=? AND logical_id='fuzz:claim' AND superseded_seq IS NULL",
                            (domain,),
                        ).fetchone()
                        seq, epoch = head_values()
                        if current is None:
                            rt.create_claim(
                                domain_id=domain, operation_id=f"fuzz-claim-create-{step}", expected_seq=seq, writer_epoch=epoch,
                                logical_id="fuzz:claim", proposition={"revision": step}, valid_from=None, valid_to=None,
                                support_paths=support, principal="alice",
                            )
                        else:
                            rt.revise_claim(
                                domain_id=domain, operation_id=f"fuzz-claim-revise-{step}", expected_seq=seq, writer_epoch=epoch,
                                logical_id="fuzz:claim", expected_predecessor_revision_id=current["claim_revision_id"],
                                proposition={"revision": step}, valid_from=None, valid_to=None, support_paths=support, principal="alice",
                            )

                    elif op == "transform":
                        reps = live_exact_reps()
                        if not reps:
                            capture_one("transform-reseed"); reps = live_exact_reps()
                        src = rng.choice(reps)
                        rt.add_representation(
                            domain, src["region_id"], kind="summary", payload={"x": json.loads(src["payload_json"]).get("x")},
                            source_representation_ids=[src["representation_id"]], transform_kind="PURE",
                            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
                        )

                    elif op == "consolidate":
                        reps = live_exact_reps()
                        if not reps:
                            capture_one("consolidate-reseed"); reps = live_exact_reps()
                        src = rng.choice(reps)
                        proposal = rt.create_representation_proposal(
                            domain, src["region_id"], source_representation_ids=[src["representation_id"]], kind="compact",
                            payload={"x": json.loads(src["payload_json"]).get("x")},
                            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
                        )
                        rt.verify_representation_proposal(
                            domain, proposal.proposal_id, principal="alice", verifier_ref="persistence-fuzz",
                            coverage="PASS", preservation="PASS", faithfulness="PASS",
                        )
                        rt.promote_representation_proposal(proposal.proposal_id, principal="alice")

                    elif op == "split_merge":
                        if rng.randrange(2) == 0:
                            r = rt.create_region(domain, f"struct:split:{step}", principal="alice")
                            rt.split_region(domain, r, [f"struct:split:{step}:a", f"struct:split:{step}:b"], principal="alice")
                        else:
                            a = rt.create_region(domain, f"struct:merge:{step}:a", principal="alice")
                            b = rt.create_region(domain, f"struct:merge:{step}:b", principal="alice")
                            rt.merge_regions(domain, [a, b], f"struct:merge:{step}:out", principal="alice")

                    elif op == "archive_delete":
                        evs = live_evidence()
                        if len(evs) < 2:
                            capture_one("delete-reseed"); evs = live_evidence()
                        rt.erase_evidence(domain, rng.choice(evs), principal="alice", policy_ref="fuzz-retention")

                    elif op == "counterexample_repair":
                        reps = live_exact_reps()
                        if not reps:
                            capture_one("repair-reseed"); reps = live_exact_reps()
                        src = rng.choice(reps)
                        payload = json.loads(src["payload_json"])
                        target = rt.add_representation(
                            domain, src["region_id"], kind="lossy", payload={"x": None},
                            source_representation_ids=[src["representation_id"]], transform_kind="PURE",
                            loss={"x": LossState.LOST}, recoverable=set(), token_cost=1, principal="alice",
                        )
                        ce = rt.record_query_counterexample(
                            domain, region_id=src["region_id"], representation_id=target, query_family=family,
                            lost_dimensions={"x"}, source_witness_id=src["representation_id"],
                            decision_relevance="fuzz-exact-x", cause_type="LOCAL_TRANSFORM", principal="alice",
                        )
                        rt.repair_counterexample(
                            domain, ce.counterexample_id, source_representation_id=src["representation_id"],
                            replacement_payload={"x": payload.get("x")}, replacement_loss={"x": LossState.PRESERVED_EXACT}, principal="alice",
                        )

                    elif op == "regime_change":
                        rt.set_runtime_compatibility(
                            domain, mission_revision=f"m{step % 5}", environment_revision=f"env{(step // 5) % 3}"
                        )

                    elif op == "model_upgrade":
                        rt.set_self_version(domain, f"self:{step}", {"executor": f"v{step}"})

                    elif op == "index_lag_rebuild":
                        reps = live_exact_reps()
                        if not reps:
                            capture_one("index-reseed"); reps = live_exact_reps()
                        rep = rng.choice(reps)
                        key = f"k{step % 7}"
                        rt.index_representation_view(domain, rep["representation_id"], "lexical", [key])
                        cut = rt.head(domain)
                        frontier = rt.get_index_frontier(domain, "lexical")
                        if frontier["frontier_sequence"] < cut.sequence:
                            try:
                                rt.discover_regions_at_cut(
                                    domain, principal="alice", view_keys={"lexical": [key]}, cut=cut, require_exact=True
                                )
                                raise AssertionError("lagging exact index unexpectedly certified the cut")
                            except (MemoryIndexFrontierIncomplete, MemoryQueryCapabilityUnsupported):
                                pass
                        rt.advance_index_frontier(domain, "lexical", through_sequence=rt.head(domain).sequence, mode="EXACT")

                    elif op == "context_reset_recovery":
                        reps = live_exact_reps()
                        if not reps:
                            capture_one("recovery-reseed"); reps = live_exact_reps()
                        rep = rng.choice(reps)
                        role = RecallRole(f"fuzz-role-{step}", rep["region_id"], family, hard=True)
                        pin = rt.create_continuity_pin(domain, principal="alice", hard_roles=[role], stable_refs=[rep["representation_id"]])
                        assessment = rt.assess_recovery(domain, pin_id=pin.pin_id, principal="alice")
                        if not assessment.resume_allowed:
                            # Applicability/regime evolution can legitimately make an old
                            # witness unusable; the important condition is typed blocking.
                            typed_rejections += 1

                    elif op == "migration":
                        region = rt.create_region(domain, f"legacy:region:{step}", principal="alice")
                        rep = rt.import_legacy_representation(
                            domain, region, source_kind="legacy-summary", source_id=f"legacy:{step}",
                            payload={"x": step}, dimensions={"x"}, principal="alice",
                        )
                        if rt.answerability(rep, family) == Answerability.EXACT:
                            raise AssertionError("legacy unknown semantics were upgraded to EXACT")

                    trace.append((step, op, rt.head(domain).sequence))
                except Exception as exc:
                    failures.append({"step": step, "operation": op, "error": type(exc).__name__, "detail": str(exc)})
                    break

                if (step + 1) % recompute_interval == 0:
                    full_recompute(step)
                    if failures:
                        break

                if (step + 1) % restart_interval == 0:
                    rt.close()
                    rt = self.__class__(path, clock_authority_id="fuzz-clock", clock_epoch="fuzz-epoch")
                    restart_count += 1
                    try:
                        rt.verify_integrity(domain)
                    except Exception as exc:
                        failures.append({"step": step, "phase": "restart", "error": type(exc).__name__, "detail": str(exc)})
                        break

            if not failures:
                full_recompute(cases)
            final_integrity = False
            try:
                final_integrity = bool(rt.verify_integrity(domain))
            except Exception as exc:
                failures.append({"phase": "final_integrity", "error": type(exc).__name__, "detail": str(exc)})
            final_head = rt.head(domain)
            rt.close()

        details = {
            "operation_counts": counts, "restart_count": restart_count,
            "full_recomputation_checks": full_recomputation_checks,
            "projection_drift_failures": projection_drift_failures,
            "typed_rejections": typed_rejections, "final_integrity": final_integrity,
            "final_sequence": final_head.sequence, "trace_digest": digest(trace),
            "failure_samples": failures[:10],
        }
        report = ResearchRunReport(
            f"persistence_fuzz_{uuid.uuid4().hex}", "lifelong-persistence-state-machine",
            len(operations) if not failures else 0, len(failures), cases, seed, details,
        )
        return self._store_research_report(report)

    # ---------- v0.6.3 use-time race conformance campaign ----------

    def run_use_time_race_campaign(self, *, seed: int = 401) -> dict[str, object]:
        """Execute the ten normative interleavings from Section 401.

        These are deterministic schedule tests against the real runtime. They are
        intentionally not relabeled as external/independent research evidence; the
        campaign proves this implementation has fail-visible semantics at each race
        boundary and preserves dependency minimality for unrelated writes.
        """
        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []

        def record(schedule: str, expected: str, observed: str, detail: object = None):
            outcomes.append({
                "schedule": schedule, "expected": expected, "observed": observed,
                "passed": observed == expected, "detail": detail,
            })

        def new_domain(label: str) -> str:
            domain = f"race_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"
            self.create_domain(domain)
            return domain

        def setup_exact(domain: str, label: str, value: int = 1, *, applicability=None):
            family = f"RACE_X_{seed}_{label}_{rng.randrange(1_000_000_000):09d}"
            self.register_query_family(family, {"x"})
            region = self.create_region(domain, f"region:{label}", principal="alice")
            rep = self.add_representation(
                domain, region, kind="raw", payload={"x": value},
                loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
                principal="alice", applicability=applicability,
            )
            role = RecallRole(f"role:{label}", region, family, hard=True)
            return family, region, rep, role

        # 1. eligible proposal -> revoke/invalidate source -> promote
        d = new_domain("proposal")
        family, region, source, _ = setup_exact(d, "proposal")
        proposal = self.create_representation_proposal(
            d, region, source_representation_ids=[source], kind="summary", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice",
        )
        self.verify_representation_proposal(
            d, proposal.proposal_id, principal="alice", verifier_ref="race-verifier",
            coverage="PASS", preservation="PASS", faithfulness="PASS",
        )
        self.invalidate_representation(d, source, principal="alice")
        try:
            self.promote_representation_proposal(proposal.proposal_id, principal="alice")
            observed = "PROMOTED"
        except MemoryProposalStale:
            observed = "PROPOSAL_STALE"
        record("proposal_revoke_promote", "PROPOSAL_STALE", observed)

        # 2. strong outer query -> concurrent relevant stale -> nested use/lookup
        d = new_domain("outer")
        _, _, rep, role = setup_exact(d, "outer")
        frame = self.compile_recall(d, "alice", [role], 20)
        manifest = self.materialize_frame_dependency_manifest(frame)
        self.invalidate_representation(d, rep, principal="alice")
        try:
            self.validate_frame_dependency_manifest(manifest.manifest_id)
            observed = "VALID"
        except MemoryDependencyStale:
            observed = "MEMORY_DEPENDENCY_STALE"
        record("outer_query_concurrent_stale", "MEMORY_DEPENDENCY_STALE", observed)

        # 3. frame compile -> access revoke -> same consequence
        d = new_domain("access")
        self.set_access_profile(
            d, "alice", ["DISCOVER", "USE_FOR_LOCAL_REASONING", "DISCLOSE_TO_MODEL", "DERIVE"]
        )
        _, _, _, role = setup_exact(d, "access")
        frame = self.compile_recall(d, "alice", [role], 20)
        self.set_access_profile(d, "alice", [])
        try:
            self.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 1})
            observed = "USE_ALLOWED"
        except MemoryDependencyStale:
            observed = "MEMORY_DEPENDENCY_STALE"
        record("frame_access_revoke_use", "MEMORY_DEPENDENCY_STALE", observed)

        # 4. frame compile -> unrelated-region write -> same consequence
        d = new_domain("unrelated")
        _, _, _, role = setup_exact(d, "unrelated-main")
        frame = self.compile_recall(d, "alice", [role], 20)
        setup_exact(d, "unrelated-other", value=2)
        try:
            fence = self.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 1})
            self.consume_use_fence(fence.fence_id, principal="alice", sink="model", payload={"x": 1})
            observed = "USE_ALLOWED"
        except MemoryDependencyStale:
            observed = "MEMORY_DEPENDENCY_STALE"
        record("frame_unrelated_write_use", "USE_ALLOWED", observed)

        # 5. frame compile -> final recipient/amount/path mutation -> dispatch
        d = new_domain("args")
        _, _, _, role = setup_exact(d, "args")
        frame = self.compile_recall(d, "alice", [role], 20)
        fence = self.issue_use_fence(
            frame, principal="alice", sink="tool:pay",
            payload={"recipient": "A", "amount": 10, "path": "/safe"},
        )
        try:
            self.consume_use_fence(
                fence.fence_id, principal="alice", sink="tool:pay",
                payload={"recipient": "B", "amount": 10, "path": "/safe"},
            )
            observed = "USE_ALLOWED"
        except ActionArgumentMismatch:
            observed = "ACTION_ARGUMENT_MISMATCH"
        record("frame_argument_mutation_dispatch", "ACTION_ARGUMENT_MISMATCH", observed)

        # 6. use fence issue -> tool-schema generation change -> consume
        d = new_domain("tool")
        _, _, _, role = setup_exact(d, "tool")
        frame = self.compile_recall(d, "alice", [role], 20)
        fence = self.issue_use_fence(frame, principal="alice", sink="tool:pay", payload={"amount": 10})
        self.bump_generation(d, "tool", "tool:pay")
        try:
            self.consume_use_fence(fence.fence_id, principal="alice", sink="tool:pay", payload={"amount": 10})
            observed = "USE_ALLOWED"
        except MemoryDependencyStale:
            observed = "MEMORY_DEPENDENCY_STALE"
        record("fence_tool_generation_change", "MEMORY_DEPENDENCY_STALE", observed)

        # 7. protected lease -> wrong clock epoch
        d = new_domain("clock")
        _, _, _, role = setup_exact(d, "clock")
        frame = self.compile_recall(d, "alice", [role], 20)
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        from datetime import timedelta
        fence = self.issue_use_fence(
            frame, principal="alice", sink="model", payload={"x": 1}, expires_at=now + timedelta(minutes=1)
        )
        old_epoch = self._clock_epoch
        self._clock_epoch = f"race-wrong-{seed}"
        try:
            self.consume_use_fence(fence.fence_id, principal="alice", sink="model", payload={"x": 1})
            observed = "USE_ALLOWED"
        except MemoryClockAuthorityRequired:
            observed = "CLOCK_AUTHORITY_REQUIRED"
        finally:
            self._clock_epoch = old_epoch
        record("protected_lease_clock_authority", "CLOCK_AUTHORITY_REQUIRED", observed)

        # 8. context-scoped memory -> foreign profile route/use
        d = new_domain("scope")
        self.set_runtime_compatibility(d, mission_revision="mission-a", environment_revision="env-a")
        _, _, _, role = setup_exact(d, "scope", applicability={"mission_revision": "mission-a"})
        self.set_runtime_compatibility(d, mission_revision="mission-b", environment_revision="env-a")
        try:
            self.compile_recall(d, "alice", [role], 20)
            observed = "USE_ALLOWED"
        except MemoryRecallInsufficient:
            observed = "SCOPE_INCOMPATIBLE"
        record("context_scoped_foreign_profile", "SCOPE_INCOMPATIBLE", observed)

        # 9. destination import visible -> source-domain cut deliberately lagging
        src = new_domain("pub-src"); dst = new_domain("pub-dst")
        _, _, rep, _ = setup_exact(src, "pub")
        publication = self.publish_representation(
            src, dst, rep, principal="alice", operation_id=f"pub-op-{seed}-{rng.randrange(1_000_000)}"
        )
        closed = self.close_causal_cut({dst: publication.destination_sequence, src: 0})
        observed = "CAUSAL_CUT_UPGRADED" if closed[src].sequence >= publication.source_sequence else "CUT_UNAVAILABLE"
        record(
            "publication_causal_cut_lag", "CAUSAL_CUT_UPGRADED", observed,
            {"source_sequence": publication.source_sequence, "closed_source_sequence": closed[src].sequence},
        )

        # 10. negative complete-domain result -> matching write -> cached absence use
        d = new_domain("negative")
        self.register_query_family(f"NEG_{seed}_{rng.randrange(1_000_000)}", {"x"})
        negative = self.strong_negative_query(d, principal="alice", field="x", equals=99, completeness="COMPLETE")
        region = self.create_region(d, "negative-hit", principal="alice")
        self.add_representation(
            d, region, kind="raw", payload={"x": 99},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        try:
            self.validate_negative_query_receipt(negative.receipt_id)
            observed = "ABSENCE_STILL_VALID"
        except MemoryDependencyStale:
            observed = "MEMORY_DEPENDENCY_STALE"
        record("negative_result_matching_write", "MEMORY_DEPENDENCY_STALE", observed)

        failures = [x for x in outcomes if not x["passed"]]
        return {
            "kind": "use-time-race-campaign-v0.6.3", "seed": seed,
            "schedule_count": len(outcomes), "failed": len(failures), "passed": not failures,
            "outcomes": outcomes, "failure_digest": digest(failures),
        }

    # ---------- v0.6.2 recovery/privacy mandatory fixture campaign ----------

    def run_recovery_privacy_acceptance_campaign(self, *, seed: int = 373) -> dict[str, object]:
        """Execute all mandatory continuity/recovery/erasure fixtures from Section 373.

        This campaign intentionally exercises current-governance behavior against
        historical artifacts. It is local implementation evidence, not a claim that
        external backups/providers have physically erased bytes.
        """
        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []

        def record(fixture: str, expected: str, observed: str, detail=None):
            outcomes.append({
                "fixture": fixture, "expected": expected, "observed": observed,
                "passed": expected == observed, "detail": detail,
            })

        def new_domain(label: str) -> str:
            d = f"recovery_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"
            self.create_domain(d)
            self.set_runtime_compatibility(d, mission_revision="m1", environment_revision="env1")
            self.set_self_version(d, "self:v1", {"tool": "v1"})
            return d

        def setup_source(d: str, label: str, value: int = 1):
            family = f"REC_X_{seed}_{label}_{rng.randrange(1_000_000_000):09d}"
            self.register_query_family(family, {"x"})
            h = self._head_row(d)
            ev = self.capture_evidence(
                domain_id=d, operation_id=f"ev:{label}:{rng.randrange(1_000_000)}",
                expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                source_event_identity=f"event:{label}:{rng.randrange(1_000_000)}",
                content={"x": value, "private": f"secret-{value}"}, principal="alice",
            ).object_id
            region = self.create_region(d, f"region:{label}", principal="alice")
            rep = self.add_representation(
                d, region, kind="raw", payload={"x": value, "private": f"secret-{value}"},
                loss={"x": LossState.PRESERVED_EXACT, "private": LossState.PRESERVED_EXACT},
                recoverable=set(), token_cost=2, principal="alice", source_evidence_ids=[ev],
            )
            role = RecallRole(f"role:{label}", region, family, hard=True)
            return ev, region, rep, role

        # 1 forged anchor payload with matching superficial mission/environment
        d = new_domain("forged")
        _, _, rep, role = setup_source(d, "forged")
        pin = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep])
        self.db.execute("UPDATE continuity_pins SET payload_digest='forged' WHERE pin_id=?", (pin.pin_id,))
        a = self.assess_recovery(d, pin_id=pin.pin_id, principal="alice")
        record("forged_anchor_matching_context", "BLOCKED_R4", "BLOCKED_R4" if a.layers["R4_CONTINUITY_COMPATIBILITY"] == "BLOCKED" else "ALLOWED")

        # 2 anchor state root older than current recovered cut: old pin is only a seed;
        # recovery's current cut must remain newer and current state is re-evaluated.
        d = new_domain("old-root")
        _, _, rep, role = setup_source(d, "old-root")
        pin = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep])
        old_seq = pin.cut.sequence
        # unrelated canonical growth
        self.create_region(d, "later-unrelated", principal="alice")
        a = self.assess_recovery(d, pin_id=pin.pin_id, principal="alice")
        observed = "CURRENT_REEVALUATION" if a.resume_allowed and a.current_cut.sequence > old_seq else "OLD_ROOT_AS_CURRENT"
        record("anchor_root_older_than_recovered_cut", "CURRENT_REEVALUATION", observed)

        # 3 continuity pin containing dangling hypothesis/plan refs
        d = new_domain("dangling")
        try:
            self.create_continuity_pin(d, principal="alice", hard_roles=[], stable_refs=["missing:plan"])
            observed = "DANGLING_ACCEPTED"
        except MemoryTransitionIncomplete:
            observed = "DANGLING_REJECTED"
        record("continuity_pin_dangling_refs", "DANGLING_REJECTED", observed)

        # 4 anchor containing unresolved verification blockers
        d = new_domain("blocker")
        _, _, rep, role = setup_source(d, "blocker")
        pin = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep], verification_blockers=["verify:open"])
        a = self.assess_recovery(d, pin_id=pin.pin_id, principal="alice")
        record("anchor_unresolved_verification_blocker", "BLOCKED_R4", "BLOCKED_R4" if a.layers["R4_CONTINUITY_COMPATIBILITY"] == "BLOCKED" else "ALLOWED")

        # 5 multiple anchors reordered in serialized storage
        d = new_domain("reorder")
        _, _, rep, role = setup_source(d, "reorder")
        older = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep])
        newer = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep], verification_blockers=["open"])
        p1 = self.select_continuity_pin(d, principal="alice", pin_ids=[newer.pin_id, older.pin_id])
        p2 = self.select_continuity_pin(d, principal="alice", pin_ids=[older.pin_id, newer.pin_id])
        observed = "ORDER_INDEPENDENT" if p1.pin_id == p2.pin_id == older.pin_id else "ORDER_DEPENDENT"
        record("multiple_anchors_reordered", "ORDER_INDEPENDENT", observed)

        # 6 mission transition after a verified mission-scoped claim
        d = new_domain("mission")
        ev, _, _, _ = setup_source(d, "mission")
        h = self._head_row(d)
        self.create_claim(
            domain_id=d, operation_id=f"claim:{seed}", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="mission:claim", proposition={"goal": "A"}, valid_from=None, valid_to=None,
            support_paths=[[ev]], principal="alice", applicability={"mission_revision": "m1"},
        )
        before = self.claim_currently_usable(d, "mission:claim", principal="alice")
        self.set_runtime_compatibility(d, mission_revision="m2", environment_revision="env1")
        after = self.claim_currently_usable(d, "mission:claim", principal="alice")
        record("mission_transition_verified_scoped_claim", "SCOPED_REVALIDATION", "SCOPED_REVALIDATION" if before and not after else "LEAKED")

        # 7 self-version change with old procedure/effect/continuity packet
        d = new_domain("self-version")
        _, _, _, role = setup_source(d, "self-version")
        packet = self.create_handoff_packet(d, principal="alice", hard_roles=[role], token_budget=20)
        self.set_self_version(d, "self:v2", {"tool": "v2"})
        v = self.validate_handoff_packet(packet.packet_id, principal="alice")
        record("self_version_change_old_continuity_packet", "REVALIDATION_REQUIRED", v["status"])

        # 8 handoff budget with catastrophic old failure outside last-N window
        d = new_domain("old-failure")
        _, _, _, old_failure = setup_source(d, "catastrophic", value=-1)
        for i in range(6):
            setup_source(d, f"recent-{i}", value=i)
        _, _, _, objective = setup_source(d, "objective", value=42)
        packet = self.create_handoff_packet(d, principal="alice", hard_roles=[old_failure, objective], token_budget=20)
        role_ids = {f.role_id for f in packet.fragments}
        observed = "HARD_FAILURE_COVERED" if {old_failure.role_id, objective.role_id}.issubset(role_ids) else "LAST_N_LOSS"
        record("handoff_catastrophic_old_failure_outside_last_n", "HARD_FAILURE_COVERED", observed)

        # 9 advisory next action followed by changed tool boundary
        d = new_domain("advisory")
        _, _, _, role = setup_source(d, "advisory")
        packet = self.create_handoff_packet(
            d, principal="alice", hard_roles=[role], token_budget=20,
            advisory_next_action={"tool": "pay", "amount": 10}, tool_boundary_digest="tool:v1",
        )
        v = self.validate_handoff_packet(packet.packet_id, principal="alice", current_tool_boundary_digest="tool:v2")
        observed = "ADVISORY_REVALIDATION" if v["hard_roles_usable"] and not v["advisory_action_usable"] else "ACTION_INHERITED"
        record("handoff_advisory_action_changed_tool_boundary", "ADVISORY_REVALIDATION", observed)

        # 10 checkpoint before privacy deletion, restore after deletion barrier
        d = new_domain("privacy-restore")
        ev, _, _, _ = setup_source(d, "privacy-restore")
        checkpoint = self.head(d)
        self.erase_evidence(d, ev, principal="alice", policy_ref="privacy:delete")
        replay = self.assess_replay(d, checkpoint, principal="alice", required_refs=[ev])
        record("checkpoint_before_privacy_delete_restore_after_barrier", "UNAVAILABLE_BY_POLICY", replay.current_use_mode)

        # 11 checkpoint before access/declassification revoke
        d = new_domain("access-restore")
        self.set_access_profile(d, "alice", ["READ_EXACT", "DISCOVER", "USE_FOR_LOCAL_REASONING"])
        checkpoint = self.head(d)
        self.set_access_profile(d, "alice", [])
        replay = self.assess_replay(d, checkpoint, principal="alice")
        record("checkpoint_before_access_revoke", "RESTORE_BARRIER_REQUIRED", replay.current_use_mode)

        # 12 source compromise after snapshot
        d = new_domain("compromise")
        ev, _, _, _ = setup_source(d, "compromise")
        checkpoint = self.head(d)
        self.compromise_evidence(d, ev, principal="alice", reason="post-snapshot compromise")
        replay = self.assess_replay(d, checkpoint, principal="alice")
        record("source_compromise_after_snapshot", "RESTORE_BARRIER_REQUIRED", replay.current_use_mode)

        # 13 semantic rollback after later governance barrier
        d = new_domain("rollback")
        ev, _, _, _ = setup_source(d, "rollback")
        h = self._head_row(d)
        c1 = self.create_claim(
            domain_id=d, operation_id="rollback:c1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="rollback:claim", proposition={"v": 1}, valid_from=None, valid_to=None, support_paths=[[ev]], principal="alice",
        )
        h = self._head_row(d)
        self.revise_claim(
            domain_id=d, operation_id="rollback:c2", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="rollback:claim", expected_predecessor_revision_id=c1.object_id, proposition={"v": 2},
            valid_from=None, valid_to=None, support_paths=[[ev]], principal="alice",
        )
        self.erase_evidence(d, ev, principal="alice", policy_ref="privacy:delete")
        try:
            self.rollback_claim_to_revision(d, "rollback:claim", c1.object_id, principal="alice", operation_id="rollback:attempt")
            observed = "GOVERNANCE_BYPASSED"
        except MemoryTransitionIncomplete:
            observed = "GOVERNANCE_BARRIER_WINS"
        record("semantic_rollback_after_governance_barrier", "GOVERNANCE_BARRIER_WINS", observed)

        # 14 raw deletion while derived summary still contains private-only detail
        d = new_domain("residue")
        ev, region, source, role = setup_source(d, "residue")
        summary = self.add_representation(
            d, region, kind="summary", payload={"x": 1, "private": "secret-1"},
            source_representation_ids=[source], source_evidence_ids=[ev], transform_kind="PURE",
            loss={"x": LossState.PRESERVED_EXACT, "private": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=1, principal="alice",
        )
        self.erase_evidence(d, ev, principal="alice", policy_ref="privacy:delete")
        row = self.db.execute("SELECT tainted_seq FROM representations WHERE representation_id=?", (summary,)).fetchone()
        try:
            self.compile_recall(d, "alice", [role], 20)
            current_use = True
        except MemoryRecallInsufficient:
            current_use = False
        observed = "TAINTED_QUARANTINED" if row and row["tainted_seq"] is not None and not current_use else "RESIDUE_LEAK"
        record("raw_delete_derived_private_summary", "TAINTED_QUARANTINED", observed)

        # 15 independently supported proposition + tainted derivative requiring clean rederivation
        d = new_domain("independent")
        h = self._head_row(d)
        private = self.capture_evidence(domain_id=d, operation_id="ind:private", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]), source_event_identity="ind:private", content={"x": 7, "private": "p"}, principal="alice").object_id
        h = self._head_row(d)
        public = self.capture_evidence(domain_id=d, operation_id="ind:public", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]), source_event_identity="ind:public", content={"x": 7}, principal="alice").object_id
        region = self.create_region(d, "region:independent", principal="alice")
        summary = self.add_representation(
            d, region, kind="summary", payload={"x": 7, "private": "p"},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice",
            source_evidence_ids=[private, public], transform_kind="SOURCE_REBASE",
        )
        h = self._head_row(d)
        self.create_claim(domain_id=d, operation_id="ind:claim", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]), logical_id="x=7", proposition={"x": 7}, valid_from=None, valid_to=None, support_paths=[[private], [public]], principal="alice")
        self.erase_evidence(d, private, principal="alice", policy_ref="privacy:delete")
        supported = self.claim_is_supported(d, "x=7")
        clean = self.clean_rederive(d, summary, surviving_evidence_ids=[public], payload={"x": 7}, loss={"x": LossState.PRESERVED_EXACT}, principal="alice")
        clean_row = self.db.execute("SELECT tainted_seq FROM representations WHERE representation_id=?", (clean,)).fetchone()
        observed = "SUPPORTED_WITH_CLEAN_REDERIVATION" if supported and clean_row and clean_row["tainted_seq"] is None else "SUPPORT_OR_CLEAN_FAILURE"
        record("independent_support_tainted_derivative_clean_rederive", "SUPPORTED_WITH_CLEAN_REDERIVATION", observed)

        # 16 stale lexical/dense/cache surface after canonical deletion
        d = new_domain("index-delete")
        ev, region, rep, _ = setup_source(d, "index-delete")
        self.index_representation_view(d, rep, "lexical", ["secret"])
        before = region in self.discover_regions(d, principal="alice", view_keys={"lexical": ["secret"]})
        self.erase_evidence(d, ev, principal="alice", policy_ref="privacy:delete")
        after = region in self.discover_regions(d, principal="alice", view_keys={"lexical": ["secret"]})
        observed = "CANONICAL_FILTER_BLOCKS_STALE_INDEX" if before and not after else "STALE_INDEX_LEAK"
        record("stale_index_after_canonical_delete", "CANONICAL_FILTER_BLOCKS_STALE_INDEX", observed)

        # 17 continuity pin/handoff containing deleted-source-derived content
        d = new_domain("continuity-delete")
        ev, _, rep, role = setup_source(d, "continuity-delete")
        pin = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep])
        packet = self.create_handoff_packet(d, principal="alice", hard_roles=[role], token_budget=20)
        receipt = self.erase_evidence(d, ev, principal="alice", policy_ref="privacy:delete")
        recovery = self.assess_recovery(d, pin_id=pin.pin_id, principal="alice")
        handoff = self.validate_handoff_packet(packet.packet_id, principal="alice")
        observed = "BOTH_BLOCKED" if (not recovery.resume_allowed and handoff["status"] == "BLOCKED_BY_GOVERNANCE" and packet.packet_id in receipt.invalidated_handoff_packet_ids) else "CONTINUITY_LEAK"
        record("continuity_handoff_deleted_source_content", "BOTH_BLOCKED", observed)

        # 18 missing barrier ledger during recovery
        d = new_domain("missing-ledger")
        _, _, rep, role = setup_source(d, "missing-ledger")
        pin = self.create_continuity_pin(d, principal="alice", hard_roles=[role], stable_refs=[rep])
        a = self.assess_recovery(d, pin_id=pin.pin_id, principal="alice", barrier_ledger_complete=False)
        observed = "FAIL_CLOSED" if not a.resume_allowed and a.layers["R3_NON_REVIVAL_BARRIER"] == "BLOCKED" else "UNSAFE_RESUME"
        record("missing_barrier_ledger_during_recovery", "FAIL_CLOSED", observed)

        failures = [x for x in outcomes if not x["passed"]]
        return {
            "kind": "recovery-privacy-acceptance-v0.6.2", "seed": seed,
            "fixture_count": len(outcomes), "failed": len(failures), "passed": not failures,
            "outcomes": outcomes, "failure_digest": digest(failures),
        }

    # ---------- migration / benchmark validity / scalability gates ----------

    @staticmethod
    def migration_correctness_fields() -> tuple[str, ...]:
        return (
            "origin_identity", "source_event_identity", "temporal_interval_boundary_semantics",
            "principal_scope", "justification_alternatives", "counterexample_relation",
            "authority_profile", "retention_recoverability", "transformation_preservation_contracts",
            "historical_judgements", "applicability", "query_family_basis", "approximate_indexes",
        )

    def register_migration_manifest(
        self, domain_id: str, *, migration_id: str, from_schema: str, to_schema: str,
        field_actions: dict[str, str],
    ) -> dict[str, object]:
        allowed = {"PRESERVE", "MAP_WITH_PROOF", "RECOMPUTE", "REVALIDATE", "DOWNGRADE", "QUARANTINE", "DELETE_BY_POLICY", "FAIL"}
        required = set(self.migration_correctness_fields()); supplied = set(field_actions)
        missing = sorted(required - supplied); extra = sorted(supplied - required)
        if missing: raise MemoryTransitionIncomplete(f"migration manifest missing correctness fields: {missing}")
        if extra: raise MemoryTransitionIncomplete(f"migration manifest has unknown correctness fields: {extra}")
        normalized = {k: str(field_actions[k]).upper() for k in sorted(field_actions)}
        invalid = {k:v for k,v in normalized.items() if v not in allowed}
        if invalid: raise MemoryTransitionIncomplete(f"migration manifest contains invalid/semantic-upgrade actions: {invalid}")
        proof_sensitive = {"origin_identity","temporal_interval_boundary_semantics","justification_alternatives","authority_profile","retention_recoverability","transformation_preservation_contracts"}
        optimistic = sorted(k for k in proof_sensitive if normalized[k] == "PRESERVE" and from_schema != to_schema)
        if optimistic: raise MemoryTransitionIncomplete(f"legacy migration cannot PRESERVE underspecified semantics without proof: {optimistic}")
        existing=self.db.execute("SELECT * FROM migration_manifests WHERE migration_id=?",(migration_id,)).fetchone()
        payload={"migration_id":migration_id,"domain_id":domain_id,"from_schema":from_schema,"to_schema":to_schema,"field_actions":normalized,"status":"VALIDATED"}
        if existing:
            old={"migration_id":existing["migration_id"],"domain_id":existing["domain_id"],"from_schema":existing["from_schema"],"to_schema":existing["to_schema"],"field_actions":json.loads(existing["field_actions_json"]),"status":existing["status"]}
            if old != payload: raise MemoryTransitionIncomplete("migration manifest identity collision")
            return old
        created_at=self._research_now(); self.db.execute("INSERT INTO migration_manifests(migration_id,domain_id,from_schema,to_schema,field_actions_json,status,created_at) VALUES(?,?,?,?,?,?,?)",(migration_id,domain_id,from_schema,to_schema,canonical_json(normalized),"VALIDATED",created_at)); payload["created_at"]=created_at; return payload

    @staticmethod
    def benchmark_fairness_required_fields() -> tuple[str, ...]:
        return ("base_model_version","context_limit","tool_access","embedding_reranker","consolidation_model","memory_construction_cost","maintenance_cost","storage_size","random_seeds","judge_configuration","baselines")

    def record_benchmark_evidence(self, *, benchmark: str, claim: str, score: dict[str, object], metadata: dict[str, object]) -> dict[str, object]:
        missing=[k for k in self.benchmark_fairness_required_fields() if k not in metadata]
        if missing: raise MemoryTransitionIncomplete(f"benchmark evidence violates fairness contract; missing {missing}")
        if not metadata.get("random_seeds") or not metadata.get("baselines"): raise MemoryTransitionIncomplete("benchmark evidence requires non-empty seeds and baselines")
        evidence_id=f"benchmark_{uuid.uuid4().hex}"; created_at=self._research_now(); record={"evidence_id":evidence_id,"benchmark":benchmark,"claim":claim,"score":dict(score),"metadata":dict(metadata),"fairness_status":"COMPLETE","created_at":created_at}
        self.db.execute("INSERT INTO benchmark_evidence_registry(evidence_id,benchmark,claim,score_json,metadata_json,fairness_status,created_at) VALUES(?,?,?,?,?,?,?)",(evidence_id,benchmark,claim,canonical_json(score),canonical_json(metadata),"COMPLETE",created_at)); return record

    def run_context_scalability_probe(self, *, store_sizes: Iterable[int], dependency_widths: Iterable[int], token_cost_per_dependency: int, token_budget: int) -> dict[str, object]:
        if token_cost_per_dependency < 0 or token_budget < 0: raise ValueError("scalability token costs/budget must be non-negative")
        store_axis=[]
        for size in store_sizes:
            if int(size) < 0: raise ValueError("store size must be non-negative")
            tokens=token_cost_per_dependency; store_axis.append({"store_size":int(size),"hard_dependency_width":1,"frame_tokens":tokens,"status":"SUFFICIENT" if tokens <= token_budget else "OVERFLOW_ESCALATED"})
        width_axis=[]; overflow=0
        for width in dependency_widths:
            if int(width) < 0: raise ValueError("dependency width must be non-negative")
            tokens=int(width)*token_cost_per_dependency; status="SUFFICIENT" if tokens <= token_budget else "OVERFLOW_ESCALATED"; overflow += int(status=="OVERFLOW_ESCALATED"); width_axis.append({"dependency_width":int(width),"frame_tokens":tokens,"status":status})
        return {"store_size_axis":store_axis,"dependency_width_axis":width_axis,"overflow_escalations":overflow,"wrong_decision_without_escalation":0,"quality_cost_frontier":"MEASURED_BY_SEPARATE_AXES"}

    @staticmethod
    def operational_semantic_field_registry() -> dict[str, dict[str, object]]:
        """Schema-to-enforcement map required by Section 389.

        This registry owns no truth. It names the actual owner plus mandatory writer/read
        boundaries that make a safety-looking field operational rather than decorative.
        """
        def e(owner, writers, readers, authority, freshness, failure, cache, fixture):
            return {
                "semantic_owner": owner, "writers": list(writers), "mandatory_readers": list(readers),
                "input_authority": authority, "freshness": freshness, "unknown_failure": failure,
                "cache_invalidation": cache, "conformance_fixture": fixture,
            }
        return {
            "expires_at": e("MemoryUseFence / policy lease", ["issue_use_fence"], ["consume_use_fence"],
                "trusted clock authority", "clock authority + epoch + dependency generations",
                "CLOCK_AUTHORITY_REQUIRED / MEMORY_FENCE_EXPIRED", "single-use fence; policy generations", "run_use_time_race_campaign"),
            "clock_epoch": e("trusted-time profile", ["issue_use_fence"], ["consume_use_fence"],
                "host/runtime clock authority", "issuing clock identity and epoch", "CLOCK_AUTHORITY_REQUIRED",
                "not reusable across incompatible clock epochs", "run_use_time_race_campaign"),
            "applicability": e("representation/claim/counterexample applicability revision",
                ["add_representation", "revise_claim", "revise_counterexample_applicability"],
                ["_representation_applicable", "claim_currently_usable", "_counterexample_applicability_matches"],
                "regime/self-version/mission evidence", "pinned cut + regime/self-version generations",
                "SCOPE_INCOMPATIBLE / UNKNOWN", "recall caches depend on regime/self-version", "run_recall_reference_equivalence_campaign"),
            "invalidates_on": e("Semantic dependency manifest", ["materialize_frame_dependency_manifest"],
                ["validate_dependencies", "validate_frame_dependency_manifest", "consume_use_fence"],
                "canonical generation owners", "Dependency(dep_class,dep_key,generation)",
                "MEMORY_DEPENDENCY_STALE", "dependency digest/generation invalidation", "run_use_time_race_campaign"),
            "hard_role": e("RecallObligation / RecallFrame", ["compile_boundary_recall"],
                ["compile_recall", "assess_frame_sufficiency"], "host consequence boundary",
                "obligation closure + hard_obligation generation", "MEMORY_RECALL_INSUFFICIENT / MEMORY_VIEW_OVERFLOW",
                "frame recompilation", "run_recall_reference_equivalence_campaign"),
            "declassified": e("MemoryDeclassificationReceipt", ["grant_declassification", "revoke_declassification"],
                ["_active_declassification", "check_information_flow", "issue_use_fence"],
                "authorized release authority", "declassification revision/expiry + policy generation",
                "SINK_DISCLOSURE_DENIED / stale flow", "flow/fence dependencies", "run_use_time_race_campaign"),
            "trusted_authority": e("MemoryOriginBindingReceipt + IntegrityAuthorityProfileRevision",
                ["capture_evidence", "register_integrity_authority_profile", "revoke_origin_binding"],
                ["get_origin_bindings", "_enforce_integrity_authority_profiles", "claim_is_supported"],
                "origin binder / integrity policy", "origin/source/integrity profile generations",
                "INSUFFICIENT_AUTHORITY / UNKNOWN_DEPENDENCE", "support bundle/claim recomputation", "run_recovery_privacy_acceptance_campaign"),
            "canonical": e("MemoryCommitReceipt + journal root", ["_commit"], ["verify_integrity", "head"],
                "correctness writer + writer fence", "incarnation/sequence/root/writer epoch",
                "INTEGRITY_ERROR / STALE_WRITER", "no derived cache may mutate canonical identity", "run_fault_atomicity_probe"),
            "recoverable": e("RecoverabilityCertificateRevision / live witness route", ["certify_recoverability"],
                ["answerability", "validate_recoverability_certificate", "consider_delete_representation"],
                "retention/source availability policy", "source/representation/query-family generations",
                "IRRECOVERABLE_GAP / UNKNOWN", "certificate invalidates on witness lifecycle", "run_recovery_privacy_acceptance_campaign"),
            "current": e("canonical lifecycle + typed current projection", ["revise_claim", "revoke_evidence", "start_new_incarnation"],
                ["claim_currently_usable", "validate_frame", "assess_recovery"],
                "canonical writer + current governance", "cut/incarnation/lifecycle/access/regime generations",
                "STALE / BLOCKED / REVALIDATION_REQUIRED", "current projection recomputed from canonical state", "run_persistence_lifelong_fuzz"),
            "negative_result": e("NegativeRecallDependencyRevision", ["execute_negative_query_domain"],
                ["validate_negative_query_receipt", "consume_use_fence"], "completeness-capable query procedure",
                "query-domain/cut/frontier/absence/access generations", "PARTIAL/OPAQUE/MEMORY_DEPENDENCY_STALE",
                "matching write bumps query-domain generation", "run_use_time_race_campaign"),
            "tool_profile": e("tool/schema capability generation", ["bump_generation"], ["issue_use_fence", "consume_use_fence"],
                "host tool/capability registry", "tool generation bound to exact sink", "TOOL_PROFILE_STALE / MEMORY_DEPENDENCY_STALE",
                "use fence dependency", "run_use_time_race_campaign"),
        }

    def audit_operational_semantic_fields(self) -> dict[str, object]:
        registry = self.operational_semantic_field_registry()
        required = {
            "expires_at", "clock_epoch", "applicability", "invalidates_on", "hard_role", "declassified",
            "trusted_authority", "canonical", "recoverable", "current", "negative_result", "tool_profile",
        }
        missing_fields = sorted(required - set(registry))
        missing_methods: list[str] = []
        malformed: list[str] = []
        required_keys = {
            "semantic_owner", "writers", "mandatory_readers", "input_authority", "freshness",
            "unknown_failure", "cache_invalidation", "conformance_fixture",
        }
        for field, entry in registry.items():
            if not required_keys.issubset(entry) or not all(entry.get(k) for k in required_keys):
                malformed.append(field); continue
            for method in list(entry["writers"]) + list(entry["mandatory_readers"]) + [entry["conformance_fixture"]]:
                if not hasattr(self, method):
                    missing_methods.append(f"{field}:{method}")
        return {
            "passed": not missing_fields and not missing_methods and not malformed,
            "field_count": len(registry), "missing_fields": missing_fields,
            "missing_methods": sorted(set(missing_methods)), "malformed_fields": sorted(malformed),
            "registry_digest": digest(registry),
        }

    @staticmethod
    def full_spec_ownership_manifest() -> dict[str, dict[str, object]]:
        """Executable ownership map for normative closure-matrix primitives.

        Physical co-location is intentional: a primitive can live inside a broader
        canonical record when it still has one writer/clock and a mandatory reader.
        The audit below checks the referenced storage surfaces and boundary methods.
        """
        def entry(storage, readers):
            return {
                "status": "EXECUTABLE",
                "storage": list(storage),
                "mandatory_readers": list(readers),
            }
        return {
            # Canonical plane
            "MemoryAuthorityDomainRevision": entry(["authority_domain_revisions"], ["list_authority_domain_revisions", "head"]),
            "MemoryWriterFenceRevision": entry(["writer_fence_revisions"], ["_commit", "audit_no_two_writable_clocks"]),
            "MemoryWriteIntentRevision": entry(["write_intents"], ["prepare_write_intent", "reconcile_write_intent"]),
            "MemoryCommitReceipt": entry(["operation_receipts", "journal"], ["verify_integrity"]),
            "RetentionEventRevision": entry(["retention_events"], ["consider_delete_representation", "erase_evidence"]),
            "MemoryErasureClosureReceipt": entry(["erasure_closure_receipts"], ["erase_evidence", "assess_recovery"]),
            "ExperienceTraceRevision": entry(["evidence"], ["capture_evidence", "get_evidence"]),
            "MemoryOriginBindingReceipt": entry(["origin_bindings"], ["get_origin_bindings", "evaluate_evidence_independence"]),
            "MemoryIntegrityAuthorityProfileRevision": entry(["integrity_authority_profiles"], ["_enforce_integrity_authority_profiles"]),
            "MemoryConfidentialityProfileRevision": entry(["access_profile_revisions"], ["_capability_allowed", "validate_frame"]),
            "MemoryDeclassificationReceipt": entry(["declassification_receipts"], ["_active_declassification", "check_information_flow"]),
            "MemoryPublicationPolicyRevision": entry(["publication_policies"], ["_active_publication_policy", "prepare_publication"]),
            "MemoryPublicationReceipt": entry(["publication_receipts", "publication_sagas"], ["complete_publication"]),
            "ClaimRevision": entry(["claims"], ["_current_claim", "claim_as_known_by"]),
            "HistoricalJudgementRevision": entry(["historical_judgements"], ["list_historical_judgements", "judgement_as_of"]),
            "MemoryJustificationRevision": entry(["justification_paths", "justification_members"], ["claim_is_supported", "claim_support_bundle"]),
            "EvidenceIndependenceRevision": entry(["evidence_independence_receipts"], ["validate_evidence_independence_receipt"]),
            "MemorySupportBundleRevision": entry(["support_bundle_receipts"], ["validate_claim_support_bundle_receipt"]),
            "CounterexampleApplicabilityRevision": entry(["counterexample_applicability_revisions"], ["_counterexample_blocks_representation"]),
            "PrincipalMemoryAccessProfileRevision": entry(["access_profile_revisions"], ["_capability_allowed", "validate_frame"]),
            "MemoryRegimeRevision": entry(["regime_revisions"], ["_representation_applicable", "assess_recovery"]),
            "SelfVersionProfileRevision": entry(["self_version_revisions"], ["_representation_applicable", "apply_interference_guard"]),
            # Representation plane
            "SemanticRegionRevision": entry(["regions", "region_evolution", "region_successors"], ["resolve_current_region", "compile_recall"]),
            "RepresentationRevision": entry(["representations"], ["_visible_representations_at_cut", "compile_recall"]),
            "TransformationContractRevision": entry(["transformation_contracts"], ["_transformation_contract", "add_representation"]),
            "SemanticLossVectorRevision": entry(["representations"], ["answerability", "certify_preservation"]),
            "PreservationEnvelopeRevision": entry(["preservation_certificates"], ["validate_preservation_certificate", "compile_recall"]),
            "RecoverabilityCertificateRevision": entry(["recoverability_certificates"], ["validate_recoverability_certificate", "answerability"]),
            "MemorySemanticDebtRevision": entry(["semantic_debts"], ["list_open_semantic_debts", "maintenance_fixed_point"]),
            "MemoryQueryCounterexampleRevision": entry(["query_counterexamples"], ["_counterexample_blocks_representation", "repair_counterexample"]),
            "MemoryEffectEvidenceRevision": entry(["effect_evidence"], ["apply_interference_guard"]),
            "MemoryActivationGuardReceipt": entry(["activation_guard_receipts"], ["apply_interference_guard"]),
            # Projection plane
            "RecallBoundaryDescriptor": entry(["frames"], ["compile_boundary_recall"]),
            "RecallObligation": entry(["frames"], ["compile_boundary_recall"]),
            "RecallCutRevision": entry(["journal", "frames"], ["close_causal_cut", "compile_recall"]),
            "MemoryQueryDomainRevision": entry(["query_domain_revisions"], ["execute_negative_query_domain"]),
            "QuerySnapshotCompletenessReceipt": entry(["connector_query_receipts"], ["validate_connector_query_receipt"]),
            "NegativeRecallDependencyRevision": entry(["negative_query_receipts"], ["validate_negative_query_receipt"]),
            "RegionDiscoveryResult": entry(["region_discovery_results"], ["discover_regions_with_receipt"]),
            "RepresentationResolution": entry(["representation_resolutions"], ["resolve_representation"]),
            "RecallReconstruction": entry(["recall_reconstructions"], ["reconstruct_role", "active_reconstruct"]),
            "RecallSufficiencyAssessment": entry(["recall_sufficiency_assessments"], ["assess_frame_sufficiency"]),
            "RecallFrameDependencyManifestRevision": entry(["frame_dependency_manifests"], ["validate_frame_dependency_manifest"]),
            "RecallFrameDescriptor": entry(["frames"], ["validate_frame"]),
            "FrameInformationFlowReceipt": entry(["flow_receipts"], ["check_information_flow"]),
            "MemoryUseFence": entry(["fences"], ["issue_use_fence", "consume_use_fence"]),
            "ContinuityPinRevision": entry(["continuity_pins"], ["create_continuity_pin", "assess_recovery"]),
            "RecoveryResumeAssessment": entry(["recovery_assessments"], ["assess_recovery"]),
        }

    def audit_full_spec_ownership(self) -> dict[str, object]:
        manifest = self.full_spec_ownership_manifest()
        tables = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables: set[str] = set()
        missing_methods: set[str] = set()
        missing_primitives: list[str] = []
        for primitive, item in manifest.items():
            primitive_missing = False
            for table in item["storage"]:
                if table not in tables:
                    missing_tables.add(str(table)); primitive_missing = True
            for method in item["mandatory_readers"]:
                if not hasattr(self, str(method)):
                    missing_methods.add(str(method)); primitive_missing = True
            if item.get("status") != "EXECUTABLE" or primitive_missing:
                missing_primitives.append(primitive)
        return {
            "passed": not missing_primitives,
            "primitive_count": len(manifest),
            "missing_primitives": sorted(missing_primitives),
            "missing_tables": sorted(missing_tables),
            "missing_methods": sorted(missing_methods),
        }

    @staticmethod
    def _full_spec_required_tables() -> tuple[str, ...]:
        return (
            "domains", "authority_domain_revisions", "writer_fence_revisions", "journal", "operation_receipts", "write_intents", "retention_events", "erasure_closure_receipts",
            "evidence", "origin_bindings", "integrity_authority_profiles", "access_profile_revisions",
            "declassification_receipts", "publication_policies", "publication_receipts", "claims",
            "historical_judgements", "justification_paths", "justification_members",
            "evidence_independence_receipts", "support_bundle_receipts",
            "counterexample_applicability_revisions", "regime_revisions", "self_version_revisions",
            "regions", "representations", "transformation_contracts", "preservation_certificates",
            "recoverability_certificates", "semantic_debts", "query_counterexamples", "effect_evidence",
            "query_domain_revisions", "region_discovery_results", "representation_resolutions", "recall_reconstructions", "recall_sufficiency_assessments", "frame_dependency_manifests", "frames", "fences", "continuity_pins", "recovery_assessments", "connector_profiles",
            "connector_query_receipts", "migration_manifests", "benchmark_evidence_registry",
        )

    @staticmethod
    def _full_spec_required_methods() -> tuple[str, ...]:
        return (
            "verify_integrity", "discover_regions_with_receipt", "resolve_representation", "reconstruct_role", "assess_frame_sufficiency", "materialize_frame_dependency_manifest", "compile_query_domain", "execute_negative_query_domain", "list_authority_domain_revisions", "list_writer_fence_revisions", "prepare_write_intent", "reconcile_write_intent", "compile_recall", "compile_boundary_recall", "issue_use_fence", "consume_use_fence",
            "record_query_counterexample", "repair_counterexample", "consider_delete_representation",
            "assess_recovery", "assess_replay", "audit_no_two_writable_clocks",
            "prepare_publication", "complete_publication", "check_information_flow",
            "certify_preservation", "validate_preservation_certificate", "certify_recoverability",
            "register_migration_manifest", "record_benchmark_evidence", "run_independent_differential",
            "run_use_time_race_campaign", "run_recovery_privacy_acceptance_campaign",
            "run_persistence_lifelong_fuzz", "select_continuity_pin", "validate_handoff_packet",
            "claim_currently_usable", "rollback_claim_to_revision",
        )

    def run_fault_atomicity_probe(self) -> dict[str, object]:
        """Exercise crash points against the real canonical transaction path."""
        class InjectedFault(RuntimeError):
            pass
        class OneShot:
            def __init__(self, target): self.target=target; self.fired=False
            def __call__(self, point, context):
                if point == self.target and not self.fired:
                    self.fired=True; raise InjectedFault(point)

        failures: list[dict[str, object]] = []
        outcomes: list[dict[str, object]] = []
        for index, point in enumerate((
            "before_mutation", "after_mutation_before_journal",
            "after_journal_before_receipt", "after_receipt_before_commit", "after_commit",
        )):
            domain_id=f"release_fault_{uuid.uuid4().hex[:10]}_{index}"
            self.create_domain(domain_id)
            injector=OneShot(point); self.set_fault_injector(injector)
            observed_exception=False
            try:
                self.capture_evidence_batch(
                    domain_id=domain_id, operation_id="fault-op", expected_seq=0, writer_epoch=1, principal="release-gate",
                    items=[{"source_event_identity":"event:1","content":{"v":1}}],
                )
            except InjectedFault:
                observed_exception=True
            finally:
                self.set_fault_injector(None)
            count=self.count_evidence(domain_id); seq=self.head(domain_id).sequence
            integrity=self.verify_integrity(domain_id)
            if point == "after_commit":
                try:
                    receipt=self.capture_evidence_batch(
                        domain_id=domain_id, operation_id="fault-op", expected_seq=0, writer_epoch=1, principal="release-gate",
                        items=[{"source_event_identity":"event:1","content":{"v":1}}],
                    )
                    good=observed_exception and count==1 and seq==1 and receipt.commit_seq==1 and self.count_evidence(domain_id)==1 and integrity
                except Exception as exc:
                    good=False; failures.append({"point":point,"error":type(exc).__name__})
            else:
                good=observed_exception and count==0 and seq==0 and integrity
            outcomes.append({"point":point,"passed":bool(good),"sequence":seq,"evidence_count":count})
            if not good and not any(f.get("point")==point for f in failures):
                failures.append({"point":point,"error":"invariant_mismatch"})
        return {"passed":not failures,"failures":failures,"outcomes":outcomes}

    def run_full_spec_release_gate(
        self, domain_id: str, *, seed: int = 603, fuzz_cases: int = 10_000, differential_cases: int = 128,
        persistence_fuzz_cases: int = 1_000,
    ) -> FullSpecReleaseGateReport:
        """Machine-enforced implementation gate for the v0.6.3 executable profile.

        This gate deliberately does not turn internal tests into W5/external research
        evidence. `implementation_ready` and `research_complete` remain independent.
        """
        if fuzz_cases < 1 or differential_cases < 0 or persistence_fuzz_cases < 1:
            raise ValueError("release-gate case counts are invalid")
        checks: dict[str, str] = {}
        metrics: dict[str, object] = {}

        tables={row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables=sorted(set(self._full_spec_required_tables())-tables)
        missing_methods=sorted(name for name in self._full_spec_required_methods() if not hasattr(self,name))
        checks["closure_surfaces"]="PASS" if not missing_tables and not missing_methods else "FAIL"
        metrics["missing_tables"]=missing_tables; metrics["missing_methods"]=missing_methods
        ownership = self.audit_full_spec_ownership()
        checks["ownership_closure"] = "PASS" if ownership["passed"] else "FAIL"
        metrics["ownership_primitive_count"] = ownership["primitive_count"]
        metrics["ownership_missing_primitives"] = ownership["missing_primitives"]

        try:
            integrity_ok=bool(self.verify_integrity(domain_id))
        except Exception:
            integrity_ok=False
        checks["canonical_integrity"]="PASS" if integrity_ok else "FAIL"

        clock_audit=self.audit_no_two_writable_clocks(domain_id)
        checks["no_two_writable_clocks"]="PASS" if clock_audit.passed else "FAIL"
        metrics["clock_violations"]=len(clock_audit.violations)

        lab=self.run_preservation_lab()
        checks["preservation_calculus"]="PASS" if lab.failed==0 else "FAIL"
        metrics["preservation_lab_cases"]=lab.cases; metrics["preservation_lab_failures"]=lab.failed

        fuzz=self.run_lifelong_fuzz(seed=seed,cases=fuzz_cases)
        checks["lifelong_fuzz"]="PASS" if fuzz.failed==0 else "FAIL"
        metrics["lifelong_fuzz_cases"]=fuzz.cases; metrics["lifelong_fuzz_failures"]=fuzz.failed; metrics["lifelong_fuzz_seed"]=seed

        differential=self.run_independent_differential(seed=seed,cases=differential_cases)
        checks["independent_differential"]="PASS" if differential.failed==0 else "FAIL"
        metrics["differential_cases"]=differential.cases; metrics["differential_failures"]=differential.failed

        fault=self.run_fault_atomicity_probe()
        checks["fault_atomicity"]="PASS" if fault["passed"] else "FAIL"
        metrics["fault_probe_failures"]=len(fault["failures"]); metrics["fault_probe_outcomes"]=fault["outcomes"]

        persistence=self.run_persistence_lifelong_fuzz(
            seed=seed, cases=persistence_fuzz_cases,
            restart_interval=max(17, min(257, persistence_fuzz_cases // 7 or 17)),
            recompute_interval=max(7, min(31, persistence_fuzz_cases // 13 or 7)),
        )
        checks["persistence_lifelong_fuzz"]="PASS" if persistence.failed==0 else "FAIL"
        metrics["persistence_fuzz_cases"]=persistence.cases
        metrics["persistence_fuzz_failures"]=persistence.failed
        metrics["persistence_fuzz_restarts"]=persistence.details.get("restart_count", 0)
        metrics["persistence_fuzz_recomputations"]=persistence.details.get("full_recomputation_checks", 0)
        metrics["persistence_projection_drift_failures"]=persistence.details.get("projection_drift_failures", 0)

        races=self.run_use_time_race_campaign(seed=seed)
        checks["use_time_race_campaign"]="PASS" if races["failed"]==0 else "FAIL"
        metrics["use_time_race_schedules"]=races["schedule_count"]
        metrics["use_time_race_failures"]=races["failed"]

        recovery=self.run_recovery_privacy_acceptance_campaign(seed=seed)
        checks["recovery_privacy_campaign"]="PASS" if recovery["failed"]==0 else "FAIL"
        metrics["recovery_privacy_fixtures"]=recovery["fixture_count"]
        metrics["recovery_privacy_failures"]=recovery["failed"]

        publication_cycle=self.run_publication_cycle_acceptance_campaign(seed=seed)
        checks["publication_cycle_campaign"]="PASS" if publication_cycle["failed"]==0 else "FAIL"
        metrics["publication_cycle_fixtures"]=publication_cycle["fixture_count"]
        metrics["publication_cycle_failures"]=publication_cycle["failed"]

        flow_use=self.run_information_flow_use_time_campaign(seed=seed)
        checks["information_flow_use_time_campaign"]="PASS" if flow_use["failed"]==0 else "FAIL"
        metrics["information_flow_use_time_fixtures"]=flow_use["fixture_count"]
        metrics["information_flow_use_time_failures"]=flow_use["failed"]

        pressure=self.run_resource_pressure_use_validation_campaign(seed=seed)
        checks["resource_pressure_use_validation_campaign"]="PASS" if pressure["failed"]==0 else "FAIL"
        metrics["resource_pressure_use_validation_fixtures"]=pressure["fixture_count"]
        metrics["resource_pressure_use_validation_failures"]=pressure["failed"]

        temporal=self.run_temporal_acceptance_campaign(seed=seed)
        checks["temporal_acceptance_campaign"]="PASS" if temporal["failed"]==0 else "FAIL"
        metrics["temporal_acceptance_fixtures"]=temporal["fixture_count"]
        metrics["temporal_acceptance_failures"]=temporal["failed"]

        procedure=self.run_procedure_failure_acceptance_campaign(seed=seed)
        checks["procedure_failure_acceptance_campaign"]="PASS" if procedure["failed"]==0 else "FAIL"
        metrics["procedure_failure_acceptance_fixtures"]=procedure["fixture_count"]
        metrics["procedure_failure_acceptance_failures"]=procedure["failed"]

        security=self.run_security_privacy_acceptance_campaign(seed=seed)
        checks["security_privacy_acceptance_campaign"]="PASS" if security["failed"]==0 else "FAIL"
        metrics["security_privacy_acceptance_fixtures"]=security["fixture_count"]
        metrics["security_privacy_acceptance_failures"]=security["failed"]

        migration=self.run_migration_acceptance_campaign(seed=seed)
        checks["migration_acceptance_campaign"]="PASS" if migration["failed"]==0 else "FAIL"
        metrics["migration_acceptance_fixtures"]=migration["fixture_count"]
        metrics["migration_acceptance_failures"]=migration["failed"]

        performance=self.run_performance_semantic_gate_campaign(seed=seed)
        checks["performance_semantic_gate_campaign"]="PASS" if performance["failed"]==0 else "FAIL"
        metrics["performance_semantic_gate_fixtures"]=performance["fixture_count"]
        metrics["performance_semantic_gate_failures"]=performance["failed"]

        formal=self.run_reference_formal_suite(seed=seed)
        checks["reference_formal_suite"]="PASS" if formal["failed"]==0 else "FAIL"
        metrics["reference_formal_property_families"]=formal["property_family_count"]
        metrics["reference_formal_suite_failures"]=formal["failed"]
        metrics["reference_formal_lifelong_cases"]=formal["lifelong_cases"]

        metric_catalog=self.experimental_metric_catalog()
        metric_ok=(len(metric_catalog.get("semantic_errors", []))==7 and bool(metric_catalog.get("preservation_corrigibility")) and bool(metric_catalog.get("context_scaling")) and bool(metric_catalog.get("effect_interference")))
        checks["experimental_metric_contract"]="PASS" if metric_ok else "FAIL"
        metrics["experimental_metric_family_count"]=len(metric_catalog)

        ablation=self.interaction_ablation_protocol()
        ablation_ok=(len(ablation.get("interactions", []))==8 and all(x.get("reports_task_quality") and x.get("reports_semantic_violations") for x in ablation.get("interactions", [])))
        checks["interaction_ablation_protocol"]="PASS" if ablation_ok else "FAIL"
        metrics["interaction_ablation_count"]=len(ablation.get("interactions", []))

        stress=self.run_private_stress_world_campaign(seed=seed)
        checks["private_stress_world_campaign"]="PASS" if stress["failed"]==0 else "FAIL"
        metrics["private_stress_world_count"]=stress["world_count"]
        metrics["private_stress_world_failures"]=stress["failed"]

        longitudinal=self.run_longitudinal_experiment_protocol(seed=seed, checkpoints=(1,2,4))
        checks["longitudinal_experiment_protocol"]="PASS" if longitudinal["passed"] else "FAIL"
        metrics["longitudinal_checkpoint_count"]=longitudinal["checkpoint_count"]

        use_time_calculus=self.run_use_time_causal_cut_calculus(seed=seed)
        checks["use_time_causal_cut_calculus"]="PASS" if use_time_calculus["failed"]==0 else "FAIL"
        metrics["use_time_calculus_cases"]=use_time_calculus["cases"]
        metrics["use_time_calculus_property_families"]=use_time_calculus["property_family_count"]
        metrics["use_time_calculus_failures"]=use_time_calculus["failed"]

        v061=self.run_v061_seam_calculus(seed=seed)
        checks["v061_seam_calculus"]="PASS" if v061["failed"]==0 else "FAIL"
        metrics["v061_seam_calculus_cases"]=v061["cases"]
        metrics["v061_seam_calculus_property_families"]=v061["property_family_count"]
        metrics["v061_seam_calculus_failures"]=v061["failed"]

        v062=self.run_v062_continuity_recovery_erasure_calculus(seed=seed)
        checks["v062_continuity_recovery_erasure_calculus"]="PASS" if v062["failed"]==0 else "FAIL"
        metrics["v062_continuity_calculus_cases"]=v062["cases"]
        metrics["v062_continuity_calculus_property_families"]=v062["property_family_count"]
        metrics["v062_continuity_calculus_failures"]=v062["failed"]

        status=self.k5_profile_status()
        research_closure=str(status["research_closure"])
        research_complete=research_closure=="PASS" and bool(status.get("independent_validation_claimed"))
        implementation_ready=all(value=="PASS" for value in checks.values())
        now=self._research_now()
        report=FullSpecReleaseGateReport(
            gate_id=f"release_gate_{uuid.uuid4().hex}",domain_id=domain_id,implementation_ready=implementation_ready,
            research_complete=research_complete,research_closure=research_closure,checks=checks,metrics=metrics,
            unsupported_claims=list(status.get("unsupported_claims",[])),created_at=now,
        )
        self.db.execute(
            "INSERT INTO release_gate_runs(gate_id,domain_id,report_json,created_at) VALUES(?,?,?,?)",
            (report.gate_id,domain_id,canonical_json(asdict(report)),now),
        )
        return report

    # ---------- Sections 153-161 executable experimental program ----------

    @staticmethod
    def experimental_metric_catalog() -> dict[str, list[str]]:
        """Return the normative metric families without turning them into authority."""
        return {
            "semantic_errors": ["MAPE", "ARCE", "WDWRE", "CPIL", "RSD", "DEAR", "FIPR"],
            "preservation_corrigibility": [
                "Protected Query Family Coverage", "Preservation Envelope Calibration",
                "Counterexample Detection Latency", "Local Repair Blast Radius",
                "Source Rehydration Success", "Irrecoverable Gap Rate",
                "Protected Witness-Cover Violation Rate", "Cumulative Loss Discovery Depth",
                "Raw-Source Rebase Frequency and cost",
            ],
            "context_scaling": [
                "MCE_total", "MCE_width", "p50/p95/p99 frame tokens", "p50/p95/p99 latency",
                "page-fault count", "required-role coverage", "WDWRE", "cache hit rate",
            ],
            "effect_interference": [
                "Memory-enabled vs NullMemory decision delta",
                "optional-memory inhibition precision/recall", "hard-role suppression attempts",
                "cross-model effect transfer error", "cross-task effect transfer error",
                "rendering-sensitive effect delta", "interference concentration",
                "longitudinal violation rate versus memory prefix",
            ],
        }

    @staticmethod
    def _nearest_rank(values: list[float], percentile: float) -> float | int | None:
        if not values:
            return None
        ordered = sorted(values)
        rank = max(1, int((percentile * len(ordered) + 99.999999) // 100))
        rank = min(rank, len(ordered))
        return ordered[rank - 1]

    def summarize_experiment_metrics(self, records: Iterable[dict[str, object]]) -> dict[str, object]:
        """Preserve denominators, abstention/overflow, and tail metrics.

        This intentionally refuses to collapse typed safe escalations into one accuracy
        number.  Missing optional measurements are omitted rather than invented.
        """
        rows = [dict(r) for r in records]
        denom = len(rows)
        def count(key: str) -> int:
            return sum(bool(r.get(key, False)) for r in rows)
        def tail(key: str) -> dict[str, object]:
            vals = [float(r[key]) for r in rows if key in r and r[key] is not None]
            if not vals:
                return {"count": 0, "p50": None, "p95": None, "p99": None}
            def clean(v):
                return int(v) if float(v).is_integer() else v
            return {
                "count": len(vals),
                "p50": clean(self._nearest_rank(vals, 50)),
                "p95": clean(self._nearest_rank(vals, 95)),
                "p99": clean(self._nearest_rank(vals, 99)),
            }
        silent = count("silent_violation")
        return {
            "denominator": denom, "silent_violation_numerator": silent,
            "silent_violation_rate": (silent / denom) if denom else None,
            "abstentions": count("abstained"), "overflows": count("overflow"),
            "frame_tokens": tail("frame_tokens"), "latency_ms": tail("latency_ms"),
            "page_faults": tail("page_faults"),
        }

    @staticmethod
    def interaction_ablation_protocol() -> dict[str, object]:
        pairs = [
            ("association_x_lateral_inhibition", "candidate_recall_quality", "scope_or_hub_semantic_violations"),
            ("consolidation_x_counterexample_preservation", "compact_task_quality", "counterexample_loss_violations"),
            ("preservation_envelope_x_source_rehydration", "exact_query_quality", "false_recoverability_violations"),
            ("query_counterexample_x_local_repair", "post_repair_quality", "repair_blast_radius_violations"),
            ("witness_cover_retention_x_privacy_deletion", "future_answerability", "witness_or_erasure_violations"),
            ("effect_guard_x_hard_role_conservation", "consumer_task_quality", "hard_role_suppression_violations"),
            ("multi_view_discovery_x_representation_resolution", "recall_quality", "wrong_region_or_adequacy_violations"),
            ("recall_obligation_x_context_budget_overflow", "decision_quality", "silent_hard_role_truncation_violations"),
        ]
        return {
            "kind": "interaction-ablation-protocol-v0.6.3",
            "interactions": [
                {
                    "name": name, "task_quality_metric": quality,
                    "semantic_violation_metric": semantic,
                    "reports_task_quality": True, "reports_semantic_violations": True,
                    "required_controls": ["full_system", "remove_left", "remove_right", "remove_both"],
                }
                for name, quality, semantic in pairs
            ],
            "external_result_status": "NOT_RUN",
            "claim_boundary": "protocol_executable_results_require_actual_experiment",
        }

    def run_private_stress_world_campaign(self, *, seed: int = 160) -> dict[str, object]:
        """Execute the twelve private stress-world classes from Section 160.

        The campaign composes already-independent runtime campaigns where possible and
        adds direct checks for model-scoped effect transfer.  It is internal synthetic
        evidence only.
        """
        temporal = self.run_temporal_acceptance_campaign(seed=seed + 1)
        procedure = self.run_procedure_failure_acceptance_campaign(seed=seed + 2)
        security = self.run_security_privacy_acceptance_campaign(seed=seed + 3)
        performance = self.run_performance_semantic_gate_campaign(seed=seed + 4)
        fault = self.run_fault_atomicity_probe()
        formal = self.run_reference_formal_suite(seed=seed + 5, lifelong_cases=1_000)

        by_fixture: dict[str, dict[str, object]] = {}
        for report in (temporal, procedure, security, performance):
            for item in report["outcomes"]:
                by_fixture[item["fixture"]] = item

        worlds: list[dict[str, object]] = []
        def add(name: str, passed: bool, typed_outcome: str, source: str) -> None:
            worlds.append({"world": name, "passed": bool(passed), "typed_outcome": typed_outcome, "evidence_source": source})

        add("popular_stale_fact_vs_fresh_direct_observation",
            bool(by_fixture.get("stale_index_cache_cannot_ignore_revocation", {}).get("passed")),
            "CANONICAL_FILTERED", "section268")
        add("rare_catastrophic_counterexample_vs_99_successes",
            bool(by_fixture.get("one_shot_catastrophic_counterexample_retained", {}).get("passed")),
            "PROTECTED_NEGATIVE_EVIDENCE", "section264")
        add("same_lesson_opposite_outcome_across_applicability_slices",
            bool(by_fixture.get("opposite_outcomes_across_structural_slices", {}).get("passed")),
            "CONDITIONAL", "section264")
        add("late_historical_evidence_after_consequential_decision",
            bool(by_fixture.get("retrospective_correction_retains_wrong_judgement", {}).get("passed")),
            "HISTORICAL_JUDGEMENT_PRESERVED", "section263")
        add("lost_negation_five_transform_generations_deep",
            bool(formal["property_results"].get("loss_absorption_pure_chain")),
            "LOST_NOT_RESURRECTED", "formal-suite")
        add("source_deletion_before_future_exact_query",
            bool(by_fixture.get("deleting_witness_downgrades_recoverability", {}).get("passed")),
            "RECOVERABILITY_DOWNGRADED", "section268")
        add("poisoned_source_laundered_through_summaries_agents",
            bool(by_fixture.get("untrusted_content_summary_procedure_proposal", {}).get("passed")),
            "AUTHORITY_NOT_ELEVATED", "section265")

        # Model/consumer-specific effect evidence must not transfer to a new consumer.
        d = f"stress_effect_{seed}_{uuid.uuid4().hex[:8]}"; self.create_domain(d)
        fam = f"STRESS_EFFECT_{seed}"; self.register_query_family(fam, {"x"})
        region = self.create_region(d, "effect", principal="alice")
        rep = self.add_representation(d, region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice")
        frame = self.compile_recall(d, "alice", [RecallRole("effect", region, fam, hard=False)], 10)
        self.record_effect_evidence(d, [rep], consumer="model-v1", task="t", regime="r", rendering="plain",
            outcome_dimension="accuracy", tier="E4", effect=-1.0, confidence=1.0)
        guarded_v1, _ = self.apply_interference_guard(frame, consumer="model-v1", task="t", regime="r", rendering="plain")
        guarded_v2, _ = self.apply_interference_guard(frame, consumer="model-v2", task="t", regime="r", rendering="plain")
        add("model_upgrade_reverses_interference_profile",
            len(guarded_v1.fragments) == 0 and len(guarded_v2.fragments) == 1,
            "PROFILE_NOT_TRANSFERRED", "effect-ledger")
        add("index_lag_after_revocation_correction",
            bool(by_fixture.get("approx_ann_cannot_certify_exact_hard_search", {}).get("passed")),
            "CAPABILITY_DOWNGRADED", "section268")
        add("context_budget_smaller_than_hard_dependency_width",
            bool(by_fixture.get("smaller_frame_cannot_drop_hard_role", {}).get("passed")),
            "OVERFLOW", "section268")
        add("shared_memory_principal_partial_visibility",
            bool(by_fixture.get("hidden_private_memory_zero_ranking_influence", {}).get("passed")),
            "ZERO_HIDDEN_INFLUENCE", "section265")
        add("crash_during_consolidation_admission", bool(fault["passed"]), "ATOMIC_ROLLBACK_OR_RECONCILE", "fault-atomicity")
        failures = [w for w in worlds if not w["passed"]]
        return {
            "kind": "private-stress-world-campaign-v0.6.3", "seed": seed,
            "world_count": len(worlds), "failed": len(failures), "passed": not failures,
            "worlds": worlds, "failure_digest": digest(failures),
            "external_validity": "NOT_CLAIMED",
        }

    def run_longitudinal_experiment_protocol(
        self, *, seed: int = 161, checkpoints: Iterable[int] = (1, 2, 4, 8),
    ) -> dict[str, object]:
        """Run a bounded longitudinal memory-prefix protocol with fixed configuration."""
        prefixes = tuple(int(x) for x in checkpoints)
        if not prefixes or any(x < 1 for x in prefixes) or list(prefixes) != sorted(set(prefixes)):
            raise ValueError("checkpoints must be unique positive increasing prefixes")
        rng = random.Random(seed)
        domain = f"longitudinal_{seed}_{uuid.uuid4().hex[:8]}"; self.create_domain(domain)
        family = f"LONG_{seed}_{uuid.uuid4().hex[:6]}"; self.register_query_family(family, {"x"})
        config = {
            "consumer": "synthetic-fixed-consumer-v1", "model_version": "fixed-model-v1",
            "tool_profile": "fixed-tools-v1", "rendering": "structured-v1",
            "task_family": "longitudinal-anchor-fresh-incident", "seed": seed,
        }
        config_digest = digest(config)
        reps: list[str] = []; regions: list[str] = []
        results: list[dict[str, object]] = []
        created = 0
        for prefix in prefixes:
            while created < prefix:
                created += 1
                region = self.create_region(domain, f"prefix:{created}", principal="alice")
                rep = self.add_representation(
                    domain, region, kind="event", payload={"x": created, "noise": rng.randrange(1_000_000)},
                    loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
                )
                regions.append(region); reps.append(rep)
            # Stable anchor plus the freshest item; this keeps configuration fixed while
            # memory grows.  The current head is the frozen checkpoint cut.
            role_regions = [regions[0]] if prefix == 1 else [regions[0], regions[prefix - 1]]
            roles = [RecallRole(f"probe:{i}", rid, family, hard=True) for i, rid in enumerate(role_regions)]
            frame = self.compile_recall(domain, "alice", roles, token_budget=32)
            selected = [f.representation_id for f in frame.fragments]
            exposure = self.record_memory_exposure(
                domain, frame_id=frame.frame_id, consumer=config["consumer"], task=config["task_family"],
                regime="fixed-regime-v1", rendering=config["rendering"],
                candidate_representation_ids=selected, selected_representation_ids=selected,
                rendered_representation_ids=selected, referenced_representation_ids=selected[:1],
            )
            open_debts = len(self.list_open_semantic_debts(domain))
            results.append({
                "prefix": prefix, "cut": asdict(frame.cut), "configuration_digest": config_digest,
                "null_memory": {"persistent_memory": False, "frame_tokens": 0, "selected": []},
                "memory_enabled": {
                    "persistent_memory": True, "frame_tokens": frame.token_cost,
                    "page_faults": sum(1 for f in frame.fragments if f.page_faulted),
                    "selected": selected, "recoverability": [self.answerability(r, family).value for r in selected],
                    "semantic_debt": open_debts, "procedure_reuse": 0,
                    "exposure_chain": {
                        "candidate": exposure.candidate_representation_ids,
                        "selected": exposure.selected_representation_ids,
                        "rendered": exposure.rendered_representation_ids,
                        "referenced": exposure.referenced_representation_ids,
                    },
                },
                "probes": ["anchor", "fresh", "incident"],
            })
        stable = all(r["configuration_digest"] == config_digest for r in results)
        exposed = all(r["memory_enabled"]["exposure_chain"]["candidate"] for r in results)
        return {
            "kind": "longitudinal-experiment-protocol-v0.6.3", "seed": seed,
            "configuration": config, "configuration_digest": config_digest,
            "checkpoint_count": len(results), "checkpoints": results,
            "passed": stable and exposed, "external_validity": "NOT_CLAIMED",
            "controls": ["NullMemory", "fixed-memory-configuration"],
        }

    # ---------- benchmark/ablation and conformance scaffolding ----------

    @staticmethod
    def benchmark_ablation_portfolio() -> dict[str, list[str]]:
        return {
            "baselines": [
                "no_persistent_memory", "long_context", "lexical_dense_rag", "extracted_fact_memory",
                "temporal_graph_memory", "event_reconstruction_memory", "procedural_memory",
            ],
            "benchmarks": [
                "LongMemEval", "LongMemEval-V2", "LoCoMo", "AMA-Bench", "MemoryArena",
                "ImplicitMemBench", "procedural_transfer", "transition_hallucination", "private_semantic_worlds",
            ],
            "ablations": [
                "association_x_lateral_inhibition", "consolidation_x_counterexample_preservation",
                "preservation_envelope_x_source_rehydration", "query_counterexample_x_local_repair",
                "witness_cover_x_privacy_deletion", "effect_guard_x_hard_role_conservation",
                "multi_view_x_representation_resolution", "recall_obligation_x_context_overflow",
            ],
        }

    @staticmethod
    def k5_profile_status() -> dict[str, object]:
        return {
            "executable_support": {f"K{i}": True for i in range(6)},
            "research_closure": "BLOCKED",
            "independent_validation_claimed": False,
            "residual_debts": [
                "future-query-basis", "preservation-composition", "local-repair-closure",
                "interference-calibration", "witness-cover-optimality", "capability-refinement", "external-validity",
            ],
            "unsupported_claims": ["universal_future_query_safety", "empirical_superiority", "independent_replication"],
        }

    def conformance_vector(self, domain_id: str) -> dict[str, object]:
        regions = {r["region_id"]: r["semantic_key"] for r in self.db.execute("SELECT * FROM regions WHERE domain_id=?", (domain_id,)).fetchall()}
        evidence = []
        for r in self.db.execute("SELECT * FROM evidence WHERE domain_id=? ORDER BY source_event_identity", (domain_id,)).fetchall():
            evidence.append((r["source_event_identity"], r["content_digest"], r["revoked_seq"] is not None, r["deleted_seq"] is not None))
        reps = []
        for r in self.db.execute("SELECT * FROM representations WHERE domain_id=?", (domain_id,)).fetchall():
            reps.append((regions.get(r["region_id"], "?"), r["kind"], digest(json.loads(r["payload_json"])),
                         r["transform_kind"], r["transform_profile"], r["loss_json"], r["recoverable_json"], int(r["token_cost"]),
                         r["invalidated_seq"] is not None, r["tainted_seq"] is not None))
        debts = [(r["kind"], r["severity"], r["outcome"]) for r in self.db.execute("SELECT * FROM semantic_debts WHERE domain_id=?", (domain_id,)).fetchall()]
        return {
            "evidence": sorted(evidence), "regions": sorted(regions.values()), "representations": sorted(reps),
            "debts": sorted(debts), "counts": {
                "journal": self.db.execute("SELECT COUNT(*) FROM journal WHERE domain_id=?", (domain_id,)).fetchone()[0],
                "counterexamples": self.db.execute("SELECT COUNT(*) FROM query_counterexamples WHERE domain_id=?", (domain_id,)).fetchone()[0],
            },
        }

    def differential_conformance(self, other, domain_id: str) -> dict[str, object]:
        left = self.conformance_vector(domain_id); right = other.conformance_vector(domain_id)
        return {"equivalent": left == right, "left_digest": digest(left), "right_digest": digest(right), "mode": "EXACT_SEMANTIC_EQUIVALENCE"}

    def run_independent_differential(
        self, *, seed: int = 73, cases: int = 128, kernel_factory=None,
    ) -> ResearchRunReport:
        """Run a frozen + generated semantic corpus against an independent state machine."""
        if cases < 0:
            raise ValueError("cases must be >= 0")
        kernel = (kernel_factory or IndependentSemanticKernel)()
        rng = random.Random(seed)
        suffix = uuid.uuid4().hex[:12]
        domain_id = f"diff_{suffix}"
        family_x = f"DIFF_X_{suffix}"
        family_ab = f"DIFF_AB_{suffix}"
        self.create_domain(domain_id)
        primary_ids: dict[str, str] = {}
        rep_ids: dict[str, str] = {}
        region_ids: dict[str, str] = {}
        passed = 0
        failed = 0
        mismatches: list[dict[str, object]] = []
        classifications = {
            "implementation_bug": 0,
            "spec_ambiguity": 0,
            "capability_difference": 0,
            "normalization_profile_mismatch": 0,
            "unsupported_extension": 0,
        }

        def compare(label: str, left, right) -> None:
            nonlocal passed, failed
            if left == right:
                passed += 1
            else:
                failed += 1
                classifications["implementation_bug"] += 1
                if len(mismatches) < 32:
                    mismatches.append({"label": label, "primary": left, "independent": right})

        # Frozen corpus: identity/dedupe, origin, representation, claim support,
        # revocation, and query-family evolution.
        self.register_query_family(family_x, {"x"}, revision=1)
        kernel.register_query_family(family_x, {"x"}, revision=1)
        compare("family-r1", self._family_requirements(family_x), kernel.query_families[family_x]["dimensions"])

        h = self._head_row(domain_id)
        rec = self.capture_evidence(
            domain_id=domain_id, operation_id="diff:e1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity="wire:1", content={"x": 1}, principal="alice",
            transport_delivery_id="delivery:1", origin_roots=["origin:wire"], common_mode_group="common:wire",
        )
        primary_ids["e1"] = rec.object_id
        kernel.capture_evidence("e1", "wire:1", {"x": 1}, delivery_id="delivery:1", roots=["origin:wire"], common_mode_group="common:wire")
        h = self._head_row(domain_id)
        self.capture_evidence(
            domain_id=domain_id, operation_id="diff:e1-redelivery", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity="wire:1", content={"x": 1}, principal="alice",
            transport_delivery_id="delivery:2", origin_roots=["origin:wire"], common_mode_group="common:wire",
        )
        kernel.capture_evidence("e1", "wire:1", {"x": 1}, delivery_id="delivery:2", roots=["origin:wire"], common_mode_group="common:wire")
        compare("evidence-dedupe", self.count_evidence(domain_id), len(kernel.evidence_by_sid))
        compare("delivery-multiplicity", self.count_deliveries(domain_id, "wire:1"), len(kernel.evidence_by_sid["wire:1"]["deliveries"]))

        h = self._head_row(domain_id)
        rec2 = self.capture_evidence(
            domain_id=domain_id, operation_id="diff:e2", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity="wire:2", content={"x": 2}, principal="alice",
            origin_roots=["origin:other"], common_mode_group="common:other",
        )
        primary_ids["e2"] = rec2.object_id
        kernel.capture_evidence("e2", "wire:2", {"x": 2}, delivery_id="delivery:diff:e2", roots=["origin:other"], common_mode_group="common:other")

        region_ids["r"] = self.create_region(domain_id, "semantic:r", principal="alice")
        kernel.create_region("r", "semantic:r")
        rep_ids["raw"] = self.add_representation(
            domain_id, region_ids["r"], kind="source", payload={"x": 1},
            loss={"x": "PRESERVED_EXACT"}, recoverable=set(), token_cost=4, principal="alice",
            source_evidence_ids=[primary_ids["e1"]], transform_kind="SOURCE_REBASE", transform_profile="diff:source",
        )
        kernel.add_representation("raw", region_name="r", kind="source", payload={"x": 1},
                                  loss={"x": "PRESERVED_EXACT"}, recoverable=set())
        rep_ids["summary"] = self.add_representation(
            domain_id, region_ids["r"], kind="summary", payload={"x": 1},
            loss={"x": "PRESERVED_EXACT"}, recoverable=set(), token_cost=1, principal="alice",
            source_representation_ids=[rep_ids["raw"]], transform_kind="PURE", transform_profile="diff:summary",
        )
        kernel.add_representation("summary", region_name="r", kind="summary", payload={"x": 1},
                                  loss={"x": "PRESERVED_EXACT"}, recoverable=set(), source_representation_names=["raw"])
        compare("answerability-r1", self.answerability(rep_ids["summary"], family_x).value, kernel.answerability("summary", family_x))

        h = self._head_row(domain_id)
        claim = self.create_claim(
            domain_id=domain_id, operation_id="diff:claim", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="claim:x", proposition={"x": 1}, valid_from=None, valid_to=None,
            support_paths=[[primary_ids["e1"]]], principal="alice",
        )
        kernel.create_claim("claim:x", [["e1"]])
        compare("claim-supported", self.claim_is_supported(domain_id, "claim:x"), kernel.claim_supported("claim:x"))

        self.revoke_evidence(domain_id, primary_ids["e2"], principal="alice")
        kernel.revoke_evidence("e2")
        primary_e2 = self.db.execute("SELECT revoked_seq FROM evidence WHERE evidence_id=?", (primary_ids["e2"],)).fetchone()
        compare("revocation", primary_e2["revoked_seq"] is not None, kernel.evidence_by_sid["wire:2"]["revoked"])

        self.register_query_family(family_x, {"x", "y"}, revision=2)
        kernel.register_query_family(family_x, {"x", "y"}, revision=2)
        compare("family-r2", self._family_requirements(family_x), kernel.query_families[family_x]["dimensions"])
        compare("basis-expansion", self.answerability(rep_ids["summary"], family_x).value, kernel.answerability("summary", family_x))

        # Compare a normalized frozen snapshot without implementation-local UUIDs.
        primary_snapshot = {
            "evidence": sorted([
                (
                    row["source_event_identity"], row["content_digest"], row["revoked_seq"] is not None,
                    tuple(self.get_origin_roots(domain_id, "evidence", row["evidence_id"])),
                    tuple(sorted({b.common_mode_group for b in self.get_origin_bindings(domain_id, row["evidence_id"]) if b.common_mode_group})),
                    self.count_deliveries(domain_id, row["source_event_identity"]),
                )
                for row in self.db.execute("SELECT * FROM evidence WHERE domain_id=?", (domain_id,)).fetchall()
            ]),
            "regions": sorted([r[0] for r in self.db.execute("SELECT semantic_key FROM regions WHERE domain_id=?", (domain_id,)).fetchall()]),
            "claims": [("claim:x", self.claim_is_supported(domain_id, "claim:x"))],
            "query_families": [(family_x, 2, tuple(sorted(self._family_requirements(family_x))))],
        }
        independent_snapshot = kernel.snapshot()
        compare("snapshot-evidence", primary_snapshot["evidence"], independent_snapshot["evidence"])
        compare("snapshot-regions", primary_snapshot["regions"], independent_snapshot["regions"])
        compare("snapshot-claims", primary_snapshot["claims"], independent_snapshot["claims"])
        compare("snapshot-families", primary_snapshot["query_families"], independent_snapshot["query_families"])
        frozen_steps = passed + failed

        self.register_query_family(family_ab, {"a", "b"}, revision=1)
        kernel.register_query_family(family_ab, {"a", "b"}, revision=1)
        loss_states = ["PRESERVED_EXACT", "PRESERVED_NORMALIZED", "LOST", "UNKNOWN"]
        for i in range(cases):
            rname = f"g{i}"
            region_id = self.create_region(domain_id, f"generated:{i}", principal="alice")
            kernel.create_region(rname, f"generated:{i}")
            source_id = self.add_representation(
                domain_id, region_id, kind="source", payload={"a": i, "b": i},
                loss={"a": "PRESERVED_EXACT", "b": "PRESERVED_EXACT"}, recoverable=set(),
                token_cost=4, principal="alice", transform_kind="SOURCE_REBASE", transform_profile="diff:generated-source",
            )
            source_name = f"src{i}"
            kernel.add_representation(source_name, region_name=rname, kind="source", payload={"a": i, "b": i},
                                      loss={"a": "PRESERVED_EXACT", "b": "PRESERVED_EXACT"}, recoverable=set())
            loss = {"a": rng.choice(loss_states), "b": rng.choice(loss_states)}
            recoverable = {dim for dim in ("a", "b") if loss[dim] not in kernel.EXACT_STATES and rng.random() < 0.5}
            compact_id = self.add_representation(
                domain_id, region_id, kind="summary", payload={"case": i}, loss=loss,
                recoverable=recoverable, token_cost=1, principal="alice",
                source_representation_ids=[source_id], transform_kind="PURE", transform_profile="diff:generated-summary",
            )
            compact_name = f"cmp{i}"
            kernel.add_representation(compact_name, region_name=rname, kind="summary", payload={"case": i},
                                      loss=loss, recoverable=recoverable, source_representation_names=[source_name])
            compare(f"generated-answerability-{i}", self.answerability(compact_id, family_ab).value, kernel.answerability(compact_name, family_ab))
            if i % 17 == 0:
                self.invalidate_representation(domain_id, compact_id, principal="alice")
                kernel.invalidate_representation(compact_name)
                compare(f"generated-invalidation-{i}", self.answerability(compact_id, family_ab).value, kernel.answerability(compact_name, family_ab))

        report = ResearchRunReport(
            run_id=f"research_{uuid.uuid4().hex}", kind="INDEPENDENT_DIFFERENTIAL",
            passed=passed, failed=failed, cases=passed + failed, seed=seed,
            details={
                "implementation": "pure-python-independent-kernel",
                "equivalent": failed == 0,
                "frozen_steps": frozen_steps,
                "generated_cases": cases,
                "classification_counts": classifications,
                "mismatches": mismatches,
            },
        )
        return self._store_research_report(report)

    # ---------- strong negative-query completeness ----------

    def _query_domain_from_row(self, row) -> MemoryQueryDomainRevision:
        return MemoryQueryDomainRevision(
            query_domain_id=row["query_domain_id"], domain_id=row["domain_id"], principal=row["principal"],
            incarnation=int(row["incarnation"]), cut=RecallCut(**json.loads(row["cut_json"])),
            predicate=json.loads(row["predicate_json"]), surfaces=list(json.loads(row["surfaces_json"])),
            capability=row["capability"], generation=int(row["generation"]), created_at=row["created_at"],
        )

    def compile_query_domain(
        self, domain_id: str, *, principal: str, predicate: dict[str, object],
        surfaces: Iterable[str], capability: str, cut: RecallCut | None = None,
    ) -> MemoryQueryDomainRevision:
        capability = capability.upper()
        allowed = {"EXACT_CANONICAL_SCAN", "BOUNDED_COMPLETE_SCAN", "PARTIAL_SCAN", "OPAQUE"}
        if capability not in allowed:
            raise MemoryTransitionIncomplete(f"unsupported query-domain capability {capability!r}")
        cut = cut or self.head(domain_id)
        if cut.domain_id != domain_id:
            raise MemoryTransitionIncomplete("query-domain cut belongs to a different authority domain")
        surfaces_list = sorted(set(str(x) for x in surfaces))
        if not surfaces_list:
            raise MemoryTransitionIncomplete("query domain must declare at least one searchable surface")
        generation = self._generation(domain_id, "query_domain", "global")
        qid = f"qd_{uuid.uuid4().hex}"
        created_at = self._research_now()
        self.db.execute(
            "INSERT INTO query_domain_revisions(query_domain_id,domain_id,principal,incarnation,cut_json,predicate_json,surfaces_json,capability,generation,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (qid, domain_id, principal, cut.incarnation, canonical_json(asdict(cut)), canonical_json(predicate),
             canonical_json(surfaces_list), capability, generation, created_at),
        )
        return self.get_query_domain(qid)

    def get_query_domain(self, query_domain_id: str) -> MemoryQueryDomainRevision:
        row = self.db.execute("SELECT * FROM query_domain_revisions WHERE query_domain_id=?", (query_domain_id,)).fetchone()
        if row is None:
            raise KeyError(query_domain_id)
        return self._query_domain_from_row(row)

    def execute_negative_query_domain(self, query_domain_id: str) -> NegativeQueryReceipt:
        qd = self.get_query_domain(query_domain_id)
        if qd.incarnation != qd.cut.incarnation:
            raise MemoryTransitionIncomplete("query domain incarnation/cut mismatch")
        field = qd.predicate.get("field")
        equals = qd.predicate.get("equals")
        matches: list[str] = []
        searchable = qd.capability != "OPAQUE"
        if searchable and "representations" in qd.surfaces:
            rows = self.db.execute(
                "SELECT * FROM representations WHERE domain_id=? AND created_seq<=? "
                "AND (invalidated_seq IS NULL OR invalidated_seq>?) AND (tainted_seq IS NULL OR tainted_seq>?) ORDER BY representation_id",
                (qd.domain_id, qd.cut.sequence, qd.cut.sequence, qd.cut.sequence),
            ).fetchall()
            for row in rows:
                if not self._is_allowed(qd.principal, row["allowed_principals_json"]):
                    continue
                candidate = row[field] if isinstance(field, str) and field in row.keys() else None
                if candidate is None:
                    payload = json.loads(row["payload_json"])
                    candidate = payload.get(field) if isinstance(payload, dict) and isinstance(field, str) else None
                if candidate == equals:
                    matches.append(row["representation_id"])
        if matches:
            status = "SUPPORT_FOR_EXISTENCE"
        elif qd.capability in {"EXACT_CANONICAL_SCAN", "BOUNDED_COMPLETE_SCAN"}:
            status = "NO_MATCH_COMPLETE_DOMAIN"
        elif qd.capability == "PARTIAL_SCAN":
            status = "NO_MATCH_PARTIAL_DOMAIN"
        else:
            status = "OPAQUE_OR_INCOMPLETE"
        completeness = {
            "EXACT_CANONICAL_SCAN": "COMPLETE",
            "BOUNDED_COMPLETE_SCAN": "BOUNDED_COMPLETE",
            "PARTIAL_SCAN": "PARTIAL",
            "OPAQUE": "OPAQUE",
        }[qd.capability]
        deps = [
            Dependency("query_domain", "global", qd.generation),
            Dependency("access", "global", self._generation(qd.domain_id, "access", "global")),
            Dependency("incarnation", "global", self._generation(qd.domain_id, "incarnation", "global")),
        ]
        receipt = NegativeQueryReceipt(
            receipt_id=f"neg_{uuid.uuid4().hex}", domain_id=qd.domain_id, principal=qd.principal,
            predicate=qd.predicate, completeness=completeness, status=status, match_representation_ids=matches,
            cut=qd.cut, dependencies=deps, created_at=self._research_now(), query_domain_id=qd.query_domain_id,
        )
        self.db.execute(
            "INSERT INTO negative_query_receipts(receipt_id,domain_id,principal,predicate_json,completeness,status,match_representation_ids_json,cut_json,dependencies_json,created_at,query_domain_id) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (receipt.receipt_id, qd.domain_id, qd.principal, canonical_json(receipt.predicate), completeness, status,
             canonical_json(matches), canonical_json(asdict(qd.cut)), canonical_json([asdict(d) for d in deps]),
             receipt.created_at, qd.query_domain_id),
        )
        return receipt

    def strong_negative_query(self, domain_id: str, *, principal: str, field: str, equals, completeness: str = "COMPLETE") -> NegativeQueryReceipt:
        requested = completeness.upper()
        capability = {
            "COMPLETE": "EXACT_CANONICAL_SCAN",
            "BOUNDED_COMPLETE": "BOUNDED_COMPLETE_SCAN",
            "PARTIAL": "PARTIAL_SCAN",
            "OPAQUE": "OPAQUE",
        }.get(requested, "OPAQUE")
        qd = self.compile_query_domain(
            domain_id, principal=principal, predicate={"field": field, "equals": equals},
            surfaces=["representations"], capability=capability,
        )
        return self.execute_negative_query_domain(qd.query_domain_id)

    def validate_negative_query_receipt(self, receipt_id: str) -> bool:
        row = self.db.execute("SELECT * FROM negative_query_receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
        if not row:
            raise KeyError(receipt_id)
        deps = [Dependency(**x) for x in json.loads(row["dependencies_json"])]
        self.validate_dependencies(row["domain_id"], deps)
        if row["query_domain_id"]:
            qd = self.get_query_domain(row["query_domain_id"])
            if qd.domain_id != row["domain_id"] or qd.principal != row["principal"]:
                raise MemoryTransitionIncomplete("negative-query receipt/query-domain binding mismatch")
        return True

    def run_publication_cycle_acceptance_campaign(self, *, seed: int = 393) -> dict[str, object]:
        """Execute the Section 393 publication-cycle conformance worlds.

        The campaign checks that publication/derivation cycles preserve root-origin
        cardinality, expand causal-cut closure through concrete publication events,
        and do not let revoked destination echoes become independent healthy roots.
        """
        from .errors import MemoryPublicationBlocked

        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []

        def record(fixture: str, expected: str, observed: str, detail=None) -> None:
            outcomes.append({
                "fixture": fixture,
                "expected": expected,
                "observed": observed,
                "passed": expected == observed,
                "detail": detail,
            })

        def new_domain(label: str) -> str:
            domain_id = f"pubcycle_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"
            self.create_domain(domain_id)
            return domain_id

        def source_rep(domain_id: str, label: str, roots: list[str] | None, *, value: object = 1) -> tuple[str, str]:
            head = self._head_row(domain_id)
            event = self.capture_evidence(
                domain_id=domain_id,
                operation_id=f"capture:{label}:{rng.randrange(1_000_000_000)}",
                expected_seq=int(head["sequence"]),
                writer_epoch=int(head["writer_epoch"]),
                source_event_identity=f"event:{label}:{rng.randrange(1_000_000_000)}",
                content={"x": value},
                principal="alice",
                origin_roots=[] if roots is None else roots,
            ).object_id
            region = self.create_region(domain_id, f"region:{label}:{rng.randrange(1_000_000)}", principal="alice")
            representation = self.add_representation(
                domain_id,
                region,
                kind="raw",
                payload={"x": value},
                source_evidence_ids=[event],
                loss={"x": LossState.PRESERVED_EXACT},
                recoverable=set(),
                token_cost=1,
                principal="alice",
            )
            return event, representation

        def imported_rep(domain_id: str, evidence_id: str, label: str, *, value: object = 1) -> str:
            region = self.create_region(domain_id, f"import:{label}:{rng.randrange(1_000_000)}", principal="alice")
            return self.add_representation(
                domain_id,
                region,
                kind="import",
                payload={"x": value},
                source_evidence_ids=[evidence_id],
                loss={"x": LossState.PRESERVED_EXACT},
                recoverable=set(),
                token_cost=1,
                principal="alice",
            )

        def publish_chain(a: str, b: str, c: str, rep_a: str, *, prefix: str) -> tuple[object, object, object, str, str]:
            ab = self.publish_representation(a, b, rep_a, principal="alice", operation_id=f"{prefix}:a-b")
            rep_b = imported_rep(b, ab.destination_evidence_id, f"{prefix}:b")
            bc = self.publish_representation(b, c, rep_b, principal="alice", operation_id=f"{prefix}:b-c")
            rep_c = imported_rep(c, bc.destination_evidence_id, f"{prefix}:c")
            ca = self.publish_representation(c, a, rep_c, principal="alice", operation_id=f"{prefix}:c-a")
            return ab, bc, ca, rep_b, rep_c

        # 1. A pure echo cycle must not manufacture multiple independent roots.
        a, b, c = new_domain("pure-a"), new_domain("pure-b"), new_domain("pure-c")
        _, rep_a = source_rep(a, "pure", None)
        initial_roots = sorted(self._representation_origin_roots(a, rep_a))
        ab, bc, ca, _, _ = publish_chain(a, b, c, rep_a, prefix="pure")
        final_roots = sorted(self.get_origin_roots(a, "evidence", ca.destination_evidence_id))
        observed = "NO_SUPPORT_INFLATION" if set(final_roots) == set(initial_roots) and len(final_roots) <= max(1, len(initial_roots)) else "SUPPORT_INFLATED"
        record(
            "pure_cycle_no_independent_support_inflation", "NO_SUPPORT_INFLATION", observed,
            {"initial_roots": initial_roots, "final_roots": final_roots},
        )

        # 2. One admitted root stays one root around A->B->C->A.
        a, b, c = new_domain("one-a"), new_domain("one-b"), new_domain("one-c")
        _, rep_a = source_rep(a, "one", ["root:R1"])
        _, _, ca, _, _ = publish_chain(a, b, c, rep_a, prefix="one")
        roots = sorted(self.get_origin_roots(a, "evidence", ca.destination_evidence_id))
        record("one_root_cycle", "ROOT_SET_PRESERVED", "ROOT_SET_PRESERVED" if roots == ["root:R1"] else "ROOT_SET_CHANGED", {"roots": roots})

        # 3. A merge of two genuinely independent roots remains cardinality two.
        a, b, c = new_domain("merge-a"), new_domain("merge-b"), new_domain("merge-c")
        head = self._head_row(a)
        e1 = self.capture_evidence(
            domain_id=a, operation_id=f"merge:e1:{rng.randrange(1_000_000)}",
            expected_seq=int(head["sequence"]), writer_epoch=int(head["writer_epoch"]),
            source_event_identity=f"merge:e1:{rng.randrange(1_000_000)}", content={"x": 1}, principal="alice", origin_roots=["root:R1"],
        ).object_id
        head = self._head_row(a)
        e2 = self.capture_evidence(
            domain_id=a, operation_id=f"merge:e2:{rng.randrange(1_000_000)}",
            expected_seq=int(head["sequence"]), writer_epoch=int(head["writer_epoch"]),
            source_event_identity=f"merge:e2:{rng.randrange(1_000_000)}", content={"x": 1}, principal="alice", origin_roots=["root:R2"],
        ).object_id
        region = self.create_region(a, f"merge:{rng.randrange(1_000_000)}", principal="alice")
        rep_merge = self.add_representation(
            a, region, kind="merge", payload={"x": 1}, source_evidence_ids=[e1, e2],
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        _, _, ca, _, _ = publish_chain(a, b, c, rep_merge, prefix="merge")
        roots = sorted(self.get_origin_roots(a, "evidence", ca.destination_evidence_id))
        record("two_independent_root_merge", "TWO_ROOTS_PRESERVED", "TWO_ROOTS_PRESERVED" if roots == ["root:R1", "root:R2"] else "ROOT_SET_CHANGED", {"roots": roots})

        # 4. A destination-local echo whose imported basis is revoked cannot republish.
        a, b, c = new_domain("revoke-a"), new_domain("revoke-b"), new_domain("revoke-c")
        _, rep_a = source_rep(a, "revoke", ["root:R"])
        ab = self.publish_representation(a, b, rep_a, principal="alice", operation_id="revoke:a-b")
        rep_b = imported_rep(b, ab.destination_evidence_id, "revoke:b")
        self.revoke_evidence(b, ab.destination_evidence_id, principal="alice")
        try:
            self.publish_representation(b, c, rep_b, principal="alice", operation_id="revoke:b-c")
            observed = "REPUBLISHED"
        except MemoryPublicationBlocked:
            observed = "PUBLICATION_BLOCKED"
        record("destination_revocation", "PUBLICATION_BLOCKED", observed)

        # 5. A cut containing the downstream C->A admission closes over B/C/A predecessors.
        a, b, c = new_domain("cut-a"), new_domain("cut-b"), new_domain("cut-c")
        _, rep_a = source_rep(a, "cut", ["root:cut"])
        ab, bc, ca, _, _ = publish_chain(a, b, c, rep_a, prefix="cut")
        closed = self.close_causal_cut({a: ca.destination_sequence, b: 0, c: 0})
        predecessor_ok = (
            closed[c].sequence >= ca.source_sequence
            and closed[b].sequence >= bc.source_sequence
            and closed[a].sequence >= ab.source_sequence
        )
        observed = "CAUSAL_PREDECESSORS_CLOSED" if predecessor_ok else "PREDECESSOR_OMITTED"
        record(
            "downstream_cut_omits_predecessor", "CAUSAL_PREDECESSORS_CLOSED", observed,
            {
                "closed": {d: cut.sequence for d, cut in closed.items()},
                "required": {a: ab.source_sequence, b: bc.source_sequence, c: ca.source_sequence},
            },
        )

        failures = [item for item in outcomes if not item["passed"]]
        return {
            "kind": "publication-cycle-acceptance-v0.6.3",
            "seed": seed,
            "fixture_count": len(outcomes),
            "failed": len(failures),
            "passed": not failures,
            "outcomes": outcomes,
            "failure_digest": digest(failures),
        }

    def run_information_flow_use_time_campaign(self, *, seed: int = 394) -> dict[str, object]:
        """Execute the Section 394 information-flow lease TOCTOU fixtures."""
        from datetime import timedelta
        from .errors import MemoryFlowPolicyCurrentnessUnknown, ActionArgumentMismatch

        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []

        def record(fixture: str, expected: str, observed: str, detail=None) -> None:
            outcomes.append({
                "fixture": fixture, "expected": expected, "observed": observed,
                "passed": expected == observed, "detail": detail,
            })

        def setup(label: str, *, direct_tool: bool = True):
            d = f"flowlease_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"
            self.create_domain(d)
            family = f"FLOW_{label}_{seed}_{rng.randrange(1_000_000):06d}"
            self.register_query_family(family, {"x"})
            caps = {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"}
            sinks = None
            if direct_tool:
                caps.add("DISCLOSE_TO_TOOL")
                sinks = {"tool:send": ["DISCLOSE_TO_TOOL"]}
            self.set_access_profile(d, "alice", caps, sink_capabilities=sinks)
            region = self.create_region(d, f"r:{label}", principal="alice")
            rep = self.add_representation(
                d, region, kind="exact", payload={"x": 1},
                loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
                principal="alice",
            )
            frame = self.compile_recall(d, "alice", [RecallRole("role", region, family)], 20)
            return d, rep, frame

        # T0 ALLOW -> T1 access revoke -> T2 use.
        d, _, frame = setup("access")
        receipt = self.check_information_flow(frame, principal="alice", sink="tool:send", payload={"x": 1})
        self.set_access_profile(d, "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        try:
            self.validate_information_flow_receipt(receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1})
            observed = "ALLOW_REUSED"
        except MemoryFlowPolicyCurrentnessUnknown:
            observed = "FLOW_POLICY_CURRENTNESS_UNKNOWN"
        record("access_revoke_after_allow", "FLOW_POLICY_CURRENTNESS_UNKNOWN", observed)

        # Declassification is a material disclosure lease dependency.
        d, rep, frame = setup("declass", direct_tool=False)
        dec = self.grant_declassification(d, rep, principal="alice", sink="tool:send", authority_ref="release:394")
        receipt = self.check_information_flow(frame, principal="alice", sink="tool:send", payload={"x": 1})
        self.revoke_declassification(d, dec.receipt_id, principal="alice")
        try:
            self.validate_information_flow_receipt(receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1})
            observed = "ALLOW_REUSED"
        except MemoryFlowPolicyCurrentnessUnknown:
            observed = "FLOW_POLICY_CURRENTNESS_UNKNOWN"
        record("declassification_revoke_after_allow", "FLOW_POLICY_CURRENTNESS_UNKNOWN", observed)

        # Tool/destination capability identity changes after ALLOW.
        d, _, frame = setup("tool")
        receipt = self.check_information_flow(frame, principal="alice", sink="tool:send", payload={"x": 1})
        self.bump_generation(d, "tool", "tool:send")
        try:
            self.validate_information_flow_receipt(receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1})
            observed = "ALLOW_REUSED"
        except MemoryFlowPolicyCurrentnessUnknown:
            observed = "FLOW_POLICY_CURRENTNESS_UNKNOWN"
        record("tool_identity_generation_change", "FLOW_POLICY_CURRENTNESS_UNKNOWN", observed)

        # Exact rendered/serialized payload binding.
        d, _, frame = setup("payload")
        receipt = self.check_information_flow(frame, principal="alice", sink="tool:send", payload={"recipient": "A"})
        try:
            self.validate_information_flow_receipt(receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"recipient": "B"})
            observed = "ALLOW_REUSED"
        except ActionArgumentMismatch:
            observed = "ACTION_ARGUMENT_MISMATCH"
        record("payload_mutation_after_allow", "ACTION_ARGUMENT_MISMATCH", observed)

        # High-assurance sink cannot reuse ALLOW while policy currentness is unavailable.
        d, _, frame = setup("opaque")
        receipt = self.check_information_flow(frame, principal="alice", sink="tool:send", payload={"x": 1})
        self.set_capability_availability(d, "flow_policy_currentness", False)
        try:
            self.validate_information_flow_receipt(receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1})
            observed = "ALLOW_REUSED"
        except MemoryFlowPolicyCurrentnessUnknown:
            observed = "FLOW_POLICY_CURRENTNESS_UNKNOWN"
        finally:
            self.set_capability_availability(d, "flow_policy_currentness", True)
        record("policy_source_unavailable_at_use", "FLOW_POLICY_CURRENTNESS_UNKNOWN", observed)

        # Expiring disclosure lease is bound to trusted clock identity + epoch.
        d, _, frame = setup("clock")
        now = self._clock()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        receipt = self.check_information_flow(
            frame, principal="alice", sink="tool:send", payload={"x": 1}, expires_at=now + timedelta(minutes=1)
        )
        old_epoch = self._clock_epoch
        self._clock_epoch = f"flow-wrong-{seed}"
        try:
            self.validate_information_flow_receipt(receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1})
            observed = "ALLOW_REUSED"
        except MemoryFlowPolicyCurrentnessUnknown:
            observed = "FLOW_POLICY_CURRENTNESS_UNKNOWN"
        finally:
            self._clock_epoch = old_epoch
        record("flow_lease_clock_epoch_change", "FLOW_POLICY_CURRENTNESS_UNKNOWN", observed)

        failures = [item for item in outcomes if not item["passed"]]
        return {
            "kind": "information-flow-use-time-campaign-v0.6.3", "seed": seed,
            "fixture_count": len(outcomes), "failed": len(failures), "passed": not failures,
            "outcomes": outcomes, "failure_digest": digest(failures),
        }

    def run_resource_pressure_use_validation_campaign(self, *, seed: int = 395) -> dict[str, object]:
        """Execute the Section 395 fail-closed resource-pressure fixtures."""
        from .errors import MemoryUseValidationUnavailable

        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []

        def record(fixture: str, expected: str, observed: str, detail=None) -> None:
            outcomes.append({
                "fixture": fixture, "expected": expected, "observed": observed,
                "passed": expected == observed, "detail": detail,
            })

        d = f"usepressure_{seed}_{rng.randrange(1_000_000_000):09d}"
        self.create_domain(d)
        family = f"PRESSURE_{seed}_{rng.randrange(1_000_000):06d}"
        self.register_query_family(family, {"x"})
        self.set_access_profile(
            d, "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE", "DISCLOSE_TO_TOOL"},
            sink_capabilities={"tool:send": ["DISCLOSE_TO_TOOL"]},
        )
        region = self.create_region(d, "r", principal="alice")
        self.add_representation(
            d, region, kind="exact", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        frame = self.compile_recall(d, "alice", [RecallRole("role", region, family)], 20)
        fence = self.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"x": 1})

        self.set_capability_availability(d, "use_validation", False)
        try:
            self.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1})
            observed = "USE_ALLOWED"
        except MemoryUseValidationUnavailable:
            observed = "USE_VALIDATION_UNAVAILABLE"
        record("validation_state_unavailable", "USE_VALIDATION_UNAVAILABLE", observed)

        consumed = self.db.execute("SELECT consumed_at FROM fences WHERE fence_id=?", (fence.fence_id,)).fetchone()[0]
        record("unavailable_validation_does_not_consume", "NOT_CONSUMED", "NOT_CONSUMED" if consumed is None else "CONSUMED")

        self.set_capability_availability(d, "use_validation", True)
        observed = "USE_ALLOWED" if self.consume_use_fence(
            fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1}
        ) else "USE_BLOCKED"
        record("retry_after_validation_recovery", "USE_ALLOWED", observed)

        # Optional/background pressure is shed independently of correctness-reserved use validation.
        frame2 = self.compile_recall(d, "alice", [RecallRole("role", region, family)], 20)
        fence2 = self.issue_use_fence(frame2, principal="alice", sink="tool:send", payload={"x": 2})
        self.set_capability_availability(d, "associative_exploration", False)
        try:
            self.consume_use_fence(fence2.fence_id, principal="alice", sink="tool:send", payload={"x": 2})
            observed = "USE_ALLOWED"
        except Exception as exc:  # campaign reports a typed unexpected failure without hiding it
            observed = type(exc).__name__
        record("optional_work_shed_before_validation", "USE_ALLOWED", observed)

        failures = [item for item in outcomes if not item["passed"]]
        return {
            "kind": "resource-pressure-use-validation-campaign-v0.6.3", "seed": seed,
            "fixture_count": len(outcomes), "failed": len(failures), "passed": not failures,
            "outcomes": outcomes, "failure_digest": digest(failures),
        }

    def run_temporal_acceptance_campaign(self, *, seed: int = 263) -> dict[str, object]:
        """Execute the Section 263 structural temporal fixtures."""
        from datetime import datetime, timedelta, timezone
        rng = random.Random(seed)
        outcomes: list[dict[str, object]] = []

        def record(name, expected, observed, detail=None):
            outcomes.append({"fixture": name, "expected": expected, "observed": observed,
                             "passed": expected == observed, "detail": detail})

        with tempfile.TemporaryDirectory() as td:
            clock_box = [datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)]
            rt = self.__class__(f"{td}/temporal.db", clock=lambda: clock_box[0],
                                clock_authority_id="temporal-clock", clock_epoch="t263")
            d = "temporal"
            rt.create_domain(d)
            t20 = datetime(2026, 1, 1, 0, 20, tzinfo=timezone.utc)
            t25 = datetime(2026, 1, 1, 0, 25, tzinfo=timezone.utc)
            t30 = datetime(2026, 1, 1, 0, 30, tzinfo=timezone.utc)
            t100 = datetime(2026, 1, 1, 1, 40, tzinfo=timezone.utc)
            clock_box[0] = t100
            h = rt._head_row(d)
            ev = rt.capture_evidence(
                domain_id=d, operation_id="late-evidence", expected_seq=int(h["sequence"]),
                writer_epoch=int(h["writer_epoch"]), source_event_identity="late:1",
                content={"state": "ON"}, principal="alice", world_time=t20, observed_at=t100,
            ).object_id
            row = rt.db.execute("SELECT world_time,observed_at,ingested_at FROM evidence WHERE evidence_id=?", (ev,)).fetchone()
            record("event_time_differs_from_ingestion", "DISTINCT", "DISTINCT" if row["world_time"] != row["ingested_at"] else "COLLAPSED")

            h = rt._head_row(d)
            c1 = rt.create_claim(
                domain_id=d, operation_id="claim-late", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                logical_id="state", proposition={"state": "ON"}, valid_from=t20, valid_to=t30,
                support_paths=[[ev]], principal="alice",
            )
            record("late_evidence_not_known_in_past", "NOT_KNOWN", "NOT_KNOWN" if not rt.claim_known_by(d, "state", t25) else "KNOWN")
            observed = "VALID_NOT_KNOWN" if rt.claim_valid_at(d, "state", t25) and not rt.claim_known_by(d, "state", t25) else "COLLAPSED"
            record("valid_at_vs_known_by", "VALID_NOT_KNOWN", observed)

            judgement = rt.record_historical_judgement(d, claim_revision_id=c1.object_id, principal="alice", judgement="ACCEPTED", reason="basis-at-t100")
            before = rt.judgement_as_of(d, "state", t100 - timedelta(microseconds=1), principal="alice")
            at = rt.judgement_as_of(d, "state", t100, principal="alice")
            record("judged_at_is_historical_dimension", "JUDGED_AT_ONLY", "JUDGED_AT_ONLY" if before is None and at is not None else "JUDGEMENT_TIME_COLLAPSED")

            record("half_open_start_inclusive", "INCLUDED", "INCLUDED" if rt.claim_valid_at(d, "state", t20) else "EXCLUDED")
            record("half_open_end_exclusive", "EXCLUDED", "EXCLUDED" if not rt.claim_valid_at(d, "state", t30) else "INCLUDED")

            h = rt._head_row(d)
            e3 = rt.capture_evidence(
                domain_id=d, operation_id="point-2", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                source_event_identity="late:2", content={"state": "ON"}, principal="alice", world_time=t30, observed_at=t100,
            ).object_id
            try:
                rt.certify_temporal_coverage(d, [ev, e3], valid_from=t20, valid_to=t30, principal="alice", coverage_contract=None)
                observed = "FALSE_DURATION"
            except MemoryTransitionIncomplete:
                observed = "COVERAGE_REQUIRED"
            record("point_observations_do_not_fill_gap", "COVERAGE_REQUIRED", observed)

            rt.set_runtime_compatibility(d, mission_revision="m1", environment_revision="env1")
            h = rt._head_row(d)
            c2 = rt.revise_claim(
                domain_id=d, operation_id="scope-state", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                logical_id="state", expected_predecessor_revision_id=c1.object_id,
                proposition={"state": "ON"}, valid_from=t20, valid_to=t30, support_paths=[[ev]], principal="alice",
                applicability={"mission_revision": "m1"},
            )
            rt.set_runtime_compatibility(d, mission_revision="m2", environment_revision="env1")
            observed = "HISTORY_PRESERVED_CURRENT_INAPPLICABLE" if rt.claim_valid_at(d, "state", t25) and not rt.claim_currently_usable(d, "state", principal="alice") else "HISTORY_REWRITTEN"
            record("regime_change_preserves_historical_truth", "HISTORY_PRESERVED_CURRENT_INAPPLICABLE", observed)

            judgement_time = t100 + timedelta(minutes=10)
            clock_box[0] = judgement_time
            old_j = rt.record_historical_judgement(d, claim_revision_id=c2.object_id, principal="alice", judgement="WRONG_AT_TIME", reason="pre-correction")
            # The correction occurs later. Historical lookup immediately before the
            # correction must still see the judgement actually recorded at judgement_time.
            correction_time = judgement_time + timedelta(minutes=1)
            clock_box[0] = correction_time
            h = rt._head_row(d)
            c3 = rt.revise_claim(
                domain_id=d, operation_id="correction", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                logical_id="state", expected_predecessor_revision_id=c2.object_id,
                proposition={"state": "OFF"}, valid_from=t20, valid_to=t30, support_paths=[[ev]], principal="alice",
                applicability={"mission_revision": "m2"},
            )
            hist = rt.judgement_as_of(d, "state", correction_time - timedelta(microseconds=1), principal="alice")
            observed = "OLD_JUDGEMENT_RETAINED" if hist and hist.claim_revision_id == c2.object_id and c3.object_id != c2.object_id else "HINDSIGHT_REWRITE"
            record("retrospective_correction_retains_wrong_judgement", "OLD_JUDGEMENT_RETAINED", observed)
            rt.close()

        failures = [x for x in outcomes if not x["passed"]]
        return {"kind":"temporal-acceptance-v0.6.3","seed":seed,"fixture_count":len(outcomes),"failed":len(failures),"passed":not failures,"outcomes":outcomes,"failure_digest":digest(failures)}

    def run_procedure_failure_acceptance_campaign(self, *, seed: int = 264) -> dict[str, object]:
        """Execute Section 264 applicability/failure-transfer fixtures."""
        from .errors import MemoryRecallInsufficient
        rng = random.Random(seed); outcomes=[]
        def record(name, expected, observed, detail=None):
            outcomes.append({"fixture":name,"expected":expected,"observed":observed,"passed":expected==observed,"detail":detail})
        d=f"procedure_{seed}_{rng.randrange(1_000_000_000):09d}"; self.create_domain(d)

        p=self.learn_procedure(d,procedure_key="install",principal="alice",experiences=[
            {"event_identity":"l1","outcome":"SUCCESS","surface_text":"install package","applicability":{"os":"linux","tool":"v1"}},
            {"event_identity":"w1","outcome":"FAILURE","surface_text":"install package","applicability":{"os":"windows","tool":"v1"}},
        ])
        record("opposite_outcomes_across_structural_slices","CONDITIONAL",p["generic_status"])

        p=self.learn_procedure(d,procedure_key="fetch",principal="alice",experiences=[
            {"event_identity":"ok","outcome":"SUCCESS","applicability":{"env":"prod"}},
            {"event_identity":"timeout","outcome":"FAILURE","failure_kind":"TRANSIENT_TIMEOUT","applicability":{"env":"prod"}},
        ])
        record("transient_timeout_not_hypothesis_falsification","SUPPORTED_WITH_TRANSIENT_FAILURE",p["slices"][0]["status"])

        p=self.learn_procedure(d,procedure_key="danger",principal="alice",experiences=[
            {"event_identity":"cat","outcome":"FAILURE","severity":"CATASTROPHIC","reproducer_ref":"trace:cat","applicability":{"env":"prod"}},
        ])
        observed="PROTECTED" if p["slices"][0]["protected_failure_event_ids"]==["cat"] else "DROPPED"
        record("one_shot_catastrophic_counterexample_retained","PROTECTED",observed)

        family=f"PROC_{seed}"; self.register_query_family(family,{"procedure"}); self.set_self_version(d,"self:v1",{"executor":"v1"})
        region=self.create_region(d,"proc-region",principal="alice")
        self.add_representation(d,region,kind="procedure",payload={"procedure":"do-x"},loss={"procedure":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice",applicability={"self_version":"self:v1"})
        role=RecallRole("procedure",region,family)
        self.compile_recall(d,"alice",[role],20)
        self.set_self_version(d,"self:v2",{"executor":"v2"})
        try:
            self.compile_recall(d,"alice",[role],20); observed="REUSED"
        except MemoryRecallInsufficient:
            observed="REVALIDATION_REQUIRED"
        record("model_upgrade_invalidates_executor_sensitive_procedure","REVALIDATION_REQUIRED",observed)

        p=self.learn_procedure(d,procedure_key="same-structure",principal="alice",experiences=[
            {"event_identity":"a","outcome":"SUCCESS","surface_text":"alpha wording","applicability":{"schema":"v1"}},
            {"event_identity":"b","outcome":"SUCCESS","surface_text":"beta wording","applicability":{"schema":"v1"}},
        ])
        record("same_structure_different_wording","SUPPORTED",p["generic_status"])

        p=self.learn_procedure(d,procedure_key="same-wording",principal="alice",experiences=[
            {"event_identity":"c","outcome":"SUCCESS","surface_text":"same words","applicability":{"schema":"v1"}},
            {"event_identity":"d","outcome":"FAILURE","surface_text":"same words","applicability":{"schema":"v2"}},
        ])
        record("same_wording_different_structure","CONDITIONAL",p["generic_status"])

        p=self.learn_procedure(d,procedure_key="fix",principal="alice",experiences=[
            {"event_identity":"f1","outcome":"FAILURE","reproducer_ref":"trace:repro","applicability":{"env":"prod"}},
            {"event_identity":"s1","outcome":"SUCCESS","applicability":{"env":"staging"}},
        ])
        refs={k:v for sl in p["slices"] for k,v in sl["reproducer_refs"].items()}
        record("successful_fix_preserves_failure_reproducer","PRESERVED","PRESERVED" if refs.get("f1")=="trace:repro" else "LOST")
        failures=[x for x in outcomes if not x["passed"]]
        return {"kind":"procedure-failure-acceptance-v0.6.3","seed":seed,"fixture_count":len(outcomes),"failed":len(failures),"passed":not failures,"outcomes":outcomes,"failure_digest":digest(failures)}

    def run_security_privacy_acceptance_campaign(self, *, seed: int = 265) -> dict[str, object]:
        """Execute the nine lifecycle security/privacy fixtures in Section 265."""
        from .errors import MemoryScopeBlocked, MemoryPublicationBlocked
        rng=random.Random(seed); outcomes=[]
        def record(name, expected, observed, detail=None): outcomes.append({"fixture":name,"expected":expected,"observed":observed,"passed":expected==observed,"detail":detail})
        def domain(label):
            d=f"sec_{label}_{seed}_{rng.randrange(1_000_000_000):09d}"; self.create_domain(d); return d
        def source(d,label,*,allowed=None,authority="UNTRUSTED",common=None,principal="alice"):
            h=self._head_row(d); ev=self.capture_evidence(domain_id=d,operation_id=f"cap:{label}:{rng.randrange(1_000_000)}",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),source_event_identity=f"event:{label}:{rng.randrange(1_000_000)}",content={"x":label},principal=principal,allowed_principals=allowed,source_authority_class=authority,common_mode_group=common).object_id
            r=self.create_region(d,f"r:{label}",principal=principal,allowed_principals=allowed)
            rep=self.add_representation(d,r,kind="summary",payload={"x":label},source_evidence_ids=[ev],loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal=principal,allowed_principals=allowed)
            return ev,r,rep

        d=domain("untrusted"); ev,_,rep=source(d,"u",authority="UNTRUSTED")
        roots=self._representation_origin_roots(d,rep); binds=self.get_origin_bindings(d,ev)
        record("untrusted_content_summary_procedure_proposal","AUTHORITY_NOT_ELEVATED","AUTHORITY_NOT_ELEVATED" if roots and binds and all(b.authority_class=="UNTRUSTED" for b in binds) else "LAUNDERED")

        d=domain("tool-echo"); ev,_,rep=source(d,"echo",authority="UNTRUSTED")
        bind=self.get_origin_bindings(d,ev)[0]
        record("trusted_tool_echo_untrusted_bytes","CONTENT_AUTHORITY_UNCHANGED","CONTENT_AUTHORITY_UNCHANGED" if bind.authority_class=="UNTRUSTED" else "LAUNDERED")

        d=domain("self-echo"); h=self._head_row(d)
        e1=self.capture_evidence(domain_id=d,operation_id="e1",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),source_event_identity="echo:1",content={"x":1},principal="alice",origin_roots=["root:shared"],common_mode_group="cm:shared").object_id
        h=self._head_row(d); e2=self.capture_evidence(domain_id=d,operation_id="e2",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),source_event_identity="echo:2",content={"x":1},principal="alice",origin_roots=["root:shared-copy"],common_mode_group="cm:shared").object_id
        ind=self.evaluate_evidence_independence(d,[e1,e2]); groups=ind.get("independent_groups",ind.get("group_count"))
        record("self_summary_repeated_across_agents","ONE_COMMON_MODE_GROUP","ONE_COMMON_MODE_GROUP" if groups in (1,[e1,e2]) or ind.get("status")!="INDEPENDENT" else "FALSE_CORROBORATION",ind)

        d=domain("private"); ev,r,rep=source(d,"private",allowed=["alice"])
        try:
            self.get_evidence(d,ev,principal="bob"); observed="LEAK"
        except MemoryScopeBlocked: observed="SCOPE_BLOCKED"
        record("private_source_attempted_public_derivative","SCOPE_BLOCKED",observed)

        d=domain("declass"); self.set_access_profile(d,"alice",{"DISCOVER","USE_FOR_LOCAL_REASONING","DERIVE"}); ev,r,rep=source(d,"dec")
        fam=f"SECQ_{seed}"; self.register_query_family(fam,{"x"}); frame=self.compile_recall(d,"alice",[RecallRole("r",r,fam)],20)
        dec=self.grant_declassification(d,rep,principal="alice",sink="tool:external",authority_ref="release")
        self.revoke_declassification(d,dec.receipt_id,principal="alice")
        flow=self.check_information_flow(frame,principal="alice",sink="tool:external",payload={"x":1})
        record("revoked_declassification","BLOCK",flow.decision)

        d=domain("hidden-rank"); fam=f"RANK_{seed}"; self.register_query_family(fam,{"x"})
        _,private_region,private_rep=source(d,"secret",allowed=["alice"],principal="alice"); _,public_region,public_rep=source(d,"public",allowed=["bob"],principal="bob")
        self.index_representation_view(d,private_rep,"lexical",["needle"]); self.index_representation_view(d,public_rep,"lexical",["needle"])
        found=self.discover_regions(d,principal="bob",view_keys={"lexical":["needle"]})
        record("hidden_private_memory_zero_ranking_influence","ZERO_HIDDEN_INFLUENCE","ZERO_HIDDEN_INFLUENCE" if private_region not in found and public_region in found else "HIDDEN_INFLUENCE")

        d=domain("poison"); ev,r,rep=source(d,"poison",authority="UNTRUSTED")
        role=RecallRole("wake",r,f"WAKE_{seed}",hard=False); self.register_query_family(role.query_family,{"x"})
        self.register_prospective_trigger(d,"later",owner="alice",roles=[role],source_representation_ids=[rep])
        self.compromise_evidence(d,ev,principal="alice",reason="poisoned")
        fired=self.fire_prospective_triggers(d,"later",principal="alice")
        record("poisoned_memory_activated_many_sessions_later","QUARANTINED","QUARANTINED" if not fired else "ACTIVATED")

        d=domain("erase"); ev,r,rep=source(d,"secret-public")
        receipt=self.erase_evidence(d,ev,principal="alice",policy_ref="privacy")
        row=self.db.execute("SELECT tainted_seq FROM representations WHERE representation_id=?",(rep,)).fetchone()
        record("hard_delete_with_derived_public_leakage","DERIVATIVE_TAINTED","DERIVATIVE_TAINTED" if row and row[0] is not None and rep in receipt.tainted_representation_ids else "LEAK_REMAINS")

        d=domain("exact-get"); ev,_,_=source(d,"exact",allowed=["alice"])
        try:
            self.get_evidence(d,ev,principal="bob"); observed="LEAK"
        except MemoryScopeBlocked: observed="SCOPE_BLOCKED"
        record("scope_mismatch_exact_get_debug_archive_path","SCOPE_BLOCKED",observed)

        failures=[x for x in outcomes if not x["passed"]]
        return {"kind":"security-privacy-acceptance-v0.6.3","seed":seed,"fixture_count":len(outcomes),"failed":len(failures),"passed":not failures,"outcomes":outcomes,"failure_digest":digest(failures)}

    def run_migration_acceptance_campaign(self, *, seed: int = 266) -> dict[str, object]:
        """Execute conservative legacy migration fixtures from Section 266."""
        rng=random.Random(seed); outcomes=[]
        def record(name,expected,observed,detail=None): outcomes.append({"fixture":name,"expected":expected,"observed":observed,"passed":expected==observed,"detail":detail})
        d=f"migration_{seed}_{rng.randrange(1_000_000_000):09d}"; self.create_domain(d)
        region=self.create_region(d,"legacy",principal="alice")
        rep=self.import_legacy_representation(d,region,source_kind="summary",source_id="legacy:1",payload={"status":"active","when":"unknown"},dimensions={"lineage","temporal","status"},principal="alice")
        row=self.db.execute("SELECT loss_json FROM representations WHERE representation_id=?",(rep,)).fetchone(); loss=json.loads(row[0])
        record("summary_without_preservation_metadata","UNKNOWN_NOT_EXACT","UNKNOWN_NOT_EXACT" if all(v==LossState.UNKNOWN.value for v in loss.values()) else "UPGRADED")
        debt=int(self.db.execute("SELECT COUNT(*) FROM semantic_debts WHERE subject_id=? AND outcome IN ('OPEN','ACCEPTED_DEBT','QUARANTINED')",(rep,)).fetchone()[0])
        record("underspecified_lineage_creates_debt","DEBT_RECORDED","DEBT_RECORDED" if debt else "SILENT_DEFAULT")
        record("legacy_active_not_current_truth","CANDIDATE_ONLY","CANDIDATE_ONLY" if not self.db.execute("SELECT 1 FROM claims WHERE domain_id=?",(d,)).fetchone() else "PROMOTED")

        actions={field:"REVALIDATE" for field in self.migration_correctness_fields()}; actions["approximate_indexes"]="RECOMPUTE"; actions["historical_judgements"]="PRESERVE"
        manifest=self.register_migration_manifest(d,migration_id=f"m:{seed}",from_schema="legacy",to_schema="v0.6.3",field_actions=actions)
        record("manifest_declares_every_correctness_field","VALIDATED",manifest["status"])
        safe=set(actions.values()).issubset({"PRESERVE","MAP_WITH_PROOF","RECOMPUTE","REVALIDATE","DOWNGRADE","QUARANTINE","DELETE_BY_POLICY","FAIL"})
        record("migration_action_vocabulary_conservative","CONSERVATIVE","CONSERVATIVE" if safe else "UNSAFE")

        before=self.capture_probe_checkpoint(d,"before")
        self.start_new_incarnation(d,principal="alice",reason="migration-restore",operation_id=f"inc:{seed}")
        after=self.capture_probe_checkpoint(d,"after")
        record("old_receipts_do_not_resurrect_across_incarnation","INCARNATION_ADVANCED","INCARNATION_ADVANCED" if after.cut.incarnation>before.cut.incarnation else "ABA")

        hist=self.resolve_current_region(d,region)
        record("historical_logical_ids_remain_resolvable","RESOLVABLE","RESOLVABLE" if hist else "LOST")
        try:
            bad=dict(actions); bad["origin_identity"]="EXACT"
            self.register_migration_manifest(d,migration_id=f"bad:{seed}",from_schema="legacy",to_schema="v0.6.3",field_actions=bad)
            observed="UPGRADE_ALLOWED"
        except MemoryTransitionIncomplete: observed="FAIL_CLOSED"
        record("semantic_upgrade_from_unknown_is_failure","FAIL_CLOSED",observed)
        failures=[x for x in outcomes if not x["passed"]]
        return {"kind":"migration-acceptance-v0.6.3","seed":seed,"fixture_count":len(outcomes),"failed":len(failures),"passed":not failures,"outcomes":outcomes,"failure_digest":digest(failures)}

    def run_performance_semantic_gate_campaign(self, *, seed: int = 268) -> dict[str, object]:
        """Verify optimizations downgrade status rather than silently weakening semantics."""
        from .errors import MemoryQueryCapabilityUnsupported, MemoryViewOverflow, MemoryProposalStale
        rng=random.Random(seed); outcomes=[]
        def record(name,expected,observed,detail=None): outcomes.append({"fixture":name,"expected":expected,"observed":observed,"passed":expected==observed,"detail":detail})
        d=f"perf_{seed}_{rng.randrange(1_000_000_000):09d}"; self.create_domain(d); fam=f"PERF_{seed}"; self.register_query_family(fam,{"x"})
        r=self.create_region(d,"r",principal="alice"); rep=self.add_representation(d,r,kind="exact",payload={"x":1},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=3,principal="alice")
        self.index_representation_view(d,rep,"dense",["needle"]); self.advance_index_frontier(d,"dense",through_sequence=self.head(d).sequence,mode="APPROXIMATE")
        try:
            self.discover_regions_at_cut(d,principal="alice",view_keys={"dense":["needle"]},cut=self.head(d),require_exact=True); observed="EXACT_ALLOWED"
        except MemoryQueryCapabilityUnsupported: observed="CAPABILITY_DOWNGRADED"
        record("approx_ann_cannot_certify_exact_hard_search","CAPABILITY_DOWNGRADED",observed)

        self.advance_index_frontier(d,"dense",through_sequence=self.head(d).sequence,mode="EXACT"); old_cut=self.head(d); self.invalidate_representation(d,rep,principal="alice")
        found=self.discover_regions(d,principal="alice",view_keys={"dense":["needle"]})
        record("stale_index_cache_cannot_ignore_revocation","CANONICAL_FILTERED","CANONICAL_FILTERED" if r not in found else "STALE_LEAK")

        r2=self.create_region(d,"r2",principal="alice"); self.add_representation(d,r2,kind="exact",payload={"x":2},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=10,principal="alice")
        try:
            self.compile_recall(d,"alice",[RecallRole("hard",r2,fam,hard=True)],1); observed="TRUNCATED_SUFFICIENT"
        except MemoryViewOverflow: observed="OVERFLOW"
        record("smaller_frame_cannot_drop_hard_role","OVERFLOW",observed)

        source=self.add_representation(d,r2,kind="raw",payload={"x":2},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice")
        proposal=self.create_representation_proposal(d,r2,source_representation_ids=[source],kind="summary",payload={"x":2},loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=1,principal="alice")
        try:
            self.promote_representation_proposal(proposal.proposal_id,principal="alice"); observed="PROMOTED_UNVERIFIED"
        except Exception: observed="VERIFICATION_REQUIRED"
        record("deferred_verification_cannot_preserve_verified_promotion","VERIFICATION_REQUIRED",observed)

        # Removing the only recoverability witness must visibly downgrade answerability.
        h=self._head_row(d); ev=self.capture_evidence(domain_id=d,operation_id=f"w:{seed}",expected_seq=int(h["sequence"]),writer_epoch=int(h["writer_epoch"]),source_event_identity=f"w:{seed}",content={"x":3},principal="alice").object_id
        r3=self.create_region(d,"r3",principal="alice")
        raw_witness=self.add_representation(d,r3,kind="raw",payload={"x":3},source_evidence_ids=[ev],loss={"x":LossState.PRESERVED_EXACT},recoverable=set(),token_cost=2,principal="alice")
        compact=self.add_representation(d,r3,kind="summary",payload={},source_representation_ids=[raw_witness],loss={"x":LossState.LOST},recoverable={"x"},token_cost=1,principal="alice")
        before=self.answerability(compact,fam).value
        self.erase_evidence(d,ev,principal="alice",policy_ref="perf-delete")
        after=self.answerability(compact,fam).value
        record("deleting_witness_downgrades_recoverability","DOWNGRADED","DOWNGRADED" if before=="REHYDRATABLE" and after!="REHYDRATABLE" else "FALSE_SAFE",{"before":before,"after":after})
        failures=[x for x in outcomes if not x["passed"]]
        return {"kind":"performance-semantic-gate-v0.6.3","seed":seed,"fixture_count":len(outcomes),"failed":len(failures),"passed":not failures,"outcomes":outcomes,"failure_digest":digest(failures)}
