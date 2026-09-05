# Nolane Memory v0.6.3 Full-Spec Executable Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Extend the existing K0-K2 + Semantic-OCC reference kernel into executable K0-K5 support for every implementation-relevant contract in the v0.6.3 spec, while preserving explicit research/empirical debt instead of self-certifying production correctness.

**Architecture:** Keep `runtime.py` as the deterministic canonical/representation/recall/OCC substrate. Add focused mixins for lifelong evolution, effects/security, continuity/erasure, and K5 research/runtime tooling; each mixin owns its schema and methods but uses the same SQLite transaction, generation, access, and hash semantics. New higher-level features remain derived/audit/control state and never become independent factual authority.

**Tech Stack:** Python 3.11+, stdlib only, SQLite WAL/FULL synchronous, `unittest`, deterministic JSON/SHA-256.

**Spec:** `/mnt/data/NOLANE-MEMORY-V0.6.3-FINAL-USE-TIME-CAUSAL-CUT-SEMANTIC-OCC-RUNTIME-RESEARCH-SPEC.md`

## Global Constraints

- One canonical correctness order per Memory Authority Domain; all authority-changing writes use expected-base/epoch/idempotency semantics.
- Derived representations, effect evidence, frames, flow receipts, recovery assessments, and indexes never own factual truth.
- Unknown/opaque/incomplete states fail visibly for hard obligations; no optimistic promotion.
- Access filtering happens before hidden retrieval influence and again at sink disclosure.
- Privacy deletion may destroy recoverability; the runtime records explicit debt/gaps rather than retaining forbidden content.
- Weak/observational effect evidence cannot suppress hard-required memory.
- K5 executable support must not be reported as independent validation or W5 closure.

---

### Task 1: Shared K3-K5 semantic types and schema composition

**Files:**
- Modify: `src/nolane_memory/types.py`
- Modify: `src/nolane_memory/errors.py`
- Modify: `src/nolane_memory/runtime.py`
- Create: `src/nolane_memory/evolution.py`
- Create: `src/nolane_memory/effects_security.py`
- Create: `src/nolane_memory/continuity.py`
- Create: `src/nolane_memory/research.py`
- Test: `tests/test_full_profile_types_schema.py`

**Interfaces:**
- Produces enums/dataclasses for debt, counterexamples, retention, effects, flow receipts, continuity pins, recovery assessments, erasure receipts, discovery/research reports.
- `MemoryRuntime` inherits `EvolutionMixin`, `EffectsSecurityMixin`, `ContinuityMixin`, `ResearchMixin` and invokes each `_init_*_schema()` after base schema creation.

- [x] Write failing schema/type smoke tests that instantiate the new DTOs and verify all subsystem tables exist after `MemoryRuntime` creation.
- [x] Run the new test and verify failure because the modules/tables do not exist.
- [x] Add enums/dataclasses/errors and mixin schema initialization with no behavior beyond persistence ownership.
- [x] Run baseline + new tests and verify green.

### Task 2: K3 semantic debt, counterexample repair, and fixed-point evolution

**Files:**
- Modify: `src/nolane_memory/evolution.py`
- Modify: `src/nolane_memory/runtime.py`
- Test: `tests/test_k3_evolution.py`

**Interfaces:**
- `create_semantic_debt(domain_id, subject_kind, subject_id, kind, severity, evidence_needed, consequence) -> SemanticDebt`
- `transition_semantic_debt(domain_id, debt_id, outcome, evidence_ref, principal) -> SemanticDebt`
- `record_query_counterexample(...) -> QueryCounterexample`
- `repair_counterexample(..., source_representation_id, replacement_payload, replacement_loss, cause_type, principal) -> RepairReceipt`
- `maintenance_fixed_point(domain_id, region_id, normalized_semantics) -> MaintenanceReceipt`

- [x] Write failing tests: debt cannot disappear without typed transition; counterexample remains durable after repair; descendant prose cannot restore LOST without a source witness; repeated stable maintenance returns one semantic revision; shared-profile cause bumps profile dependency while region-content cause stays local.
- [x] Run tests and confirm expected missing-method failures.
- [x] Implement durable debt/counterexample/repair/fixed-point tables and methods using canonical transitions for control state.
- [x] Re-run and refactor only after green.

### Task 3: Witness-cover retention, erasure consequences, migration and longitudinal probes

**Files:**
- Modify: `src/nolane_memory/evolution.py`
- Modify: `src/nolane_memory/runtime.py`
- Test: `tests/test_k3_retention_migration.py`

**Interfaces:**
- `protect_region_obligation(domain_id, region_id, query_family, principal) -> str`
- `consider_delete_representation(domain_id, representation_id, principal, allow_irreversible=False) -> RetentionDecision`
- `import_legacy_representation(...)-> representation_id` marks unknown provenance/dimensions conservatively and creates debt.
- `capture_probe_checkpoint(domain_id, label) -> ProbeCheckpoint`

- [x] Write failing tests for safe redundant deletion, blocked last-witness deletion, policy-authorized irreversible deletion creating debt/gap, legacy unknown provenance staying UNKNOWN, and probe checkpoint retaining normalized conformance fields.
- [x] Run red tests.
- [x] Implement witness-cover feasibility over protected query families and conservative migration/probe persistence.
- [x] Run all tests green.

### Task 4: K4 access capability algebra, declassification, composition flow gate, and shared publication

**Files:**
- Modify: `src/nolane_memory/effects_security.py`
- Modify: `src/nolane_memory/runtime.py`
- Modify: `src/nolane_memory/types.py`
- Test: `tests/test_k4_security_flow.py`

**Interfaces:**
- `set_access_profile(domain_id, principal, capabilities, sink_capabilities=None)`
- `grant_declassification(domain_id, representation_id, principal, sink, authority_ref) -> DeclassificationReceipt`
- `revoke_declassification(...)`
- `check_information_flow(frame, principal, sink, payload) -> FrameInformationFlowReceipt`
- `publish_representation(src_domain, dst_domain, representation_id, principal, operation_id) -> PublicationReceipt`

- [x] Write failing tests for private-memory zero hidden influence with explicit profiles, local-reasoning permission not implying tool disclosure, declassification allow then revoke, composed payload block despite per-fragment read access, publication preserving root origins and causal cut dependency.
- [x] Run red tests.
- [x] Implement capability checks at discover/read/hydrate/sink boundaries; add declassification and flow receipts; add governed publication with preserved origin roots and causal edge.
- [x] Run full suite green.

### Task 5: K4 effect ledger, interference guard, prospective triggers and self-version scope

**Files:**
- Modify: `src/nolane_memory/effects_security.py`
- Modify: `src/nolane_memory/runtime.py`
- Test: `tests/test_k4_effects_prospective.py`

**Interfaces:**
- `record_effect_evidence(..., tier, effect, confidence) -> EffectEvidence`
- `apply_interference_guard(frame, consumer, task, regime, rendering) -> ActivationGuardReceipt`
- `register_prospective_trigger(..., event_key, roles, owner) -> trigger_id`
- `fire_prospective_triggers(domain_id, event_key, principal) -> list[RecallRole]`
- `set_self_version(domain_id, profile_id, metadata) -> None`

- [x] Write failing tests proving E0 cannot veto hard roles, strong scoped evidence can suppress optional fragments only in matching consumer/task/regime/rendering, model upgrade prevents effect-profile transfer, trigger firing creates obligations not actions, duplicate/cyclic trigger roles dedupe.
- [x] Run red tests.
- [x] Implement scoped effect ledger/guard, trigger registry/firing, and self-version generation semantics.
- [x] Run all tests green.

### Task 6: Continuity pins, layered recovery, hard erasure closure and clean rederivation

**Files:**
- Modify: `src/nolane_memory/continuity.py`
- Modify: `src/nolane_memory/runtime.py`
- Test: `tests/test_continuity_erasure.py`

**Interfaces:**
- `create_continuity_pin(...)-> ContinuityPin`
- `assess_recovery(...)-> RecoveryResumeAssessment` with R0-R6 statuses.
- `erase_evidence(domain_id, evidence_id, principal, policy_ref) -> MemoryErasureClosureReceipt`
- `clean_rederive(...)-> new_representation_id`
- `create_handoff_packet(...)-> HandoffPacket`

- [x] Write failing tests for forged/root-mismatched pin, dangling refs, unresolved blockers, mission/self-version drift, pre-delete snapshot blocked by later erasure barrier, source deletion tainting derived reps and continuity artifacts, clean rederivation requiring surviving sources, hard handoff roles surviving recency pressure.
- [x] Run red tests.
- [x] Implement R0-R6 assessment, non-revival barriers, source-evidence lineage/taint closure, erasure receipt surface accounting, clean rederivation, and hard-cover handoff generation.
- [x] Run all tests green.

### Task 7: K5 multi-view discovery, active reconstruction, degraded modes, formal lab and fuzz/differential harness

**Files:**
- Modify: `src/nolane_memory/research.py`
- Modify: `src/nolane_memory/runtime.py`
- Test: `tests/test_k5_research_runtime.py`
- Create: `examples/full_profile.py`

**Interfaces:**
- `index_representation_view(representation_id, view, keys)` and `discover_regions(...)`
- `active_reconstruct(...)` returns competing candidates / ambiguity instead of silent top-1 collapse.
- `set_capability_availability(domain_id, capability, available)` for explicit degraded modes.
- `run_preservation_lab()`, `run_lifelong_fuzz(seed, cases)`, `conformance_vector(domain_id)`, `differential_check(model_b)`.

- [x] Write failing tests for multi-view union, causal/temporal discovery independent of lexical similarity, ambiguity surfacing, archive-unavailable page-fault downgrade, effect-ledger-unavailable disabling inhibition, bounded preservation exhaustive properties, and seeded lifelong fuzz preserving invariants.
- [x] Run red tests.
- [x] Implement deterministic derived indexes, reconstruction, capability switches, formal tiny-world lab, state-machine fuzz, and normalized conformance vector/differential adapter.
- [x] Run all tests including longer fuzz profile.

### Task 8: CLI/docs/package/full verification

**Files:**
- Modify: `src/nolane_memory/cli.py`
- Modify: `src/nolane_memory/__init__.py`
- Modify: `README.md`
- Modify: `docs/CONFORMANCE.md`
- Modify: `pyproject.toml`
- Create: `docs/FULL_PROFILE_LIMITS.md`

**Interfaces:**
- CLI commands expose `status`, `debts`, `erase`, `recover`, `lab`, and `fuzz` without bypassing runtime policy.

- [x] Add CLI smoke tests/commands and update package exports/version to `0.6.3b1`.
- [x] Document executable K0-K5 support separately from empirical/independent validation debt.
- [x] Run `PYTHONPATH=src python -m unittest discover -s tests -v`.
- [x] Run `python -m compileall -q src tests examples`.
- [x] Run examples, CLI smoke, preservation lab and seeded fuzz.
- [x] Build wheel with `python -m pip wheel . --no-deps --no-build-isolation -w dist` and install it into a clean target for smoke import.
- [x] Recreate ZIP and SHA-256 manifests only after all verification passes.
