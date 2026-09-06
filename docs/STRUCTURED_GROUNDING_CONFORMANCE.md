# Structured Consequence Grounding — v0.6.4 Conformance Hardening Candidate

Status: **DRAFT / OPT-IN / NOT A v0.7 SEMANTIC CLAIM**

This document specifies the bounded purpose of the structured consequence-grounding surface introduced on `feat/v064-structured-grounding-conformance`.

## 1. Purpose

Nolane Memory v0.6.3 already requires a consequence-bound `RecallBoundaryDescriptor` whose hard obligation includes action/tool grounding dependencies. `compile_boundary_recall(...)` remains the primary mechanism for compiling those hard roles before a consequential action.

The structured-grounding surface does not replace that contract and does not claim to discover every material dependency. It adds a machine-checkable defense-in-depth path for structured output atoms that a host already knows were derived from memory.

The target failure is:

```text
memory frame B supplies value v
        ↓
host/model retains v
        ↓
a later consequence payload emits v at JSON path p
        ↓
B changes before or after use-fence issuance
```

If the host provides a strong grounding for `p`, the runtime must bind the emitted atom back to canonical persisted provenance and join that provenance into the existing `MemoryUseFence` read-set.

## 2. Ownership

No new truth authority is created.

- Canonical evidence/representations remain the factual owners.
- Persisted recall frames remain the source of the dependency manifest used by a grounding.
- `ConsequenceAtomGrounding` is a projection/receipt, not a truth record.
- `MemoryUseFence` remains the sole use-time currentness, final-payload binding, and single-use owner.

## 3. Grounding levels

The API exposes the candidate levels from the v0.7 research blueprint as bounded provenance states:

- `G0_UNKNOWN`
- `G1_MODEL_PROPOSED`
- `G2_AUDITED_BOUNDED`
- `G3_STRUCTURED_BOUND`
- `G4_DETERMINISTIC_CLOSED`

For the current implementation, strong structured use accepts only `G3_STRUCTURED_BOUND`. A model-proposed self-report cannot upgrade itself to G3.

These values are not confidence scores and are not authority/truth scores.

## 4. Host contract

A conforming host must still compile the action/decision boundary correctly. Structured grounding is additional enforcement, not permission to omit known hard roles.

For each memory-derived structured atom the host chooses to bind:

1. retain the source `RecallFrame` that supplied the value;
2. call `ground_consequence_atom(frame, role_id=..., source_field=..., atom_path=...)`;
3. declare the atom path as required when issuing the use fence;
4. pass the grounding projection to `issue_use_fence(...)`;
5. consume the normal `MemoryUseFence` exactly as before.

Example shape:

```python
grounding = runtime.ground_consequence_atom(
    source_frame,
    role_id="recipient",
    source_field="recipient",
    atom_path="/to",
)

fence = runtime.issue_use_fence(
    active_frame,
    principal="alice",
    sink="tool:send",
    payload={"to": "old@example.com", "body": "status"},
    consequence_groundings=[grounding],
    required_grounding_paths={"/to"},
)
```

## 5. Runtime checks

For grounded structured use, the runtime:

1. reloads the source frame from persisted storage;
2. verifies frame/domain/principal identity;
3. resolves exactly one persisted role/representation fragment;
4. obtains the source field from that persisted fragment;
5. verifies the grounding value digest;
6. resolves the emitted atom through JSON Pointer;
7. requires the emitted value to equal the persisted grounded value;
8. reloads the source frame dependency manifest rather than trusting caller-supplied dependencies;
9. validates those dependencies before fence issuance;
10. merges them with the active frame dependencies;
11. delegates final sink policy, payload digest, persistence and single-use semantics to the existing `MemoryUseFence` implementation;
12. relies on the existing consume-time dependency validation to catch mutation after issuance.

## 6. Required fail-closed cases

The current candidate rejects strong grounded use when:

- a required grounding path is absent;
- a supplied projection is not recognized;
- completeness is below G3;
- the source frame is missing or malformed;
- source role/representation identity is absent or ambiguous;
- the source value digest is forged or inconsistent;
- the emitted payload atom differs from the grounded value;
- source dependencies are stale;
- a source comes from another principal;
- a source comes from another domain without an explicit governed import;
- merged dependency generations disagree.

## 7. Backward compatibility

If no consequence groundings and no required grounding paths are supplied, `issue_use_fence(...)` delegates to the v0.6.3 implementation unchanged.

This is intentional for compatibility. It also means the feature cannot prove a host supplied a complete boundary unless the host opts into and correctly declares the required grounding surface.

## 8. Research interpretation

The original Crucible E0 direct-recipient trace was classified `HOST_OBLIGATION_VIOLATION`: rc4 already requires recipient/action-tool grounding roles to be present in the consequence boundary.

A second hidden-transform trace can execute a false accept when a material transform input is omitted, but rc4's normative hard basis already includes action/tool grounding dependencies. Therefore that observation is best interpreted as a practical **enforcement gap under an incomplete host boundary**, not evidence that v0.6.3 semantically permits the omission.

The structured-grounding candidate is therefore justified here as conformance hardening and defense in depth. It does not earn a v0.7 semantic revision and it does not close W5.

## 9. Explicit non-claims

This candidate does **not** claim:

- universal material-dependency discovery;
- natural-language dependency-extraction completeness;
- that every output atom can be deterministically grounded;
- that G3 implies factual truth independent of the source's authority/currentness;
- that model self-report is trustworthy provenance;
- external benchmark superiority;
- independent external replication;
- W5 research closure;
- SRSC/BGC as a uniquely necessary semantic architecture.

## 10. Promotion gate

Before this candidate can leave draft status:

- the focused structured-grounding conformance matrix must pass;
- the full existing test suite must remain green;
- release-gate/compile/example checks must remain green;
- no ordinary v0.6.3 fence behavior may regress when grounding is unused;
- the PR must preserve the non-claim boundary above.
