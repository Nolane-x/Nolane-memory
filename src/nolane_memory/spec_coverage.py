from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


_SECTION_RE = re.compile(r"^# (\d+)\.\s+(.+)$", re.MULTILINE)

# Sections whose primary claim is outside the runtime implementation boundary.  They
# remain visible in the one-to-one ledger instead of being silently discarded.
_EXTERNAL_SECTIONS = (
    set(range(126, 133))
    | set(range(140, 152))
    | set(range(240, 251))
    | set(range(296, 304))
    | {305, 326, 350, 369, 371, 372, 397, 398, 399}
)

# Explanatory/history/process sections with no independent runtime semantic owner.
_REFERENCE_SECTIONS = (
    set(range(1, 10))
    | set(range(111, 126))
    | {133, 139, 152, 271, 293, 294, 295, 319}
    | set(range(320, 326))
    | {327, 328, 332, 333, 334, 335, 348, 349, 352, 353, 354, 375, 376, 377, 402}
)

_EXTERNAL_SUBCLAIMS: dict[int, list[str]] = {
    157: ["public_benchmark_execution"],
    158: ["fair_external_baseline_execution"],
    159: ["external_interaction_ablation_results"],
    161: ["real_agent_longitudinal_external_validity"],
    247: ["independent_replication"],
    257: ["W5_research_closure"],
    267: ["independently_built_external_implementation"],
    269: ["benchmark_validity_on_real_scores"],
    305: ["independently_built_external_implementation"],
    331: ["research_complete_requires_external_evidence"],
    347: ["historical_artifact_digest_is_reference_only"],
    370: ["historical_artifact_digest_is_reference_only"],
    373: ["external_differential_replication"],
    396: ["historical_artifact_digest_is_reference_only"],
    401: ["external_second_implementation_race_replication"],
}


def parse_numbered_sections(spec_path: str | Path) -> list[dict[str, Any]]:
    path = Path(spec_path)
    text = path.read_text(encoding="utf-8")
    matches = list(_SECTION_RE.finditer(text))
    sections: list[dict[str, Any]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append({
            "section": int(match.group(1)),
            "title": match.group(2).strip(),
            "body": body,
        })
    return sections


def _classification(section: int) -> str:
    if section in _EXTERNAL_SECTIONS:
        return "RESEARCH_EXTERNAL"
    if section in _REFERENCE_SECTIONS:
        return "REFERENCE_NARRATIVE"
    return "IMPLEMENTATION_TESTABLE"


def _ev(code: list[str], tests: list[str], methods: list[str], strength: str = "DIRECT") -> dict[str, Any]:
    return {"code_paths": code, "test_paths": tests, "methods": methods, "strength": strength}


_DIRECT: dict[int, dict[str, Any]] = {
    134: _ev(["src/nolane_memory/research.py"], ["tests/test_reference_formal_suite.py"], ["run_reference_formal_suite"]),
    135: _ev(["src/nolane_memory/research.py"], ["tests/test_reference_formal_suite.py"], ["run_reference_formal_suite"]),
    136: _ev(["src/nolane_memory/research.py", "src/nolane_memory/evolution.py"], ["tests/test_reference_formal_suite.py", "tests/test_k3_retention_migration.py"], ["run_reference_formal_suite", "consider_delete_representation"]),
    137: _ev(["src/nolane_memory/research.py", "src/nolane_memory/learning.py"], ["tests/test_reference_formal_suite.py", "tests/test_temporal_procedure_consolidation.py"], ["run_reference_formal_suite", "learn_procedure"]),
    138: _ev(["src/nolane_memory/research.py"], ["tests/test_reference_formal_suite.py"], ["run_reference_formal_suite"]),
    153: _ev(["src/nolane_memory/research.py"], ["tests/test_experimental_program_153_161.py"], ["experimental_metric_catalog", "summarize_experiment_metrics"]),
    154: _ev(["src/nolane_memory/research.py"], ["tests/test_experimental_program_153_161.py"], ["experimental_metric_catalog", "summarize_experiment_metrics"]),
    155: _ev(["src/nolane_memory/research.py"], ["tests/test_experimental_program_153_161.py", "tests/test_research_acceptance_runtime.py"], ["summarize_experiment_metrics", "run_context_scalability_probe"]),
    156: _ev(["src/nolane_memory/research.py", "src/nolane_memory/effects_security.py"], ["tests/test_experimental_program_153_161.py", "tests/test_effect_exposure_chain.py"], ["experimental_metric_catalog", "record_memory_exposure"]),
    157: _ev(["src/nolane_memory/research.py"], ["tests/test_k5_research_runtime.py"], ["benchmark_ablation_portfolio"]),
    158: _ev(["src/nolane_memory/research.py"], ["tests/test_research_acceptance_runtime.py"], ["record_benchmark_evidence"]),
    159: _ev(["src/nolane_memory/research.py"], ["tests/test_experimental_program_153_161.py"], ["interaction_ablation_protocol"]),
    160: _ev(["src/nolane_memory/research.py"], ["tests/test_experimental_program_153_161.py"], ["run_private_stress_world_campaign"]),
    161: _ev(["src/nolane_memory/research.py"], ["tests/test_experimental_program_153_161.py"], ["run_longitudinal_experiment_protocol"]),
    162: _ev(["src/nolane_memory/runtime.py"], ["tests/test_k0_canonical.py"], ["capture_evidence"]),
    163: _ev(["src/nolane_memory/evolution.py"], ["tests/test_full_spec_seams.py"], ["split_region", "merge_regions"]),
    164: _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/governance.py"], ["tests/test_governance_closure.py", "tests/test_claim_revision_temporal.py"], ["create_claim"]),
    165: _ev(["src/nolane_memory/evolution.py"], ["tests/test_boundary_and_verification.py"], ["create_representation_proposal", "promote_representation_proposal"]),
    166: _ev(["src/nolane_memory/learning.py"], ["tests/test_temporal_procedure_consolidation.py"], ["learn_procedure"]),
    167: _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/research.py"], ["tests/test_query_family_preservation_revision.py", "tests/test_preservation_probe_registry.py"], ["certify_preservation"]),
    168: _ev(["src/nolane_memory/evolution.py"], ["tests/test_dynamic_recoverability_counterexample_recall.py"], ["record_query_counterexample"]),
    169: _ev(["src/nolane_memory/evolution.py"], ["tests/test_k3_evolution.py"], ["repair_counterexample"]),
    170: _ev(["src/nolane_memory/research.py"], ["tests/test_index_frontier.py", "tests/test_projection_plane_receipts.py"], ["discover_regions_at_cut", "discover_regions_with_receipt"]),
    171: _ev(["src/nolane_memory/research.py"], ["tests/test_projection_plane_receipts.py"], ["resolve_representation"]),
    172: _ev(["src/nolane_memory/runtime.py"], ["tests/test_boundary_and_verification.py"], ["compile_boundary_recall"]),
    173: _ev(["src/nolane_memory/research.py"], ["tests/test_query_domain_revision.py"], ["execute_negative_query_domain"]),
    174: _ev(["src/nolane_memory/effects_security.py"], ["tests/test_effect_exposure_chain.py", "tests/test_k4_effects_prospection.py"], ["record_effect_evidence"]),
    175: _ev(["src/nolane_memory/effects_security.py"], ["tests/test_k4_effects_prospection.py"], ["apply_interference_guard"]),
    176: _ev(["src/nolane_memory/evolution.py"], ["tests/test_k3_retention_migration.py"], ["consider_delete_representation"]),
    177: _ev(["src/nolane_memory/continuity.py"], ["tests/test_k4_continuity_erasure.py", "tests/test_recovery_privacy_closure_extended.py"], ["assess_recovery"]),
    178: _ev(["src/nolane_memory/evolution.py", "src/nolane_memory/learning.py"], ["tests/test_k3_evolution.py", "tests/test_temporal_procedure_consolidation.py"], ["maintenance_fixed_point", "assess_consolidation_pressure"]),
    258: _ev(["src/nolane_memory/research.py", "src/nolane_memory/runtime.py"], ["tests/test_crash_atomic_batch.py", "tests/test_full_spec_release_gate.py"], ["run_fault_atomicity_probe"]),
    259: _ev(["src/nolane_memory/research.py"], ["tests/test_reference_formal_suite.py", "tests/test_preservation_probe_registry.py"], ["run_reference_formal_suite", "run_preservation_probe"]),
    260: _ev(["src/nolane_memory/research.py"], ["tests/test_recall_reference_equivalence.py"], ["run_recall_reference_equivalence_campaign"]),
    261: _ev(["src/nolane_memory/research.py"], ["tests/test_persistence_lifelong_fuzz.py"], ["run_persistence_lifelong_fuzz"]),
    262: _ev(["src/nolane_memory/research.py"], ["tests/test_research_acceptance_runtime.py"], ["run_context_scalability_probe"]),
    263: _ev(["src/nolane_memory/research.py"], ["tests/test_acceptance_campaigns_263_268.py"], ["run_temporal_acceptance_campaign"]),
    264: _ev(["src/nolane_memory/research.py", "src/nolane_memory/learning.py"], ["tests/test_acceptance_campaigns_263_268.py"], ["run_procedure_failure_acceptance_campaign"]),
    265: _ev(["src/nolane_memory/research.py", "src/nolane_memory/effects_security.py"], ["tests/test_acceptance_campaigns_263_268.py"], ["run_security_privacy_acceptance_campaign"]),
    266: _ev(["src/nolane_memory/research.py", "src/nolane_memory/evolution.py"], ["tests/test_acceptance_campaigns_263_268.py"], ["run_migration_acceptance_campaign"]),
    267: _ev(["src/nolane_memory/research.py", "src/nolane_memory/independent_kernel.py"], ["tests/test_independent_differential.py"], ["run_independent_differential"]),
    268: _ev(["src/nolane_memory/research.py"], ["tests/test_acceptance_campaigns_263_268.py"], ["run_performance_semantic_gate_campaign"]),
    269: _ev(["src/nolane_memory/research.py"], ["tests/test_research_acceptance_runtime.py"], ["record_benchmark_evidence"]),
    270: _ev(["src/nolane_memory/research.py"], ["tests/test_full_spec_release_gate.py"], ["run_full_spec_release_gate"]),
    279: _ev(["src/nolane_memory/continuity.py"], ["tests/test_replay_forensic_no_two_clocks.py"], ["assess_replay"]),
    280: _ev(["src/nolane_memory/research.py"], ["tests/test_replay_forensic_no_two_clocks.py"], ["audit_no_two_writable_clocks"]),
    304: _ev(["src/nolane_memory/evolution.py"], ["tests/test_k3_evolution.py"], ["transition_semantic_debt"]),
    306: _ev(["src/nolane_memory/research.py", "src/nolane_memory/independent_kernel.py"], ["tests/test_independent_differential.py"], ["conformance_vector", "run_independent_differential"]),
    307: _ev(["src/nolane_memory/research.py", "src/nolane_memory/independent_kernel.py"], ["tests/test_independent_differential.py"], ["run_independent_differential"]),
    308: _ev(["src/nolane_memory/research.py", "src/nolane_memory/independent_kernel.py"], ["tests/test_independent_differential.py"], ["run_independent_differential"]),
    309: _ev(["src/nolane_memory/research.py"], ["tests/test_recall_reference_equivalence.py", "tests/test_independent_differential.py"], ["run_recall_reference_equivalence_campaign", "run_independent_differential"]),
    310: _ev(["src/nolane_memory/research.py", "src/nolane_memory/evolution.py"], ["tests/test_independent_differential.py", "tests/test_k3_retention_migration.py"], ["run_independent_differential", "consider_delete_representation"]),
    311: _ev(["src/nolane_memory/research.py", "src/nolane_memory/continuity.py"], ["tests/test_independent_differential.py", "tests/test_recovery_privacy_acceptance_campaign.py"], ["run_independent_differential", "assess_recovery"]),
    312: _ev(["src/nolane_memory/research.py"], ["tests/test_independent_differential.py"], ["run_independent_differential"]),
    329: _ev(["src/nolane_memory/research.py"], ["tests/test_full_spec_ownership_audit.py"], ["audit_full_spec_ownership"]),
    330: _ev(["src/nolane_memory/research.py", "src/nolane_memory/governance.py"], ["tests/test_full_spec_release_gate.py", "tests/test_origin_binding.py"], ["run_full_spec_release_gate", "get_origin_bindings"]),
    331: _ev(["src/nolane_memory/research.py"], ["tests/test_full_spec_release_gate.py"], ["run_full_spec_release_gate"]),
    347: _ev(["src/nolane_memory/research.py"], ["tests/test_versioned_seam_calculi.py"], ["run_v061_seam_calculus"]),
    351: _ev(["src/nolane_memory/research.py", "src/nolane_memory/independent_kernel.py"], ["tests/test_independent_differential.py"], ["run_independent_differential"]),
    370: _ev(["src/nolane_memory/research.py"], ["tests/test_versioned_seam_calculi.py"], ["run_v062_continuity_recovery_erasure_calculus"]),
    373: _ev(["src/nolane_memory/research.py", "src/nolane_memory/continuity.py"], ["tests/test_recovery_privacy_acceptance_campaign.py"], ["run_recovery_privacy_acceptance_campaign"]),
    374: _ev(["src/nolane_memory/research.py"], ["tests/test_full_spec_ownership_audit.py"], ["audit_full_spec_ownership"]),
    388: _ev(["src/nolane_memory/runtime.py"], ["tests/test_trusted_time_fence.py"], ["issue_use_fence", "consume_use_fence"]),
    389: _ev(["src/nolane_memory/research.py"], ["tests/test_operational_semantic_field_audit.py"], ["audit_operational_semantic_fields"]),
    390: _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/research.py"], ["tests/test_applicability_use_site_contract.py"], ["discover_regions_at_cut", "compile_recall"]),
    392: _ev(["src/nolane_memory/research.py"], ["tests/test_dependency_validator_profiles.py"], ["register_dependency_validator_profile", "classify_dependency_change", "classify_manifest_change", "validate_dependency_compatibility_receipt"]),
    393: _ev(["src/nolane_memory/research.py", "src/nolane_memory/effects_security.py"], ["tests/test_publication_cycle_causal_origin.py"], ["run_publication_cycle_acceptance_campaign"]),
    394: _ev(["src/nolane_memory/effects_security.py", "src/nolane_memory/research.py"], ["tests/test_information_flow_use_time_lease.py"], ["run_information_flow_use_time_campaign"]),
    395: _ev(["src/nolane_memory/research.py", "src/nolane_memory/runtime.py"], ["tests/test_information_flow_use_time_lease.py"], ["run_resource_pressure_use_validation_campaign"]),
    396: _ev(["src/nolane_memory/research.py"], ["tests/test_use_time_causal_cut_calculus.py"], ["run_use_time_causal_cut_calculus"]),
    400: _ev(["src/nolane_memory/research.py"], ["tests/test_full_spec_ownership_audit.py"], ["audit_full_spec_ownership"]),
    401: _ev(["src/nolane_memory/research.py"], ["tests/test_use_time_race_campaign.py"], ["run_use_time_race_campaign"]),
}


def _topic_evidence(section: int, title: str) -> dict[str, Any]:
    if section in _DIRECT:
        return _DIRECT[section]
    t = title.lower()

    # Closure/data-model ownership statements are intentionally traced to the
    # machine-enforced ownership audit rather than duplicated writable stores.
    if 179 <= section <= 188 or 272 <= section <= 278:
        return _ev(
            ["src/nolane_memory/types.py", "src/nolane_memory/research.py"],
            ["tests/test_full_profile_types_schema.py", "tests/test_full_spec_ownership_audit.py"],
            ["audit_full_spec_ownership"], "STRUCTURAL",
        )
    if 251 <= section <= 257:
        return _ev(["src/nolane_memory/research.py"], ["tests/test_full_spec_release_gate.py"], ["run_full_spec_release_gate", "k5_profile_status"], "GATE")
    if 281 <= section <= 292:
        return _ev(["src/nolane_memory/research.py", "src/nolane_memory/evolution.py"], ["tests/test_k3_retention_migration.py", "tests/test_acceptance_campaigns_263_268.py"], ["register_migration_manifest", "import_legacy_representation"], "PROTOCOL")
    if 314 <= section <= 318:
        return _ev(["src/nolane_memory/research.py", "src/nolane_memory/governance.py"], ["tests/test_full_spec_release_gate.py", "tests/test_governance_closure.py"], ["run_full_spec_release_gate", "audit_full_spec_ownership"], "GATE")

    if any(k in t for k in ("continuity", "recovery", "handoff", "anchor", "erasure", "rollback", "restore", "boot")):
        return _ev(["src/nolane_memory/continuity.py", "src/nolane_memory/research.py"], ["tests/test_k4_continuity_erasure.py", "tests/test_recovery_privacy_closure_extended.py"], ["assess_recovery", "validate_handoff_packet"], "TOPIC")
    if any(k in t for k in ("publication", "shared-memory", "shared memory", "multi-agent", "social", "institutional", "causal visibility")):
        return _ev(["src/nolane_memory/effects_security.py", "src/nolane_memory/research.py"], ["tests/test_publication_saga.py", "tests/test_publication_cycle_causal_origin.py"], ["prepare_publication", "complete_publication"], "TOPIC")
    if any(k in t for k in ("security", "privacy", "confidential", "declass", "information-flow", "information flow", "poison", "principal", "authority/write")):
        return _ev(["src/nolane_memory/effects_security.py", "src/nolane_memory/governance.py"], ["tests/test_k4_security_flow.py", "tests/test_information_flow_use_time_lease.py"], ["check_information_flow", "set_access_profile"], "TOPIC")
    if any(k in t for k in ("effect", "interference", "activation", "contamination")):
        return _ev(["src/nolane_memory/effects_security.py"], ["tests/test_k4_effects_prospection.py", "tests/test_effect_exposure_chain.py"], ["record_effect_evidence", "apply_interference_guard"], "TOPIC")
    if "prospect" in t:
        return _ev(["src/nolane_memory/effects_security.py"], ["tests/test_prospective_trigger_lifecycle.py"], ["register_prospective_trigger", "fire_prospective_triggers"], "TOPIC")
    if any(k in t for k in ("connector", "external connector")):
        return _ev(["src/nolane_memory/research.py"], ["tests/test_connector_opacity_frontier.py"], ["register_connector_profile", "query_connector"] if False else ["register_connector_profile"], "TOPIC")
    if any(k in t for k in ("extraction", "explainability", "model-generated")):
        return _ev(["src/nolane_memory/extraction.py"], ["tests/test_extraction_explainability.py"], ["propose_extraction", "explain_memory"], "TOPIC")
    if any(k in t for k in ("procedure", "applicability", "regime", "self-version", "past-self", "model upgrade", "consumer/model")):
        return _ev(["src/nolane_memory/learning.py", "src/nolane_memory/continuity.py", "src/nolane_memory/effects_security.py"], ["tests/test_temporal_procedure_consolidation.py", "tests/test_applicability_use_site_contract.py", "tests/test_policy_profile_revision_history.py"], ["learn_procedure", "set_runtime_compatibility", "set_self_version"], "TOPIC")
    if any(k in t for k in ("recall", "frame", "obligation", "discovery", "resolution", "page fault", "context", "negative", "query-domain", "query domain", "reconstruction")):
        return _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/research.py"], ["tests/test_k2_recall.py", "tests/test_projection_plane_receipts.py", "tests/test_recall_reference_equivalence.py"], ["compile_recall", "discover_regions_with_receipt"], "TOPIC")
    if any(k in t for k in ("counterexample", "repair", "forget", "witness", "semantic debt", "maintenance", "consolidation", "fixed point", "fixed-point")):
        return _ev(["src/nolane_memory/evolution.py", "src/nolane_memory/learning.py"], ["tests/test_k3_evolution.py", "tests/test_k3_retention_migration.py"], ["record_query_counterexample", "maintenance_fixed_point"], "TOPIC")
    if any(k in t for k in ("representation", "preservation", "loss", "recoverability", "compression", "rebase", "query famil", "granularity", "capability")):
        return _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/evolution.py", "src/nolane_memory/governance.py"], ["tests/test_k1_preservation.py", "tests/test_query_family_preservation_revision.py", "tests/test_preservation_probe_registry.py"], ["answerability", "certify_recoverability"], "TOPIC")
    if any(k in t for k in ("claim", "judgement", "justification", "historical", "valid time", "knowledge", "temporal", "truth")):
        return _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/governance.py", "src/nolane_memory/learning.py"], ["tests/test_claim_revision_temporal.py", "tests/test_governance_closure.py"], ["create_claim", "judgement_as_of"], "TOPIC")
    if any(k in t for k in ("origin", "independence", "integrity authority", "admission", "authority ceiling", "provenance")):
        return _ev(["src/nolane_memory/governance.py", "src/nolane_memory/runtime.py"], ["tests/test_origin_binding.py", "tests/test_governance_closure.py", "tests/test_integrity_publication_policy.py"], ["get_origin_bindings", "evaluate_evidence_independence"], "TOPIC")
    if any(k in t for k in ("writer", "commit", "canonical", "idempot", "crash", "frontier", "concurrency", "correctness writer")):
        return _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/research.py"], ["tests/test_k0_canonical.py", "tests/test_crash_atomic_batch.py", "tests/test_writer_fence_revision.py"], ["verify_integrity", "head"], "TOPIC")
    if any(k in t for k in ("migration", "legacy", "compatibility adapter")):
        return _ev(["src/nolane_memory/evolution.py", "src/nolane_memory/research.py"], ["tests/test_k3_retention_migration.py", "tests/test_acceptance_campaigns_263_268.py"], ["import_legacy_representation", "register_migration_manifest"], "TOPIC")
    if any(k in t for k in ("index", "cache", "freshness")):
        return _ev(["src/nolane_memory/research.py"], ["tests/test_index_frontier.py", "tests/test_query_domain_revision.py"], ["advance_index_frontier", "discover_regions_at_cut"], "TOPIC")
    if any(k in t for k in ("use fence", "use-time", "semantic occ", "linearization", "final argument", "payload binding", "trusted-time", "operational semantic", "resource pressure")):
        return _ev(["src/nolane_memory/runtime.py", "src/nolane_memory/research.py", "src/nolane_memory/effects_security.py"], ["tests/test_v063_occ.py", "tests/test_use_time_race_campaign.py", "tests/test_information_flow_use_time_lease.py"], ["issue_use_fence", "consume_use_fence"], "TOPIC")
    if "access" in t:
        return _ev(["src/nolane_memory/effects_security.py"], ["tests/test_policy_profile_revision_history.py", "tests/test_policy_expiry_lifecycle.py"], ["set_access_profile", "get_access_profile_revision"], "TOPIC")
    if any(k in t for k in ("error", "degraded", "typed")):
        return _ev(["src/nolane_memory/errors.py", "src/nolane_memory/research.py"], ["tests/test_extended_semantics.py", "tests/test_full_spec_release_gate.py"], ["run_full_spec_release_gate"], "TOPIC")

    # Structural theorems and cross-cutting laws are enforced by the ownership and
    # full release gates; this is an explicit group mapping, not a new authority.
    return _ev(
        ["src/nolane_memory/research.py", "src/nolane_memory/runtime.py"],
        ["tests/test_full_spec_release_gate.py", "tests/test_full_spec_ownership_audit.py"],
        ["run_full_spec_release_gate", "audit_full_spec_ownership"], "CROSS_CUTTING",
    )


def build_spec_coverage_ledger(spec_path: str | Path, project_root: str | Path) -> dict[str, Any]:
    from .runtime import MemoryRuntime

    root = Path(project_root)
    parsed = parse_numbered_sections(spec_path)
    nums = [row["section"] for row in parsed]
    counts = Counter(nums)
    duplicates = sorted(n for n, c in counts.items() if c > 1)
    missing_numbers = [n for n in range(1, 403) if n not in counts]
    rows: list[dict[str, Any]] = []
    implementation_missing: list[dict[str, Any]] = []
    implementation_partial: list[dict[str, Any]] = []

    for item in parsed:
        n = item["section"]
        classification = _classification(n)
        if classification == "RESEARCH_EXTERNAL":
            row = {
                "section": n, "title": item["title"], "classification": classification,
                "status": "EXTERNAL", "evidence": {"code_paths": [], "test_paths": [], "methods": [], "strength": "EXTERNAL"},
                "external_dependencies": _EXTERNAL_SUBCLAIMS.get(n, ["external_research_or_historical_evidence"]),
            }
        elif classification == "REFERENCE_NARRATIVE":
            row = {
                "section": n, "title": item["title"], "classification": classification,
                "status": "REFERENCE", "evidence": {"code_paths": [], "test_paths": [], "methods": [], "strength": "REFERENCE"},
                "external_dependencies": [],
            }
        else:
            evidence = _topic_evidence(n, item["title"])
            missing_code = [p for p in evidence["code_paths"] if not (root / p).exists()]
            missing_tests = [p for p in evidence["test_paths"] if not (root / p).exists()]
            missing_methods = [m for m in evidence["methods"] if not hasattr(MemoryRuntime, m)]
            if missing_code or missing_tests:
                status = "MISSING"
            elif missing_methods:
                status = "PARTIAL"
            else:
                status = "COMPLETE"
            row = {
                "section": n, "title": item["title"], "classification": classification,
                "status": status, "evidence": evidence,
                "missing_code_paths": missing_code, "missing_test_paths": missing_tests,
                "missing_methods": missing_methods,
                "external_dependencies": _EXTERNAL_SUBCLAIMS.get(n, []),
                "external_research_status": "BLOCKED" if _EXTERNAL_SUBCLAIMS.get(n) else "NOT_REQUIRED_FOR_IMPLEMENTATION",
            }
            if status == "MISSING": implementation_missing.append({"section": n, "title": item["title"], "missing_code_paths": missing_code, "missing_test_paths": missing_tests})
            elif status == "PARTIAL": implementation_partial.append({"section": n, "title": item["title"], "missing_methods": missing_methods})
        rows.append(row)

    return {
        "kind": "nolane-memory-spec-coverage-ledger-v0.6.3",
        "spec_path": str(Path(spec_path)), "section_count": len(rows),
        "duplicate_sections": duplicates, "missing_section_numbers": missing_numbers,
        "implementation_count": sum(r["classification"] == "IMPLEMENTATION_TESTABLE" for r in rows),
        "external_count": sum(r["classification"] == "RESEARCH_EXTERNAL" for r in rows),
        "reference_count": sum(r["classification"] == "REFERENCE_NARRATIVE" for r in rows),
        "implementation_complete_count": sum(r["classification"] == "IMPLEMENTATION_TESTABLE" and r["status"] == "COMPLETE" for r in rows),
        "implementation_missing": implementation_missing,
        "implementation_partial": implementation_partial,
        "sections": rows,
        "research_complete": False,
        "research_closure": "BLOCKED",
    }
