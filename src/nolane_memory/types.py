from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LossState(str, Enum):
    PRESERVED_EXACT = "PRESERVED_EXACT"
    PRESERVED_NORMALIZED = "PRESERVED_NORMALIZED"
    COARSENED = "COARSENED"
    LOST = "LOST"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Answerability(str, Enum):
    EXACT = "EXACT"
    BOUNDED = "BOUNDED"
    REHYDRATABLE = "REHYDRATABLE"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


class Recoverability(str, Enum):
    IN_REPRESENTATION = "IN_REPRESENTATION"
    SOURCE_REHYDRATABLE = "SOURCE_REHYDRATABLE"
    ALTERNATIVE_WITNESS_AVAILABLE = "ALTERNATIVE_WITNESS_AVAILABLE"
    NEW_EVIDENCE_REQUIRED = "NEW_EVIDENCE_REQUIRED"
    IRRECOVERABLE_UNDER_CURRENT_RETENTION = "IRRECOVERABLE_UNDER_CURRENT_RETENTION"
    SCOPE_BLOCKED_FOR_PRINCIPAL = "SCOPE_BLOCKED_FOR_PRINCIPAL"


@dataclass(frozen=True)
class CommitReceipt:
    domain_id: str
    operation_id: str
    request_digest: str
    commit_seq: int
    previous_root: str
    root: str
    object_id: str
    kind: str
    committed_at: str
    incarnation: int = 1


@dataclass(frozen=True)
class MemoryAuthorityDomainRevision:
    domain_id: str
    revision: int
    predecessor_revision: int | None
    incarnation: int
    writer_epoch: int
    sequence: int
    root: str
    action: str
    reason: str
    created_at: str


@dataclass(frozen=True)
class MemoryWriterFenceRevision:
    domain_id: str
    writer_epoch: int
    predecessor_epoch: int | None
    incarnation: int
    reason: str
    created_at: str
    created_sequence: int


@dataclass(frozen=True)
class MemoryWriteIntentRevision:
    domain_id: str
    incarnation: int
    operation_id: str
    request_digest: str
    kind: str
    object_id: str
    status: str
    created_at: str
    expires_at: str | None = None
    reconciled_at: str | None = None
    commit_seq: int | None = None
    receipt_json: dict[str, Any] | None = None
    last_error: str | None = None


@dataclass(frozen=True)
class OriginBindingReceipt:
    binding_id: str
    domain_id: str
    evidence_id: str
    origin_identity: str
    transport_channel: str
    external_identity: str | None
    authority_class: str
    common_mode_group: str | None
    raw_evidence_digest: str
    scope_ceiling: list[str]
    binder_procedure: str
    created_seq: int
    revoked_seq: int | None = None
    revocation_reason: str | None = None


@dataclass(frozen=True)
class RecallRole:
    role_id: str
    region_id: str
    query_family: str
    hard: bool = True
    temporal_mode: str = "CURRENT_EPISTEMIC"
    use_capability: str = "USE_FOR_LOCAL_REASONING"
    risk_class: str = "normal"
    allow_approximation: bool = False


@dataclass(frozen=True)
class RecallBoundaryDescriptor:
    task: str
    principal: str
    explicit_roles: list[RecallRole] = field(default_factory=list)
    canonical_constraint_roles: list[RecallRole] = field(default_factory=list)
    action_tool_roles: list[RecallRole] = field(default_factory=list)
    prospective_event_keys: list[str] = field(default_factory=list)
    revalidation_roles: list[RecallRole] = field(default_factory=list)
    security_roles: list[RecallRole] = field(default_factory=list)
    optional_roles: list[RecallRole] = field(default_factory=list)
    sink: str | None = None
    token_budget: int = 4096
    page_fault_budget: int = 64
    role_budget: int = 256
    compatibility_profile: dict[str, str] = field(default_factory=dict)
    safety_critical_dimensions: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class RecallObligation:
    hard_roles: list[RecallRole]
    optional_roles: list[RecallRole]
    closure_iterations: int
    compatibility_profile: dict[str, str] = field(default_factory=dict)
    safety_critical_dimensions: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class RecallCut:
    domain_id: str
    incarnation: int
    sequence: int
    root: str


@dataclass(frozen=True)
class FrameFragment:
    role_id: str
    representation_id: str
    region_id: str
    query_family: str
    payload: Any
    token_cost: int
    page_faulted: bool = False


@dataclass(frozen=True)
class Dependency:
    dep_class: str
    dep_key: str
    generation: int


@dataclass(frozen=True)
class RecallFrame:
    frame_id: str
    domain_id: str
    principal: str
    cut: RecallCut
    fragments: list[FrameFragment]
    dependencies: list[Dependency]
    sufficiency: str
    token_cost: int
    roles: list[RecallRole] = field(default_factory=list)


@dataclass(frozen=True)
class RegionDiscoveryResult:
    result_id: str
    domain_id: str
    principal: str
    cut: RecallCut
    candidate_region_ids: list[str]
    reasons: dict[str, list[str]]
    frontier_receipts: list[dict[str, Any]]
    require_exact: bool
    created_at: str


@dataclass(frozen=True)
class RepresentationResolution:
    resolution_id: str
    domain_id: str
    principal: str
    role: RecallRole
    cut: RecallCut
    selected_representation_id: str | None
    status: str
    options: list[dict[str, Any]]
    created_at: str


@dataclass(frozen=True)
class RecallReconstruction:
    reconstruction_id: str
    domain_id: str
    principal: str
    role: RecallRole
    cut: RecallCut
    status: str
    candidate_representation_ids: list[str]
    signatures: list[str]
    created_at: str


@dataclass(frozen=True)
class RecallSufficiencyAssessment:
    assessment_id: str
    frame_id: str
    status: str
    hard_role_ids: list[str]
    covered_hard_role_ids: list[str]
    unresolved_hard_role_ids: list[str]
    token_cost: int
    created_at: str


@dataclass(frozen=True)
class RecallFrameDependencyManifestRevision:
    manifest_id: str
    frame_id: str
    domain_id: str
    cut: RecallCut
    dependencies: list[Dependency]
    dependency_digest: str
    completeness: str
    created_at: str


@dataclass(frozen=True)
class MemoryUseFence:
    fence_id: str
    frame_id: str
    domain_id: str
    principal: str
    sink: str
    payload_digest: str
    dependency_digest: str
    issued_at: str
    expires_at: str | None
    consumed: bool = False
    clock_authority_id: str | None = None
    clock_epoch: str | None = None
    flow_receipt_id: str | None = None


class DebtOutcome(str, Enum):
    OPEN = "OPEN"
    NARROWED = "NARROWED"
    PARTIALLY_DISCHARGED = "PARTIALLY_DISCHARGED"
    DISCHARGED_BY_FORMAL_RESULT = "DISCHARGED_BY_FORMAL_RESULT"
    DISCHARGED_BY_REPLICATION = "DISCHARGED_BY_REPLICATION"
    DISCHARGED_BY_POLICY_DECISION = "DISCHARGED_BY_POLICY_DECISION"
    SUPERSEDED_BY_NEW_CONTRACT = "SUPERSEDED_BY_NEW_CONTRACT"
    ACCEPTED_RESIDUAL_RISK = "ACCEPTED_RESIDUAL_RISK"
    DESTROYED_BY_POLICY = "DESTROYED_BY_POLICY"


class EffectTier(str, Enum):
    E0 = "E0"  # observational correlation
    E1 = "E1"  # matched comparison
    E2 = "E2"  # shadow/counterfactual
    E3 = "E3"  # paired intervention
    E4 = "E4"  # strong controlled intervention


class FlowDecision(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_TRANSFORM = "ALLOW_WITH_TRANSFORM"
    BLOCK = "BLOCK"
    OPAQUE = "OPAQUE"


class RecoveryLayerStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"
    NOT_EVALUATED = "NOT_EVALUATED"
    OPAQUE = "OPAQUE"


class RepairCause(str, Enum):
    REGION_CONTENT = "REGION_CONTENT"
    REGION_BOUNDARY = "REGION_BOUNDARY"
    SHARED_TRANSFORM_PROFILE = "SHARED_TRANSFORM_PROFILE"
    NORMALIZER = "NORMALIZER"
    QUERY_FAMILY_BASIS = "QUERY_FAMILY_BASIS"
    SOURCE_INTEGRITY = "SOURCE_INTEGRITY"
    SCHEMA_POLICY = "SCHEMA_POLICY"


@dataclass(frozen=True)
class SemanticDebt:
    debt_id: str
    domain_id: str
    subject_kind: str
    subject_id: str
    kind: str
    severity: str
    consequence: str
    evidence_needed: str
    outcome: str
    created_seq: int
    resolved_seq: int | None = None
    evidence_ref: str | None = None


@dataclass(frozen=True)
class QueryCounterexample:
    counterexample_id: str
    domain_id: str
    region_id: str
    representation_id: str
    query_family: str
    lost_dimensions: list[str]
    source_witness_id: str | None
    decision_relevance: str
    cause_type: str
    created_seq: int
    resolved_seq: int | None = None
    replacement_representation_id: str | None = None


@dataclass(frozen=True)
class RepairReceipt:
    repair_id: str
    domain_id: str
    counterexample_id: str
    cause_type: str
    invalidated_representation_ids: list[str]
    replacement_representation_id: str | None
    dependency_fanout: list[str]
    status: str
    created_seq: int


@dataclass(frozen=True)
class RetentionDecision:
    decision_id: str
    domain_id: str
    target_kind: str
    target_id: str
    status: str
    protected_families: list[str]
    uncovered_families: list[str]
    debt_id: str | None
    created_seq: int


@dataclass(frozen=True)
class MaintenanceReceipt:
    maintenance_id: str
    domain_id: str
    region_id: str
    semantic_digest: str
    outcome: str
    created_seq: int


@dataclass(frozen=True)
class ProbeCheckpoint:
    checkpoint_id: str
    domain_id: str
    label: str
    cut: RecallCut
    vector: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class DeclassificationReceipt:
    receipt_id: str
    domain_id: str
    representation_id: str
    principal: str
    sink: str
    authority_ref: str
    created_seq: int
    revoked_seq: int | None = None
    expires_at: str | None = None


@dataclass(frozen=True)
class FrameInformationFlowReceipt:
    flow_receipt_id: str
    frame_id: str
    candidate_payload_digest: str
    principal: str
    sink: str
    source_memory_refs: list[str]
    declassification_receipt_refs: list[str]
    blocked_or_rewritten_fragment_refs: list[str]
    hard_roles_affected: list[str]
    decision: str
    policy_checks: list[str]
    procedure_revision: str
    created_at: str
    dependencies: list[Dependency] = field(default_factory=list)
    expires_at: str | None = None
    clock_authority_id: str | None = None
    clock_epoch: str | None = None


@dataclass(frozen=True)
class MemoryExposureReceipt:
    exposure_id: str
    domain_id: str
    frame_id: str
    consumer: str
    task: str
    regime: str
    rendering: str
    candidate_representation_ids: list[str]
    selected_representation_ids: list[str]
    rendered_representation_ids: list[str]
    referenced_representation_ids: list[str]
    created_at: str


@dataclass(frozen=True)
class EffectEvidence:
    effect_id: str
    domain_id: str
    representation_ids: list[str]
    consumer: str
    task: str
    regime: str
    rendering: str
    outcome_dimension: str
    tier: str
    effect: float
    confidence: float
    created_at: str
    exposure_id: str | None = None


@dataclass(frozen=True)
class ActivationGuardReceipt:
    guard_id: str
    frame_id: str
    consumer: str
    task: str
    regime: str
    rendering: str
    inhibited_optional_representation_ids: list[str]
    blocked_hard_role_ids: list[str]
    decision: str
    created_at: str


@dataclass(frozen=True)
class PublicationReceipt:
    publication_id: str
    source_domain: str
    source_sequence: int
    destination_domain: str
    destination_sequence: int
    source_representation_id: str
    destination_evidence_id: str
    origin_roots: list[str]
    created_at: str


@dataclass(frozen=True)
class ContinuityPin:
    pin_id: str
    domain_id: str
    cut: RecallCut
    state_digest: str
    mission_revision: str | None
    self_version: str | None
    environment_revision: str | None
    hard_roles: list[RecallRole]
    verification_blockers: list[str]
    stable_refs: list[str]
    created_seq: int


@dataclass(frozen=True)
class RecoveryResumeAssessment:
    assessment_id: str
    domain_id: str
    pin_id: str | None
    layers: dict[str, str]
    resume_allowed: bool
    first_blocked_layer: str | None
    current_cut: RecallCut
    created_at: str


@dataclass(frozen=True)
class MemoryErasureClosureReceipt:
    receipt_id: str
    domain_id: str
    retention_event_id: str
    target_kind: str
    target_id: str
    surfaces: dict[str, str]
    tainted_representation_ids: list[str]
    invalidated_continuity_pin_ids: list[str]
    recoverability_downgrades: list[str]
    status: str
    created_seq: int
    invalidated_handoff_packet_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HandoffPacket:
    packet_id: str
    domain_id: str
    principal: str
    cut: RecallCut
    fragments: list[FrameFragment]
    blockers: list[str]
    mission_revision: str | None
    self_version: str | None
    created_at: str
    advisory_next_action: Any | None = None
    tool_boundary_digest: str | None = None


@dataclass(frozen=True)
class ResearchRunReport:
    run_id: str
    kind: str
    passed: int
    failed: int
    cases: int
    seed: int | None
    details: dict[str, Any]


@dataclass(frozen=True)
class MemoryQueryDomainRevision:
    query_domain_id: str
    domain_id: str
    principal: str
    incarnation: int
    cut: RecallCut
    predicate: dict[str, Any]
    surfaces: list[str]
    capability: str
    generation: int
    created_at: str


@dataclass(frozen=True)
class NegativeQueryReceipt:
    receipt_id: str
    domain_id: str
    principal: str
    predicate: dict[str, Any]
    completeness: str
    status: str
    match_representation_ids: list[str]
    cut: RecallCut
    dependencies: list[Dependency]
    created_at: str
    query_domain_id: str | None = None


@dataclass(frozen=True)
class ConnectorQueryReceipt:
    receipt_id: str
    domain_id: str
    connector_id: str
    profile_revision: int
    principal: str
    predicate: dict[str, Any]
    snapshot_id: str | None
    pages_seen: int
    completeness: str
    status: str
    result_ids: list[str]
    transport_authority: str
    content_authority: str
    dependencies: list[Dependency]
    cut: RecallCut
    created_at: str
    provider_error: str | None = None


@dataclass(frozen=True)
class TemporalCoverageReceipt:
    receipt_id: str
    domain_id: str
    evidence_ids: list[str]
    valid_from: str
    valid_to: str
    coverage_contract: str
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class EvidenceIndependenceReceipt:
    receipt_id: str
    domain_id: str
    evidence_ids: list[str]
    dependence: str
    independent_root_count: int
    root_origins: list[str]
    common_mode_groups: list[str]
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class SupportBundleReceipt:
    receipt_id: str
    domain_id: str
    logical_id: str
    claim_revision_id: str
    live_paths: list[dict[str, Any]]
    supported: bool
    independence_receipt_id: str | None
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class RecoverabilityCertificate:
    certificate_id: str
    domain_id: str
    representation_id: str
    query_family: str
    status: str
    source_witness_ids: list[str]
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class PreservationCertificate:
    certificate_id: str
    domain_id: str
    representation_id: str
    query_family: str
    query_family_revision: int
    verifier_ref: str
    status: str
    missing_dimensions: list[str]
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class DependencyCompatibilityReceipt:
    receipt_id: str
    domain_id: str
    dep_class: str
    dep_key: str
    previous_generation: int
    current_generation: int
    profile_id: str
    profile_revision: int
    procedure: str
    classification: str
    old_observable_digest: str | None
    new_observable_digest: str | None
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class PreservationProbeReceipt:
    receipt_id: str
    domain_id: str
    source_representation_id: str
    target_representation_id: str
    query_family: str
    profile_id: str
    profile_revision: int
    procedure: str
    verifier_class: str
    tool_profile_ref: str | None
    status: str
    dimension_results: dict[str, str]
    source_observable_digest: str | None
    target_observable_digest: str | None
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class ExtractionProposal:
    proposal_id: str
    domain_id: str
    source_evidence_id: str
    principal: str
    extractor_revision: str
    extracted_fields_digest: str
    source_handles: dict[str, str]
    candidate_types: list[str]
    uncertainty: dict[str, float]
    high_risk_fields: list[str]
    dependencies: list[Dependency]
    status: str
    created_at: str
    promoted_representation_id: str | None = None


@dataclass(frozen=True)
class ExtractionVerificationReceipt:
    receipt_id: str
    proposal_id: str
    domain_id: str
    verifier_ref: str
    field_results: dict[str, str]
    status: str
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class RegionEvolutionReceipt:
    evolution_id: str
    domain_id: str
    kind: str
    predecessor_region_ids: list[str]
    successor_region_ids: list[str]
    created_seq: int


@dataclass(frozen=True)
class RepresentationProposal:
    proposal_id: str
    domain_id: str
    region_id: str
    kind: str
    source_representation_ids: list[str]
    transform_profile: str
    payload_digest: str
    dependencies: list[Dependency]
    created_at: str
    promoted_representation_id: str | None = None


@dataclass(frozen=True)
class HistoricalJudgement:
    judgement_id: str
    domain_id: str
    claim_revision_id: str
    principal: str
    judgement: str
    reason: str
    cut: RecallCut
    created_seq: int
    created_at: str


@dataclass(frozen=True)
class TransitionVerificationReceipt:
    receipt_id: str
    proposal_id: str
    domain_id: str
    verifier_ref: str
    coverage: str
    preservation: str
    faithfulness: str
    status: str
    dependencies: list[Dependency]
    created_at: str


@dataclass(frozen=True)
class AccessProfileRevision:
    domain_id: str
    principal: str
    revision: int
    predecessor_revision: int | None
    capabilities: list[str]
    sink_capabilities: dict[str, list[str]]
    created_seq: int
    expires_at: str | None = None


@dataclass(frozen=True)
class RegimeRevision:
    domain_id: str
    revision: int
    predecessor_revision: int | None
    mission_revision: str | None
    environment_revision: str | None
    schema_revision: str
    created_seq: int


@dataclass(frozen=True)
class SelfVersionProfileRevision:
    domain_id: str
    revision: int
    predecessor_revision: int | None
    profile_id: str
    metadata: dict[str, Any]
    created_seq: int


@dataclass(frozen=True)
class CounterexampleApplicabilityRevision:
    counterexample_id: str
    domain_id: str
    revision: int
    predecessor_revision: int | None
    applicability: dict[str, Any]
    status: str
    created_seq: int


@dataclass(frozen=True)
class ReplayForensicAssessment:
    assessment_id: str
    domain_id: str
    cut: RecallCut
    available_modes: list[str]
    current_use_mode: str
    barriers: list[dict[str, Any]]
    unavailable_refs: list[str]
    connector_receipt_ids: list[str]
    created_at: str


@dataclass(frozen=True)
class NoTwoWritableClocksAudit:
    audit_id: str
    domain_id: str
    passed: bool
    checks: dict[str, str]
    violations: list[dict[str, Any]]
    created_at: str


@dataclass(frozen=True)
class FullSpecReleaseGateReport:
    gate_id: str
    domain_id: str
    implementation_ready: bool
    research_complete: bool
    research_closure: str
    checks: dict[str, str]
    metrics: dict[str, Any]
    unsupported_claims: list[str]
    created_at: str
