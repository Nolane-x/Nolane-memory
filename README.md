# Nolane Memory v0.6.3 — Full Executable Runtime (`0.6.3rc3`)

`nolane-memory` is a dependency-free Python/SQLite implementation of the **implementation-relevant K0–K5 contracts** in the Nolane Memory v0.6.3 specification, including Causal Recall Cuts, Semantic OCC, use-time fencing, corrigibility, governed publication, recovery/erasure and executable research/conformance gates.

The package deliberately separates two claims:

1. **Implementation readiness** — every normative closure-matrix primitive has an executable storage/co-location owner, mandatory reader and regression/harness path.
2. **Research closure** — the runtime does **not** self-certify empirical superiority, universal future-query safety or external independent replication. Those remain external evidence obligations.

## K0 — Canonical integrity and authority

- Serialized canonical write order per Memory Authority Domain using SQLite `BEGIN IMMEDIATE`.
- Immutable `MemoryAuthorityDomainRevision` history with incarnation/predecessor lineage.
- Immutable `MemoryWriterFenceRevision` history plus hot writer-epoch mirror; no-two-writable-clocks audit detects drift.
- Durable `MemoryWriteIntentRevision` lifecycle (`PENDING/COMMITTED/EXPIRED`) independent from canonical truth; crash-before-commit leaves only an auditable intent.
- Expected-base CAS, writer fencing, incarnation-scoped idempotency and lost-response reconciliation.
- Source-event identity separated from transport delivery identity; retries cannot manufacture evidence multiplicity.
- Canonical origin binding with authority ceiling/common-mode grouping and revocation/compromise lifecycle.
- Claim revision history with predecessor CAS, valid-time/knowledge-time semantics, immutable historical judgements and OR-of-AND justifications.
- Integrity-authority profiles are revisioned/expiring and rechecked at admission.
- Content-bearing bytes are excluded from immutable journal payloads; audit state keeps semantic digests so hard erasure is not defeated by a hidden audit copy.

## K1 — Representation, preservation and recoverability

- Stable semantic regions with revisioned split/merge lineage and multi-representation fibers.
- Revisioned query-family bases and structured loss vectors.
- `EXACT / BOUNDED / REHYDRATABLE / UNKNOWN / UNSUPPORTED` answerability.
- Recoverability is a live source-route proof, not a static metadata promise.
- Durable preservation and recoverability certificates carry Semantic-OCC dependencies and become stale when source/query-family/transform contracts change.
- PURE derivation cannot self-recover a lost semantic dimension; SOURCE_REBASE requires a restoring basis.
- Revisioned transformation contracts enforce protected dimensions and invalidate dependent proposals/certificates/frames.
- Model extraction is a provenance-bound candidate proposal; high-risk promotion requires typed verification.

## K2 — Recall and context virtualization

- Hard/optional Recall Roles and proactive `RecallBoundaryDescriptor -> RecallObligation` compilation.
- One coherent Recall Cut across nested strong reads, including historical incarnation correctness.
- Typed `MemoryQueryDomainRevision` binds principal, incarnation, cut, surface and completeness capability.
- Connector opacity/capability profiles distinguish transport authority from content authority and complete from partial/opaque provider domains.
- Exact index frontiers are contiguous; an isolated high sequence cannot fabricate completeness. Metadata-only frontier advancement no longer self-lags by one canonical sequence.
- Principal and applicability filtering happens before hidden influence/ranking.
- Typed `RegionDiscoveryResult`, `RepresentationResolution`, `RecallReconstruction`, `RecallSufficiencyAssessment` and `RecallFrameDependencyManifestRevision` make the projection proof inspectable without creating another truth clock.
- Semantic page faults, hard-role fixed point expansion and fail-visible token/page-fault overflow.
- Query-family scoped counterexamples can quarantine a falsified representation without deleting historical state; unrelated family/regime counterexamples do not pollute recall.
- Strong negative receipts distinguish complete/partial/opaque domains and stale on phantom/domain/frontier changes.
- Exact final payload/use is protected by a short-lived, single-use `MemoryUseFence` bound to dependencies, principal, sink and final payload digest.

## K3 — Lifelong evolution and corrigibility

- Durable semantic debt lifecycle with explicit transition outcomes.
- Query-counterexample preservation, applicability revisions, source-rebase repair and causal-local repair fan-out.
- Witness-cover retention prevents accidental destruction of the last protected semantic route unless policy explicitly authorizes irreversible loss.
- Fixed-point maintenance treats semantic no-op as success rather than rewriting memory endlessly.
- Applicability-conditioned procedure learning deduplicates semantic events and keeps contradictory regimes separate instead of averaging them into a generic rule.
- Explicit temporal coverage receipts prevent point observations from silently becoming continuous-duration claims.
- Selective consolidation triggers read canonical pressure/debt/counterexample state under revisioned policy.
- Conservative migration manifests require an explicit action for every correctness-bearing surface and reject semantic upgrades from underspecified legacy state.

## K4 — Security, effects, multi-agent publication and continuity

- Revisioned/expiring principal access profiles with operation-specific capability algebra.
- Explicit declassification receipts with revocation/expiry; disclosure authority never raises factual authority.
- Whole-payload information-flow gate and sink-specific capability checks.
- Cross-domain publication is a two-authority saga and binds revisioned publication policy; policy/source change while pending forces revalidation.
- Publication preserves origin/common-mode lineage and cannot turn a destination copy into independent evidence.
- Effect evidence is scoped by consumer/task/regime/rendering and can be linked to an explicit candidate→selected→rendered→referenced exposure chain.
- Strong negative effects may inhibit optional context but can never erase a hard role.
- Prospective triggers have expiry, source lineage, causal frontier, sticky revoke and explicit reactivation; they generate recall obligations, not action authority.
- Revisioned regime and self-version histories drive applicability and currentness checks.
- Continuity pins, layered R0–R6 recovery, incarnation barriers, replay/forensic assessments and non-revival erasure closure.
- Clean rederivation only uses surviving permitted source evidence.

## K5 — Research/conformance runtime

- Multi-view derived discovery and ambiguity-preserving reconstruction.
- Explicit degraded-capability behavior rather than silent semantic weakening.
- Full Part XIII reference formal suite: 16 property families, 32,768 answerability worlds, 20,000 loss chains, exact witness-cover/hard-frame worlds, 1,000-region repair and 50,000-step composition fuzz.
- Versioned model-free calculi: v0.6.1 Seam Calculus (36 families / 80,553 cases), v0.6.2 Continuity–Recovery–Erasure Calculus (24 / 135,880) and v0.6.3 Use-Time/Causal-Cut Calculus (34 / 131,701).
- Reproducible seeded lifelong state-model fuzzing plus real-SQLite persistence state-machine fuzz with restart/full-recomputation drift checks.
- A **second independent pure-Python semantic kernel** with separate normalization/hash/state implementation and frozen/generated differential corpus. This is implementation independence inside the package, **not external replication**.
- Real canonical fault-injection probe across pre/post mutation, journal, receipt and post-COMMIT lost-response points.
- Benchmark fairness registry, migration validity gate, two-axis context scalability probe, 263–268 acceptance campaigns, 373 recovery/privacy campaign, 393 publication-cycle campaign, 394 information-flow lease campaign, 395 resource-pressure campaign and 401 race campaign.
- Machine-enforced ownership audit for all **48 normative primitives** in closure matrices 272–274.
- `run_full_spec_release_gate()` checks 27 implementation gates, including ownership/integrity, formal/calculus suites, state-model + persistence fuzz, differential, crash atomicity, temporal/procedure/security/migration/performance campaigns, recovery/privacy, publication, use-time flow/resource pressure and longitudinal/stress protocols.
- `SPEC_COVERAGE_LEDGER.json` maps all 402 numbered sections: 302 implementation-testable sections are required COMPLETE; research-external and narrative sections remain explicitly separate.

## Verification

Current `0.6.3rc3` source is required to pass:

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests examples
PYTHONPATH=src python examples/basic_runtime.py
PYTHONPATH=src python examples/full_profile.py
```

Operator gates:

```bash
nolane-memory --db memory.db ownership
nolane-memory --db memory.db release-gate personal --seed 603 --fuzz-cases 100000 --differential-cases 1024
```

The release gate intentionally reports `implementation_ready` separately from `research_complete`.

The frozen `0.6.3rc3` evidence bundle records **250/250 pytest**, **302/302 implementation-testable spec sections COMPLETE**, a 27/27 implementation release gate, 100,000 state-model fuzz cases, 1,200 real-SQLite persistence operations, and 1,097 normalized independent-kernel differential comparisons.

## CLI

```bash
nolane-memory --db memory.db init personal
nolane-memory --db memory.db status
nolane-memory --db memory.db head personal
nolane-memory --db memory.db ownership
nolane-memory --db memory.db release-gate personal --seed 603 --fuzz-cases 100000 --differential-cases 1024
nolane-memory --db memory.db lab
nolane-memory --db memory.db fuzz --seed 603 --cases 100000
nolane-memory --db memory.db debts personal
nolane-memory --db memory.db erase personal ev_... --principal alice --policy-ref privacy:delete
nolane-memory --db memory.db recover personal --pin-id pin_... --principal alice
```

## DeepSeek Harness plugin

This repository also ships `plugins/deepseek-harness/`, an experimental Cordis adapter for the current DeepSeek Harness developer-preview plugin API. The host fixes the Nolane database/domain/principal; model-facing tools cannot choose those authority boundaries. Captured model evidence defaults to `UNSPECIFIED` authority, recall consumes only predeclared Nolane query/representation contracts, and the expensive release-gate tool is disabled unless the host explicitly enables it.

The adapter is pinned to the observed 2026-09-05 developer-preview surface (`@deepseek-ai/dsh-tools` 0.1.3-alpha.1, Cordis 4.0.2, Schemastery 3.18.2). DeepSeek Harness warns that preview APIs can break; GitHub CI installs those packages and typechecks the plugin against the real published declarations. See `plugins/deepseek-harness/README.md`.

## Project layout

```text
src/nolane_memory/
  runtime.py             canonical K0–K2 kernel, Semantic OCC, query domains/frontiers
  evolution.py           K3 debt, repair, retention, region/proposal evolution
  governance.py          origin, authority, judgement, support/independence proofs
  learning.py            temporal coverage, procedure learning, consolidation policy
  extraction.py          provenance-bound model extraction proposals/verifiers
  effects_security.py    access, flow, publication, exposure/effects, prospection
  continuity.py          recovery, replay barriers, erasure closure, handoff
  independent_kernel.py  independent pure-Python differential semantic kernel
  research.py            K5 labs/fuzz/differential/fault/ownership/release gates
  types.py               typed semantic DTOs/enums
  errors.py              typed semantic failures
  normalize.py           canonicalization and hashing
  cli.py                 operator CLI

tests/                   semantic, adversarial, crash and conformance regressions
examples/                executable examples
docs/                    conformance, limits and release evidence
```

## Honest boundary

The executable runtime can demonstrate its own bounded invariants. It cannot legitimately convert those internal results into claims of universal future-query preservation, empirical superiority, production-distributed consensus, external provider erasure, natural-language extraction completeness or independent external replication. Those remain explicit external research/integration obligations rather than hidden PASS booleans.
