# Nolane Memory GitHub Publication + DeepSeek Harness Plugin Design

## Goal
Publish the verified Nolane Memory v0.6.3 runtime to the empty `Nolane-x/Nolane-memory` repository only after a fresh forensic audit, and add a DeepSeek Harness integration without moving DeepSeek-specific authority into the memory kernel.

## Architecture
The Python runtime remains the only owner of Nolane Memory semantics. `plugins/deepseek-harness/` is a TypeScript Cordis plugin for the current DeepSeek Harness developer-preview API. It depends on the Harness `tools` service, registers model-callable tools, and communicates with a Python JSON-lines bridge that imports only the public `nolane_memory` package surface.

The bridge owns no extra memory state. Every request opens a `MemoryRuntime` against the configured SQLite DB, invokes a public operation, serializes a typed result, and closes the runtime. This deliberately favors correctness and process isolation over a hidden long-lived Python cache. The Harness plugin validates arguments before forwarding them and returns fail-visible errors rather than converting them into successful memory results.

## DeepSeek tool surface
- `nolane_memory_status`: report runtime/research status and domain head/integrity.
- `nolane_memory_capture`: capture durable evidence with semantic event identity and authority metadata. The bridge reads the current writer-fence epoch and exact head before the OCC write; a concurrent relevant mutation remains a typed conflict rather than a hidden retry loop.
- `nolane_memory_recall`: compile a caller-declared set of RecallRole objects under explicit token/page-fault budget and compatibility profile. The plugin does not invent query-family semantics or auto-promote summaries.
- `nolane_memory_verify`: run domain integrity and no-two-writable-clocks audit.
- `nolane_memory_release_gate`: operator-only diagnostic surface, disabled by default because it is expensive.

## Safety and authority boundaries
1. The plugin never turns model text into admitted factual authority by itself.
2. Capture defaults to `source_authority_class=UNSPECIFIED`; stronger authority must be explicitly configured by the host/caller.
3. Recall requires pre-existing query-family/representation contracts. Failure to satisfy a hard role remains typed insufficiency/overflow.
4. No action authorization is granted by memory results or use fences.
5. The bridge uses a configured Python executable and database path; it never invokes a shell.
6. JSON-lines stdout is protocol-only; diagnostics go to stderr.
7. DeepSeek Harness is developer preview. Compatibility is pinned and documented, and a static/API contract test guards the currently documented plugin shape.

## Repository layout
- `src/nolane_memory/`: core runtime, unchanged in ownership.
- `tests/`: core regression suite plus bridge tests.
- `plugins/deepseek-harness/src/index.ts`: Cordis tool plugin.
- `plugins/deepseek-harness/python/nolane_memory_bridge.py`: public-API bridge.
- `plugins/deepseek-harness/tests/`: protocol/contract tests that can run without a model key.
- `plugins/deepseek-harness/cordis.patch.yml`: example overlay.
- `.github/workflows/ci.yml`: Python core verification plus plugin static/protocol verification.

## Testing
The publication gate requires fresh core pytest/unittest, compileall, release gate, multi-seed fuzz/integrity checks, clean wheel install, ZIP/extract verification, Python bridge protocol tests, plugin contract tests, and final tests from the exact Git tree to be published. A lack of npm network access in the audit environment is reported explicitly; the plugin package includes pinned peer/dev compatibility metadata and keyless protocol tests, but a real DeepSeek Harness install remains a downstream compatibility test.
