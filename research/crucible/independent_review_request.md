# Independent Review Request — E0 Hidden-Dependency Classification

Campaign: `NM-V07-W5-CRUCIBLE-2026-09-06`  
Experiment: `E0_DIRECT_RC4_HIDDEN_DEPENDENCY_REPRODUCTION`  
Baseline: Nolane Memory `0.6.3rc4` at `c8ab348cf430801adb705c53b680fc102270e475`  
Status: **PENDING INDEPENDENT CLASSIFICATION**

## Review objective

Attempt to falsify the E0 interpretation. The reviewer must decide whether the observed stale structured consequence is:

1. `KERNEL_READ_SET_GAP` — the trace obeys the documented rc4 host/runtime contract, yet a material prior-context dependency can remain outside the active frame/use-fence read-set;
2. `HOST_OBLIGATION_VIOLATION` — an already-existing rc4 normative host/adapter contract requires the material premise to be carried into the active consequence dependency set, and E0 violates that contract;
3. `TEST_INVALID` — the test misuses an rc4 API or its oracle does not correspond to the runtime contract being claimed;
4. `INCONCLUSIVE` — available contracts/evidence do not justify one of the classifications above.

This review is a **falsification gate**, not an endorsement request. A reviewer should prefer `HOST_OBLIGATION_VIOLATION`, `TEST_INVALID`, or `INCONCLUSIVE` whenever the source supports them.

## Exact bounded observation under review

The executable test in `tests/crucible/test_hidden_dependency_race.py` performs this sequence:

1. Create exact action representation `A` and exact contact representation `B_old`.
2. Recall `B_old` into prior host/model context.
3. Compile the active consequence frame from `A` only.
4. Assert the active frame manifest contains neither the contact region nor `B_old` representation.
5. Invalidate `B_old` and create `B_new` without mutating `A`.
6. Assert the active `A` frame still validates.
7. Construct structured payload `{to: B_old.email, body: "status"}` from the previously retained value.
8. Issue and consume `MemoryUseFence` for that exact payload and sink `tool:send`.
9. Freshly recall the contact region and observe `B_new.email`.
10. Oracle marks the accepted payload stale because `payload.to != B_current.email`.

No dependency on `B` is manually injected into the active frame or fence.

## Primary falsification question

> Does rc4 already impose a normative obligation, before `MemoryUseFence` issuance, that every materially used value retained from prior host/model context must be reintroduced as an explicit dependency of the active consequence frame/fence?

If **yes**, cite the exact existing source/doc/test/adapter invariant and explain how E0 violates it. Do not infer a new requirement from the desired v0.7 behavior.

If **no**, explain why the runtime's current manifest/fence contract is correctly modeled by E0 and whether the missing dependency is best classified as a kernel semantic seam or an integration seam.

## Required source checks

Review at minimum:

- `src/nolane_memory/runtime.py`
  - `compile_recall(...)`
  - frame dependency manifest construction/currentness validation
  - `issue_use_fence(...)`
  - `consume_use_fence(...)`
- `tests/test_v063_occ.py`
- `docs/FULL_PROFILE_LIMITS.md`
- `docs/RC4_RELEASE_PROVENANCE.md`
- DeepSeek Harness bridge/plugin code, specifically any invariant that carries prior-context material inputs into active consequence dependencies.
- `research/crucible/preregistration.json`
- `research/crucible/source_snapshot.json`
- `research/crucible/e0_rc4_result.json`
- `tests/crucible/test_hidden_dependency_race.py`

## Decision criteria

### `KERNEL_READ_SET_GAP`

Return this only if all are true:

- E0 uses rc4 APIs according to their existing documented contracts;
- no existing host/adapter obligation requires `B` to be enumerated in the active consequence dependency set;
- the fence accepts while all enumerated dependencies are current;
- the structured consequence is stale under the explicit current-state oracle;
- fixing the failure requires either consequence-side dependency capture/closure or an equivalent strengthening of the semantic contract.

### `HOST_OBLIGATION_VIOLATION`

Return this only if all are true:

- an existing rc4 contract predating E0 explicitly requires the materially used prior-context value to be carried forward;
- the requirement is normative/machine-enforced or test-backed, not merely a design preference;
- a conforming host would prevent the E0 construction without adding v0.7 semantics.

### `TEST_INVALID`

Return this only with a concrete API/contract mismatch, invalid oracle, or impossible production state transition.

### `INCONCLUSIVE`

Return this when the evidence is insufficient to distinguish kernel semantics from an unwritten host assumption.

## Required reviewer output

Provide:

```json
{
  "classification": "KERNEL_READ_SET_GAP | HOST_OBLIGATION_VIOLATION | TEST_INVALID | INCONCLUSIVE",
  "confidence": "LOW | MEDIUM | HIGH",
  "falsification_attempts": ["..."],
  "decisive_evidence": ["path:line-or-symbol ..."],
  "missing_evidence": ["..."],
  "e1_allowed": false,
  "reason": "..."
}
```

`e1_allowed` may become `true` only when the reviewer concludes that G0 is satisfied strongly enough to preregister the identical-trace structured treatment. It must remain `false` for `TEST_INVALID` or unresolved `INCONCLUSIVE`; for `HOST_OBLIGATION_VIOLATION`, the next action is to repair/test the existing host contract rather than introduce SRSC semantics.

## Non-claims

- E0 does not prove universal dependency incompleteness.
- E0 does not prove SRSC/BGC is uniquely correct.
- E0 does not establish production prevalence or external superiority.
- This review does not close W5.
- The authoring reasoning chain that produced E0 is **not** an independent reviewer for G5.
