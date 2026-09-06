# Nolane Memory 0.6.3rc4 Release Provenance

`0.6.3rc4` is a release-engineering synchronization cut from the canonical GitHub `main` after the `0.6.3rc3` runtime and DeepSeek Harness integration were merged and verified.

## Canonical base

- Repository: `Nolane-x/Nolane-memory`
- Canonical base commit: `56e0d7499f068378590893db5b7130007d38714f`
- Merged runtime/plugin PR: #1
- Merged publication-evidence cleanup PR: #3
- Superseded draft PR #2: closed

## Scope

This cut does not claim a new semantic runtime theorem beyond the verified v0.6.3 implementation surface. It synchronizes downloadable artifacts with the GitHub source after the final DeepSeek Harness compatibility and CI patches.

The release gate continues to distinguish:

- `implementation_ready = true` when all executable implementation gates pass.
- `research_complete = false` while external empirical/independent-replication obligations remain outstanding.

## Required release evidence

The rc4 artifact workflow must pass the full Python test suite, unittest suite, compile/examples, release-contract gate at 100,000 lifelong fuzz cases / 1,024 differential cases / 1,200 SQLite persistence operations, version synchronization, and GitHub's current DeepSeek Harness workspace typecheck before the release artifact is considered canonical.
