# Nolane Memory v0.6.3 — executable conformance map

“Executable support” means a concrete storage/co-location owner, mandatory runtime reader and regression/harness path exists. It does **not** mean the package self-awards external empirical research closure.

| Gate / surface | Executable support | Evidence |
|---|---:|---|
| Memory Authority Domain revision/incarnation history | Yes | authority-domain revision regressions |
| Writer fence immutable history + stale-writer enforcement | Yes | writer-fence regressions + no-two-clocks audit |
| Durable write intents independent from truth durability | Yes | pre-commit crash/reconcile/expiry regressions |
| Canonical CAS/idempotency/journal integrity | Yes | K0 + crash atomicity tests |
| Evidence identity vs delivery multiplicity | Yes | K0/differential tests |
| Origin binding / authority ceiling / common-mode grouping | Yes | origin/governance tests |
| Integrity-authority admission profiles | Yes, revisioned/expiring | integrity-policy tests |
| Claim revision + valid/known time | Yes | claim temporal tests |
| Historical judgements + OR-of-AND justifications | Yes | governance tests |
| Evidence independence/support bundle receipts | Yes | durable proof receipt tests |
| Query-family revision + preservation certificate invalidation | Yes | query-family/transform tests |
| Live recoverability certificate / no stale rehydratable promise | Yes | dynamic recoverability tests |
| Semantic region split/merge + representation fibers | Yes | K1/K3 seam tests |
| Model extraction as provenance-bound candidate | Yes | extraction tests |
| Connector opacity/completeness capability | Yes | connector frontier tests |
| Contiguous exact index frontier + no self-lag | Yes | index/projection regressions |
| Typed Memory Query Domain + bounded strong absence | Yes | query-domain tests |
| Recall Cut historical incarnation correctness | Yes | replay/incarnation tests |
| Discovery/Resolution/Reconstruction/Sufficiency/Manifest receipts | Yes | projection-plane tests |
| Recall boundary fixed point / hard-role conservation | Yes | boundary tests |
| Semantic page faults / hard token overflow | Yes | K2 tests |
| Query counterexample applicability + recall quarantine | Yes | counterexample recall tests |
| Semantic OCC proposal/transition verification | Yes | proposal/verification tests |
| Semantic debt / repair / fixed-point maintenance | Yes | K3 tests |
| Witness-cover retention / irreversible gap debt | Yes | retention tests |
| Temporal coverage proof | Yes | learning tests |
| Applicability-conditioned procedure learning | Yes | learning tests |
| Selective consolidation pressure policy | Yes | learning tests |
| Access profile revision history + expiry | Yes | policy-history/expiry tests |
| Declassification revoke/expiry | Yes | security/expiry tests |
| Whole-payload information-flow gate | Yes | security-flow tests |
| Publication policy + source/destination saga revalidation | Yes | publication tests |
| Effect evidence + explicit exposure chain | Yes | effect exposure tests |
| Hard-role effect guard conservation | Yes | effect/prospection tests |
| Prospective trigger lifecycle/frontier/source/expiry | Yes | prospective lifecycle tests |
| Regime + self-version immutable histories | Yes | profile-history tests |
| Continuity pins / R0–R6 recovery | Yes | continuity/recovery tests |
| Erasure barrier / derivative taint / clean rederive | Yes | erasure tests |
| Replay/forensic classification + restore barriers | Yes | replay tests |
| Migration manifest conservative action vocabulary | Yes | research acceptance tests |
| Benchmark fairness evidence registry | Yes | research acceptance tests |
| Context scalability two-axis fail-visible probe | Yes | research acceptance tests |
| Part XIII formal suite | Yes | `run_reference_formal_suite()` — 16 families; exhaustive/fuzz sub-worlds |
| Lifelong deterministic state-model fuzz | Yes | `run_lifelong_fuzz()` |
| Independent second semantic implementation | **Yes, internal** | `independent_kernel.py` + differential tests |
| Frozen/generated independent differential conformance | Yes | `run_independent_differential()` |
| Canonical crash/lost-response fault injection | Yes | `run_fault_atomicity_probe()` |
| Closure matrix ownership audit | **48/48 primitives** | `audit_full_spec_ownership()` |
| v0.6.1 Seam Calculus | Yes | `run_v061_seam_calculus()` — 36 families / 80,553 cases |
| v0.6.2 Continuity–Recovery–Erasure Calculus | Yes | `run_v062_continuity_recovery_erasure_calculus()` — 24 / 135,880 |
| v0.6.3 Use-Time/Causal-Cut Calculus | Yes | `run_use_time_causal_cut_calculus()` — 34 / 131,701 |
| Sections 263–268 acceptance campaigns | Yes | temporal/procedure/security/migration/performance campaign methods |
| Sections 373/393/394/395/401 campaigns | Yes | recovery/privacy, publication, flow lease, resource pressure, race campaign methods |
| 402-section implementation traceability ledger | **302/302 implementation-testable COMPLETE** | `docs/SPEC_COVERAGE_LEDGER.json` |
| Machine-readable full-spec implementation gate | Yes | `run_full_spec_release_gate()` — 27 required checks |
| Real production distributed consensus/frontiers | No claim | local SQLite authority reference |
| Natural-language extraction completeness | No claim | extractor interface is provenance/verification machinery only |
| Empirical interference calibration | No claim | scoped effect model exists; calibration remains external |
| External benchmark superiority | No claim | fairness registry/portfolio only |
| Independent **external** replication | No claim | internal second kernel is not external replication |
| W5 research closure | **BLOCKED** | `k5_profile_status()` |

## Ownership closure

The executable ownership audit covers all 48 normative primitives in closure matrices 272–274. Physical co-location is allowed where one correctness clock and one mandatory reader remain unambiguous; the audit rejects missing tables/methods and duplicate/current-mirror clock drift.

## Interpretation

A green implementation gate demonstrates the bounded executable semantics represented in this package. It does not prove universal future-query safety, external provider deletion, production distributed consensus, natural-language completeness or empirical superiority.

## 402-section coverage

The v0.6.3 source specification contains 402 consecutively numbered sections. The release ledger classifies 302 as implementation-testable, 47 as research-external, and 53 as reference/narrative. The implementation release condition requires `implementation_missing=[]` and `implementation_partial=[]`; external research obligations remain visible rather than being converted into implementation PASS.

## Harness adapters

The DeepSeek Harness Cordis plugin under `plugins/deepseek-harness/` is an integration adapter, not a new semantic authority plane. Its Python bridge imports only the public `nolane_memory` package surface; host configuration fixes database/domain/principal, capture defaults to `UNSPECIFIED` authority, and typed core failures remain fail-visible. DeepSeek Harness compatibility is independently version-pinned and must not be interpreted as W5/external research closure.
