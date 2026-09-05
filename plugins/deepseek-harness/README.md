# Nolane Memory plugin for DeepSeek Harness

Experimental Cordis adapter for DeepSeek Harness (`dsh`). It exposes Nolane Memory as model-callable tools while leaving all memory authority and correctness semantics inside the Python runtime.

## Compatibility

Pinned against the DeepSeek Harness developer-preview surface observed on 2026-09-05:

- DeepSeek Harness tools: `@deepseek-ai/dsh-tools` `0.1.3-alpha.1`
- Cordis: `@deepseek-ai/cordis` `4.0.2`
- Schemastery: `@deepseek-ai/schemastery` `3.18.2`
- Node: `^22.19.0 || >=24.0.0`

DeepSeek Harness explicitly warns that compatibility-breaking changes are expected during developer preview. Re-run `npm run typecheck` against the target Harness version before deployment.

## Safety model

The host fixes the database, authority domain and principal in plugin config. Those values are not model-facing tool arguments. Evidence captured by the model defaults to `source_authority_class=UNSPECIFIED`; the adapter does not turn model text into trusted fact. Recall only compiles pre-existing Nolane query-family/representation contracts, and typed insufficiency/overflow remains fail-visible.

## Install

Install Nolane Memory into the Python environment used by the Harness process, then install this plugin's pinned JS dependencies. Add the plugin row to a Cordis composition/profile overlay. `cordis.patch.yml` shows a standalone example.

The plugin starts a fresh Python bridge process for each call. This intentionally avoids hidden cross-call Python state. Configure `pythonExecutable` when `python3` does not resolve to the environment containing `nolane_memory`.

## Tools

- `nolane_memory_status`
- `nolane_memory_capture`
- `nolane_memory_recall`
- `nolane_memory_verify`
- `nolane_memory_release_gate` (disabled unless `enableReleaseGate=true`)

Tool results are canonical JSON strings so DeepSeek Harness result rendering cannot silently reinterpret typed Nolane receipts.

## Verification

The repository's Python suite exercises the bridge keylessly and checks the Cordis plugin contract. GitHub CI additionally installs the pinned DeepSeek packages and runs TypeScript typechecking. No model API key is required for these checks.
