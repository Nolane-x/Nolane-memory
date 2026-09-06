# Nolane Memory Milestone 0 Independent Review Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the reproduced rc4 hidden-dependency race into a minimal, review-ready falsification package without changing production runtime semantics, then stop at the independent-review gate before E1/SRSC production work.

**Architecture:** Keep `MemoryRuntime` and all production semantics unchanged. Strengthen only the Crucible research evidence: minimize the executable trace, make the host-contract-vs-kernel-gap classification explicit, bind the result to exact source/CI identities, and expose a reviewer checklist. E1 remains forbidden until an independent reviewer classifies the trace.

**Tech Stack:** Python 3.11/3.12/3.13, `unittest`/`pytest`, SQLite-backed `nolane_memory.MemoryRuntime`, GitHub Actions.

**Spec:** `NOLANE-MEMORY-V0.7-W5-CRUCIBLE-SEMANTIC-READ-SET-CLOSURE-RESEARCH-BLUEPRINT(1).md` (campaign `NM-V07-W5-CRUCIBLE-2026-09-06`), especially Phase A, G0, Milestone 0, and the E0/E1 preregistration rules.

## Global Constraints

- Baseline semantic target remains Nolane Memory `0.6.3rc4`; no public semantic version bump in Milestone 0.
- Do not modify `src/nolane_memory/runtime.py` or any production authority owner in this milestone.
- E0 is evidence of a bounded missing-read-set seam only; it does not establish production prevalence, universal natural-language incompleteness, or SRSC uniqueness.
- Preserve `MemoryUseFence` as the single use-time authority; do not create a parallel fence.
- Do not preregister or implement E1 until the independent classification gate is satisfied.
- W5 remains `BLOCKED`.

---

### Task 1: Minimize and lock the E0 trace

**Files:**
- Modify: `tests/crucible/test_hidden_dependency_race.py`
- Modify: `research/crucible/e0_rc4_result.json`

**Interfaces:**
- Consumes: current rc4 APIs `compile_recall(...)`, `validate_frame(...)`, `issue_use_fence(...)`, `consume_use_fence(...)`.
- Produces: one bounded trace proving `B` influenced the payload, `B` is absent from the active frame manifest, `B` changes, the active frame remains valid, the fence accepts the stale payload, and a fresh oracle observes `B_new`.

- [ ] **Step 1: Preserve the existing E0 executable test as the RED/green discriminator**

The test must continue to assert all six observations above and must not manually inject `B` into the active dependency manifest.

- [ ] **Step 2: Run focused E0**

Run:

```bash
python -m pytest -q tests/crucible/test_hidden_dependency_race.py -vv
```

Expected: PASS on unmodified rc4 semantics, because the purpose of E0 is to reproduce the false accept.

- [ ] **Step 3: Record a compact machine-readable trace**

Add a `minimal_trace` array to `research/crucible/e0_rc4_result.json` containing exactly the causal steps and expected observations, without adding interpretation not exercised by the test.

- [ ] **Step 4: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/crucible/test_hidden_dependency_race.py research/crucible/e0_rc4_result.json
git commit -m "research: minimize and lock E0 hidden-dependency trace"
```

### Task 2: Make the alternative host-contract explanation falsifiable

**Files:**
- Create: `research/crucible/independent_review_request.md`
- Modify: `research/crucible/e0_rc4_result.json`

**Interfaces:**
- Consumes: exact E0 trace and rc4 source snapshot.
- Produces: a reviewer decision with one of `KERNEL_READ_SET_GAP`, `HOST_OBLIGATION_VIOLATION`, `TEST_INVALID`, or `INCONCLUSIVE`, plus evidence references.

- [ ] **Step 1: Write the reviewer packet**

The packet must ask the reviewer to attempt to falsify E0 by locating an existing rc4 contract that requires every materially used prior-context premise to be represented in the active consequence dependency set before `MemoryUseFence` issuance.

- [ ] **Step 2: Define acceptance criteria**

`KERNEL_READ_SET_GAP` requires that the test obey all existing documented host/runtime obligations while still passing stale `B`. `HOST_OBLIGATION_VIOLATION` requires an existing normative contract, test, or adapter invariant that E0 violates without adding new v0.7 semantics. `TEST_INVALID` requires a concrete mismatch with rc4 API semantics. Otherwise return `INCONCLUSIVE`.

- [ ] **Step 3: Bind the review request into the E0 result**

Add `independent_review.status = "PENDING"` and the review packet path. Keep `semantic_revision_earned = false`.

- [ ] **Step 4: Commit**

```bash
git add research/crucible/independent_review_request.md research/crucible/e0_rc4_result.json
git commit -m "research: add independent E0 classification gate"
```

### Task 3: Verify current-head evidence and expose the review gate

**Files:**
- Modify: PR #7 metadata only after CI evidence is known.

**Interfaces:**
- Consumes: current PR head SHA and GitHub Actions results.
- Produces: a review-ready PR whose body states exact current-head evidence and explicitly blocks E1/merge on independent classification.

- [ ] **Step 1: Verify current head**

Require `release-artifact-rc4` success and the normal `verify` workflow to finish successfully on the current head. Do not cite an older head as current-head closure.

- [ ] **Step 2: Update PR #7 body**

State the current head SHA, current workflow run IDs, E0 outcome, and the remaining independent classification gate.

- [ ] **Step 3: Mark PR ready for review**

Only after the current-head verification above is green.

- [ ] **Step 4: Stop before E1**

Do not create production SRSC/BGC code or claim `0.7.0-alpha.1` until the independent gate returns a classification that passes G0.
