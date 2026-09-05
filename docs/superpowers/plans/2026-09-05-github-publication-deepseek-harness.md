# GitHub Publication + DeepSeek Harness Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit Nolane Memory rc2, add a fail-visible DeepSeek Harness plugin using only public runtime APIs, and publish the verified tree to `Nolane-x/Nolane-memory` through a review branch/PR.

**Architecture:** Core Python semantics remain authoritative. A TypeScript Cordis plugin registers DSH tools and delegates via a shell-free JSON-lines Python bridge. Publication uses a fresh branch because the GitHub repository is currently empty.

**Tech Stack:** Python 3.11+, SQLite, pytest/unittest, TypeScript ESM, DeepSeek Harness/Cordis current developer-preview plugin API, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-05-github-publication-deepseek-harness-design.md`

## Global Constraints
- Do not weaken Nolane Memory authority, recall, privacy, use-time or research-closure semantics.
- DeepSeek adapter imports only public `nolane_memory` APIs.
- Never invoke subprocesses with a shell.
- Model-facing capture defaults to unspecified factual authority.
- Errors are fail-visible protocol errors; never return an error as a successful memory result.
- Publish only after verification from the exact candidate tree.

---

### Task 1: Fresh forensic audit
**Files:** no production changes.
- [ ] Run pytest and unittest independently.
- [ ] Run compileall, package/import checks, manifest/spec digest checks, static-danger scan and SQLite integrity probes.
- [ ] Run release gate and multi-seed fuzz/differential campaigns; record exact results.

### Task 2: Python bridge protocol
**Files:**
- Create: `plugins/deepseek-harness/python/nolane_memory_bridge.py`
- Test: `tests/test_deepseek_harness_bridge.py`

**Interfaces:** newline-delimited JSON request `{id, method, params}` -> response `{id, ok, result}` or `{id, ok:false, error:{type,message}}`.
- [ ] Write failing tests for status, capture, recall validation, integrity and error serialization.
- [ ] Run targeted tests and confirm RED.
- [ ] Implement bridge using only public package API and shell-free process assumptions.
- [ ] Run targeted tests GREEN.

### Task 3: Cordis plugin
**Files:**
- Create: `plugins/deepseek-harness/package.json`
- Create: `plugins/deepseek-harness/tsconfig.json`
- Create: `plugins/deepseek-harness/src/index.ts`
- Create: `plugins/deepseek-harness/cordis.patch.yml`
- Create: `plugins/deepseek-harness/README.md`
- Test: `tests/test_deepseek_harness_plugin_contract.py`

**Interfaces:** `name`, `inject=['tools']`, `Config`, `apply(ctx, config)`, DSH tool names listed in the design.
- [ ] Write contract tests first and confirm RED.
- [ ] Implement pinned Cordis/DSH tool registration and process bridge client.
- [ ] Run contract/protocol tests GREEN.

### Task 4: CI/publication metadata
**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.gitignore`
- Modify: `README.md`
- Modify: `docs/CONFORMANCE.md`
- [ ] Add CI that runs core and plugin protocol/contract checks.
- [ ] Document DeepSeek compatibility boundary and installation overlay.
- [ ] Re-run full verification.

### Task 5: Exact-tree publication
- [ ] Build/rebuild wheel and release ZIP from exact tree if source changed.
- [ ] Extract artifact and rerun tests.
- [ ] Create GitHub publication branch from empty main.
- [ ] Upload complete verified text tree and required binary artifact(s) without generated caches.
- [ ] Open PR to `main` describing evidence and known external research/DSH-preview limits.
- [ ] Fetch PR/diff and verify expected files are present.
