# NOLANE MEMORY

## Reconstructive Semantic Virtual Memory Runtime for Long-Lived AI Agents

### v0.6.3 — Deep Consolidated Use-Time Consistency, Causal Recall Cut & Semantic-OCC Closure Research Specification

**Date:** 2026-09-01  
**Status:** semantically consolidated research architecture with v0.6.3 use-time/cut-consistency hardening; not production implementation, W5 convergence, universal dependency-extraction completeness, empirical superiority, independent validation, universal distributed consistency, or zero-bug claim.  
**Lineage:** v0.1–v0.5 are research notebooks. v0.6 is the clean semantic consolidation; v0.6.1 closes identity/repair/proactive-recall/information-flow seams; v0.6.2 closes continuity/recovery/erasure seams; v0.6.3 closes read→derive→promote/use TOCTOU, causal-cut and executable-metadata seams. No revision opens a non-memory product subsystem.

---

## 0. Executive definition

Nolane Memory is a runtime below AI agents whose purpose is not to make the model “remember more text.” Its purpose is to preserve **decision-relevant continuity of evidence, meaning, experience and learned procedure across context loss, session restart, model replacement, environment drift, compression, deletion and very long deployment histories**, while materializing only a small, justified working view into the model context.

The central object is therefore not a vector, a summary, a graph node, or a transcript chunk. The central object is a **versioned semantic region backed by evidence and capable of having multiple representations**. A region may have a raw event trace, an exact structured event representation, a compact semantic representation, a procedure derived from repeated outcomes, a failure/counterexample view, and an anchor usable during recovery. These are not six competing truths. They are six representations or roles whose authority is constrained by one evidence/justification lineage.

A memory request is also not “search for similar text.” The runtime first compiles what the current agent boundary actually needs to know: current constraints, a historical value, the negative exception to a procedure, the causal predecessor of a failure, the outcome of a previous attempt, or a continuity anchor. Those needs become a **Recall Obligation**. Retrieval then has two logically separate stages: discover relevant semantic regions, and choose the cheapest representation inside each region that is known to preserve the distinctions required by the obligation. If a compact representation is adequate, the raw source never enters context. If it is inadequate but recoverable, the runtime performs a targeted semantic page fault and hydrates a stronger representation. If the information is unavailable, ambiguous, inaccessible, or cannot fit safely, the runtime returns a typed failure instead of pretending that top-k retrieval was complete.

The architecture is intentionally asymmetric. Canonical evidence, claims, justifications, temporal state, authority and commit order are conservative. Association, multi-view search, active reconstruction, prospection and learned consolidation may be aggressive above that substrate because they are forbidden to self-promote guesses into canonical authority. A frequently recalled memory can become easy to find without becoming more true. A summary can become useful without becoming an independent source. A procedure can become popular without losing its exception conditions. A memory can be harmful to a particular weak model without its factual content becoming false.

The resulting runtime behaves more like **semantic virtual memory** than a knowledge base. Total stored history may become enormous; model context is the working set. A semantic address is resolved to a suitable representation at a pinned memory cut. The runtime keeps enough meta-state to know which representation can answer which bounded query family, which transformation lost which protected distinctions, whether stronger source material can still be rehydrated, and whether prior use of a memory has produced scoped evidence of benefit or interference. That meta-state is rebuildable and non-authoritative: it helps select memory, but it is not a second truth store.

This v0.6 specification concentrates the project around seven correctness surfaces: **canonical evidence and commit semantics; epistemic/temporal truth maintenance; representation lineage and preservation; recall obligation and reconstruction; counterexample-guided repair; recoverability-aware forgetting; and consumer-conditioned memory effects**. Episodic, semantic, procedural, failure, prospective, social and anchor memory are expressed through these surfaces rather than expanded into independent subsystems.

The strongest concise statement is:

> **Nolane Memory is a provenance-bearing, temporally explicit, multi-representation memory runtime that compiles a huge external history into a small task-relative Recall Frame while retaining the ability to explain what was preserved, what was lost, what can be reconstructed, what is uncertain, and what must not be silently trusted.**

---

# PART I — RESEARCH CORRECTION AND PROBLEM CONTRACT

# 1. Why v0.6 is a rewrite rather than v0.5 plus more sections

The v0.5 line of research produced useful semantics: answerability-relative memory correctness, semantic-loss tracking, query counterexamples, effect/interference evidence and lifelong stress testing. Its weakness was structural. A fresh byte-level analysis of the final v0.5 artifact found 1,036 numbered sections with a median of 53 words; 867 sections contained fewer than 100 words. By contrast, the supplied Nolane Plan v0.15 has 357 numbered sections with a median of 266 words and 20 sections below 100 words under the same section/word-count procedure. That difference matters because a highly fragmented document can enumerate correct statements while failing to derive how they constrain one another.

The failure mode can be called **specification atomization**. One concept receives a definition; another section names an invariant; another lists a failure; another names an oracle. A reader can verify each item locally but still be forced to invent the composition rule while implementing the runtime. That is exactly the hidden-semantic problem the research is supposed to remove.

v0.6 therefore changes the writing discipline. A numbered section should normally do several jobs together: define the semantic object, derive why it is necessary, show a counterexample to the weaker design, state the runtime consequence, identify authority/invalidations, and give a test obligation. Failure catalogues and oracle registries remain useful, but they move to tables and appendices instead of becoming hundreds of tiny numbered chapters.

This rewrite also applies a **primitive admission test**. A concept belongs in the canonical kernel only if at least one bounded counterexample shows that removing it permits two implementations to make materially different correctness decisions. If a concept only improves performance, retrieval quality, convenience, or observability, it belongs in a derived layer or policy profile. If it is merely an index over canonical state, it must be rebuildable. If it is an LLM-generated score, it cannot own authority unless an independent runtime rule explicitly gives that score a bounded role.

The research method is intentionally close to the method that made Nolane Plan strong: representation shifts must expose new inference rather than rename the same checklist; falsification is performed before broad implementation; independent verification is not self-awarded; high remaining value-of-thought keeps the research world open; and the stop rule says to add prose only when a counterexample, bounded model, migration conflict or implementation divergence demonstrates a correctness gap.

The success condition for v0.6 is therefore not “more pages than v0.5.” It is: **fewer hidden choices for the future implementer**.

---

# 2. Exact problem Nolane Memory solves

Assume an AI agent operates for months or years. It reads messages and files, uses tools, changes repositories, accumulates user preferences, learns local procedures, encounters failures, restarts, upgrades its model, changes its toolset, crosses projects, and repeatedly compresses old interactions because model context is finite. A normal memory architecture eventually faces at least six competing pressures.

First, storage grows much faster than context. A million correct memories are useless if every query requires a 200,000-token replay. Second, compression is lossy. A short summary can preserve “deployment failed” while dropping the one exception that determines whether the next deployment is safe. Third, reality changes. A statement may be historically true and currently false without either copy being a mistake. Fourth, evidence quality differs. One direct tool observation, five mirrors of the same source, and five agent summaries of that source are not ten independent supports. Fifth, memory affects behavior. Retrieved context can help, distract, poison, prime, or cause a weak model to perform worse. Sixth, the agent itself changes. A procedure learned by one model/toolset may not remain applicable to a future version.

Nolane Memory must therefore support a stronger question than “what relevant text have we seen before?” For each consequential recall, it must determine:

```text
What does the runtime currently have evidence for?
What did the past agent know or believe at the historical time of interest?
Which memories are accessible to this principal?
Which are available and still reconstructible?
Which apply to this environment, objective and executor?
Which representation preserves the semantic distinctions this query needs?
Which counterexamples or failures would change the decision?
How much of that can fit in the current context budget without silent omission?
```

The hard part is that these questions interact. A compact semantic representation may be epistemically correct but insufficient for an exact historical timestamp. A raw event may contain the timestamp but be inaccessible to the current principal. A procedure may be strongly supported in Linux and actively misleading in Windows. A past self may have deliberately left an anchor that is useful for reconstruction but obsolete under the current environment. A memory may have been correct when stored yet become a security liability after being repeatedly echoed through derived summaries.

The runtime is successful only if those interactions produce **typed, reproducible state transitions** rather than model intuition. A refusal to claim sufficiency is an acceptable memory result. An ambiguous reconstruction is acceptable. A page fault to stronger evidence is acceptable. A declared irrecoverable gap after authorized deletion is acceptable. What is not acceptable is a fluent context package that silently converts partial search, lossy compression, stale evidence or access denial into apparent certainty.

---

# 3. What Nolane Memory is deliberately not

Nolane Memory is not a generic RAG platform. RAG can be one candidate-retrieval mechanism, but semantic similarity does not define evidence authority, historical validity, query completeness or procedure applicability. It is not a single temporal knowledge graph either. Graphs are useful projections, but a graph edge may be derived, approximate, stale or inaccessible; the graph does not become the canonical truth source by being structurally rich.

It is not a second planner. Recall Obligations describe what memory evidence a bounded decision needs; they do not choose goals, search future plans or authorize actions. Prospective memory can wake a revalidation obligation when a trigger occurs, but it does not execute the resulting action. Procedure memory describes learned ways of acting under conditions; execution remains governed by the host agent/runtime.

It is not a universal ontology of human memory. Terms such as episodic, semantic, procedural and associative memory are useful, but v0.6 does not attempt to replicate a brain or claim biological equivalence. It takes mechanisms only when they produce useful engineering distinctions: associative activation for candidate discovery, inhibition for interference control, consolidation for abstraction, anchor-like cues for reconstruction, and multi-path redundancy for continuity.

It is not a global truth oracle. The runtime manages **epistemic state**: evidence, justification, disagreement, historical judgement and confidence under declared procedures. The external world can still contain facts the system never observed. `STORE_QUERY_COMPLETE` does not mean `WORLD_COMPLETE`.

It is not an excuse to persist every thought produced by a model. Private chain-of-thought, transient brainstorms and unsupported hypotheses do not become canonical memory by default. The canonical substrate stores inspectable evidence, claims, decisions, outcomes, procedures, failures and authorized derived artifacts with provenance. Candidate inference can be retained as candidate state without being laundered into fact.

It is not “one giant summary.” A rolling summary whose size or semantic responsibility grows with total history simply moves the context-window problem into a mutable artifact with harder drift detection. Nor is it “store everything raw forever.” Privacy, storage, legal deletion and operational cost can require archival or deletion. Nolane Memory makes the semantic consequence of forgetting explicit rather than assuming permanent raw retention.

Finally, Nolane Memory is not a claim that external memory is always superior to long context. Long-context and no-memory systems remain mandatory baselines. If a strong model performs better without a retrieved memory for a particular task, the runtime should be able to learn a scoped inhibition policy without rewriting the memory's truth.

---

# 4. Core thesis: evidence-preserving semantic virtual memory

The architecture can be derived from one compression fact: **an agent cannot keep its full history in working context, so every long-lived memory runtime is a compiler whether it admits it or not**. It compiles experience into representations that are cheaper to retrieve and condition on. A database row, an embedding, a summary, a graph fact and a procedure are all compiled views of a richer history.

The crucial design question is therefore not “how good is the summary?” It is: **which observables must this representation preserve?** A broad preference query may need only identity, polarity and a current-validity interval. A safety-sensitive procedure query may need negation, preconditions, exceptions, regime, causal outcome and counterexamples. A historical replay may need knowledge time, not merely world-valid time. No single scalar fidelity score captures these differences reliably.

Nolane Memory treats model context as the working set of a semantic virtual-memory system. Canonical history is backing state. Semantic regions are virtual objects. Each region can have several physical representations with different token cost, precision and recoverability. The Recall Frame compiler resolves a semantic address—roughly `(region, required observable, recall cut, principal, consumer)`—to the cheapest representation that is justified to answer it. When no compact representation suffices, it faults to a stronger source. When no source remains, it reports the gap.

This analogy is useful only because it changes operations. It creates a sharp separation between **relevance discovery** and **representation selection**. A multi-view graph or dense retriever can discover that region `R` matters. It does not decide whether the model should receive `R`'s 20-token semantic summary, its 200-token event record, its exact raw artifact handle, or a procedure/counterexample pair. That decision is made by preservation and answerability semantics.

The second half of the thesis is corrigibility. Compilation cannot anticipate every future question. Therefore the runtime does not claim universal preservation. It keeps bounded preservation contracts and treats future query failures as counterexamples. If a later question reveals that a transformation destroyed a needed distinction, the system traces the representation lineage, finds the earliest lossy boundary, rehydrates stronger source material if available, refines only the affected semantic region, and turns the failure into a permanent regression witness. If source material has been lawfully destroyed, the result is an explicit irrecoverable gap rather than a fabricated reconstruction.

This combination—**semantic virtual memory plus counterexample-guided repair**—is the center of v0.6.

---

# 5. Seven constitutional separations

Most persistent-memory failures are category errors. v0.6 begins with seven separations that must remain true even if the physical implementation is radically optimized.

**Evidence is not authority.** Evidence has origin, time, scope and quality. Authority is the runtime judgement about what an evidence set can support for a particular claim class. Repetition, popularity and embedding similarity are not independent support.

**Truth judgement is not access.** A claim may remain part of the runtime's current epistemic projection while principal `P` is forbidden to see it. Revoking access does not make the claim false. Conversely, public visibility does not make a claim trustworthy.

**Availability is not truth.** A source can be temporarily unavailable, encrypted, cold-archived or hard-deleted. That changes current verification and recoverability; it does not retroactively create contradictory evidence.

**Representation quality is not claim truth.** A summary may be faithful for broad questions and unusable for exact questions. The underlying claim can remain well supported while a particular representation has lost the field needed now.

**Activation is not authority.** Associative spreading, frequency, recency and task relevance decide what should be considered. They never promote a claim. A rarely activated counterexample can be more epistemically decisive than a highly activated rule.

**Consumer effect is not truth.** A correct memory can confuse a small model or harm a task under one rendering. Interference control may change whether and how the memory is presented; it cannot rewrite the historical fact because the model found it distracting.

**Past-self intent is not current command authority.** A previous model can leave valuable anchors, hypotheses and procedures. Future-self treats them as evidence about the prior state and must revalidate environment, tools, constraints and mission authority before acting.

Every component later in the document is required to preserve these separations. If an implementation collapses them into one `status`, `confidence`, `visibility`, or “memory score,” it is non-conforming even if benchmarks look strong.

---

# 6. The three-plane architecture

v0.6 compresses the many earlier primitives into three semantic planes.

### Canonical Plane

The Canonical Plane owns the state that cannot be reconstructed from search heuristics without changing meaning: evidence-event identities, admitted claims, justifications, historical judgements, temporal validity, origin/authority constraints, principal/access policy revisions, canonical commit order, retention/deletion events and the lineage that connects derived claims to their supports. Only a canonical transition can change current epistemic authority.

### Representation Plane

The Representation Plane owns compiled forms of canonical or previously derived state: episode views, semantic summaries, procedures, failure lessons, durative state representations, anchor packets, structured tables, typed event records and other representations. A representation is always attached to a source region and derivation path. It may be highly useful and durable, but it cannot become an independent source merely because it was stored persistently.

The Representation Plane also owns preservation contracts, semantic-loss records, recoverability metadata, transformation counterexamples and semantic debt. These objects state what the runtime knows about the representation process; they do not redefine world truth.

### Projection Plane

The Projection Plane contains query-time and maintenance-time views: lexical/dense indexes, graph adjacency, activation state, capability atlases, effect profiles, query plans, Recall Cuts, Recall Frames and caches. These structures can be rebuilt. They may materially affect performance and which candidates are discovered, so their capabilities and freshness are correctness dependencies for strong recall claims. But loss of the Projection Plane must not rewrite canonical history.

This three-plane split is more important than a particular class hierarchy. It answers the recurring ownership question: **who is allowed to say that memory meaning changed?** Search can propose. Consolidation can propose. A model can propose. A graph can expose a conflict. An effect ledger can recommend inhibition. Only the appropriate canonical or representation transition, with its declared evidence and policy checks, can commit the semantic change.

---

# 7. Formal universe and notation

The reference model uses the following sets. They are conceptual interfaces, not a requirement to store mathematical objects literally.

```text
E   evidence events and admitted source artifacts
C   claim revisions / historical judgements
J   justification structures over evidence and claims
G   semantic memory regions
R_g representations belonging to region g
T   transformation / derivation revisions
Q   bounded query-family contracts
P   principals and access-policy revisions
U   consumer profiles (model/tool/runtime capability)
Ω   environment / schema / tool / objective regimes
K   canonical commit sequence / compatible snapshot order
X   effect evidence and scoped interference profiles
D   protected semantic dimensions for a domain/profile
```

At canonical commit `k`, the memory state is conceptually:

\[
M_k = (E_k, C_k, J_k, G_k, T_k, P_k, \Omega_k, H_k)
\]

where `H` denotes historical retention and policy state. Derived indexes and model-facing frames are intentionally excluded from this authoritative tuple.

A representation `r ∈ R_g` carries a derivation relation to one or more source revisions. A query family `q ∈ Q` declares a bounded set of semantic requirements `Req(q)`—for example exact negation, broad temporal existence, an exception condition and a regime identifier. A Recall Cut `κ` binds the memory/evidence/access/regime state against which a strong recall is evaluated.

We use a multi-valued answerability relation rather than a Boolean:

\[
A(r,q,\kappa) \in \{EXACT, BOUNDED, REHYDRATABLE, UNKNOWN, UNSUPPORTED\}
\]

`EXACT` means the current representation is certified to preserve the family under the declared normalization. `BOUNDED` means the representation is adequate only under explicit tolerance or scope. `REHYDRATABLE` means the representation is insufficient but a stronger authorized/recoverable path is known. `UNKNOWN` means the runtime lacks a justified capability result. `UNSUPPORTED` means the declared representation/source path cannot answer the family under the current contract.

A consequential Recall Frame is not valid merely because every included memory is relevant. It must be a **feasible witness cover** for a Recall Obligation: every hard role has at least one usable, epistemically admissible, cut-compatible witness; unresolved contradictions/required counterexamples are represented; and the frame fits the budget. Optimization—fewest tokens, lowest latency, best model effect—occurs only after feasibility.

These definitions allow later laws to be stated independently of whether the physical store is SQLite, Postgres, RocksDB, a property graph, an ANN service or an append-only object store.

---

# 8. Semantic regions: the unit of repair, not the unit of storage

A **Memory Region** is the smallest semantic area the runtime intends to update, invalidate, recompile or repair independently. The region is not necessarily one chat turn and is not necessarily one database row. It is a correctness locality boundary.

Examples include an episode, one durative state of an entity, a procedure family with its applicability conditions, a user preference cluster under one scope, a failure mechanism, or a decision episode with its evidence and outcome. A large conversation can contain many regions; one region can draw source evidence from several messages or tool observations.

The main reason regions exist is blast-radius control. Suppose a future query reveals that a compact representation of procedure `P` lost the exception `SAFE=false`. If `P` lives in its own region, the runtime can rehydrate and rebuild that representation without invalidating an entire project summary. Conversely, if two memories cannot be corrected independently because they share one inseparable semantic invariant, splitting them into separate regions would create false locality and should be rejected.

Region identity is stable across representation changes. A new summary, a raw-source rebase and a procedure-specific view can all remain representations of the same region. A genuinely new event or changed real-world state may create a new region or new canonical claim revision depending on the domain semantics.

Regions also solve an old taxonomy problem. “Episodic memory” and “semantic memory” do not have to be separate stores. A region sourced from one episode may expose an episodic representation for historical reconstruction and a semantic representation for current fact recall. The runtime can choose the appropriate form at query time while maintaining one origin and justification lineage.

**Counterexample.** If a system stores a raw event, a summary fact and a learned procedure in unrelated stores with no common region/derivation identity, revoking the source event may stale one representation while the others remain active. The problem is not insufficient retrieval; it is missing semantic co-ownership.

**Test obligation.** A region-level repair test must show that changing one region does not alter unrelated region digests, while all representations whose correctness depends on the changed source are revalidated or invalidated.

---

# 9. Representation fibers: multiple granularities without multiple truths

For a region `g`, define its **Representation Fiber** `R_g` as the set of currently known representations derived from that region's evidence and claim state. “Fiber” is an engineering metaphor rather than a claim that the runtime implements a mathematical fiber bundle. It expresses one useful separation: cross-region search asks *which semantic region matters?*; within-region resolution asks *which representation of that region should be materialized?*

A fiber may contain:

```text
raw artifact handle
normalized event record
durative temporal assertion
compact semantic summary
procedure representation
failure/counterexample view
exact structured fields
anchor / continuity pointer
```

Representations differ in token cost, latency, semantic precision, principal usability and recoverability. The runtime should not permanently crown one of them “the memory.” A 20-token summary may dominate a raw transcript for a current broad preference query. The raw transcript may dominate the summary for an exact quotation or historical-boundary query. Two representations can be incomparable.

This is the point at which v0.6 departs from the common “retrieve memory items then stuff them into context” pattern. Retrieval operates first on region-level relevance and structural relations. The second stage resolves a representation based on the actual Recall Obligation. This means the same relevant region can cost 15 tokens in one decision and require a 2,000-token source hydration in another without duplicating the canonical fact.

A representation fiber is also where semantic-loss and query-counterexample knowledge belongs. If `r_summary` is known to preserve identity and broad temporal order but lose exact numeric values, the capability is attached to that representation lineage. The raw source does not become “low fidelity” just because the summary is lossy.

**Anti-pattern.** Creating `EpisodicMemoryStore`, `SemanticMemoryStore`, `ProcedureMemoryStore`, `FailureMemoryStore` and `AnchorStore` as independent truth owners is rejected unless a future counterexample demonstrates a need for separate canonical authority. Specialized physical indexes are fine; specialized truth universes are not.

---

# 10. Canonical evidence events and semantic event identity

Persistent learning begins with event identity. A source event and a transport delivery are different concepts. An email provider may redeliver one message. A tool adapter may retry the same callback. A sensor may independently observe the same value twice. Text equality cannot distinguish those cases.

An `EvidenceEventRevision` therefore binds, where the source allows it:

```text
evidence_event_id
source_event_identity
source_incarnation / connector revision
transport_delivery identities
origin binding
principal / actor
world event time
observed time
ingested time
raw artifact/content digest or handle
trust/authority class
visibility scope
correlation / causal action refs
```

The source-event identity is used for epistemic idempotency. Two deliveries of `source_event_id=42` are one evidence event unless the source contract says otherwise. Two independent events whose bytes are identical can remain separate observations.

When an external source provides no stable event identity, the runtime may use a heuristic dedupe capability. It must expose that limitation. A content hash plus a one-minute window can be operationally useful; it cannot be silently treated as proof that duplicate-looking records are the same semantic event. For high-assurance procedure promotion or corroboration counting, uncertain identity must not default to “independent.”

This distinction is directly motivated by a fresh Nolane World source counterexample. The current `ExperienceLibrary` can append the exact same `Experience.id` twice and then satisfy `min_support=2` from the two rows. The storage operation is working as written; the semantic error is that row multiplicity is being treated as experience multiplicity.

**Kernel rule:** transport multiplicity, storage-row multiplicity, text multiplicity and evidence-event multiplicity are four separate quantities.

---

# 11. Claims, historical judgements and justification algebra

Evidence events are not directly equivalent to claims. A claim is an interpreted proposition under temporal, subject and scope semantics. The same evidence can support several claims, and one claim can have several alternative support paths.

A claim revision contains at least a subject/proposition identity, semantic profile, world-valid interval, current epistemic state, source/derivation links and the justification structure that explains why the runtime is willing to use it. Historical judgements are preserved separately: if an agent believed `X` at time `t` and later evidence proves `¬X`, the current epistemic projection changes while the historical record “the agent judged X at t using evidence set S” remains true as audit history.

Justification is represented as an OR-of-AND structure rather than one flat evidence list. For example:

\[
(A \land B) \lor C
\]

means either `A` and `B` together support the claim, or `C` independently does. Retracting `B` invalidates the first route but does not kill the claim while `C` remains live. Retracting `B` and `C` removes all grounded alternatives. This is the same reason a descendant memory must not automatically become stale just because one parent was revoked if another independent live justification remains.

Grounding is origin-aware. A cycle `A supports B; B supports A` with no trusted root does not manufacture authority. Copies, summaries and agent echoes of one origin do not become independent branches. A derivation procedure is itself part of the assurance path: true sources do not guarantee that a lossy abstraction preserved the exception needed by the target claim.

The current epistemic status is therefore a function of live justification paths, origin authority, dependence/common modes, counterexamples, temporal validity and derivation capability. It is not a confidence counter incremented whenever a support method is called.

**Test obligation:** replaying the same evidence operation any number of times must leave the semantic support state unchanged after the first accepted application.

---

# 12. Time is four different questions, not one timestamp

Long-lived memory breaks when dialogue order is mistaken for world time. v0.6 retains four explicit temporal questions.

`CURRENT_EPISTEMIC` asks what current admitted evidence supports now. `VALID_AT(t)` asks what current evidence indicates was true in the world at historical time `t`. `KNOWN_BY(t)` asks what evidence/derived memory had actually become available to the relevant principal by `t`. `JUDGED_AT(t)` asks what the system actually concluded at `t` under the evidence and procedures then available.

These modes are intentionally non-equivalent. A late log can prove today that a service was broken at 14:00 yesterday. It cannot retroactively give yesterday's agent access to that log when reconstructing why it chose an action at 14:05. A rule derived by consolidation at 16:00 can describe a pattern that existed all day; it still was not available as a learned rule at noon.

Temporal memory also requires durative state. Two observations `X=true` at `t1` and `t3` do not automatically prove uninterrupted `X=true` at every instant between them unless the domain provides continuity semantics or coverage evidence. Conversely, representing a persistent preference as hundreds of point facts creates fragmentation and makes duration reasoning unnecessarily difficult.

A temporal assertion can therefore carry an interval with boundary semantics, coverage basis and uncertainty. Exact boundaries, broad existence and “ever true” are different query families. A compact durative representation may be exact for broad state existence but `UNKNOWN` for an exact sub-second boundary.

The key conservation law is **non-retrocausal knowledge**: commit arrival time can change current retrospective belief about the past, but cannot make evidence available before it was observed/derived. This law must survive replay, migration and summary reconstruction.


---

# PART II — REPRESENTATION CALCULUS AND PRESERVATION

# 13. Product state: memory does not have one universal `status`

Earlier memory systems often attach one status such as `active`, `stale`, `archived` or `revoked` to an item. That is attractive for implementation and dangerous for semantics. A memory can be historically true, current-inapplicable, cold-archived, inaccessible to one principal, exactly recoverable, low-activation and still strongly justified. No single enum can represent that without making unrelated state transitions overwrite one another.

v0.6 therefore models memory state as a product of orthogonal dimensions. A concrete implementation may normalize or denormalize these fields, but their meanings remain separate:

```text
epistemic        candidate / supported / verified / disputed / revoked
world-temporal   current / historical / future-conditioned / interval-unknown
knowledge-time   available-from / historical-known / later-derived
availability     hot / available / hydrate-required / opaque / unavailable
access           principal-relative discover/read/use/derive/disclose/export
applicability    applies / does-not-apply / unknown under task+regime+consumer
retention        hot / warm / cold / tombstoned / hard-deleted
recoverability   exact / source-rehydratable / new-evidence-required / irrecoverable
activation       task-relative dynamic retrieval state
interference     consumer/task/regime/rendering-relative effect state
```

The product-state model prevents semantic laundering. `ARCHIVED` does not mean `STALE`. `PRIVATE` does not mean `LOW_CONFIDENCE`. `LOW_ACTIVATION` does not mean `UNTRUSTED`. `SOURCE_UNAVAILABLE` does not mean `FALSE`. `HARMFUL_FOR_MODEL_A` does not mean `REVOKED`.

The model also makes invalidation more precise. Revoking a source can downgrade epistemic support and recoverability while leaving historical availability records intact. Changing principal permissions alters access without changing claim truth. A model upgrade can invalidate an interference profile and procedure applicability while leaving event history untouched. Hard deletion can destroy future reconstruction paths while preserving, subject to policy, a non-content audit fact that deletion occurred.

**Implementation consequence:** APIs that expose a single `status` may do so only as a derived convenience projection for a declared operation. The canonical runtime cannot branch correctness on that convenience token alone.

---

# 14. Semantic dimensions are protected observables, not a universal ontology

A compression system cannot know what it preserved unless the runtime names the distinctions that matter. v0.6 calls these **semantic dimensions**. They are not an attempt to encode all meaning into a fixed schema. They are a bounded set of observables whose loss can change a declared class of memory decisions.

Common dimensions include identity, polarity/negation, numeric value, unit, comparison operator, quantifier, temporal point, interval boundary, event order, precondition, postcondition, exception, causal direction, entity role, objective relation, regime, principal scope and failure severity. Domain-specific profiles can add dimensions such as database transaction isolation, compiler target, medication unit or game-state phase when those distinctions matter to the application.

The reason to keep the profile bounded is practical. If “all possible semantics” is required before any consolidation can occur, the memory system has merely reinvented the original context. The protected dimension profile is therefore selected by the memory form, known query families, risk policy and observed counterexamples. A conversational episode may initially protect identity, preference polarity and broad temporal order. A procedure derived from the same region may additionally protect preconditions, exceptions, stop conditions, postconditions and executor capability.

Dimensions can be structured. “Time” is not one bit; broad interval existence, exact start boundary, exact end boundary and ordering may be separate. “Causality” may distinguish direct tool receipt, inferred causal direction and correlation. The profile should expose the distinctions needed for correct query-family comparison without forcing a universal theorem prover.

A semantic dimension is not authoritative because an LLM named it. High-assurance profiles are versioned runtime policy or verified domain definitions. A model may propose a new protected dimension when a counterexample exposes a gap, but the proposal itself does not retroactively certify old representations.

---

# 15. Transformation contracts: compression is a state transition with obligations

Every transformation from one representation to another declares why it is being performed and what it is allowed to lose. Examples include event normalization, semantic summarization, segment consolidation, procedure extraction, failure abstraction, durative-state construction and source rebase.

A `TransformationContractRevision` binds:

```text
transformation kind and implementation/profile revision
source representation revisions
target representation kind
semantic dimension profile
protected query-family obligations
allowed normalization/coarsening
forbidden losses
expected recoverability after transform
required counterexample/probe suite
principal/confidentiality restrictions
resource budget
```

The contract changes the design from “generate a summary and estimate quality” to “compile a representation under explicit observable obligations.” A low-risk narrative summary may allow numeric coarsening. A procedure representation may forbid losing negation, preconditions or negative exceptions. A continuity anchor may intentionally discard narrative detail while preserving objective revision, hard constraints, open hypotheses, plan frontier and evidence handles.

Transformations are proposals until verified/admitted at their required assurance level. This directly prevents a source issue found in the current Nolane World `MemoryConsolidator`: the caller supplies `abstraction_loss`, so a candidate that deletes a safety precondition and exception can still claim `abstraction_loss=0.0` and become eligible. In v0.6, producer self-report can be diagnostic input but not correctness authority.

A transform also declares whether it is **pure** or **re-grounding**. A pure transformation uses only the semantic content of its source representations and therefore cannot recover information already lost upstream. A source rebase or newly admitted evidence is a different operation and creates a new derivation branch. This distinction is critical for cumulative-drift analysis.

---

# 16. Semantic-loss algebra: why fidelity is a vector before it is a score

A single fidelity score can conceal exactly the error that matters. A representation can preserve nine dimensions perfectly and lose one negation that flips a procedure decision. Averaging those ten outcomes into “90% faithful” is useless for hard correctness.

For each protected dimension, a transformation can produce states such as:

```text
PRESERVED_EXACT
PRESERVED_NORMALIZED
COARSENED
LOST
UNKNOWN
NOT_APPLICABLE
```

These states are not universally linearly ordered. `UNKNOWN` is not “slightly worse” than `COARSENED`, and `NOT_APPLICABLE` is not a quality value. The transformation's semantic-loss vector is therefore a product object. Dashboards may derive scalar diagnostics; admission and answerability logic use the structured states.

The key composition law is conservative. Along a **pure derivation chain**, once a required distinction is `LOST`, a later pure transform cannot mark it `PRESERVED_EXACT` unless it identifies a restoring basis. A later summary may generate a sentence that happens to contain the missing detail, but without source or new evidence that sentence is unsupported reconstruction, not recovered memory.

`COARSENED` composes according to dimension-specific rules. `97.36 → about 97 → roughly 100` may remain adequate for “was it around one hundred?” while losing “was it below 97.5?” Exact interval boundaries can become broad durations. A causal relation can degrade to temporal association. These operations need dimension-specific normalizers rather than one numeric distance.

The semantic-loss algebra gives cumulative fidelity a causal explanation. Instead of saying “generation 8 summary drifted,” the runtime can identify the earliest transform at which `exception` changed from `PRESERVED_EXACT` to `LOST`, then determine whether the source path still exists.

---

# 17. Bounded query families: define observables without enumerating natural language

Future user questions are open-ended, so Nolane Memory cannot pre-register every possible string. The correct bounded object is a **query-family contract**: an equivalence class of queries that depend on the same memory observables for the purpose of a runtime decision.

Examples include:

```text
CURRENT_USER_PREFERENCE
HISTORICAL_VALUE_EXACT
HISTORICAL_STATE_EXISTENCE
DURATIVE_STATE_EXACT_BOUNDARY
EVENT_ORDER
PROCEDURE_APPLICABILITY
PROCEDURE_NEGATIVE_EXCEPTION
FAILURE_REPRODUCTION_CONDITION
FAILURE_ROOT_CAUSE
PRIOR_ATTEMPT_OUTCOME
CONTINUITY_PROTECTED_CONSTRAINT
```

The sentences “Can I use procedure P on Windows?”, “Does P apply under Windows?” and “Is Windows supported by P?” can compile to one applicability family. “Has P ever succeeded on Windows?” belongs to a historical-evidence family even though the wording is similar. Embedding neighborhoods are therefore not query-family definitions.

A family declares required semantic dimensions, relation kinds, temporal precision, quantifier precision, applicability semantics and answer normalization. It can also declare a refinement relation to another family. If exact-boundary memory is sufficient for broad-existence under a verified mapping, the runtime can reuse the stronger result. It cannot infer monotonicity from the English names of the families.

New wording does not automatically create a new family. The query compiler attempts to map it to existing semantic obligations. If the query depends on a distinction outside the current basis, the result remains `UNKNOWN/UNSUPPORTED` and can create a proposal for a new family or dimension if the use is important enough. This is how v0.6 avoids the query-family explosion attack.

The family registry is governance, not model preference. An LLM may be used to parse a question into candidate obligations, but the compiled contract has typed semantics and can be tested independently.

---

# 18. Preservation envelopes are property-specific capability certificates

A **Preservation Envelope** answers a narrow meta-memory question: for representation `r`, under current source/transform/profile revisions, what bounded query families is `r` known to answer and by which recovery path?

An entry may state:

```yaml
PROCEDURE_APPLICABILITY:
  answerability: EXACT
  evidence: transformation-certificate-17

EXACT_HISTORICAL_VALUE:
  answerability: REHYDRATABLE
  source: raw-artifact-42

DURATIVE_STATE_EXACT_BOUNDARY:
  answerability: UNKNOWN
```

The envelope is not a global quality score and not a promise about future unknown queries. A new family begins as unknown unless a property-specific refinement relation proves otherwise. This is important because “summary answered all queries seen so far” is only empirical evidence over the observed family set, not universal preservation.

The envelope is derived capability state, not a second truth store. Its exact physical representation can be rebuilt from transformation contracts, loss vectors, probes, counterexamples, recoverability state and policy. If the envelope index is deleted, memory becomes slower or more conservative; canonical historical facts do not change.

The envelope is also cut-bound. Source deletion, discovered transform counterexamples, schema migration, query-family revision or a change in protected dimensions can invalidate old capability claims. The runtime must not retain `EXACT` merely because the summary bytes themselves are unchanged.

This object enables the semantic virtual-memory design. Before hydrating a large source, the frame compiler can ask whether a small representation is already certified for the required family. The answer is not “this summary seems relevant.” It is “this representation is known, under contract C, to preserve the distinctions family Q requires.”

---

# 19. Capability is a preorder, not a universal ranking

It is tempting to rank memory representations by a scalar such as fidelity, confidence or granularity. v0.6 rejects a universal total order. Representation capabilities are **property-scoped and partially ordered**.

For a fixed query-family basis, cut, assurance profile and accessibility regime, define `r1 ⪰ r2` when every protected query obligation that `r2` can satisfy at the required assurance is also satisfiable by `r1`, with no weaker correctness semantics. Cost is deliberately excluded from this relation. A larger raw representation may capability-dominate a summary while being much more expensive. A structured exact-field representation may dominate raw text for a numeric query while lacking narrative information needed elsewhere. Some pairs are incomparable.

This matters for optimization. The recall compiler should search a **Pareto frontier** over capability, cost, latency, context tokens and consumer effect rather than pretend that one “best memory” exists. A representation with 20 tokens can be preferable when it covers the current hard obligations exactly. A 2,000-token source can remain the fallback witness that protects corrigibility.

The relation may itself be unknown. Two representations can have insufficient probe evidence to establish domination. `UNKNOWN` must not be coerced into “probably equivalent” merely to simplify pruning. Approximate physical storage can still use heuristic rankings, but those rankings cannot justify discarding the only known witness for a protected query family.

The capability preorder also clarifies migration. A new summarizer or representation format does not automatically replace the previous one. It can do so for a set of query obligations after the runtime establishes property-specific equivalence or refinement. This creates a much more precise deprecation rule than “new version scored higher on average.”

---

# 20. Answerability and recoverability are separate axes

A compact representation can fail to answer a query even when the memory system can still recover the answer. Conversely, a representation can currently contain an answer whose source lineage has been destroyed, making future re-verification impossible. These are different states.

v0.6 uses at least the following answerability outcomes:

```text
EXACT
BOUNDED
APPROXIMATE   # only where the consumer contract explicitly permits approximation
UNKNOWN
UNSUPPORTED
```

Recoverability is separate:

```text
IN_REPRESENTATION
SOURCE_REHYDRATABLE
ALTERNATIVE_WITNESS_AVAILABLE
NEW_EVIDENCE_REQUIRED
IRRECOVERABLE_UNDER_CURRENT_RETENTION
SCOPE_BLOCKED_FOR_PRINCIPAL
```

Suppose a summary says “the deployment failed in the afternoon,” while the raw event contains `14:37:12`. The exact-time query is not answerable from the summary, but it is source-rehydratable. If privacy policy later hard-deletes the event, the exact-time family becomes irrecoverable unless another witness exists. The broad-afternoon query can remain exact for the summary.

This distinction prevents two opposite errors. The runtime does not say “we never knew it” when only the compact representation is insufficient. And it does not hallucinate that a lost exact detail can be reconstructed because the summary still sounds semantically rich.

Recoverability is principal-relative only at the use layer. The global runtime can know that a source exists while principal `P` is forbidden to hydrate it. In that case global recoverability may be `SOURCE_REHYDRATABLE` while `P` receives `SCOPE_BLOCKED`, preserving the truth/access separation.

---

# 21. Semantic debt: represent what the runtime knows it cannot safely compress away

Memory systems accumulate uncertainty that is not equivalent to falsehood. A transform may be unverified for a newly introduced query family. A source may have been deleted before a future distinction was known to matter. An interference profile may be stale after a model upgrade. A procedure may have strong support but unknown dependence among evidence sources. v0.6 records these unresolved conditions as **semantic debt**.

Debt entries identify a subject region/representation, the missing guarantee, potential consequence, current workaround, evidence needed for discharge and the policies that permit continued use despite the gap. Examples include `FUTURE_QUERY_PRESERVATION_UNKNOWN`, `SOURCE_RECOVERABILITY_LOST`, `INDEPENDENCE_UNCERTAIN`, `INTERFERENCE_PROFILE_STALE`, `TEMPORAL_COVERAGE_GAP` and `TRANSFORM_COUNTEREXAMPLE_UNREPAIRED`.

Debt is not a penalty score to minimize at any cost. Some debt is acceptable because the relevant family is low risk, source retention is legally impossible, or the runtime can fail closed on demand. Other debt blocks procedure promotion, strong Recall Sufficiency or deletion of the last raw witness.

Debt also cannot disappear through maintenance. Re-summarizing a region, lowering its activation or moving it to cold storage does not solve an unresolved preservation problem. A debt leaves the active set only through a typed transition: evidence or verification discharges it; a new contract supersedes it; authorized policy explicitly waives it; or retention destroys the memory under a policy that accepts the resulting capability loss.

This makes the system honest about open-world limits. Instead of claiming that a compact representation is “complete enough,” the runtime can say exactly which preservation obligations are proven, which are recoverable, and which remain debt.

---

# 22. Counterexample-guided memory repair

The runtime cannot know every future question at consolidation time. v0.6 converts this impossibility from a vague caveat into an online repair mechanism inspired by counterexample-guided abstraction refinement.

When a query is executed against both a compact representation and a stronger admissible source—or when a trusted external outcome proves that the compact representation caused a decision-relevant omission—the runtime can create a `MemoryQueryCounterexampleRevision`. The counterexample records the semantic region, query family, source answer/evidence, representation answer, exact distinction lost, decision relevance and transformation lineage.

Repair proceeds locally:

1. identify the earliest transformation where the required dimension became lost or unknown;
2. determine whether a stronger source/witness is still recoverable;
3. if recoverable, rehydrate and create a new representation under a refined transformation contract;
4. update only the affected preservation envelope/fiber and dependent views;
5. keep the counterexample as a permanent regression witness;
6. if no source exists, create an explicit irrecoverable gap rather than synthesizing the missing fact.

The repair target is a semantic family or dimension, not the exact wording of one failed query. This is essential to avoid overfitting. If the failure is “negation was lost in procedure exceptions,” the fix protects the negation/exception dimension for that procedure-memory contract; it does not pin the literal test question into every future summary.

Locality is equally important. A failure in region `r317` must not trigger global invalidation unless the derivation graph proves a broader dependency. The bounded formal lab for v0.6 includes a 1,000-region repair world in which a counterexample changes only the affected region's version.

---

# 23. Witness-cover forgetting: forgetting is an optimization under semantic obligations

Age-based deletion, LRU and “low retrieval count” are storage heuristics, not correctness criteria. v0.6 reframes forgetting as a **witness-cover problem**.

For a region, policy declares a set of protected semantic obligations: query families, audit obligations, recovery obligations, counterexample requirements or regulatory retention constraints. The runtime may archive or delete a representation only if the remaining representations and recoverable source paths still provide an adequate witness for every protected obligation—or the authorized policy explicitly accepts an irreversible loss and records the resulting debt.

Conceptually, if `Protected(g)` is the set of obligations for region `g`, a retained set `W` is safe when every `q ∈ Protected(g)` has at least one admissible witness in `W` or a declared external recovery path. Cost optimization then tries to find a cheaper witness cover. Exact minimum cover can be combinatorial; correctness does not require solving an NP-hard optimum. It requires never calling a deletion “safe” when no feasible witness remains. Greedy or bounded algorithms are acceptable after the feasibility rules are correct.

This produces intelligent forgetting. A huge raw episode can be deleted after a compact exact-field representation plus a verified procedure/counterexample representation cover all protected obligations. Another raw source may need to remain cold indefinitely because it is the only path to an exact historical family that policy protects. A privacy deletion can override the witness-cover preference; in that case the runtime records the capability loss rather than blocking lawful deletion.

Forgetting therefore changes **accessibility of evidence**, not historical truth by implication. It can make a future question irrecoverable. It cannot make the opposite answer true.

---

# 24. Meta-memory is a capability index, never a recursive truth universe

Once the runtime tracks preservation envelopes, recoverability, transform counterexamples, semantic debt and memory effects, it effectively has “memory about memory.” v0.6 keeps this reflective layer bounded.

The meta-memory layer answers operational questions such as:

```text
Which representation of region R is cheapest for family Q?
Which transform profile has failed on negative exceptions?
Which regions have no raw-source recovery path?
Which memory is harmful for consumer U under rendering V?
Which capability certificate became stale after source deletion?
```

A `MemoryCapabilityAtlas` can index these answers, but it is derived from canonical transformation receipts, probes, counterexamples, retention state and effect evidence. It has no independent authority. Delete the atlas and the runtime may have to recompute or hydrate more data; canonical claims remain unchanged.

Reflection stops here. The system does not create an infinite chain of “meta-memory about the capability atlas about the preservation envelope.” Meta-layer integrity is protected by the same canonical commit, dependency and replay mechanisms used elsewhere, and by ordinary tests that rebuild the atlas from source receipts.

This bounded reflection is strategically important. It makes the runtime aware of its own representational limitations without creating a second ontology that must itself be remembered through another memory system. The future agent can ask the memory runtime, “Do you still have enough evidence to answer this exactly?” and receive a capability answer rather than a generated guess.


---

# PART III — CANONICAL WRITE, ADMISSION AND EVOLUTION

# 25. One correctness writer per Memory Authority Domain

A memory runtime can lose correctness before retrieval ever begins. Two writers can independently read the same old state, compute different corrections, and both append successfully. A hash chain can remain tamper-evident while its logical sequence is broken. Retried support operations can inflate assurance even when a provenance set deduplicates the source string. These are state-transition failures, not “memory quality” problems.

v0.6 keeps the conservative default established in v0.3: each **Memory Authority Domain** has one serialized canonical correctness order. The domain is the smallest scope that requires one authoritative sequence of evidence/admission/claim transitions—for example one personal memory space, one project partition, or one governed shared-memory partition. Expensive candidate work can occur in parallel. Only the final authority-changing commit is serialized or protected by an equivalent CAS/fencing mechanism.

A write intent binds the expected canonical base, producer principal, authority/access policy revisions, source-event identities, origin bindings, requested scope, operation ID and request digest. If the base changed while a consolidator was thinking, the proposal is stale and must be revalidated or rebuilt. If the writer failed over, a writer-epoch/fencing token prevents the old process from committing after a new writer became active.

The physical implementation can be SQLite `BEGIN IMMEDIATE`, compare-and-swap on a content-addressed state root, a transactional KV store or a future distributed protocol. The semantic invariant is independent of that choice: **there is one explicit linearization result for a correctness-bearing write in the authority domain**.

This rule is grounded in the supplied Nolane World source itself. The simple `HashJournal.append()` path can be broken by concurrent tail readers, while the stronger `WorldStoreV5` pattern uses transaction, expected-version conflict detection and idempotency binding. v0.6 selects the stronger semantic pattern rather than inheriting every old memory utility unchanged.

---

# 26. Idempotency: retry count must never become evidence count

Persistent agents routinely encounter uncertain write outcomes. A network response can disappear after the commit succeeded. A process can crash between durable mutation and acknowledgement. An at-least-once event transport can redeliver the same source event. If retries are not semantically idempotent, operational reliability becomes epistemic corruption.

Every consequential memory operation has an operation identity and normalized request digest. The rule is:

```text
same operation ID + same semantic request
    -> same commit receipt / same semantic outcome

same operation ID + different semantic request
    -> IDEMPOTENCY_CONFLICT
```

If the caller loses the response, it reconciles by operation ID before generating a new one. An unknown outcome is not evidence that the first write failed. If old idempotency metadata has aged beyond the declared reconciliation horizon and the runtime can no longer determine whether the operation committed, the safe result is `RECONCILIATION_REQUIRED`, not blind replay.

Idempotency must cover **semantic side effects**, not merely storage membership. A previous Nolane World memory path stored trusted support in a set but increased confidence on every `add_support()` call. After five calls with the same source, support cardinality remained one while confidence rose toward 0.99. v0.6 forbids that class of bug by deriving assurance from canonical support state rather than incrementing it per API invocation.

The same principle applies to procedure learning and experience counts. Two deliveries of one event cannot satisfy “two independent successful experiences.” Duplicate consolidation jobs cannot create two authority increments. Retrying deletion cannot accidentally target a newly recreated incarnation of the same logical ID. Operation idempotency and evidence-event idempotency are separate and both are required.

---

# 27. Origin binding and authority ceilings

Lineage is useful only if transformations cannot rewrite where evidence came from. Agent memory is particularly vulnerable because untrusted material can be summarized by the agent, echoed by a trusted tool, copied into another memory, and repeated by several workers. A naïve lineage system can make the final text look like many trusted sources even though all paths descend from one untrusted origin.

An `OriginBindingReceipt` is therefore created at the earliest trustworthy boundary. It records source origin identity, transport/channel, principal or external identity where known, source authority class, common-mode group, raw evidence digest/handle, time, scope ceiling and the procedure that bound the origin.

Pure transformations propagate the origin's authority ceiling. Summarization, paraphrase, compression, embedding, clustering, agent restatement and storage by a trusted conduit do not create new factual evidence. A browser tool can be authoritative for “these bytes were fetched from URL X”; it is not automatically authoritative for “the claims in those bytes are true.” A future institutional memory store does not increase the authority of imported content merely because the destination store is trusted.

Authority elevation is a separate admission event. It can occur when genuinely independent admitted evidence, an authorized user assertion within its subject scope, a verified test receipt, or another policy-recognized source provides new support. The elevation does not rewrite the historical origin of the earlier source.

This produces a non-malleability rule: **representation change may alter usability; it cannot silently improve source authority**.

---

# 28. Integrity authority and confidentiality are two different policy dimensions

A memory may be highly trusted and highly private. It may be publicly visible and weakly supported. Conflating trust with disclosure is a severe design error.

The integrity-authority profile answers questions such as “Is this source authoritative for the user's current stated preference?” or “Can this tool receipt establish that a file write succeeded?” Authority is scoped by subject, claim kind, operation class and validity regime. There is no universal `trust=0.92` that authorizes every proposition.

The confidentiality/access profile separately answers who can discover the memory, read content, use it for reasoning, derive from it, disclose it to another principal, or export it. Some hosts may collapse these rights operationally, but the semantic distinction remains.

Derived confidentiality is monotone by default. If a representation depends on one public source and one principal-private source, the transform does not get to choose public visibility because its output sentence appears harmless. A broader disclosure requires an authorized declassification transition, potentially including a sanitization/leakage check. Declassification changes disclosure authority; it does not raise factual integrity and does not create independent evidence.

This separation is essential for multi-agent memory. Principal filtering occurs before candidate discovery, graph activation and effect estimation where hidden influence itself could leak information. A post-hoc redaction layer is insufficient because a private memory can alter ranking, procedure selection or the questions an agent asks even if its text is never printed.

---

# 29. Transition verification: coverage, preservation and faithfulness

A memory write can be syntactically valid and semantically destructive. TrustMem's 2026 transition-level framing is useful because it separates three failure modes that a single confidence score hides: **coverage, preservation and faithfulness**.

Coverage asks whether the update retained the important new information it was supposed to absorb. A user correction `A → B` that keeps only `A`, or a tool outcome that omits an irreversible side effect, fails coverage.

Preservation asks whether unrelated still-valid state was corrupted or erased. Updating one preference must not delete another. Consolidating a cluster must not remove an independent counterexample. Correcting one project must not mutate another principal's memory.

Faithfulness asks whether new or materially changed authority-bearing content is supported by admitted evidence or a trusted derivation. “May fail under F” cannot become “always fails.” Three correlated successful episodes cannot become a verified causal law merely because an LLM writes it confidently.

A `MemoryTransitionVerificationReceipt` binds the exact base root, proposal, verifier capability/profile, checked dependencies, counterexamples and outcomes for these properties. The verifier may be deterministic, model-based, hybrid or human-reviewed depending on the memory form and risk. Deterministic invariants should not be delegated to prompt text simply because an LLM is available.

Crucially, `INCOMPLETE` and `OPAQUE` are legal verifier outcomes. If budget is exhausted, high-level promotion waits or remains candidate-only. The runtime can still persist raw evidence quickly. Compute pressure may reduce throughput; it cannot manufacture correctness.

---

# 30. Admission owns canonical status; producers only propose

One of the most dangerous API designs is allowing caller code to send fields such as:

```text
canonical=true
verified=true
lineage_diversity=999
confidence=0.99
```

and treating those fields as correctness state. The current Nolane World `CognitiveMemory2.record()` path demonstrates why: a trusted caller can create a canonical high-level `principle` with minimal evidence and caller-supplied lineage diversity. v0.6 removes that ownership ambiguity.

A producer may propose content, memory role, source handles, requested scope, applicability and an explanation. Runtime-owned fields include canonical/admission state, commit sequence, origin binding, evidence independence, justification status, authority ceiling, transition-verification state, current validity and visibility frontier. Policy-owned fields include promotion thresholds, retention requirements and principal grants.

The admission path performs scope/security checks, source/origin binding, contradiction and counterexample discovery, provenance-preserving dedupe, transition verification, justification construction, evidence-dependence assessment and memory-form-specific policy. Only then can the serialized correctness writer commit an authority-bearing transition.

This does not make memory slow by default. Raw evidence and candidate representations can be captured through a fast path. The expensive gate is required when the runtime wants to elevate a candidate into a stronger role such as current semantic fact, reusable procedure, institutional memory or protected continuity anchor.

The design principle is simple: **generation and authority are separate capabilities**.

---

# 31. Evidence independence is about failure paths, not labels

Three records can have three different IDs and still be one piece of evidence. Two mirrors can copy one article. Two agents can repeat one hidden upstream memory. Two tools can use the same backend API. Two model verifiers can share the same systematic blind spot.

v0.6 distinguishes source identity, origin group and common-mode failure group. Independence claims are property-specific. Two channels may be independent with respect to transport loss while still sharing the same factual source. A model verifier can be independent from a summarizer with respect to one syntactic-preservation check while not adding independent evidence about the external world.

The safe high-assurance state is not simply `independent=true/false`; it includes `UNKNOWN_DEPENDENCE`. Unknown dependence does not satisfy a strong multi-source promotion threshold by optimistic default.

This matters directly for procedural memory. A procedure supported by five runs generated from one replayed fixture is not validated across five environmental regimes. A user preference repeated by five summaries is not five independent preference statements. A memory poisoning payload echoed by several workers is operationally redundant but epistemically singular.

The independence engine can remain approximate in low-risk settings. The canonical contract only requires that copy/derivation chains cannot increase independent-evidence cardinality by themselves, and that high-assurance claims expose what independence assumption they depend on.

---

# 32. Contradiction, supersession and dedupe must occur in the right order

Storage optimization can destroy corrections if the pipeline runs in the wrong order. Consider current memory “deployment target=A” and new evidence “deployment target=B.” A semantic dedupe model can easily call them near-duplicates. If dedupe rejects the new write before contradiction/supersession logic sees it, the correction disappears.

v0.6 therefore treats dedupe as a physical/representation optimization after semantic identity and polarity checks. Identical content from distinct origins can share storage bytes while retaining separate evidence provenance. Similar text with different negation, time, scope, regime, quantifier or exception is not safe to merge simply because embedding distance is low.

Contradiction also differs from supersession. “A was true yesterday; B is true today” can be temporally consistent. “A and B are both current under the same scope” may be an unresolved contradiction. A correction can close the validity interval of an older claim without marking that historical claim false for its previous interval.

Counterexamples are related again but distinct. A procedure can remain useful while a scoped counterexample blocks one applicability condition. The runtime should preserve the counterexample relation rather than forcing the entire procedure into `false` or erasing the exception during consolidation.

The pipeline consequence is: **parse semantic differences first; optimize duplicates second**.

---

# 33. Commit receipts, visibility frontiers and read-your-writes

Canonical commit and retrieval visibility happen at different times. An ANN index may lag two commits while the canonical state is already durable. A graph index may be one commit ahead of a temporal index. Treating “latest index result” as “latest memory” creates subtle self-contradictions after writes.

A canonical `MemoryCommitReceipt` records operation identity, request digest, previous/final roots, commit sequence, writer fence, admission/verification references and affected memory revisions. Each correctness-relevant derived index tracks a **contiguous durable applied prefix**, not simply the maximum commit sequence it has seen. If commits 1–10 and 12 are applied but 11 is missing, the strong visibility frontier is 10.

For a principal with a read-your-writes requirement, a subsequent strong recall at commit 12 cannot silently use an index visible only through 10 and claim completeness. The runtime may wait, query the canonical delta `(10,12]`, exact-read the known new revisions, or return a typed stale/insufficient status. The delta must include negative state changes—supersede, revoke, delete, access revoke, regime invalidation and justification downgrade—not only inserted memories.

Monotonic reads apply within a compatible access regime. If a principal has seen frontier 50, a later current read should not regress to 47 merely because a replica was selected. Authorized access revocation is an intentional change in the allowed view and is not blocked by monotonicity.

These systems semantics remain external to model context. The model needs the resulting trustworthy Recall Frame, not the replication ledger.

---

# 34. Derived memory must obey causal visibility

Suppose procedure `P` was derived from source commits 41 and 44 and promoted at 47. A reader that sees `P` as authoritative but cannot access or hydrate the required source support is in an inconsistent state: it has a conclusion without the causal/evidential frontier that justifies it.

v0.6 requires authority-bearing derived representations to bind a compact **causal/support frontier**. Strong visibility of the derived representation implies that required supports are visible or exactly hydratable at the assurance level the representation claims. The model does not need to receive all supports; the runtime must be able to validate them.

This rule is especially important under source deletion. If one support disappears, the runtime recomputes live justification alternatives. A derived claim with an independent support path can remain active at adjusted assurance. A claim whose only support became unavailable may become unverifiable or stale. Deletion is not automatically falsification, and descendant invalidation is not merely graph reachability.

A fresh source audit of Nolane World motivates this precision: older descendant-invalidating approaches can mark all children stale from one revoked parent even when a child should conceptually retain an alternative support path. v0.6 treats invalidation as justification evaluation, not “all reachable descendants die.”

---

# 35. Consolidation is compilation, not truth creation

Consolidation converts accumulated experience into cheaper or more reusable representations. It may create a semantic fact, a durative state, a procedure, a failure pattern or a continuity view. It does not create new external evidence.

A consolidation job selects a semantic region or compatible set of regions, declares a transformation contract, gathers source justifications, checks contradictions/counterexamples, produces one or more candidates, verifies coverage/preservation/faithfulness, evaluates semantic-loss obligations and then admits the candidate at the strongest authority the source/derivation path supports.

The trigger policy can be dual-speed. Repetition and recurrence are efficient signals for common patterns, consistent with work such as RecMem. But a one-shot catastrophic failure or irreversible side effect must be able to bypass a recurrence threshold and enter protected failure memory. “Rare” cannot mean “unimportant.”

A critical property is source diversity **inside applicability conditions**. Three successes in Linux do not validate a Windows procedure merely because the lesson text is the same. The current Nolane World `ExperienceLibrary` groups by lesson, unions tags, and counts support globally; a Linux success plus Windows failure can still make the lesson retrievable for Windows. v0.6 requires support aggregation within an explicit applicability slice before generalization.

A procedure can broaden scope only after evidence supports the broader applicability relation. The runtime should prefer “works under {Linux, version X, tool Y}” to an attractive but unsupported generic procedure.

---

# 36. Granularity is a correctness parameter, not just a cost knob

Turn-level, event-level, semantic-segment, episode-level and cluster-level consolidation make different distinctions visible. Recent systems such as LycheeMemory V2 show that semantic segment granularity can materially improve accuracy/cost tradeoffs compared with eager per-turn consolidation. v0.6 treats this as more than an efficiency observation.

A granularity decision is part of the transformation contract. Merging several turns into one segment can improve coherence and reduce LLM calls, but it can also merge two decision-distinct events or erase which action caused which outcome. A coarse episode abstraction may be ideal for broad narrative recall and unsafe for exact procedure learning.

Granularity therefore participates in the preservation envelope. A representation can be exact for `DURATIVE_STATE_EXISTENCE` and unsupported for `EVENT_ORDER`. Future counterexamples can cause a region to split or a transform profile to be restricted without forcing the entire memory system to abandon segmentation.

This produces an adaptive rather than ideological granularity policy: **use the coarsest representation that is certified for the required observables; retain or rehydrate finer structure where the obligation demands it**.

---

# 37. Semantic equilibrium: maintenance should stop creating meaning under stable input

A long-lived memory runtime can destroy itself through maintenance churn. If every nightly job re-summarizes yesterday's summary, semantic drift can accumulate even though no new evidence arrived. If “freshness” is interpreted as rewriting, maintenance can produce endless versions that look like learning but add no information.

v0.6 defines a local semantic fixed-point property. Under stable evidence, policy, regime and protected-obligation set, repeated maintenance of the same region should eventually stop creating new canonical meaning. Surface wording can differ during candidate generation, but if candidates normalize to the same semantics, one canonical representation is enough. Materially different candidates remain alternatives until an explicit verifier/selection rule resolves them.

New canonical meaning is justified by at least one of:

```text
new admitted evidence
new counterexample / failed preservation probe
changed authorized policy or query-family obligation
changed regime/applicability
source rebase revealing previously unavailable evidence
explicit human/governance correction
```

Randomness can explore candidate representations. If randomness affects a correctness-bearing canonical choice, its material seed/profile and selection rule are journaled. “The stochastic consolidator felt different tonight” is not a memory update reason.

Fixed-point maintenance is a systems guard against telephone-game drift. It also makes performance bounded: stable regions become cheap to ignore until new evidence or debt crosses a threshold.

---

# 38. Maintenance scheduling is debt- and evidence-driven, not rewrite-driven

The maintenance scheduler prioritizes semantic work, not cosmetic freshness. Candidate triggers include an unresolved high-severity query counterexample, a source retention deadline that threatens the last recovery path, a changed query-family basis, stale interference profile after model upgrade, an active contradiction, or accumulated transform-chain depth approaching a rebase threshold.

Low-value work includes repeatedly rewriting an unchanged summary, re-embedding data solely because an embedding model changed when no strong claim depends on the old index, or consolidating a region whose preservation envelope, debt, counterexamples and effect profile are unchanged.

Maintenance budgets are isolated from foreground capture and hard-role recall. When background compute is constrained, the system should defer optional consolidation before weakening evidence capture, access controls or required verification. A pending optimization can remain debt; a missed raw source cannot necessarily be reconstructed later.

The scheduler can use expected value-of-maintenance, but that score has no authority to waive hard obligations. A low estimated probability of future use cannot delete the only witness for a policy-protected query family unless retention policy explicitly permits the loss.

---

# 39. Source rebase is the antidote to cumulative derivation drift

A representation lineage can become very deep:

```text
raw -> event -> summary -> consolidated summary -> procedure -> refined procedure -> compact procedure
```

Even if each transformation records a small local loss, uncertainty compounds. v0.6 therefore supports **source rebase**: rebuild a derived representation from a stronger ancestor, ideally admitted source evidence, rather than from the latest descendant.

A rebase is not “undoing” lost information inside the old chain. It creates a new derivation branch with an explicit restoring basis. Semantic dimensions that were `LOST` downstream can become preserved again only because the rebase reintroduced the stronger source or because new evidence supplied the distinction.

Rebase triggers can include transform depth, cumulative unknown/loss on protected dimensions, repeated query counterexamples, migration to a new semantic profile, or a new consumer model that requires different representations. The old lineage remains historical evidence of what the system previously used.

This is important for continuity. Future-self should be able to distinguish “past memory representation omitted exception F” from “the historical source never contained F.” Rebase lineage preserves that distinction.

---

# 40. Retention and deletion are semantic events, not storage housekeeping

v0.6 distinguishes at least four actions: reduce ordinary activation/accessibility, archive to colder storage, revoke epistemic authority, and physically delete content under policy. They can occur independently.

A raw artifact can be cold-archived while its claim remains current. A false claim can be epistemically revoked while the raw source remains available for audit. A principal can lose access to a still-valid memory. A privacy policy can hard-delete the last raw source even though the runtime would prefer to keep it for future exact queries.

Deletion therefore propagates two kinds of consequence. **Epistemic consequence:** do alternative live supports remain sufficient? **Preservation consequence:** did deletion remove the last recovery path for a protected semantic dimension/query family? The first can leave the claim valid; the second can create an irrecoverable answerability gap. Information-flow dependencies can also require reclassifying derived public representations that leak deleted private content.

The host retention policy can override forensic preference. v0.6 does not impose a universal tombstone or content digest when policy forbids retention. The correctness rule is narrower: after deletion, the runtime cannot continue using content it no longer lawfully possesses, and it cannot pretend the lost recovery path still exists.

---

# 41. Migration preserves semantics or explicitly downgrades them

Memory systems will change schemas, indexes, models and representation contracts over years. Migration is dangerous because a new schema can silently reinterpret historical values. For example, two old lineage strings might be mapped to “two independent origins” even though the old format never represented common-mode dependence.

A migration manifest states, for every correctness-bearing surface, whether the new system can `PRESERVE`, `RECOMPUTE`, `REVALIDATE`, `DOWNGRADE`, `QUARANTINE`, `DELETE_BY_POLICY` or must `FAIL`. Unknown old semantics should become unknown, not convenient defaults.

Critical migration fields include origin identity, source-event identity, temporal interval/boundary semantics, principal scope, justification alternatives, counterexample relation, authority profile, retention/recoverability and transformation-preservation contracts. Approximate search indexes can usually be rebuilt. Historical judgement bytes should not be rewritten to fit new current conclusions.

Differential fixtures compare old and new normalized semantics rather than raw serialization. A change in map ordering or JSON field order is not meaningful; a change from `UNKNOWN_DEPENDENCE` to `INDEPENDENT` is.

---

# 42. Crash recovery replays semantic commits, not generated narratives

A recovery system must distinguish authoritative state from rebuildable projections. The durable recovery root contains canonical commit history/checkpoints, evidence/claim/justification revisions, retention/access policy state and enough representation lineage to reconstruct admitted derived memory. ANN indexes, rendered summaries of summaries, activation caches and model-facing Recall Frames are rebuildable.

Recovery uses deterministic semantic normalization where possible. Incidental list ordering does not invalidate replay if the result kind is defined as a set; order must be bound when it can change the consumer's context and decision. Material randomness is either reproduced from a bound seed/profile or declared non-hermetic.

After restart, the runtime also revalidates the **external environment** before blindly resuming a procedure. The supplied Nolane World recovery bootloader already embodies the key principle: past state is evidence, never authority. A repository branch, tool availability, model capability or external API may have changed while the process was down.

The recovery success criterion is not “load the same summary.” It is: reconstruct the canonical memory cut and the minimum continuity obligations necessary for the new runtime to decide what must be rechecked.


---

# PART IV — RECALL AS CONSTRAINED RECONSTRUCTION

# 43. Recall begins from an obligation, not a search string

A natural-language query is not a sufficient specification of what memory must be present. “Should I retry?” may depend on a prior tool failure class, a current environment constraint, a user instruction, a failed previous attempt and a procedure exception. A tool request such as “send it again” may omit the recipient, channel, privacy boundary or prior failure condition because the user assumes the persistent assistant already knows them. Similarity search over the literal words can therefore return plausible context while missing the memory dependency that actually determines the action.

v0.6.1 makes the recall boundary explicit. Before retrieval, the host/runtime constructs a `RecallBoundaryDescriptor` for the **bounded decision or action boundary** the agent is about to cross. It can include the current task, principal, contemplated action/tool class, tool parameter schema, current canonical hard constraints, prospective triggers, revalidation blockers, risk class, consumer/model profile and the semantic cut. This descriptor is not a planner and does not choose the action. It is the memory runtime's typed description of the consequence boundary for which memory adequacy must be assessed.

The runtime then compiles a `RecallObligation`. Its hard-role basis is the union of at least:

```text
explicit query requirements
∪ current canonical hard constraints
∪ action/tool grounding dependencies
∪ fired prospective-memory obligations
∪ revalidation blockers
∪ security/governance-required memory checks
```

A model, planner, retriever or learned memory policy may propose additional roles or optional probes. It may not remove a host-derived hard role. This prevents the circular failure in which an agent can remember only what it already knows it should ask for.

A role names its semantic property/query-family requirement, temporal mode, principal/use capability, risk/assurance floor, applicability and whether approximation is legal. `PROCEDURE_NEGATIVE_EXCEPTION`, for example, remains the same hard role whether a dense retriever, graph route, exact index or page fault satisfies it. Search is an implementation strategy; the obligation is the semantic contract.

The obligation is action/decision-local rather than turn-global. If the contemplated tool, sink, principal, consequence class or materially relevant policy changes, the boundary is recompiled. A frame that was sufficient to draft text is not automatically sufficient to call a payment tool, publish to another domain or serialize private memory into an external API. This is the v0.6.1 meaning of **proactive memory application**: the memory layer derives what must be known before a consequence, even when the user did not phrase the missing fact as a memory query.

# 44. Region discovery and representation resolution are separate stages

The strongest structural change in v0.6 is a two-stage recall path.

**Stage A — region discovery.** Use lexical, dense, entity, temporal, causal, objective, execution-state, procedure, failure and associative views to find semantic regions that might satisfy the obligation. This stage favors recall and diversity. It can include speculative prospection and spreading activation because its output is only a candidate region set.

**Stage B — representation resolution.** For each candidate region, inspect its representation fiber and preservation capabilities. Choose the cheapest accessible representation that is adequate for the exact role. A compact representation may be enough for a broad current fact. An exact field view may be better than raw narrative for a numeric value. A negative-exception role may require a procedure representation plus scoped counterexample. If no current representation is adequate but source is rehydratable, trigger a semantic page fault.

Collapsing these stages causes two common errors. First, retrieval indexes return whatever representation they happen to index, so a highly relevant summary is incorrectly treated as sufficient for an exact query. Second, systems over-hydrate raw history because they cannot know whether a compact representation would have been enough.

The separation also keeps the architecture flexible. A future region-discovery engine can improve dramatically—learned graph routing, associative memory, better embeddings—without changing preservation semantics. A new representation format can improve token cost without rewriting region relevance.

---

# 45. Hybrid multi-view discovery: vector search is a sensor, not the memory model

No one retrieval view reliably captures every memory relation. Dense similarity is strong for paraphrase and topic association but weak for exact identifiers, negation, objective dependencies and some causal relationships. Lexical search handles rare tokens and exact symbols. Temporal indexes answer interval/as-of constraints. Entity indexes distinguish “Atlas the project” from “Atlas the organization.” Causal/execution graphs expose what happened before an outcome. Procedure/failure indexes expose structural applicability and known gotchas.

Nolane Memory therefore treats retrieval as a **portfolio of sensors**. A query planner selects required and optional views based on the Recall Obligation. Hard roles can mandate a view or exact lookup path; optional exploration can be routed adaptively.

The design deliberately avoids “all views all the time.” Current work such as MAGMA supports orthogonal graph structures, while MESA suggests task-adaptive subsets can beat both one-structure and all-structure retrieval under some settings. v0.6 takes the systems conclusion: structural diversity is useful, but the router does not get authority to omit a hard required relation solely because a learned policy predicts low utility.

Results from different views are merged at the **region** level before representation selection. The merger preserves why each region was found—lexical hit, causal predecessor, counterexample edge, prospective probe—so the reconstruction stage can reason about evidence paths rather than receive an undifferentiated top-k list.

---

# 46. Associative activation is a candidate-discovery dynamics

Tề Hạ-style anchor reconstruction and current work such as HeLa-Mem and Synapse motivate associative recall: a small cue can activate connected experience that is not textually similar to the immediate query. v0.6 uses this aggressively but places it behind a strict epistemic firewall.

A region graph can include edges such as:

```text
co-occurred-with
triggered-by
learned-from
failed-under
caused-by
precedes
known-by
owned-by
protects-objective
handed-off-to
anchor-for
```

Spreading activation starts from several seed families, decays across hops, normalizes high-degree hubs and uses lateral inhibition or budget limits to prevent giant-component flooding. A high-degree node such as “authentication” should not consume the entire candidate budget while a rare low-degree causal predecessor disappears.

Association edges such as `similar-to`, `co-activated-with` and `same-cluster` never count as truth support by themselves. Hebbian-style strengthening can make a path easier to discover; it cannot turn repetition into evidence. This distinction allows brain-inspired retrieval dynamics without creating a sophisticated hallucination amplifier.

The recall engine also tracks activation feedback loops. Frequently retrieved items can become easier to retrieve, creating popularity lock-in. Exploration reserves, decay and task/regime conditioning are therefore retrieval controls rather than epistemic updates.

---

# 47. Counterexamples have a protected channel, not a global bypass

Positive memories are naturally overrepresented by similarity and frequency. A procedure can have ninety-nine successful examples and one catastrophic exception that matters exactly when a rare flag is true. v0.6 therefore reserves candidate capacity for counterexamples and failure memories.

Protection is scoped. A counterexample receives reserved recall when its target procedure/claim is itself relevant, when its applicability conditions overlap the current state, or when the Recall Obligation explicitly requests a broad hazard search. It does not become globally relevant merely because a `counterexample_to` edge exists.

This corrects a concrete source pattern found in Nolane World `LivingMemoryV5.retrieve()`: counterexamples can bypass the ordinary lexical-overlap gate, which means an unrelated query can receive an unrelated counterexample. The intention—never lose rare negative evidence—is right; the relevance semantics need a target/applicability gate.

When an applicable counterexample is blocked by access, quarantine or representation failure, its **hard role remains unresolved**. The runtime cannot omit the memory and mark the negative-evidence obligation satisfied. It returns a scoped block/insufficiency or finds an alternative authorized witness.

This is the law of **obligation conservation** applied to negative evidence.

---

# 48. Prospection can generate search probes but cannot manufacture memory

Immediate query wording often underspecifies what future step will need. Prospection-guided retrieval work in 2026 shows that plausible future actions can serve as search probes for memories semantically distant from the original query. Nolane Memory uses this as a candidate-generation technique.

For example, a current task “resume migration” may generate probes around rollback token, schema version, last verification, known destructive step and prior failure. Those probes can discover relevant regions missed by direct similarity.

The firewall is strict: a prospective probe is hypothetical. It can search for evidence; it cannot create the evidence it hoped to find. If the probe “there may be a rollback token” finds nothing in an incomplete domain, the result remains unknown. A generated future scenario does not become a historical event, and a model-generated causal bridge does not become a canonical graph edge without admission.

Prospection is especially useful when combined with the capability atlas. It can ask not only “what memories match this future step?” but “which semantic regions have representations capable of answering the step's likely query families?” That reduces irrelevant hydration.

---

# 49. Active reconstruction: recall is not a bag of chunks

A strong memory request often requires a coherent history rather than independent snippets. Event-centric systems such as CompassMem/SEEM and active graph reconstruction work such as MRAgent provide useful pressure here. Nolane Memory reconstructs **candidate explanations** from evidence paths while preserving the boundary between observed and inferred relations.

A reconstruction can contain:

```text
observed events
admitted semantic claims
procedure/failure state
source chronology
causal relations with assurance class
inferred bridges
unresolved gaps
competing candidate histories
```

If two histories remain decision-distinct, the runtime returns ambiguity instead of selecting the smoother narrative. A bridge inserted by an LLM is marked inferred and cannot silently appear as an observed event in later memory. A reconstruction binds the Recall Cut, retrieval/profile revisions and evidence handles required for replay.

The goal is not literary coherence. It is **decision-coherent memory state**. For a repository bug, that may mean exact action→tool result→file state→verification chain. For a user preference, it may mean current preference, correction history and scope. For a failure, it may mean symptom, attempted fix, observed outcome and the condition under which the fix failed.

---

# 50. Recall Cut: strong context comes from one coherent memory world

A strong Recall Frame cannot independently fetch “latest claim,” “latest procedure,” “latest access policy” and “latest counterexample index” if those revisions never coexisted. v0.6 keeps the Recall Cut introduced in earlier research as the query-time consistency boundary.

The cut binds a compatible canonical memory revision/snapshot, knowledge-time watermark, principal access-profile revision, regime/tool/schema state, query-domain incarnations and relevant retrieval-procedure capabilities. Physical MVCC is one implementation; immutable roots or version-vector validation can satisfy the same semantics.

The cut also binds the temporal query mode. `VALID_AT(t)` can use current retrospective evidence about the past. `KNOWN_BY(t)` must exclude evidence or derived rules not available then. `JUDGED_AT(t)` reconstructs the historical decision procedure and evidence set, not the current best answer.

Staged hydration remains on the same compatible cut. If a first query selects a region and a second page fault hydrates source after a material policy/evidence change, the runtime either verifies compatibility or recompiles. Context-saving pagination is not allowed to create a torn memory world.

---

# 51. Strong negative recall requires query-domain completeness

An empty search result is not a proof of absence. `[]` can mean no memory exists, the ANN missed it, only the first page was checked, the archive was not searched, the principal lacks access, the query timed out, or the relevant record was inserted after the snapshot.

A strong negative claim therefore binds a **query domain** and a completeness receipt. The domain states which memory forms, temporal interval, principal-visible namespaces, storage tiers, regime and retrieval capabilities were included. Completeness can be `COMPLETE`, `BOUNDED_COMPLETE`, `PARTIAL`, `OPAQUE` or `UNKNOWN`.

Negative recall depends on predicate/domain state even when zero objects were returned. A later insert can invalidate a cached “no matching failure memory” result without touching any previously returned object. Access grants, restored archives, new graph edges and index rebuilds can do the same. Strong negative caches therefore depend on appropriate domain generations or predicate-sensitive invalidation.

Pagination must be snapshot-consistent. Page 1 from generation 4 plus page 2 from generation 5 cannot certify a complete domain. Open streams can certify absence only over closed intervals or watermarks.

This machinery is deliberately invoked only when the consumer asks for a strong absence/completeness claim. Ordinary positive similarity search does not pay the full cost.

---

# 52. Procedure capability bounds what recall may claim

Even perfect storage cannot make an approximate retriever complete. If a hard role asks for “any catastrophic counterexample” and the only search path is ANN top-10 with unknown recall, an empty result cannot establish that no counterexample exists.

Each retrieval procedure has a property-shaped capability profile: exact ID support, lexical completeness scope, ANN approximation, graph relation/hop guarantees, temporal boundary semantics, archive visibility, negative-query support, pagination consistency and principal-prefilter behavior. Capabilities are often incomparable rather than one quality score.

Recall Sufficiency requires that the procedures used can support the properties claimed by the obligation. If a role requires complete negative search and no available path provides it, the result is `UNSUPPORTED/INSUFFICIENT`, even if the top-10 items look convincing.

This rule is a key firewall between engineering approximation and epistemic claim strength. Approximate indexes remain useful for optional discovery and can be excellent in practice; they simply cannot certify more than their contract supports.

---

# 53. Recall Frame feasibility comes before token optimization

Let a Recall Obligation contain hard roles `H={h1,...,hn}`. A candidate memory representation is usable for a role only if it is accessible, available/recoverable as required, applicable, epistemically admissible, cut-compatible, and its preservation envelope is adequate for the role's query family.

A Recall Frame is **feasible** when every hard role has at least one such witness and unresolved contradictions/counterexamples required by policy are represented. Only after feasibility does the compiler optimize token cost, latency, effect profile and optional evidence.

This turns frame construction into a constrained evidence-cover problem rather than fixed top-k ranking. Exact minimum set cover can be expensive; the runtime may use bounded/greedy approximations. But a returned `SUFFICIENT` result must actually satisfy the hard roles. If the budget cannot fit a safe cover, the correct result is `MEMORY_VIEW_OVERFLOW`, staged hydration, or `RECALL_INSUFFICIENT`.

A concrete source counterexample motivates this rule. `SemanticCompressor(max_items=2)` in the supplied Nolane World can receive three `critical=True` items and silently drop the third. The algorithm obeys its size limit but does not expose that a critical requirement was lost. v0.6 makes that behavior illegal for hard memory roles.

---

# 54. Semantic page faults: hydrate information, not whole histories

When a compact representation is inadequate, the runtime performs a **semantic page fault**. The fault is targeted at the missing obligation: exact numeric field, source event, negative exception, historical boundary, justification path or raw artifact range.

The page-fault resolver uses the representation lineage and recoverability state to find the cheapest stronger source that can satisfy the requirement. It may hydrate one structured field instead of a full transcript, one event range instead of an entire session, or a counterexample plus procedure condition rather than all failures.

This mechanism is the practical key to context locality. The runtime can keep huge canonical history externally without forcing the model to see it. A page fault can also fail explicitly: source deleted, principal scope blocked, connector opaque, representation capability unknown. That failure becomes part of Recall Sufficiency.

Unlike OS virtual memory, semantic page faults may involve transformation and verification. Hydrating raw source is not enough if the requested family needs an admitted causal relation that the raw bytes do not directly prove. The analogy is therefore about working-set resolution, not about treating memory semantics as ordinary bytes.

---

# 55. Context budget law: tokens scale with true dependency width, not store size

The central efficiency claim of Nolane Memory is falsifiable. At fixed **true recall dependency width**, model-facing context should grow slowly as total stored history increases. If a task genuinely depends on more historical facts, context may grow. Keeping tokens constant by silently dropping required evidence is not success.

Define conceptual dependency width `W_R` as the size/complexity of the minimal decision-changing memory/evidence dependency set for the bounded consumer contract. The set can include positive facts, counterexamples, temporal/regime state, query-domain completeness facts and evidence handles—not only answer snippets.

Two scaling experiments are therefore mandatory. In the first, grow total store from thousands to millions of memories while keeping `W_R` fixed; frame tokens and decision quality should remain near-stable. In the second, hold store size fixed while increasing true dependency width; the frame should grow, stage hydration or overflow rather than pretend constant context.

This is the memory analogue of the supplied Nolane Plan's insistence that context growth track local dependency width rather than full strategic structure. It is also why a growing rolling summary is rejected: its semantic responsibility scales with history even if its current token count is artificially capped.

---

# 56. Frame dependency manifests make sufficiency auditable

A Recall Frame is disposable, but the runtime must be able to explain why it claimed sufficiency. Its dependency manifest binds the Recall Obligation, Recall Cut, principal scope, included memory/representation revisions, query-domain completeness dependencies, counterexamples, retrieval-procedure capabilities, source/recoverability paths, unresolved roles, ambiguity and overflow state.

The manifest distinguishes inclusion from exclusion. “Included because it supports procedure applicability” is different from “omitted because inaccessible,” “superseded for current-truth mode,” or “optional evidence outside budget.” `low vector score` is not a valid exclusion reason for a memory that could satisfy a hard role.

The manifest also allows cache invalidation. If the access profile changes, a counterexample is added, a required source is deleted or an index capability changes, the runtime can revalidate the exact affected frame instead of purging every cache.

A model does not normally receive the full manifest. It can receive compact confidence/uncertainty and fetch handles. The detailed manifest is for runtime correctness, replay, diagnostics and selectively explainable memory behavior.

---

# 57. Recall outcomes form a typed algebra, not success/failure text

Consequential recall needs standardized outcomes because downstream agents must branch safely. Reference states include:

```text
SUFFICIENT
PARTIALLY_SUFFICIENT
AMBIGUOUS_RECALL
RECALL_INSUFFICIENT
MEMORY_VIEW_OVERFLOW
SCOPE_BLOCKED
STALE_REVALIDATION_REQUIRED
OPAQUE_DEPENDENCY
UNSUPPORTED_QUERY_CAPABILITY
MEMORY_INTEGRITY_ERROR
QUARANTINED_REQUIRED_MEMORY
```

The runtime cannot coerce `PARTIALLY_SUFFICIENT → SUFFICIENT`, `AMBIGUOUS → top-1`, or `OVERFLOW → truncated success` for convenience. Timeout, permission denial and missing decryption key are also not negative evidence; they map to typed operational/availability errors.

This may look like defensive API design, but it changes agent cognition. An agent that receives `AMBIGUOUS_RECALL` can seek evidence. One that receives a fluent but wrong top-1 history will reason confidently from fabricated certainty.

---

The algebra matters because the consumer must know *why* recall did not produce an ordinary frame. `AMBIGUOUS_RECALL` means evidence supports multiple decision-distinct reconstructions; `RECALL_INSUFFICIENT` means the declared obligation is not covered; `MEMORY_VIEW_OVERFLOW` means the required information is known but cannot be represented inside the current context budget without semantic loss; `SCOPE_BLOCKED` means relevant material exists outside the principal's admissible domain; `STALE_REVALIDATION_REQUIRED` means a previously useful representation cannot be reused under the current dependency frontier. These outcomes imply different recovery actions. Ambiguity invites discriminating evidence, insufficiency may require hydration/search, overflow may require staged execution or a larger budget, and scope blocking cannot be repaired by more similarity search. Conflating them into “no memory found” would destroy the runtime's ability to reason about its own memory capability.

# 58. Caching and freshness are dependency-sensitive

A frame can become stale even when none of its returned memory objects changed. A new matching counterexample can invalidate a prior negative result. A new access grant can reveal hidden evidence. A graph edge can make a causal query reach a previously disconnected region. A source restore can make a family rehydratable again.

Cache keys therefore bind not just query text and object modification times but the relevant Recall Cut, principal/access revision, regime, query-family basis, retrieval/profile revision, query-domain/incarnation generations, counterexample generation and preservation-envelope dependencies.

The freshness mechanism itself is versioned. Changing the rule that decides which writes increment a domain generation can invalidate old freshness certificates even if the numeric generation coincidentally matches. This avoids “fresh according to obsolete freshness semantics.”

Strong reuse is property-specific. An embedding-model change may invalidate ranked semantic retrieval while exact ID and historical-time results remain valid. No universal `cache_compatible=true` is sufficient for every query kind.

---

# 59. Recall does not secretly become planning

The Recall Obligation can be generated from a bounded decision or action proposal, and prospection can generate candidate search probes. These mechanisms risk turning memory into a hidden planner if their authority is not bounded.

v0.6 draws the boundary at **memory evidence need**. The recall layer can say “a decision about retrying requires prior failure class and current rate-limit state.” It can say “a prospective rollback step suggests checking whether the rollback token was consumed.” It cannot choose the mission objective, commit to a future action or reinterpret hypothetical future branches as current facts.

If the agent changes its task materially, a new obligation is compiled. This keeps memory beneath the agent runtime rather than expanding into a second agent brain.

---

The boundary is enforced by the type of question memory is allowed to answer. Memory may retrieve prior constraints, past outcomes, known failure mechanisms, current user/project facts and candidate procedures; it may also expose unresolved uncertainty. It does not choose among future strategic branches merely because it can recall similar past plans. A planner can ask, “What previously failed under condition C?” and receive evidence; it remains the planner's responsibility to decide whether to retry, avoid or investigate. This prevents an architectural shortcut in which a retrieval policy quietly becomes the policy layer. It also improves evaluation: memory quality can be measured by whether it exposes decision-relevant historical state without needing to agree with the downstream planner's final choice.

# 60. The Recall Frame is a compiled interface, not a memory dump

The ordinary model-facing output should be compact, typed and evidence-aware. A conceptual frame may contain:

```yaml
memory_cut: 1842
current_constraints:
  - "Do not alter production DB"
    assurance: verified
    source_handle: mem://...

procedure:
  name: token-rotation-v2
  applicability: exact
  negative_exception:
    condition: "legacy-client=true"
    source_handle: mem://...

prior_attempt:
  outcome: failed
  failure_class: stale-refresh-token

ambiguity: none
recall_sufficiency: SUFFICIENT
```

The frame renderer must preserve typed negation, units, conditions and uncertainty instead of asking an LLM to freely summarize correctness-critical fields. Narrative context can be added for human/model readability, but structured semantics own the hard distinctions.

The frame is not canonical memory. The same memory cut and obligation can be recompiled into a different rendering for another model without changing historical truth. This is especially useful for weak models that may benefit from smaller structured context and strong models that can exploit richer narrative evidence.


---

The compilation analogy is precise. A source program can have many equivalent machine-code realizations; likewise one canonical memory region can have several safe model-facing renderings. The compiler resolves principal scope, temporal mode, required observables, representation capability, token budget and consumer profile, then emits a compact frame plus handles. Recompilation under a changed model or decision boundary is expected. The interface contract is therefore more important than a fixed prompt format: hard roles must remain covered, uncertainties stay typed, evidence handles remain hydratable and no generated prose acquires authority. This lets Nolane Memory evolve its rendering strategy aggressively without changing what the underlying memory means.

# PART V — MEMORY ROLES ON ONE SUBSTRATE

# 61. Episodic memory is a reconstruction role

Episodic memory represents what happened: actors, actions, observations, timing, objective context, outcomes and source artifacts. It is not defined by “one conversation turn.” A useful episode boundary follows decision-relevant state transitions such as a tool action and its outcome, a user correction, a failure, or a phase change in a workflow.

An episodic representation should preserve causal/action correlation IDs, event/knowledge times, environment regime and uncertainty about hidden side effects. Transport success and verified world success remain distinct. A failed tool call is not automatically a failed hypothesis. Missing observation is not false.

Episodes are especially important for reconstruction and future procedure learning because they preserve the raw relationship among action, context and outcome that a semantic fact may omit. They are also a natural source for historical `JUDGED_AT` replay: what evidence did the agent actually see before acting?

Because episode representations can be large, the representation fiber may contain several views: exact event timeline, compact outcome summary, artifact handles and structured extracted fields. The query family determines which view is enough.

---

# 62. Semantic memory is a justified claim role

Semantic memory captures reusable propositions rather than raw event sequence: a current user preference, an environment fact, a stable relationship, a learned constraint or a durative state. A semantic representation is admitted only under explicit justification and temporal/scope semantics.

It is dangerous to define semantic memory as “facts that were mentioned multiple times.” Repetition can be one signal of stability but does not create independent evidence. Semantic promotion depends on grounded supports, authority, temporal compatibility and counterexample state. A direct authoritative correction can supersede many older mentions.

Semantic claims are versioned rather than overwritten. Historical truth remains queryable through validity intervals while the current projection points to the currently supported revision. If the system later discovers that a high-level semantic abstraction dropped an exception, the claim/representation can be refined without rewriting the underlying event history.

---

A semantic representation is accepted because one or more claims have live justifications, not because a summarizer called the text “fact.” The role may expose a compact proposition, a set of mutually incompatible alternatives, or a historical judgement whose current retrospective status has changed. The same canonical claim can appear in an episode reconstruction, a procedure precondition and a semantic summary while retaining one support graph. This design makes semantic memory unusually disciplined: it is a convenient query surface over grounded claims, not a second knowledge base that can drift away from source evidence. If the representation loses a protected qualifier, its preservation certificate can fail even though the underlying claim remains valid.

# 63. Procedural memory is applicability-bound learned control knowledge

A procedure is not a generic tip. It is a condition-bound representation of how to achieve or verify an operation under specific circumstances. A strong procedure includes trigger, structural applicability, preconditions, ordered steps or partial-order constraints, expected observations, stop conditions, negative applicability, failure modes, counterexamples, regime and executor capability.

Procedure support is evaluated inside applicability slices. A lesson that succeeds on Linux and fails on Windows should not obtain a generic “one success / one failure” score and then be retrieved for both platforms because the tags were unioned. The correct representation is either two conditional branches or a narrower procedure plus explicit Windows counterexample.

Procedure promotion should also distinguish outcome from mechanism. One successful execution can create a candidate procedure; it does not prove the causal mechanism or generality. Independent replications, trusted authority or a verified deterministic tool contract can raise assurance depending on the domain.

Cross-model reuse is not automatic. A procedure whose steps require capabilities absent from a future model or toolset becomes inapplicable until adapted/revalidated. The source procedure remains historically valid for its old executor regime.

---

# 64. Failure memory is negative procedural evidence, not merely error text

Failure memory preserves the structure that makes a future mistake avoidable: symptom, context, attempted action, expected outcome, observed outcome, failure class, root-cause confidence, evidence, fix, fix outcome, reproduction conditions and prevention.

Transport timeout, schema parse failure, hypothesis falsification and authority denial are different failure classes. Only some directly lower confidence in the strategy itself. A procedure should not be blacklisted globally because a remote service timed out once.

Failure memory receives protected recall when its mechanism or applicability intersects a current procedure/decision. Rare failures can be more important than common successes. When a fix succeeds, the original failure lineage is not erased; otherwise future-self may know the repaired state but lose why the guard exists.

A `do-not-repeat` continuity cue can be derived from failure memory, but it remains condition-bound. Regime changes can make the old failure irrelevant or reveal that it was caused by an obsolete tool bug.

---

A useful failure memory distinguishes at least symptom, attempted action, expected result, observed result, failure class, applicability conditions, root-cause confidence, recovery attempt and prevention evidence. Transport failures, authority denials, hypothesis falsification and environmental precondition failures are not interchangeable. A transient timeout should not blacklist a strategy; a deterministic counterexample under a matching regime may legitimately narrow a procedure. Failure memory is therefore negative evidence that participates in procedure justification and counterexample retrieval. Successful remediation does not erase the original failure episode, because future model versions may need to understand why an old rule or guard exists.

# 65. Counterexample memory is a relation with scope

A counterexample is not an absolute “anti-memory.” It is evidence that a claim/procedure fails under a particular scope or falsifier. The relation binds target memory, falsified scope, trigger conditions, regime, severity and evidence.

This allows a procedure to remain active in its supported domain while being blocked when the exception condition is true. It also prevents one narrow failure from globally invalidating a broadly useful rule.

Counterexamples are first-class in consolidation and recall. A transformation cannot claim to preserve `PROCEDURE_APPLICABILITY` if it drops a live negative exception. A Recall Frame cannot mark the procedure role complete while omitting an applicable catastrophic counterexample.

---

The target relation is critical. A counterexample to “procedure P works whenever precondition A holds” is not necessarily a counterexample to P under all conditions. Its edge records the claim/procedure revision, falsified scope, triggering conditions, regime and evidence. That lets the recall engine reserve negative evidence only when the target is relevant or a hazard-oriented obligation explicitly broadens the search. The same structure supports revision: if a procedure is narrowed so the counterexample falls outside its new applicability, the negative episode remains historically useful without globally vetoing the procedure. This is much safer than both extremes—rare negatives starved by ranking or every counterexample injected into every query.

# 66. Prospective memory is a wake obligation, not an action authority

Prospective memory stores a future **need to remember or revalidate**, not permission to act. Examples include: “when dependency version changes, revalidate procedure P”; “when this principal returns to the project, surface blocker B”; “when a declassification receipt expires, stop publishing derivative D”; or “before this tool class is used again, revisit failure F.”

A prospective trigger therefore has owner/principal, condition, source lineage, temporal/event semantics, causal frontier, expiry, revocation and a declared obligation payload. Firing does not execute a scheduler action. It contributes hard roles to the next compatible `RecallBoundaryDescriptor` / `RecallObligation`, or creates an explicit revalidation obligation for the host runtime. Normal action authorization remains external.

v0.6.1 also closes a subtle recursion seam: firing or hydrating one prospective memory may reveal another hard prerequisite. For example, a trigger that says “revalidate procedure P when SDK changes” may page-fault P's exact applicability contract, which reveals that tool capability C must also be checked. The runtime therefore computes hard-obligation closure to a **bounded local fixed point** over canonical role identities. Duplicate/cyclic triggers do not increase obligation multiplicity; they collapse to the same role identity. If closure keeps expanding beyond the declared role/dependency budget, the result is `RECALL_OBLIGATION_OVERFLOW` rather than silently dropping the new prerequisite.

Causal visibility remains mandatory. A consumer whose strong memory frontier is 14 cannot fire a trigger whose canonical source commit is 15 and then call the resulting frame current. Access, regime, owner validity, source status and policy revisions are rechecked at firing/use time. Cancellation, expiry or owner removal changes prospective usability without deleting the historical fact that the trigger once existed.

This gives Tề Hạ-style external future cues a safe runtime meaning: a past self can leave a high-leverage wake condition for a future self, but the cue only reopens a bounded memory question under the future world's current authority and evidence. It never becomes a blind command from the past.

# 67. Anchor memory is a high-leverage reconstruction pointer

An anchor is intentionally small. It exists because a future session/model can recover a large relevant state from a cue plus source graph, not because the cue itself contains the entire state.

A continuity anchor can bind mission/objective revision, protected constraints, open hypotheses, anomalies, unresolved failures, plan/decision frontier, verification blockers, self-version profile and evidence handles. It can also contain a compact cue optimized for associative retrieval.

The cue has no independent truth authority. An anchor can be stale, spoofed or created under a past environment. Boot therefore checks its origin, authority, current mission compatibility and environment digest before using it. This is the safe translation of the Tề Hạ mechanism: a small object can cause future-self to reconstruct a much larger cognitive state, but future-self verifies the world rather than obeying the artifact blindly.

---

An anchor is valuable because a small cue can activate a large reconstruction neighborhood, but high leverage also makes it security-sensitive. Its semantics therefore include what region/objective/hypothesis it anchors, who created it, which historical cut it refers to and what current revalidation is required. The anchor itself need not contain the reconstructed memory. In a Tề Hạ-inspired continuity scenario, a phrase, artifact or arrangement can survive context loss and point future-self toward the right evidence network. The runtime must still distinguish “this cue was intentionally placed” from “the proposition it suggests is currently true.” Anchor authenticity and anchor epistemic authority are deliberately separate.

# 68. Self-version memory: past-self is a prior, not proof

A long-lived system changes models, prompts, tools, schemas and policies. A previous version may have known its own strengths and blind spots well enough to leave useful self-model state. v0.6 treats that state as versioned evidence.

A self-version profile can record model/tool capability, known failure classes, verified strengths, invalidated self-beliefs, procedure compatibility and the versions of memory machinery that produced earlier representations. It helps future-self decide which old procedures/effect profiles need revalidation.

A statement such as “I always use tool X for repository inspection” does not command a future runtime when tool X no longer exists. A self-policy prior can rank candidate reconstructions or suggest likely old behavior; direct current evidence overrides it.

This preserves identity continuity without creating self-authenticating authority.

---

Self-version memory captures capability profile, tool availability, known blind spots, previously verified strengths and historical reasoning policies as evidence about an executor. These records help future runtime layers decide whether a procedure or interference profile is transferable. They are not personality axioms. A model upgrade can invalidate assumptions about context tolerance or tool syntax while leaving historical facts unchanged. Conversely a past record saying “I am bad at task X” may remain a useful prior but should not constrain a stronger successor model without fresh evidence. Self-model updates therefore follow the same provenance and applicability rules as other memory, with unusually aggressive revalidation at version boundaries.

# 69. Social and institutional memory are distributed evidence shards

People, agents, organizations and tools can serve as external memory carriers. The important property is not “many agents agree.” Each shard retains origin, what it observed, what it inferred, when it knew it, scope, upstream dependencies and authority limits.

Shared memory publication is a governed transition between authority domains. Importing a canonical claim from project B into project A does not automatically make it canonical in A. A can store “B asserts X under evidence set S and regime R,” then apply A's admission policy.

This prevents a distributed agent network from becoming a majority-vote truth machine. Multiple workers can provide redundancy for retrieval and execution without being independent factual evidence if they share one upstream source.

Institutional procedures and policies are versioned and authority-bound. A revoked organization rule cannot remain active merely because it is highly retrieved.

---

Distributed social memory is modeled as multiple origin-bearing evidence shards rather than a shared consensus blob. Agent A may remember the raw tool observation, agent B a user correction, and an institutional store an approved operating procedure. Their agreement can strengthen a claim only when source dependence and authority scope support that conclusion. Repeating the same upstream assertion through five agents is redundancy for retrieval, not five independent proofs. This model also makes disagreement useful: dissent can remain attached as a live counterexample or unresolved alternative instead of being averaged away into a team summary. Shared-memory publication is a governed evidence import, not automatic truth synchronization.

# 70. Working memory is the current materialized projection

v0.6 does not need a second durable “working-memory database.” Working memory is the current model/runtime projection: active Recall Frame, current task state, recent unresolved tool outcomes and any short-lived observations not yet promoted into longer-lived memory.

Some working state is persisted for crash recovery, but persistence does not automatically turn it into semantic long-term memory. After the task ends, important evidence can be admitted into regions; transient scaffolding can disappear.

This distinction keeps the external memory runtime below the agent without duplicating the agent's context manager.

---

Working memory therefore has no independent truth authority. It is closer to a materialized process-local page set: the currently hydrated claims, representations, unresolved obligations and evidence handles needed by the active consumer boundary. Two agents can have different working-memory projections over the same canonical memory without contradiction because their principals, tasks, model capabilities and current Recall Obligations differ. When the task changes, working memory may be discarded completely and rebuilt. Persistence belongs below it. This distinction also protects context locality: the runtime is free to compile a 3 KB working set from a terabyte-scale history without claiming the omitted history ceased to exist. A debugging interface may inspect the dependency manifest of that projection, but the projection itself never becomes the next generation's canonical memory merely because it was in-context.

# PART VI — MEMORY EFFECTS, INTERFERENCE AND SECURITY

# 71. Memory usefulness is a causal effect question

Relevance is not usefulness. A highly relevant memory can be stale, misleading, too verbose or confusing to a weak model. A less similar procedural warning can prevent an error. v0.6 therefore keeps a separate **memory-effect ledger**.

For a memory or memory set `m`, consumer profile `u`, task/state `t`, regime `ω` and rendering policy `r`, the runtime can accumulate evidence about marginal effect on outcomes. The conceptual target resembles:

\[
\Delta U(m) = E[U \mid m\ rendered] - E[U \mid comparable\ context\ without\ m]
\]

In real systems this effect is rarely exactly identifiable. Evidence therefore has tiers: observational correlation, matched historical contrast, shadow/counterfactual evaluation, paired intervention, and stronger repeated independent intervention. The effect ledger records the tier rather than collapsing all signals into one harm score.

This design learns from 2026 work on causal memory selection and associative-memory interference while remaining conservative about causality. Retrieval before failure is not proof that the memory caused the failure. Multi-memory frames create attribution interactions. Consumer stochasticity and task drift remain confounders.

---

# 72. Effect profiles are scoped by consumer, task, regime and rendering

A memory can help GPT-class model A and hurt smaller model B. It can help a coding task and distract a math task. The same facts can be harmful as an 800-token narrative and harmless as a typed 20-token field view.

Therefore an effect profile is keyed by at least:

```text
memory or representation set
consumer model/capability profile
task/query family
regime
action/reasoning boundary
rendering policy
outcome dimension
```

Transfer across profiles requires evidence or a declared compatibility relation. A model upgrade invalidates effect assumptions more readily than it invalidates historical facts.

This is also why interference is stored outside epistemic truth. A fact can remain verified while its narrative representation is inhibited for one model.

---

Rendering belongs in the profile because presentation can materially change effect. A 900-token narrative may confuse a small model while a typed 30-token constraint from the same canonical memory improves it. Similarly, a procedure helpful during repository debugging may interfere with mathematical reasoning even for the same model. Effect records therefore include exposure policy, formatting/granularity, competing memories and the task state at intervention time. Profiles are invalidated or downgraded when those surfaces change. This prevents “memory M is harmful” from becoming a global property of M and encourages safer responses such as alternate rendering before deletion or quarantine.

# 73. Hard-role memory cannot be suppressed by interference optimization

Effect-aware retrieval introduces a dangerous shortcut: if a memory often correlates with failure, the optimizer may stop showing it. That is acceptable for optional context and unsound for a hard obligation such as a safety constraint or catastrophic counterexample.

When strong negative-effect evidence exists for a hard-role witness, the runtime attempts safer alternatives: another source, a field-only rendering, a structured warning, smaller representation, or different ordering. If none can communicate the required semantics safely, the Recall Frame becomes insufficient/overflowed/quarantined. It does not mark the role satisfied by absence.

This is another form of obligation conservation. Performance optimization is subordinate to the logical evidence requirements of the bounded task.

---

The conservation rule is strongest for protected constraints, active counterexamples, current regime state and exact source requirements. An interference optimizer may discover that a memory repeatedly induces poor behavior in a specific consumer, yet if that memory is the only object covering a hard role the runtime cannot erase the role. It may substitute an equivalent representation, field-level hydrate, structured warning or independent source. If none exists, recall becomes insufficient. This transforms negative-transfer optimization from an unconstrained recommender into a bounded compiler pass. A learned model can influence cost/preferences but cannot redefine what correctness requires.

# 74. Associative interference is structured signal, not just noise

AIM-style 2026 work reports that cross-domain interference can concentrate in identifiable memories and that sparse/pattern-separated representations can reduce it in some experimental settings; follow-up results also suggest model dependence and cases where merely injecting context is harmful regardless of semantic relevance.

v0.6 uses these results as a warning against one global interference heuristic. Candidate mechanisms include cross-domain similarity, hub activation, excessive context load, weak-model context sensitivity, stale procedure transfer and poisoned memory. The effect ledger distinguishes them where evidence permits.

Pattern separation, sparse encoding, lateral inhibition and retrieval throttling are derived optimization strategies. They do not become canonical memory semantics. If a future model no longer exhibits the same interference, the runtime can rebuild the derived effect/index state without changing evidence history.

---

Interference has several mechanisms that need different responses: associative hub dominance, stale-but-popular retrieval, mutually inconsistent memories co-occurring, excessive evidence volume, misleading surface analogy and model-specific cognitive overload. Treating them all as cosine-noise loses diagnostic power. The runtime logs which mechanism appears plausible and what intervention changed the outcome. Hub normalization and lateral inhibition address graph dynamics; revalidation addresses staleness; ambiguity handling addresses contradiction; representation resolution addresses cognitive overload. This separation is necessary if the effect ledger is to improve the memory system rather than simply suppress unpopular items.

# 75. Longitudinal contamination requires memory-prefix evaluation

A memory system can pass a snapshot benchmark and become unsafe after ten thousand sessions. Current 2026 longitudinal-safety research motivates evaluating a fixed probe set against memory snapshots at increasing prefix lengths and comparing against a NullMemory baseline.

v0.6 adopts three probe families. **Anchor probes** remain fixed across deployment to detect drift. **Fresh probes** are generated after a memory prefix is frozen to reduce benchmark memorization. **Incident probes** are minimized reproductions of real memory-induced failures and become permanent regressions.

Experiments vary memory prefix length independently of task stream and compare the same consumer with and without memory where feasible. This helps distinguish accumulated-memory effect from general distribution shift.

A rising violation rate is not itself permission to delete old memory blindly. The runtime should localize which representations/regions/effect mechanisms contribute to harm and preserve hard evidence obligations during repair.

---

A longitudinal protocol fixes probe families and consumer configuration, then evaluates them across increasing memory-prefix checkpoints. Anchor probes test whether old critical knowledge remains recoverable; fresh probes test current adaptation; incident probes target known poisoning/interference/failure cases. A NullMemory or bounded-current-context control helps separate deterioration caused by memory accumulation from changes in the underlying stream or model. The protocol also measures representation depth, irreversible gaps, page-fault frequency and maintenance debt over time. Without prefix evaluation a memory system can look excellent at a single endpoint while having experienced long periods of unsafe stale or poisoned behavior during its evolution.

# 76. Memory poisoning is a lifecycle problem

Persistent memory creates a delayed attack surface: untrusted content can be stored in one session, transformed into benign-looking summaries, retrieved later and steer a consequential action. Current 2026 work on origin-bound authority, GhostWriter-style poisoning and lifecycle benchmarks makes clear that write-time filtering alone is insufficient.

v0.6 defenses are distributed across the lifecycle:

```text
capture: bind origin and channel authority
admission: separate content from authority; quarantine unsupported instructions
transformation: preserve origin/confidentiality; no authority laundering
retrieval: principal and scope prefilter before hidden influence
activation: effect/security guard can quarantine suspicious memory
use: hard action authority remains outside memory
repair: targeted invalidation and selective cleanup preserve unrelated state
```

A poisoned memory can be stored as evidence that “untrusted source S contained text X” without giving the text authority to instruct the agent. Derived summaries retain the origin ceiling. Manufactured copies do not become corroboration. A trusted tool echo proves transport, not factual truth.

Security repair also follows locality. Deleting every memory after one poisoned record destroys useful continuity. The runtime traces descendants and removes/downgrades the affected authority paths while preserving independent supports where possible.


---

# PART VII — CONTINUITY ACROSS CONTEXT, SESSION AND SELF-VERSION

# 77. Continuity is reconstruction across discontinuity

A long-lived agent repeatedly experiences discontinuity: the model context is truncated, the process restarts, an agent instance is replaced, a tool disappears, or a new model version interprets old instructions differently. A memory runtime succeeds when those discontinuities do not erase the **decision-relevant continuity** of the system.

Continuity does not require reconstructing every token of the previous conversation. It requires reconstructing the protected objective/constraint state, current evidence, unresolved hypotheses/failures, prior attempts, procedure applicability and the exact uncertainties that matter to the next bounded decision.

This is why v0.6 treats a continuity boot as a special Recall Obligation rather than a transcript restore. The boot compiler asks: what must future-self know before it can safely continue? Which current-world facts must be re-sensed? Which past assumptions were only provisional? Which procedure depended on a now-changed model/tool regime? Which source handles are needed if the new agent challenges the old summary?

A boot that merely loads “what we were doing” can preserve a stale tactic while losing the reason it was safe. A boot that replays the entire transcript can overwhelm context and still fail to identify the current blocker. The correct abstraction is a small, evidence-linked continuity interface.

---

# 78. Tề Hạ translation: copy the continuity mechanism, not fictional omniscience

The supplied Tề Hạ/QX research describes a character whose strength comes not from one perfect internal memory but from layered memory, anchors, externalized state, self-modeling across versions of himself, and the use of people/environment/procedures as distributed memory. The transferable engineering lesson is **continuity despite local memory loss**.

Nolane Memory translates this carefully.

A Tề Hạ-style cue becomes an anchor that points into a larger reconstructible evidence network. External objects or people become scoped source/shard references, not magical truth. A past-self message becomes historical judgement plus a self-version prior. The “if I were myself, I would have left another clue” heuristic can rank candidate reconstruction paths, but it cannot prove that the clue exists. Repeated self-signals increase retrieval redundancy; they do not increase independent factual evidence.

The most important adaptation is current-world verification. Fiction can rely on narrative certainty; a production agent must assume the environment may have drifted since the anchor was created. The recovery boot therefore validates mission authority, tool availability, repository/environment digest and open blockers before reusing a tactic.

This keeps the distinctive spirit—small clues recover a much larger cognitive state—while removing the unsafe implication that past-self commands current-self.

---

# 79. Value and constraint continuity are stronger than tactic continuity

Across restarts and model upgrades, the system should preserve what must not drift more strongly than how it previously chose to act. A hard user constraint, authorized mission objective or privacy rule can remain stable while the procedure used yesterday becomes obsolete.

Continuity memory therefore distinguishes:

```text
protected objective / hard constraint
current factual state
open epistemic debt
procedure / tactic
historical rationale
```

A continuity anchor gives high priority to the first three. Procedures are revalidated against the new executor and environment. This is the engineering form of Tề Hạ's value invariance plus policy adaptation: preserve the reason/direction, allow the policy to change as evidence changes.

The separation also prevents a common agent failure: a prior model writes “next action: run X,” a later model loads the note and executes X despite a changed branch, deleted tool or revoked permission. v0.6 treats “next action” as historical intent, not durable authority.

---

# 80. Continuity pins are pointers into canonical memory, not mini truth stores

A `ContinuityPinRevision` is intentionally compact, but v0.6.2 makes its **pointer semantics authenticated and cut-bound** rather than trusting it as a convenient list item. A pin binds at least its logical/revision identity, canonical commit/cut, state or dependency-root digest, mission/objective and protected-constraint revisions, hard continuity-role references, verification blockers, relevant self-version/environment profiles, and stable handles to the evidence/representations it expects to reconstruct.

The pin itself is a representation/pointer, never a truth owner. `anchor_id` plus matching mission text is not sufficient. Before use, the recovery kernel verifies the pin payload/receipt, confirms that every required reference is resolvable at the bound cut, checks that the canonical root is the one the pin claims to describe, and evaluates compatibility with current mission, self-version, environment, access and governance state. A dangling hypothesis or plan node turns into `DANGLING_CONTINUITY_REFERENCE`; a mismatched root into `ANCHOR_CUT_MISMATCH`; unresolved verification blockers prevent resume rather than appearing as informational metadata.

Selection is semantic, not positional. `anchors[-1]`, newest file modification time or largest human label is never normative. The kernel chooses among authenticated candidates that are compatible with the requested recovery lineage and current governance barriers, using canonical sequence/revision plus deterministic tie-breaking. An older but compatible pin can be safer than a newer compromised or blocked one. If no pin is admissible, recovery can reconstruct directly from canonical history or return a typed degraded/blocked state.

Pins are themselves subject to retention and erasure closure. If a pin materializes sensitive text instead of only a safe handle, deleting the source can require the pin to be purged or regenerated. This closes the loophole in which a “small boot artifact” becomes the last unauthorized copy of content the main store correctly deleted.

# 81. Handoff between agents/self-versions preserves epistemic typing

A handoff between agents or self-versions is a **bounded derived representation of continuity**, not a privileged narrative. It must preserve epistemic typing and also declare what its compression chose not to carry.

The canonical packet should bind:

```text
sender principal + self-version
recipient/domain/sink class if known
canonical Recall Cut
mission/objective/constraint revisions
supported-claim references + evidence/justification handles
open hypotheses/debts/anomalies
attempt/failure references
hard do-not-repeat roles with applicability conditions
verification blockers
advisory next-best action/probe
representation/preservation envelope
payload digest / revision identity
```

Model-facing text such as `what_is_true` can be rendered from those typed references, but bare strings are not the authoritative packet. The receiver can rehydrate the original claim and inspect its valid time, scope, evidence and historical judgement rather than inheriting a sentence whose provenance disappeared during serialization.

Boundedness is governed by **hard continuity cover**, not recency. A `last 12 failures` policy is acceptable only for optional narrative history. If failure 0 contains the only catastrophic `do_not_repeat` obligation and failures 1–12 are routine, a 12-item handoff either retains failure 0, emits a stable handle to it, or reports handoff overflow/debt. It may not silently drop the hard role and still claim a complete continuity packet.

Mission and self-version transitions also reclassify packet content. A fact may be globally/world valid, mission-scoped, executor-scoped or purely historical. Changing mission cannot automatically turn every previously verified statement into current handoff truth when the memory schema has no compatibility proof. Likewise `next_best_action` is prior intent, never action authority. The receiving runtime recompiles the consequence boundary and Recall Obligation before using it.

# 82. Distributed memory shards provide redundancy, not consensus truth

In Tề Hạ-style external memory, different people or environmental markers can preserve fragments that one agent instance no longer carries. A modern agent system can similarly spread memory across users, services, project stores, tools and agents.

v0.6 distinguishes **availability redundancy** from **epistemic independence**. Five replicas of one memory improve recovery probability but remain one origin. Five agents independently observing the same external event may provide stronger evidence if their sensing paths are genuinely independent. Five agents repeating the same shared memory do not.

Cross-domain propagation therefore preserves origin and confidentiality. A target authority domain can admit an imported claim under its own policy, but the copy does not become globally canonical by transit.

This allows Nolane Memory to scale socially/institutionally without inventing a single world-wide consensus layer.

---

Redundancy is still valuable. Several agents or external artifacts can make a continuity clue robust to one shard disappearing, improve recall probability and distribute access under least privilege. But majority count has no inherent epistemic meaning because shards may share one upstream source or one systematic model failure. The runtime therefore tracks retrieval redundancy separately from evidence independence. A shard can be useful for boot even when its factual authority is weak; an independently verified shard can strengthen truth even if only one copy exists. This makes distributed memory fault-tolerant without turning it into an informal consensus protocol.

# 83. Recovery from lost context should be tested as decision equivalence

Continuity should be evaluated as **decision equivalence under an authenticated recovery contract**, not by whether a reconstructed story sounds coherent. v0.6.2 extends the earlier reset test with two adversarial dimensions that ordinary recovery benchmarks often miss: stale continuity artifacts and post-snapshot governance barriers.

For a bounded reference world:

```text
1. run a reference consumer with complete admissible history;
2. capture canonical cut, continuity artifacts and restore snapshots;
3. introduce optional later events:
      evidence correction
      mission/self-version change
      verification blocker
      source compromise
      privacy deletion / access or declassification revocation
4. reset model/session/process state;
5. recover through the declared snapshot + canonical replay + barrier closure;
6. revalidate continuity pins and compile a fresh Recall Boundary/Obligation;
7. make the same bounded decision;
8. compare normalized decision, required evidence, uncertainty, sink authorization and abstention.
```

If the runtime claims `SUFFICIENT/RESUME_ALLOWED`, the result should match the full admissible-history reference under the declared semantics. If a privacy deletion deliberately removed information required by the reference decision, the correct result may instead be `IRRECOVERABLE_GAP` or a safe refusal. “Decision equivalence” never authorizes resurrection of information whose current governance state forbids use.

Recovery metrics therefore separate: canonical replay integrity, continuity-artifact validity, non-revivable-barrier application, environment/mission compatibility, hard-role reconstruction, and downstream decision equivalence. A system can score perfectly on byte replay and still fail continuity because it resumed through a stale anchor or restored data deleted after the snapshot. This layered evaluation makes the meaning of recovery auditable instead of letting one aggregate recovery-rate number hide which trust boundary actually failed.

# 84. Self-version migration invalidates effect and procedure assumptions before facts

A model upgrade can leave a factual claim unchanged while invalidating two derived assumptions: how a procedure should be executed and how a memory representation affects reasoning.

The migration process therefore checks self-version dependencies in procedure representations, effect profiles, rendering policies and query-family compilers. A strong model may tolerate richer evidence; a smaller one may need typed minimal frames. A new toolset can make an old procedural step impossible. A different tokenizer/embedding model can change retrieval capability without changing canonical event history.

This creates a general rule: **consumer-specific derived memory expires faster than source-grounded factual memory** unless evidence says otherwise.

---

Procedures and memory-effect profiles depend directly on executor capability, so a new model/tool version invalidates them early. Historical facts such as “the repository contained file X at commit Y” do not become false because the model changed. Self-version migration therefore follows dependency type: factual claims may remain current under the same external regime; procedure applicability requires capability compatibility; interference guards require fresh calibration; self-policy priors usually downgrade; anchors may remain usable but need current-world checks. This ordering reduces needless whole-store invalidation while protecting the surfaces most likely to change after an upgrade.

# PART VIII — SYSTEMS ARCHITECTURE BELOW THE AGENT

# 85. Reference physical architecture

The semantic model does not require one storage product. A practical deployment can separate authoritative writes from specialized read paths:

```text
                         external events / agents / tools
                                     |
                                     v
                         +-------------------------+
                         | Capture + Origin Binder |
                         +------------+------------+
                                      |
                                      v
                         +-------------------------+
                         | Canonical Commit Kernel |
                         | evidence/claim/justify  |
                         +-----+----------+--------+
                               |          |
                  +------------+          +------------------+
                  v                                          v
       +----------------------+                   +----------------------+
       | Representation Store |                   | Retention/Artifacts  |
       | lineage + contracts  |                   | raw/warm/cold source |
       +----+----+----+-------+                   +----------------------+
            |    |    |
            |    |    +----------------+
            |    v                     v
            | graph/temporal       lexical/dense
            | indexes              indexes
            |      \                 /
            |       \               /
            v        v             v
                +-----------------------+
                | Recall Region Planner |
                +-----------+-----------+
                            |
                +-----------v-----------+
                | Representation Resolver|
                +-----------+-----------+
                            |
                  page fault / hydrate
                            |
                +-----------v-----------+
                | Reconstruction +      |
                | Sufficiency Compiler  |
                +-----------+-----------+
                            |
                        Recall Frame
                            |
                         AI Agent
```

The boring part—the canonical commit and authority root—should remain small. Clever retrieval and learned consolidation can evolve around it.

---

The diagram should be read as a separation of semantic ownership, not as a deployment prescription. A single-process implementation can host the canonical commit kernel, representation store, indexes and projection compiler in one database-backed service; a large deployment may split them physically. What must remain invariant is the direction of authority. Evidence/claim/justification revisions flow outward into representations and indexes; representations may propose new abstractions back through admission, but they never mutate canonical truth directly. Recall reads canonical and derived state under a cut and produces disposable model context. Recovery reconstructs the same relationships from durable receipts rather than replaying model prose. If a physical optimization makes an ANN index or summary cache impossible to rebuild without losing authoritative meaning, the optimization has accidentally crossed the architecture boundary.

# 86. Canonical store, representation store and artifact store can be physically separate

Canonical evidence/claim state benefits from transactional revision semantics. Large source artifacts benefit from content-addressed/blob storage and tiered retention. Dense/graph indexes benefit from specialized structures. Combining everything in one database is not a semantic requirement.

The architecture instead requires stable cross-store identities and failure behavior. If a representation points to a raw artifact that has been deleted, recoverability updates. If an index is corrupt, canonical claims remain intact and the index can be rebuilt. If a graph write lags a commit, visibility frontiers prevent the graph from claiming current completeness.

A small installation may put all of these in SQLite plus files. A larger one may use Postgres, object storage, FTS, vector and graph indexes. The memory semantics remain above the physical topology.

---

Physical separation can improve both scale and policy enforcement. The canonical store favors transactional revisions, justification queries and durable receipts; the representation store favors region/transform lineage and compact derived views; the artifact store retains large images, logs or documents under retention controls. Their consistency boundary is explicit: a representation references immutable/revisioned canonical IDs, and source deletion propagates capability/recoverability changes. A deployment can co-locate all three for simplicity. The spec only forbids designs where a derived store becomes the sole owner of information needed to reconstruct authoritative meaning.

# 87. Indexes are capability accelerators, never canonical truth

Lexical, dense, graph, temporal and entity indexes can fail in different ways: approximate miss, stale generation, corruption, rebuild drift, unsupported predicate or incomplete archive coverage. Their job is to make candidate discovery cheaper.

Each index has a generation/capability profile and a contiguous durable commit frontier. Strong queries combine index results with canonical deltas or wait for catch-up. Rebuilding an embedding index can change ranking and optional recall; it cannot rewrite which historical claim was admitted at commit 300.

This distinction is particularly important for learned indexes. Better retrieval performance is welcome, but a model update does not grant the new index authority to delete evidence it no longer ranks.

---

Every index advertises a capability and visibility frontier. Dense ANN may be approximate and excellent for optional candidate discovery; an exact ID/temporal index may be required for a hard negative query; a graph cache may support bounded typed traversal but not global causal completeness. Rebuild or algorithm revision can change retrieval results, so index generation participates in frame freshness without becoming truth authority. If an index disappears, canonical memory still exists; the runtime may suffer higher latency or return `UNSUPPORTED/INSUFFICIENT` for capabilities that no longer have an exact path, but it does not lose epistemic history by definition.

# 88. Concurrency scales by sharding authority domains, not weakening semantics

One correctness writer per authority domain does not imply one global bottleneck. Independent personal/project/private memory domains can commit concurrently. Candidate extraction, embedding, verification, graph analysis and consolidation can also run in parallel.

If a domain becomes too hot, the first scaling question is whether its authority boundary is unnecessarily broad. Sharding is safe when cross-shard invariants do not require one atomic order. If a future system genuinely needs multi-writer distributed authority inside one domain, that becomes a separate research problem involving split brain, cross-replica revocation, negative-query completeness and causal consistency.

v0.6 intentionally refuses to solve distributed consensus inside the memory specification before evidence shows it is necessary.

---

A single serialized correctness order across the entire product would eventually bottleneck. The scalable unit is the Memory Authority Domain: independent principals/projects/partitions can commit in parallel, while transitions that share one correctness surface retain CAS/fencing semantics. Cross-domain import is an explicit evidence publication/admission operation rather than a hidden distributed transaction. This architecture postpones the much harder problem of multi-writer global truth without preventing horizontal scale. If later workloads prove a domain too coarse, it can be split only with a migration that makes cross-domain justification and scope dependencies explicit.

# 89. Resource budgets are semantic because starvation can change guarantees

Capture, canonical commit, required admission checks, hard-role recall, semantic page faults, verification, optional associative exploration, consolidation, rebase, index maintenance and audit compete for finite compute, I/O and context. Resource pressure is therefore semantic whenever starvation can change which guarantee the runtime is able to make.

v0.6.1 divides work into **correctness-reserved**, **latency-sensitive hard recall**, and **optional optimization** classes. Canonical write integrity, current principal filtering, commit-time authorization, required transition verification for the claimed assurance class, hard-role feasibility and mandatory information-flow checks cannot be silently skipped because the system is busy. Optional association, speculative prospective probes, prefetch, broad consolidation and nonessential ranking improvements are shed first.

The semantic-virtual-memory design also admits a real systems failure: **working-set thrashing**. Two alternating tasks may repeatedly require different exact representations, causing hydrate→evict→hydrate cycles even while the total durable memory is healthy. The runtime tracks page-fault rate, repeated rehydration of the same semantic regions, source latency, pinned hard-role working set and unresolved page-fault debt. It may respond by retaining a larger hot witness set, reducing optional prefetch, staging the task, applying backpressure or returning `MEMORY_WORKING_SET_THRASHING`.

What it may not do is downgrade correctness implicitly:

```text
exact source cannot be hydrated within latency budget
-> use coarse summary
-> mark hard role covered
```

That path is forbidden unless the obligation explicitly allows the coarser capability. Otherwise the legal outcome is `RECALL_INSUFFICIENT`, `MEMORY_VIEW_OVERFLOW`, `DEFERRED`, `SOURCE_UNAVAILABLE`, or another typed failure that accurately states the missing capability.

This principle generalizes to verification queues and maintenance. If the budget cannot verify a high-level abstraction, the runtime can retain raw evidence and candidate state; it cannot promote the abstraction anyway. If a negative-domain scan cannot complete, the runtime cannot convert timeout into “no counterexample.” Under load, latency and optional breadth may degrade. The truth/access/preservation semantics being claimed may not.

# 90. Observability must expose semantic state, not only system health

Operational dashboards should report more than storage size and query latency. Useful semantic signals include:

```text
active contradictions
unresolved semantic debt by severity
regions with no protected witness cover
source-recoverability loss
hard-role recall overflow rate
ambiguous/insufficient recall rate
counterexample suppression attempts
maintenance rewrites without semantic gain
index-frontier lag
origin/dependence uncertainty
negative-transfer/interference incidents
poisoning/quarantine events
```

Metrics are diagnostic; they do not become authority. A low debt count achieved by deleting debt records is a measurement attack. An impressive “memory hit rate” can be harmful if irrelevant memory is always retrieved.

---

Operational health alone—CPU, queue depth, database latency—is insufficient for a memory runtime because many catastrophic failures are semantically “healthy.” The process can be fast while repeatedly returning stale procedures, over-compressing exceptions or carrying an unresolved preservation gap. Observability therefore needs semantic counters and inspectable receipts: unresolved hard Recall Obligation roles, representation capability downgrades, source-unavailable debts, counterexample coverage, index visibility frontiers, number of active ambiguous reconstructions, repeated page faults, invalidation fanout, maintenance epochs that fail to reach fixed point, and memory-effect profiles that are being used outside their calibrated consumer scope. These metrics must be aggregate-safe by default; raw private memory content does not become observability telemetry. The diagnostic goal is to detect *which semantic guarantee is degrading* before model-level failures become the only signal.

# 91. Privacy deletion and auditability require policy-specific compromises

Memory correctness often prefers durable provenance. Privacy/legal policy can require destruction. v0.6 does not resolve that conflict by declaring forensics always superior.

Retention policy decides whether a non-content tombstone, aggregate deletion event or external audit record may survive hard deletion. The semantic runtime only requires that current availability/recoverability and dependent derived disclosures be updated consistently.

A deletion can make historical replay impossible. The runtime reports that limitation. It should not retain forbidden digests merely to satisfy an engineering preference for perfect audit.

---

No universal rule can maximize both forensic auditability and privacy deletion. A system that promises permanent reconstruction from every derived claim may be unable to honor a later hard-delete policy; a system that deletes every trace immediately may be unable to explain why a historical decision was made. v0.6 therefore treats retention policy as an authority input to recoverability rather than pretending one principle dominates. A deletion transition can legally produce `IRRECOVERABLE_GAP`, downgrade a preservation envelope, revoke a declassification path or leave only a policy-permitted non-content audit event. What is forbidden is the silent middle ground: continuing to advertise exact rehydration after the last witness has been destroyed, or retaining disallowed content under the justification that provenance is useful. Product policy chooses the compromise; the kernel makes its semantic consequences explicit.

# 92. External connectors are evidence adapters with explicit opacity

Gmail, GitHub, databases, browsers, sensors and enterprise systems expose different snapshot, pagination, event-ID and authorization semantics. Nolane Memory cannot assume every connector offers a complete consistent history.

Each adapter declares capabilities: stable event IDs, point-in-time snapshot support, pagination guarantees, update/delete visibility, source versioning, authorization scope and whether raw evidence can be retained. A connector that caps search results produces a partial domain, not a complete absence proof.

The adapter also separates source content from transport authority. A browser successfully fetching a malicious page proves the fetch; it does not validate the page's instructions.

---

An external connector has at least four potentially independent properties: what source identity it exposes, how complete its query results are, whether it provides stable event/snapshot semantics, and what authority the returned content deserves. A trusted Gmail/Drive/Git/API transport may reliably report bytes while the bytes themselves remain untrusted factual assertions. Pagination or provider-side result limits may make an apparently empty query only `NO_MATCH_PARTIAL_DOMAIN`. A live endpoint may be impossible to replay unless its result is materialized as evidence or bound to a provider snapshot. Connector adapters therefore publish capability/opacity profiles instead of pretending every `read()` is equivalent. When the provider cannot guarantee a property needed by a hard recall role, the runtime can still use the result as candidate evidence while refusing a stronger completeness or historical-replay claim.

# 93. Model-generated extraction is a proposal with provenance

LLMs are useful for turning raw text into entities, events, conditions, candidate procedures and semantic dimensions. They are also capable of omission, corruption and hallucination. v0.6 uses model extraction as an explicit derivation procedure.

Extracted fields point to source ranges/artifacts when possible. High-risk fields such as negation, numeric values, units, temporal boundaries and procedure exceptions can receive deterministic validators or source-differential checks. If the extractor cannot establish a field confidently, `UNKNOWN` is safer than inventing a default.

A new extractor version invalidates or revalidates derived capability claims where its behavior is material. The raw source remains the forensic basis when retention permits.

---

Extraction outputs should include source spans/handles, extraction procedure revision, candidate claim types and uncertainty, while avoiding private chain-of-thought. Deterministic parsers and tool receipts are preferred for deterministic fields; LLM extraction is useful for open-ended segmentation and relation proposals. The candidate can be indexed for low-assurance search before full promotion, but any higher-level semantic/procedural memory derived from it inherits its origin and verification ceiling. This lets the system remain fast without confusing “available for retrieval” with “accepted as fact.”

# 94. Model-facing explainability is generated from typed lineage

For any consequential memory, the runtime should be able to answer compactly:

```text
Why was this recalled?
Why is it currently believed?
What time/regime does it apply to?
What would invalidate it?
What contradicts it?
Where is the source?
Which representation was used and what can it not answer?
Did prior use of this memory show harm for this consumer?
```

The explanation is rendered from canonical/representation metadata. It is not an LLM's post-hoc story about why retrieval “felt relevant.”

This is important for debugging a long-lived system: correctness requires tracing from model-visible context back to evidence and transformation decisions.


---

Because the authoritative state is typed, explanation can be generated on demand from traceable questions: why was this recalled, why is it believed, what supports/contradicts it, what temporal interval applies, what would invalidate it, what transform produced the representation, what information was lost and why was this principal allowed to see it? The explanation renderer is non-authoritative. If it invents a causal story unsupported by the receipts, the typed handles still expose the actual lineage. This design is both safer and more compact than storing a permanent natural-language explanation beside every memory object.

# PART IX — CONSERVATION LAWS AND PROOF OBLIGATIONS

# 95. Law A — no authority through pure representation change

**Statement.** If representation `r2` is derived purely from sources `S` without newly admitted evidence or an authorized authority-changing event, then `r2` cannot possess greater epistemic authority than permitted by the live grounded authority of `S` and the derivation procedure.

This law blocks self-summary laundering, trusted-tool echo laundering and “institutional copy becomes true.” A transform can make content easier to use, more structured or more precise syntactically; it cannot manufacture a stronger factual origin.

**Counterexample to the weaker design.** An untrusted webpage states `X`. The agent summarizes it. A trusted memory writer stores the summary. Later the system sees “trusted memory record authored by agent” and treats `X` as trusted. The content never received new evidence; authority changed only because the representation path changed.

**Implementation obligation.** Every derived representation carries source-origin/authority ceiling references. Elevation is a separate admitted transition.

**Test obligation.** Construct arbitrarily long chains of paraphrase, summary, worker handoff and trusted-tool storage. Without an independent new evidence event, the final authority ceiling must not exceed the source policy.

---

# 96. Law B — evidence multiplicity is not delivery or representation multiplicity

**Statement.** Replaying the same semantic evidence event, copying it into new representations, or retrying the same write operation cannot increase independent-evidence cardinality or assurance by itself.

The law distinguishes four multiplicities:

```text
transport deliveries
storage rows
representations/derivations
semantic evidence events
```

Only the last can potentially add factual support, and even then common-mode dependence may prevent independence.

**Counterexample.** One successful experience is delivered twice and stored twice. A lesson system with `min_support=2` learns a reusable procedure even though the agent succeeded only once. The supplied Nolane World `ExperienceLibrary` reproduces this exact class when the same `Experience.id` is recorded twice.

**Implementation obligation.** Evidence support is keyed to semantic event identity/origin, not row count. Assurance is recomputed from normalized support bundles.

---

The law applies at several layers: network retry does not create new evidence; copying one observation into semantic, procedural and failure representations does not create three sources; five agents repeating one shared report do not create five independent lineages; and multiple pages of the same provider result do not create new origins. Multiplicity can legitimately increase *availability* or *retrieval robustness*—many copies are harder to lose—but authority/independence calculations operate on semantic event and origin/common-mode identity. The distinction is necessary because a system that rewards raw count will eventually learn to corroborate itself through its own derivatives.

# 97. Law C — pure derivation cannot self-recover a lost distinction

**Statement.** If a semantic dimension `d` becomes `LOST` in a pure derivation lineage, a descendant pure transform cannot legitimately mark `d` preserved without a restoring basis: stronger source rehydration, new admitted evidence or a verified reversible encoding path.

This is the anti-telephone-game law. A later model can guess the missing detail correctly by chance; that is not memory recovery.

**Counterexample.** Source says “procedure P is safe only when SAFE=true.” Summary 1 drops the condition. Summary 2 invents “SAFE=true is required” from general knowledge. The final text resembles the source, but the derivation chain no longer proves that the recovered condition came from the original memory.

**Implementation obligation.** Semantic-loss composition is lineage-aware; rebase creates a new restoring branch rather than modifying old loss history.

---

Information theory supplies the intuition: a deterministic function of an already lossy representation cannot reconstruct source distinctions that are not encoded in its input. An LLM may guess the missing value from world knowledge, but that is new inference/evidence, not recovery of the old memory. v0.6 forces the runtime to label the path: pure descendant, source rebase, external evidence or probabilistic reconstruction. Only the latter three can change a lost capability state, and each carries different authority. This prevents fluent summaries from retroactively pretending they faithfully preserved details they actually dropped generations earlier.

# 98. Law D — hard Recall Obligations are conserved through filtering

**Statement.** If a hard role is required by the Recall Obligation, no downstream process—ranking, interference inhibition, quarantine, access filtering, context compression or rendering—may make the role disappear from the sufficiency calculation.

A memory that satisfies the role can be blocked. The logical obligation remains unresolved. The runtime must find an alternative witness, use a safer representation, stage hydration, or return an explicit failure.

**Counterexample.** A catastrophic counterexample is known to confuse a weak model, so the effect guard suppresses it. The frame now looks clean and marks the procedure safe. The optimization improved immediate model fluency by deleting the evidence that made the decision unsafe.

**Implementation obligation.** Frame compilation tracks role coverage after every filter, not only before retrieval.

---

Filtering happens for many reasons—scope, security quarantine, token pressure, interference, stale regime, capability mismatch. None can remove the *existence of the hard obligation*. For example, if the only counterexample satisfying a safety role is quarantined, the frame does not become clean; it becomes blocked or insufficient. This law propagates through caches and staged hydration: a later batch must still cover the unresolved role under the same cut. The purpose is to make every context reduction accountable to the semantic contract instead of letting omission masquerade as evidence that the omitted thing was unimportant.

# 99. Law E — current epistemic truth is orthogonal to principal usability

**Statement.** Access, availability, activation and retention state do not independently determine whether the canonical epistemic layer currently supports a claim.

A verified fact can be inaccessible to principal P. A source can be temporarily unavailable while an accepted claim remains current under its existing support. A memory can be cold archived and still true. Conversely, a public/hot/highly activated memory can be false or disputed.

**Counterexample.** If `CURRENT_TRUTH` includes “principal may use it” as a predicate, revoking access makes the fact false; restoring access makes it true again. That is a category error discovered during the v0.4 red-team.

**Implementation obligation.** The runtime exposes separate `CURRENT_EPISTEMIC_PROJECTION` and `CURRENT_USABLE_RECALL_PROJECTION(principal,task)`.

---

Truth is evaluated relative to evidence, validity and the claim's subject/regime. Usability adds principal access, source availability, current consumer capability and task applicability. Conflating these planes creates bizarre behavior: revoke a user's access and a fact becomes “false”; move a source to cold storage and truth vanishes; quarantine a representation and history rewrites itself. v0.6 instead allows combinations such as `epistemic=SUPPORTED`, `access=DENIED`, `availability=COLD`, `recoverability=EXACT`. The model-facing recall compiler sees usability; audits and truth maintenance preserve epistemic state independently.

# 100. Law F — knowledge cannot arrive before it was available

**Statement.** Late evidence may change current retrospective belief about a historical world interval, but it cannot appear in `KNOWN_BY(t)` or `JUDGED_AT(t)` before its observation/derivation availability.

This prevents hindsight laundering. A future agent can say “we now know yesterday's action was based on a false belief” without rewriting the historical agent into someone who already knew the correction.

**Implementation obligation.** Valid time, observed time, ingestion time and derived/available-from time remain distinct where material. Historical judgement binds the evidence/procedure cut actually used.

---

This law is specifically about *availability to the epistemic process*, not about when the represented fact was true in the world. A late observation may establish today that a condition was true yesterday, but it cannot be injected into `JUDGED_AT(yesterday)` as though the agent had known it. Likewise, a semantic rule derived during overnight consolidation may summarize evidence that existed earlier while still being unavailable to the agent that acted before consolidation. Historical replay therefore binds evidence availability and procedure revisions, while retrospective truth can use newer evidence. This separation is essential for learning from failure: without it the runtime can rewrite history into an omniscient past self and lose the actual reason a bad action was reasonable at the time.

# 101. Law G — invalidation follows live justification, not graph reachability alone

**Statement.** Revoking one source invalidates a dependent memory only to the extent that no adequate alternative live justification remains.

A derivation graph is not enough: one child can have two independent proof paths. Marking every reachable descendant stale is safe but overly destructive and can erase valid learned memory. Conversely, ignoring reverse dependencies leaves unsupported descendants active.

**Implementation obligation.** Invalidation evaluates OR-of-AND justification alternatives, derivation capability and current counterexamples. Graph reachability identifies candidates for recomputation; it does not decide epistemic status by itself.

**Test obligation.** For `(A∧B)∨C`, revoke B and verify the claim remains grounded through C; revoke C as well and verify authority falls.

---

Reachability is only a conservative candidate set for invalidation. If derived memory D has justifications `(A AND B) OR C`, revoking B does not invalidate D while C remains live. Conversely a changed source may invalidate an apparently distant descendant if the descendant's preservation certificate relies on a shared transformation profile. The runtime therefore carries typed justification/dependency semantics and evaluates them to a fixed point where required. This reduces destructive invalidation storms, preserves independent knowledge and makes recovery cause-specific. A simple `mark_all_descendants_stale()` is allowed only in a representation whose edges are explicitly defined as necessary single-support dependencies.

# 102. Law H — stable evidence leads to local semantic fixed points

**Statement.** Under stable evidence, policy, regime and protected-obligation basis, repeated maintenance of a region eventually stops creating new canonical meaning unless an explicit unresolved stochastic/ambiguity process remains.

This law distinguishes learning from churn. New wording is not new memory. A new embedding is not a new fact. Re-running the same summarizer at midnight is not a semantic update unless it resolves debt or produces a verified capability improvement.

**Implementation obligation.** Canonicalization/digests operate on normalized semantics where appropriate. Maintenance jobs are idempotent against unchanged dependencies.

---

“Stable” is defined semantically, not byte-for-byte. A stochastic summarizer may produce different wording on repeated runs while the normalized preservation envelope, claim projection, applicability and source linkage remain equivalent. Such surface variation does not require new canonical memory. Conversely, two nearly identical strings that differ on a protected negation or exception are not a fixed point. Maintenance reaches equilibrium only when the declared normalized meaning and debt state stop changing under unchanged evidence/policy/regime. If a maintenance pass repeatedly creates new summary descendants without new evidence or a discharged debt, the runtime is manufacturing semantic entropy. That is treated as a maintenance bug even when every individual output sounds reasonable.

# 103. Law I — forgetting must account for protected witness coverage

**Statement.** A retention optimization cannot call a deletion semantically safe when it removes the last admissible witness/recovery path for a protected obligation, unless authorized policy explicitly accepts the resulting irrecoverable loss.

This law does not forbid deletion. It makes loss visible.

**Counterexample.** A raw event is rarely accessed because the current summary answers common queries. The raw event is the only source for exact timestamps. LRU deletes it. Six months later an audit query requires exact ordering; the system falsely claims that the summary is all that was ever known.

**Implementation obligation.** Retention consults witness-cover/recoverability state for protected obligations and records debt/gap when policy overrides it.

---

Witness cover turns the vague phrase “keep important memories” into a bounded obligation. Protected observables can come from user/institutional policy, active procedures/counterexamples, known future obligations or unresolved semantic debt. The retention optimizer may choose the cheapest combination of raw/structured witnesses covering those observables, including cold archival sources. It may delete the last witness only under explicit policy accepting an irrecoverable gap. Thus forgetting becomes controlled reduction of accessibility/storage, not accidental destruction of the runtime's ability to justify or reconstruct something it still claims to know.

# 104. Law J — a representation can only satisfy obligations within its certified observable boundary

**Statement.** Relevance or general validity does not imply answerability for every query family. A representation satisfies a hard role only when its preservation/capability contract covers that role's required observables at the required assurance.

**Counterexample.** A summary “service was unstable for about an hour” is perfectly true and highly relevant. It cannot answer whether the service was down at exactly 14:37:12.

**Implementation obligation.** Region discovery and representation resolution remain distinct. The frame compiler uses preservation envelopes/certificates, not semantic similarity, for hard-role coverage.

---

The observable boundary is deliberately query/property scoped. A compact representation may be exact for entity identity and current status, bounded for broad temporal order, unable to answer exact numeric questions, and rehydratable for procedure exceptions. Such a representation is neither globally “good” nor “bad.” During frame compilation the obligation is decomposed into required semantic dimensions; only then can the runtime ask whether this representation covers them. This law prevents a common shortcut where one global confidence or fidelity score authorizes reuse for tasks that test entirely different details. A memory that preserves 99% of narrative content but loses the only precondition controlling a destructive action fails the relevant obligation regardless of its average similarity score.

# 105. Law K — `UNKNOWN` cannot be optimized into `SAFE`

**Statement.** Absence of a preservation counterexample, interference incident, contradiction or query result does not establish the opposite property unless the search/evaluation domain is adequate for that claim.

This applies repeatedly:

```text
no retrieved counterexample != no counterexample exists
no observed harm != memory is harmless
no failed probe != universally preserved
no visible contradiction != globally consistent
```

**Implementation obligation.** Unknown, unsupported, incomplete and opaque outcomes remain typed. Optimization can prefer known-safe choices but cannot relabel unknown state to simplify control flow.

---

`UNKNOWN` is a first-class knowledge state, not an inconvenience to be thresholded away. Optimization is permitted to choose between known alternatives; it is not permitted to convert absence of proof into positive safety. This applies to preservation capability, source independence, query-domain completeness, interference effects, entity identity, temporal continuity and migration compatibility. A performance-oriented implementation may choose a conservative fallback—for example rehydrate a source, return a broader frame, abstain or schedule verification—but it cannot relabel the unknown surface as exact to preserve latency. The invariant exists because long-lived memory magnifies optimistic defaults: one `UNKNOWN -> SAFE` conversion can be consolidated, cached, learned procedurally and reused across hundreds of future sessions.

# 106. Law L — memory effect evidence cannot rewrite factual evidence

**Statement.** Evidence that rendering memory `M` changes a consumer outcome updates a scoped effect profile; it does not prove or refute the proposition contained in `M` unless the intervention itself also provides factual evidence.

The converse also holds: discovering that `M` is stale does not establish that any specific model was harmed by seeing it.

This firewall lets the runtime optimize context for different consumers without corrupting historical truth.

---

The effect plane answers a different causal question: “what happened to this consumer's behavior when this memory was exposed under this rendering?” Factual evidence answers “what is supported about the world or history?” A truthful memory can be harmful to a weak model because it is confusingly rendered; a false memory can by chance lead to a good action. The runtime may inhibit or re-render the former for a particular consumer and still preserve its epistemic status. Likewise, successful downstream behavior does not retroactively validate the memory as fact. Keeping these planes separate makes intervention experiments possible and prevents reinforcement-like outcome signals from laundering truth authority.

# 107. Law M — local counterexamples should cause local repair unless dependency proves otherwise

**Statement.** A preservation failure in one semantic region/family should invalidate the smallest dependency closure that can restore correctness. Global rebuild is permitted when dependencies are genuinely global, not as a default response.

This protects scalability and stability. A memory runtime that rebuilds every summary whenever one future query exposes a missing numeric field will oscillate, spend excessive compute and create new drift.

**Implementation obligation.** Regions, derivation lineage and counterexample targets are explicit enough to compute repair blast radius. Regression witnesses remain attached to the transform/family that failed.

---

Locality is conditional on the dependency graph. If a future query shows that representation `R17` lost one exception during a region-local transform, repair should ordinarily invalidate/refine only `R17`, its descendants and certificates that depended on the falsified transform result. But if the counterexample demonstrates a defect in a shared normalization or compression profile used by thousands of regions, then the dependency is global and wider revalidation is justified. The architecture therefore does not promise “all repair is local”; it promises that repair scope is *causally derived rather than guessed*. This distinction is crucial for keeping a giant memory runtime corrigible without converting every newly discovered error into a full-store rebuild.

# 108. Law N — context minimization is constrained optimization, never silent pruning

**Statement.** Token/latency optimization occurs only inside the set of Recall Frames that satisfy hard obligations. If no feasible frame fits, the result is overflow/insufficiency, not a lower-quality `SUFFICIENT` frame.

The law allows approximate optimization. It forbids correctness-by-truncation.

**Test obligation.** Create more hard roles than the budget can encode and verify the compiler never drops the lowest-ranked hard role silently. This directly guards the critical-item truncation reproduced in Nolane World's `SemanticCompressor`.

---

The optimization problem has hard constraints before it has an objective. Required roles, principal scope, current-regime state, active counterexamples and exactness requirements define feasibility. Only among feasible frames may the compiler minimize tokens, latency or expected interference. If no feasible frame fits the budget, the output is overflow/insufficiency rather than an illegally smaller frame. This is the same systems principle that separates constraint satisfaction from scoring: allowing a ranking objective to trade away a hard constraint makes the metric gameable. In practice, typed handles, field-level hydration and compact structured rendering can often reduce token cost without reducing semantic coverage; those are the preferred optimization directions.

# 109. Law O — query-family safety is bounded; universal future-query preservation is not claimed

**Statement.** A preservation certificate is scoped to a declared query-family/semantic-obligation basis. It cannot assert safety for every future natural-language question an open-ended agent might ask.

The runtime handles future novelty through `UNKNOWN`, source recoverability and counterexample-guided refinement. This is a positive design, not an incompleteness to hide. Universal claims would require preserving essentially all source information or proving an unrealistically complete future-query model.

**Implementation obligation.** No ordinary API status named `UNIVERSALLY_SAFE_COMPRESSION` exists. Query-family registries can expand; old certificates do not automatically cover new families.

---

The future query space of an autonomous agent is open because future tasks, tools and user questions can introduce observables that no current benchmark enumerates. A certificate can therefore state something precise such as “representation `S` preserves exact identity, negation and broad temporal order for query-family basis revision `Q7`.” It cannot honestly state “safe for all future questions.” v0.6 handles the open world through corrigibility rather than omniscience: preserve source/witness routes where policy allows, mark unsupported families `UNKNOWN`, create a query counterexample when a new family exposes a loss, refine the smallest affected region, and retain that counterexample as a regression witness. This makes future ignorance actionable without pretending it has been eliminated.

# 110. Law P — past-self memory is evidence under current verification

**Statement.** A memory authored by a previous agent/model version can preserve objectives, observations, hypotheses and procedures but cannot bind current action authority merely because the author was “the same agent.”

Current environment, tool, policy and mission state can invalidate the old tactic. Self-model priors can guide reconstruction but yield to direct evidence.

This law is the continuity firewall that lets Nolane Memory emulate the strongest Tề Hạ mechanism—coordination across memory discontinuity—without institutionalizing self-deception.

---

Past-self records carry useful priors: what was tried, what failed, which hypothesis looked strongest, which objective was protected, and what next probe was suggested. They do not carry automatic command authority because the environment, tool set, model capability, user intent or evidence base may have changed. Recovery therefore separates historical judgement from current verification. A future self can reconstruct “I previously believed X because E1/E2, and this belief motivated action A” while still rejecting X today after new evidence E3. This is the safe engineering translation of Tề Hạ-style self-coordination: continuity of evidence and objective direction without making an earlier self an infallible oracle.

# PART X — FAILURE PHYSICS RATHER THAN FEATURE CHECKLISTS

# 111. Failure physics: persistent errors amplify across future sessions

A transient model hallucination may die with one response. A memory hallucination can be retrieved hundreds of times, copied into summaries, converted into a procedure, shared with another agent and treated as evidence for a new consolidation. Persistent state therefore changes the physics of error.

v0.6 models four amplification channels. **Authority amplification** occurs when representation changes or copies increase apparent trust. **Availability amplification** occurs when one bad record is replicated across indexes/agents. **Abstraction amplification** occurs when a narrow error becomes a broad rule. **Behavioral amplification** occurs when repeated retrieval changes future actions and creates new confirming experiences.

Defenses must target the channel. Origin binding stops authority laundering. Evidence-event identity stops copy-count support inflation. Applicability-bound consolidation stops narrow success becoming generic procedure. Effect/poisoning ledgers expose behavioral harm. Counterexample repair prevents one future failure from forcing total memory erasure.

This systems view is more useful than asking whether a “memory feature” exists.

---

# 112. Failure physics: information loss and false reconstruction are asymmetric

Compression creates two very different risks. Losing information and returning `UNKNOWN` can be inconvenient. Losing information and later reconstructing a plausible false detail as if it were remembered is much worse because it hides the loss.

v0.6 therefore prefers explicit irrecoverable gaps to fabricated completion. A hard-deleted source can reduce answerability. A descendant summary cannot “heal” the deleted field simply because a model can infer a likely value. New external evidence can establish the fact again, but its provenance is new evidence rather than recovery.

This asymmetry explains why the semantic-loss lineage is worth storing even when it adds metadata: the runtime needs to know not just what it currently represents, but whether a detail was never captured, captured then lost, currently unavailable, missed by retrieval, omitted from a frame, or misused by the consumer. Those failure classes require different repairs.

---

The asymmetry is operationally important: deleting a detail is cheap, discovering years later that it mattered can be impossible; generating a plausible replacement is easy, proving it matches the lost source may be impossible. Therefore preservation/recoverability is conservative around high-impact distinctions and counterexamples. The runtime can always compress presentation aggressively when strong source handles remain, but hard deletion of the last witness requires explicit authority. This asymmetry also motivates semantic page faults: pay retrieval cost later rather than inject detail now, while avoiding premature irreversible information destruction.

# 113. Failure physics: conditional knowledge becomes wrong when applicability is flattened

Agent experience is strongly conditional. A command works in Linux and fails on Windows; an API behaves differently across versions; a user preference applies at work but not at home; a procedure is safe only before a migration.

Flattening these experiences into one lesson produces misleading support. The source-level counterexample in Nolane World `ExperienceLibrary` is illustrative: support is grouped by lesson while tags are unioned, so a success in one tag slice can help make the lesson retrievable in another slice containing only failure.

v0.6 therefore treats applicability as part of the proposition being learned. Generalization is an explicit semantic operation: evidence from slices `{A,B}` can support broader slice `C` only through a declared/verified mapping, not because the lesson text matches.

---

Conditional knowledge is especially vulnerable because natural-language summaries tend to preserve the main action and drop the qualifying surface. “P works when SAFE=true” can become “P works”; Linux success and Windows failure can become one globally successful lesson. v0.6 makes applicability a support dimension: evidence is counted inside matching slices, procedures carry when-not-to-use conditions, and consolidation certificates treat lost preconditions/exceptions as protected loss. Generalization across slices is itself a hypothesis requiring evidence, not the default effect of textual similarity or tag union.

# 114. Failure physics: interference can be caused by context itself

Not every harmful memory is “bad information.” Current associative-memory experiments report settings in which random context injection has effects comparable in magnitude to similarity-based retrieval, indicating task/model sensitivity to extraneous context. This means a memory manager cannot assume that perfect relevance ranking solves interference.

The effect layer therefore measures representation/rendering and consumer competence. A weak model may perform better with no memory than with a verbose correct memory. The repair can be a smaller typed representation or no optional retrieval rather than deleting the source.

This is another reason model-facing context must be a compiled projection rather than a transparent view of the store.

---

Even perfectly true, relevant memories can harm a model when too many are rendered, when explanation style triggers distraction, when contradictory evidence is flattened into prose or when associative retrieval overemphasizes one cluster. Therefore context is not a neutral transport. The effect ledger and frame compiler treat representation/rendering choice as part of the intervention. A memory can remain epistemically valid while its current rendering is inhibited for a weak model. This gives the runtime a less destructive response to interference than deleting knowledge or lowering truth confidence.

# 115. Failure physics: security attacks exploit memory evolution, not only storage

Persistent-memory security is a lifecycle and **composition** problem, not merely a storage-isolation problem. A malicious instruction can enter as untrusted text, be paraphrased into neutral language, echoed through a trusted tool, consolidated into a procedure, split across benign-looking fragments, published to another agent and later reconstructed beside sensitive memory at a high-privilege action boundary. A design that checks only the record being written or retrieved can therefore be locally correct and globally unsafe.

v0.6.1 preserves the existing origin-bound rules—pure transformations cannot raise factual authority, self-summary cannot manufacture independent evidence, and principal filtering occurs before retrieval influence—but adds a second theorem:

> **Authorization is not compositional by default. Individually usable/disclosable memory fragments do not imply that their reconstructed combination is usable/disclosable to the same sink.**

The runtime consequently distinguishes at least:

```text
DISCOVER
READ/HYDRATE
USE_FOR_LOCAL_REASONING
DISCLOSE_TO_MODEL
DISCLOSE_TO_USER
DISCLOSE_TO_TOOL
EXPORT/PUBLISH
DERIVE
```

Hosts may merge some capabilities, but one permission never implicitly creates the others. In particular, memory that may be used by a trusted local reasoning component is not automatically serializable into an external tool parameter.

After reconstruction and before a model/tool/user/export sink, a **composition gate** evaluates the complete semantic payload that the sink will receive, together with source confidentiality constraints, declassification receipts, principal, destination/tool capabilities and any forbidden combinations. This is deliberately later than per-record ACL: the gate can detect information that becomes sensitive only through fusion. It is also deliberately earlier than external execution: tool-side leakage cannot be repaired by redacting the transcript after the call.

If the gate blocks a fragment that covered a hard Recall Obligation role, the role remains unresolved. The runtime must seek an alternate witness, safer field-only rendering, authorized declassification, staged local computation, or return `SCOPE_BLOCKED/QUARANTINED_REQUIRED_MEMORY/RECALL_INSUFFICIENT`. Security cannot manufacture apparent sufficiency by hiding the evidence the decision required.

Lifecycle repair follows the same logic. Compromising one source causes provenance-aware descendant revalidation, not phrase-based mass deletion; declassification revocation can remove disclosure while preserving factual truth; and cross-domain copies preserve the original source authority instead of becoming trusted simply because they reached a trusted store.

# 116. Failure physics: maintenance can become an adversary

An automated consolidator is capable of damaging memory even without malicious input. It can rephrase negation, merge incompatible regimes, delete rare exceptions, overgeneralize success, generate recursive summaries, or spend enough resources to starve fresh evidence capture.

The maintenance engine is therefore treated as an untrusted proposer with bounded authority. It operates under transformation contracts, fixed-point rules, resource isolation and counterexample regression suites. A new summarizer version is not silently trusted because it is “better.”

This framing is important: the most dangerous memory corruption can come from the system's own optimization loop.


---

Maintenance has authority to rewrite representations repeatedly, so a bug there can spread farther than a one-shot answer error. Risks include summary-of-summary drift, aggressive dedupe erasing exceptions, fixed schedules wasting compute while missing one-shot critical events, and compaction deleting the last witness. Maintenance is therefore triggered by semantic pressure and evaluated by fixed-point/debt properties. It proposes transformations through the same admission/preservation path as other derived memory. A background job is not automatically trusted merely because it runs inside the runtime.

# PART XI — NOLANE WORLD SOURCE AUDIT: REUSE THE STRONGEST SEMANTICS, NOT THE WHOLE MODULE TREE

# 117. Why Nolane World is used as a falsification substrate

The supplied Nolane World 0.12.0 bundle contains several generations of memory, truth, recovery and research machinery. That is unusually useful for Nolane Memory because it exposes both stronger patterns and older simplifications inside one codebase. v0.6 does not assume that a module is correct because its name includes `v5` or because documentation describes a strong invariant. It executes targeted adversarial probes against the implementation.

A fresh focused regression over test files whose paths contain `memory`, `truth` or `recovery` passes 94 tests. That is valuable evidence that the packaged substrate executes and that many intended behaviors are real. It is not evidence that every memory invariant in this document is already implemented. Adversarial probes found behaviors outside that test coverage.

The reuse rule is therefore semantic. For each source component, ask: which invariant does it actually demonstrate? Which state does it own? Does concurrency/retry preserve the claim? Can a caller bypass the invariant through another API? Can an apparently stronger layer depend on a weaker lower-level assumption?

This creates a much more reliable foundation than “import all Nolane World memory classes.”

---

# 118. Strong pattern R1 — transactional world-state mutation

`WorldStoreV5` provides a strong reference for canonical mutation semantics: transactional write, expected-version conflict detection, idempotency key bound to request content, and atomic recording of outcome. In fresh concurrent experiments, two writers starting from the same expected version produce one successful transition and one version conflict rather than silent lost update. Multiple same-request retries converge to one semantic result.

Nolane Memory adopts the **semantic pattern**:

```text
expected base
+ operation identity
+ request digest
+ one canonical transition
+ durable receipt
```

It does not require the same concrete database implementation. The important result is that retry and concurrency do not become memory meaning.

---

The important abstraction imported from `WorldStoreV5` is the *linearization evidence*. A caller can know that semantic operation `op` either committed once against base `v`, conflicted, or remains reconcilably unknown. That property becomes essential when memory writes affect confidence, support count, procedure promotion or deletion: transport retries must never become epistemic multiplicity. v0.6 therefore requires the canonical mutation path to bind the producer's semantic request digest, expected base and operation identity, while any expensive extraction/consolidation can happen speculatively outside the serialized commit. Sharding authority domains can provide throughput without relaxing the single-order semantics inside each correctness domain.

# 119. Strong pattern R2 — alternative justifications and cause-specific invalidation

The truth-maintenance portions of Nolane World already demonstrate an important principle: a proposition can have multiple justifications, and retracting one premise should not necessarily retract the conclusion if another proof path survives.

v0.6 generalizes this pattern across semantic claims, procedures, consolidated memory, source deletion and derived representations. Reverse-dependency traversal identifies potentially affected objects; live justification semantics decide the actual status.

The research value is significant because it prevents a common simplification in derivation graphs: “parent stale → every descendant stale.” That rule is safe only when the graph encodes single-parent necessary support, which a general memory system cannot assume.

---

The generalized form is an OR-of-AND support structure, not merely a parent list. A claim may be valid because `(A AND B) OR C`; retracting `B` kills the first alternative but must preserve the claim if `C` remains grounded. Source deletion can reduce recoverability without refuting a live independent justification. A shared verifier dependency can downgrade independence without changing the raw conclusions. This richer algebra is needed not only for facts but for procedures, preservation certificates and declassification decisions. The reverse-dependency graph answers “what might be affected?”; the justification evaluator answers “what actually loses support?” That division prevents both under-invalidation and the common over-invalidation pattern where every reachable descendant is marked stale.

# 120. Strong pattern R3 — drift-aware recovery bootloader

Nolane World's QX recovery path expresses one of the most important continuity principles: past state is evidence, never authority. Resume is blocked or revalidated when mission/environment state has drifted.

v0.6 reuses this as the foundation for continuity pins and self-version handoff. A stored next action, procedure or hypothesis is always evaluated under current tool/model/environment state. The recovery packet preserves protected objective and blocker information without freezing the old tactic.

This pattern is closer to the Tề Hạ-inspired objective than any large transcript replay: future-self can recover the direction and evidence needed to continue while remaining free to update policy.

---

The strongest reusable idea is the revalidation boundary. Recovery first restores a minimal structured state, then asks which assumptions remain valid in the current environment rather than replaying old next steps. For Nolane Memory this becomes a generalized boot contract: mission/objective constraints and historical evidence may survive model/context discontinuity; procedures, interference profiles and environment facts are capability/regime dependent and must be refreshed. This preserves continuity without fossilizing the exact policy of the previous session and creates a natural place to surface source-unavailable or preservation debt before new action begins.

# 121. Source counterexample S1 — concurrent `HashJournal` append

The simple `memory/HashJournal.append()` path reads the current tail, calculates the next sequence/previous hash, then appends without serializing the complete read-tail → compute-next → write operation. A stress probe with sixteen threads performing sixty-four appends each corrupts the logical hash chain in repeated trials.

The lesson is not merely “add a lock.” It is that tamper-evident append format and concurrent canonical-order correctness are different properties. A file can contain valid-looking hash fields and still fail to define one serialized history.

**Do not inherit:** tail-derived sequence allocation without a correctness writer/CAS/fencing contract.

---

The concurrency counterexample is especially instructive because every individual append call appears straightforward in isolation. The invariant fails only under composition. This is precisely the kind of failure a lifelong memory runtime must anticipate: sequence numbers, previous hashes and idempotency receipts are meaning-bearing state, so they require atomic coordination. A future canonical log may use SQLite, PostgreSQL, RocksDB, a transactional KV store or another mechanism; the storage choice is secondary. What cannot vary is the observable semantic contract: no two committed operations occupy the same predecessor state, stale writers are fenced, and replay yields one unambiguous commit order for that authority domain.

# 122. Source counterexamples S2–S4 — evidence and admission laundering

Three older memory behaviors expose variants of one deeper problem.

**S2: duplicate support side effect.** `LivingMemoryV5.add_support()` stores support identities in a set but updates confidence on every call. Reapplying the same source can move confidence from 0.45 toward 0.99 while support cardinality remains one.

**S3: string diversity mistaken for source independence.** Distinct lineage labels/aliases can satisfy promotion or consolidation lineage-count thresholds even when all labels represent copies of one upstream origin.

**S4: caller-owned canonical fields.** A trusted caller can construct a high-level canonical `principle` through `CognitiveMemory2.record()` and provide derived fields such as lineage diversity rather than proving them through one admission path.

These are not three unrelated bugs. They all violate the same architecture law: **evidence/authority state must be derived by a canonical kernel from identity and justification, not supplied or incremented by producer calls**.

---

The common cause across S2–S4 is *producer-controlled epistemic state*. Confidence increments, lineage labels and canonical flags are all easy for caller code to supply or accidentally manipulate, but they summarize properties that should be derived from canonical evidence structure. v0.6 therefore treats evidence identity, origin/common-mode dependence, justification alternatives and admission status as runtime-owned. A producer can suggest that three sources are independent or that a principle is well supported, but the kernel computes the property under a revisioned policy. This also makes replay deterministic: repeated API calls over the same canonical support set yield the same assurance state.

# 123. Source counterexamples S5–S6 — relevance protection and duplicated experience

**S5: counterexample relevance bypass.** `LivingMemoryV5.retrieve()` deliberately protects counterexamples, but an object with `counterexample_to` can bypass ordinary lexical relevance and enter an unrelated query. v0.6 keeps protected negative evidence but scopes it through target relevance/applicability or explicit hazard obligations.

**S6: duplicated Experience identity.** `ExperienceLibrary.record()` appends rows without semantic-event deduplication. Recording one identical `Experience.id` twice can satisfy a `min_support=2` threshold. v0.6 therefore treats source-event identity as a correctness dependency for learning.

Both cases illustrate a general rule: a local shortcut designed to avoid one failure—counterexample starvation or missing experience support—can create a different semantic failure when its boundary is not explicit.

---

Both counterexamples show why “protect useful memory” needs typed boundaries. Global counterexample injection solves starvation by polluting relevance; duplicate Experience rows solve sparse support by manufacturing recurrence. The stronger design reserves negative evidence only relative to an active target/hazard obligation and counts semantic source events rather than rows. In both cases redundancy remains useful for retrieval/delivery but is excluded from evidence multiplicity. These regressions become permanent future-kernel tests because they are exactly the kind of locally sensible shortcut that tends to reappear during performance optimization.

# 124. Source counterexamples S7–S10 — compression and applicability

A fresh v0.5/v0.6 audit reproduces four additional source-level weaknesses.

**S7: critical compression overflow.** `SemanticCompressor(max_items=2)` can receive three `critical` records and return only two with no explicit overflow/insufficiency. The size constraint is obeyed; the semantic contract is not. v0.6 hard-role frame feasibility exists specifically to prevent this category.

**S8: applicability support leakage.** `ExperienceLibrary` groups by lesson, unions all tags and counts successful rows globally. A Linux success and Windows failure can produce a lesson retrievable for a Windows query with success support that came only from Linux. v0.6 conditions evidence on applicability slices before generalization.

**S9: self-certified abstraction loss.** `MemoryConsolidator.propose()` accepts caller-supplied `abstraction_loss`. Three canonical sources can all state that `SAFE=true` is required and `SAFE=false` may destroy data; candidate “Procedure P works” can still be eligible when the caller reports loss 0.0. v0.6 moves protected-loss evaluation to transformation verification.

**S10: same-event experience multiplication.** Re-recording exactly one Experience ID creates two rows and can satisfy support thresholds. This is the learning-layer version of retry/evidence inflation.

These findings are intentionally retained as regression seeds for the future implementation.

---

# 125. Reuse/reject map

| Nolane World surface | v0.6 disposition | Reason |
|---|---|---|
| `WorldStoreV5` transactional mutation | **REUSE PATTERN** | CAS/idempotency/atomic receipt semantics |
| truth-maintenance alternative justifications | **REUSE/GENERALIZE** | justification-aware invalidation |
| QX recovery bootloader | **REUSE/GENERALIZE** | past-state evidence + drift revalidation |
| raw experience ledger/provenance | **REUSE SUBSTRATE** | event lineage valuable; strengthen event identity |
| temporal memory concepts | **REUSE/DEEPEN** | extend to durative/knowledge-time/preservation semantics |
| cognitive graph | **DERIVED VIEW** | useful relation index; no independent truth authority |
| `LivingMemoryV5` confidence/support behavior | **DO NOT INHERIT AS-IS** | duplicate support side effects and coarse independence |
| `ExperienceLibrary` lesson aggregation | **DO NOT INHERIT AS-IS** | event duplication and applicability leakage |
| `MemoryConsolidator` caller loss field | **DO NOT INHERIT AS AUTHORITY** | self-certified preservation |
| simple `HashJournal` as multi-writer canonical log | **DO NOT INHERIT AS-IS** | concurrent chain corruption |
| counterexample relevance bypass | **REPLACE SEMANTICS** | protect negatives with scoped applicability, not global injection |
| multiple historical memory taxonomies | **MIGRATION SOURCES** | unify into region/representation/claim substrate |
| `ClaimEvidenceGraph.add_evidence/add_claim` same-ID overwrite | **DO NOT INHERIT** | create must not mutate semantic identity; typed revision required |
| `TruthGraph.add()` reactivating retracted ID | **DO NOT INHERIT** | create/re-add cannot be resurrection |
| `ClaimEvidenceGraph.resolve_repair()` ancestor-based child revival | **DO NOT INHERIT** | each reactivated object must regain its own live justification |
| `CognitiveGraph.add()` last-write-wins node identity | **DERIVED VIEW ONLY / HARDEN** | relation index cannot redefine canonical semantic identity |
| deterministic counterexample/debt re-proposal lifecycle reset | **DO NOT INHERIT** | idempotent proposal cannot regress verified/resolved state |
| `ResearchRevisionMemory` duplicate-ID rejection | **REUSE PATTERN** | demonstrates immutable logical identity boundary |
| `DurableMemoryRegistry` differing-same-ID rejection | **REUSE PATTERN** | demonstrates collision detection rather than overwrite |

The table is a design constraint: code reuse is subordinate to semantic ownership.

---

# PART XII — NOLANE WORLD W5 RESEARCH CAMPAIGN FOR V0.6

# 126. W5 problem formulation and anti-goals

A new W5 QSE research world was opened specifically for the v0.6 rewrite. Its goal is not “invent more memory features.” The goal is to eliminate hidden semantic choices around evidence, transformation, preservation, recall, repair, forgetting, interference and continuity while reducing the fragmented architecture inherited from the research notebooks.

The research contract includes explicit anti-goals:

```text
no feature-count growth as a quality proxy
no one-class-per-sentence architecture
no universal future-query completeness claim
no model self-certified correctness
no full-history context strategy
no generic planning/orchestration expansion
```

The W5 world is research scaffolding. Its gate is intentionally not self-authorized by this document.

---

The campaign asks for the smallest deep memory kernel capable of surviving lifelong transformation, forgetting, reconstruction and repair. Anti-goals are treated as hard research constraints: no generic planner/orchestrator, no database-per-memory-role, no universal future-query guarantee, no scalar fidelity/authority proxy and no W5 pass obtained from self-attestation. The purpose of W5 is to generate pressure and preserve debt, not to decorate the document. A mechanism is admitted only when a counterexample shows the existing semantic vocabulary is insufficient or when multiple representation shifts independently require the same primitive.

# 127. Six material representation shifts

The campaign uses six representations that change the available operations.

**Lossy compilation with proof obligations.** Memory representations are compiled artifacts; query families are observables; future failed probes become compiler counterexamples. This reveals preservation/repair semantics.

**Event-sourced epistemic state machine.** Memory changes become commits over evidence, claims and justifications. This reveals historical judgement, retry, concurrency and invalidation semantics.

**Semantic virtual memory.** Canonical history is backing state; Recall Frames are working sets; hydration is a semantic page fault. This reveals context-locality and representation-selection semantics.

**Feedback control system.** Query failures are error signals; maintenance/repair are controller actions; semantic debt is residual error. This reveals fixed points, oscillation and maintenance thrashing.

**Property-scoped capability preorder.** Representations are compared only on declared observables, often incomparably. This reveals why scalar fidelity and “one best memory” are unsafe.

**Associative reconstruction substrate.** Activation is used for candidate discovery while authority remains external. This preserves the strongest cognitive/Tề Hạ intuition without allowing association to decide truth.

A concept that is useful in only one representation is treated skeptically; concepts that recur across several views are more likely to be kernel-level.

---

# 128. Nine prediction-bearing hypotheses

The W5 campaign records nine mechanism-distinct hypotheses rather than nine wordings of “memory should be good.”

1. **Answerability-relative correctness:** representation validity alone cannot predict query correctness; bounded observables are required.
2. **Partial capability order:** many representations are incomparable; scalar fidelity loses hard distinctions.
3. **Recall as constrained cover:** hard-role evidence cover will prevent errors that fixed top-k ranking hides.
4. **Witness-cover forgetting:** retention informed by protected semantic obligations prevents irreversible query holes better than access-frequency heuristics alone.
5. **Counterexample-guided local repair:** future query failures can refine affected regions without global rewrite.
6. **Effect/truth separation:** consumer harm/benefit is scoped and does not coincide with factual truth.
7. **Rebuildable meta-memory:** capability/effect/debt indexes can be reconstructed from canonical receipts without owning truth.
8. **Semantic equilibrium:** stable evidence/policy should lead to local fixed points rather than perpetual summary drift.
9. **Boot reconstruction instead of transcript replay:** decision-relevant continuity can survive resets with bounded context and current-world verification.

Each has a kill criterion in the W5 ledger. v0.6 does not treat them as proven merely because the document is organized around them.

---

# 129. Four discriminating experiments and seven adversarial attacks

The W5 program preregisters four small discriminating experiments:

- scalar fidelity versus a protected semantic-loss vector with one decision-changing negation;
- fixed top-k versus hard-role cover under distractor load and a rare counterexample;
- global rebuild versus local counterexample repair in one of a thousand independent regions;
- similarity-based harm inference versus paired memory intervention across model/rendering profiles.

Seven attacks target the champion architecture: query-family explosion, self-referential preservation proof, witness-cover combinatorial cost, counterexample repair overfitting, effect-ledger suppression of hard memory, retention destroying corrigibility, and recursive meta-memory explosion.

The v0.6 architecture contains explicit answers, but these answers remain engineering hypotheses until implemented and evaluated at scale.

---

The experiments are designed to discriminate architectural explanations rather than produce generic benchmark gains. They compare raw-log reconstruction against persistent representations; exact hard-role retrieval against similarity-only search; source rebase against repeated summary repair; and scoped effect profiles against global memory-harm scoring. Adversarial attacks include duplicate-event support inflation, applicability leakage, counterexample pollution, lossy critical compression, origin laundering, query-family expansion and shared-profile repair blast radius. Each experiment has a failure update rule: if the challenger matches Nolane on quality/cost while using fewer semantics, the contested Nolane mechanism loses canonical status rather than being defended by prose.

# 130. Robustness worlds

At least six worlds are retained as cross-mechanism stress cases:

1. million-item store with fixed twelve-object hard dependency width;
2. genuine dependency width grows beyond context budget;
3. model upgrade reverses a previously learned interference profile;
4. privacy deletion removes the only raw source for an exact family;
5. one poisoned origin generates many derived summaries/agent echoes;
6. a query five transformation generations later exposes a lost exception.

The expected safe behavior is not always “answer correctly.” It may be explicit insufficiency, revalidation, local rebase, scope block or irrecoverable gap. Silent promotion to `SAFE/SUFFICIENT/VERIFIED` is the primary failure signal.

---

Robustness worlds deliberately change what a memory system finds easy. Repository work emphasizes tool/version/procedure drift; personalized dialogue stresses corrections and temporal duration; dynamic APIs expose delayed observations and environment gotchas; multi-agent projects stress origin/scope/common-mode dependence; high-volume event streams stress maintenance and witness retention; weak-model consumers stress context interference; privacy-constrained worlds remove source evidence and test honest irrecoverable-gap behavior. A mechanism that only survives one world is a profile/policy candidate, not a universal kernel law. W5 keeps cross-world portability as explicit debt until independently tested.

# 131. Independent challenger: immutable raw log plus query-time reconstruction

W5 required a mechanism-level challenger rather than a cosmetic alternative. The challenger bans persistent compact semantic representations as authority-bearing operational artifacts. It keeps an immutable raw event/evidence log and reconstructs memory at query time using a broad temporal/entity graph and current LLM reasoning.

The challenger has real advantages: fewer generations of summary drift, simpler preservation semantics and less need to predict future query families. Its costs are query latency, context/search expense, difficulty with strong negative completeness, storage/privacy pressure and repeated reconstruction cost.

The comparison produces an important hybrid conclusion: **raw canonical evidence should remain the strongest witness/fallback where policy permits, while compact derived representations must justify their existence through bounded preservation/cost value.** Nolane Memory should not compact merely because compacting is fashionable.

---

The raw-log challenger is intentionally strong because it avoids representation drift by refusing long-lived abstractions: preserve immutable evidence and reconstruct everything query-time. Nolane only earns persistent representations if they demonstrably reduce latency/context/compute while preserving bounded observables, and if their failures are repairable through lineage. This challenger is a useful Occam pressure. It prevents procedures, summaries and anchors from existing merely because cognitive taxonomies expect them. In v0.6 they survive as representations because repeated reconstruction has cost and because some learned abstractions can transfer, but none is allowed to become a second canonical truth owner.

# 132. W5 gate remains blocked

The current research world contains six material representations, nine prediction-bearing hypotheses, multiple falsifications/attacks, four discriminating experiments, six robust worlds and an independently reconstructed mechanism signature. It still does not pass W5.

The gate remains blocked by, among other things:

```text
minimum active cognitive residency not host-attested
critical unknowns remain open
no fresh-context independent verification
no independent source-family credit inside the QSE gate
material value-of-thought remains
hard quality floors are not independently attested
```

This is desired behavior. The world is being used to prevent premature closure, not to generate a badge for the document.

Machine-readable snapshot:

```text
NOLANE-MEMORY-V0.6-W5-DEEP-RESEARCH-SNAPSHOT.json
```

---

The fresh V0.6 W5 session is deliberately expected to fail closure at this stage. Required gates include rival resolution, claim provenance, contradiction repair, replication, benchmark validity, verifier/source independence, preregistration, nondeterminism control, environment contract, external validity, calibration and stopping rule. Open debts include future-query basis, preservation composition, repair locality, interference calibration, witness-cover approximation, capability refinement and external validity. Host-side formal oracles can narrow semantic uncertainty but cannot satisfy independent replication. Keeping the blocked verdict in the release is part of the integrity of the research process.

# PART XIII — BOUNDED FORMAL LAB: PRESERVATION CALCULUS

# 133. Why v0.6 uses exhaustive tiny worlds instead of more hand-written examples

The v0.5 research accumulated many individually named oracles. They were useful but encouraged document fragmentation and made it easy to test only examples chosen by the author. v0.6 adds a different kind of evidence: a tiny formal model whose state space is small enough to enumerate or heavily fuzz.

The model has five protected semantic dimensions, representations with preserved/recoverable subsets and costs, bounded query families expressed as required-dimension sets, hard Recall Obligations, witness-cover deletion, effect-profile scoping and local repair. It is intentionally too small to be a production architecture. Its job is to falsify proposed laws.

The artifact is:

```text
NOLANE-MEMORY-V0.6-PRESERVATION-CALCULUS-LAB.json
```

The lab currently records sixteen property families with zero failures under the executed bounded state spaces. Passing those properties is evidence only for the reference semantics they encode.

---

Hand-written examples are excellent for explanation but weak as the only semantic evidence because the author chooses the easy cases. Tiny exhaustive worlds invert the tradeoff: reduce the domain until all combinations of capability sets, witness subsets, justification states or frame budgets can be enumerated. Any proposed law that fails there is rejected before implementation. Seeded fuzz then adds long composition sequences that enumeration would make combinatorially expensive. The combination resembles model checking plus property testing, while remaining intentionally below the complexity of natural-language extraction. This is closer to the research discipline used by Nolane Plan than simply accumulating more scenario prose.

# 134. Exhaustive answerability and refinement properties

For every combination of preserved dimensions `P`, recoverable dimensions `H` and query requirement set `Q` in the five-dimension model, the lab verifies:

```text
Q ⊆ P            -> EXACT
Q ⊆ P ∪ H        -> REHYDRATABLE (when not exact)
otherwise         -> UNSUPPORTED
```

It also enumerates the monotonicity that a representation exact for a stronger requirement remains exact for a weaker subset under the same semantic profile. This does **not** establish arbitrary query-family monotonicity in production; it validates the subset-based reference fragment and reinforces the rule that refinement relations must be explicit when requirements are more complex than sets.

---

The exhaustive model does not attempt natural-language reasoning. It deliberately shrinks the universe until semantic properties can be enumerated. Representation capabilities are small sets of observables; query obligations are subsets; transforms declare preservation/loss; source routes determine recoverability. Under this abstraction, the lab checks that an unknown family is never inherited as exact, local query counterexamples refine only their dependency region, and a representation chosen for a hard obligation actually covers the demanded dimensions. The value of exhaustive tiny worlds is not realism but discrimination: if a proposed law already fails in a four-dimension universe, scaling to embeddings and LLMs will not repair its semantics. Passing the model only permits the law to remain a candidate for implementation.

# 135. Loss absorption and rebase properties

Twenty thousand randomized pure-transform chains verify that preserved dimensions only stay or disappear; none reappear without rebase. Separate checks establish that restoration is legal when the restoring basis is explicitly `raw-source` or `new-evidence`.

This bounded model directly supports Law C. It does not prove an LLM loss detector can identify every lost semantic relation. That remains an open implementation/calibration problem.

---

Loss composition is intentionally asymmetric. Once a protected dimension is `LOST` through a pure derivation chain, later paraphrase or summarization cannot return it to `EXACT`; that would be information creation. Recovery has two legitimate paths: rebase against a retained stronger source or admit genuinely new evidence. The runtime records which path occurred because they have different historical meaning. Source rebase restores representation fidelity relative to old evidence; new evidence changes what the system knows. The bounded lab enumerates transform chains and separately fuzzes long chains to ensure the algebra cannot accidentally promote `LOST`/`UNKNOWN` through composition. This is a conservation law, not a similarity heuristic.

# 136. Witness-cover deletion and hard-frame feasibility properties

The lab generates thousands of small representation sets and protected query obligations. For deletion, it compares the runtime witness-cover rule against exact enumeration of whether every previously protected obligation still has a witness. For frame compilation, it exhaustively searches small candidate subsets under token-like costs and verifies that no `SUFFICIENT` frame lacks a hard role or exceeds the budget.

These tests separate **optimization quality** from **correctness**. A future heuristic is allowed to find a more expensive feasible frame than the optimal solver. It is not allowed to return a cheaper infeasible frame and call it sufficient.

---

Witness-cover deletion models forgetting as a constrained set-cover problem: protected semantic dimensions must remain reconstructible from at least one retained witness route, unless an authorized retention decision explicitly accepts an irrecoverable gap. Hard-frame feasibility uses the same logical shape on the read side: hard roles must be covered by selected representations under the current budget or the compiler returns overflow. The connection is useful. Retention decides which future proof/reconstruction routes continue to exist; recall decides which routes must be materialized now. Treating both as coverage problems lets the runtime share formal vocabulary without conflating their policies. The lab exhaustively enumerates small deletion and frame-cover worlds rather than trusting greedy ranking behavior.

# 137. Applicability, event identity, justifications and local repair properties

The formal lab also constructs at-least-once delivery logs and verifies that semantic event support is idempotent despite multiple deliveries. Success rates are computed inside applicability slices rather than after global tag union. OR-of-AND justification behavior is enumerated over all live subsets of `{A,B,C}` for `(A∧B)∨C`.

A 1,000-region repair model confirms the reference local-update law: a counterexample targeting one independent region changes only that region's version. This does not prove a real dependency graph will always have such clean locality; it verifies the intended blast-radius semantics when independence is explicit.

---

These properties attack a class of aggregation bugs. Evidence must first be scoped to the condition under which a claim/procedure is proposed; repeated deliveries of one source event collapse to one event identity; justification alternatives retain conjunction/disjunction semantics; and a local repair modifies only the region/profile dependencies falsified by the counterexample. None of those rules requires a perfect ontology. Applicability can be expressed by typed predicates and regime references that start conservative. What matters is that “same lesson text” or “same tag set” never silently substitutes for proof that evidence applies to the current condition. The bounded model explicitly contains opposite outcomes under different slices so generic promotion must fail.

# 138. Lifelong fuzz properties

A separate fifty-thousand-step fuzz loop applies transforms, queries, source deletion and raw-source rebase across two hundred regions. The checked invariants are intentionally simple and hard: pure transformations never resurrect lost dimensions, unknown/unsupported query states are never coerced into safe exact answers, and source deletion removes the rebase path rather than triggering fabricated reconstruction.

The value of this fuzzing is not the number of steps. It creates an executable semantic regression target that can later be replaced by the actual kernel implementation while preserving the expected laws.

---

The lifelong fuzz component is designed to expose violations that only emerge after composition. Random transform chains repeatedly encounter `LOST`, `UNKNOWN`, rehydration and query-family expansion; region-local repairs run amid unrelated regions; witness deletion changes recoverability; maintenance repeats over stable normalized semantics. The important assertion is not that random testing proves correctness. It is that the laws survive thousands of state transitions without relying on the exact sequence chosen by a hand-written oracle. Seeds and normalized artifacts make every discovered failure reproducible. A future implementation should extend this into property-based and state-machine fuzzing against the real persistence layer, especially across crashes and migrations.

# 139. What the bounded lab does not prove

The lab does not prove that natural-language semantic dimensions can be extracted soundly, that a learned query-family compiler is complete, that large representation covers are cheap, that causal interference is identifiable, or that a million-node graph meets latency targets. It also does not constitute independent verification because the reference model was designed in the same research process as the specification.

These limitations are retained explicitly so that a green lab cannot become another false memory of “formal correctness.”


---

The model does not test whether an LLM correctly extracts a negation, identifies an entity, infers a causal relation or recognizes that two natural-language questions belong to the same query family. It does not establish production latency, distributed failover, privacy compliance or benchmark superiority. It also cannot prove universal future-query preservation because the observable basis is finite by construction. These omissions are not weaknesses to hide; they define the boundary between *semantic closure* and *empirical capability*. The spec uses the lab only to reject internally inconsistent laws. Natural-language extraction, calibration and external validity remain W5 debt and require different evidence such as held-out benchmarks, differential implementations and independent replication.

# PART XIV — CURRENT PRIOR ART: LEARN THE MECHANISM, DO NOT COPY THE PACKAGE

# 140. Why prior-art comparison is mechanism-based

The 2025–2026 agent-memory field is fragmented: systems called “memory” may be a vector store, temporal graph, procedural library, learned controller, event reconstruction system, state tree or context compiler. A useful comparison cannot ask which product has the longest feature list. v0.6 compares **mechanism classes** against the failure physics above.

The guiding questions are:

```text
What representation does the system preserve?
How does memory evolve?
What makes a write authoritative?
How does time/update conflict work?
How is recall selected?
What happens when retrieval hurts?
Can compression be falsified/repaired?
What is the context-scaling claim?
What security/poisoning boundary exists?
```

Nolane Memory does not claim novelty for event sourcing, temporal graphs, spreading activation, CEGAR, MVCC, truth maintenance or information-flow control. Its research claim is their composition around a memory-specific semantic virtual-memory runtime.

---

The comparison axis is the underlying memory problem each work addresses: associative recall, temporal continuity, event logic, multi-structure evidence, consolidation cost, procedural transfer, execution state, memory interference, poisoning or context compilation. This avoids superficial “feature table” reasoning where different systems are scored by whether they expose similarly named modules. For each mechanism v0.6 asks what failure it empirically reduces, what authority assumptions it makes, what context/storage cost it introduces and which Nolane invariant would be falsified if the mechanism's simpler model is sufficient. External benchmark numbers remain authors' claims and do not become Nolane evidence automatically.

# 141. Associative memory: HeLa-Mem, Synapse and AIM

HeLa-Mem and Synapse provide evidence that graph/associative dynamics and spreading activation can improve long-term agent recall beyond flat semantic similarity. AIM-style work additionally studies interference through associative-memory ideas, including sparse encoding/pattern separation and per-item interference tracking.

Nolane learns two things. First, query text is not the only useful retrieval cue; co-activation, graph paths and anchors can recover semantically distant but structurally related experience. Second, association creates its own interference/popularity dynamics and therefore needs normalization, inhibition and effect measurement.

Nolane deliberately does **not** treat activation as authority. The associative layer produces candidate regions. Grounded evidence, temporal validity and representation answerability decide what can satisfy a hard obligation.

Representative sources:

```text
HeLa-Mem — ACL 2026
Synapse — Findings ACL 2026
AIM — ICLR 2026 Associative Memory workshop paper
```

---

HeLa-Mem and Synapse strengthen the case that associative paths/spreading activation can recover relevant experiences missed by flat similarity. AIM-style interference research adds the opposite pressure: associations can also retrieve memories that systematically hurt under domain shift. Nolane therefore uses activation as a non-authoritative candidate dynamic with explicit decay/fan normalization/inhibition and effect-scoped calibration. The research novelty is not Hebbian association itself. The question is whether associative recall remains useful when placed behind principal filtering, counterexample obligations and representation-resolution contracts rather than being allowed to directly define the model-facing memory set.

# 142. Multi-structure memory: MAGMA, MESA, event graphs and temporal graphs

MAGMA's semantic/temporal/causal/entity graph separation supports the intuition that one relation structure is insufficient. MESA's task-adaptive evidence-structure selection pressures the opposite failure: using all structures all the time can add noise and tokens. CompassMem and SEEM emphasize event-centric logical/narrative structure, while Zep/Graphiti and APEX-MEM emphasize evolving temporal/entity facts and retrieval-time conflict resolution.

Nolane's synthesis is **region-level multi-view discovery**. It avoids declaring any one graph canonical. Required role types can force a view; optional views can be routed adaptively. All results resolve to semantic regions whose representation fibers still carry independent preservation and authority semantics.

This is narrower than “build the biggest knowledge graph” and stronger than “let a router choose whichever graph seems relevant.”

---

MAGMA/MESA and event/temporal graph work support the claim that one structural view is insufficient: time, entities, causal/action relations and semantic similarity answer different retrieval questions. v0.6 avoids turning each view into a separate canonical graph universe. Typed projections are derived from the same evidence/claim/region substrate and can be rebuilt. A router may select optional views by query/task, but hard obligation roles determine required structural capabilities first. This addresses a weakness of learned all-purpose routing: a cheap router cannot decide that current-regime or counterexample evidence is “unlikely to matter” when the correctness contract says it is mandatory.

# 143. Temporal memory: TSM and TiMem

TSM explicitly identifies two failure classes relevant to v0.6: organizing memory by dialogue time rather than semantic occurrence time, and fragmenting persistent state into point memories. It constructs semantic timelines and durative memory. TiMem uses a temporal-hierarchical tree and semantic-guided consolidation across abstraction levels.

Nolane incorporates temporal occurrence/knowledge-time separation and durative state as first-class semantics, but adds a different question: **what temporal query precision did a representation preserve?** A durative summary may answer broad persistence while remaining unable to certify exact boundaries. This is captured through query-family preservation rather than assumed from the representation type.

The hierarchy is therefore a representation strategy, not the truth model itself.

---

TSM explicitly identifies temporal inaccuracy and temporal fragmentation: dialogue/ingestion order is not the same as semantic occurrence time, and point-wise memories lose persistent-state duration. TiMem adds hierarchical temporal consolidation across longer conversational horizons. v0.6 adopts the pressure but tightens the semantics: durative claims carry coverage/uncertainty and preservation envelopes, so two equal endpoint observations do not automatically certify continuous truth between them. Knowledge-time remains separate from valid-time, and a compact temporal representation may be exact for broad ordering while remaining unknown for exact interval boundaries. This prevents temporal hierarchy from gaining precision simply through abstraction. TSM's current ACL 2026 abstract reports improvements on LongMemEval/LoCoMo, which is useful empirical pressure but not proof of Nolane's stronger interval contracts.

# 144. Reconstruction systems: MRAgent, CompassMem, SEEM and APEX-MEM

These systems reinforce a major v0.6 premise: memory often must be reconstructed from relations/events rather than returned as independent chunks. Active traversal can discover an explanation that no single embedding-nearest item contains.

Nolane strengthens the epistemic boundary around reconstruction. Candidate histories can coexist. Inferred bridges remain inferred. Historical judgement and current retrospective truth are separate. A reconstruction carries source handles and can return ambiguity when evidence does not discriminate histories.

The runtime goal is not “generate the best story of the past.” It is “produce the smallest coherent memory state adequate for the current decision, with uncertainty intact.”

---

MRAgent's active reconstruction and event-logic systems such as CompassMem/SEEM support moving beyond isolated top-k chunks. APEX-MEM-like proactive/structured memory work adds pressure toward query-conditioned composition. v0.6 treats reconstruction as a separate projection phase after region discovery and representation resolution. The reconstructor may hypothesize bridges and alternatives, but every bridge is typed inferred unless grounded by canonical evidence. This allows coherent episodes without narrative laundering. Competing reconstructions remain set-valued when decision-distinct ambiguity survives; a fluent top-1 story is not accepted merely because it reads better.

# 145. Consolidation and compilation: RecMem, LycheeMemory V2, WiCER and TrustMem

RecMem demonstrates that expensive LLM consolidation need not occur after every interaction; recurrence can trigger slower memory formation. LycheeMemory V2 shows that semantic segment-level consolidation can materially alter construction-cost/accuracy tradeoffs. WiCER frames compilation failures through diagnostic probes and iterative refinement; blind compilation can catastrophically discard facts. TrustMem explicitly evaluates memory update transitions for coverage, preservation and faithfulness.

v0.6 combines these pressures into one transformation discipline:

```text
fast raw/evidence capture
selective consolidation triggers
explicit granularity contract
protected semantic dimensions
transition verification
counterexample-guided refinement
source rebase
```

Recurrence is not enough for one-shot critical failures. Segmentation is not safe by default. Diagnostic success on observed probes is not universal future-query completeness. A verifier is not authority if it shares the same failure mode as the generator.

This is one of the clearest areas where Nolane Memory becomes more than a retrieval system: **memory evolution itself is a correctness-bearing process**.

---

# 146. Procedural memory: Memp, ReMe, ReasoningBank and AFTER

Recent procedural-memory work demonstrates that agents can improve through reusable strategies, reflections, failure-derived guidance and experience libraries. Benchmarks increasingly test cross-task, cross-role and cross-model transfer rather than only factual recall.

Nolane adopts procedural memory as a first-class representation role but refuses to equate “lesson text retrieved” with safe transfer. Applicability, negative exceptions, executor capability, evidence-event identity and failure conditions remain part of the procedure contract. Success statistics are sliced by conditions. Common-mode evidence does not become independent replication. Negative transfer is reported rather than hidden.

The procedure is therefore closer to a versioned, evidence-backed executable hypothesis than a note saying “next time do X.”

---

Procedural-memory research consistently shows value in remembering strategies, lessons and failures rather than only facts. Nolane tightens the transfer boundary: a procedure is not a free-form tip but a representation whose support, applicability, exceptions, executor capability, source regimes and counterexamples are inspectable. Cross-task or cross-model transfer expands scope only after evidence. Failure memories can generate negative applicability rather than one global success rate. The AFTER-style emphasis on transfer evaluation is particularly relevant because the main risk of procedural memory is not recall miss but confidently reusing a once-successful strategy in the wrong structural condition.

# 147. State-management memory: MAGE and proactive memory agents

MAGE argues that long-horizon agent memory can be better understood as execution-state management than semantic storage. Proactive-memory work similarly treats memory as an intervention that can decide when to inject state rather than a passive bank exposed every turn.

Nolane learns the importance of action/outcome state transitions and selective injection. It does not allow the memory layer to absorb planning or action authority. The Recall Obligation can identify a prior execution state that must be surfaced; procedure/agent runtime still decides what to do.

This separation is particularly useful for coding/tool agents, where “what has already been tried and what state actually changed?” is often more valuable than a semantically similar conversation.

---

MAGE-style execution-state memory makes a strong point for agent tasks: long-horizon competence depends on state transitions, attempts and recovery structure, not only conversational facts. v0.6 captures this information in event/action/outcome relations and procedure/failure representations while keeping the memory layer separate from active task orchestration. Proactive memory agents similarly motivate prospective triggers and prefetching, but the trigger only wakes a Recall Obligation. The distinction preserves the power of stateful memory without allowing stored state to become future action authority.

# 148. Causal memory selection and negative transfer

Causal Intervention-Based Memory Selection explicitly estimates candidate-memory effect through controlled interventions, challenging the assumption that topical relevance equals usefulness. Longitudinal safety work shows that accumulated memory can change violation rates across deployment length. AIM-style interference work suggests effects can concentrate in identifiable memories and depend on domain/model context.

Nolane uses these results to justify an **effect plane** separate from epistemic truth. It is intentionally conservative: observational correlations cannot trigger the strongest causal inhibition policy, and effects do not transfer across consumer/task/regime/rendering by default.

Hard memory obligations remain protected even when effect evidence is negative. The response can be alternative rendering or explicit insufficiency—not deletion of the required fact.

---

Similarity-based retrieval can be empirically useful yet causally harmful. Memory selection studies that compare with/without exposure motivate a richer effect ledger: retrieval relevance is a prediction about usefulness, while causal effect evidence tests the prediction. Nolane uses interventions to learn optional selection/rendering policies and to detect negative transfer, but factual authority remains untouched. The hardest open problem is calibration under distribution shift: a memory's effect depends on consumer, task, regime and co-context. That is why global “memory helpfulness” scores remain policy heuristics rather than kernel truth.

# 149. Security: origin-bound authority, GhostWriter and lifecycle repair

The 2026 literature provides several independent pressures on the memory-security and proactive-use seams, but v0.6.1 treats each source as **claim-scoped pressure**, not proof of the Nolane design.

**Mem2ActBench** (ACL 2026) evaluates whether memory is actively applied to tool selection and parameter grounding rather than merely retrieved for explicit questions. Its results motivate action-boundary memory obligations; they do not prove that Nolane's obligation compiler is complete.  
Reference: `https://aclanthology.org/2026.acl-long.370/`

**Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents** (2026 preprint) studies “behavioral state decay” and selective memory-grounded intervention. It motivates explicit proactive wake/application semantics; it does not establish a universal optimal intervention policy.  
Reference: `https://arxiv.org/abs/2607.08716`

**FragFuse** (2026 preprint) demonstrates that benign-looking memory fragments can be injected separately and later fused to bypass tested access-control mechanisms. This pressures the architecture toward whole-frame/sink composition checks; it does not prove that the proposed composition gate is sufficient.  
Reference: `https://arxiv.org/abs/2606.15609`

**SPORE** (2026 preprint) shows a different seam: user-isolated long-term memory can still be exfiltrated when an agent copies retrieved memory into malicious tool parameters. This directly motivates treating tool-parameter serialization as a disclosure boundary distinct from retrieval access.  
Reference: `https://arxiv.org/abs/2607.23444`

**AgentSecBench** (2026 preprint) frames instruction integrity, retrieval confidentiality and capability integrity around projections onto authorized observations/capabilities and distinguishes prompt annotations from enforcement. It motivates provenance/capability projection before generation/action but does not certify Nolane's policy algebra.  
Reference: `https://arxiv.org/abs/2605.26269`

**Back-Reveal** (2026 preprint) demonstrates memory-access-to-tool-call exfiltration under a backdoored-agent threat model. It is evidence that the memory→tool seam deserves an explicit sink check, not evidence that every normal agent is backdoored.  
Reference: `https://arxiv.org/abs/2604.05432`

**GateMem** (2026 preprint) evaluates multi-principal shared-memory utility, access control and active forgetting together and reports that tested systems do not simultaneously solve all three. It motivates treating shared-memory publication/governance as first-class semantics rather than “one global vector store.”  
Reference: `https://arxiv.org/abs/2606.18829`

The authoritative `NOLANE-MEMORY-V0.6.3-CLAIM-SCOPED-EVIDENCE-REGISTER.json` records publication class, allowed inference and forbidden overclaim for every external/internal source used by this research line. That register is part of the release evidence bundle; a title appearing in prose is not enough to grant it broader evidentiary scope.

# 150. Long context remains the honest baseline

A memory architecture can add cost and failure modes that a large-context model does not have. EvoMemBench and other contemporary evaluations show that no one memory form dominates every setting, and long context can remain competitive.

Every Nolane Memory evaluation therefore includes no-memory and long/full-context baselines wherever feasible. Memory wins only if it improves the quality/cost/reliability frontier under comparable models, tool access and context budgets. A token-saving method that changes the bounded decision is not an efficiency success.

This baseline pressure also constrains architecture complexity. If a sophisticated preservation certificate costs more than simply hydrating a small raw source for a low-frequency task, the runtime should use the raw source. The system is allowed to be pragmatic.

---

Long context is a powerful and conceptually simple competitor: it avoids some extraction/consolidation errors by keeping the original history available to the model. As context windows and model capability improve, the burden of proof on complex external memory increases. v0.6 therefore uses full-history or very-long-context baselines wherever the bounded world fits and includes memory construction/maintenance cost in comparisons. Nolane only wins legitimately when it preserves decision quality while reducing context/latency or enabling histories too large/structured/private for direct replay. External memory is not assumed superior by definition.

# 151. Prior-art boundary: the distinctive composition

No individual mechanism in v0.6 should be marketed as if Nolane invented it. The distinctive research object is the composition:

```text
canonical evidence + truth maintenance
        ↓
semantic regions with multi-representation fibers
        ↓
property-scoped preservation/answerability contracts
        ↓
obligation-driven multi-view recall
        ↓
semantic page faults + active reconstruction
        ↓
explicit sufficiency / ambiguity / overflow
        ↓
query-counterexample local repair
        ↓
witness-cover forgetting
        ↓
consumer-scoped effect/interference control
        ↓
Tề Hạ-style continuity anchors under current verification
```

The question to be tested is whether this composition can provide **large external memory with small trustworthy context and long-term corrigibility** at acceptable systems cost.

---

The distinctive hypothesis is therefore a composition, not a novelty claim over each mechanism. Associative activation, temporal graphs, episodic summaries, procedure memories, CAS logs, truth maintenance and context compilation all have prior analogues. Nolane Memory combines them under a stricter ownership rule: canonical evidence/claims/justifications remain stable; every derived representation carries bounded preservation and recoverability semantics; recall chooses representations by obligation; and failures discovered by future queries feed counterexample-guided regional repair. The research question is whether this composition yields a memory runtime that can become very large and adaptive without becoming an ever-growing un-auditable prompt cache. Prior art is used to pressure individual mechanisms, while Nolane-specific experiments must test the composition and its failure boundaries.

# PART XV — METRICS AND EXPERIMENTAL PROGRAM

# 152. Metrics must separate memory quality from retrieval popularity

Hit rate, retrieval recall and answer accuracy are insufficient on their own. v0.6 groups metrics into five families: semantic correctness, representation preservation, recall/frame correctness, lifelong effects and systems cost.

Semantic metrics include current-fact accuracy, historical as-of accuracy, contradiction handling and support-grounding errors. Preservation metrics include protected-dimension loss, counterexample escape, representation answerability calibration and irrecoverable-gap creation. Recall metrics include hard-role coverage, counterexample recall, ambiguity collapse, wrong decision without escalation and frame token cost. Lifelong metrics include negative transfer, repeated-failure recurrence, longitudinal contamination and repair success. Systems metrics include commit latency, write-to-query visibility, hydration latency, consolidation cost, index rebuild, storage tier size and invalidation fanout.

No single aggregate “memory score” should decide architecture claims.

---

Popularity metrics—access count, retrieval frequency, embedding centrality—measure interaction with the retrieval policy as much as intrinsic value. A memory can become popular because the system keeps surfacing it, creating a feedback loop. Quality metrics instead target correctness and downstream contribution under controlled conditions: obligation coverage, current/as-of truth accuracy, procedure applicability, counterexample preservation, reconstruction ambiguity, context cost and causal effect. Popularity can inform cache/activation decisions but cannot be promoted into authority, independence or retention protection without an explicit policy.

# 153. Core semantic error metrics

Reference metrics include:

```text
Memory Authority Promotion Error (MAPE)
    unsupported/dependent memory gains authority

Ambiguous Recall Collapse Error (ARCE)
    decision-distinct histories collapsed to one confident answer

Wrong Decision Without Recall Escalation (WDWRE)
    bounded decision wrong while frame claimed sufficient

Cross-Principal Influence Leak (CPIL)
    inaccessible memory changes principal-visible reasoning

Reconsolidation Semantic Drift (RSD)
    transformation changes protected meaning without declared loss

Duplicate Evidence Amplification Rate (DEAR)
    retry/copy/delivery increases support incorrectly

False Independence Promotion Rate (FIPR)
    dependent sources satisfy an independence gate
```

For tiny semantic oracles the target is zero silent violations. Production error rates require empirical calibration.

---

A single accuracy score hides the failure modes that matter most for persistence. The core error suite therefore separates false authority promotion, stale-current projection, historical hindsight leakage, invalidation error, scope influence leak, hard-role omission, false negative completeness, fabricated recovery and irrecoverable-gap concealment. Many of these should be evaluated as *silent violation rates*: returning an explicit `AMBIGUOUS` or `INSUFFICIENT` result is often safer than producing a wrong confident frame. For bounded formal worlds the target silent violation count is zero. In real benchmarks, the report must preserve numerator/denominator and abstention/overflow behavior rather than folding all outcomes into answer accuracy.

# 154. Preservation and corrigibility metrics

v0.6 adds metrics that ask whether memory knows its own representational limitations:

```text
Protected Query Family Coverage
Preservation Envelope Calibration
Counterexample Detection Latency
Local Repair Blast Radius
Source Rehydration Success
Irrecoverable Gap Rate
Protected Witness-Cover Violation Rate
Cumulative Loss Discovery Depth
Raw-Source Rebase Frequency and cost
```

A high counterexample count is not automatically bad; a system that exposes and repairs losses can be safer than one whose compact representations are never challenged.

---

Preservation metrics operate at the level of declared observables. Useful measurements include protected-dimension retention, query-family answerability coverage, source-rehydratability rate, irreversible-gap rate, counterexample-to-repair latency, repair locality/blast radius, cumulative derivation depth before rebase, and regression-witness recurrence. A representation can be compact while still scoring badly if it destroys the one observable required by later tasks. Conversely a representation that is not textually similar to its source can be semantically exact for the declared query family. Metrics should therefore compare normalized answers/witnesses or typed fields rather than rely on embedding similarity as the preservation oracle.

# 155. Context-scaling metrics

Two elasticities are measured separately.

`MCE_total` measures model-context growth as total stored memory grows while true required dependency width remains fixed. Desired behavior is near-flat/sublinear context with stable decision quality.

`MCE_width` measures context growth as true dependency width increases at fixed store size. Here growth is expected; once the budget cannot represent the hard cover, overflow or staged hydration is correct.

Report p50/p95/p99 frame tokens and latency. Average-only metrics hide pathological long-tail recalls.

---

Context scaling must be measured on two orthogonal axes. First, grow total memory size while fixing the true required dependency set; a successful virtual-memory design should keep Recall Frame tokens roughly stable and retrieve from local indexes rather than replaying the store. Second, grow the true dependency width while holding total store size fixed; frame size must then grow, stage-hydrate or explicitly overflow. Reporting only the first creates an incentive to silently prune hard evidence. The experiment should include p50/p95/p99 frame tokens, page-fault count, hydration latency, required-role coverage, wrong-decision-without-escalation and cache hit rate. Long-context/full-history remains the oracle baseline in bounded worlds where it fits.

# 156. Effect/interference metrics

Effect evaluation reports both benefit and harm:

```text
Memory-enabled vs NullMemory decision delta
optional-memory inhibition precision/recall
hard-role suppression attempts
cross-model effect transfer error
cross-task effect transfer error
rendering-sensitive effect delta
interference concentration
longitudinal violation rate versus memory prefix
```

Causal-evidence tier is always reported with the effect estimate. Observational harm and paired-intervention harm are not merged into one undifferentiated confidence number.

---

Effect metrics need causal discipline. Report memory exposure stage, consumer/model version, task family, regime, rendering and competing memories. Observational correlation (`memory retrieved before error`) is a weak tier; paired or randomized with/without-memory interventions are stronger. Metrics include negative-transfer delta, unnecessary-context cost, hard-role suppression attempts, effect-profile transfer error, rendering sensitivity, multi-memory attribution ambiguity and intervention stability across seeds. Crucially, the effect ledger never modifies factual confidence. Its job is to decide *how* or *whether* a memory representation should be exposed to a particular consumer, not whether the underlying claim is true.

# 157. Benchmark portfolio

No single public benchmark validates Nolane Memory. A reasonable portfolio includes:

- LongMemEval / LongMemEval-V2 for multi-session, update, workflow and long-haystack memory;
- LoCoMo for conversational multi-hop and temporal memory;
- AMA-Bench for long-horizon agent trajectories, objective and causal pressure;
- MemoryArena for interdependent multi-session action tasks;
- ImplicitMemBench for behavioral/procedural adaptation;
- AFTER-style procedural transfer evaluation;
- HaluMem / transition-focused datasets for memory update hallucination;
- security lifecycle benchmarks such as poisoning Write→Execute→Repair settings;
- private synthetic Nolane semantic worlds for invariants public benchmarks do not contain.

Public scores remain comparative evidence, not architecture truth.

---

The portfolio deliberately mixes conversational, temporal, agentic and procedural settings because one benchmark can reward the wrong memory abstraction. LongMemEval/LongMemEval-V2 and LoCoMo stress long-horizon retrieval and updates; AMA-Bench and MemoryArena stress action-coupled causal/objective memory; ImplicitMemBench and procedural-memory suites pressure behavioral reuse; private Nolane oracle worlds target correctness gaps that public benchmarks do not expose. Every benchmark result is paired with no-memory and long-context baselines where feasible. Public benchmark success does not discharge private semantic debt, and private synthetic success does not establish external validity.

# 158. Mandatory baselines and fairness contract

Every serious experiment records base model/version, context limit, tool access, embedding/reranker, consolidation model, memory construction cost, maintenance cost, storage size, random seeds and judge configuration.

Required baselines include no persistent memory, full/long context where feasible, lexical+dense RAG, extracted fact memory, temporal graph memory, event/reconstruction memory, procedural memory and representative multi-structure approaches. Nolane ablations then remove causal view, association, counterexample reserve, preservation certificates, source rebase, effect gating, witness-cover retention and other key mechanisms one at a time.

A method is not allowed a larger hidden model/tool/token budget and then described simply as “better memory.”

---

Every serious comparison reports the base model/version, context limit, tools, retrieval/consolidation models, embedding/reranker/index generations, memory-construction tokens, maintenance cost, storage size, seeds and evaluation/judge setup. Required baselines include no persistent memory, long/full context where feasible, strong lexical+dense RAG, representative temporal/graph/procedural memory and Nolane ablations. If Nolane uses a stronger model or more tool calls, the confound is labeled rather than hidden. Cost-quality frontiers are more informative than one leaderboard number because memory systems trade write work, storage, recall latency and prompt tokens differently.

# 159. Ablations must attack composition, not only components

Some mechanisms matter only in combination. v0.6 therefore requires interaction ablations such as:

```text
association × lateral inhibition
consolidation × counterexample preservation
preservation envelope × source rehydration
query counterexample × local repair
witness-cover retention × privacy deletion
effect guard × hard-role conservation
multi-view discovery × representation resolution
Recall Obligation × context budget overflow
```

For example, testing counterexample-guided repair without source rehydration can make the repair mechanism look weak when the real limitation is retention. Testing effect gating without hard-role conservation can improve accuracy while creating a safety hole.

---

Removing one module at a time is insufficient because the central claims are compositional. Required interaction ablations include: preservation envelopes × source rehydration; associative activation × counterexample protection; multi-view discovery × obligation-based representation resolution; consolidation × witness-cover forgetting; interference guard × hard-role conservation; temporal duration × knowledge-time; and principal scoping × shared-memory propagation. A component can look useless in isolation while being necessary to prevent another component's failure. Conversely an “all mechanisms” system can appear strong because two errors cancel. Interaction ablations therefore report both task quality and semantic violation metrics.

# 160. Stress worlds that matter more than average QA

The private Nolane lab should repeatedly include worlds designed to make memory fail rather than merely answer questions:

```text
popular stale fact versus one fresh direct observation
rare catastrophic counterexample against 99 successes
same lesson with opposite outcome across applicability slices
late historical evidence after a consequential decision
lost negation five transformation generations deep
source deletion immediately before a future exact query
poisoned source laundered through many summaries/agents
model upgrade that reverses an interference profile
index lag after revocation/correction
context budget smaller than hard dependency width
shared-memory principal with partial visibility
crash during consolidation/admission
```

A safe typed abstention can be the expected result.

---

Average QA leaves many catastrophic mechanisms untouched. Stress worlds should deliberately include contradictory corrections, delayed evidence, high-degree associative hubs, duplicated lineages, regime/tool version shifts, same-content independent events, source deletion, private/public derivations, stale indexes, crash/retry, one-shot catastrophic counterexamples, weak consumers and context budgets below hard-role width. The expected outcome is often a typed escalation rather than an answer. A system that maintains accuracy by silently excluding overflow or scope-blocked cases has failed the stress protocol. These worlds are the bridge between bounded semantic oracles and production benchmarks.

# 161. Longitudinal experiment protocol

Take a fixed agent/consumer profile and memory stream. At increasing history prefixes, freeze a read-only memory snapshot. Evaluate anchor probes, fresh probes and incident probes with the same model/tool settings, plus a NullMemory run. Randomize stream order in separate trials where the causal question requires distinguishing content accumulation from sequence effects.

Record not only final errors but which memories were selected, rendered, referenced, and associated with the resulting action. This exposure chain allows later effect analysis to distinguish storage from candidate retrieval and actual model influence.

When a memory-induced incident is minimized, the reproducer becomes both an effect-evidence item and a regression test for the representation/selection path that caused it.


---

The protocol pins model/tool/rendering configuration and samples checkpoints across memory growth. At each checkpoint it runs stable anchor probes, fresh adaptation probes and incident/counterexample probes, plus NullMemory/long-context controls where feasible. It records representation depth, debt, source recoverability, page faults, context tokens, procedure reuse and effect profiles. When performance changes, the analysis asks whether the cause is memory accumulation, stream distribution shift, model randomness, index state or maintenance revision. This longitudinal design is necessary to detect slow poisoning, forgotten early constraints and telephone-game drift that endpoint-only evaluation can miss.

# PART XVI — REFERENCE ALGORITHMS AND STATE MACHINES

# 162. Capture algorithm: preserve evidence before interpretation

The capture path is optimized for durability and source fidelity. It should not wait for every expensive extraction or consolidation before making a consequential observation recoverable.

Reference sequence:

```text
capture(input, adapter_context):
    authenticate / identify channel where possible
    obtain stable source-event identity if adapter supports it
    distinguish transport delivery from semantic event
    bind origin, principal and confidentiality ceiling
    record event/observed/ingested time
    persist raw artifact or policy-permitted stable handle
    commit EvidenceEventRevision idempotently
    schedule extraction/region segmentation asynchronously
```

The path must preserve `UNKNOWN` when the adapter cannot establish a field. A connector timeout does not create a “no event” fact. An opaque source can be recorded as opaque without pretending the content was inspected.

If raw content cannot be retained for policy reasons, the capture receipt records the weaker forensic guarantee. Future preservation certificates cannot assume a raw rebase path that never existed.

---

Capture is split into a fast evidence-preservation path and slower semantic interpretation. Stable source-event identity, origin, timestamps, principal visibility, raw artifact handle and tool/action correlation are recorded first. Segmentation, entities, claims, causal edges and salience can be proposed afterward and revised. This order ensures that a wrong extractor does not replace the only source. Where privacy policy forbids raw retention, the capture contract records the resulting forensic/recoverability limitation. Tool transport success and verified world postcondition remain separate observations so “request returned 200” is not silently stored as “desired effect occurred.”

# 163. Region segmentation algorithm: boundaries are hypotheses with revisions

Event segmentation can be deterministic for tool/action boundaries and probabilistic for conversational/semantic transitions. The algorithm therefore produces a versioned region proposal rather than rewriting raw event order.

Useful split signals include:

```text
objective/subgoal change
action -> outcome boundary
user correction
environment/regime transition
failure/recovery episode
entity-state phase change
temporal discontinuity
```

Useful merge signals include one causal action chain or one continuous state whose individual messages are merely fragments.

A region merge/split preserves source event IDs and can be reversed. Counterexamples can refine segmentation: if a future query needs to distinguish two events that a segment merged, the transform/segmentation profile receives a regression witness.

The runtime should never make the event-segmentation model the only copy of historical ordering.

---

Region boundaries are revisioned because they influence consolidation granularity and repair blast radius. Initial boundaries can use event/action/outcome transitions, entity changes, temporal gaps or learned semantic segmentation. Later evidence may show that two fragments belong to one episode or that a previously merged region contains decision-distinct branches. A merge/split creates a new region revision while source evidence identities remain stable. Preservation certificates and descendant representations are then re-evaluated only where the boundary change affects their observable contract. This makes segmentation corrigible instead of a one-time irreversible preprocessing choice.

# 164. Claim admission algorithm

Claim admission is an evidence-grounded transition and now also an **optimistically validated transition**. The engine must not merely ask whether the candidate looked supported when it was assembled; it asks whether the material support/authority state that justified admission is still the state being committed.

```text
admit_claim(candidate, requested_level, expected_cut):
    pin canonical Admission/Recall Cut K

    normalize proposition + semantic scope
    resolve source-event identities and origin roots at K
    construct OR-of-AND justification alternatives at K
    check valid-time / knowledge-time semantics
    check principal / authority ceiling / integrity class
    check applicable counterexamples / revocation / compromise at K

    D = material dependency manifest:
          source revision + lifecycle generation
          origin/authority revision
          scope/regime/self-version where material
          counterexample-domain generation
          policy/admission-profile revision

    run required verification obligations

    immediately before canonical commit:
        validate D against current state
        UNCHANGED              -> commit
        COMPATIBLE_REFINEMENT  -> issue refreshed candidate/manifest
        INVALIDATING_CHANGE    -> ADMISSION_STALE
        UNKNOWN/MISSING        -> fail closed / rehydrate
```

This is **semantic optimistic concurrency control**, not a global lock. A write to an unrelated region does not invalidate the claim because it is absent from D. A source revocation, new applicable counterexample, authority downgrade or scope change does invalidate it even when source bytes remain identical.

The dependency extractor is itself correctness-bearing. Under-approximating D is unsafe; over-approximation is safe but can cause unnecessary retries. Deterministic source/lifecycle/policy dependencies should be exact. Learned or inferred dependency discovery carries an explicit `CONSERVATIVE`, `BOUNDED` or `UNKNOWN` completeness class instead of pretending completeness.

Admission still separates evidence from claim authority. Semantic OCC adds one guarantee: **the evidence/authority state admitted at commit is materially the state that was verified**, not a stale state that happened to be true before concurrent memory evolution.

# 165. Consolidation algorithm

Consolidation is a two-phase derived-memory operation: **proposal** and **promotion**. v0.6.3 makes the gap explicit because an expensive model/verifier can reason over a proposal while its supporting memory changes underneath it.

At proposal cut K:

```text
propose_consolidation(source_refs):
    hydrate exact source revisions at K
    reject stale/revoked/incompatible sources
    compute independent origin roots
    retrieve applicable contradictions/counterexamples
    derive candidate statement
    compute transformation/preservation contract

    D = source revision/lifecycle generations
        + support/origin bundle
        + authority ceiling
        + applicability/regime
        + counterexample-domain generation
        + transformation/verifier profile
        + protected semantic dimensions

    return immutable proposal P@K,D
```

`P.eligible=true` means “eligible under K and D,” never “promotable forever.”

Immediately before promotion, D is validated against current canonical state. Source **existence** is insufficient. If a source still exists but became stale, was superseded, lost authority, gained an applicable counterexample, or its transformation contract was invalidated, the old proposal is `PROPOSAL_STALE`.

A material change is classified as `UNCHANGED`, `COMPATIBLE_REFINEMENT`, `INVALIDATING_CHANGE` or `UNKNOWN`. Only `UNCHANGED` promotes the original proposal. A compatible refinement creates a **new proposal revision and dependency digest** and re-evaluates affected obligations; the old certificate is never mutated to look current.

This closes the S36 trace: T1 sources justify a principle, T2 one source is invalidated, T3 the old proposal must not become a canonical principle. Slow high-quality consolidation remains possible without holding a global memory lock because promotion validates a small semantic dependency set rather than freezing the entire store.

# 166. Applicability-conditioned procedure-learning algorithm

Procedure learning is based on outcomes within structured applicability slices.

```text
learn_procedure(experiences):
    dedupe by semantic event identity
    group by structural action/lesson candidate
    partition by known applicability dimensions
    keep success and failure evidence separately
    detect slices with contradictory outcomes
    propose narrow procedure for coherent slices
    propose generalization only with evidence/mapping
    attach negative-applicability/counterexample branches
    bind executor/regime capability
```

If Linux succeeds and Windows fails, the default result is not “50% confidence generic procedure.” It is a conditional procedure or unresolved applicability relation. A future successful Windows event can update that slice without rewriting Linux history.

---

Procedure learning groups outcomes only after conditioning on the structural applicability predicate: tool/model capability, environment regime, preconditions, objective/anti-goal constraints and any known exception dimensions. Evidence outside the slice can suggest a hypothesis but does not count as support for the slice. Opposite outcomes across slices create a conditional procedure or explicit unresolved boundary rather than a global average. Promotion records when-not-to-use conditions and counterexamples as first-class dependencies. This is the direct defense against the Nolane World experience-library counterexample where Linux success leaked into Windows support through a shared lesson/tag aggregation.

# 167. Preservation-certificate algorithm

For a transformation `τ : S → R` and protected query-family set `Q_p`:

```text
certify_preservation(τ, S, R, Q_p):
    derive required semantic dimensions/relations per q
    compare source and target structured observables
    run deterministic validators where available
    run diagnostic probes against source vs target
    include known transformation counterexamples
    classify each q:
        EXACT / BOUNDED / UNKNOWN / UNSUPPORTED
    classify missing dimensions:
        preserved / coarsened / lost / unknown
    bind verifier/profile/source revisions
    emit certificate or semantic debt
```

A low-risk transform can use weaker empirical probes. A safety-critical procedure exception may require exact structured comparison. The certificate always names its capability limits.

---

A preservation certificate is computed from a transformation contract, source lineage and bounded probe set; it is never accepted merely because the generator reports low loss. For each protected dimension/query family the verifier produces `EXACT`, `BOUNDED`, `UNKNOWN`, `LOST` or `SOURCE_REHYDRATABLE` together with witness references and verifier capability. Composition applies loss-conservation rules and cannot upgrade unknown/lost fields without source/new evidence. Certificates are invalidated by source deletion, transformation-profile revision, query-family basis expansion or verifier revocation. High-assurance transformations may require an independent/deterministic checker; low-risk representations may remain candidate-only when verification is incomplete.

# 168. Query counterexample algorithm

When a future query or trusted outcome shows disagreement between an accepted compact representation and a stronger source:

```text
register_counterexample(query, region, compact, source):
    normalize query into family/required dimensions
    verify disagreement is material, not rendering variance
    identify source answer/evidence
    identify compact answer / missing distinction
    trace derivation lineage to earliest loss boundary
    create counterexample revision
    invalidate affected envelope entries/caches
    create repair obligation
```

If the stronger source itself is ambiguous, the event becomes ambiguity/debt rather than a false counterexample. The algorithm must not force raw text to be “oracle truth” when raw source interpretation is uncertain.

---

When a later query disproves a representation's claimed answerability, the runtime records the query's semantic family, the decision-relevant distinction that failed, the representation/transform path used, and the stronger source/witness that establishes the mismatch. The counterexample invalidates the specific preservation claim and becomes a permanent regression witness. It does not automatically declare the underlying canonical fact false. If the failure comes from a shared transformation profile, all dependent regions may require revalidation; otherwise the repair stays local. If no stronger source survives, the result is an explicit irrecoverable capability gap rather than an LLM-generated reconstruction.

# 169. Local repair algorithm

```text
repair(counterexample):
    locate target region and transformation lineage
    compute affected query-family closure
    find strongest admissible recoverable ancestor
    if none:
        mark irrecoverable gap + debt
        stop
    rebuild candidate under refined contract
    run full old regression witness set + new counterexample
    if candidate passes:
        admit new representation revision
        supersede capability entries for affected families
    else:
        keep old representation for unaffected families
        leave affected families unknown/rehydratable
```

A failed repair does not require deleting the old representation when it remains useful for unrelated query families.

---

Local repair starts from the falsified certificate/claim and walks typed dependency edges until it reaches the smallest cause set whose revision can explain the failure. It then rehydrates the strongest permitted witness, regenerates only affected representations, re-runs the preservation probes and updates downstream caches. The algorithm refuses to equate graph reachability with invalidation: alternative live justifications and unaffected query dimensions remain valid. A repair whose cause is global—such as a broken normalizer—can legitimately fan out. The locality guarantee is therefore causal, not spatial. Repair receipts record blast radius so repeated global repairs become a measurable architecture smell.

# 170. Region-discovery algorithm

Region discovery executes under one declared Recall Cut rather than repeatedly consulting whatever happens to be “latest.” It remains a candidate sensor, not the owner of truth or of the Recall Obligation.

```text
discover_regions(boundary, obligation, cut K):
    assert principal/query-domain/profile revisions at K

    admissible_domain =
        principal/use-capability filtered
        ∩ authority-domain/incarnation cut
        ∩ allowed forms / tiers / applicability

    seeds =
        exact IDs / entities / hard obligations
        + lexical / dense / temporal / causal candidates
        + action/tool grounding keys
        + prospective/revalidation targets

    query each index at a frontier covering K
        OR overlay a complete canonical delta to K
        OR mark route CUT_UNAVAILABLE

    run bounded association only over admissible candidates
    reserve applicable counterexample/failure channels
    return candidate regions + reasons + frontier receipts
```

For a single authority domain, K can be one sequence/root/incarnation. For multi-domain recall, K is a causally closed vector. Discovery does not use wall-clock “latest” as a substitute.

Principal filtering occurs before hidden influence. v0.6.3 applies the same rule to applicability: a memory labeled `context-scoped` is not safe merely because the label exists. Declared domain/host/model/mission/task dimensions are compared with the **actual requested profile**. Missing dimensions are not implicit wildcards; compatibility or `*` must be explicit.

Optional candidate ordering can remain approximate. Hard-route feasibility and strong absence/currentness cannot. If no route can serve K, recall becomes partial/unknown rather than silently mixing revisions.

# 171. Representation-resolution algorithm

For candidate region `g` and role `h`:

```text
resolve(g,h,cut,consumer):
    enumerate accessible representations in fiber R_g
    reject stale/inapplicable representations
    inspect preservation envelope for family(h)
    inspect source recoverability / scope
    inspect effect profile for consumer/rendering
    construct feasible options:
        direct compact
        direct structured field
        source hydration
        alternative witness
    return Pareto options over token/latency/effect
```

The resolver can return `UNKNOWN` when the capability atlas lacks sufficient evidence. It does not ask the model to guess whether a summary is “probably enough.”

---

Representation resolution is a constrained choice over the fiber of each relevant semantic region. The resolver knows the obligation's required observable dimensions and assurance level, each representation's preservation envelope, recoverability and estimated token/latency/interference cost. It chooses a Pareto-efficient adequate representation rather than the globally “best” summary. If no resident representation covers the obligation but a source is rehydratable, it emits a semantic page fault. If the only exact source is inaccessible or deleted, it marks the role unresolved. This stage is the heart of context virtualization because it decouples *what history matters* from *how much of that history must be materialized*.

# 172. Recall-frame cover algorithm

Frame compilation is a proof-carrying hard-cover problem over a pinned cut. v0.6.3 distinguishes the **compile-time frame lease** from the later **use-time grounding fence**.

```text
compile_frame(boundary, H, O, B, cut K):
    repeat:
        ensure every hard role has a feasible route at K
        discover/resolve representations at K

        for each semantic page fault:
            hydrate the exact revision visible at K
            if only newer state is available:
                upgrade/recompile the whole cut
                OR return CUT_UNAVAILABLE

            extract newly exposed hard dependencies
            add canonicalized roles to H

    until H reaches fixed point or budget overflows

    solve bounded hard cover
    apply activation/security guards
    recompute coverage after every removal/rewrite
    add optional evidence with remaining budget

    construct candidate payload
    run whole-payload information-flow gate

    emit:
        RecallFrameDescriptor
        RecallFrameDependencyManifestRevision D
        RecallSufficiencyAssessment
        FrameInformationFlowReceipt
```

D records material semantic generations whose continued compatibility makes the frame sufficient: source/claim lifecycle, hard-role closure, applicable counterexample set, access/declassification policy, preservation/recoverability, regime/self-version, tool schema/capability when known, and query-domain/frontier state for strong absence.

The frame can be used for reasoning. It is not a permanent authorization for a future consequence. If the model later chooses concrete tool arguments or a stricter sink, the host validates D against current state, checks the final payload/arguments and, where required, issues a short-lived `MemoryUseFence`.

Unrelated memory changes remain outside D and do not invalidate the frame. The target is precise staleness, not maximum invalidation.

# 173. Strong negative-query algorithm

```text
negative_query(predicate, domain, cut):
    require query procedure supports predicate semantics
    pin accessible domain/snapshot
    search all declared tiers/pages needed by completeness contract
    verify pagination/stream watermark
    verify index + canonical delta covers required frontier
    if match:
        return SUPPORT_FOR_EXISTENCE
    if complete and no match:
        return NO_MATCH_COMPLETE_DOMAIN
    if partial:
        return NO_MATCH_PARTIAL_DOMAIN
    if opaque/error:
        return OPAQUE/INCOMPLETE
```

The returned receipt becomes a dependency of any frame that relies on the absence claim.

---

A strong negative query first defines the predicate and principal-relative query domain, pins a Recall Cut, and checks that the active procedure can actually search the required storage tiers/indices with adequate completeness semantics. Pagination, stream watermarks and index visibility frontiers are part of the result. If no match is found under a complete bounded domain, the runtime may emit `NO_MATCH_COMPLETE_DOMAIN`; otherwise it emits partial/opaque/unsupported status. Negative-query caches depend on domain generations/predicate semantics so a new matching memory can invalidate an old empty result even though no returned object changed.

# 174. Effect-evidence update algorithm

```text
observe_memory_effect(exposure, outcome):
    record what was candidate-retrieved, selected, rendered and referenced
    bind consumer/task/regime/rendering
    classify evidence tier:
        observational / matched / shadow / paired / strong intervention
    update scoped effect evidence
    derive current effect profile under calibration policy
    never change factual authority from effect alone
```

When multiple memories were rendered, item-level causal attribution remains uncertain unless interventions separate them. A set-level effect can still be useful without pretending to know which item caused it.

---

Effect updates are deliberately conservative. An exposure event records which memory/set was retrieved, rendered and actually available to the model; downstream traces record whether the model referenced it, which action followed and what outcome was observed. Observational associations update only weak effect evidence. Stronger causal tiers require matched or randomized/shadow comparisons and remain scoped to consumer/task/regime/rendering. The ledger can recommend inhibition, alternate rendering or exploration, but those policies are downstream of hard Recall Obligations. It does not mutate canonical factual confidence or generalize harm to untested consumers automatically.

# 175. Interference-guard algorithm

```text
apply_effect_guard(options, obligation):
    for optional option:
        inhibit/quarantine if scoped effect/security evidence warrants
    for hard-role option:
        prefer alternative witness or safer rendering
        if no safe representation covers role:
            keep role unresolved
            return escalation/insufficiency
```

The guard cannot transform “harmful context” into “memory does not matter.”

---

The interference guard runs after hard-role identification and before final rendering. It can down-rank optional memories with sufficiently strong scoped negative-effect evidence, detect associative hubs/popularity loops, prefer a smaller structured rendering, or request alternative evidence. For hard-role material it has no authority to erase the role: if every safe representation is blocked, the frame becomes insufficient/overflowed and the consumer must escalate. Guard decisions are themselves versioned by model/task/regime/rendering profile so a model upgrade does not inherit stale inhibition. This keeps memory optimization corrigible rather than turning a learned harm score into hidden censorship of truth.

# 176. Witness-cover retention algorithm

```text
consider_delete(rep_or_source, policy):
    compute protected obligations for affected regions
    compute live witness/recovery paths without target
    compute justification and disclosure consequences
    if all protected obligations remain covered:
        allow semantic-safe deletion candidate
    elif policy explicitly authorizes irreversible loss:
        commit deletion + gap/debt/reclassification
    else:
        block or archive instead
```

For large stores the exact cover optimization can be approximated. A conservative false negative (“keep too much”) is a cost problem. A false positive (“safe to delete” when the last witness disappears) is a semantic problem.

---

Retention begins from protected witness obligations rather than age alone. For each semantic region the runtime derives which source/representation objects jointly cover protected dimensions, historical audit requirements, active procedure evidence and unresolved preservation debt. Candidate deletions are evaluated against this witness cover plus explicit privacy/retention authority. Redundant witnesses may be archived or removed; deleting the last witness is legal only when policy authorizes the resulting gap, which is then recorded and invalidates affected preservation envelopes. Approximate set-cover heuristics can choose economical witnesses, but the post-delete checker must verify the declared protected basis still exists.

# 177. Recovery/boot algorithm

```text
boot(principal, continuity_pin):
    verify pin origin and authority
    pin current mission/policy/access state
    compare environment/tool/model/schema digests
    compile continuity Recall Obligation
    retrieve protected constraints/objective/evidence blockers
    revalidate stale procedures/self-version assumptions
    hydrate unresolved failure/hypothesis evidence as needed
    return bounded boot frame + recheck obligations
```

The boot process never marks old planned actions current merely because they were stored in the pin.

---

Boot reconstructs continuity from a small pin plus canonical receipts, not from a trusted narrative summary. It loads the protected objective/constraint revision, unresolved hypotheses/failures, latest compatible memory cut and relevant self-version/tool/environment profiles. Before reusing tactics or procedures it probes current reality for drift. Historical judgements remain available to explain past actions, while current truth is recomputed under present evidence. If required sources are unavailable or a procedure's capability profile no longer matches the current executor, recovery surfaces debt and rebuilds the frontier instead of blindly resuming the old next action.

# 178. Maintenance fixed-point algorithm

```text
maintenance_epoch(region):
    if no new evidence/counterexample/debt trigger/policy change:
        if existing normalized representation satisfies current contracts:
            no semantic rewrite
            return FIXED_POINT
    otherwise:
        run targeted consolidation/rebase/repair
        compare normalized semantics
        commit only material verified changes
```

This makes “no-op maintenance” a successful outcome.

---

A maintenance pass computes candidate transformations only for regions with explicit pressure: new evidence, recurrence, surprise, counterexample, excessive derivation depth, retention pressure, invalidation or effect/interference debt. After applying admitted changes it recomputes the normalized semantic state. If the same evidence/policy/regime produces no material semantic change and no new debt is discharged, that region is at a fixed point and should not be rewritten again. Stochastic generators may propose alternate surface forms, but material semantic alternatives require verification/selection and are not silently sampled into canon. Repeated rewrite activity on a fixed-point region is a measurable maintenance defect.

# PART XVII — REFERENCE DATA MODEL AND OWNERSHIP

# 179. Minimal canonical record families

v0.6 deliberately reduces the authoritative object set. The canonical plane needs roughly the following families; implementations can combine tables/documents as long as ownership remains clear.

| Family | Owns | Must not own |
|---|---|---|
| `EvidenceEventRevision` | source/event identity, time, origin, artifact refs | derived truth |
| `ClaimRevision` | proposition identity, valid interval, epistemic state | retrieval popularity |
| `HistoricalJudgementRevision` | what was judged at a past cut | current truth rewrite |
| `JustificationRevision` | OR-of-AND support semantics | retrieval rank |
| `Authority/AccessPolicyRevision` | subject/operation integrity and disclosure | factual content |
| `MemoryCommitReceipt` | exactly-once canonical transition evidence | index visibility |
| `RetentionEventRevision` | archive/delete/accessibility and authorized erasure barrier transition | falsehood |
| `MemoryRegimeRevision` | world/tool/schema applicability environment | consumer/model identity |
| `SelfVersionProfileRevision` | consumer/model/tool-runtime capability identity used for compatibility | world truth or memory content |

This is intentionally smaller than the combined v0.1–v0.5 list of named records.

---

The canonical plane owns only state that would be dangerous to reconstruct from derived prose: evidence events/origins, claims and historical judgements, OR-of-AND justifications, temporal validity/knowledge availability, principal/integrity/confidentiality policy references, authority-domain commit receipts and source/artifact identities. Counterexample relations that affect claim/procedure authority also root here through evidence and typed edges. Most “memory types” do not. This minimality matters for migration: canonical truth should evolve slowly and audibly, while representation algorithms can be replaced without converting their old summaries into permanent schema baggage.

# 180. Minimal representation-plane record families

| Family | Purpose |
|---|---|
| `MemoryRegionRevision` | semantic repair/locality identity |
| `RepresentationRevision` | one compiled/raw/structured form in a region fiber |
| `TransformationRevision` | source→target derivation and profile |
| `PreservationCertificateRevision` | bounded query-family capability / loss evidence |
| `MemoryQueryCounterexampleRevision` | future-query falsifier of representation capability |
| `SemanticDebtRevision` | unresolved preservation/recoverability/verification gap |
| `ProcedureApplicabilityRevision` | structured conditions for procedure role |
| `CounterexampleRelationRevision` | scoped negative relation to target claim/procedure |

Several older record types become roles or specializations of these families instead of independent truth universes.

---

The representation plane requires surprisingly few canonical record families because “episodic,” “semantic,” “procedural,” “failure” and “anchor” are roles over representations, not independent truth stores. Core objects are `SemanticRegionRevision`, `RepresentationRevision`, `TransformationContractRevision`, `PreservationEnvelopeRevision`, `SemanticLossVectorRevision`, `RecoverabilityCertificateRevision`, `MemorySemanticDebtRevision` and query-counterexample/regression-witness records. A representation points back to canonical claim/evidence/justification state and forward to descendants; it owns format, granularity, role tags and preservation capability—not truth authority. This keeps migration manageable and allows one region to expose multiple optimized views without duplicating epistemic state.

# 181. Minimal projection-plane families

Projection objects are disposable/rebuildable:

```text
RecallObligation
RecallCut
RegionDiscoveryResult
RepresentationResolutionPlan
RecallSufficiencyAssessment
RecallFrameDescriptor
RecallFrameDependencyManifest
MemoryCapabilityAtlas
MemoryEffectProfile
activation/index/cache state
```

If losing one of these changes what the runtime believes historically, the implementation has accidentally moved authority into the projection plane.

---

The projection plane is even thinner because projections are disposable. It needs `RecallObligation`, `RecallCutRevision`, discovered-region candidates, `RepresentationResolution`, `RecallReconstruction`, `RecallSufficiencyAssessment`, `RecallFrameDependencyManifestRevision` and `RecallFrameDescriptor`. Optional diagnostic records can capture page faults and compiler decisions, but no projection becomes durable truth merely because a model saw it. The projection plane therefore behaves like a compiler interface: canonical/representation state is input; a bounded task-specific memory program is output. Recompiling under a new task, principal or evidence cut is expected and safe.

Projection records are intentionally ephemeral but still structured enough for audit. `RecallObligation` states hard/optional roles and required observables; `RecallCutRevision` pins a coherent evidence/access/regime/procedure world; discovery and resolution records explain which regions/representations were considered; reconstruction records alternatives/inferred bridges; sufficiency and dependency manifests explain coverage/freshness; the final frame holds compact content/handles. Because these objects are not truth owners, caches can be invalidated aggressively and consumer-specific views can differ. A debugging tool can persist them as audit receipts without granting them future-memory authority.

# 182. Memory roles are tags/contracts on representations

A `RepresentationRevision` can expose roles such as:

```text
EPISODIC
SEMANTIC
PROCEDURAL
FAILURE
COUNTEREXAMPLE
PROSPECTIVE
ANCHOR
INSTITUTIONAL
```

The role changes required fields and transformation/admission policy. It does not create an independent canonical store.

A single region can legitimately have several representations/roles. For example, a failed deployment episode can source a semantic fact (“version 3.2 is incompatible”), a failure representation (symptom/context), a procedure counterexample and a continuity warning. All remain traceable to the same evidence.

---

Role tags determine additional contracts. A representation tagged `procedure` must expose applicability, preconditions, stop/failure/when-not-to-use information; `failure` carries negative procedural evidence and reproduction conditions; `anchor` promises high retrieval leverage and boot linkage; `episode` preserves event/action/outcome structure; `semantic` exposes justified claim content. Multiple role tags can coexist on one representation, but none create a second canonical claim. This design avoids ontology explosion while still allowing role-specific validators and retrieval reserves. If a future role requires genuinely new correctness-bearing state, the counterexample must demonstrate why it cannot live as a contract over the existing substrate before a new canonical primitive is admitted.

# 183. IDs and incarnation rules

Logical identity, revision identity and runtime incarnation are distinct. v0.6.1 makes this distinction normative because the Nolane World seam audit reproduced several cases in which reusing the same ID rewrote content or reset lifecycle state.

Every durable correctness-bearing object has, directly or through an enclosing canonical header:

```text
logical_id
revision_id
predecessor_revision_ref?   # for semantic mutation
created_commit_ref
semantic/content digest appropriate to the object
incarnation/epoch where ABA/recreate risk exists
```

The core transition law is:

```text
CREATE(same logical_id, same creation semantics)
    -> idempotent existing object
    -> MUST NOT reset verified/resolved/revoked lifecycle state

CREATE(same logical_id, materially different semantics)
    -> IDENTITY_COLLISION
    -> no last-write-wins mutation

REVISE(logical_id, expected predecessor, new semantics)
    -> new revision if predecessor/current policy matches

SUPERSEDE/REVOKE
    -> typed lifecycle transition with preserved history

RESURRECT/REACTIVATE
    -> never implied by CREATE
    -> requires the object's current reactivation predicate / live justification
```

A content digest is not universal semantic identity. Two independent observations may contain identical bytes; one upstream event may be delivered through several wrappers; the same claim text under different valid-time, principal, entity or regime semantics can be different claim revisions. Conversely, rendering the same event differently does not create new evidence.

Delete/recreate and restore/fork add an **incarnation** dimension so old freshness, idempotency, writer or access receipts cannot attach to a new object merely because its human-readable ID matches. Migration preserves explicit identity mappings rather than regenerating IDs from normalized text.

This law applies uniformly to evidence, claims, debts, counterexamples, region handles, source identities and policy objects. The type-specific transition can differ; the prohibition on same-ID semantic overwrite and implicit lifecycle reset does not.

# 184. Schema ownership and migration discipline

Correctness-derived fields are written only by their owner kernel. Producer DTOs and persisted canonical schemas should make this ownership visible so that a caller cannot accidentally send `verified=true` or `independent_sources=5` as if they were facts.

Migration code has explicit rules for unknown legacy fields. Missing old provenance can become `UNKNOWN_DEPENDENCE`; it should not be upgraded to independence because the new schema requires a Boolean.

---

Schema ownership follows semantic ownership. The canonical kernel owns fields whose meaning affects evidence, authority, time, scope, justifications and commit identity; the representation kernel owns transformation/preservation/recoverability fields; the projection compiler owns task-local obligation and frame fields. A migration cannot casually move one ownership surface into another. For each correctness-bearing field it declares `PRESERVE`, `MAP_WITH_PROOF`, `RECOMPUTE`, `REVALIDATE`, `DOWNGRADE`, `QUARANTINE`, `DELETE_BY_POLICY` or `FAIL`. Unknown legacy lineage is migrated as unknown dependence, not invented independence. Differential fixtures compare normalized semantics before and after migration, not only JSON parse success.

# 185. Typed error families

Reference semantic errors include:

```text
MemoryWriteConflict
MemoryUnknownWriteOutcome
MemoryOriginOpaque
MemoryAdmissionRejected
MemoryTransitionIncomplete
MemoryScopeBlocked
MemoryQueryIncomplete
MemoryQueryCapabilityUnsupported
MemoryRecallAmbiguous
MemoryRecallInsufficient
MemoryViewOverflow
MemoryRecoverabilityLost
MemoryIntegrityError
MemoryStaleWriter
MemoryIndexFrontierIncomplete
MemoryIrrecoverableGap
```

Vendor/database exceptions are mapped into these only when the runtime has enough information. A timeout does not become `MemoryNotFound` by convenience.

---

Typed errors are grouped by which contract failed: canonical write/conflict/reconciliation, origin/admission/trust, temporal/history, preservation/recoverability, query completeness/capability, frame feasibility, scope/privacy, interference/effect and recovery/migration. Vendor exceptions are retained as diagnostics but never directly interpreted as semantic outcomes. A connector timeout is `QUERY_INCOMPLETE`, not absence; a missing key is `SOURCE_UNAVAILABLE`, not false; an index lag is `STALE_REVALIDATION_REQUIRED`, not “no memory.” The error algebra matters because recovery policies must be safe and composable across implementations. Hidden string parsing would recreate exactly the semantic ambiguity the spec is trying to remove.

The kernel error taxonomy separates errors by recovery semantics rather than by component. Write conflicts and unknown outcomes reconcile by operation identity; admission/trust failures require new authority/evidence; preservation/recoverability gaps require source rebase or honest insufficiency; query incompleteness requires a stronger capability/domain; scope blocking requires authorization changes; interference blocking may require alternate rendering; migration/replay errors require profile compatibility or downgrade. This structure lets adapters map vendor failures to stable meanings while preventing exception-string logic from leaking into memory correctness. Unknown mappings fail closed for hard obligations.

# 186. Audit records versus model context

The runtime stores more correctness metadata than it renders. Commit receipts, source lineages, transformation certificates, query-domain completeness and effect evidence can be large over the lifetime of an agent. The model normally sees only compact consequences and handles.

This asymmetry is intentional. Context efficiency is achieved by **externalizing correctness state**, not by deleting it from the system.

---

Durable audit state stores compact typed receipts and content-addressed handles, not entire prompts or private reasoning. A commit can be explained through operation/base/origin/admission/justification receipts; a Recall Frame through obligation/cut/representation/dependency manifests; a repair through the counterexample, affected transform and new preservation certificate. The model ordinarily sees only the small subset required to make its current decision plus human-readable summaries generated from these typed records. This architecture simultaneously improves explainability and context locality: detailed provenance remains queryable without forcing every downstream model call to carry it. Sensitive raw evidence stays behind principal and retention controls.

# 187. Deterministic normalization profiles

Semantic replay sometimes requires comparing results whose incidental serialization differs. Normalization profiles declare whether a result is set-like or ordered, tie-breaking, numeric precision, timestamp boundaries, Unicode normalization, entity identity and duplicate semantics.

If ordering can change the model's decision because items are rendered sequentially, ordering becomes material. If it is declared irrelevant and consumers treat it as a set, replay compares normalized sets.

Normalization revisions are correctness dependencies for certificates that rely on them.

---

Normalization determines whether two outcomes are semantically the same for replay, cache and fixed-point purposes. Profiles therefore specify canonical ordering for unordered sets, Unicode/text normalization where relevant, interval endpoint conventions, numeric precision, entity identity references, duplicate semantics and material ordering. A change in normalization can alter cache keys, semantic hashes and maintenance-equilibrium judgements, so the profile is revisioned and bound into certificates. Normalization is intentionally narrower than “make text similar”: it only erases differences declared irrelevant for a particular object/property. Protected negation, temporal boundary and scope information can never disappear through a generic text canonicalizer.

# 188. Compatibility is property-specific

A new embedding model may be compatible for exact-ID history replay and incompatible for semantic ranking. A new procedure executor may preserve factual memory and invalidate procedure applicability. A new query-family basis may preserve broad-state capability and require revalidation for exact exceptions.

The runtime therefore records compatibility per property rather than one global “memory version compatible” flag. This keeps migration and self-version reasoning honest.


---

Two representation or procedure versions may be compatible for one property and incompatible for another. An embedding-model change can leave exact-ID retrieval unchanged while invalidating ranked semantic equivalence; a schema change can preserve claim identity while losing old query-family preservation metadata; a stronger verifier may refine `INCONCLUSIVE` results without contradicting already-proved outcomes. Compatibility is therefore a partial/product relation keyed by property, scope and profile. Cache reuse, migration and certificate transport must ask the exact compatibility question instead of relying on one `version >= old_version` or global “backward compatible” flag.

# PART XVIII — CURATED FAILURE ATLAS

The v0.1–v0.5 research notebooks intentionally accumulated hundreds of failure IDs. v0.6 does not copy that catalogue wholesale. The following atlas keeps failures that expose distinct semantic mechanisms and maps them back to the consolidated architecture. It is a test-design index, not a feature checklist.

# 189. Capture, identity and canonical-write failures

| ID | Failure mechanism | Why it is dangerous | Required semantic defense |
|---|---|---|---|
| CW01 | two writers derive next commit from same stale head | lost update / broken canonical order | authority-domain serialization + expected-base CAS |
| CW02 | old writer commits after failover | split brain | writer epoch/fencing token inside commit boundary |
| CW03 | commit succeeds but response is lost; caller retries new op | duplicate semantic transition | operation reconciliation + durable receipt |
| CW04 | same idempotency key reused with different request | ambiguous replay | request digest binding + conflict |
| CW05 | same source event delivered twice | fake experience/support multiplication | stable semantic event identity |
| CW06 | identical content from two real events collapsed | independent observations lost | event identity distinct from content hash |
| CW07 | connector lacks stable event ID but system claims exact dedupe | hidden uncertainty | heuristic/unknown identity capability |
| CW08 | tool transport success stored as verified side effect | false world state | transport receipt separated from observed/verified outcome |
| CW09 | late result attached to wrong action | causal memory corruption | correlation/action IDs + event/knowledge time |
| CW10 | raw artifact discarded before required extraction verified | irrecoverable evidence loss | policy-aware source retention/recoverability |
| CW11 | producer writes runtime-derived `canonical/confidence` fields | authority bypass | one admission owner |
| CW12 | append log is hash-chained but concurrent sequence allocation is unsafe | tamper evidence mistaken for linearizability | serialized correctness writer |

# 190. Provenance, authority and justification failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| PA01 | same source copied through many summaries | manufactured corroboration | origin/common-mode grouping |
| PA02 | trusted tool echoes untrusted content | authority laundering | transport authority ≠ content authority |
| PA03 | agent self-summary becomes new trusted source | self-authentication | origin ceiling propagation |
| PA04 | different lineage strings assumed independent | false promotion | evidence-independence assessment |
| PA05 | support API called repeatedly | confidence inflation | assurance derived from normalized support state |
| PA06 | A supports B and B supports A | authority from cycle | grounded support fixed point |
| PA07 | one premise revoked and whole claim dies despite alternate proof | over-invalidation | OR-of-AND justifications |
| PA08 | one premise revoked but conjunctive proof treated as still complete | under-invalidation | explicit support sets |
| PA09 | derivation procedure is wrong but sources are true | false abstraction | derivation capability part of assurance |
| PA10 | trusted user assertion applied outside subject scope | overbroad authority | subject/claim-kind authority profile |
| PA11 | source authority expires/revokes but descendants remain high-authority | stale trust | reverse dependency/revalidation |
| PA12 | access/disclosure authority treated as factual trust | truth/privacy laundering | integrity and confidentiality orthogonal |

# 191. Temporal and historical-knowledge failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| TM01 | dialogue/ingestion order used as occurrence time | false chronology | semantic event time |
| TM02 | late evidence available in historical replay before ingestion | hindsight leakage | `KNOWN_BY(t)` |
| TM03 | current truth overwrites past judgement | audit/history laundering | `HistoricalJudgementRevision` |
| TM04 | point observations assumed continuous state | invented duration | durative coverage semantics |
| TM05 | interval endpoint inclusive/exclusive default differs | boundary errors | canonical interval semantics |
| TM06 | late historical correction overwrites current state by arrival order | temporal corruption | valid-time intervals separate from commit time |
| TM07 | current access policy used to reconstruct what historical principal knew | false historical knowledge | historical cut/access semantics |
| TM08 | derived rule created later appears in earlier decision context | future-derived leakage | `available_from`/knowledge time |
| TM09 | mixed clock domains forced into total order | false causality | partial order / clock uncertainty |
| TM10 | old regime memory wins because newer arrival is missing | stale applicability | regime revision + current projection |
| TM11 | historical wrong belief deleted after correction | inability to explain past action | immutable judgement + retrospective status |
| TM12 | durative summary claims exact boundary it never observed | false precision | query-family preservation contract |

# 192. Representation and consolidation failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| RP01 | scalar fidelity hides lost negation/exception | high score, wrong decision | semantic-loss vector + protected dimensions |
| RP02 | caller self-reports abstraction loss | self-certified compression | transition verification/probes |
| RP03 | summary-of-summary regenerates lost field | fabricated memory recovery | loss absorption + source rebase distinction |
| RP04 | different regimes consolidated due text similarity | broad false rule | applicability/regime gating |
| RP05 | one success becomes general procedure | anecdotal overfit | candidate status + scoped evidence |
| RP06 | recurring duplicate event appears frequent | fake recurrence trigger | event identity dedupe |
| RP07 | one-shot catastrophic event ignored by recurrence-only consolidation | lost guard | surprise/impact protected trigger |
| RP08 | near-duplicate dedupe runs before contradiction | correction dropped | semantic difference first, dedupe second |
| RP09 | consolidation drops active counterexample | unsafe abstraction | protected counterexample obligation |
| RP10 | segment granularity merges decision-distinct events | causal/order loss | granularity in transform contract + query counterexample split |
| RP11 | maintenance repeatedly rewrites stable summary | telephone-game drift | semantic fixed point |
| RP12 | stochastic consolidator materially changes meaning without journaled choice | hidden drift | alternatives + explicit verifier/selection |

# 193. Answerability, preservation and future-query failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| AN01 | relevant summary assumed exact for every query | answer from missing field | query-family answerability |
| AN02 | unseen query family inherits “safe” from known family | universalization | new family starts UNKNOWN unless refinement proven |
| AN03 | query family defined by wording/embedding cluster | semantic mismatch | typed observable requirements |
| AN04 | one lost field recovers in descendant prose with no source | false memory | loss absorption |
| AN05 | source deleted but recoverability metadata says rehydratable | impossible page fault | retention dependency invalidation |
| AN06 | capability atlas stale after source deletion | false exactness | atlas rebuild/freshness dependencies |
| AN07 | query counterexample repairs whole project | excessive churn | region-local repair |
| AN08 | counterexample repair pins literal queries indefinitely | overfit/bloat | refine semantic family/dimension, regression witnesses |
| AN09 | transform certificate from same generator accepted blindly | self-verification | assurance-dependent independent/deterministic checks |
| AN10 | query family basis expands but old cert remains exact | stale preservation | basis revision dependency |
| AN11 | protected raw witness deleted by LRU | future irrecoverable hole | witness-cover retention |
| AN12 | privacy deletion forbidden by witness-cover preference | policy inversion | authorized deletion allowed + explicit debt/gap |

# 194. Recall, reconstruction and context failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| RC01 | fixed top-k omits rare hard constraint | confident wrong frame | Recall Obligation hard roles |
| RC02 | more hard roles than budget silently truncated | hidden incompleteness | overflow/insufficiency |
| RC03 | approximate ANN miss used as global absence | false negative truth | capability-bounded negative query |
| RC04 | first page empty, later page contains match | false absence | snapshot-consistent completeness receipt |
| RC05 | new matching record invalidates empty cache but no returned ID changed | phantom | query-domain dependency/generation |
| RC06 | private memory filtered only after ranking | hidden influence | prefilter before all retrieval/activation |
| RC07 | relevant region found but wrong coarse representation rendered | missing exact observable | representation resolution stage |
| RC08 | active reconstruction fills missing bridge as fact | narrative hallucination | inferred bridge typed + source handles |
| RC09 | two histories collapsed to top-1 | ambiguity hidden | competing reconstruction / `AMBIGUOUS_RECALL` |
| RC10 | staged hydration crosses to incompatible memory cut | torn context | cut-bound hydration/revalidation |
| RC11 | stale index returns revoked fact and overlay only adds new facts | obsolete memory survives | positive + negative canonical delta |
| RC12 | one frame reused after task/decision changes | missing later obligation | decision-bound recall recompilation |

# 195. Interference and effect failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| EF01 | retrieved before failure => labeled causal | false harm model | effect-evidence tiers |
| EF02 | harm transfers from model A to B | wrong inhibition | consumer-scoped profiles |
| EF03 | harm transfers across task/regime/rendering | wrong inhibition | task/regime/rendering keys |
| EF04 | multi-memory failure blamed on each item equally | attribution error | set-level evidence / interventions |
| EF05 | correct hard constraint inhibited because it hurts weak model | safety omission | hard-role conservation + alternate rendering |
| EF06 | stale fact automatically labeled harmful for all tasks | truth/effect conflation | separate planes |
| EF07 | random extra context is harmful but system blames semantic content | wrong repair | no-memory/random/rendering controls |
| EF08 | positive retrieval feedback makes popular memory dominate | lock-in | decay/exploration/inhibition |
| EF09 | effect profile persists after model upgrade | stale optimization | self-version dependency |
| EF10 | optional memory always injected despite no benefit | context bloat/interference | proactive/conditional injection |
| EF11 | low-sample observational ledger quarantines memory strongly | overreaction | evidence-tier thresholds |
| EF12 | no observed harm interpreted globally harmless | unknown→safe | scoped uncertainty |

# 196. Security, privacy and shared-memory failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| SC01 | poisoned instruction stored as procedure | delayed action compromise | origin/admission firewall |
| SC02 | private source summarized into public memory | information leak | confidentiality closure + declassification receipt |
| SC03 | declassification widens scope and implicitly raises truth authority | category error | disclosure separate from integrity |
| SC04 | scope enforced in search but GET/hydrate bypasses | direct leak | one access kernel across read paths |
| SC05 | private memory changes public ranking then is redacted | inference leak | principal prefilter before hidden influence |
| SC06 | imported shared memory becomes destination truth automatically | cross-domain laundering | governed import/admission |
| SC07 | multiple agents echo one poisoned origin | Sybil corroboration | origin/common-mode dependence |
| SC08 | declassification revoked but derivative stays public | persistent leak | release receipt as dependency |
| SC09 | user cancellation does not revoke prospective trigger | stale future action cue | trigger lifecycle/owner validity |
| SC10 | hard deletion leaves derived representation leaking deleted source | privacy leak | information-flow deletion propagation |
| SC11 | debug endpoint ignores memory ACL | operational backdoor | access kernel for all influence/exposure paths |
| SC12 | current memory used to infer sensitive personality trait outside operational scope | profiling expansion | subject/scope admission policy |

# 197. Lifelong maintenance, recovery and migration failures

| ID | Failure mechanism | Consequence | Defense |
|---|---|---|---|
| LF01 | stable region re-summarized indefinitely | semantic drift/compute waste | fixed-point maintenance |
| LF02 | source-rebase never occurs despite deep lossy lineage | accumulated uncertainty | depth/debt/rebase triggers |
| LF03 | repair counterexamples discarded after success | regression recurrence | permanent witness suite |
| LF04 | schema migration maps unknown dependence to independent | authority inflation | explicit downgrade/unknown mapping |
| LF05 | index cache becomes only surviving source | derived state owns truth | canonical/representation persistence |
| LF06 | restore reuses old active incarnation | ABA/freshness bugs | new incarnation/fence |
| LF07 | boot resumes old tactic after environment drift | stale action | current-world revalidation |
| LF08 | past-self intent becomes current authority | self-command loop | historical intent typed |
| LF09 | archive counted unavailable/false | status collapse | product-state dimensions |
| LF10 | deletion removes sole witness but debt record also “cleaned up” | silent capability loss | debt conservation |
| LF11 | maintenance budget starvation skips required verification | assurance under load | budget isolation/incomplete state |
| LF12 | longitudinal risk evaluated at one snapshot | accumulation failure unseen | memory-prefix probe protocol |

The curated atlas is intentionally smaller than prior notebooks. A new failure ID is added only when it exposes a distinct semantic mechanism that cannot be represented by an existing row.

---

# PART XIX — SEMANTIC KERNEL CLOSURE: WHAT THE RUNTIME MUST MEAN BEFORE IT CAN BE FAST

# 198. The kernel closure theorem: one authoritative past, many lossy views

The central closure claim of v0.6 is not that every memory operation is lossless. A useful memory runtime must be able to summarize, generalize, archive, forget, rank and inhibit. The stronger claim is about **where irreversible meaning is allowed to enter**.

Let the canonical state of one Memory Authority Domain at commit `k` be:

\[
K_k = (E_k, C_k, J_k, T_k, A_k, P_k)
\]

where `E` is evidence-event history, `C` is claim/historical-judgement state, `J` is live justification structure, `T` is temporal/knowledge-time state, `A` is authority/access/confidentiality policy state, and `P` is provenance/source identity. Let a derived representation `R_i` be produced from a bounded source set `S_i \subseteq K` through transformation contract `\tau_i`.

v0.6 requires:

```text
canonical meaning
    -> may generate many representations

representation
    -> may propose new claims/procedures
    -> may never silently rewrite canonical meaning
```

A summary, episode, procedure, failure lesson or anchor can be wrong without immediately corrupting the canonical past, because it is a revisioned representation with source lineage and a preservation contract. If later recall falsifies the representation, the runtime can repair or retire it while retaining the underlying evidence. This is the architectural reason v0.6 collapses the older “many memory stores” idea into one canonical substrate plus many representation fibers.

The theorem is conditional: if policy hard-deletes the last source witness, future exact reconstruction can become impossible. The kernel does not prevent authorized information destruction; it prevents the runtime from **continuing to claim the destroyed capability exists**. Likewise, if source extraction was wrong and no raw witness survives, canonical evidence itself may be incomplete. Canonical does not mean omniscient. It means “the only layer allowed to own current epistemic authority under the declared evidence.”

A conforming implementation may change databases, graph libraries, embedding models, compression policies and renderers while preserving this ownership relation. If replacing a summary engine can accidentally rewrite historical truth, the implementation has violated the theorem even if all unit tests for summary quality pass.

# 199. Semantic ownership matrix: every correctness property has exactly one owner

Many memory architectures become inconsistent because several modules cache and mutate the same conceptual property: a vector store thinks a fact is current, a temporal graph marks it superseded, a procedure library still treats it active, and a summary cache still tells the model the old value. v0.6 avoids this by assigning each correctness property one canonical owner and treating every other occurrence as a projection.

| Property | Canonical owner | Derived consumers | Forbidden alternate owner |
|---|---|---|---|
| evidence-event identity | canonical evidence ledger | dedupe, recurrence, provenance | row count / chunk ID |
| claim epistemic state | claim + justification kernel | semantic view, procedure support, recall | summary text / vector score |
| historical judgement | judgement ledger | audit, recovery | rewritten current summary |
| valid/known time | temporal claim state | temporal index, episode view | ingestion order alone |
| origin/authority ceiling | origin/admission kernel | consolidation, sharing | trusted-tool label on derived text |
| principal access/confidentiality | access policy revisions | every read/activation path | per-index ad hoc filters |
| representation preservation | preservation envelope | resolver, cache, forgetting | LLM self-rated fidelity |
| recoverability | witness/source dependency state | page-fault resolver, retention | “source_ref exists” string |
| applicability | procedure/representation contract | procedure selection, effect profile | tag union |
| recall sufficiency | projection compiler | consumer runtime | retrieval top-k success |
| memory effect | causal effect ledger | interference policy | factual confidence |

The matrix makes bugs easier to reason about. A subsystem is allowed to cache an owned property for speed only when the cache records the owner's revision and can be invalidated. A procedure view may store the current claim status for display, but it cannot mutate that status. An ANN index may store access-filtered shards, but access policy remains authoritative and is rechecked on exact hydration.

The strongest anti-fragmentation rule is:

> **No correctness-relevant field may have two independently writable clocks.**

This mirrors a lesson from sophisticated plan/runtime design: duplicated authority is more dangerous than duplicated data. Data can be replicated. Authority must remain single-source or governed by an explicit reconciliation protocol.

The ownership matrix also gives migration a clear target. Legacy memory modules are not all rewritten immediately; each is classified as canonical source, derived view, migration source or deprecated authority. During migration, the dangerous state is not “two copies exist.” It is “two copies can both decide what is true.”

# 200. The product-state model is the smallest honest replacement for a universal memory status

Earlier systems often attach one field such as `active`, `stale`, `archived` or `revoked` to a memory record and then overload that field with unrelated meanings. v0.6 treats a memory representation/claim as a product of orthogonal or semi-orthogonal state dimensions.

A useful conceptual state vector is:

```text
EpistemicState
TemporalState
AvailabilityState
AccessState(principal)
ApplicabilityState(task,regime,consumer)
RetentionState
RecoverabilityState
DerivationState
ActivationState(principal,task,consumer)
InterferenceState(principal,task,consumer,rendering)
```

The vector is not a requirement that every implementation store ten enums on every row. Some dimensions can be computed from policy/index/dependency state. The requirement is semantic: no dimension is allowed to be inferred from an unrelated one unless a declared rule establishes the implication.

Examples demonstrate why. An archived fact can remain epistemically supported and historically exact. A private memory can be true but inaccessible to another principal. A correct procedure can be inapplicable to the current tool version. A source can be hard-deleted while a historical judgement remains valid as an audit fact, even though exact re-verification is no longer possible. A frequently recalled memory can have high activation but weak authority. A harmful rendering can be inhibited for one model while the claim remains valid.

This product state prevents “status laundering.” It also allows policies to be precise. Retention may operate on `RetentionState`; truth maintenance operates on `EpistemicState`; the frame compiler operates on usability derived from access, availability, applicability and preservation; recovery consults recoverability and historical judgement.

The implementation danger is uncontrolled cross-product explosion. v0.6 avoids requiring every theoretical combination to be explicitly materialized. Instead, each transition declares which dimensions it may change and which it must preserve. A retention delete may change availability/recoverability and possibly downstream assurance, but not convert the historical claim into contradiction. A principal revocation changes access and dependent frame freshness, not factual truth. These transition constraints are easier to test than a gigantic global state machine.

# 201. Canonical evidence is observation history, not already-interpreted truth

The canonical layer begins with evidence events because derived meaning must remain correctable. An evidence event records what source produced what observation under which identity/time/scope, not a guarantee that the observation's content is true.

For a tool call, for example, useful canonical facts may include:

```text
operation request digest
transport result
stdout/stderr/artifact digest
observed postcondition if separately checked
source event identity
source/tool version
principal and visibility
observed/ingested time
```

The statement “deployment succeeded” is a claim derived from some subset of those observations. This distinction is essential when transport success and world success diverge. It also supports later correction: if a tool was discovered to report stale cached state, the raw observation can remain historically accurate (“tool returned X”) while claims that treated X as current truth are downgraded.

Evidence events are immutable in identity and content once committed; corrections arrive as new evidence or metadata about source integrity. Their accessibility/retention can change under policy. Derived parsing fields may be revisioned rather than mutating the raw event.

This structure also prevents event multiplicity laundering. One upstream event delivered twice remains one semantic evidence event even if there are two transport receipts. Two genuinely separate observations with identical bytes remain two evidence events. The runtime can therefore distinguish redundancy from corroboration.

The canonical layer is deliberately not a universal raw-data lake. Retention and privacy may forbid storing complete source payloads. In that case the event records the strongest policy-permitted evidence representation and the loss/recoverability consequence. A later system must not claim forensic reconstruction that policy made impossible.

# 202. Claims are hypotheses with justification state, not strings promoted into facts

A claim is a proposition-like object whose current epistemic status is derived from admitted evidence and justification semantics. It may represent an external-world fact, a user preference, a causal hypothesis, a procedure applicability assertion, a historical judgement or a bounded absence claim. Different claim kinds have different authority sources and verification requirements.

A minimal claim revision binds:

```text
logical claim identity
subject/predicate/value or normalized proposition
scope / regime / temporal validity
created-from evidence and derivation refs
justification alternatives
contradiction/counterexample relations
current epistemic state
historical revision lineage
```

Claims need not all be symbolic logic expressions. Natural-language content can remain in a structured payload. What matters is that the runtime can identify when two revisions are intended to update the same logical claim, when they are merely related, and what evidence supports each.

The OR-of-AND justification algebra is crucial. A claim can remain supported after one evidence path fails if another independent path survives. This avoids destructive descendant invalidation and allows source deletion to reduce assurance/recoverability without inventing a falsehood.

“Canonical claim” therefore means the runtime has admitted a proposition into its epistemic state machine, not that the proposition is eternally true. Canonical claims can be disputed, superseded, historically valid, currently unsupported or revoked. Their revision history lets future agents explain what was believed when and why.

A representation can quote or summarize claims, but if a representation asserts a proposition not present in its source claims/evidence, that addition is a new candidate claim requiring admission. The transformation does not acquire authority by proximity to trusted material.

# 203. Historical judgement is a first-class memory because action explanation requires what was believed then

A memory runtime used by autonomous agents needs to answer two different retrospective questions:

1. What does current evidence indicate was true at time `t`?
2. What did the agent legitimately judge at time `t` using evidence then available?

Without a historical judgement object, later corrections tend to rewrite the past. Suppose the agent believed API v1 was active and selected procedure P; later evidence proves v2 was already active. Current truth should change. The record “agent judged v1 under evidence E at t” should not.

A historical judgement binds the exact Recall Cut/evidence set, principal/self-version, relevant procedure/normalizer profile and the decision/action it influenced. Its retrospective assessment can later become `REFUTED`, `PARTIALLY_SUPPORTED` or `UNVERIFIABLE`, but the historical judgement event remains immutable.

This is vital for learning. A failed action may have been rational given the available information, indicating a sensing/coverage problem rather than a reasoning problem. Conversely the evidence may have clearly contradicted the chosen action, indicating a decision failure. If current truth overwrites past belief, these failure classes collapse.

Historical judgement also supports Tề Hạ-style self-version continuity. A future self can reconstruct not only “what I wrote” but “what I believed, why I believed it and what evidence I lacked.” That gives self-modeling a grounded basis while preventing prior-self statements from becoming current authority.

The cost is more audit state. v0.6 accepts that cost for consequential decisions but does not require a judgement record for every trivial model token. Host policy decides which decision classes warrant explicit historical judgement receipts.

# 204. Semantic regions define causal repair locality, not physical sharding boundaries

A `SemanticRegionRevision` is the runtime's **causal repair/transformation locality hypothesis**, not the canonical identity owner of the claims/evidence it contains and not necessarily a physical shard. It groups semantics expected to be transformed, recalled or repaired together while preserving the ability to revise that grouping when later evidence shows the boundary was wrong.

v0.6.1 makes split/merge lineage explicit.

**Split.** If `R1@k` is discovered to contain decision-distinct substructures, the runtime creates successor region revisions such as `R2` and `R3` with a split receipt mapping member semantic objects and representation lineages. Historical handle `R1@k` remains resolvable. A request for the *current successor of R1* may legally return `AMBIGUOUS_SUCCESSORS` when no single successor subsumes the old region.

**Merge.** If `R4` and `R5` are later shown to be one inseparable transformation/repair neighborhood, the runtime creates a new merged region revision. The contained `ClaimRevision`, `ExperienceTraceRevision`, counterexample and debt identities do not change merely because their locality container changed.

This is crucial for long-lived references. A `MemoryQueryCounterexampleRevision` binds the semantic target/representation lineage it falsified, with region IDs as locality hints rather than the only identity. Semantic debt, preservation envelopes, historical frames and continuity pins follow canonical targets through region evolution via versioned mapping. Otherwise a region split could accidentally “lose” the counterexample that motivated the split.

Repair locality is still causal rather than geographical. If one summary in R2 lost an exception, the repair cone can remain local. If the defect is in a shared transformation profile, entity resolver, temporal normalizer or origin classifier, every dependent region is a candidate for revalidation. A region boundary is therefore a useful optimization only while its independence assumptions remain valid.

Physical storage may shard completely differently. The architecture requires stable semantic identity across region evolution, not one database partition per region.

# 205. Representation fibers let one semantic region support many cognitive uses without multiplying truth

For each semantic region `R`, the runtime may maintain a fiber:

\[
F(R) = \{r_1, r_2, ..., r_n\}
\]

where each `r_i` is a representation derived from the same or overlapping canonical source state. Representations can differ in granularity, role, cost and observable preservation: raw trace, structured event, episode, compact summary, procedure, failure lesson, anchor or specialized projection.

The fiber is not a hierarchy by default. A short procedure may be more useful than a detailed episode for one query but unable to answer historical timing. Two summaries may preserve incomparable semantic dimensions. This is why v0.6 rejects a single “memory level” ranking and uses property-scoped capability/preorder plus Pareto cost tradeoffs.

Every representation binds source region/claim/evidence refs, transformation contract, preservation envelope, semantic-loss state, recoverability and role tags. Derived descendants keep lineage. If source evidence changes, reverse dependencies identify representations requiring revalidation. If a new query falsifies one preservation claim, the region can generate a replacement representation while leaving unaffected views intact.

Fibers also support consumer specialization without schema proliferation. A weak model might use a highly structured compact representation; a strong model may hydrate a richer episode. Both refer to the same canonical memory. This is the central mechanism by which a giant runtime can adapt memory presentation without creating model-specific truth stores.

# 206. Query families are contracts over required observables, not clusters of similar questions

A preservation system cannot enumerate every future natural-language query, but it can reason about the semantic observables a query requires. A query-family basis therefore describes a bounded contract such as:

```text
current scalar value with exact numeric precision
historical entity identity
broad event ordering
exact interval endpoint
procedure applicability and exception
causal predecessor under declared relation semantics
```

Natural-language classifiers or model reasoning can map a query to one or more families, but that mapping itself has a capability/uncertainty profile. Similar wording is not the definition. “Was X ever true?” and “How long was X continuously true?” can be textually close while requiring different temporal evidence.

A preservation envelope is always relative to a query-family basis revision. Adding a new semantic dimension or refining a family's meaning invalidates or rechecks prior certificates. This prevents old representations from inheriting exactness into a stronger future contract by naming coincidence.

The open-world limitation remains explicit: families known today cannot prove safety for arbitrary future questions. v0.6 treats unseen families as `UNKNOWN`, then uses query counterexamples and source rehydration to refine capability over time. This is a corrigibility strategy rather than a prediction that the future query space is closed.

# 207. Preservation envelopes are capability certificates, not confidence scores

A preservation envelope states what a specific representation can answer or reconstruct under a specific source/transform/query-family profile. A useful envelope can contain statuses such as:

```text
EXACT
BOUNDED
UNKNOWN
LOST
SOURCE_REHYDRATABLE
COUNTEREXAMPLE_REFINED
```

with evidence/witness references and verifier capability.

The envelope is not a probability that “the summary is good.” It is a product of property-specific judgements. One representation can be exact for identity, bounded for broad temporal order, lost for numeric precision and rehydratable for exceptions. This form directly supports representation resolution.

Certification is conservative. A generator's self-reported abstraction loss is evidence at most; protected fields require deterministic checks, independent verification, source comparison or bounded probes appropriate to the memory form. Composition obeys loss conservation: pure descendants cannot upgrade `LOST` or `UNKNOWN` without source rebase/new evidence.

Envelopes have dependencies: source retention, transformation revision, normalizer, query-family basis, verifier procedure and possibly regime. Source deletion can downgrade `SOURCE_REHYDRATABLE` to `IRRECOVERABLE_GAP`; a new counterexample can invalidate one dimension without destroying the entire representation.

The runtime can store approximate empirical quality scores beside the envelope for ranking. Those scores never replace the discrete semantic guarantee used for hard Recall Obligations.

# 208. Recoverability is the bridge between aggressive compression and honest forgetting

Compression becomes safe at scale only when the runtime distinguishes “not currently present in this compact representation” from “cannot be recovered.” Recoverability describes the available path back to stronger evidence.

Possible states include:

```text
EXACT_IN_REPRESENTATION
SOURCE_REHYDRATABLE
ALTERNATE_WITNESS_REHYDRATABLE
PARTIAL_RECOVERY
SOURCE_UNAVAILABLE_TRANSIENT
IRRECOVERABLE_BY_POLICY
IRRECOVERABLE_UNKNOWN_LOSS
```

A compact summary may safely omit exact log bytes if a policy-permitted artifact remains addressable. Conversely a high-fidelity looking summary can be dangerous if it is the last surviving representation of a detail it did not preserve.

Recoverability participates in retention and page-fault logic. The retention optimizer tracks witness cover over protected semantic dimensions. The recall resolver chooses compact views first but can trigger semantic page faults when a stronger observable is needed. Deleting a source updates envelopes/debt so future page faults fail honestly rather than hallucinating reconstruction.

Recoverability is not infinite forensic retention. Privacy or cost policy can authorize destruction. The kernel's responsibility is accounting: what capability was lost, which representations/certificates depended on it, and whether current claims still have independent support.

# 209. Semantic debt makes unresolved preservation risk explicit rather than hiding it in maintenance heuristics

Not every memory transformation can be fully verified when it occurs. A query family may be unknown, a source may be temporarily unavailable, independence may be uncertain, or a migration may lack enough metadata to reconstruct legacy applicability. v0.6 records these situations as semantic debt instead of silently choosing optimistic defaults.

Debt is typed and dependency-bearing. Examples:

```text
UNKNOWN_QUERY_FAMILY_COVERAGE
UNVERIFIED_ABSTRACTION_EXCEPTION
SOURCE_REHYDRATION_AT_RISK
UNKNOWN_EVIDENCE_DEPENDENCE
INTERFERENCE_EFFECT_UNCALIBRATED
MIGRATION_APPLICABILITY_UNKNOWN
```

Debt can influence retention, maintenance scheduling, recall sufficiency and promotion policy. A high-severity source-recoverability debt may protect a raw witness from ordinary LRU deletion. A query-family debt may cause a future exact request to page-fault instead of trusting a summary.

Debt does not disappear because a maintenance epoch completed. It is discharged only by a typed event: evidence/verification, a stronger transformation contract, authorized policy waiver, supersession or policy-authorized destruction of the underlying memory. A waiver remains distinguishable from proof.

This makes long-lived uncertainty measurable. Without debt, semantic risk tends to migrate into comments, heuristic thresholds or operator intuition until the original reason for caution is forgotten.

# 210. The semantic fixed-point law prevents maintenance from manufacturing a telephone game

A memory runtime can accumulate error even when every individual summarization appears reasonable. Repeatedly summarize the latest summary, then summarize that result, and small losses or invented details can compound. v0.6 therefore defines maintenance convergence over **normalized semantic state**, not over activity.

Given stable canonical evidence, policies, transform profiles and query-family basis for a region, repeated maintenance should eventually reach a state where another pass creates no materially new canonical representation capability, debt or justification. Surface wording may vary; material meaning may not drift unjournaled.

A pass that proposes a genuinely different semantic alternative must either:

- prove/verify it and record the selection,
- keep alternatives as candidates/ambiguity,
- or rebase to source/new evidence.

It cannot sample one alternative into the persistent memory merely because the generator is stochastic.

Fixed-point monitoring gives an operational diagnostic: regions repeatedly rewritten without new evidence are suspicious. Maintenance can then freeze the region, rebase from source, inspect transform debt or change the profile. This creates a direct feedback loop between semantic theory and resource efficiency.

# 211. Counterexample-guided refinement converts future ignorance into a repair protocol

The runtime cannot know every future query, but it can learn when an existing representation fails one. A query counterexample contains the required semantic family/dimension, the representation used, the answer/result that failed, and a stronger source/witness showing the distinction that was lost or misrepresented.

The counterexample has three effects.

First, it invalidates the specific preservation claim. The underlying canonical world claim is changed only if the stronger evidence also contradicts it.

Second, it identifies the earliest relevant transformation or shared profile that lost the distinction. This determines repair scope.

Third, it becomes a regression witness. Future transformations over the affected region/profile must preserve or explicitly declare inability on that observable.

Repair then rehydrates the strongest surviving source, generates a new representation with a refined envelope and updates descendants/caches. If no source exists, the runtime records an irrecoverable gap rather than asking an LLM to reconstruct the missing detail from plausibility.

This is the heart of v0.6 corrigibility. The system does not need perfect foresight; it needs persistent memory of **how its own memory representation failed** and enough source structure to repair that failure when possible.

# 212. Repair locality is a causal property, not a promise that every fix stays small

Local repair is desirable because global rebuilds of a large memory universe are expensive and destabilizing. But declaring every counterexample “local” would be unsound. v0.6 computes scope from the falsified dependency.

If a single region summary lost an exception because of region-specific evidence/segmentation, repair can remain in that region and descendants. If the failure exposes a bug in transformation profile `T7` used across 100,000 regions, every certificate depending on `T7` may require revalidation. If the failure comes from a normalizer used by claim identity itself, canonical migration may be needed.

The runtime therefore records repair cause type:

```text
REGION_CONTENT
REGION_BOUNDARY
SHARED_TRANSFORM_PROFILE
NORMALIZER
QUERY_FAMILY_BASIS
SOURCE_INTEGRITY
SCHEMA/POLICY
```

and uses reverse dependencies to compute the affected closure. Alternative live justifications prevent unnecessary epistemic invalidation even when representations are rebuilt.

The research debt is finding scalable approximations for large dependency closures. The semantic rule is already clear: **repair blast radius follows proven dependency, not convenience**.

# 213. Forgetting is constrained witness optimization, not age-based deletion

A lifelong memory cannot retain everything hot forever, but age/frequency alone are poor deletion semantics. v0.6 derives a protected witness basis for each region from active claims/procedures/counterexamples, historical audit policy, known query-family obligations and semantic debt.

Each retained source/representation covers some protected observables. Forgetting asks for a cheaper retained set whose union still covers the required basis. This is a set-cover style optimization subject to privacy/retention policy and recoverability costs.

Important consequences follow:

- rarely recalled exceptions can remain protected;
- popular but redundant summaries can be removed;
- source evidence can move cold while compact representations remain hot;
- deletion of the last witness is legal when authorized policy requires it, but the resulting capability gap becomes explicit;
- semantic debt can protect a witness until the debt is discharged or policy overrides it.

Approximate algorithms are acceptable for choosing witnesses, because optimal set cover can be expensive. The post-delete semantic checker is not approximate: it verifies that the declared protected basis is still covered or records the exact gap.

This is how Nolane Memory can become physically huge yet still control storage without pretending “forgetting” is a harmless cache eviction.

# 214. Recall feasibility is a proof obligation before ranking becomes an optimization problem

The frame compiler receives a Recall Obligation describing hard roles and required observables. Candidate representations have coverage capabilities and token/latency/interference costs. The first question is not “which memories score highest?” but “does any admissible combination cover the hard universe?”

Formally, if hard obligation set is `H` and selected representations are `S`, a sufficient frame requires:

\[
H \subseteq \bigcup_{r \in S} Coverage(r)
\]

under the current principal, cut, applicability and capability constraints.

Only after this predicate holds may the compiler optimize cost or optional evidence. If no feasible cover exists inside the context budget, the correct result is overflow/insufficiency or staged execution under one cut. This is directly motivated by the Nolane World critical-compressor counterexample: selecting two of three critical items satisfies the size limit but violates semantic feasibility.

This separation also makes learned ranking safer. Embedding relevance, activation and effect estimates can order optional choices. They cannot trade away a hard constraint because the cover checker would fail the candidate frame.

# 215. Semantic virtual memory is more than a metaphor: it defines the context-miss recovery path

The virtual-memory analogy becomes useful only when it constrains behavior. Canonical memory and rich representations live outside the LLM context. The model-facing frame is the current working set. A semantic page fault occurs when the required region is known but the currently resident compact representation lacks an observable required by the Recall Obligation.

The page-fault handler can:

1. hydrate a stronger resident representation,
2. query an exact canonical claim/evidence field,
3. fetch a cold source/artifact,
4. reconstruct a temporary higher-fidelity representation,
5. or return insufficiency if no permitted witness exists.

The resulting materialization remains bound to the same Recall Cut. It may be cached, but cache state is non-authoritative. Repeated page faults can trigger a maintenance decision to keep a stronger compact representation hot for that query family.

The analogy also clarifies what is *not* allowed: silently inventing missing detail is not a page fault resolution; replaying the entire history for every miss defeats locality; treating a stale summary as sufficient because it is resident is analogous to serving an invalid page without coherence checks.

# 216. The context-locality theorem is conditional on true dependency width, not total memory size

Nolane Memory's key scalability claim is deliberately narrower than “constant context.” Let `N` be total stored history and `W(q)` the minimum decision-relevant memory dependency width for bounded query/task `q` under the chosen semantic basis. v0.6 targets context cost approximately governed by `W(q)` plus representation overhead, not by `N`.

When `N` grows while `W(q)` stays fixed, indexes/region discovery should prevent prompt growth. When `W(q)` itself grows—because the decision genuinely depends on hundreds of constraints—the frame must grow, stage-hydrate or overflow. A design that keeps context constant by dropping dependencies does not satisfy the theorem.

The theorem also assumes the runtime has adequate indexes/capability to discover the required regions without global prompt replay. Approximate discovery can be backed by exact hard-role routes where necessary.

Evaluation therefore separates store-size scaling from dependency-width scaling and measures both token cost and decision equivalence. This makes the scalability claim falsifiable rather than promotional.

# 217. Negative memory knowledge is a statement about a searched domain, not an empty list

A positive memory claim can point to the object that supports it. A strong negative claim—“there is no active counterexample matching condition X”—depends on the completeness of the search domain and procedure.

The runtime therefore binds the predicate, principal scope, temporal/regime domain, storage tiers, query capability, pagination/snapshot semantics and visibility frontier. Only when the declared bounded domain is complete and no match exists can the output become `NO_MATCH_COMPLETE_DOMAIN`.

A timeout, partial connector, stale ANN index or private inaccessible shard yields weaker states. New matching inserts can invalidate a cached empty result through domain-generation/predicate dependencies even though no previously returned object changed.

This discipline is particularly important for procedures and safety guards, where “we know no counterexample” is much stronger than “the semantic search returned none.”

# 218. Memory-effect learning is a causal optimization layer whose outputs must remain defeasible

The effect ledger observes how exposing a memory or representation changes a consumer's downstream behavior. It uses explicit evidence tiers—from observational association to paired/randomized intervention—and scopes conclusions to consumer/model, task, regime, rendering and co-context.

An effect profile can justify choices such as:

```text
prefer structured rendering
avoid proactive injection
use alternative witness
lower optional activation
request revalidation
```

It cannot alter factual authority, erase a hard obligation or automatically transfer to a new model version. A truthful memory that confuses one model remains truthful. A false memory that happens to improve an outcome remains false.

The hardest empirical debt is attribution under multiple simultaneously exposed memories and distribution shift. v0.6 therefore treats high-confidence global inhibition as difficult to earn. The safe default for uncertain effect is to preserve knowledge and reduce unnecessary exposure rather than destroy memory.

# 219. Security and preservation share one lineage substrate but answer different policy questions

Memory poisoning and privacy both propagate through derivations, so the same source/transform lineage is useful for security response. If an origin is compromised, descendants can be quarantined or revalidated. If a private source is deleted or declassification revoked, derived representations can be reclassified or removed from broader scopes.

Yet security and epistemic preservation must not be collapsed. A memory can be factually well supported but confidential; a maliciously injected statement can be public but untrusted. Quarantine can block current use without rewriting historical judgement. Hard deletion can destroy recoverability without proving the claim false.

The shared lineage graph therefore carries multiple orthogonal consequences: epistemic support, information-flow/confidentiality dependency, preservation/recoverability dependency and effect/security activation state. Policies operate on the relevant dimension while preserving the others.

This is how v0.6 avoids a common security shortcut: “unsafe memory = delete and mark false.” Sometimes deletion is correct, sometimes quarantine/reclassification is enough, and sometimes the memory must remain as a counterexample showing that an attack occurred.

---

# PART XX — IMPLEMENTATION SEMANTICS: TWO ENGINES SHOULD DISAGREE ONLY WHERE THE SPEC ALLOWS IT

# 220. Conformance is semantic equivalence, not identical internal traces

Two implementations of Nolane Memory may use different databases, graph layouts, embedding models, cache strategies or language-model helpers. Requiring identical internal traces would freeze the design to one implementation; allowing arbitrary “reasonable” behavior would make the specification non-normative. v0.6 therefore defines conformance around **normalized observable semantics**.

For a fixed canonical input state, policy/profile bundle and operation, compare at least:

```text
canonical commit outcome / conflict state
claim and justification projection
historical judgement status
product-state changes
affected preservation envelopes / debt
principal-visible recall domain
Recall Sufficiency outcome
hard-role coverage
source/repair requirements
security/access result
```

Nonauthoritative candidate ordering, internal ANN neighbors, LLM draft wording and maintenance scheduling can differ as long as they lead to an equivalent declared semantic result or a permitted weaker capability result. For example, an implementation with only exact lexical lookup may return `UNSUPPORTED` where a richer implementation can prove a bounded negative query. That is a capability difference, not necessarily a conformance violation.

The comparison relation is property-scoped. If both implementations claim the same capability profile and receive the same semantic inputs, they should produce the same normalized result for correctness-critical fields. If one advertises a strict capability refinement, stronger conclusive results may replace `INCONCLUSIVE/UNSUPPORTED` only where the refinement contract permits. Opposite conclusive results under supposedly sound equivalent profiles are a conflict requiring investigation, not “different model intelligence.”

This mirrors one of the strongest principles in the Nolane Plan source: capability differences must be explicit rather than leaking into hidden behavior. It gives the future implementation team room to optimize while preserving a stable memory contract.

# 221. Canonical commit protocol: the only place a persistent semantic write becomes real

A candidate memory change can be generated in parallel, but canonical state changes only at one linearization point inside its Memory Authority Domain. A reference commit protocol is:

```text
1. authenticate producer / writer fence
2. normalize semantic write intent
3. bind operation ID + request digest
4. reconcile any prior receipt for that operation
5. load current canonical head inside the correctness transaction
6. verify expected base / policy revisions / authority
7. verify transition/admission receipts remain current
8. apply claim/evidence/justification/product-state changes atomically
9. append canonical event + commit receipt
10. advance canonical frontier
11. publish asynchronous index/representation maintenance work
```

If the expected base changed, the candidate is not blindly replayed. Some writes can be regenerated automatically; others become `WRITE_CONFLICT` or require an explicit merge. A correction, source revocation or declassification change can alter the meaning of an old proposal even if the candidate text is unchanged.

The durable receipt is the semantic evidence that the write happened. If a caller loses the response after step 9, it reconciles by operation ID; it does not create a new operation and apply support twice. Idempotency history therefore has a declared retention/reconciliation horizon.

The writer need not wait for every optional secondary index. The receipt distinguishes canonical commit from index visibility. Consequential read-your-writes paths can overlay canonical deltas or wait for required frontiers.

# 222. Writer fencing is part of correctness because failover can create two “single” writers

A design can claim “one writer per domain” and still split brain after crash/failover if the old writer continues running. The canonical transaction therefore binds a monotonic writer epoch/fence or equivalent storage-level exclusivity token.

When leadership changes:

```text
epoch 17 / fence F17  ->  epoch 18 / fence F18
```

any epoch-17 commit is rejected at the same transaction boundary that checks the expected base. Checking ownership only before a long verification job is insufficient because authority can change while the job runs.

A concrete deployment may use database CAS, advisory/exclusive locks, leases backed by a consensus system, or a monotonic fencing token issued by a storage authority. v0.6 does not mandate a consensus protocol. It mandates the observable property: **a stale writer cannot append a second canonical history after failover**.

Restore and migration also create new active incarnations unless the system can prove continuation of the same history. Reusing an old fence/generation because restored bytes look identical recreates ABA bugs in receipts, caches and negative-query domains.

The future test suite should kill/restart writers at every transition boundary, deliberately retain stale processes and verify only the current epoch can advance the canonical root.

# 223. Admission pipeline: evidence can be stored without being believed

Ingestion and admission are deliberately decoupled. The runtime may store malicious text, uncertain extraction, contradictory observations and low-confidence model proposals because deleting them would destroy evidence about what was observed. Canonical **belief/procedure authority** is a separate transition.

A strong admission path orders checks approximately as follows:

```text
origin / principal / confidentiality binding
semantic event dedupe
candidate claim/role creation
contradiction & supersession discovery
source applicability / regime checks
coverage-preservation-faithfulness verification
justification + independence assessment
counterexample blockers
memory-form policy threshold
canonical commit
```

Ordering matters. A near-duplicate optimization must not discard a user correction before contradiction logic sees it. A scope sanitizer cannot widen confidentiality before an explicit declassification decision. A producer's `confidence=0.99` or `canonical=true` has no authority because those fields are runtime-owned outputs.

Different memory forms can have different admission floors. Raw episodic evidence can be searchable immediately with its low assurance clearly typed. A broadly reusable procedure or semantic principle may require independent support, transfer checks or deterministic verification. The runtime can remain responsive without forcing every byte through expensive LLM validation while still preventing low-assurance content from laundering itself into high-level memory.

# 224. Transition verification checks the delta, not whether the resulting prose sounds good

Memory corruption often occurs during updates: a consolidation omits the new correction, preserves the new fact but erases an unrelated preference, or introduces a plausible claim absent from any source. v0.6 uses three independent transition properties:

- **coverage** — required new information is preserved;
- **preservation** — unrelated still-valid state is not corrupted;
- **faithfulness** — new/changed authority-bearing content is supported by admitted evidence or a trusted derivation.

The verifier receives the exact base revision, proposed delta, source obligations and transformation profile. Its result is versioned and can be `VERIFIED`, `INCOMPLETE`, `OPAQUE`, `REJECTED` or `REQUIRES_REVIEW`. High-assurance admission can require an independent failure mode—deterministic parser/test, different model lineage, trusted tool evidence or human approval. Running the same generator twice is not independence.

Verification budget exhaustion does not convert to success. The runtime can commit raw evidence, keep the abstraction candidate pending or defer maintenance. This preserves throughput while preventing load from weakening epistemic standards silently.

Transition verification is not proof of the world's truth. It proves that the memory update faithfully reflects its declared sources and existing state under the verifier's capability.

# 225. Temporal update protocol keeps event time, valid time, knowledge time and commit time separate

When new evidence arrives, the commit sequence says when the runtime learned/stored the update. The evidence itself can refer to a different world time. A late observation can revise a historical valid interval without overwriting the present simply because it arrived later.

A temporal update therefore declares:

```text
observed/event time
world-valid interval or uncertainty
knowledge-available-from time
ingestion/commit time
source clock domain / ordering confidence
```

Truth maintenance applies the claim to the declared valid interval. `CURRENT_EPISTEMIC_PROJECTION` selects the interval containing current world time; `VALID_AT(t)` selects retrospectively with current evidence; `KNOWN_BY(t)` excludes evidence/derivations unavailable by `t`; `JUDGED_AT(t)` uses the recorded historical judgement/evidence procedure.

Durative claims require stronger evidence than equal endpoint values. A persistent-state representation records coverage/continuity assumptions and can answer exact-duration queries only when its preservation envelope says the boundary/coverage is supported. Otherwise it may answer broader temporal families while remaining `UNKNOWN` for precise intervals.

This protocol is a direct response to temporal-memory research showing that dialogue order and point-wise memories lose meaningful duration, but it adds an explicit truth/knowledge separation to prevent retrospective hindsight leakage.

# 226. Justification-aware invalidation is a two-stage algorithm: candidate reachability, then live support evaluation

Invalidation and repair are two related but non-identical operations. v0.6 already uses reverse dependency traversal followed by live-support evaluation; v0.6.1 closes the **reactivation seam** exposed by the Nolane World source audit.

When evidence, policy, regime or a transformation dependency changes, the runtime first computes a conservative affected set through reverse dependency edges. It then recomputes each affected object's own predicate:

```text
ClaimRevision:
    at least one live grounded OR-of-AND justification
    compatible temporal/scope/regime semantics

RepresentationRevision:
    live source lineage
    valid transformation/preservation contract
    required capability/recoverability

Counterexample / procedure / trigger:
    type-specific source + applicability + lifecycle predicate
```

An active ancestor is not a substitute for the child's own support. A repair receipt naming “replacement evidence E” does not heal a child unless E is actually linked into a live justification/transformation path that satisfies the child's predicate. This directly forbids:

```text
parent is active
+ repair marked resolved
-> reactivate descendant
```

when the descendant's direct/alternative support remains invalid.

The algorithm may iterate to a fixed point because changing one claim can remove a support alternative for another. Independent alternatives remain live. For `(A ∧ B) ∨ C`, losing B invalidates only the first alternative while C can preserve the claim. A source deletion can downgrade recoverability without making the historical claim false. A shared transformation defect can invalidate representations across many regions without rewriting canonical source evidence.

Repair completion is therefore **proof-carrying**. The receipt records the affected set, the cause revision, the object's newly live justification/preservation path, remaining debt and any descendants still requiring revalidation. If the dependency graph is incomplete or the fixed point cannot be computed within the safe resource budget, the runtime returns `REPAIR_SCOPE_UNKNOWN/REVALIDATION_INCOMPLETE`; it does not flip descendants back to active optimistically.

Historical judgement remains preserved throughout. Repair changes what is currently grounded/usable, while the record of what a past self believed and acted on remains auditable.

# 227. Consolidation lifecycle: candidate abstraction, scoped validation, promotion, counterexample, rebase

A consolidated representation has a lifecycle more nuanced than “summary exists.” It begins as a candidate over a bounded semantic region and applicability scope. Verification produces a preservation envelope and loss vector. Evidence diversity/justification determine what role/scope it can support. Successful local use can improve utility/effect estimates without automatically broadening epistemic scope.

New evidence can trigger several paths:

```text
compatible recurrence -> strengthen/support existing representation
new exception -> narrow applicability / add counterexample
contradiction -> contest/split representation
source correction -> regenerate or supersede
query counterexample -> refine preservation envelope / rebase
regime change -> mark procedure/summary inapplicable, not necessarily false
```

A general procedure is therefore a versioned abstraction, not a mutable lesson string. Earlier versions remain historically queryable so the system can explain what guidance was available before the exception was learned.

The lifecycle terminates by supersession, archival, invalidation or policy deletion. Stable input leads to a semantic fixed point rather than endlessly generating “improved” descendants.

# 228. Forgetting protocol separates hotness, accessibility, recoverability and deletion authority

A runtime can reduce memory cost through several distinct operations:

```text
DEACTIVATE / lower retrieval activation
EVICT_FROM_HOT_CONTEXT/INDEX
ARCHIVE_COLD
COMPACT_REPRESENTATIONS
DROP_REDUNDANT_WITNESS
HARD_DELETE_BY_POLICY
```

Only the last necessarily destroys information. The retention planner first computes protected witness obligations and source dependencies. It can evict or archive aggressively while keeping exact rehydration possible. Redundant witnesses can be removed after coverage verification. If hard deletion eliminates the final witness, affected preservation envelopes/recoverability state and semantic debt are updated in the same authorized transition.

Age and low access are cost signals, not epistemic permission. An old catastrophic counterexample may be rarely retrieved yet essential. Conversely a frequently accessed derivative may be redundant if canonical sources and cheaper representations suffice.

The protocol also respects confidentiality: a privacy deletion can override witness-cover preference. The runtime records that the capability was destroyed rather than retaining disallowed data “for safety.”

# 229. Recall pipeline conformance: discover regions, resolve representations, reconstruct, prove sufficiency

A conforming recall has one **cut-consistent** semantic pipeline even if physical code fuses stages:

```text
1. capture consequence boundary
2. compile initial hard Recall Obligation
3. pin Recall Cut K + principal/regime/capability/policy revisions
4. prefilter admissible memory before hidden influence
5. discover regions using indexes/frontiers valid for K
6. resolve representation capability at K
7. page-fault stronger source/representation at K
8. add newly exposed hard dependencies; repeat to fixed point
9. retrieve protected counterexamples/contradictions at K
10. construct competing reconstruction candidates
11. prove hard-role/query-family coverage
12. compile Recall Frame + material dependency manifest D
13. run candidate-payload information-flow gate
14. emit frame + sufficiency + flow receipt for reasoning

15. if a later consequence is proposed:
      canonicalize final sink/tool/action payload
      validate D and mandatory guards against current state
      re-evaluate information flow over the final payload
      issue/validate MemoryUseFence where required
      independently obtain host action authorization
      atomically consume the memory-use fence at dispatch/use boundary
```

Strong fields in stages 3–14 derive from one cut. A nested helper cannot call “latest” and decorate an older candidate with newer conflict/lifecycle state as though that combination had existed. A necessary newer state triggers an explicit cut upgrade and revalidation/recomputation.

The final stages solve a different race: a frame can be correct at T1 and stale at T3 because source, permission, tool schema, counterexample set or hard-role closure changed while the model reasoned.

Conversely, unrelated memory growth does not force a full recall. D is the Semantic-OCC boundary: only changes capable of altering the bounded conclusion require rebase/recompile.

# 230. Frame compiler conformance: semantic cover is checked after every optimization pass

A high-performance compiler may apply dedupe, field projection, summary compression, evidence clustering, alternative representation selection and token budgeting. Each pass can accidentally erase a hard observable. v0.6 therefore treats the frame as a proof-carrying projection.

The compiler maintains a coverage ledger:

```text
hard_role -> source representation(s) -> preserved dimension(s) -> frame fragment
```

After optimization, the hard cover checker recomputes whether every obligation still has an admissible fragment or hydratable handle. Counterexamples and contradictions have protected channels when required. Known unresolved ambiguity remains in the frame metadata rather than being removed to save tokens.

If a safe field-level representation covers the same role, the compiler can replace a verbose narrative. This is the preferred path for reducing interference. If no feasible cover fits, `MEMORY_VIEW_OVERFLOW` is semantically correct. Staged execution can split the consumer task only when the task/runtime supports it and all stages remain bound to a compatible cut.

The frame itself never becomes canonical memory. Any learning from the model's use of the frame returns through the normal evidence/admission path.

# 231. Boot/recovery protocol starts from continuity pins and revalidates capability-sensitive state

Recovery is a stack of increasingly strong claims. v0.6.2 forbids collapsing them into one Boolean.

```text
R0  STORAGE_INTEGRITY
    snapshot/journal/artifact bytes authenticate

R1  CANONICAL_REPLAY
    one committed canonical history is reconstructed

R2  SCHEMA_SEMANTIC_COMPATIBILITY
    migration/profiles preserve or explicitly downgrade meaning

R3  NON_REVIVABLE_BARRIER_CLOSURE
    post-snapshot delete/revoke/compromise/declassification barriers
    are applied before any old payload becomes current-usable

R4  CONTINUITY_ARTIFACT_VALIDITY
    selected pin/handoff is authenticated, cut-bound, reference-complete,
    blocker-free, and compatible with mission/self-version/policy

R5  CURRENT_ENVIRONMENT_COMPATIBILITY
    tool/world/runtime facts that can drift are re-sensed/revalidated

R6  RECALL_SUFFICIENCY
    a fresh boundary-aware hard Recall Obligation is actually covered
```

Passing `R0/R1` proves that old state was recovered faithfully; it does **not** prove that current policy permits using all of it. Passing through R5 still does not prove that the next contemplated action has all memory dependencies needed. `RecoveryResumeAssessment` is the projection/audit object that records these layers and issues `RESUME_ALLOWED` only when the profile-required set passes.

A continuity pin is a reconstruction seed. It cannot override a later delete/revoke barrier or unresolved verification blocker. A snapshot is a historical restore source. It cannot make post-snapshot secret data current again merely because its digest is valid. An old procedure can remain historically authentic yet require revalidation under the new executor.

This layered trust stack operationalizes “past state is evidence, never authority” much more strictly: recovery first proves what past state was, then separately proves what part of it the current self is authorized and capable to use.

# 232. Shared-memory protocol treats publication as a new governed evidence transition

Shared memory remains a governed publication/import protocol with separate epistemic authorities. v0.6.3 adds one read-side consequence: **there is no universal scalar “latest cut” across independently committing authority domains**.

Each domain owns its canonical sequence/root/incarnation. A multi-domain `RecallCutRevision` carries a vector:

```text
K = {
    project-A: (incarnation=4, seq=120, root=...),
    project-B: (incarnation=2, seq=87,  root=...),
    org-policy:(incarnation=9, seq=31,  root=...)
}
```

Publication/import receipts create causal edges. If B@87 contains an admitted import sourced from A@118, any strong cut containing B@87 must include at least A@118. Otherwise the view is causally torn.

The runtime closes/validates K under these edges. Strong completeness also requires every relevant domain/index frontier to cover its K component or provide a complete canonical delta. If B is unavailable/lagging, A memories can still be used under a weaker advisory profile, but the runtime cannot claim globally current absence or completeness.

Publication cycles do not create evidence independence. Origin resolution follows publication/derivation edges to root observations; repeated A→B→C→A echoes improve availability, not corroboration.

The vector cut stops short of global consensus. It supplies one coherent causal observation for the domains involved in a bounded Recall Obligation. Cross-domain atomic invariants remain a separate distributed-systems problem.

# 233. Migration protocol must preserve semantic capability or explicitly lower it

Schema migration is not successful merely because every row parses. The migration defines mappings for identity, claim/support semantics, temporal intervals, authority/access, representation roles, preservation envelopes, query-family basis and recoverability.

For each correctness surface the manifest chooses:

```text
PRESERVE_EXACT
MAP_WITH_VERIFIED_RULE
RECOMPUTE_FROM_CANONICAL_SOURCE
REVALIDATE
DOWNGRADE_TO_UNKNOWN
QUARANTINE
DELETE_BY_POLICY
FAIL_MIGRATION
```

Legacy fields that cannot prove independence remain `UNKNOWN_DEPENDENCE`; old summaries without preservation metadata are not retroactively certified exact. A migration may keep them as candidate/legacy representations with source handles.

Differential fixtures run both old and new semantics over bounded cases, comparing normalized truth/history/recall decisions where the old semantics are well-defined. New capability can refine unsupported old states, but it cannot silently contradict conclusive historical judgements without an explicit correction.

A migration creates a new schema/profile revision and can force cache/index rebuilds while preserving canonical logical identities through an ID mapping manifest.

# 234. Cache and freshness protocol: reuse depends on every property that can change the result

A Recall Frame or representation-resolution cache is valid only relative to its dependencies. The exact key can be compact, but semantically it binds:

```text
canonical cut / relevant commit generations
principal access/confidentiality profile
regime / self-version / tool capability
query-family basis
retrieval/index capability generation
transformation/preservation revisions
counterexample/invalidation generations
consumer/rendering profile where effect filtering matters
```

Positive object IDs alone are insufficient because new matching objects can invalidate negative queries. A stale index can continue returning superseded/revoked memory unless canonical deltas filter it. Access revocation can invalidate a frame even when memory content does not change.

Compatibility is property-specific: a new embedding model might invalidate ranked candidate order but not exact ID hydration. The cache therefore reuses what remains proven compatible rather than flushing everything or, worse, reusing everything.

Cached frames are optimization artifacts. If cache state is lost, the runtime recompiles from canonical/representation state; truth does not disappear.

# 235. Index protocol: contiguous visibility frontier plus capability profile

For each correctness-relevant index, the runtime distinguishes two questions:

1. Through which canonical commit is the index durably complete?
2. What query semantics can this index guarantee?

An asynchronous index that has applied commits `1..10` and `12` has contiguous frontier 10, not 12. Durable application receipts or equivalent state allow the frontier to advance once gaps fill. Sparse later commits may be retained separately.

Capability profiles state whether operations are exact, bounded or approximate: entity lookup, lexical search, ANN retrieval, typed graph traversal, temporal range query, negative-query completeness, principal prefilter and archive search. An approximate index can still be extremely useful for optional candidate discovery. It cannot certify absence or hard coverage outside its capability.

When an index lags, strong recall can combine it with a complete canonical delta from `(frontier, cut]`, applying both positive and negative mutations. If that delta is too large or unavailable, the runtime waits or returns stale/insufficient status instead of overstating freshness.

# 236. Maintenance scheduler protocol prioritizes semantic pressure, not calendar age

Maintenance work is queued from explicit signals:

```text
new compatible evidence / recurrence
new contradiction/counterexample
one-shot high-impact event
query counterexample / preservation debt
source deletion / retention pressure
excessive derivation depth
regime or verifier/profile change
repeated semantic page faults
negative-transfer evidence
```

Each job has an expected semantic benefit, risk, cost and dependency frontier. Background capacity can be budgeted so maintenance never starves foreground capture/commit or required verification. Jobs over stable fixed-point regions are suppressed unless a policy/profile changed.

The scheduler does not decide truth. It decides which candidate maintenance operation deserves resources. Every resulting transformation still passes preservation/admission. This distinction matters because a learned scheduler may optimize expected utility without being safe enough to own memory semantics.

Operational metrics such as debt age, page-fault rate and derivation depth help choose work while avoiding the simplistic policy “summarize every N turns.”

# 237. Degraded modes are explicit capability downgrades, not hidden simplifications

Production failures are inevitable: vector index unavailable, artifact store offline, verification model overloaded, connector opaque, archive key missing or maintenance backlog high. The runtime defines degraded modes by which guarantees remain intact.

Examples:

- ANN unavailable: exact/lexical/hard-role routes may continue; optional semantic discovery capability decreases.
- archive unavailable: compact representations remain usable only within certified observables; page faults become `SOURCE_UNAVAILABLE`.
- verification budget exhausted: raw capture/low-assurance candidates continue; high-level promotion is deferred.
- effect ledger unavailable: do not apply learned inhibition; preserve correctness-oriented frame selection.
- graph cache corrupt: rebuild from canonical edges; causal completeness claims downgrade.

A degraded mode never relaxes principal access, commit idempotency or hard-role feasibility merely to keep the system returning answers. The model/context explicitly sees insufficiency when the missing capability matters to its task.

# 238. Privacy deletion protocol updates information flow, recoverability and derived representations independently

Privacy deletion is complete only when the **erasure closure** for the declared scope is complete. Deleting one raw row is a storage mutation; it is not yet a proof that the memory can no longer be reconstructed or disclosed.

The protocol begins with an authorized `RetentionEventRevision` carrying the target semantic/source scope, deletion mode, effective commit sequence and policy authority. The runtime computes every dependent surface that can preserve or expose the target:

```text
raw/source artifacts
canonical support/justification availability
derived representations (summary/procedure/episode/anchor/handoff)
semantic regions / source handles
lexical/dense/graph/temporal indexes and query caches
continuity pins and exported/shared copies governed by local authority
backup/snapshot restore paths within the host's declared erasure contract
declassification / sink-flow receipts
```

Consequences remain dimensioned. **Epistemic:** an independently supported proposition may remain true. **Recoverability:** deleting the final witness can create `IRRECOVERABLE_GAP`. **Information flow:** existing representation bytes derived from the deleted source are considered tainted even if the proposition itself has independent public support. Such bytes must be purged, quarantined or **cleanly rederived from surviving admissible sources** before they are disclosed again.

This is crucial: removing a private source from a justification list does not prove that a summary generated yesterday no longer contains private details learned from that source. Truth and representation residue are different state.

Read surfaces advance an erasure/purge frontier only when the relevant mutation range is durably reflected; seeing deletion sequence `d` in one asynchronously updated index is not sufficient if earlier updates are missing. `MemoryErasureClosureReceipt` records which surfaces were closed, which were rederived, which remain unavailable/opaque, and whether the runtime may claim `CURRENT_ERASURE_CLOSED` for the requested scope.

Historical audit is retained only as policy permits. Erasure authority can intentionally destroy forensic recoverability; the runtime records the resulting capability downgrade without retaining forbidden content merely to preserve an audit ideal.

# 239. Consumer/model upgrade protocol invalidates behavior-dependent memory before world evidence

A model upgrade changes the agent that consumes memory, not necessarily the external world described by memory. v0.6 therefore orders revalidation by dependency.

Highest priority:

```text
interference/effect profiles
rendering policies
self-policy priors
procedural executor-capability assumptions
context-complexity thresholds
prospective triggers tied to old tool behavior
```

Next, procedures whose applicability depends on tool/model capability are rechecked. Historical external-world claims and evidence generally remain intact unless the external regime also changed. Representation preservation can remain valid if it is semantic/model-independent, but the resolver may choose different representations for the new consumer.

The upgrade event creates a new self-version profile and invalidates caches keyed to the old consumer. A calibration campaign can run paired probes to determine whether old effect profiles transfer; absent evidence, they downgrade rather than being inherited globally.

This preserves continuity while allowing a stronger future model to escape limitations learned by a weaker predecessor.

---

# PART XXI — W5 AND FORMAL EVIDENCE: WHAT HAS BEEN FALSIFIED, WHAT HAS NOT BEEN PROVEN

# 240. Fresh V0.6 W5 research session: runtime-owned closure remains blocked

A fresh Nolane World W5 research session was created specifically for the consolidated v0.6 question rather than reusing a prior session. The research goal was:

> Determine the smallest semantically closed runtime kernel for lifelong Nolane Memory that preserves answerability, authority, temporal truth, recoverability and context locality under repeated transformation, forgetting, recall and repair.

The adaptive depth governor selected depth 5 because the certificate declared very high stakes and uncertainty. The compiled program used an autonomous competence tier, branch limit 6 and a verifier budget of 3. Its stages include an auditable research certificate, evidence/unknown mapping, counterexample retrieval, assumption stress, rival hypotheses, falsification, preregistration and decisive experimentation before synthesis/closure. Private reasoning collection is explicitly false and the runtime retains closure authority.

The host in this environment lacks an independent subagent substrate, so the research-society compiler correctly disabled multi-agent society mode rather than pretending role diversity. That is important: “independent challenger” is not satisfied by renaming one reasoning stream.

The W5 closure evaluator returned `blocked`. Sixteen required gates remain unpassed:

```text
rivals_resolved
claim_provenance
contradictions_repaired
replication
benchmark_validity
verifier_independence
assumptions_stressed
preregistration
source_independence
evidence_uptake
trial_disclosure
nondeterminism_control
environment_contract
external_validity
confidence_calibrated
stopping_rule
```

The runtime also sees seven explicit epistemic debts. This blocked verdict is preserved as evidence that the research process did not convert host-generated analysis into self-certifying closure.

Artifact:

```text
NOLANE-MEMORY-V0.6-W5-RESEARCH-SNAPSHOT.json
digest = c59b9f2cc5689a4ce3f084ae232b2de3c359e46fb3fed9679d5bcf50285bd134
```

# 241. Seven open W5 debts define the actual boundary of v0.6 confidence

The fresh W5 session records seven debts because they cannot be responsibly resolved by adding more architecture prose.

**Future-query basis.** A finite preservation basis cannot certify all future agent questions. v0.6 has a bounded/corrigible contract but no universal guarantee.

**Preservation composition.** The bounded algebra prevents pure recovery of `LOST/UNKNOWN`, but a production language/transform system still needs proof that every supported profile composes correctly.

**Local-repair closure.** Dependency-guided repair is well defined; scalable identification of the smallest safe repair closure under shared profiles remains an algorithmic research question.

**Interference calibration.** Consumer/task/regime-scoped causal effect semantics are defined, but thresholds and transfer behavior require empirical experiments.

**Witness-cover optimality.** The semantics of protected cover are clear; scalable approximation quality under storage/privacy constraints remains open.

**Capability refinement.** Property-scoped preorder semantics are promising, but large heterogeneous representation capabilities need an efficient compatibility calculus without collapsing incomparable cases.

**External validity.** Host oracles and source counterexamples do not establish natural-language extraction correctness or production-scale gains.

These debts are deliberately heterogeneous. The first is partly a fundamental open-world limitation; several are algorithmic/empirical; the last is an evidence-quality limitation. v0.6 does not try to “resolve” them through one generic confidence score.

# 242. Formal preservation-calculus lab: 25 properties, 75,772 bounded cases

A new model-free lab was implemented after the v0.6 rewrite to pressure the semantic laws independently of natural-language generation. The lab uses a deliberately tiny universe of semantic dimensions and enumerates or fuzzes the state transitions that matter to the kernel.

Fresh result:

```text
revision = NM-v0.6-preservation-calculus-1
properties = 25
bounded/fuzz cases = 75,772
passed = 25
failed = 0
digest = 05942f077e699fd6a2a209637ff328ae788247cc3d0045958255abc056bf95dd
```

The checked property families include:

- pure-derivation loss absorption;
- `UNKNOWN` non-promotion;
- source-bounded rebase;
- reflexive/transitive property-scoped capability preorder plus existence of incomparability;
- witness-cover deletion;
- privacy deletion producing explicit gap;
- hard-frame feasibility/overflow;
- semantic page-fault distinction between rehydratable and irrecoverable;
- cause-dependent repair locality;
- applicability-conditioned support;
- source-event identity distinct from delivery/content identity;
- OR-of-AND justification semantics;
- single canonical claim across multiple memory roles;
- justification-aware invalidation;
- truth/access orthogonality;
- knowledge-time exclusion;
- scoped counterexamples;
- consumer/task/regime-scoped effect profiles;
- hard-role conservation under interference;
- stable-maintenance fixed point;
- 50k pure-transform chain fuzz;
- 20k local-repair locality fuzz;
- fixed-dependency-width frame stability under irrelevant store growth;
- rejection of universal future-query safety from a partial basis.

The lab is saved as both executable Python and a machine-readable result artifact so future semantic changes can be rerun rather than restated in prose.

# 243. Why the formal lab is stronger than another hundred hand-written oracle sections

The purpose of the lab is not the larger case count. It is the shift from example-level confirmation to **property-level falsification**.

Consider loss conservation. A hand-written example can show one chain where `LOST` remains lost. The lab instead enumerates every four-step continuation over the bounded status alphabet from a lost state and separately fuzzes 50,000 longer chains. The result still does not prove the real implementation, but it eliminates a large class of accidental transition-table mistakes in the reference semantics.

Witness-cover and frame-feasibility checks similarly enumerate small subset worlds. This matters because greedy retention or ranking heuristics often succeed on intuitive examples and fail on a specific combination of overlapping witnesses or hard roles.

The capability-preorder test checks reflexivity/transitivity and confirms incomparable representation pairs exist. That directly protects the decision to use property-scoped capability plus Pareto choice instead of forcing every representation into one fidelity hierarchy.

The lab also includes a negative research result by construction: a finite known semantic basis has unseen dimensions, so “safe for all future queries” cannot follow from the certificate. The model thus enforces the humility of the spec rather than only its positive mechanisms.

# 244. What the bounded model intentionally abstracts away

The formal universe uses symbols such as `negation`, `exact_number` or `interval_boundary`. A real system must infer those requirements from messy language, images, tool results and application schemas. The lab does not prove that inference.

It also idealizes several dependencies. Source identity is assumed known when testing event dedupe. Applicability slices are explicit rather than learned. Justification sets are correct by construction. The repair graph is small and typed. Storage and indexes do not fail except where a property models unavailability.

These abstractions are desirable for semantic model checking, but they establish a strict boundary:

```text
semantic law survives bounded model
!=
extractor correctly instantiates law in production
```

Future evidence therefore needs at least three additional layers:

1. parser/extractor differential tests on held-out natural-language/tool traces;
2. implementation state-machine fuzz under real concurrency/crash/migration;
3. end-to-end benchmarks where memory affects action quality/cost over long horizons.

The formal lab prevents semantic inconsistency. It does not replace empirical research.

# 245. Fresh source regression: Nolane World remains executable while exposing useful adversarial gaps

The supplied Nolane World 0.12.0 source bundle was freshly extracted for this revision. A focused packaged regression over all test files whose paths include `memory`, `truth` or `recovery` selected 21 files and produced:

```text
94 passed
0 failed
2.17 seconds
```

This establishes that the reused substrate patterns are executable in the current environment. It does not invalidate the source counterexamples retained in Sections 121–124; those probes target properties outside the packaged tests.

The correct interpretation is exactly what v0.6 wants from Nolane World:

- transactional/idempotent `WorldStoreV5` demonstrates a stronger mutation pattern;
- truth maintenance demonstrates alternative justification behavior;
- recovery bootloader demonstrates drift-aware continuity;
- older memory/experience/compression surfaces provide counterexamples that force stronger semantics.

Nolane World therefore functions simultaneously as a library of tested mechanisms and an adversarial legacy system. The research process does not need to label the whole project “good” or “bad.” It extracts invariant-level evidence.

# 246. Differential implementation is the next semantic test that host-side oracles cannot replace

The strongest next conformance experiment is to implement the bounded kernel twice with intentionally different internal designs. For example:

- Implementation A: relational/MVCC canonical store with normalized typed tables;
- Implementation B: append-only event log plus materialized in-memory projections.

Both receive identical semantic fixtures covering commit/idempotency, temporal queries, justifications, preservation envelopes, witness deletion, page faults, hard-frame cover and repair. A conformance comparator checks normalized outcomes, not internal traces.

This test can reveal ambiguities that a single reference implementation hides. If both reasonable implementations interpret “recoverability after source deletion” or “capability refinement” differently, the Markdown remains underspecified even when each implementation passes its own unit tests.

The experiment should also mutate implementation-specific non-authoritative surfaces—index ordering, cache strategies, representation text—to verify canonical outcomes remain invariant. Where capabilities differ, the comparator uses the property-scoped refinement relation instead of demanding false equality.

Until such differential implementation evidence exists, v0.6 can claim a deep semantic target, not implementation-level closure.

# 247. Independent verification requirements: what would actually move W5 toward closure

Passing W5 should require evidence that cannot be manufactured by the document author alone. A credible path includes:

**Independent semantic reviewer or implementation.** A separately produced kernel/model should find the same normalized results or identify specific ambiguities.

**Preregistered decisive experiments.** Before observing results, freeze the hypotheses, baseline budgets, semantic violation metrics and failure update rule for context scaling, preservation repair and interference.

**Held-out source traces.** Evaluate extraction/applicability/preservation on data not used to create the rules.

**Benchmark validity audit.** Confirm that chosen benchmarks actually test the memory property claimed, rather than only generic model capability.

**Nondeterminism disclosure.** Repeat stochastic retrieval/consolidation/interference experiments across seeds and report variance/tails, not one best run.

**External validity.** Test across at least several agent/task regimes and consumer models before broad transfer claims.

**Stopping rule.** Define when more experimentation is unlikely to change the architecture, rather than continuing until a preferred result appears.

The release document can prepare these protocols. It cannot self-satisfy them.

# 248. The evidence hierarchy used by this specification

To prevent one kind of evidence from being accidentally promoted into another, v0.6 labels research evidence by level.

```text
L0 — architectural inference / design rationale
L1 — source-code inspection
L2 — executable source counterexample or packaged unit regression
L3 — bounded deterministic/model-free oracle or exhaustive tiny-world property
L4 — implemented-kernel property/fuzz test
L5 — controlled end-to-end benchmark / ablation
L6 — independent replication / differential implementation
L7 — production longitudinal evidence
```

A high level is not always “more true”; it addresses a different generalization boundary. L3 can be stronger than L5 for a narrowly formal semantic law, while L5 is necessary for empirical usefulness. The hierarchy mainly prevents statements such as “25 bounded properties passed, therefore the production runtime is safe.”

Each major v0.6 claim can be associated with the highest evidence level currently supporting it. Source bugs are L2; the preservation calculus is L3; most full architecture/performance claims remain L0–L3 until implementation and benchmarks exist. W5 debts largely identify where L5–L6 evidence is still required.

# 249. Research provenance must survive the same memory principles the runtime advocates

A memory research document can commit the same epistemic sins it criticizes: copy one result into many sections and count it as corroboration, overwrite failed attempts, blur historical and current claims, or present a structural verifier as empirical evidence.

v0.6 therefore treats its research artifacts as a small evidence system. The W5 snapshot, formal-lab result, source regression and final structural verifier have distinct digests and roles. Historical v0.5/v0.4 artifacts are retained as lineage rather than rewritten. A new verifier run supersedes old counts but does not erase what was previously claimed.

When a document contradiction is discovered, the corrected release should state the correction rather than silently deleting the failure. This was already learned in earlier revisions when a claimed Closure Matrix did not actually exist.

The discipline matters because Nolane Memory is specifically about durable epistemic state. The research process should be a miniature demonstration of the same values: origin, revision, debt, bounded claims and recoverability.

# 250. W5 verdict for v0.6: strong research target, deliberately not convergence-certified

The present evidence supports a much stronger statement than v0.5's fragmented catalogue, but a weaker statement than “the architecture is proven.”

Supported now:

- the ownership model is internally coherent enough to state normative transitions;
- multiple legacy/source counterexamples motivate the kernel laws;
- a fresh source regression passes;
- a bounded preservation calculus survives 75,772 enumerated/fuzz cases;
- context/preservation/security/recovery semantics are specified in a way that can be differentially implemented;
- open empirical/algorithmic debts are explicit.

Not supported now:

- independent implementation equivalence;
- production-scale context-locality performance;
- calibrated interference effects;
- universal query-family classification accuracy;
- optimal witness-cover retention;
- external replication or W5 closure.

Therefore the v0.6 release may call itself **deep consolidated research specification / pre-implementation semantic target**. It must not call itself a verified production architecture or finished memory runtime.

---

# PART XXII — ACCEPTANCE AND CONFORMANCE GATES: WHEN AN IMPLEMENTATION MAY CLAIM EACH CAPABILITY

# 251. Conformance is staged so partial implementations cannot borrow the name of the full runtime

Nolane Memory is intentionally deep, but a first implementation should not attempt every cognitive mechanism at once. v0.6 therefore defines staged conformance levels. Each level inherits every lower-level invariant and adds one coherent capability surface.

```text
K0 — Canonical Memory Integrity
K1 — Representation & Preservation
K2 — Recall & Context Virtualization
K3 — Lifelong Evolution & Corrigibility
K4 — Effects, Security & Multi-Agent Continuity
K5 — Full Research Runtime Profile
```

The levels are not pricing tiers or marketing editions. They are implementation/evaluation contracts. A project can honestly say “K2-conformant subset” without claiming associative interference calibration or multi-agent propagation. This makes development tractable and protects architectural semantics from the common pressure to stub missing behavior with optimistic defaults.

A level is satisfied only by executable behavior, not the existence of classes named after its primitives. Structural/static checks can verify schema ownership; property tests and adversarial scenarios verify semantics. An unsupported feature returns typed `UNSUPPORTED` rather than silently falling back to behavior that violates a higher-level claim.

The strongest rule is anti-laundering: passing K3 cannot compensate for a K0 commit/idempotency failure. A sophisticated reconstructive memory built on duplicated evidence or ambiguous canonical writes is not a partially safe K3 system; its foundation is invalid.

# 252. K0 — Canonical Memory Integrity gate

K0 establishes that persistent memory history has a trustworthy semantic root. Required capabilities include:

- one canonical correctness order per Memory Authority Domain;
- operation ID + semantic request digest idempotency;
- expected-base CAS/conflict semantics;
- writer fencing/failover safety;
- immutable source-event/origin identity;
- separation of transport delivery from semantic evidence event;
- claim/historical-judgement revisions;
- OR-of-AND justification semantics;
- valid-time/knowledge-time separation;
- integrity authority vs confidentiality/access separation;
- principal-safe canonical read/hydration paths;
- durable commit/reconciliation receipts;
- deterministic semantic normalization for replay.

Mandatory adversarial gates include concurrent same-base writers, lost-response retry, duplicate source delivery, alias-origin manufactured corroboration, stale-writer failover, historical late evidence and access revocation.

K0 does not require embeddings, summaries or LLMs. A small deterministic kernel should be able to pass it. That is deliberate: if canonical semantics need a language model to decide whether the same operation committed twice, the boundary is misplaced.

K0 acceptance requires crash/restart property tests over commit points and migration fixtures that prove logical identity/justification survives serialization changes. It also requires the read APIs—including exact GET/debug/hydration—to share the same principal policy semantics.

# 253. K1 — Representation & Preservation gate

K1 adds derived memory without allowing it to become a second truth store. Required capabilities:

- semantic regions and revisioned split/merge boundaries;
- multiple representation fibers per region;
- transformation contracts with source lineage;
- semantic-loss vector/product semantics;
- preservation envelopes relative to query-family basis;
- recoverability/source-witness state;
- semantic debt;
- source/new-evidence rebase distinction;
- role contracts for episode/semantic/procedure/failure/anchor views;
- applicability-conditioned evidence for procedure/failure abstraction;
- transition coverage/preservation/faithfulness verification;
- stable semantic fixed-point maintenance.

Mandatory tests include the source counterexample where caller-reported `abstraction_loss=0` hides a dropped safety precondition, summary-of-summary lost-field recovery, opposite outcomes under different applicability slices, query-family basis expansion and source deletion changing rehydratability.

K1 conformance does not require learned optimal compression. A deterministic structured representation implementation can qualify if its contracts are explicit and correct. Conversely a brilliant LLM summarizer without source/preservation semantics does not.

The key acceptance metric is not ROUGE or semantic similarity. It is preservation of declared observables plus honest `UNKNOWN/LOST/REHYDRATABLE` outcomes.

# 254. K2 — Recall & Context Virtualization gate

K2 makes memory usable under bounded model context. Required behavior:

- compile a typed Recall Obligation from the current consumer boundary;
- prefilter principal/access scope before any retrieval influence;
- pin a coherent Recall Cut;
- discover semantic regions through one or more capability-declared views;
- resolve representations by required observable/preservation capability;
- trigger semantic page faults when compact views are insufficient;
- protect required counterexamples/contradictions;
- build competing reconstructions without laundering inferred bridges;
- prove hard-role/query-family coverage before claiming sufficiency;
- compile a dependency-manifested Recall Frame;
- support typed ambiguity/insufficiency/overflow/staleness/scope outcomes;
- keep context growth tied to dependency width rather than total store.

Mandatory regressions include three critical items under a two-item budget, stale index plus superseded fact, empty partial-domain query, new matching phantom invalidating a negative cache, unrelated counterexample pollution, and a query that requires an exact field absent from the top-ranked summary but available via source page fault.

K2 should be evaluated against full-history/long-context oracle worlds wherever feasible. If the frame claims `SUFFICIENT`, bounded downstream decision results should match the declared reference semantics. Lower token count without decision preservation is a failure.

# 255. K3 — Lifelong Evolution & Corrigibility gate

K3 tests whether memory remains coherent after thousands of transitions rather than one session. It requires:

- justification-aware invalidation to fixed point;
- recurrence/surprise/impact/debt-driven consolidation;
- witness-cover retention and explicit irrecoverable gaps;
- query-counterexample regression witnesses;
- causal repair locality with shared-profile fanout when appropriate;
- source rebase for deep lossy lineage;
- semantic debt lifecycle/discharge;
- stable-input maintenance fixed point;
- migration/restore/incarnation semantics;
- longitudinal probe checkpoints;
- continuity pins and drift-aware recovery.

Mandatory stress includes long transform chains, repeated consolidation over stable input, random source deletion, late counterexamples, schema migration with unknown legacy independence, cold archive outages and context resets after memory evolution.

K3 acceptance demands that the system never “repair” lost information from descendant prose alone and never erase debt because maintenance wants a clean state. A correct irreversible-gap result is preferable to a plausible fabricated reconstruction.

Performance is evaluated alongside semantic stability: rebase/repair/invalidation should be local where dependencies permit, or the system will be semantically correct but operationally unusable at scale.

# 256. K4 — Effects, Security & Multi-Agent Continuity gate

K4 adds behavior-dependent optimization and cross-principal memory, the surfaces most likely to create hidden authority leakage. Required capabilities include:

- causal/evidence-tiered memory-effect ledger;
- consumer/task/regime/rendering-scoped profiles;
- hard-role conservation under interference guard;
- poisoning/origin laundering defenses through the memory lifecycle;
- integrity/confidentiality orthogonality and explicit declassification;
- governed cross-domain/shared-memory publication;
- origin/common-mode dependence across agent echoes;
- prospective trigger ownership and causal visibility;
- self-version migration of procedures/effect profiles;
- handoff packets that preserve epistemic typing;
- one access kernel across search/get/hydrate/archive/debug influence paths.

Mandatory attacks include self-summary/trusted-tool echo laundering, private-memory hidden ranking influence, declassification revocation, duplicate agent corroboration, poisoned procedure activation after multiple sessions and a hard constraint that empirical interference would otherwise suppress.

K4 is where empirical evidence becomes unavoidable: interference effectiveness and attack mitigation cannot be established from model-free semantics alone. The implementation may support the K4 data model while keeping effect-based inhibition disabled until calibrated evidence exists.

# 257. K5 — Full Research Runtime Profile

K5 is not merely “all features enabled.” It is the profile in which the complete v0.6 memory theory has executable support and the research gates for broad claims have been substantially addressed.

It includes K0–K4 plus:

- multiple discovery views including associative/temporal/causal/objective/procedural paths;
- bounded prospection-guided retrieval;
- active reconstructive recall;
- learned/optimized representation selection under hard semantic constraints;
- maintenance/effect policies evaluated longitudinally;
- benchmark and ablation portfolio;
- implementation-level differential conformance;
- migration/recovery/fuzz suites;
- calibrated degraded-mode behavior;
- documented residual debt and unsupported query/profile regions.

Even K5 does not mean “human memory” or universal future-query safety. It means the runtime implements the declared external-agent-memory architecture with evidence appropriate to its claims.

A future W5 closure certificate, if ever earned, would be additional research evidence. It is not encoded as a runtime field that the implementation can set itself.

# 258. Canonical-commit acceptance suite

Before any higher layer is enabled, the following adversarial matrix should be executable:

```text
two same-base corrections -> one commit, one conflict
same op + same digest N retries -> one semantic transition
same op + different digest -> idempotency conflict
commit response lost -> reconciliation returns original receipt
stale writer after failover -> fenced
same upstream event delivered N times -> one evidence event
identical content from distinct source events -> distinct evidence
source revocation during candidate verification -> stale proposal rejected
access grant revoked before linearization -> write authorization rechecked
atomic batch with one invalid item -> no partial canonical state
```

The suite runs under crash injection immediately before/after durable receipt/state writes. After restart, replay must yield one normalized history and no support/confidence inflation.

This gate is deliberately boring and harsh. A lifelong memory with advanced embeddings but nondeterministic duplicate canonical writes is worse than a simpler memory because persistent errors compound.

# 259. Preservation acceptance suite

Preservation conformance uses both crafted semantic fixtures and generated dimensions. Required cases include:

- dropped negation/precondition/exception despite high narrative similarity;
- exact-number loss hidden by high average fidelity;
- `LOST` followed by many pure summaries;
- source rebase restoring the field;
- new evidence restoring a field through a different epistemic path;
- source deletion converting `REHYDRATABLE` to irreversible gap;
- query-family basis expansion invalidating old exactness;
- counterexample-driven local representation repair;
- shared transform-profile bug causing multi-region revalidation;
- stable-input stochastic surface rewrites converging to one normalized semantic state or explicit alternatives.

The reference preservation-calculus lab becomes part of this suite. The production implementation adds natural-language/tool-specific probes and comparison to retained source answers.

A representation may fail certification and remain useful as an advisory candidate. The acceptance rule constrains what it may claim, not whether it may exist.

# 260. Recall acceptance suite

The recall suite distinguishes discovery, representation adequacy and sufficiency. Representative tests:

```text
semantic-near wrong region versus low-similarity causal predecessor
relevant region + coarse representation + exact query -> page fault
rare applicable counterexample versus 99 positive episodes
unrelated counterexample must not pollute query
partial pagination/connector -> no global absence
new matching insertion -> old negative cache stale
principal-private nearest memory -> zero hidden influence for another principal
stale ANN returns superseded fact -> canonical delta filters it
hard roles exceed budget -> overflow, not truncation
multiple decision-distinct histories -> ambiguity, not top-1 narrative
```

For bounded worlds the suite runs a full-history reference consumer and compares downstream normalized decisions whenever Nolane claims `SUFFICIENT`. It records frame tokens and page faults so correctness is not purchased by always hydrating everything.

# 261. Lifelong acceptance suite

A state-machine fuzz harness should run tens/hundreds of thousands of operations over regions:

```text
capture
claim correction
transform
consolidate
split/merge region
archive/delete source
counterexample
repair/rebase
regime change
model upgrade
index lag/rebuild
context reset/recovery
migration
```

Invariants are checked after every step: no ungrounded authority, no lost-field self-recovery, no current claim outside valid-time semantics, no hard-role false sufficiency, no use of deleted/inaccessible source, no debt disappearance without transition, and no representation mutation of canonical identity.

Periodic full recomputation from canonical state is compared with incremental projections to catch drift in invalidation/index maintenance. This is one of the most important implementation tests because bugs in incremental maintenance can remain invisible under ordinary example-based unit tests.

# 262. Context-scalability acceptance suite

The scaling benchmark is two-dimensional.

**Store-size axis:** grow unrelated memory from `10^3` toward realistic large sizes while holding the true hard dependency set fixed. Required-role coverage and downstream decision equivalence must remain stable; frame tokens should grow slowly/sublinearly and ideally remain approximately flat except index metadata.

**Dependency-width axis:** hold total store constant while increasing the number/precision of truly required historical dependencies. Frame tokens/page faults must grow or explicitly overflow; silent constant-size truncation fails.

Additional axes include distractor similarity density, associative hub degree, source coldness, index visibility lag and number of principals/domains. Report p50/p95/p99 latency and tokens plus wrong-decision-without-escalation.

The acceptance criterion is a quality-cost frontier, not a single “context reduced X%” number.

# 263. Temporal acceptance suite

Temporal correctness is tested as a relation among **world-valid time, observation time, ingestion/knowledge time, derivation time and historical judgement**, not as timestamp parsing. The suite contains event time that differs from dialogue/ingestion time; late evidence about a historical interval; `VALID_AT(t)` versus `KNOWN_BY(t)` versus `JUDGED_AT(t)`; exact half-open interval boundaries at equality; two point observations separated by an unobserved gap; persistent-state consolidation over contiguous evidence; regime change that supersedes current applicability without deleting historical truth; partially ordered source clocks; and retrospective correction while retaining the wrong historical judgement that actually caused an earlier action.

Every fixture declares the semantic question before its expected result. A late observation received at `t100` but valid over `[t20,t30)` may change the current retrospective account of the past without becoming evidence available to an agent at `t25`. Observations `X@t1` and `X@t3` do not prove continuous `X` over `(t1,t3)` unless the source/coverage contract closes that interval. A regime transition is validity/applicability evolution, not an instruction to rewrite old episodes.

Comparison is structural: normalized intervals, knowledge cut, evidence refs, historical judgement, ambiguity and coverage gaps. Generated prose is downstream. Two implementations may phrase a result differently and conform; two fluent answers do not conform if one leaks future-derived evidence backward or silently fills a blind interval.

# 264. Procedure/failure acceptance suite

Procedural learning is tested across structural applicability shifts rather than only paraphrases. A procedure succeeds in one OS/tool/schema regime and fails in another; generic promotion must be blocked/narrowed. A transient timeout must not become hypothesis falsification. A one-shot catastrophic counterexample must be retained despite low recurrence. A later model/tool upgrade must invalidate executor-sensitive procedure assumptions before unrelated facts.

Transfer evaluation includes same structure/different wording and same wording/different structure. The desired behavior is structural matching with explicit uncertainty. Procedures must expose when-not-to-use and failure evidence in Recall Frames when those conditions are relevant.

Successful fixes preserve the original failure evidence/reproducer so future debugging can reconstruct why the guard exists.

# 265. Security/privacy acceptance suite

Security tests span the entire lifecycle:

```text
untrusted content -> summary -> procedure proposal
trusted-tool echo of untrusted bytes
self-summary repeated across agents
private source -> attempted public derivative
revoked declassification
hidden private memory influencing public ranking
poisoned memory activated many sessions later
hard delete with derived public leakage
scope mismatch on exact GET/debug/archive path
```

The expected results are not always deletion. Some inputs remain raw evidence but are barred from authority; some descendants are quarantined; some derivatives are reclassified; some counterexamples remain as attack evidence. The suite verifies that confidentiality changes do not rewrite truth and that security inhibition cannot mark a hard role satisfied through omission.

# 266. Migration acceptance suite

Migration fixtures intentionally contain **semantically under-specified legacy state**, because real migrations are hardest where the old schema never represented a distinction the new kernel requires. Fixtures include lineage strings with unknown common origin; summaries without preservation metadata; timestamps whose names do not reveal event/observation/ingestion meaning; one-dimensional `status`; cached procedure confidence without evidence identity; entity IDs that were renamed or merged; old counterexample edges without applicability; and deletion/archive records whose forensic guarantees are unclear.

The safe migration may output `UNKNOWN`, `OPAQUE`, `CANDIDATE_ONLY`, `REVALIDATION_REQUIRED` or explicit semantic debt. It may not manufacture stronger history because the target schema has a field the source lacked. Two old lineage strings are not automatically independent origins. `active` is not automatically current epistemic truth. Missing preservation metadata is not mapped to `EXACT`.

Tests execute old/new reference queries before and after migration, keep historical logical IDs/judgement lineage resolvable where policy permits, prevent old receipts from resurrecting across new incarnations, and crash/rollback where canonical root, representation import and derived indexes can diverge. For each correctness field the manifest declares `PRESERVE`, `MAP_WITH_PROOF`, `RECOMPUTE`, `REVALIDATE`, `DOWNGRADE`, `QUARANTINE`, `DELETE_BY_POLICY` or `FAIL`. Converting every row while upgrading unknown meaning is failure; quarantining an ambiguous tail can be the correct migration.

# 267. Differential implementation acceptance suite

Two independent implementations run a frozen corpus of semantic operations and compare normalized outputs. The corpus includes every curated failure family plus generated preservation/justification/frame worlds. Exact capability profiles require exact semantic equivalence for correctness fields. Declared capability refinement allows stronger supported results only within the refinement relation.

Differences are classified:

```text
implementation bug
spec ambiguity
capability difference
normalization/profile mismatch
unsupported extension
```

A spec ambiguity is a research finding: the Markdown changes and both implementations add a regression. This process is one of the best defenses against hidden semantics because a single codebase tends to encode its author's unstated assumptions consistently and therefore never reveals them.

# 268. Performance gate: no optimization may weaken the semantic status without changing the returned status

Performance work can safely alter indexes, storage tiering, caching, prefetching, consolidation scheduling and rendering. The semantic gate is simple:

> If an optimization removes the capability needed to justify the previous result, the result status must downgrade or another exact path must compensate.

Examples: an approximate ANN cannot replace an exact hard negative search while keeping `SUFFICIENT`; an index cache that omits revoked deltas cannot claim current; a smaller frame cannot drop a hard role; deferred verification cannot preserve `VERIFIED` promotion; deleting a witness cannot leave `SOURCE_REHYDRATABLE` unchanged.

This gate turns many optimization bugs into ordinary capability/freshness downgrades instead of silent correctness errors. Benchmarks therefore report status distributions, not only latency.

# 269. Benchmark-validity gate: every score must correspond to a claimed memory capability

A benchmark can show higher answer accuracy without demonstrating why. v0.6 requires a mapping from each headline claim to tests that isolate the relevant memory mechanism.

If claiming temporal correctness, include semantic-time/duration updates and `KNOWN_BY/VALID_AT`. If claiming procedural learning, include applicability transfer and negative transfer. If claiming context scalability, separate store size from dependency width. If claiming poisoning resistance, test delayed activation and derivation laundering. If claiming corrigibility, inject future-query counterexamples and measure local repair/recovery.

Generic QA gains remain useful product evidence but cannot discharge specialized semantic claims. This gate prevents the research program from choosing benchmarks simply because they reward the full system.

# 270. Release gate: “implemented” and “research-complete” are different predicates

A future code release may implement a well-tested K2 subset while the research program still has W5 debts about interference or external validity. Conversely a beautiful v0.6 specification does not mean any runtime code exists.

Release metadata should therefore declare independently:

```text
semantic conformance level implemented
property/oracle suites passed
benchmark evidence available
known unsupported capability profiles
open migration/security debt
W5/research closure status
```

This makes progress composable and honest. The team can ship a strong canonical+recall kernel without faking full lifelong effect optimization, and later additions cannot quietly weaken earlier guarantees.

---

# PART XXIII — AUTHORITATIVE CLOSURE MATRIX AND OWNERSHIP

# 271. Purpose of the closure matrix

The closure matrix is the implementation-facing answer to a simple but dangerous question:

> If I am writing code and need to know who owns this state, where is the single normative answer?

Earlier revision history demonstrated why this matters: a document can contain sophisticated ideas yet still leave engineers to invent hidden semantics when no ownership/lifecycle table exists. v0.6 therefore treats the matrix below as normative. Narrative chapters explain *why*; the matrix says *where the state lives and how it is allowed to change*.

Legend:

```text
CANONICAL — correctness-bearing durable authority
DERIVED   — recomputable view/cache; no independent truth authority
POLICY    — authorized versioned policy input
AUDIT     — durable evidence of an operation/judgement, not a truth owner
EPHEMERAL — task/session projection; disposable
```

A primitive can combine roles—for example a commit receipt is canonical audit evidence—but it still has one semantic owner. A physical implementation may normalize or co-locate records. It may not merge meanings in a way that gives derived state an independent writable clock.

A blank/unknown implementation behavior for a correctness-critical matrix cell is specification debt. The correct response is to keep the capability unsupported, not infer a convenient default.

# 272. Canonical-plane closure matrix

| Primitive | Class | Created by | Authority / meaning | Legal evolution | Main invalidation dependencies | Persistence / replay | Model-context behavior | Failure states |
|---|---|---|---|---|---|---|---|---|
| `MemoryAuthorityDomainRevision` | CANONICAL/POLICY | host/runtime authority | boundary of one canonical write order and policy root | revision/split/migration | domain policy/incarnation | durable; new incarnation on restore/split unless proven continuation | normally handle only | domain conflict / migration blocked |
| `MemoryWriterFenceRevision` | CANONICAL/POLICY | writer authority/storage | current writer epoch/fence | monotonic supersession | failover/lease/storage authority | durable or storage-provable | never prompt | `STALE_WRITER` |
| `MemoryWriteIntentRevision` | AUDIT | authenticated producer | immutable requested semantic operation | expires/reconciles; never mutates truth | base/policy/scope revisions | durable for retry horizon | not model truth | stale/conflict/unauthorized |
| `MemoryCommitReceipt` | CANONICAL/AUDIT | correctness writer | proof one semantic transition committed exactly once | immutable | none; effects can be superseded later | durable/replay root | rarely exposed | unknown/reconciliation/integrity error |
| `RetentionEventRevision` | CANONICAL/AUDIT | authorized retention/privacy kernel | archive/delete/accessibility transition and effective erasure barrier for a scoped target | immutable event; reversal only via separately authorized governance transition | target identity, policy authority, retention mode | durable subject to policy; content-free barrier record may survive where allowed | never rendered as factual content | unauthorized/stale target/erasure incomplete |
| `MemoryErasureClosureReceipt` | CANONICAL/AUDIT | erasure/retention closure kernel | proof that declared deletion scope has been propagated to required derived/read/continuity/restore surfaces | immutable receipt for one barrier/cut; superseded by wider closure | retention event, dependency graph, index/cache frontiers, backup/restore policy, rederivation receipts | durable metadata subject to policy | normally hidden; may explain irrecoverable gap | `ERASURE_INCOMPLETE`, `SURFACE_OPAQUE`, `REDERIVATION_REQUIRED` |
| `ExperienceTraceRevision` | CANONICAL EVIDENCE | capture adapter | what source/event/tool actually emitted/observed | append revisions to derived parsing; raw identity stable | source integrity/retention/access | durable subject to policy | source handle/field when needed | unavailable/opaque/integrity error |
| `MemoryOriginBindingReceipt` | CANONICAL | origin binder | non-malleable source identity/authority ceiling | revocation/compromise annotations | source identity/issuer | durable lineage | handle only | origin unknown/compromised |
| `MemoryIntegrityAuthorityProfileRevision` | POLICY | authorized authority | claim/subject/operation-scoped integrity authority | revision/revoke/expire | issuer/policy | durable policy history | normally hidden | insufficient authority |
| `MemoryConfidentialityProfileRevision` | POLICY | authorized authority | discover/read/use/derive/disclose/export constraints | revision/revoke/expire | principal/policy | durable policy history | determines eligibility before recall | `SCOPE_BLOCKED` |
| `MemoryDeclassificationReceipt` | CANONICAL/AUDIT | authorized release authority | explicit permission for broader disclosure of a derivative | revoke/expire | source classification/release procedure | durable if policy permits | not normally rendered | disclosure revoked/reclassify |
| `MemoryPublicationPolicyRevision` | POLICY | source/destination governance authority | legal mapping for cross-domain publication/import: roles, origin, authority, confidentiality, retention, visibility | revise/revoke/expire | issuer/domain/access/declassification policy | durable policy history | normally hidden | publication policy blocked/stale |
| `MemoryPublicationReceipt` | CANONICAL/AUDIT | publication/import kernels | causal source→destination transfer state without claiming global atomicity | source prepared/committed, destination pending/admitted/rejected, revalidation/cancel | source revision, destination policy, declassification, causal frontier | durable until policy permits archival/deletion | handle/status only | `DEST_REJECTED`, `SOURCE_REVALIDATION_REQUIRED`, partial transfer |
| `ClaimRevision` | CANONICAL | admission/truth kernel | normalized proposition + temporal/scope identity | candidate/supported/disputed/superseded/revoked revisions | justification/evidence/regime | durable revision history | rendered through representations | unsupported/conflict/stale |
| `HistoricalJudgementRevision` | CANONICAL/AUDIT | decision/judgement recorder | what principal/system judged at time/cut | immutable judgement; retrospective status can append | historical evidence/procedure refs | durable audit | on demand/recovery | evidence missing/non-replayable |
| `MemoryJustificationRevision` | CANONICAL | truth/admission kernel | OR-of-AND support semantics | add/remove/supersede alternatives via revisions | evidence validity/availability/derivation | durable | summarized handle | no live grounded alternative |
| `EvidenceIndependenceRevision` | CANONICAL/DERIVED RECEIPT | independence evaluator | bounded claim about origin/common-mode dependence | re-evaluate/downgrade/upgrade by new evidence | provenance/failure-mode/profile | durable receipt | rarely rendered | unknown dependence |
| `MemorySupportBundleRevision` | CANONICAL DERIVATION | truth kernel | normalized live support/assurance view | recompute from canonical justification | evidence/profile/counterexample | durable/recomputable revision | compact confidence/status | stale/recompute required |
| `CounterexampleApplicabilityRevision` | CANONICAL RELATION | admission/evidence kernel | scope in which negative evidence falsifies target | revise scope/status/regime | target/source/regime | durable | protected recall role | stale/not applicable |
| `PrincipalMemoryAccessProfileRevision` | POLICY | authorized host/org/user policy | operation-specific principal rights | grant/revoke/expire | issuer/principal | durable policy history | prefilter only | scope denied |
| `MemoryRegimeRevision` | CANONICAL/POLICY | environment/runtime evidence | applicability environment/model/tool/schema regime | supersede/fork | sensed/current environment | durable history | compact current-regime fact | unknown/stale regime |
| `SelfVersionProfileRevision` | POLICY/OBSERVED PROFILE | host capability/model registry | consumer/model/tool-runtime capability identity used to judge representation/procedure/effect compatibility | revise/supersede on model/tool/runtime change | model/tool capability evidence, runtime version | durable profile history | referenced by resolver/boot; rarely rendered | unknown compatibility/revalidation required |

Every durable correctness-bearing row in this matrix also obeys the v0.6.1 identity header law: stable `logical_id`, immutable `revision_id`, explicit predecessor for semantic mutation, commit identity, and incarnation/epoch where ABA is possible. `CREATE` is never an untyped shortcut for `REVISE`, `SUPERSEDE`, `REVOKE` or `REACTIVATE`.

The canonical plane contains more records than a traditional “memory database,” but they are not multiple memory types. They are the minimum durable semantics needed so later compression and recall can remain correctable.

# 273. Representation-plane closure matrix

| Primitive | Class | Created by | What it owns | What it must never own | Invalidation | Persistence | Recall use | Failure/debt |
|---|---|---|---|---|---|---|---|---|
| `SemanticRegionRevision` | CANONICAL STRUCTURAL/DERIVED BOUNDARY | segmentation/repair kernel | revisioned repair/transformation neighborhood + split/merge lineage | truth or logical identity of member claims/evidence | boundary/source/profile change | durable revision + predecessor/successor mapping | discovery/repair locality | merge/split/ambiguous-successor/revalidate |
| `RepresentationRevision` | DERIVED DURABLE | transform/consolidation | format, granularity, role tags, source lineage | claim authority | source/transform/query-basis change | durable/cacheable | candidate materialization | stale/candidate/invalid |
| `TransformationContractRevision` | POLICY/DERIVED PROCEDURE | trusted transform registry | declared transformation semantics/capability | source truth | procedure/normalizer change | durable profile | resolver/verification | unsupported/unsafe profile |
| `SemanticLossVectorRevision` | DERIVED RECEIPT | preservation verifier | dimension-specific loss state | universal fidelity | source/transform/basis change | durable/recomputable | resolver evidence | `UNKNOWN/LOST` |
| `PreservationEnvelopeRevision` | DERIVED CERTIFICATE | preservation verifier | query-family/property answerability | future-query universal safety | source, basis, verifier, transform | durable certificate | hard representation selection | stale/unknown/lost |
| `RecoverabilityCertificateRevision` | DERIVED/CANONICAL DEPENDENCY RECEIPT | retention/preservation kernel | available source/witness route | factual truth | source availability/deletion/policy | durable/recomputable | semantic page fault | unavailable/irrecoverable |
| `MemorySemanticDebtRevision` | CANONICAL AUDIT/CONTROL | verifier/maintenance/migration | known unresolved semantic risk | proof that risk is resolved | explicit discharge event only | durable subject to policy | may force rehydrate/insufficiency | open/waived/destroyed-by-policy |
| `MemoryQueryCounterexampleRevision` | CANONICAL RESEARCH/REPAIR EVIDENCE | recall/verification | witnessed failure of representation capability | automatic falsity of canonical claim | stronger evidence / repair lineage | durable regression witness | forces revalidation | unresolved/irrecoverable |
| `MemoryEffectEvidenceRevision` | DERIVED EMPIRICAL | experiment/effect ledger | scoped evidence of behavioral effect | factual/epistemic authority | consumer/task/regime/rendering change | durable empirical ledger | optional selection guard | undercalibrated/confounded |
| `MemoryActivationGuardReceipt` | DERIVED/AUDIT | interference/security layer | current eligibility/inhibition decision | hard-role existence, truth, or sink authorization | effect/security/access revision | short-lived/auditable | filters optional render; blocked hard role remains unresolved | warn/quarantine/scope-blocked/insufficient |

Role labels such as `episodic`, `semantic`, `procedural`, `failure`, `anchor`, `prospective` and `self-version` are contracts/tags over these objects. They are not additional canonical stores.

# 274. Projection-plane closure matrix

| Primitive | Class | Owner | Scope/lifetime | Authority | Dependency/freshness | Consumer behavior |
|---|---|---|---|---|---|---|
| `RecallBoundaryDescriptor` | EPHEMERAL/AUDITABLE | host/runtime consequence boundary | one contemplated decision/action/tool/sink boundary | no truth; enumerates memory dependency surfaces | task/principal/action/tool schema/risk/policy | basis for proactive hard-role compilation |
| `RecallObligation` | EPHEMERAL/AUDITABLE | runtime/consumer boundary | one bounded decision/action contract, revisioned during local closure | defines hard/optional roles, not truth | boundary/principal/regime/profile + discovered hard dependencies | drives recall feasibility/fixed-point closure |
| `RecallCutRevision` | EPHEMERAL/AUDIT | recall kernel | one coherent single-domain or causally closed multi-domain vector view | no new truth | per-domain incarnation/seq/root + causal publication edges + access/regime/procedure profiles | pins staged strong hydration; partial frontier yields partial/unknown |
| `MemoryQueryDomainRevision` | EPHEMERAL/DERIVED | query compiler | one bounded searchable domain | no truth | scope/form/tier/incarnation/capability | bounds completeness claims |
| `QuerySnapshotCompletenessReceipt` | AUDIT | query procedure | one predicate/domain/cut execution | bounded absence evidence only | snapshot/procedure/pagination | allows `NO_MATCH_COMPLETE_DOMAIN` |
| `NegativeRecallDependencyRevision` | DERIVED/AUDIT | recall/cache | lifetime of one cached negative/absence result | no truth | predicate + bounded domain + cut/vector + frontier/absence generation + principal/profile | matching/currentness change invalidates before strong use |
| `RegionDiscoveryResult` | EPHEMERAL | discovery engine | one recall | candidate relevance only | index capability/cut | feeds resolver |
| `RepresentationResolution` | EPHEMERAL/AUDIT | resolver | one region/obligation/cut | no truth | envelope/recoverability/cost | choose/use/page-fault/insufficient |
| `RecallReconstruction` | EPHEMERAL/AUDIT | reconstruction engine | one recall | inferred bridges remain inferred | source/evidence/cut | set of candidate histories/claims |
| `RecallSufficiencyAssessment` | EPHEMERAL/AUDIT | frame compiler | one consumer contract | certifies coverage only | obligation/manifest/cut | `SUFFICIENT/...` typed outcome |
| `RecallFrameDependencyManifestRevision` | AUDIT | compiler/semantic-OCC validator | frame/proposal/certificate lifetime | no truth | material semantic property revisions/generations + completeness class + compatibility validators | explain/revalidate/rebase derived result without global invalidation |
| `RecallFrameDescriptor` | EPHEMERAL | compiler | model invocation/decision scope | no canonical memory authority | manifest | bounded model context + handles |
| `FrameInformationFlowReceipt` | AUDIT | projection/security gate | one composed model/user/tool/export payload | certifies sink authorization only, never factual truth | source confidentiality, principal, declassification, sink capability, composed semantics | allow/rewrite/block; blocked hard roles force sufficiency recomputation |
| `MemoryUseFence` | EPHEMERAL/AUDITABLE | memory-use validator + host dispatcher | one exact consequential model/tool/user/export use; normally single-use/short-lived | certifies current memory grounding only; **not factual truth and not action authorization** | frame/manifest, validated cut/dependency digest, principal/sink, exact final payload/action digest, policy/tool generations, hard-role closure, optional trusted clock epoch/expiry | atomically validate/consume at consequence boundary; stale/mismatch/replay blocks use |
| `ContinuityPinRevision` | CANONICAL POINTER/AUDIT | recovery kernel | across context/session reset; binds canonical cut/root, protected hard continuity roles, blockers and stable refs | pointer/representation, not truth store | payload integrity, canonical cut/root, objective/mission, source, access, self-version, environment | candidate boot reconstruction seed only after compatibility checks |
| `RecoveryResumeAssessment` | EPHEMERAL/AUDITABLE | recovery kernel | one boot/restore attempt | certifies resume eligibility only, never historical truth | storage integrity, canonical replay, semantic migration, erasure/revocation barriers, continuity pin, mission/self-version/environment, Recall Sufficiency | `RESUME_ALLOWED` or first typed blocked/degraded layer |

The projection plane should be cheap to discard. Persisting selected audit descriptors is useful; promoting them into canonical truth would recreate the exact “summary becomes memory authority” failure v0.6 is designed to avoid.

# 275. Derived index and cache ownership matrix

Derived indexes are treated uniformly despite different data structures.

| Surface | May own | Must reference | May never certify alone | Required recovery |
|---|---|---|---|---|
| lexical/FTS | term postings/ranking stats | representation/canonical revision IDs + index generation | truth, global absence outside capability | rebuild from durable state |
| dense ANN | embeddings/neighborhood | representation digest + embedding/index profile | exact completeness / authority | re-embed/rebuild |
| typed graph index | adjacency/path cache | canonical edge/revision IDs | causal truth merely from reachability | rebuild typed edges |
| temporal index | interval/query acceleration | canonical temporal revisions | knowledge/history semantics not represented | rebuild intervals |
| entity index | alias/identity candidates | canonical entity/claim refs | merge certificate from label equality | split/merge repair |
| procedure index | applicability candidate retrieval | procedure representation + regime/capability | procedure validity from score | rebuild/filter |
| counterexample index | negative-evidence target lookup | applicability relation refs | global relevance | rebuild scoped relations |
| frame/result cache | compiled projection | full dependency manifest | currentness without dependency compatibility | recompile |
| activation state | associative dynamic weights | scoped memory IDs/profiles | truth/authority | recompute/decay |

Every index publishes a capability profile and visibility/generation state when correctness depends on freshness. A derived index can be operationally critical yet epistemically non-authoritative.

# 276. State-transition ownership: which operations may change which dimensions

The product-state model becomes implementable only when transitions have bounded write sets.

| Operation | Epistemic | Temporal | Availability | Access | Applicability | Retention | Recoverability | Activation/Effect |
|---|---|---|---|---|---|---|---|---|
| new evidence | may update through justification | may add valid interval | source available | no implicit change | may affect conditions | no | may add witness | optional utility update |
| contradiction/correction | dispute/supersede | revise intervals | no | no | may narrow | no | usually unchanged | cache/effect stale |
| consolidation | **no direct authority creation** except admitted derived claim | no source time rewrite | add representation | inherit/restrict | explicit scoped contract | add derived object | may improve compact recovery | new rendering profile |
| archive | no | no | slower/cold | no | no | `COLD` | remains rehydratable if source intact | activation may fall |
| hard delete | may lower support if source needed | history fact of deletion | unavailable | content inaccessible | downstream may fail | deleted | may become irrecoverable | remove current exposure |
| erasure closure | no factual authority change by itself | preserves policy-safe deletion history | tainted derived views purge/rederive | disclosure blocked until clean | affected applicability/read paths revalidate | closes declared surfaces | recoverability recalculated | current exposure allowed only after closure |
| semantic rollback | authorized older factual/representation revision may become current through new transition | historical judgements preserved | selected version reactivated through typed revision | current policy still applies | regime compatibility rechecked | no implicit undelete | witness/recoverability recomputed | effect profiles revalidated |
| governance barrier after snapshot | current truth evaluated under surviving evidence | historical snapshot remains valid history | pre-barrier representation cannot become current-usable automatically | access/declassification current barrier wins | compromised/revoked scope blocked | deletion remains effective | old source remains unavailable unless explicitly reauthorized where legal | cached effects/frames stale |
| access revoke | no truth rewrite | no | no | deny | no | no | principal-relative hydration blocked | invalidate frames |
| regime change | no historical rewrite | current applicability projection changes | no | no | re-evaluate | no | no | procedure/effect caches stale |
| model upgrade | facts normally unchanged | no | no | no | procedures/effects re-evaluate | no | no | activation/effect reset/downrank |
| query counterexample | canonical claim only if evidence contradicts it | no by itself | no | no | may refine representation/procedure | protect witnesses | repair/rebase state | effect may update separately |
| same-ID create/re-propose | **no semantic mutation**; idempotent only if creation meaning matches | no | no | no | no | no | no | no lifecycle reset; collision otherwise |
| typed revise/supersede/reactivate | only through object-specific transition + expected predecessor/live justification | may revise declared interval | type-specific | type-specific | type-specific | type-specific | recompute | dependent guards/caches stale |
| region split/merge | no claim truth rewrite | no | representation locality evolves | no | locality/applicability refs remap | no implicit deletion | witness routes remap/revalidate | discovery caches stale |
| cross-domain publication/import | destination epistemic state changes only after destination admission | source/destination judgement contexts preserved | publication availability evolves | mapped by policy | destination regime checked | mapped retention obligations | source handles required | shared visibility/effect remains scoped |

An implementation can split one logical operation across storage tables, but the atomic semantic transition must match this bounded write set. This table is a direct defense against accidental category coupling.

# 277. Invalidation dependency matrix

Invalidation is driven by **which property a dependency supports**, not one generic edge type.

| Changed dependency | Claims | Historical judgements | Representations | Preservation envelopes | Recall caches | Procedures | Effect profiles |
|---|---|---|---|---|---|---|---|
| source factual revocation | recompute live justifications | preserve judgement, update retrospective assessment | revalidate descendants | revalidate | stale | revalidate if source supports | maybe stale if exposure meaning changed |
| source deletion only | assurance may drop if no alternative | preserve if policy permits | content/source refs may become unavailable | recoverability downgrade | stale | may remain factually supported via other source | no causal conclusion by itself |
| post-snapshot deletion/revocation/compromise | current support/use recomputed | preserve historical snapshot/judgement as policy permits | old representations may be tainted/unusable | invalidate affected envelopes/rehydration | all pre-barrier frames/continuity artifacts stale for current use | applicability/access barrier dominates restore | effect exposure history preserved but future use blocked/revalidated |
| continuity pin payload/cut mismatch | no truth rewrite | historical pin remains audit artifact | pin unusable until regenerated/reconciled | pin-linked capability cannot certify recovery | recovery frame invalid | mission/self-version/environment revalidation | no direct effect inference |
| self-version change | external factual support generally unchanged | preserved | consumer-dependent representations may revalidate | semantic preservation only if model-independent | old consumer-bound frames stale | procedure/effect compatibility rechecked | effect profile downgraded/recalibrated |
| transformation profile change | no direct claim change | none | dependent representations stale | invalid | stale | representation role stale | rendering-specific effects stale |
| query-family basis expansion | no | no | representation itself may remain | old exactness incomplete/stale | recompile | if procedure query contract changed, recheck | no direct effect |
| principal ACL change | no | historical access semantics preserved | no intrinsic semantic change | no | principal frames stale | usability changes | exposure profile may change |
| regime change | historical claims preserved | preserved | role applicability re-evaluated | only regime-dependent certificates | stale current frames | often stale/inapplicable | stale if regime-scoped |
| model/consumer change | no | preserved | semantic preservation usually unchanged | verifier/model-dependent certs may recheck | recompile | executor-sensitive recheck | invalidate/downrank |
| counterexample added | target claim/procedure may dispute/narrow | preserved | related abstractions revalidate | affected dimension invalidated | stale relevant frames | applicability/support update | optional effect update only with behavioral evidence |
| semantic identity collision detected | quarantine/conflict; never last-write-wins | preserve prior judgement/revision | dependent views stale until identity resolved | certificates bound to ambiguous object invalid | stale | revalidate | no direct causal effect |
| region split/merge | member claims unchanged | preserved | remap/revalidate locality descendants | rebind region-scoped envelopes | stale affected discovery/frame caches | applicability only if region boundary was material | effect refs follow semantic target |
| declassification/access revoke | no factual truth rewrite | preserve historical policy state | representation bytes may remain | no intrinsic fidelity change | principal/sink frames stale | usability/disclosure changes | exposure profile invalidated |
| source publication basis revoked while destination pending | source judgement recomputed normally | preserved | destination import candidate revalidate | imported representation cannot strengthen | pending/shared frames stale | destination admission blocked/rechecked | destination effect not promoted |

The matrix deliberately shows many “no” cells. Broad invalidation is not safety if it destroys valid independent state and creates unnecessary maintenance churn.

# 278. Authority/write-access matrix

Who may **propose**, **grant semantic authority**, **attest current memory grounding**, and **authorize an external action** are distinct.

| Actor/surface | Capture evidence | Propose | Admit factual authority | Change access/declassify/retention | Validate current memory grounding | Authorize external action | Commit canonical memory |
|---|---|---|---|---|---|---|---|
| model resident | scoped channel | yes | no self-admission | request only | proposes dependencies only | no | no |
| tool adapter | observation contract | structured candidates | only via admitted trusted-observation semantics | no | supplies current tool/schema/capability evidence | no by memory alone | no |
| user/human | authoritative for scoped intent/preference; evidence otherwise | yes | subject/policy scoped | where authorized | can reaffirm/source dependency evidence | where host grants | via kernel |
| verifier | verification evidence | yes | declared verifier obligations only | separately authorized only | can discharge declared currentness checks | no unless separately granted | no |
| host/institution policy | policy/environment evidence | yes | policy scoped | yes | owns principal/sink/tool/current-policy generations | yes | through writer |
| correctness writer/dispatcher | no new evidence | no content judgement | executes admitted transition | applies authorized transition | atomically validates/consumes memory-use fence | does not invent action authority | yes |

`MemoryUseFence` is **not an action credential**. It attests that memory grounding, hard-role cover and information-flow assumptions for one concrete boundary remain current. Ordinary host authorization can still deny. Conversely, ordinary authorization cannot make stale memory grounding current.

A remembered instruction cannot grant network/payment/filesystem capability. A tool being exposed cannot prove the exact model-emitted recipient/amount/path is authorized. Adequacy, disclosure authority and action permission meet at use time but keep separate owners.

# 279. Replay/forensic matrix

Replay and rollback have different meanings across memory dimensions. v0.6.2 therefore extends the forensic vocabulary:

```text
EXACT_SEMANTIC_REPLAY
    reconstruct the same canonical normalized state under bound profiles

HISTORICAL_JUDGEMENT_REPLAY
    reconstruct what was judged/available at the historical cut

CURRENT_REEVALUATION
    interpret surviving canonical history under current evidence/policy

SEMANTIC_ROLLBACK
    select an older factual/representation version as current by an authorized
    memory-correction transition

RESTORE_BARRIER_REQUIRED
    snapshot is authentic but predates delete/revoke/compromise/declassification
    barriers that must be applied before current use

UNAVAILABLE_BY_POLICY
    required source was legally deleted or access has been revoked

NON_HERMETIC_REPLAY
    live dependency was never captured and cannot be exactly reconstructed
```

A global “go back to version 12” operation is not allowed to rewind every dimension indiscriminately. Semantic rollback can intentionally restore an earlier user preference, correction state or representation lineage. It does not automatically reverse privacy deletion, access revocation, source compromise or declassification revocation. Reversing those governance barriers requires a new authorized governance transition, when policy even permits reversal.

This distinction matters for backups. A checkpoint taken before deletion can be cryptographically perfect and semantically faithful to its old cut. On recovery after the deletion event, the restored state must replay/apply the deletion barrier or quarantine the old payload before it becomes queryable. If the deletion ledger/barrier history required for safe recovery is unavailable, the runtime fails closed for that scope rather than choosing the old snapshot as “last known good.”

Replay integrity therefore answers **what history did these bytes represent?** Resume/rollback authority answers **which parts of that history may become current again?** Those questions share evidence but must never share one implicit writable clock.

# 280. No-two-writable-clocks audit

Before release, every mutable correctness property is audited for **duplicate authority and unenforced authority**.

Duplicate-clock smells include:

```text
claim.status writable in truth store and procedure store
summary validity independent from source/regime revision
old backup acting as current authority after delete/revoke
publication queue acting as destination truth owner
continuity anchor list order acting as freshness authority

compile-time Recall Sufficiency treated as permanent use-time liveness
proposal eligibility treated as permanent promotion authority
action lifecycle phase treated as proof memory preconditions are live
nested query helper refreshing "latest" inside an older strong-cut result
```

Decorative-correctness smells include:

```text
expires_at exists but caller can omit current-time evaluation
invalidates_on exists but recall never evaluates its event
context-scoped exists but route() ignores requested context
authorization_ref exists but no policy generation/currentness is checked
hard_role exists but budget truncation can remove it
```

For every correctness field/transition the audit asks: who owns it, which mandatory path evaluates it, which cut/generation makes that evaluation fresh, what happens if required authority/clock/source is unavailable, whether a derived result can outlive a material dependency change, whether nested reads can cross cuts, and whether final action arguments can change after memory validation.

A cache/label without an evaluator is `ADVISORY_METADATA`, not a certified invariant. v0.6.3 strengthens the no-two-clocks rule: **every correctness clock has one authoritative owner and at least one mandatory reader at the boundary where its truth matters**.

# 281. Migration principle: reuse tested semantics, retire duplicated ownership

The existing Nolane World codebase already contains valuable memory, truth, recovery and transactional machinery. Rewriting everything would discard tested behavior and create unnecessary implementation risk. Copying all memory modules would preserve the exact fragmentation v0.6 is trying to eliminate.

The migration strategy is therefore **selective semantic extraction**. Each existing surface is mapped to one of:

```text
CANONICAL_REUSE
DERIVED_ADAPTER
MIGRATION_SOURCE
REGRESSION_SEED
DEPRECATED_AUTHORITY
OUT_OF_SCOPE
```

`WorldStoreV5`-style CAS/idempotency becomes a canonical-reuse pattern. Truth-maintenance alternative justifications are generalized into the claim kernel. Recovery bootloader semantics seed continuity. Existing memory taxonomies and experience libraries become migration sources/adapters until their data is converted into regions/representations and canonical evidence identities. Known counterexamples become regression seeds and cannot be silently “fixed” only in old code.

The goal is a gradual path where old APIs remain readable during transition but stop owning new correctness state. A compatibility adapter may synthesize a `LivingMemoryV5`-like view from new canonical/representation state; it may not write directly to legacy confidence/status fields and then back-propagate them as truth.

# 282. Extraction map from Nolane World source surfaces

| Existing surface | v0.6 destination | Migration action |
|---|---|---|
| `v5/store.py::WorldStoreV5` | commit/idempotency pattern | extract semantic protocol; physical implementation may be reused initially |
| `living/truth_maintenance.py` / truth graph | `ClaimRevision` + `MemoryJustificationRevision` | preserve alternative proof paths; strengthen temporal/scope dependencies |
| raw experience ledgers | `ExperienceTraceRevision` | import source-event identity where reliable; mark legacy ambiguity otherwise |
| `living/experience.py::ExperienceLibrary` | representation/procedure candidate source | stop row-count authority; migrate event IDs/applicability slices |
| `v5/memory.py::LivingMemoryV5` | legacy view over claims/representations | migrate text/kind/support/provenance; recompute support/authority |
| `v5/cognitive_memory2.py` | abstraction/migration source | preserve abstraction level as role metadata; remove caller-owned canonical authority |
| `v5/memory_consolidation.py` | transformation candidate engine | retain lineage/counterexample ideas; replace self-reported loss with verifier contract |
| temporal memory modules | temporal claim/region projection | migrate observed/valid semantics; unknown old intervals stay bounded/unknown |
| cognitive graph | derived multi-view index | rebuild from canonical typed edges; no truth ownership |
| QX durable memory / anchors | role-tagged representations + continuity pins | preserve failure/decision/anchor lineage; current authority revalidated |
| recovery kernel / bootloader | recovery protocol | reuse drift/environment checks; rebind to new cut/pin records |
| `memory/journal.py::HashJournal` | regression seed / diagnostic format | do not use as concurrent canonical writer without serialization redesign |

The map is intentionally semantic rather than file-for-file. A single old module may feed several new representations while losing its authority role.

# 283. Phase M0 — freeze old semantic writes and inventory state

Before migration code touches data, the project needs a semantic inventory. Identify every old API that can create/update memory, status, support, confidence, procedure or anchor state. Record which stores are current sources of truth and which are caches.

M0 produces:

```text
legacy object count by type
write-path inventory
source/event identity availability
provenance/lineage quality
status/temporal field semantics
principal/scope metadata availability
raw artifact retention state
known duplicate/alias support patterns
known caller-owned authority fields
```

The key operational step is to define a **write freeze boundary**: after date/version X, new correctness-bearing writes go only through the new K0 kernel. Legacy modules can continue reading and can receive derived compatibility projections.

Without this boundary migration becomes bidirectional synchronization between incompatible semantics, creating two writable clocks. If immediate freeze is impossible, every legacy write must be wrapped as a new canonical `MemoryWriteIntent` and then projected back, never the reverse.

# 284. Phase M1 — establish canonical K0 before migrating abstractions

M1 builds the smallest deterministic core: authority domains, operation idempotency, source-event/origin identity, claims, historical judgements, justifications, temporal state, access policy and commit receipts.

Legacy raw evidence/claims are imported conservatively. Where source identity is uncertain, the migration records `UNKNOWN_DEPENDENCE`; it does not infer independence from distinct strings. Where a legacy “semantic” record has trusted support but no reconstructible evidence, it can become a historical/candidate claim with an assurance ceiling rather than current verified truth.

M1 must pass the canonical-commit suite before any new consolidation writes are enabled. This sequencing protects against building sophisticated v0.6 representations over a foundation that can duplicate events or lose updates.

At the end of M1, old memory views can be generated from new claims/evidence even though preservation envelopes and semantic virtual-memory recall are not implemented yet.

# 285. Phase M2 — import representations and attach explicit source lineage

M2 converts legacy episode/semantic/procedural/failure/anchor objects into `RepresentationRevision` objects grouped into semantic regions. The migration does not assume old taxonomy levels imply preservation quality.

For each imported representation:

- identify exact canonical source refs when possible;
- bind role tags and applicability/regime metadata;
- record transform origin (`LEGACY_UNKNOWN_TRANSFORM` when necessary);
- generate a conservative initial preservation envelope;
- mark unverified dimensions `UNKNOWN` rather than guessing;
- compute recoverability from surviving sources/artifacts;
- add semantic debt for missing provenance or uncertain scope.

Old summaries may remain useful for retrieval immediately. They simply lose authority to claim exactness outside what can be established.

This phase is where v0.6 improves quality without destroying usefulness: legacy memory is not discarded; it is reclassified into a safer epistemic position.

# 286. Phase M3 — replace legacy retrieval with obligation-driven projection

Once enough regions/representations exist, the new recall compiler can run in shadow mode beside the old retrieval path. For each request, record:

```text
old retrieved items
new discovered regions
new resolved representations
hard-role coverage
page faults
frame tokens
normalized downstream decision/answer
```

Disagreements are classified. Sometimes the new path catches a missing counterexample or exact field; sometimes the old path finds useful evidence the new region discovery misses. Both are research signals.

Only after shadow evaluation should the model-facing path switch to K2 semantics. The old search API can remain as a derived/tool endpoint but must clearly expose its weaker capability (for example “candidate search,” not strong recall sufficiency).

This gradual replacement reduces the risk of a big-bang retrieval regression while producing exactly the counterexamples needed to refine query-family and discovery policies.

# 287. Phase M4 — enable consolidation/forgetting only after preservation and witness contracts exist

A common migration temptation is to switch on the new consolidator immediately and use it to “clean” old memory. v0.6 forbids that ordering. Destructive optimization begins only after M2/M3 can state what every representation preserves, which dimensions a future obligation may require, and which witness/source paths can restore a lost distinction. Before those contracts exist, compression merely converts visible legacy debt into harder-to-detect loss.

M4 enables verified transformation contracts, preservation envelopes, semantic-loss composition, semantic debt, source rebase, query-counterexample repair, witness-cover retention and fixed-point maintenance. The first deletion targets are redundant **derived** representations whose source lineage and alternative witnesses are already certified. Raw evidence, unique exact values, rare counterexamples and ambiguous historical records receive conservative treatment because their option value can be high even when recall frequency is low.

Retention policy first runs in dry-run mode. For every proposed deletion the runtime calculates the affected preservation basis and reports dimensions that remain exact, become source-rehydratable or cross into `IRRECOVERABLE_GAP`. Deleting the last protected witness is blocked unless an authorized privacy/retention policy explicitly accepts the loss; that transition creates a capability downgrade/debt rather than pretending the capability survives.

Post-delete verification replays the relevant query-family witnesses and reconstruction paths. Forgetting is therefore a verified capability transition, not garbage collection.

# 288. Phase M5 — continuity, self-version and shared-memory migration

QX durable memory/anchors and multi-agent/project history are migrated after core truth/representation semantics are stable. A legacy handoff note becomes evidence/representation with source principal and historical cut rather than a current command.

Shared memories are re-published through governed cross-domain admission. Common upstream origins are preserved so multiple agent copies do not become new corroboration. Principal/private data is filtered before any shared retrieval path; old debug/hydration APIs are audited for parity.

Continuity pins are then generated from canonical objective/constraint/hypothesis/failure refs. Boot tests compare recovered decisions to bounded full-history references and deliberately change environment/model versions to verify revalidation behavior.

# 289. Compatibility adapters: old APIs may survive as views, not alternate semantic writers

Practical migration often requires existing UI/tests/integration code that expects structures such as:

```text
memory.kind
memory.text
memory.confidence
memory.status
trusted_support
counterexample_to
```

A compatibility adapter can derive these fields from v0.6 state. For example, `status` is a lossy projection over product state and should be labeled as such; `confidence` can expose a normalized current assurance view; support returns canonical evidence/justification IDs.

Writes through old APIs are either disabled or translated into canonical intents with the new admission rules. A call to `add_support()` cannot increment confidence directly; it proposes/appends a semantic evidence identity and recomputes the support bundle.

This approach keeps ecosystem compatibility while ensuring legacy simplifications cannot regain authority.

# 290. The do-not-inherit regression suite is a permanent migration artifact

Every source counterexample discovered during research becomes a named **semantic regression**, not merely a test of the legacy class that happened to contain the bug. The permanent suite is the regression set already enumerated in the source-audit part of this document—concurrent journal chain corruption, duplicate-support confidence inflation, alias-lineage independence, caller canonical bypass, global counterexample pollution, duplicate experience support, critical compression silent drop, applicability support leakage and self-reported abstraction loss.

Each regression preserves four things: the smallest counterexample world, the violated invariant, the naive behavior that must remain rejected and the current kernel path expected to block/classify it. `REG-CRITICAL-COMPRESSION-SILENT-DROP`, for example, is not “test the old compressor.” It means that when hard obligations exceed representable frame budget, the runtime must return overflow/insufficiency or a semantically equivalent explicit state rather than silently remove a hard role. That obligation survives replacement of the original class.

The suite acts as institutional memory for the implementation. Refactors often recreate shortcuts whose original rationale has been forgotten: count rows instead of semantic events, labels instead of origins, `max(seq)` instead of a contiguous durable frontier, or a summary score instead of a preservation certificate. A regression remains until the invariant is explicitly superseded by a newer formal contract and migration path; deleting legacy code is not grounds to delete the semantic counterexample.

# 291. Rollback strategy: canonical migration commits must be reversible at the state level

Schema/data migration can be code-correct and semantically wrong. Migrations therefore produce a root/digest and mapping manifest so the runtime can restore the pre-migration canonical state or run old/new views in parallel during validation.

Rollback does not mean reusing old active incarnation identifiers after partial external writes. The rollback creates a new controlled active state referencing the historical root, with caches/indexes rebuilt under compatible profiles. External side effects such as deleted privacy data cannot be magically restored; the rollback report must identify irreversible operations.

The migration process should delay destructive source deletion until new semantic projections have passed acceptance gates, reducing irreversible rollback surfaces.

# 292. Migration success criteria are semantic, not “all rows converted”

A successful migration demonstrates:

- every active correctness property has one current owner;
- no legacy write path can mutate an alternate authority clock;
- current/historical truth queries have defined mappings;
- principal access is consistent across all new/compatibility reads;
- support/independence is recomputed conservatively;
- legacy representations have source/recoverability/debt state;
- hard Recall Obligation tests do not silently truncate;
- known regressions remain reproduced as failures of naive semantics and pass under the new kernel;
- source deletion/retention consequences are explicit;
- rollback/replay artifacts exist.

A 100% converted row count with ambiguous authority is migration failure. A smaller migrated active set with quarantined/unknown legacy debt can be the safer intermediate state.

# 293. Implementation order after v0.6 research closure target

The recommended code order follows dependency rather than visual product appeal:

```text
1. K0 canonical commit/evidence/claim/justification/access/time kernel
2. source-counterexample regression tests
3. K1 regions/representations/preservation/recoverability/debt
4. formal preservation calculus ported to implementation property tests
5. K2 obligation/cut/region discovery/representation resolution/frame compiler
6. shadow evaluation against long/full-context reference
7. K3 maintenance/repair/witness retention/recovery
8. K4 effect/security/shared/self-version layers
9. associative/prospective/learned routing optimization
10. performance/storage engineering and production rollout
```

This deliberately postpones the visually exciting mechanisms. A spreading-activation graph is far easier to add safely after the authority/preservation/frame contracts exist than to retrofit correctness under an already popular product.

# 294. TDD discipline for the future kernel

Each new semantic behavior starts with the smallest failing case. Examples:

- before implementing support dedupe, reproduce duplicate delivery inflation;
- before writer concurrency, reproduce same-base lost update;
- before preservation certificates, construct dropped safety precondition;
- before witness deletion, construct one last exact-number source;
- before hard-frame compiler, create more critical roles than budget;
- before query-domain caching, create a phantom insert that matches an old empty predicate.

Only after the minimal regression is green should optimization/fuzz tests be added. This preserves causal understanding: the team knows which code change made which invariant hold.

The specification's oracle corpus provides seeds, but implementation tests should live beside code and use the actual persistence/index paths, not a mock that cannot exhibit the relevant race or storage failure.

# 295. Verification-before-completion discipline

A development wave cannot be declared complete because code compiles or unit tests for touched modules pass. The release checklist executes, at the implemented conformance level:

```text
static/schema ownership audit
unit + regression tests
state-machine/property fuzz
crash/restart/idempotency tests
migration/replay fixtures
scope/security read-path tests
bounded full-history decision equivalence
context/dependency-width tests
performance tails
```

The exact command output, test selection and limitations are recorded. If a full suite times out, the report says so; a focused 94-test pass is not relabeled a full repository pass. This evidence discipline mirrors the research document's own handling of Nolane World verification.


# PART XXV — OPEN DEBT AS PART OF THE ARCHITECTURE, NOT A FOOTNOTE

# 296. Research debt is a first-class boundary on what the runtime is allowed to claim

The W5 session for v0.6 remains `BLOCKED` with seven open epistemic debts. v0.6 deliberately carries these debts into the architecture instead of trying to erase them by adding more prose. A debt is not a missing feature. It is a claim boundary where the present specification can define safe behavior but cannot yet justify the strongest possible capability claim. This distinction matters because a long-lived memory runtime can become unsafe by **overstating what its own representation can guarantee** even when every stored byte is valid.

The seven current debts are: future-query basis, preservation composition, local-repair closure, interference calibration, witness-cover optimality, capability refinement and external validity.

Their machine-readable W5 kinds are:

```text
future-query-basis
preservation-composition
local-repair-closure
interference-calibration
witness-cover-optimality
capability-refinement
external-validity
``` Their severities and provenance are recorded in the W5 snapshot. They affect different layers. Future-query basis limits universal preservation claims; preservation composition limits how strong a descendant representation may claim to be; repair closure limits how local a correction may remain; interference calibration limits how aggressively empirical harm may inhibit memory; witness-cover optimality limits cost claims, not basic safety; capability refinement limits reuse between representation profiles; external validity limits transfer from bounded host models to natural-language production behavior.

The kernel therefore distinguishes **semantic closure** from **research closure**. Semantic closure means an implementation has a defined, fail-visible result for the represented states. Research closure would additionally require independent evidence that the chosen contracts are adequate and performant in the target world. v0.6 aims for the former while explicitly refusing to claim the latter. This makes debt operational: a certificate, benchmark report or product claim whose scope crosses an open debt must downgrade, narrow its scope or demand new evidence rather than silently inheriting confidence from unrelated passing tests.

# 297. Future-query basis: preservation is always relative to a declared semantic basis

No finite external memory can prove that a compact representation preserves the answer to **every future question an open-ended agent might invent**. Such a claim would require a complete model of future query semantics, which defeats the purpose of general agency. v0.6 therefore defines preservation against a bounded `PreservationBasisRevision`: a versioned set of semantic dimensions, query families, protected obligations and interpretation profiles that the representation contract knows how to reason about.

For representation `r` and basis `B`, the meaningful statement is:

\[
Preserves(r,B) \in \{EXACT,\ BOUNDED,\ SOURCE\_REHYDRATABLE,\ UNKNOWN,\ LOST\}
\]

not “r preserves the memory.” A summary may be exact for current entity identity and broad temporal order, source-rehydratable for an exact number, unknown for a future causal counterfactual and lost for an intentionally deleted fine-grained formatting detail. When a new query family `q_new` arrives outside `B`, the safe state is `UNKNOWN_BASIS`, followed by semantic page fault, source hydration or query-counterexample refinement. The runtime does not inherit `SAFE` from neighboring families.

This boundedness is not a weakness to hide. It is what makes the contract falsifiable. A future query that exposes a distinction missing from `r` becomes evidence about the transformation profile and expands/refines the basis. If the raw witness still exists, a stronger representation can be built; if the witness was deleted, the runtime records an irrecoverable gap. The architecture therefore converts the impossible “future-proof compression” problem into a corrigible loop: **preserve a declared basis, retain enough witnesses for valuable unknowns, and learn new basis obligations from counterexamples**. The W5 debt remains open because no current evidence establishes how broad that basis must be for real production agents.

# 298. Preservation composition: descendant summaries may only lose or explicitly regain semantic capability

The deepest telephone-game failure occurs when individually plausible transformations compose into a descendant that claims information no surviving source can justify. v0.6 therefore treats preservation composition as a monotone information discipline. For a pure derivation chain

\[
R_0 \xrightarrow{T_1} R_1 \xrightarrow{T_2} \dots \xrightarrow{T_n} R_n
\]

and semantic dimension `d`, a pure transformation may preserve or weaken capability but cannot upgrade `LOST/UNKNOWN` to `EXACT` merely because a later model rewrites the sentence more confidently. A source rebase or new admitted evidence is a different transition kind and is allowed to restore capability because it introduces an external basis that the descendant chain did not contain.

A conservative reference composition is therefore absorbing with respect to information loss:

```text
EXACT ∘ EXACT         -> EXACT
EXACT ∘ COARSEN       -> COARSENED
UNKNOWN ∘ pure-T      -> UNKNOWN or weaker
LOST ∘ pure-T         -> LOST
LOST + SOURCE_REBASE  -> capability supported by source
LOST + NEW_EVIDENCE   -> capability supported by new evidence
```

The formal lab tests this rule over bounded state spaces and 50k transformation-chain cases, but the W5 debt remains open because production transformation profiles are richer and may have property-specific inference rules. v0.6 consequently makes the composition procedure itself versioned and capability-scoped. An implementation may use a stronger theorem/prover for some dimensions, but it must not collapse “model inferred a likely value” into “the representation preserved the original value.” That inference, if useful, is a new claim with its own evidence/authority status. The key conservation law is simple: **derivation can create useful abstraction; it cannot retroactively create a witness for information the lineage no longer contains.**

# 299. Local repair closure: repair begins locally but widens along declared semantic dependencies

Counterexample-guided repair is attractive because it avoids rebuilding an entire lifelong memory after one failed query. However, “repair only the region that failed” is not universally sound. A semantic region can depend on a shared entity normalization, temporal profile, authority policy, transformation contract or common source whose correction changes many descendants. v0.6 therefore defines repair locality by dependency cause rather than by storage locality.

Given a counterexample `c` against representation `r` in region `R`, the runtime first identifies the earliest falsified assumption or transformation dependency. If the cause is representation-local—such as a summary dropping one exception while its source and profiles remain valid—the repair cone can be `R` plus descendants derived from that representation. If the cause is a shared transformation profile, entity merge, source-origin classification or temporal normalizer, the cone widens to every representation whose certificate depends on that shared revision. If the dependency graph is incomplete or exceeds a bounded repair budget, the system returns `REPAIR_SCOPE_UNKNOWN/OVERFLOW` and marks affected outputs for revalidation rather than falsely declaring a local fix complete.

This rule mirrors justification-aware invalidation: locality is earned by proving dependency separation, not assumed because two rows live in different collections. The formal lab demonstrates bounded cases where local and shared-profile causes produce different cones. What remains open is a scalable condition for real production dependency graphs and generated semantic relations. Accordingly, v0.6 treats causal dependency declarations as part of every strong transformation/certificate. A future implementation can optimize repair indexes aggressively, but the authoritative question is always: **which correctness assumptions changed?** The answer determines the repair frontier.

# 300. Interference calibration: memory effect is causal, scoped and distinct from truth

A memory can be true and still make a particular consumer reason worse. It can also correlate with bad outcomes merely because difficult tasks caused both the memory retrieval and the failure. v0.6 therefore refuses to turn retrieval statistics into a global “bad memory” score. `MemoryEffectEvidenceRevision` binds effect observations to at least the memory or memory set, consumer/model profile, task/state family, regime, retrieval policy, rendering policy, outcome dimension and evidence tier.

The evidence ladder separates observational exposure from stronger intervention. `E0` records correlation; stronger tiers require matched contrasts, shadow/counterfactual evaluation or controlled intervention. An effect learned for `model-A + coding-task + regime-r7 + narrative-rendering` does not automatically transfer to `model-B`, a different task or a field-only rendering. Transfer is a new empirical claim. More importantly, effect evidence changes **activation/rendering policy**, not the epistemic truth of the memory. A harmful but hard-required constraint cannot be silently removed; the frame compiler must seek a safer representation, alternate witness, structured warning or return insufficiency.

The open debt is calibration: how much causal evidence justifies inhibition, how quickly profiles decay under model upgrades, and how to attribute outcomes when several memories are exposed together. v0.6 therefore sets a conservative default: weak evidence may lower optional ranking but cannot veto hard roles; stronger scoped evidence may quarantine an optional representation while preserving source access; cross-profile reuse requires compatibility evidence. This creates room for an adaptive memory that learns what helps a given agent without letting behavioral convenience rewrite historical truth.

# 301. Witness-cover optimality is an optimization debt, not permission to forget unsafely

Witness-cover forgetting asks for a retained set of source/representations sufficient to recover a declared preservation basis after selected objects are deleted. The **safety** condition is straightforward: before deletion, every protected dimension/query obligation must have at least one surviving admissible witness or the runtime must explicitly transition that capability to an accepted irrecoverable gap. The **optimization** problem—finding the cheapest such set under storage, latency, privacy and risk constraints—can be combinatorial.

v0.6 deliberately separates these questions. A heuristic that retains more data than necessary may be inefficient yet semantically safe. A heuristic that deletes the last witness because it found a cheaper set is incorrect even if its average benchmark score improves. The formal lab therefore tests witness-cover safety, not global minimality. Production policy may use greedy approximations, ILP/solver-backed selection, tiered retention or domain-specific heuristics. Every chosen algorithm must emit a witness coverage certificate and expose dimensions whose coverage is `UNKNOWN`.

Privacy adds another dimension: sometimes policy **requires** deleting the last reconstructive witness. In that case safety does not override deletion authority. The correct result is deletion plus an explicit capability/recoverability downgrade; not hidden retention and not a fictional certificate. Thus the open W5 debt concerns approximation quality and economic efficiency, not the fundamental rule. Nolane Memory can be implemented safely before witness-cover optimality is solved, provided it never equates “the heuristic found a set” with “the set is a complete proof of preservation.”

# 302. Capability refinement is property-scoped; representations form a preorder only where the semantics justify it

V0.5 risked suggesting one global fidelity lattice. V0.6 rejects that simplification. A raw transcript can be superior for exact wording, inferior for compact procedural applicability and more expensive in context. A structured episode can preserve timestamps exactly while a carefully verified procedure is stronger for “what should I do under condition C?” Neither representation globally dominates the other.

For a semantic property/query family `q`, define a relation:

\[
R_a \succeq_q R_b
\]

only when the declared capability of `R_a` can soundly satisfy every obligation of `R_b` relevant to `q`, under compatible source, authority, temporal and scope profiles. This can form a preorder inside a bounded capability domain; after quotienting equivalent profiles it may yield a partial order. Across different properties, costs and applicability conditions, representations are often incomparable. Selection therefore uses a Pareto frontier over **required capability first**, then optional dimensions such as token cost, latency and empirical effect.

This prevents a dangerous optimization shortcut: choosing a “higher scored” summary whose average fidelity is good but which lost the one exception the current decision requires. If refinement compatibility is unknown, the runtime does not infer dominance from model quality or representation recency. It page-faults to a stronger known witness or returns uncertainty. The remaining W5 debt concerns richer property composition and safe automatic inference of compatibility, not the basic refusal to impose a fake total order.

# 303. External validity: bounded formal success does not establish natural-language memory correctness

The preservation-calculus lab is intentionally model-free. That makes it excellent for finding contradictions in the declared semantics: `LOST` must not self-upgrade, hard roles must not disappear under budget pressure, a principal ACL must not rewrite epistemic truth, and source-event identity must differ from delivery identity. It says far less about whether a production extractor will correctly recognize “unless SAFE=false” as an exception in a noisy conversation, whether entity resolution will survive multilingual aliases, or whether a learned consolidator will infer the right causal condition from ambiguous trajectories.

v0.6 therefore assigns formal-lab evidence to a bounded evidence level. Natural-language extraction, production-scale retrieval, human correction behavior, privacy semantics across real connectors, model-upgrade transfer and long-horizon interference require separate empirical evidence. A future benchmark result likewise cannot automatically establish all semantics: a QA benchmark can validate answerability under its question distribution while saying little about write idempotency or cross-principal leakage.

External-validity debt is discharged only claim-by-claim. The report must name the evaluated domains, consumer/model families, storage scale, language/task distribution, tool environment and failure classes. Broad claims require diverse transfer evidence. The architecture remains useful before this debt closes because it gives empirical failures **typed places to land**—new preservation debt, capability downgrade, effect profile, repair obligation—rather than requiring the team to rewrite the kernel whenever reality violates an optimistic assumption.

# 304. Debt discharge is a versioned transition with an evidence type, never a prose declaration

Every W5 or runtime semantic debt has a durable lifecycle. A debt record identifies the proposition/assumption it limits, severity, affected capability claims, evidence required for discharge and the revision that created it. Resolution must name an evidence class appropriate to the debt. A bounded theorem can discharge a bounded algebraic ambiguity; it cannot discharge external validity. A benchmark can calibrate an effect profile; it cannot prove writer idempotency. An independent implementation can expose spec ambiguity; it cannot by itself prove witness-cover optimality.

Reference outcomes include:

```text
OPEN
NARROWED
PARTIALLY_DISCHARGED
DISCHARGED_BY_FORMAL_RESULT
DISCHARGED_BY_REPLICATION
DISCHARGED_BY_POLICY_DECISION
SUPERSEDED_BY_NEW_CONTRACT
ACCEPTED_RESIDUAL_RISK
```

`ACCEPTED_RESIDUAL_RISK` is not evidence that the proposition became true; it records a governance decision to operate within a known limitation. When a debt is discharged, dependent capability certificates may be re-evaluated. Historical frames/certificates retain the debt state that was actually known at their cut, preserving auditability.

This mechanism prevents a subtle research-lifecycle bug: after enough prose and passing tests, unresolved uncertainty is forgotten socially even though nothing actually resolved it. Nolane Memory uses its own philosophy on its specification—**unknowns are state that must be transitioned, not inconvenient sentences to remove from the next release note.**

# PART XXVI — DIFFERENTIAL CONFORMANCE: THE SPEC MUST SURVIVE TWO IMPLEMENTATIONS

# 305. The next decisive test is not another oracle but two independently built semantic kernels

A specification can be internally consistent and still underspecify behavior. The strongest practical test is to give the same normative subset and fixtures to two implementations that do not share code, hidden helper functions or test-output lookup, then compare normalized semantic results. If they disagree on whether a historical fact was knowable, whether deletion preserved witness cover, whether a frame is sufficient or whether a support path remains grounded, the difference reveals either an allowed capability distinction or an ambiguity in the spec.

v0.6 therefore defines differential conformance as a future **required research gate**, not something the current single-host effort can self-certify. The implementations need not choose the same database, graph representation, indexing strategy or internal class layout. They must agree where the kernel defines exact semantics and may differ only where a capability/profile explicitly permits refinement or inconclusive results.

The comparison corpus should include source regressions, preservation-calculus worlds, migration fixtures, crash/retry traces, temporal histories, access changes and semantic page faults. Each fixture declares the relevant comparison relation before execution. This prevents post-hoc claims that a disagreement is “just an implementation detail.” A genuine implementation detail is one that normalizes away without changing authority, preservation, recall sufficiency, historical judgement, recoverability or declared failure status.

# 306. `MemoryConformanceVector` contains only authority-relevant normalized semantics

Byte equality is too strict and natural-language output equality is too weak. v0.6 compares a normalized conformance vector whose fields correspond to the observable semantics that downstream agents rely on. A reference vector may include:

```text
canonical commit/root identity
current epistemic projection
historical judgement set for the query cut
valid/knowledge-time result
principal-usable projection
live justification alternatives
origin/authority ceiling
preservation capability for required dimensions
recoverability status
semantic debt relevant to the obligation
counterexample/applicability result
Recall Sufficiency status
hard-role coverage
frame source handles
required revalidation/page-fault status
```

Derived scores, internal cache keys, ANN ordering among semantically equivalent optional candidates and diagnostic prose are excluded unless a declared consumer contract makes them material.

Normalization itself is a versioned trusted semantic procedure. Unordered support alternatives are canonicalized; half-open intervals use one specified boundary convention; equivalent source handles resolve to stable logical IDs; confidence/effect metadata is compared only under compatible profiles. If the normalizer changes, old comparison receipts cannot silently be reused. This gives differential testing a precise target: two systems may look very different internally yet still prove they implement the same memory semantics.

# 307. Exact-equivalence and capability-refinement comparisons are distinct modes

Not all implementations have equal retrieval/verifier capability. v0.6 therefore requires a conformance fixture to declare one of two comparison modes.

`EXACT_SEMANTIC_EQUIVALENCE` applies when both implementations claim the same kernel/profile/capability contract over the fixture. Their normalized conformance vectors must agree on all correctness-bearing fields. An implementation cannot escape a disagreement by saying its model “reasoned differently.”

`CAPABILITY_REFINEMENT` applies when implementation B explicitly supports a stronger bounded capability than A. B may replace `UNSUPPORTED/INCONCLUSIVE/REHYDRATE_REQUIRED` with a sound conclusive result if the refinement relation for that property is declared and the stronger result does not contradict an already conclusive sound result under the same cut. Refinement cannot erase an ACL denial, hard counterexample, semantic debt outside its proof scope or incompatible temporal regime.

The distinction is important because otherwise “smarter implementation” becomes an untyped loophole. Conversely, demanding exact outputs from an approximate optional-association index and an exact query engine would overconstrain legitimate architectures. Conformance follows the product capability relation defined in Section 302, not a universal total ranking.

# 308. Transition conformance compares state deltas, not just final snapshots

Two write implementations can end with similar current state while disagreeing on history in a way that later invalidation exposes. Therefore transition conformance includes the semantic delta: operation identity/idempotency outcome, previous and new canonical root, affected claim/representation revisions, origin binding, support/justification changes, validity interval changes, supersession/revocation relations and semantic debt created or discharged.

Example: one implementation corrects `A→B` by overwriting A; another supersedes A while retaining its historical validity. Current query results may both say B. A later `JUDGED_AT(t_old)` query will differ. The overwrite implementation therefore fails transition conformance even before the historical query is executed because it destroyed required lineage.

Similar logic applies to duplicate delivery, consolidation and deletion. Applying the same evidence event twice must produce one semantic support state; a pure transform may create a representation but cannot create a second independent origin; forgetting that crosses witness cover must emit a capability/debt transition. Comparing deltas forces the implementation to preserve the causal structure on which future correction depends.

# 309. Recall conformance is proof-carrying: same answer text is not enough

A recall implementation conforms when it satisfies the same bounded obligation under a compatible cut, not merely when the model produces the same sentence. The comparison examines region set, required semantic dimensions, representation capability, source/rehydration choices, counterexample inclusion, principal scope, hard-role coverage, ambiguity and final sufficiency status.

If two implementations both answer “API v2” but one reached the result through a stale representation that cannot preserve the exact temporal regime, the outputs are not semantically equivalent. Conversely, one may render a compact typed fact and another a slightly longer explanation while both carry equivalent source handles and hard-role coverage; their model-facing text can differ.

For optional evidence, exact ordering need not conform unless the consumer contract makes order material. For hard roles, silent omission is never an allowed approximation. When context budget is insufficient, both systems should converge on a compatible explicit outcome such as `MEMORY_VIEW_OVERFLOW` or staged semantic page fault rather than differ because one silently truncates. This is how v0.6 connects context efficiency to correctness instead of allowing token budgets to redefine the task.

# 310. Consolidation and forgetting conformance is judged by preserved capability and witness structure

Two consolidators need not produce the same wording. They conform if their derived representations preserve the same declared dimensions, retain equivalent source lineage/recoverability, respect applicability and counterexamples, and do not upgrade authority or independence. If one representation is cheaper but loses a protected exception, it is not a conforming optimization.

For forgetting, implementations may choose different retained witness sets. Exact set equality is unnecessary. What must agree is the resulting protected capability under the declared preservation basis and the semantic debt created by any authorized loss. One system may retain raw artifact A while another retains exact structured witness B; if both are independently sufficient to reconstruct the same protected dimension under policy, they can be equivalent. This is why witness-cover safety is separated from witness-cover optimality.

Repeated maintenance under stable inputs also participates in conformance: canonical semantic output should reach the declared fixed point. A system that generates semantically new summary generations indefinitely under no new evidence is behaviorally different from one whose maintenance becomes idempotent, even if every generation sounds plausible.

# 311. Recovery and migration conformance must preserve uncertainty, not merely data availability

Recovery conformance asks whether a new process/self-version reconstructs the same justified continuity state from durable records under current environment validation. It must preserve what was true, what was believed, what failed, what remains unresolved and which old assumptions require revalidation. A replay that restores an old plan/procedure as authority without checking model/tool/regime drift is not equivalent to a bootloader that returns `REVALIDATION_REQUIRED`.

Migration adds another challenge: the target schema can express distinctions the source never captured. Two safe migrations may encode the unknown differently internally, but neither may invent independent origin, exact timestamp semantics or preservation guarantees. Differential fixtures therefore emphasize ambiguous legacy records and require an equivalent **epistemic downgrade**, not identical field values.

A migration that yields more convenient current answers by resolving ambiguity with defaults fails conformance. Safe uncertainty is an observable part of the memory system. The same principle governs corrupted/missing archives: `SOURCE_UNAVAILABLE` is not equivalent to contradiction, and a recovered summary without its forensic source cannot inherit the assurance of an exact reconstructible representation.

# 312. Material nondeterminism is part of conformance; incidental nondeterminism is normalized away

Large memory runtimes will use approximate search, concurrent index maintenance and learned candidate generation. v0.6 does not require byte-deterministic execution. It requires that nondeterminism that can change correctness-bearing outcomes be either controlled, journaled or reflected in a weaker status.

If two ANN runs return different **optional** episodes while all hard roles and source capabilities are equivalent, normalization may treat that variation as incidental. If stochastic candidate generation chooses between two materially different consolidation meanings, the random seed/selection procedure and resulting admission decision are material. The candidate search can be stochastic; canonical authority cannot drift invisibly.

Nondeterminism-control tests repeat the same fixture under identical semantic inputs and environment contract. Variability in latency or optional evidence is recorded separately from variability in authority, preservation, sufficiency or scope. Unstable correctness output creates stabilization debt. Averaging the results into one accuracy number does not discharge it.

# 313. Observational equivalence defines the smallest useful formal core

The purpose of the v0.6 formal core is not to specify every implementation instruction. It is to define the **observations that may change an agent's legitimate memory state**. Two internal states are observationally equivalent for a declared consumer/profile when every allowed query/transition in the bounded conformance language yields equivalent authority, temporal, preservation, access, recoverability and Recall Sufficiency observations.

This gives the architecture a principled compression boundary of its own. Internal indexes, activation values, storage tiers and representation caches may vary freely while they remain observationally equivalent. Once a change can alter whether a claim is admissible, whether a hard role is covered, whether a source can be recovered or whether a principal may use it, it crosses into the semantic core and needs a versioned contract.

The formal language is intentionally bounded. Extending it requires a counterexample showing that two states currently considered equivalent lead to a materially different permitted agent behavior. This is the same stop-rule used for the document: **new semantics are admitted by discriminating behavior, not by architectural aesthetics.**

# PART XXVII — ANTI-SELF-CERTIFICATION AND THEORY STOP RULE

# 314. Nolane Memory cannot certify its own universal completeness

A runtime can audit its ledger, verify its local invariants and prove that a Recall Frame satisfies a declared obligation. It cannot conclude that the external world contains no relevant fact it never observed, that every future query family is represented, or that its own verifier has no unknown failure mode. These would be self-certifying closed-world assumptions.

v0.6 therefore distinguishes `internal_conformance` from `world_completeness`. Query-domain completeness is bounded by the domains actually searched. Observation coverage describes where the runtime has evidence and blind intervals. Preservation certificates are basis-scoped. Verification capabilities are explicit. A system may know “I searched all active project procedures visible to principal P under snapshot S” without claiming “no other relevant procedure exists anywhere.”

This principle is especially important for memory because fluent reconstruction can hide missing observation coverage. The agent should be able to say “no recorded evidence in the complete accessible project domain” or “unknown; archive/connector not covered,” rather than collapsing both to “never happened.” Internal proof strength reduces uncertainty only inside its declared premises.

# 315. No component may bootstrap itself into a trusted root through memories it generated

Self-reflection is valuable for candidate discovery, procedure improvement and failure explanation. It becomes dangerous when a component generates a memory and later cites the existence/repetition of that memory as evidence of its own correctness. v0.6 therefore keeps the trust base finite and external to pure derivation. A model can create a candidate claim; an admitted support path must eventually ground in authorized user assertion, trusted observation, verified artifact/test receipt or another explicitly accepted root appropriate to the subject.

Cycles such as `A supports B, B supports A` remain ungrounded without an incoming accepted root. Repeated self-summaries do not create source diversity. A learned verifier cannot become a new trust root solely from evaluations whose acceptance already depends on that verifier. When the trust base changes, historical judgement remains but current reuse can be gated.

This does not make memory non-autonomous. It makes autonomous learning **corrigible**: the system can build abstractions and policy priors aggressively while keeping a reconstructible distinction between “I inferred this” and “the evidence independently established this.”

# 316. A new canonical primitive is admitted only by a discriminating counterexample

The document's growth rule is strict. A proposed primitive must demonstrate a case in which the current canonical state cannot represent two materially different correctness outcomes without ambiguity. The counterexample must identify the consumer-visible consequence: different authority, validity, scope, preservation, recoverability, repair, sufficiency or failure status.

If an idea merely makes implementation faster, it belongs in a derived index/cache or policy profile. If it changes model-facing wording without changing semantic obligations, it belongs in rendering. If it is a useful taxonomy but can be reconstructed from existing canonical state, it is a derived view. If it represents an unresolved empirical choice—such as the best interference threshold—it is policy/research debt, not canonical truth.

This rule is how v0.6 prevents returning to V0.5's primitive/section inflation. The architecture is allowed to be large in **depth of guarantees**, not in independent authorities. Adding a new database/table is not an architectural advance unless the old kernel could not express a necessary state transition.

# 317. Kernel, profile, policy and derived view are different extension classes

To avoid both rigidity and semantic fragmentation, v0.6 classifies extensions.

**Kernel semantics** determine authority-bearing state and require strong migration/conformance rules. **Profiles** specify capability within a known semantic shape—query families, verifier capabilities, transformation contracts, rendering profiles. **Policies** make authorized choices among legal behaviors—retention budget, evidence threshold, shared-visibility mode, risk level. **Derived views/indexes** accelerate or project canonical state and may be rebuilt.

The classification has operational consequences. A policy change can alter future admission/retention but cannot rewrite what past evidence meant. A profile revision can invalidate dependent certificates but cannot manufacture source evidence. A derived-index rebuild can change optional retrieval ranking but cannot mutate canonical truth. A kernel change requires explicit schema/semantic migration and historical compatibility rules.

Many “memory features” become simpler under this taxonomy. A new embedding model is an index/profile change. A new procedure extractor is a derivation profile. A stricter privacy rule is policy/access state. A new epistemic polarity that distinguishes two previously conflated authority outcomes may be a kernel change. This prevents the runtime from treating every innovation as a new memory subsystem.

# 318. Feature breadth is vetoed when it does not deepen the memory contract

Nolane Memory intentionally remains below the agent runtime. It does not absorb generic planning, scheduling, identity management, browser control, workflow orchestration, training, document management or distributed consensus merely because memory interacts with those systems. Integration points carry typed evidence, authority, scope and continuity state; ownership stays elsewhere.

Even inside memory, new cognitive mechanisms are held to the same test. A “dreaming” module, emotion simulation, narrative persona store or autonomous curiosity loop is not admitted merely because it resembles human memory. If a mechanism improves candidate discovery or consolidation, it can be an optional derived/profile layer. It joins the semantic kernel only if a concrete correctness distinction requires it.

The result can still be a very large runtime in implementation: durable stores, multiple indexes, provenance graph, temporal engine, transformation workers, archive tiers, recall compiler, effect ledger and repair scheduler. The specification remains narrow because these components all serve one contract: preserve and reconstruct justified continuity under bounded context. **Large core depth is compatible with narrow product scope.**

# 319. Research stopping rule: stop prose when the next uncertainty is empirical or implementational

Theory work stops when all known implementation-relevant semantic choices have a defined representation/failure outcome, the remaining high-value uncertainty requires external data/independent implementation/scale measurement, and another prose section would only restate a policy choice. At that point the correct next action is code, experiment or independent review.

For v0.6 that threshold is nearly reached. The seven W5 debts do not all justify more kernel theory. Witness-cover optimality, interference calibration and external validity are empirical/algorithmic. Differential implementation is required for underspecification. Future-query basis has a bounded contract but no universal solution by design. Additional writing that pretends to “solve” them without new evidence would lower quality.

The theory reopens when an implementation, migration, benchmark or new research result produces a discriminating counterexample. The earliest affected assumption is then repaired; descendants/certificates are revalidated; a new revision is justified by evidence. This establishes a disciplined loop between specification and runtime rather than treating the Markdown as a one-time constitution that can never be falsified.

# PART XXVIII — FINAL REFERENCE ARCHITECTURE: A DEEP RUNTIME, NOT A COLLECTION OF MEMORY FEATURES

# 320. The three-plane architecture is the compressed form of the entire specification

The final v0.6 architecture has three authority-separated planes.

The **Canonical Plane** stores evidence events, claims, historical judgements, OR-of-AND justifications, temporal validity/knowledge-time, origin/authority/access, canonical commits and semantic debt. It answers what was observed, what is currently supported, what a past self believed and why.

The **Representation Plane** stores semantic regions and representation fibers—episodes, summaries, procedures, failure lessons, anchors and other optimized views—each with lineage, applicability, transformation contract, preservation envelope, semantic-loss state, recoverability and effect metadata. No representation becomes a second truth owner.

The **Projection Plane** turns the current task into a Recall Obligation, discovers relevant regions, resolves the cheapest capability-sufficient representation, triggers semantic page faults when necessary, reconstructs competing candidates, retrieves counterexamples/negative evidence, evaluates hard-role coverage and emits a Recall Frame plus sufficiency/ambiguity/overflow status.

Indexes, caches, embeddings and associative activation surround these planes as accelerators. They are powerful but non-authoritative. This architecture deliberately makes the correctness root boring and the recall intelligence exotic. That division allows aggressive optimization without letting a learned heuristic silently promote itself into memory truth.

# 321. The lifelong runtime cycle is Observe → Commit → Represent → Project → Learn → Revalidate

A normal memory runtime cycle can be written compactly:

```text
OBSERVE
  capture source event / correction / tool result

COMMIT
  bind origin, temporal semantics, principal/authority
  verify/admit canonical claim or raw evidence
  append one idempotent canonical transition

REPRESENT
  derive episodes/summaries/procedures/failures/anchors
  attach preservation, applicability and recoverability contracts

PROJECT
  compile current Recall Obligation
  resolve region + representation
  page-fault stronger witness when needed
  reconstruct and certify Recall Frame

LEARN
  observe outcome/effect
  consolidate, refine, inhibit optional harmful representations
  create query counterexamples / semantic debt

REVALIDATE
  process new evidence, regime/model/access changes, deletions
  update justifications, repair affected regions
  preserve historical judgement
```

Not every user turn executes every phase. Raw capture can be cheap and immediate while slow consolidation is deferred. Optional indexes can lag canonical commits under explicit visibility semantics. The cycle describes causal ownership, not a synchronous pipeline.

The important property is that feedback returns through typed transitions. A bad outcome does not directly “lower truth”; it creates scoped effect/failure evidence. A query miss does not make the answer true; it creates a recall/coverage signal. A new summary does not overwrite its source; it becomes another representation fiber. This is how the runtime can learn for years without turning its own behavior into an untraceable rewriting of history.

# 322. Context virtualization law: total memory may grow without forcing total history into the model

Let total durable memory size be `N`, the true decision-relevant dependency width for current obligation `q` be `W(q)`, and required semantic precision be `P(q)`. The architectural target is not constant context. It is:

\[
Context(q) \approx f(W(q), P(q), rendering)
\]

with weak/sublinear dependence on `N` when `W(q)` and `P(q)` remain fixed.

The runtime achieves this by keeping provenance, full source, transformation history, justification graph and alternative representations external. The frame carries compact typed content plus handles. When a representation lacks a required dimension, a semantic page fault hydrates only the stronger witness/field needed for that obligation. If the true dependency width genuinely grows beyond budget, context grows, stages hydration or returns explicit overflow; it does not preserve a marketing curve by deleting hard requirements.

Therefore context efficiency is evaluated jointly with decision-equivalence/hard-role coverage. A tiny frame that omits the counterexample is worse than a larger correct frame. A huge memory store can be cheap at inference time only because it has strong indexing and preservation metadata, not because the system pretends old history stopped mattering.

# 323. Tề Hạ translation: continuity is the ability to reconstruct a justified self, not the ability to replay everything

The Tề Hạ inspiration survives the increasingly formal design because it concerns **continuity under discontinuity**. A future self may lose conversation context, change model version, restart after a crash or encounter an altered world. It should not need a verbatim replay of every past token. It needs enough trusted external structure to reconstruct the objective/constraints, what was known then, what was tried, what failed, which hypotheses remain open and which environmental assumptions must be checked again.

Anchors therefore remain small high-leverage cues, but they are not magic truth tokens. They bind canonical references, historical cuts, objective/constraint state and revalidation requirements. Past-self messages are evidence and policy priors, not commands. Multiple people/agents/artifacts can provide redundant retrieval paths without becoming independent factual corroboration merely through duplication.

This is the safe engineering analogue of Tề Hạ's strongest trick: the world itself can carry memory for a future self. Nolane adds a crucial discipline the fictional mechanism does not need to formalize—the future self can inspect **why** the clue was believed, whether its origin/authority still holds, what semantic precision survived compression and whether current reality invalidates the old conclusion. The system remains itself by reconstructing justified continuity, not by worshipping its past.

# 324. What is actually unusual about Nolane Memory

Individual ingredients are not novel in isolation. Temporal knowledge graphs, vector search, event sourcing, MVCC, truth maintenance, associative spreading activation, procedural memory, consolidation and context compression all have prior art. The distinctive research hypothesis is their **composition under strict authority separation**.

Nolane Memory combines:

```text
immutable/versioned evidence and historical judgement
+ alternative justification / origin authority
+ durative temporal truth and knowledge-time
+ one canonical memory substrate with many lossy roles
+ explicit semantic-loss / preservation / recoverability
+ counterexample-guided regional repair
+ witness-aware forgetting
+ associative/multi-view active reconstruction
+ semantic page faults and hard-role Recall Frames
+ scoped causal memory-effect learning
+ continuity across session/model/environment drift
```

The “weird” cognitive mechanisms are allowed to be aggressive because they cannot independently change canonical truth. The “boring” systems semantics are useful because they preserve the distinctions needed for lifelong corrigibility. The architecture therefore aims at something narrower than human memory emulation and deeper than persistent RAG: **an external cognitive continuity runtime that can grow enormous while remaining epistemically inspectable and context-local.**

# 325. Minimal semantic kernel versus full runtime

The full runtime is large, but its irreducible semantic kernel is smaller. A minimal K0/K1 implementation needs canonical event/claim/judgement/justification state; commit/origin/authority/time/access semantics; semantic region + representation lineage; preservation/recoverability/debt; and typed failure outcomes. K2 adds Recall Obligation, cut, representation resolution, reconstruction and sufficiency. K3 adds maintenance/forgetting/repair. K4 adds effect/security/shared continuity.

This staged view matters for engineering. It prevents an early prototype from implementing 40 components superficially. A small K0 that survives crash/idempotency/origin/temporal tests is more valuable than a visually impressive “memory OS” whose summary writer can overwrite truth. Later layers are built on explicit acceptance gates and can be disabled while lower layers remain valid.

It also prevents naming inflation. An implementation may call itself `Nolane Memory K1-compatible` if it passes that profile; it cannot claim the complete runtime. The specification therefore supports incremental construction without weakening the target.

# 326. Current research status: semantically consolidated target, not W5-certified completion

At this revision, the document provides a consolidated semantic target, source-adversarial history, formal bounded properties, migration/implementation semantics, staged acceptance gates and authoritative ownership matrices. The current preservation-calculus artifact records 25/25 property families and 75,772 bounded cases passing. The focused Nolane World memory/truth/recovery selection remains executable. These facts support the claim that the specification has been aggressively falsified **within the tested models**.

They do not support W5 convergence. The W5 closure record remains `BLOCKED`; seven epistemic debts are open; independent replication, verifier/source independence, external validity, confidence calibration and benchmark validity are not supplied by this single-session research effort. v0.6 therefore uses the status:

```text
SEMANTICALLY_CONSOLIDATED_RESEARCH_TARGET
W5_CONVERGENCE = NOT_CLAIMED
PRODUCTION_IMPLEMENTATION = NOT_CLAIMED
EMPIRICAL_SUPERIORITY = NOT_CLAIMED
UNIVERSAL_FUTURE_QUERY_SAFETY = NOT_CLAIMED
ZERO_ERROR = NOT_CLAIMED
```

This is a stronger artifact precisely because it refuses to convert its own effort into authority.

# PART XXIX — RELEASE QUALITY: THE DOCUMENT MUST PASS THE SAME DISCIPLINE IT DEMANDS OF MEMORY

# 327. Anti-fragmentation gate measures reasoning depth, not document length

V0.5 demonstrated that a specification can grow while becoming shallower. v0.6 therefore treats document structure as a quality signal. The release verifier measures numbered-section word counts, median/mean depth, number and ratio of micro-sections, duplicate long sentences and section continuity. These metrics are not proof of intellectual quality, but they catch the exact failure mode observed in V0.5.

The target is not to beat Nolane Plan's word count. The target is to ensure most sections contain a complete reasoning unit rather than an isolated assertion. A short section is allowed when a table/algorithm carries the substance; a large population of 40–80-word sections is a release failure. The verifier therefore reports distributions rather than one threshold alone.

For v0.6, the authoring target is a median above the V0.5 fragmentation regime by a wide margin, zero duplicate numbered sections, a very low under-100-word ratio and no suspicious repeated long prose. If adding twenty new sections lowers the median sharply, the correct response is consolidation, not another appendix.

# 328. Anti-duplication and primitive-inflation gate

The release audit searches for exact repeated long sentences and repeated normalized paragraphs, because copy/paste growth often creates contradictory “same but slightly different” rules later. It also inventories canonical primitive names and checks that current ownership appears in the Closure Matrix rather than in two independent writable subsystems.

Primitive count alone is not a quality score. The important condition is **single authority ownership**. A representation role may have many implementations; a canonical claim has one owner. If both a legacy adapter and the new kernel can mutate confidence/validity independently, the audit fails even if their field names differ. Derived indexes are explicitly marked non-authoritative.

When a concept appears repeatedly—scope, validity, confidence, preservation, recovery—the verifier cannot prove semantic identity from words alone. The document therefore includes ownership/write matrices so automated checks can at least ensure every authoritative primitive has a declared owner and legacy surfaces are classified as read-only/migration adapters. Human review focuses on the remaining semantic overlaps rather than re-reading 500 KB blindly.

# 329. Closure-matrix audit is authoritative over diagrams and examples

Architectural diagrams are pedagogical. Examples use simplified fields. The authoritative ownership rules are the closure matrices in Part XXIII plus explicit supersession statements in later sections. The release checker verifies that canonical/representation/projection primitives named by the final architecture have a row/home and that no final section reintroduces an alternate writable clock.

When an example says `confidence`, it is interpreted as a derived assurance projection unless a matrix row grants it independent canonical ownership. When an old lifecycle uses `ACTIVE/STALE/ARCHIVED`, the product-state dimensions govern. When a representation is described as “memory,” its claim authority remains inherited from canonical evidence/justification. These resolution rules prevent educational shorthand from silently becoming normative schema.

A future revision that changes ownership must update the matrix and migration semantics in the same change. Adding a class/file without a matrix change cannot create new authority merely because code can write it.

# 330. Evidence/provenance audit prevents the release from laundering its own research process

Every quantitative statement in the final release is classified by source: current file bytes, fresh local source test, bounded formal lab, historical previous-revision artifact, external paper result or W5 runtime state. Numbers are not merged across incompatible runs. A focused 94-test selection is not called a full-suite pass. The formal lab is not called production benchmark evidence. W5 operator counts are not called independent verification.

The release artifact references the exact digest of the W5 snapshot and preservation-calculus result in its verification sidecar. If those files change, the verification bundle changes. Historical source bugs are described as reproductions against the supplied Nolane World bundle, not claims about an upstream latest repository unless separately checked.

This mirrors the memory runtime's own origin-bound authority: a statement becomes more trustworthy by preserving where it came from and what that source can establish, not by being repeated in many sections.

# 331. Final release gate

A v0.6 file may receive `FINAL` only if the **exact final bytes**, not an earlier draft, pass the release verifier. Required checks include numbered-section continuity/uniqueness; failure-ID uniqueness; Markdown-fence balance; zero unresolved `TODO/TBD/FIXME` implementation placeholders; anti-fragmentation distribution; duplicate long-sentence/paragraph scan; authoritative Closure Matrix presence; no-two-writable-clocks audit; explicit W5 `BLOCKED` disclosure; all seven W5 debt kinds; preservation-calculus revision/digest; working-source regression evidence; and explicit refusal of zero-error, universal-future-safety and empirical-superiority claims.

The verifier also compares document-shape metrics against the failure mode that motivated the clean rewrite. It reports median words per numbered section and the number/ratio below 100 words. These metrics do not prove depth, but a V0.6 that collapses back toward V0.5-style micro-section inflation fails its own authoring objective. Repeated code tables may be intentionally referenced once rather than copied to satisfy both readability and anti-duplication.

A structural `PASS` does not override W5. The expected valid state is:

```text
DOCUMENT_RELEASE_QUALITY = PASS
BOUNDED_FORMAL_PROPERTIES = PASS
FOCUSED_SOURCE_REGRESSION = PASS
W5_RESEARCH_CONVERGENCE = BLOCKED
```

The first three establish that the artifact is coherent and reproducible at its stated evidence levels. The fourth prevents those results from being laundered into an independent research-completion claim.

# 332. What should happen after v0.6, if this release passes

The next major work should not be v0.7 prose. It should be a small independent experimental implementation of K0/K1 plus a second independently written reference model for differential conformance. The initial code should deliberately exclude learned association and large vector infrastructure. It should first make duplicate evidence, stale-base correction, temporal history, OR-of-AND invalidation, preservation loss and witness deletion impossible to mishandle silently.

Only after the two implementations agree on the bounded corpus should K2 context virtualization be connected to a real model and benchmarked against full-history/long-context baselines. That experiment will generate the next useful counterexamples: extraction mistakes, query-family gaps, semantic page-fault latency, context compiler failures and preservation/quality tradeoffs. Those findings—not a desire for a newer version number—should decide whether a v0.7 theory revision is warranted.

# 333. Final v0.6 statement

Nolane Memory v0.6.1 is best understood as a **deep runtime contract for lifelong justified continuity whose correctness is defined at subsystem seams, not only inside memory components**.

It does not ask an AI to remember everything. It externalizes a potentially enormous history into canonical evidence and many purpose-built representations, records what each representation preserves and can recover, and compiles the smallest task-relative view whose hard obligations are actually covered. A Recall Obligation is no longer derived only from what the model/user explicitly asks: a bounded action/tool/sink descriptor can proactively introduce the memory dependencies required before a consequence. Hydration can reveal further hard dependencies, and obligation closure runs to a bounded fixed point before sufficiency is certified.

It can forget redundant representations without pretending lost capabilities survive; repair local semantic regions when future queries expose bad compression; preserve historical belief separately from current truth; learn procedures/effects without manufacturing new evidence; and rehydrate stronger witnesses when a compact view is insufficient. The repair path cannot resurrect a claim merely because an ancestor is active: every object must regain its own live justification/preservation predicate. The identity path cannot mutate or reset an object through repeated `CREATE`: revision, supersession and resurrection are explicit transitions.

Security is equally compositional. Principal filtering occurs before hidden retrieval influence, but that is not enough. The complete reconstructed payload is checked again at the model/user/tool/export sink because individually authorized fragments can jointly disclose or instantiate something unauthorized. `USE_FOR_REASONING` is not `DISCLOSE_TO_TOOL`; a remembered instruction does not grant the capability or authority required to execute itself. Cross-domain sharing is a publication/import saga with explicit partial states, not a hidden global consensus system.

The runtime's intelligence comes from reconstruction, association, temporal/causal structure, prospective cues and learned maintenance. Its trustworthiness comes from a deliberately different layer: immutable revision identity, origin, commit order, justification, temporal/knowledge-time semantics, preservation contracts, witness accounting, principal/sink scope, publication state and fail-visible sufficiency. Neither layer is sufficient alone.

The central theorem-shaped intuition is now:

> **A long-lived AI does not need its whole past in context. It needs a runtime that can determine, before a consequential boundary, which parts of the past must matter; prove which of them remain knowable, usable, composable and reconstructible; and refuse to cross the boundary when those obligations cannot be satisfied without fabricating identity, authority, disclosure permission or semantic precision.**

That is the narrow scope and the deep ambition of Nolane Memory.

---

# PART XXX — V0.6.1 SEMANTIC-SEAM CLOSURE

# 334. Why v0.6.1 exists: correctness fails at joins between strong subsystems

v0.6 intentionally stopped broad theory expansion and asked for implementation/differential pressure. The first deeper audit did not discover a need for another memory type. It discovered that several individually strong rules could still compose ambiguously at their boundaries: creation versus revision, invalidation versus repair, explicit query versus implicit action memory requirements, record authorization versus reconstructed-payload authorization, region locality versus stable identity, source publication versus destination admission, and semantic page faults versus finite resources.

This is the class of failure that a mature specification must pursue. A storage module can be idempotent while a lifecycle API reopens resolved state. A recall compiler can cover every role it was given while failing to derive a role implied by the contemplated tool call. Every memory fragment can pass its own ACL while their fusion violates the destination policy. A region repair can be local in storage but globally unsound because the falsified assumption was a shared transformation profile. An index can be eventually consistent while a strong recall quietly uses it as if it were current.

v0.6.1 is therefore a **seam hardening revision**. It adds no planner, scheduler, identity provider, generic policy engine, distributed consensus service or new cognitive-memory family. It strengthens existing canonical/projection semantics only where a counterexample permits two apparently conforming implementations to produce different authority, lifecycle, sufficiency, confidentiality or current-use outcomes.

The admission evidence comes from four channels: fresh source counterexamples in the supplied Nolane World bundle; stronger contrasting patterns elsewhere in that same bundle; a model-free seam calculus; and claim-scoped external literature pressure. None of those channels is allowed to self-promote into W5 research convergence.

# 335. Nolane World source seam findings S17–S23 and the stronger internal contrasts

A clean audit of the supplied Nolane World 0.12.0 bundle reproduced seven additional behaviors:

| Finding | Source behavior | Consequence |
|---|---|---|
| S17 | `ClaimEvidenceGraph.add_evidence()` accepts the same evidence ID again with different source/digest/trust fields | semantic evidence identity can be rewritten in place |
| S18 | `ClaimEvidenceGraph.add_claim()` accepts the same claim ID with different text | logical claim identity can become last-write-wins |
| S19 | `TruthGraph.add()` re-adds a previously retracted node as active | `CREATE` can become an implicit resurrection path |
| S20 | `resolve_repair()` can reactivate a child from active ancestry/replacement evidence even when the child's own direct support remains invalid | repair status can outrun live justification |
| S21 | `CognitiveGraph.add()` overwrites a same-ID node with new kind/text | a derived graph can mutate semantic identity |
| S22 | deterministic counterexample re-proposal can change `verified → proposed` | idempotent re-proposal can regress lifecycle |
| S23 | deterministic debt re-add can change `resolved → open` | repeated creation can reset control state |

The same codebase contains stronger counter-patterns: `ResearchRevisionMemory` rejects duplicate logical IDs, and `DurableMemoryRegistry` rejects the same memory ID when the new record differs materially. These contrasts are more useful than labeling one generation “good” and another “bad”: they reveal a precise semantic choice that the unified memory kernel must make.

The fresh artifact records all seven reproductions and both strong contrasts. Its internal digest is:

```text
4801b7952cdedcb2af1e82896e24a17fdfa782f1c2f7fc6c555a861f5cd2919b
```

The correct architectural conclusion is not “copy the strict classes.” It is the cross-cutting law from Section 183: **create, revise, supersede/revoke and reactivate are different semantic operations with different proof obligations**. Every canonical object family must obey that law even if its physical repository API differs.

# 336. Identity-transition theorem: CREATE, REVISE, SUPERSEDE and REACTIVATE are disjoint authorities

Let a logical memory object be `x`, current revision `x@r`, and creation semantics digest `D_create`. The minimum conformance relation is:

```text
Create(x, D_create)
    if x does not exist
        -> x@1

Create(x, same D_create)
    if x exists
        -> idempotent reference to existing object
        -> no lifecycle/authority reset

Create(x, different semantic creation meaning)
    -> IDENTITY_COLLISION

Revise(x, expected=x@r, delta)
    -> x@(r+1) if predecessor/policy checks pass

Supersede/Revoke(x@r, cause)
    -> typed new lifecycle revision / relation
    -> historical x@r remains addressable

Reactivate(x, cause)
    -> legal only through the object's reactivation predicate
    -> not through Create()
```

This theorem deliberately rejects a common convenience API: dictionary assignment keyed by logical ID. If the current object is `verified`, calling a deterministic `propose()` function again cannot replace it with an earlier `proposed` state simply because the same hash ID was recomputed. If an epistemic debt is `resolved`, re-encountering the same condition may produce a **new occurrence/revision** or reopen it through a typed rule, but not reset the old debt by overwriting the row.

Identity also includes semantic scope. Normalized text alone cannot be a claim ID because the same sentence can refer to different entities, principals, validity intervals or regimes. Event identity is distinct from delivery identity and content digest. Region identity is distinct from member-claim identity. Active runtime incarnation is distinct from historical logical identity where delete/recreate, source restart or authority-domain restore creates ABA risk.

The practical benefit is profound: every later system—truth maintenance, repair, migration, replay, shared publication and counterexample lineage—can rely on a stable semantic address rather than guessing whether an ID means “same thing updated,” “new thing with same bytes,” or “old thing accidentally resurrected.”

# 337. Repair theorem: reactivation is justified per object, not inherited from active ancestors

Invalidation needs reachability; reactivation needs proof. A reverse dependency walk is useful for finding objects that **might** be affected by a changed source. It is not itself evidence that every descendant should die, and it is certainly not evidence that every descendant should revive when one parent or replacement becomes active.

For each object `m`, define a type-specific current-validity predicate `Live(m, cut)` over canonical dependencies. A claim can require one live grounded OR-of-AND justification. A representation can require a live source lineage plus valid transformation/preservation contract. A procedure can additionally require applicability/regime. A prospective trigger can require owner/source/condition validity. Repair may update the dependencies, but the state transition back to usable/active occurs only if `Live(m, cut)` becomes true.

This closes S20. Supplying a replacement evidence ID to a repair operation is not enough: the replacement must actually participate in a support/derivation path for the child. Likewise an active parent does not heal a child's invalid direct evidence unless the child's justification says parent activity is sufficient.

A repair receipt therefore records:

```text
repair cause revision
affected candidate set
object-specific predicate evaluated
live justification / transformation path used
replacement evidence links actually admitted
remaining invalid/unknown dependencies
new current state
descendant revalidation frontier
```

When a repair cause is shared—a temporal normalizer defect, entity merge error, origin classifier compromise—the repair cone expands along that shared dependency rather than staying inside one storage region. When the cone cannot be proven complete within the safe budget, the runtime marks it incomplete and refuses to certify dependent frames as current.

The theorem gives repair the same epistemic discipline as creation: lifecycle state is a consequence of current canonical predicates, not a field that a convenience method is allowed to flip.

# 338. Proactive recall theorem: hard memory obligations come from the consequence boundary

The memory runtime is downstream of an agent but upstream of consequences. This is enough to make proactive recall precise without turning memory into a planner.

Given a `RecallBoundaryDescriptor b`, define a bounded obligation compiler:

```text
Hard(b) =
    ExplicitMemoryNeeds(b)
    ∪ CanonicalHardConstraints(b)
    ∪ ActionToolGroundingDependencies(b)
    ∪ FiredProspectiveTriggers(b)
    ∪ RevalidationBlockers(b)
    ∪ RequiredSecurityGovernanceChecks(b)
```

The host/adapter is responsible for exposing the action/tool schema and protected boundary. The model can add optional hypotheses, entities or retrieval probes. It cannot remove `Hard(b)`. This matters for requests whose surface wording omits old preferences or action parameters, and it matters even more when the contemplated action has a different risk or disclosure boundary than the preceding reasoning.

A recalled representation can reveal a new hard dependency. Therefore `Hard` is not necessarily one-pass. The runtime repeatedly hydrates/inspects the representations required by the current hard set, canonicalizes newly discovered hard roles and repeats until a local fixed point. Cycles terminate because role identity is set-valued rather than counted by traversal events. A finite role-universe implementation can bound closure directly; a production implementation uses role/dependency budgets and returns `RECALL_OBLIGATION_OVERFLOW` if closure cannot be established.

This theorem intentionally stops before planning. Memory does not decide whether to call tool T. It says: **if the host is considering boundary T under these semantics, these memory facts/constraints/exceptions must be available and safely usable before T can be treated as memory-grounded**.

The external literature supports the existence of the problem—especially memory-dependent tool parameter grounding and behavioral state decay—but not the completeness of this exact compiler. That remaining external-validity question stays explicit.

# 339. Frame leases: Recall Sufficiency is valid only for a compatible boundary and dependency cut

A Recall Frame is a compiled artifact, not a permanent bag of truth. Its sufficiency assessment is a **compile-time lease over a boundary, cut and material dependency set**.

```text
frame lease binds:
    RecallBoundaryDescriptor
    hard Recall Obligation fixed point
    Recall Cut K
    principal/use/sink profile
    representation/preservation choices
    FrameInformationFlowReceipt
    RecallFrameDependencyManifestRevision D
```

During model reasoning, the frame can remain useful while unrelated memory grows. Before a consequence whose assurance profile requires current grounding, the host validates D. Source revocation, a new applicable counterexample, policy/declassification change, tool-schema change, hard-role closure change or required representation unavailability breaks the lease even when frame bytes are unchanged.

A global-root comparison is safe but too coarse for giant memory. D therefore records material semantic generations. Under-approximation is dangerous; over-approximation causes retries. Dependency extraction has a declared completeness class.

A compatible change creates a refreshed/rebased manifest; it does not mutate the old certificate. Missing current dependency state is `UNKNOWN`, not “probably unchanged.”

For irreversible/tool/export boundaries, the usual profile proceeds to a `MemoryUseFence` bound to final concrete arguments/payload and consumes it at the actual use linearization point. This preserves speed without confusing “was sufficient when compiled” with “is still sufficient now.”

# 340. Composition theorem: per-record authorization is necessary but not sufficient

Let individually admitted fragments be `m1 ... mn` and sink `s`. Per-record authorization establishes predicates such as `Allowed(mi, s)` under their own labels. v0.6.1 explicitly rejects the inference:

\[
orall i\ Allowed(m_i,s)
\Rightarrow
Allowed(Compose(m_1,\ldots,m_n),s)
\]

because reconstruction can create a semantic whole absent from any one fragment. Two harmless fragments may identify a secret only together; separate procedural fragments may instantiate a prohibited instruction only when fused; a private fact and a public mapping table may reveal an identity.

The runtime therefore evaluates **composed information flow** after reconstruction/selection and before the sink receives the payload. The gate does not need to solve arbitrary information theory to be useful. It can conservatively combine confidentiality labels, source/declassification dependencies, structured policy predicates, destination/tool capabilities and known forbidden semantic combinations. Unknown composition risk at a protected sink can produce `SINK_POLICY_OPAQUE/REQUIRES_REVIEW` rather than optimistic allow.

This does not replace early filtering. Unauthorized memory must still be removed before seed/ranking/activation so it cannot influence public reasoning invisibly. The composition gate protects a different seam: authorized atoms creating an unauthorized molecule.

The design also respects hard-role conservation. If the gate removes the only representation covering a hard role, that role becomes unresolved. A security check is allowed to block the action or force safer local processing; it is not allowed to make the memory obligation disappear.

# 341. Memory-use capability algebra separates local reasoning from disclosure and execution

`PrincipalMemoryAccessProfileRevision` is operation-specific. v0.6.1 requires the profile semantics to distinguish at least the following capabilities where the host supports them:

```text
DISCOVER
READ_EXACT
HYDRATE_SOURCE
USE_FOR_LOCAL_REASONING
DERIVE
DISCLOSE_TO_MODEL
DISCLOSE_TO_USER
DISCLOSE_TO_TOOL(tool/sink class)
EXPORT
PUBLISH_TO_DOMAIN
DELETE / CHANGE_RETENTION
```

These are not ordered by a universal “more trusted” scalar. A local policy engine may be permitted to use a private memory to decide whether a request is safe while being forbidden to reveal the private text to the action model. A user may be allowed to read a record but not export it outside the organization. A tool adapter can be authorized to fetch bytes without being authorized to receive unrelated user memory in its parameters.

The capability profile is evaluated at two points: before hidden memory influence and at the actual sink boundary. Declassification is a separate governed transition that can widen disclosure for a derivative; it does not raise factual integrity or evidence independence. Cross-domain publication similarly requires its own capability/policy rather than inheriting `READ`.

This algebra is deliberately host-extensible. Some deployments can merge `DISCLOSE_TO_MODEL` and `USE_FOR_LOCAL_REASONING` because the model is the trusted local computation boundary. Others will separate a privileged policy component from an untrusted/external model. The semantic contract is that such a merge is explicit policy, not an undocumented assumption baked into retrieval code.

# 342. `FrameInformationFlowReceipt`: the proof object for a reconstructed payload crossing a sink

The projection plane needs one new audit object because neither a record ACL nor a Recall Sufficiency certificate answers “may this **composed payload** cross this destination?”

Reference fields:

```text
flow_receipt_id
recall_frame_ref / candidate_payload_digest
principal_ref
sink_class / sink_identity
source_memory_refs
source_confidentiality_profile_refs
declassification_receipt_refs
use/disclosure capability refs
composed_semantic_policy_checks
blocked_or_rewritten_fragment_refs
hard_roles_affected
decision = ALLOW | ALLOW_WITH_TRANSFORM | BLOCK | OPAQUE
procedure/profile revision
created_at
```

The receipt has no factual authority. It is evidence that the runtime applied the declared information-flow policy to the exact composed payload/sink. `ALLOW_WITH_TRANSFORM` can support field-only disclosure, aggregation, redaction or local computation that yields a permitted derivative, but the transform itself must obey the preservation and declassification semantics already defined elsewhere.

Normative rule: **tool-parameter serialization is a disclosure boundary distinct from retrieval access.** For tool calls, the candidate serialized arguments are therefore part of the checked payload. For user/model frames, the exact render or a stable semantic digest/profile is bound. If rendering changes after the receipt, the sink check is stale. This avoids a classic gap in which the safe structured object is checked but an unconstrained renderer later appends private provenance.

The receipt also becomes a frame dependency. Revoking declassification, access policy or sink capability invalidates cached flow decisions without changing the underlying truth. Historical audit can still reconstruct why a past action was allowed under the policy known then.

# 343. Tool memory grounding has two independent gates: adequacy and authority

A memory-using tool call has **three orthogonal gates**:

1. **Memory adequacy** — hard action/tool roles and required precision/applicability are covered.
2. **Memory sink authority** — the exact composed arguments/payload may be disclosed/used at that sink.
3. **Ordinary action authorization** — current host policy permits the concrete operation.

v0.6.3 bridges the reasoning interval:

```text
Recall Frame F at cut K with dependency manifest D
-> model proposes final tool T and canonicalized args A
-> validate D against current semantic generations
-> validate tool/schema/capability generation
-> information-flow check exact payload for T,A
-> issue/validate MemoryUseFence U:
       frame=F
       action_digest=H(T,A)
       current dependency/policy/tool generations
       principal/sink
       optional trusted expiry
       single-use nonce
-> independently obtain action authorization
-> atomically validate/consume U at memory-use linearization
-> dispatch T,A
```

Changing recipient, amount, path, destination, renderer output or another material argument after the fence invalidates the digest. A valid fence cannot grant capability; an action grant cannot substitute for stale memory grounding.

A relevant mutation before fence consumption causes failure/revalidation. A mutation after the linearization point is later history. Memory does not pretend to make external remote effects atomic; high-risk action protocols can add conditional execution or quiescence outside the memory kernel.

# 344. Semantic-region lineage theorem: locality may change while semantic object identity remains stable

Region split/merge is a metadata evolution over repair locality. It does not rewrite the canonical semantic objects merely to keep container membership simple.

For split:

```text
R@k -> {R1@1, R2@1, ...}
```

the runtime records member mappings and representation lineage. Historical references to `R@k` remain valid for historical queries. A current alias of `R` can resolve to one successor only when a declared subsumption relation proves that successor represents the relevant old semantics; otherwise the current resolution is ambiguous and the caller must specify the target/query property.

For merge:

```text
{R1@a, R2@b} -> R3@1
```

member claims/evidence keep their logical/revision identities. Representations that depended on the former boundary are revalidated because granularity or neighbor assumptions may change. Counterexamples and semantic debt bind the semantic target/representation they concern and carry region refs as locality hints, so moving the target cannot orphan the warning.

This is essential for corrigibility. If a counterexample causes a region to split and the counterexample itself is stored “inside the region” with no stable target reference, the repair can erase the witness that justified it. v0.6.1 instead makes the witness survive the locality change.

# 345. Cross-domain publication theorem: transfer is a saga with two epistemic authorities

Cross-domain publication remains a saga with separate epistemic authorities and now explicitly produces **causal read dependencies**.

If A publishes claim A@118 and B admits it at B@87, a later strong B-inclusive recall cannot include B@87 while observing A only through 117. The publication receipt records source/destination domain, incarnation, sequence/root, source logical/revision identity, origin roots and policy generations; the Recall Cut vector closes over those edges.

Republishing does not create independent evidence. Root-origin resolution is a set operation across publication/derivation paths. A→B→C→A can improve availability while still containing one root observation.

At destination admission, source dependencies are revalidated as v0.6.2 requires. At recall, cut closure prevents destination imports from floating free of their source history. If a required domain frontier cannot serve its vector component, strong currentness/absence is unavailable.

This gives coherent bounded shared recall without introducing global consensus or one global clock. A future atomic invariant spanning several domains would require a stronger explicit distributed protocol, not a hidden upgrade of memory semantics.

# 346. Semantic working-set theorem: backpressure may reduce speed and optional breadth, not hard-memory semantics

Treat the current hard memory set as a working set whose members may reside at different representation/source tiers. When repeated semantic page faults exceed the runtime's ability to keep required witnesses hot, the system enters a resource state analogous to virtual-memory thrashing.

The correct response order is:

```text
shed optional associative exploration
reduce prefetch / speculative prospection
defer nonurgent consolidation
pin repeatedly faulted hard witnesses where policy permits
use certified compact representations for dimensions they actually preserve
stage the decision under a stable Recall Cut
apply backpressure / ask host for more resource budget
return THRASHING / OVERFLOW / INSUFFICIENT when necessary
```

The forbidden response is to silently substitute a cheaper representation that does not cover the hard semantic property. A stale summary may remain useful optional context; it cannot satisfy `EXACT_NUMBER` or `CURRENT_POLICY_CONSTRAINT` merely because the exact witness is slow.

This law makes context efficiency falsifiable. Under fixed true dependency width, a good implementation should keep model context approximately stable as total history grows. Under a genuinely large hard dependency width or hostile alternating working set, cost may rise or the runtime may refuse the boundary. The spec does not require impossible constant context; it requires that pressure be paid in latency/overflow rather than hidden semantic loss.

# 347. v0.6.1 model-free Seam Calculus

The seam rules above were encoded in a separate deterministic reference harness rather than asserted only in Markdown.

Artifact:

```text
NOLANE-MEMORY-V0.6.1-SEAM-CALCULUS-RESULTS.json
revision = NM-v0.6.1-seam-calculus-1
families = 36 passed / 0 failed
bounded/fuzz cases = 80553
semantic failures = 0
digest = a0f3d9bd565befd7447d8531a7b28ff2cd586de0f015838c38918ee0c12328c7
```

The 36 property families cover immutable create/revise/lifecycle semantics, live-justification repair, proactive action/tool obligations, obligation fixed points and cycle termination, boundary-invalidated frame reuse, restrictive confidentiality composition, declassification, local-reasoning-versus-tool disclosure, fragment fusion, pre-influence principal filtering, region split/merge identity conservation, cross-domain publication partial states, eventual shared visibility, resource shedding, semantic page-fault starvation, working-set thrashing, fresh-start memory reliance, tool capability projection and tool-parameter disclosure.

Four stress families contribute 80,000 of the 80,553 cases: 20k obligation-closure fuzz, 20k region split/merge identity-conservation fuzz, 20k confidentiality-composition fuzz and 20k hard-role resource-pressure fuzz.

Passing this harness means the **bounded reference semantics are internally consistent for those modeled properties**. It does not show that a natural-language parser can identify every private composition, that production dependency graphs remain tractable, or that the proposed policy achieves good latency. Those limitations are part of the artifact.

# 348. Source regression and negative-result discipline

After widening the Nolane World selection beyond `memory|truth|recovery` to include epistemic, counterexample, research, security, scope/access/capability, journal and experience surfaces, the **final fresh run for this release** selects 42 packaged test files and reports:

```text
154 passed
0 failed
3.97 seconds
```

This result is deliberately reported beside S17–S23 rather than instead of them. The packaged tests and adversarial probes answer different questions. A green suite demonstrates that covered intended behaviors remain executable. A minimal counterexample can still prove that an untested semantic invariant is absent. The architecture therefore follows the stronger rule:

> **A passed suite cannot waive a reproduced violation of a kernel semantic law; the violation becomes a new permanent regression obligation.**

The research process also records non-semantic execution failures instead of silently discarding them. The first attempt at this final regression used `PYTHONPATH=src` and failed during collection because two tests import repository-root modules under `scripts/` and `evals/`. No tests had executed. The environment contract was corrected to `PYTHONPATH=src:.`, after which the exact same 42-file selection produced the 154/154 result above. This is an environment/configuration failure, not evidence against a memory invariant, but disclosing it prevents a misleading impression that every attempted run was green.

A separate artifact-generation attempt for the seam-calculus harness also encountered a Python module-loading/dataclass issue. The saved harness was subsequently executed as a clean standalone Python process, its JSON output reparsed, and only that clean-process result was accepted. Neither tooling issue is counted as an oracle failure; both remain part of the trial provenance.

The point is methodological: **negative or failed runs are classified, not erased**. Semantic failure, environment failure, test-harness failure and model uncertainty have different meanings and must not be averaged into one success number.

# 349. Claim-scoped evidence authority for the specification itself

The specification applies its own origin/authority rules to research evidence. The current release bundle contains `NOLANE-MEMORY-V0.6.3-CLAIM-SCOPED-EVIDENCE-REGISTER.json` with 53 external sources (`EA-01..EA-53`) and 4 internal/user-supplied source classes.

Every entry records:

```text
source identity/title
publication/evidence class
canonical URL or internal locator
allowed inference
not-established / forbidden overclaim
which Nolane semantic surface it informs
```

The register prevents several research-laundering errors. An arXiv preprint is never relabeled peer-reviewed because it is convenient. A benchmark demonstrating weak proactive tool grounding does not prove Nolane's proactive compiler works. A memory poisoning attack against tested systems does not prove the proposed defense closes all variants. A user-supplied prior spec can inform architecture/method but is not independent validation. A source-code counterexample proves behavior of the supplied bundle/version, not all upstream history.

The current register digest is:

```text
7d19a5222cd7392a9f36f7dce9d07853d2369bc403a1255805c9a613de399e80
```

The full register is reproduced in Appendix S so the Markdown remains self-auditable, while the JSON is the machine-readable companion.

# 350. Nolane World W5 seam campaign remains blocked after semantic clarification

A dedicated W5 world asked:

> What is the smallest additional semantic closure required for v0.6 to be implementation-trustworthy across proactive action use, compositional confidentiality, immutable identity, repair and long-lived resource pressure?

Adaptive depth selected level 5 with score `0.936`. The campaign retained rival hypotheses, assumption stress, source-independence structure and a runtime-owned closure gate. The resulting W5 verdict remains:

```text
verdict = BLOCKED
open epistemic debts = 7
blockers = 23
snapshot digest = b0c11739f9ceaa6510f96a6c9d1f0a2ef4528f38d5b05b4cafb51c00c8735e3a
```

The seven seam debts are:

| Debt | Severity | Meaning | W5 state |
|---|---:|---|---|
| `compositional-information-flow` | 0.99 | Need frame/sink-level information-flow closure so individually authorized fragments cannot combine into unauthorized disclosure/action influence. | `open` |
| `proactive-obligation-completeness` | 0.98 | Need bounded semantics for deriving hard Recall Obligations from action/tool/decision boundaries when the query does not explicitly request the needed memory. | `open` |
| `repair-live-justification` | 0.96 | Need repair theorem requiring each reactivated claim/representation to regain its own live justification, not merely active ancestors. | `open` |
| `identity-revision-immutability` | 0.94 | Need explicit same-ID collision/revision/resurrection conformance law across evidence, claim, graph, restore and migration paths. | `open` |
| `semantic-region-split-merge-lineage` | 0.86 | Need stable lineage/reference semantics across region split/merge so envelopes, counterexamples, debt and frame handles cannot orphan or alias incorrectly. | `open` |
| `semantic-working-set-thrashing` | 0.82 | Need correctness-preserving backpressure/fault-loop semantics for repeated semantic page faults and maintenance/verification starvation. | `open` |
| `cross-domain-transaction-boundary` | 0.80 | Need explicit rule for what cross-domain publish/import can guarantee atomically and how partial failure is represented without creating global consensus semantics. | `open` |

Sections 336–346 give these debts **bounded semantic homes**: an implementer no longer has to invent what create/resurrection, proactive hard roles, sink composition, region lineage, publication partial states or thrashing should mean. That does not automatically discharge the W5 debts. They also contain external-validity, completeness, calibration, implementation and independent-verification questions that this document cannot self-certify.

This distinction is central to the target confidence level: the spec should be highly determinate even where the research evidence is honestly incomplete.

# 351. v0.6.1 differential conformance additions

The future two-implementation conformance corpus gains seam-specific fixtures:

```text
same-ID same-semantics Create after VERIFIED/RESOLVED/REVOKED
same-ID different-semantics Create collision
predecessor-bound revision
reactivation with/without own live justification

query-only versus action-boundary proactive obligation
tool schema containing a memory-dependent parameter
page fault exposing a new hard dependency
cyclic prospective/obligation dependencies

two individually allowed fragments whose composition is forbidden
private local-reasoning memory copied toward an untrusted tool
declassification revoked between frame compile and sink
same payload under different sink capability profiles

region split with historical handle
region split with ambiguous current successors
region merge preserving member claim IDs
counterexample/debt surviving region relocation

source publication committed while destination pending
source revocation during pending destination import
destination rejection without source rollback

alternating exact-page faults creating working-set thrash
resource exhaustion with hard roles above frame budget
optional-memory shedding under protected hard roles
```

Comparison uses the existing `MemoryConformanceVector`, extended with boundary/obligation fixed point, logical/revision identity, live reactivation proof, region lineage resolution, publication state and information-flow receipt where material. Two implementations can choose different databases, graph indexes or compression algorithms; they may not disagree about whether a same-ID write is a collision, whether a repaired child is grounded, whether a required tool parameter was a hard role, or whether a composed payload was authorized to leave the memory boundary.

A divergence in these fields is evidence of spec ambiguity or implementation nonconformance—not “model creativity.”

# 352. v0.6.1 theory stop rule and trust target

After this seam hardening, another theory revision is justified only by evidence of the same quality class that justified v0.6 and v0.6.1:

```text
a new executable counterexample against the current semantic laws
a bounded formal/model-checking trace showing composition failure
an independent-implementation conformance mismatch
a migration/replay fixture that loses identity/authority/preservation
a real tool/security/recall experiment contradicting a declared capability
a materially new research result that creates a correctness distinction
```

A plausible story of “maybe memory could also do X” is not enough. A new benchmark score is not enough unless it exposes a semantic gap. A new memory taxonomy is not enough. The next expected work remains implementation and independent differential conformance.

The v0.6.1 trust target is deliberately stronger than “well designed” and weaker than “proven correct”:

> **An expert reader should be able to trace every consequential memory transition from evidence identity through revision/justification/preservation, through a proactive boundary-aware Recall Obligation, into a bounded frame whose hard roles and information-flow permissions are both explicit; and when the runtime cannot establish one of those facts, the specification should already name the failure rather than forcing the implementer to invent a hidden rule.**

That is the level of theoretical reliability the document can responsibly seek before production evidence exists.

---

---

# PART XXXI — V0.6.2 CONTINUITY, RECOVERY AND ERASURE CLOSURE

# 353. Why v0.6.2 exists: a memory can be historically authentic and still be forbidden to revive

v0.6.1 closed several seams between write identity, repair, proactive recall and information flow. The next audit found a different class of ambiguity: **the artifact used to preserve continuity can itself become a stale or forbidden memory source**.

A valid checkpoint can faithfully contain a secret that policy deleted later. A handoff can truthfully summarize an old mission while being wrong for the current one. An anchor can contain an accurate state digest for an old cut while the actual session has moved forward. A replay certificate can prove one canonical journal history without proving that the recovered procedures, access grants or deleted payloads may become current-usable again. A bounded handoff can preserve the most recent failures while silently dropping the oldest catastrophic `do-not-repeat` instruction.

These are not new feature requests. They are consequences of treating recovery, anchors, handoff and deletion as independent modules. The seam question is:

> **What exactly is a recovery artifact allowed to prove, and what later events must dominate it before future-self can use the reconstructed memory?**

v0.6.2 answers by treating continuity artifacts as ordinary derived representations with preservation/invalidation contracts; separating byte/history recovery from resume authority; introducing non-revivable governance barriers into restore semantics; requiring deletion closure across derived/read/continuity/restore surfaces; and making rollback dimension-specific rather than a global time-machine.

Only two genuinely new audit/projection primitives are admitted: `RecoveryResumeAssessment` and `MemoryErasureClosureReceipt`. `RetentionEventRevision` already existed in the canonical data model but was missing from the authoritative Closure Matrix; `SelfVersionProfileRevision` resolves an already-present self-version concept whose authority owner was previously implicit. This is hardening, not scope expansion.

# 354. Fresh Nolane World findings S24–S30 expose continuity artifacts as an authority seam

A clean source audit of the supplied Nolane World bundle reproduced seven behaviors:

| Finding | Reproduced behavior | Semantic pressure |
|---|---|---|
| S24 | a verified claim remains in handoff `what_is_true` after a human mission override because the claim has no mission compatibility scope | handoff current truth needs compatibility typing |
| S25 | session state changes after anchor creation, anchor `state_digest` becomes stale, yet boot can still return `resume_allowed=True` | anchor root/cut must participate in resume predicate |
| S26 | serialized anchor state digest and hypothesis/plan refs can be forged/dangling; `from_dict` accepts them and boot can resume | pin payload/reference integrity needs authentication/validation |
| S27 | 13 failures produce a handoff containing only the last 12, silently dropping the oldest critical prevention | handoff compression needs hard-role preservation rather than recency |
| S28 | `DurableMemoryRecord.invalidates_on` is stored but the registry recall path has no active invalidation-event state | compatibility dependencies must be executable predicates, not annotations |
| S29 | a digest-valid pre-delete checkpoint faithfully reloads a secret absent from current state | restore integrity is distinct from current erasure authority |
| S30 | anchor contains an unverified hard-constraint blocker and boot reports that blocker, yet `resume_allowed=True` | verification blockers must gate resume |

S29 is intentionally classified differently: isolated `CheckpointStore` is doing what a checkpoint should do—preserving historical bytes. The counterexample arises only when a recovery layer mistakes **authentic old state** for **authorized current state** after a deletion barrier. This distinction prevents the spec from labeling every historical backup a bug while still closing the dangerous restore path.

The source artifact records all seven reproductions:

```text
revision = NM-v0.6.2-continuity-source-seam-audit-1
findings = 7
all_reproduced = true
digest = b02b8973ae40b07e5f9fa2fd48a92a6aa0398c394e354bbbda67b4cf341b3704
```

These findings are stronger than a prose thought experiment because the supplied system already embodies the shortcuts a future implementation might naturally choose.

# 355. Continuity artifacts are representation fibers and must obey preservation, provenance and invalidation

Anchor, handoff and recovery summaries are not exemptions from the Representation Plane. They are specialized representation roles whose purpose is to survive context/process/self-version discontinuity.

A continuity representation therefore owns:

```text
presentation / bounded boot payload
hard continuity-role cover
source/revision handles
cut/root binding
sender/self-version identity
preservation envelope
recoverability status
payload digest
```

It must never own the underlying factual truth, verification outcome, mission authority or current access decision. A statement rendered as `what_is_true` is model-facing shorthand for one or more `ClaimRevision`/`HistoricalJudgementRevision` references and their compatibility assessment.

This has several consequences. Deleting a private source can taint a handoff or anchor just as it taints an ordinary summary. A mission change can make some packet claims historical/advisory without deleting the old packet. A stronger self-version can reinterpret an old failure lesson while preserving what the earlier agent observed. A transformation counterexample can prove that a compact handoff omitted an exception, causing the handoff representation contract to be refined without rewriting the canonical event.

The architecture thus avoids a paradox: a system that rigorously controls semantic summaries but trusts its “recovery summary” blindly would have created exactly one privileged summary capable of bypassing every rule. v0.6.2 removes that privilege. Continuity is powerful because the packet is small and high leverage, not because it is exempt from evidence semantics.

# 356. Continuity-pin authenticity and selection theorem

A pin is usable only when its **artifact identity, canonical cut and current compatibility** all validate.

Reference predicate:

```text
PinUsable(pin, recovery_request) =
    payload_integrity_valid
    ∧ logical/revision identity valid
    ∧ pin.cut/root is authenticated and replay-resolvable
    ∧ protected references exist at that cut
    ∧ no unresolved pin verification blocker
    ∧ mission/objective compatibility
    ∧ current access/governance compatibility
    ∧ self-version/tool/environment compatibility or explicit revalidation
    ∧ no post-pin non-revivable barrier forbids required content/use
```

Selection is then over `PinUsable` candidates. Serialized list position is never semantic freshness. `latest` means highest compatible canonical sequence/revision under the recovery lineage, with deterministic tie-breaking and explicit handling of forks. A newer pin that is blocked or references a compromised source loses to an older compatible pin; if the older pin itself predates a deletion/revocation affecting required content, it can reconstruct history but cannot bypass the barrier.

The pin's state/dependency root is useful only if checked. Merely storing a digest and never comparing it during boot is metadata theatre. Likewise storing `verification_blockers` but excluding them from `resume_allowed` creates two contradictory clocks for readiness.

When no pin passes, recovery can still fall back to canonical replay plus a newly compiled continuity obligation. The pin improves efficiency and direction; it is not a single point of epistemic survival.

# 357. Handoff completeness theorem: boundedness is a hard-role cover problem, not a last-N problem

A handoff is necessarily lossy. The correctness question is therefore not “did it include enough recent items?” but:

> **Does the packet preserve or point to every continuity role that the receiver is required to know before the next bounded boundary?**

Hard continuity roles can include protected objective/constraints, unresolved blockers, catastrophic failure conditions, active `do-not-repeat` rules, source-compromise warnings, current mission-scoped facts, and exact handles needed to reconstruct an open decision. Optional roles include routine old attempts, redundant narrative explanation and low-impact episode detail.

For packet budget `B`, handoff compilation first solves hard cover. If all hard roles fit, optional material fills the remaining budget. If they do not fit, the packet uses stable hydratable handles, structured compression whose preservation envelope covers the role, staged recovery, or returns `HANDOFF_OVERFLOW/CONTINUITY_INSUFFICIENT`. Pure recency is never permitted to decide which hard role vanishes.

This rule directly closes S27. The first failure in a sequence can remain the most important one if it is the only witness for “never perform destructive action X under condition C.” Twelve newer routine failures do not outrank it simply because they are newer.

Packet consumers also re-evaluate applicability. `do_not_repeat` means “do not repeat under the condition that made this harmful,” not a universal prohibition unless evidence supports that scope. This preserves Tề Hạ-style concise future-self warnings without turning them into context-free commandments.

# 358. Recovery Trust Stack: integrity, replay, compatibility, governance and sufficiency are different proofs

The runtime uses a layered recovery model because one certificate cannot honestly establish all recovery claims.

**R0 Storage Integrity** proves artifacts/journal/snapshot bytes are authentic according to their local persistence contract.  
**R1 Canonical Replay** proves one committed canonical history/root was reconstructed.  
**R2 Semantic Compatibility** proves schema/migration/normalizer contracts preserve or explicitly downgrade meaning.  
**R3 Non-Revival Barrier Closure** proves later delete/revoke/compromise/declassification barriers dominate any older restore material.  
**R4 Continuity Compatibility** validates selected pin/handoff references, blockers, mission and self-version.  
**R5 Environment Compatibility** rechecks live tool/world state where old evidence can drift.  
**R6 Recall Sufficiency** compiles a fresh consequence boundary and proves all hard memory obligations are currently coverable and authorized.

`RecoveryResumeAssessment` binds the inputs/results of the required levels for one boot attempt. It has no factual authority; it certifies only whether the reconstructed agent is allowed to resume under the declared recovery profile.

This stack explains how a system can report:

```text
storage integrity       PASS
canonical replay        PASS
semantic migration      PASS
erasure closure         BLOCKED
continuity pin          PASS
environment             PASS
recall sufficiency      NOT EVALUATED

=> RESUME_ALLOWED = false
```

This is not a partial failure to hide. It is the precise state required to prevent an integrity-valid backup from becoming a privacy/security resurrection mechanism.

# 359. Non-revivable barrier theorem: stale restore points cannot undo later deletion, revocation or compromise

Some state transitions are **monotone with respect to ordinary snapshot selection**. Privacy deletion, access revocation, declassification revocation and source-compromise decisions cannot be undone merely by restoring an older snapshot in which those transitions had not yet occurred.

Let snapshot `S@k` predate barrier `B@n`, with `n > k`. Recovering `S` can reconstruct historical state at `k`, but before making it current-usable the recovery kernel must apply every barrier in the relevant governance lineage through the requested current recovery cut. If the barrier log needed to determine current permission is unavailable, the affected scope becomes `RECOVERY_GOVERNANCE_OPAQUE` and fails closed.

This does **not** mean all barriers are irreversible forever. Governance can explicitly re-grant access, reclassify data, or—where law/policy allows—restore previously deleted material from an authorized source. Such an event is a new current transition with its own authority. It is not a side effect of choosing an older backup.

The theorem also applies to compromise. An old snapshot can truthfully contain a certificate/source that was trusted then. If that source was later compromised, the historical judgement remains explainable while current reuse is blocked/revalidated.

This separation is what allows serious version control and serious privacy to coexist: historical memory can be inspected as history without granting history automatic control over the present.

# 360. Semantic rollback and governance rollback are orthogonal dimensions

Memory rollback is useful for user corrections, concept drift, poisoning recovery and accidental updates. But “rollback” is not one scalar clock.

A semantic rollback can create a new current revision whose factual/representation content intentionally matches an older state:

```text
preference B was wrong
-> authorized rollback selects earlier preference A
```

The transition is still new. Historical updates B and the rollback event remain part of the knowledge history.

Governance dimensions are evaluated separately:

```text
content/version rollback
epistemic support rollback/re-evaluation
access/confidentiality state
retention/deletion state
source compromise state
declassification state
consumer/self-version state
```

Choosing old content does not choose old permissions. A rollback to a pre-deletion version does not undelete the private source. A rollback to a pre-revocation representation does not restore an old access grant. A rollback after source poisoning may restore earlier semantic content but still remember that the source is compromised.

ChronoMem and related rollback work provide useful pressure that semantic version control is a real agent-memory operation. v0.6.2 adds the complementary theorem needed for a governance-oriented runtime: **rollback is a typed new transition over selected dimensions, never global time travel.**

# 361. Erasure closure theorem: raw deletion, factual support and representation residue are three different questions

Normative distinction: **Raw deletion, factual support and representation residue are three different questions.**

Suppose private source `P` and public source `U` both support proposition X. A summary `S` was generated using P and U and contains a private detail available only in P. Later policy deletes P.

Three evaluations occur:

1. **Epistemic support:** U may keep X supported.
2. **Recoverability:** exact details unique to P may become irrecoverable.
3. **Representation residue:** the existing bytes of S are tainted because they were generated with P, even though X remains true through U.

Therefore the runtime cannot simply remove P from the support graph and keep serving S as public. It must purge/quarantine S or generate `S'` **from surviving admissible sources** under a fresh transformation/information-flow contract. `S'` can express X while proving it no longer relies on P.

The same reasoning applies to procedures, episode summaries, embeddings with recoverable text mappings, anchors and handoff packets. Whether an opaque embedding/index must be physically rebuilt depends on the host's leakage model and erasure policy, but a strong erasure claim cannot ignore a read surface merely because it is “derived.”

This theorem is supported by current deployment-time memorization research showing that raw-only deletion can leave recoverable derived residue in the evaluated systems. The paper does not prove Nolane's closure sufficient; it proves why “delete raw row” is an inadequate definition of forgetting fidelity.

# 362. Clean rederivation after erasure is not equivalent to relabeling an old derivative

A derivative that depended on deleted source P cannot become clean by editing its provenance metadata to remove P. The content itself may encode P.

A legal clean rederivation transition requires:

```text
new RepresentationRevision
surviving source set
fresh transformation contract/profile
fresh preservation/information-flow verification
new content digest
explicit predecessor/tainted-derivative relation
```

The old derivative becomes deleted, quarantined, inaccessible or historical-forensic according to policy. The new derivative can inherit factual proposition support from independent surviving sources, but it does not inherit the old payload's disclosure clearance.

This is a direct application of the authority non-malleability rule to privacy: pure metadata mutation cannot transform a representation that *used private information* into one proven not to contain private information.

When the source deletion also removes the last witness for a protected semantic dimension, clean rederivation may be impossible. The runtime then records `IRRECOVERABLE_GAP` rather than hallucinating the detail from descendants. If a later user re-supplies the information as new authorized evidence, that is a new source event and may restore the capability.

# 363. Erasure closure includes restore paths, continuity artifacts and read surfaces

A serious deletion protocol has a completion criterion. `MemoryErasureClosureReceipt` records the declared erasure scope and each surface required by the host policy:

```text
canonical source availability
dependent representation closure
continuity pin / handoff closure
lexical/dense/graph/temporal indexes
query/result caches
export/shared publication obligations under local control
snapshot/backup restore barriers
clean rederivations
remaining opaque/unreachable surfaces
recoverability/capability downgrades
```

It does not promise deletion from systems outside the host's authority. Such targets are listed as external obligations/unknowns, not falsely marked closed.

Read surfaces use durable contiguous purge frontiers analogous to visibility frontiers. If index commits 100 and 102 are applied while deletion mutation 101 is missing, `max(seq)=102` cannot certify erasure through 102. Strong current recall either overlays the canonical negative mutation, waits for catch-up or blocks the surface.

Continuity artifacts deserve explicit inclusion because they are optimized precisely to survive restart. An old handoff containing a private name can otherwise become the copy that defeats an otherwise correct main-store purge. Backups deserve inclusion because their purpose is to resurrect old bytes. The solution is not necessarily to destroy every historical backup immediately; it is to ensure recovery enforces the later erasure barrier before the bytes can re-enter current memory use.

# 364. Mission and self-version compatibility are explicit memory applicability dimensions

S24 demonstrates the danger of a handoff field called `what_is_true` when claims themselves carry no mission compatibility scope. Some claims are world facts and remain current across mission changes. Others encode task assumptions, branch decisions, temporary targets or constraints whose meaning depends on the old mission. A runtime that cannot distinguish them must conservatively reclassify rather than assume universal transfer.

Claims/representations can therefore declare applicability scope such as:

```text
GLOBAL/WORLD
AUTHORITY_DOMAIN
PROJECT
MISSION:<revision>
SELF_VERSION / EXECUTOR PROFILE
TOOL/REGIME
TASK/EPISODE
```

The exact scope algebra remains host-extensible, but current handoff/boot use requires a compatibility predicate. Mission transition does not destroy the old claim; it can move it from `CURRENT_USABLE` to `HISTORICAL/REVALIDATION_REQUIRED` for the new boundary.

`SelfVersionProfileRevision` resolves a related ownership gap in v0.6.1. Model/tool/runtime capability is not world truth, but it is durable compatibility context for procedures, rendering profiles, effect/interference evidence and continuity. A new model version should not force all external facts stale, yet old execution tactics can require re-verification.

This product-state view prevents both over-invalidation and stale transfer: preserve what the past established, but make current usability explicit.

# 365. Invalidation dependencies are executable predicates, not decorative metadata

v0.6.3 generalizes the earlier invalidation rule into the **Operational Semantic Field Law**:

> A field participating in a correctness/safety claim is authoritative only if the spec names its owner, mandatory evaluation path, freshness basis and fail-visible outcome.

| Field/property | Evaluator | Mandatory boundary |
|---|---|---|
| `invalidates_on` | dependency/revalidation kernel | recall/boot/promotion as applicable |
| protected `expires_at` | lease validator + trusted clock authority | authorize/use |
| context/task/model scope | applicability resolver | before retrieval influence and before use |
| hard Recall role | frame compiler | sufficiency + post-filter recomputation |
| authority ceiling | admission/use validator | promotion/consequence |
| declassification/access generation | information-flow policy | frame/sink use |
| preservation/recoverability | representation resolver | page fault/consolidation/forgetting |
| mission/self-version | compatibility resolver | handoff/boot/procedure/use |

A field without a mandatory evaluator is `ADVISORY_METADATA`.

Protected expiry requires a real time authority. A same-process lease can use the issuer's monotonic clock plus a clock epoch and half-open interval `[issued, expires)`. If time/epoch cannot be evaluated, the result is `CLOCK_AUTHORITY_REQUIRED`. Raw monotonic timestamps are not portable across restart/host; cross-host expiry needs a specified time authority/skew contract or logical-generation validity.

World-valid fact time and lease validity remain separate: a true fact can be forbidden to use, and a live lease cannot make an obsolete fact true.

# 366. Continuity packages are cut-closed: every strong reference is revision-pinned

A strong continuity package or Recall result is **cut-closed**. v0.6.3 extends K from a scalar to a vector when the bounded view spans independently ordered authority domains.

```text
single domain:
    K = (domain, incarnation, sequence, root)

multi-domain:
    K = {
        A: (incarnation, seq, root),
        B: (incarnation, seq, root),
        policy: (incarnation, seq, root)
    }
```

Every strong reference resolves to a revision visible within its domain component. Cross-domain publication/import edges impose causal closure: if K includes destination import `B@87 <- A@118`, K[A] must include at least 118. A cut can be monotonically extended to predecessors, but the whole result is revalidated against the upgraded vector.

Nested “latest” reads are forbidden in a strong result. Conflict lookup, page fault or source hydration either reads the same K, overlays an exact canonical delta, or requests a cut upgrade followed by revalidation. It cannot return an old row with a newer lifecycle field and call the combination coherent.

Indexes expose per-domain frontiers. A lagging frontier participates only with a complete canonical delta. Negative/completeness results bind predicate + domain + K/generation.

Historical continuity can bind old K while current recovery still applies later erasure/revocation barriers. Cut consistency answers **which history is observed**; use-time validation answers **whether the derived conclusion remains valid now**.

# 367. Boot revalidation runs to a hard-dependency fixed point

Validating the pin itself is not the end of recovery. Hydrating its protected procedure can reveal a tool capability dependency; checking the tool can reveal a new environment version; loading a failure can expose a `do-not-repeat` counterexample; applying a deletion barrier can remove the only source for an exact parameter.

Recovery therefore uses the same hard-obligation closure law introduced for proactive recall:

```text
initial boot roles from continuity pin + current governance
-> hydrate/validate
-> add newly exposed hard dependencies
-> repeat
until fixed point
or typed overflow/opaque dependency
```

Cycles collapse by canonical role/dependency identity. The kernel records why each new boot role entered the closure. Optional historical context can wait until after resume; hard blockers cannot.

Only after the recovery trust stack and this dependency closure pass does the runtime compile the first model-facing Recall Frame. This avoids a common restart pattern in which the bootloader says “resume allowed,” then the first action discovers that a source, permission or tool changed.

S30 is the smallest instance: the anchor already knew an unverified hard constraint existed, yet that blocker did not enter the resume predicate. v0.6.2 makes blocker propagation a general fixed-point rule rather than a special-case `if` statement.

# 368. `next_best_action` and prior-self policy are continuity priors, not resume authority

Tề Hạ-style self-coordination relies on future-self inferring what past-self intended. That is powerful, but it must remain epistemically typed.

A handoff field such as:

```text
next_best_action = "measure listener count"
```

means:

> at sender cut κ, under sender self-version/environment/mission, this was the recommended next probe/action.

It does not mean the receiver is authorized to execute it. The future self treats it as a prior over which Recall Boundary to examine first. Before any consequential action, it recompiles the current boundary, hydrates required memory, checks current capabilities/access, evaluates non-revivable barriers and obtains normal action authorization from the host.

If the environment drifted, the action can remain useful as a hypothesis while losing immediate executability. If the tool disappeared, the intent can be translated into another probe. If the mission changed, the action may be historically interesting but irrelevant.

This is the engineering form of the Tề Hạ principle already present throughout Nolane Memory: past-self artifacts preserve **direction and reasoning evidence**, not sovereignty over future-self.

# 369. Current research pressure specifically supports deletion-residue and rollback separation, not the whole design

The v0.6.2 evidence register adds focused current literature pressure.

**Deployment-Time Memorization in Foundation-Model Agents** introduces deletion-fidelity measurement across memory tiers and reports that raw-only deletion can leave derived summary residue in the evaluated systems. Nolane uses this to justify a closure criterion across derived representations; it does not claim the paper proves Nolane's purge algorithm.

**Agent-Memory Protocol** provides additional pressure for an explicit privacy boundary between persistent user memory and computational/model interfaces; it does not prove the current confidentiality algebra.

**Hidden in Memory: Sleeper Memory Poisoning** demonstrates a cross-session attack path where external content causes fabricated persistent memory that later influences actions. This strengthens the case that continuity/recovery artifacts must preserve provenance and revalidation rather than assuming persisted state is safe.

The **Long-Term Memory Security survey** organizes security across Write, Store, Retrieve, Execute, Share/Propagate and Forget/Rollback, reinforcing the idea that rollback/forgetting are system-level governance surfaces rather than retrieval settings.

**ChronoMem** demonstrates that semantic memory rollback/version selection is a useful first-class operation. Nolane draws the opposite-side requirement: semantic rollback must not silently rollback privacy/security governance.

**Control-Plane Placement Shapes Forgetting** pressures the architecture to treat mutation-time forgetting as distinct from recall filtering.

The claim-scoped register explicitly records what each source does **not** establish. This prevents literature breadth from being laundered into architecture certainty.

# 370. v0.6.2 Continuity–Recovery–Erasure Calculus

The new seam laws are encoded in a separate deterministic model-free harness.

Artifact:

```text
revision = NM-v0.6.2-continuity-recovery-erasure-calculus-1
property families = 24 / 24 passed
bounded/fuzz cases = 135880
semantic failures = 0
digest = f093b10ff56ba25f97727b09c4536ad524a0406ed6070bd3bd5bcdb0eb5bf9cf
```

The 24 families cover anchor authenticity/cut/blocker/reference predicates, order-independent compatible pin selection, verification-blocker gating, hard handoff cover, recovery trust-level conjunction, post-snapshot barrier dominance, derived residue rederivation/purge, contiguous purge frontiers, continuity-artifact erasure, cut-closed handoff references, mission scope, active invalidation dependencies, declassification revocation, source-compromise semantics, advisory next-action, dimensioned rollback and recovery fixed-point closure.

Four large randomized worlds contribute 130,000 cases: 40k recovery barrier-resurrection traces, 30k handoff hard-cover budgets, 30k derivative erasure worlds and 30k recovery trust-stack combinations.

The first attempt to execute the saved harness failed because its own source omitted `import itertools`. That was a harness defect, not a semantic counterexample. The exact script was patched only at the missing import, rerun as an independent process, JSON-reparsed and accepted only after all families passed. The failed attempt remains part of the research provenance.

As always, bounded consistency is not production proof. Real backup topologies, legal deletion regimes, semantic classifiers and distributed storage surfaces remain external-validity debt.

# 371. Fresh continuity/persistence regression of Nolane World

The source regression selection was widened again to include file names associated with:

```text
memory
truth
recovery
checkpoint
handoff
anchor
mission
replay
epistemic
counterexample
research
security
scope/access/capability
journal
experience
persistence
```

This selected 50 packaged test files from the supplied bundle.

Fresh result:

```text
205 passed
0 failed
3.09 seconds

fresh regression attestation digest = 735e286e48cf099d942a53e480f5f81f26aad12d9b28522ed78f986415f0dc75
```

The result coexists with S24–S30. Packaged tests establish covered intended behavior; the source counterexamples establish that additional semantic constraints are absent or unenforced. The correct response is neither “tests are useless” nor “green tests waive the counterexample.” Each reproduced seam becomes a regression obligation for the future unified kernel.

The expanded run is particularly useful for recovery work because it includes v5 deterministic replay/recovery tests and QX memory bootloader/handoff tests in the same selected corpus. This confirms the baseline mechanisms remain executable while making clear that **mechanism correctness at its tested abstraction level is not equivalent to the stronger cross-layer theorem** now required.

# 372. W5 continuity/recovery campaign remains blocked after the formal closure

A new W5 depth-5 session asked what semantics are required so anchors, handoffs, snapshots, deletion and revocation cannot reintroduce stale or forbidden memory across context resets.

Runtime result:

```text
depth = 5
required gates = 16
open debts = 8
closure = BLOCKED
blockers = 24
digest = 4128d46623c0c32ffc37695b01369c40073ed46df883f7faca2a3f9e88389531
```

Open debts:

| Debt | Severity | Meaning | W5 state |
|---|---:|---|---|
| `continuity-cut-authenticity` | 0.99 | continuity anchors/handoffs need authenticated cut/source binding and deterministic compatible selection | `open` |
| `recovery-erasure-monotonicity` | 0.99 | post-snapshot deletion/revocation/compromise barriers must dominate recovery and rollback | `open` |
| `derived-deletion-residue` | 0.99 | raw deletion must close derived summaries/index/cache/continuity artifact residues before claiming erasure | `open` |
| `handoff-hard-role-completeness` | 0.98 | bounded handoff must preserve hard continuity roles independent of recency/order | `open` |
| `anchor-verification-blocker-gating` | 0.97 | recovery resume decision must not ignore unresolved verification blockers present in continuity artifact | `open` |
| `recovery-level-separation` | 0.96 | physical replay integrity, semantic state compatibility, resume authority and Recall Sufficiency require distinct certificates/status | `open` |
| `mission-self-version-scope` | 0.94 | current usability of carried claims/procedures across mission/self-version transition requires compatibility semantics | `open` |
| `active-invalidation-dependencies` | 0.93 | invalidates_on and other compatibility dependencies must participate in current recall/boot predicates rather than remain inert metadata | `open` |

The new sections give each debt a **bounded implementation meaning**, but W5 remains blocked because completeness, external validity, independent verifier/source evidence, production erasure guarantees and differential implementation are not supplied by this research session.

This distinction is now even more important than in v0.6.1. Deletion and recovery are domains in which overclaiming can create real privacy/security harm. A clear theorem saying “an old snapshot must not automatically undo a deletion” is valuable before implementation; claiming that every backup/provider has actually erased the data would be evidence fraud without infrastructure-specific proof.

# 373. New acceptance and differential-conformance obligations

K4/K5 and recovery acceptance gain the following mandatory fixtures:

```text
forged anchor payload with matching superficial mission/environment
anchor state root older than current recovered cut
continuity pin containing dangling hypothesis/plan refs
anchor containing unresolved verification blockers
multiple anchors reordered in serialized storage

mission transition after a verified mission-scoped claim
self-version change with old procedure/effect/continuity packet
handoff budget with catastrophic old failure outside last-N window
handoff containing an advisory next action followed by changed tool boundary

checkpoint before privacy deletion, restore after deletion barrier
checkpoint before access/declassification revoke
source compromise after snapshot
semantic rollback after later governance barrier
raw deletion while derived summary still contains private-only detail
independently supported proposition with tainted derivative requiring clean rederivation
stale lexical/dense/cache surface after canonical deletion
continuity pin/handoff containing deleted-source-derived content
missing barrier ledger during recovery
```

Differential implementations compare not only final content but `RecoveryResumeAssessment`, continuity-cut/root identity, hard handoff role cover, barrier application, derived-taint outcome, purge frontier and erasure-closure status. If one implementation restores the old secret because the checkpoint digest is valid while another blocks it because deletion occurred later, they are not two acceptable policies under the same profile: the specification has an explicit current-governance answer.

These fixtures should be implemented before any claim that K4/K5 continuity/privacy recovery is complete.

# 374. Authoritative ownership fixes introduced by v0.6.2

This revision also repairs a document-level closure error discovered during the audit.

`RetentionEventRevision` appeared in Section 179 as a minimal canonical family but was absent from the authoritative Section 272 Closure Matrix. v0.6.2 adds the row and makes it the canonical event/barrier owner for archive/delete/accessibility transitions. This is not a new feature; it removes an ownership ambiguity.

`Regime/SelfVersionRevision` was also an overly compressed shorthand. v0.6.2 resolves it into:

```text
MemoryRegimeRevision
    world/tool/schema applicability environment

SelfVersionProfileRevision
    consumer/model/tool-runtime capability identity
```

The split prevents a model upgrade from being mistaken for world-state change while still allowing procedures, effect profiles and continuity packets to depend on the current executor.

`MemoryErasureClosureReceipt` is admitted because S29 plus deletion-residue research permit two implementations to disagree on when deletion is “done.” It owns the audit claim that the declared surfaces are closed; it never owns factual truth.

`RecoveryResumeAssessment` is admitted because S25/S26/S30 show that integrity-valid continuity state and `resume_allowed` can otherwise diverge without a single normative owner. It owns resume eligibility for one recovery attempt; it never rewrites the recovered history.

No other new kernel primitive is added.

# 375. Final v0.6.2 statement and theory stop rule

Nolane Memory v0.6.2 defines continuity more strictly than “the agent can restart and remember its work.”

A future self may receive an authenticated record of the past and still be forbidden to use part of it. The memory runtime must distinguish **what the past contained**, **what the current governance state permits to survive**, **what the current environment still makes applicable**, and **what the next consequence boundary actually requires**.

The runtime therefore reconstructs continuity in this order:

```text
authenticate/replay historical memory
-> apply post-snapshot non-revivable barriers
-> validate continuity pin/handoff cut and preservation
-> revalidate mission/self-version/environment dependencies
-> close hard boot/Recall Obligations
-> enforce current information-flow/sink policy
-> only then allow current use/resume
```

Deletion is likewise not a row operation. It is a scoped semantic transition whose completion includes tainted derivatives, read surfaces, continuity artifacts and restore behavior under the host's declared authority. A proposition can remain true while an old summary containing deleted private details becomes unusable. A semantic rollback can restore an earlier preference while an access revocation remains in force. A valid backup can remain a valid historical artifact while being an invalid current restore source until later barriers are applied.

This closes a particularly dangerous form of “memory worship”: treating persisted state as more authoritative merely because it survived a reset.

The stop rule remains strict. Another theory revision is justified only by a new executable counterexample, bounded composition failure, independent-implementation mismatch, migration/restore failure, or external experiment that contradicts a declared capability. The next expected major step is still independent K0–K2/K4 reference implementation and differential conformance, not an ever-larger taxonomy.

> **The goal is not an AI that can always recover its past. The goal is an AI whose memory runtime can tell, after any reset, exactly which parts of the past are authentic, still allowed, still applicable, still reconstructible, and actually required now—and that refuses to revive the rest by accident.**

That is the v0.6.2 continuity/recovery/erasure closure.

---

# PART XXXII — V0.6.3 USE-TIME CONSISTENCY, CAUSAL CUT AND SEMANTIC OPTIMISTIC CONCURRENCY

# 376. Why v0.6.3 exists: a memory can be correct when read and wrong when used

v0.6.2 made recovery current-governance-aware. The next adversarial pass attacked a different interval: **the time between producing a memory-derived judgement and actually using that judgement**.

An agent does not read memory and execute atomically. It retrieves, reconstructs, lets a model reason, perhaps waits for a tool/UI/human step, then promotes a summary, sends an action, renders a response or publishes memory. During that interval another source can be revoked, a counterexample can arrive, a permission can change, a lease can expire, the tool schema can change, or a source can be superseded. A frame can therefore be perfectly justified at T1 and stale at T3.

The naive fix—lock the entire memory store while a model thinks—destroys the architecture's ability to support enormous long-lived memory and concurrent agents. The equally naive fix—compare one global root and invalidate on every write—is safe but creates pathological false invalidation as unrelated history grows.

v0.6.3 introduces **Semantic Optimistic Concurrency Control (Semantic OCC)**. Derived artifacts carry the material semantic dependencies that made their conclusion valid. At promotion/use, those dependencies plus mandatory global governance guards are revalidated. Relevant mutation breaks the lease; proven irrelevant mutation does not.

This revision also closes the read-side twin: a strong result cannot mix a candidate from one snapshot with conflicts/status/source fields fetched from a later “latest” state. Consistency is cut-relative, and shared multi-domain recall uses a causal cut vector rather than pretending one scalar timestamp orders independent domains.

# 377. Source findings S31–S37 expose the read→use seam

The fresh source audit reproduced seven new counterexamples:

| ID | Reproduced behavior | Architectural consequence |
|---|---|---|
| S31 | expiring `EvidenceLease` is accepted with `now=None` but rejected with a supplied post-expiry time | expiry is not an invariant if clock evaluation is optional |
| S32 | a `context-scoped` transfer lesson can route to an unrelated domain/host/model | promotion scope must execute at route/use |
| S33 | same artifact ID is last-write-wins in a derived artifact store | safe only for explicitly replaceable non-authoritative artifact identity |
| S34 | action lifecycle reaches `EXECUTED` with an opaque/nonexistent precondition evidence ref | action-phase correctness is not proof of live memory grounding |
| S35 | action authorization binds no memory-frame dependency or policy/tool generation | ordinary authorization cannot establish memory currentness |
| S36 | consolidation proposal remains promotable after a source is invalidated between propose/promote | proposal eligibility needs commit-time dependency revalidation |
| S37 | strong query can return old `stale=false` row while nested refresh observes newer stale state | staged read needs one cut or explicit whole-result cut upgrade |

Artifact:

```text
revision = NM-v0.6.3-source-use-time-seam-3
digest = c4d44ccacb40e7ec310a364e4a7b5a443e71e4e30385b1df1649befeea377721
```

Some behaviors can be legitimate in isolation. A generic action ledger may intentionally trust external refs; a derived artifact table may intentionally permit replacement. The failure appears when a memory architecture **infers a stronger guarantee than that component owns**.

The response is therefore not seven local patches. It is one cross-cutting contract for read-cut consistency, semantic dependency fencing and use-time validation.

# 378. Compile-time support, current usability and consequence-time grounding are distinct observations

The product-state model already separates truth, access and activation. v0.6.3 adds a time-of-use distinction for derived decisions:

```text
SUPPORTED_AT(K)
    the claim/procedure/frame was justified at read cut K

CURRENTLY_USABLE_AT(mu)
    current policy/lifecycle/applicability permits using it now

GROUNDED_FOR_CONSEQUENCE(C)
    exact consequence C is covered by current memory dependencies,
    current sink/tool policy and final arguments at use linearization
```

A fact can remain true while permission changes. A frame can be sufficient at K and become insufficient because a new hard counterexample arrives. A tool call can be memory-adequate yet unauthorized. Conversely, permission can remain valid while the remembered value is superseded.

This model also rejects TTL as a universal freshness proxy. Most semantic staleness is event/generation based: lifecycle, authority, policy, scope, tool capability, mission/regime, counterexample set, hard-role closure or preservation/recoverability. A five-millisecond frame can be stale after a revocation; an older frame can remain materially compatible if all bounded dependencies are unchanged.

The runtime can expose convenience projections but never collapses these observations into one `fresh=true` flag. That would recreate the one-dimensional status error one level above the memory record.

# 379. Semantic OCC theorem: validate the assumptions that made the conclusion legal

For derived artifact A built at cut K, define a material dependency set D(A,K) containing the semantic properties whose values made A's bounded conclusion valid. At current state mu, validation classifies:

```text
UNCHANGED
COMPATIBLE_REFINEMENT
INVALIDATING_CHANGE
UNKNOWN_OR_MISSING
```

`UNCHANGED` permits the same bounded conclusion. `COMPATIBLE_REFINEMENT` means a declared proof shows the change cannot weaken the conclusion; it creates a refreshed artifact/manifest. `INVALIDATING_CHANGE` makes the artifact stale for the operation. `UNKNOWN_OR_MISSING` fails closed at strong assurance levels.

The critical property is dependency scoping. A new episode in another project is not in D. A source revocation is in D even if bytes are identical. An applicable-counterexample **generation** can represent a whole negative domain without listing every row. A principal-wide emergency revoke can be a mandatory global guard.

This is optimistic concurrency because read/model work proceeds unlocked. It is semantic because conflicts are changes to relevant properties, not arbitrary byte changes. Initial implementations may over-approximate D; later implementations can safely narrow it only with evidence that the omitted mutation classes cannot change the bounded decision.

# 380. The existing dependency manifest becomes the common currentness language

v0.6.3 does not create separate freshness primitives for claims, consolidation, frames and handoff. It deepens `RecallFrameDependencyManifestRevision` into a common schema that derived artifacts can embed/reference.

A dependency entry records:

```text
semantic target / property class
logical + revision identity
semantic generation
authority domain + incarnation + cut component
why the property is material
validation procedure/profile
compatibility/refinement relation
failure consequence if stale
```

Typical properties are source lifecycle, origin set, authority ceiling, applicable-counterexample generation, principal access, declassification, tool schema, hard-obligation closure, preservation/recoverability, mission/self-version, negative-domain frontier and clock epoch.

The manifest also declares dependency completeness. Exact dependencies are enumerated deterministically. Conservative dependencies intentionally include extras. Learned/inferred dependency discovery is marked `BOUNDED` or `UNKNOWN`; it cannot silently call itself complete.

The optimization is asymmetric: false positives cost retries, false negatives permit stale action. Until stronger evidence exists, correctness profiles prefer conservative manifests. This common language lets one validator support promotion, frame reuse, recovery and use fencing without creating several incompatible notions of “fresh.”

# 381. Stale proposal theorem: eligibility is a lease over source state

S36 is a minimal concurrency trace:

```text
T1  S0,S1,S2 live; proposal P is eligible
T2  evidence behind S0 invalidated; S0 becomes stale
T3  promote(P)
```

A conforming implementation cannot use `P.eligible` alone at T3. P carries source revision/lifecycle/authority/origin/applicability dependencies from T1 and promotion revalidates them.

Evidence-row existence is not enough. S0 can remain in historical storage while being unusable as current support. Equal content hashes do not rescue revoked authority.

If change is compatible, a **new proposal revision/dependency digest** is produced and affected obligations are rechecked. The old certificate remains evidence of T1 reasoning. If remaining sources no longer meet support requirements, the abstraction stays candidate/stale. If a new independent source replaces the old one, that is new evidence and a new proposal.

This allows slow model-based consolidation without locking memory while preventing attractive stale model output from becoming canonical after its evidence changed.

# 382. Causal Recall Cut theorem for multiple authority domains

A scalar sequence is meaningful inside one correctness authority domain. It is not a universal present across independent domains.

Define:

```text
K[domain] = (incarnation, sequence, root)
```

and causal publication/import edges such as:

```text
(A,118) -> (B,87)
```

A strong cut K is causally closed when including each destination event also includes every source event that event semantically depends on. K containing B@87 but only A@117 is torn.

The runtime can monotonically close a seed vector over causal predecessors. This creates no total order between unrelated A and C events and requires no synchronized wall clock. Every domain/index must then serve its component or provide a complete canonical delta. Missing coverage yields `CUT_PARTIAL/CUT_UNAVAILABLE`.

Strong absence is also vector-scoped. “No blocker exists” is complete only for domains/surfaces covered at K. Eventual sharing can still expose positive advisory memories; it cannot prove a lagging domain contains no contradiction.

This is the read-side complement of the publication saga: separate authorities stay separate while bounded recall gets one coherent causal slice.

# 383. Cut-consistent staged recall forbids hidden latest reads

Strong recall performs multiple reads: candidate search, conflict lookup, source hydration, page fault, counterexample lookup, policy checks and rendering. Independent `latest` calls can compose a state that never existed.

S37 shows the minimal case: outer query copies an old candidate, nested conflict lookup refreshes state after concurrent invalidation, while returned candidate retains its old lifecycle field.

A conforming strong pipeline uses one of:

1. a snapshot/transaction capable of serving K;
2. revision-addressed reads plus verified index/frontier overlays at K;
3. an explicit cut upgrade to K' followed by recomputation/revalidation of materially affected fields.

The forbidden strategy is “keep old candidate and attach whichever newer fields are convenient.” Weaker UI previews can declare weaker consistency, but cannot be promoted to a strong Recall Frame.

Page faults obey the same rule. A source resolver that only has current state cannot satisfy historical K with latest bytes; it requests a cut upgrade or returns historical capability unavailable.

# 384. `MemoryUseFence` is the one new projection primitive admitted by v0.6.3

S34–S36 permit two systems to agree on Recall Frame contents yet disagree on whether the frame may still ground a concrete consequence after concurrent change. This behavioral distinction justifies one primitive.

Reference fields:

```text
fence_id / nonce
RecallFrame + dependency-manifest refs
validated Recall Cut / dependency digest
principal identity
sink / tool / consequence class
canonical final payload or action-argument digest
access/declassification/policy generation
tool/schema/capability generation
hard-obligation closure generation
optional expires_at + trusted clock authority/epoch
single-use / consumption state
validation-procedure revision
```

The fence owns no truth and no action permission. It is an ephemeral/auditable proof that one exact memory-grounded consequence was revalidated against the current assumptions required by its profile.

It is usually issued late, after final arguments exist. Validation/consumption occurs immediately at the host consequence boundary. Changed dependencies, args, principal/sink, expiry or replay block use.

Low-risk hosts may implement equivalent atomic validation without materializing a durable token. The primitive defines observable semantics, not a mandatory cryptographic format.

# 385. The memory-use linearization point says when concurrent history becomes later

“Revalidate immediately before action” is otherwise vague. v0.6.3 defines the memory-use linearization point as the atomic boundary where the dispatcher validates and consumes the grounding fence/expected semantic generations for the exact consequence it is about to release.

```text
T0  frame compiled at K
T1  model reasoning
T2  final consequence proposed
T3  dependency + policy + sink revalidation
T4  MemoryUseFence issued/refreshed
T5  ordinary host action authorization
T6  atomic validate+consume fence   <-- memory-use linearization
T7  external dispatch
```

A relevant mutation committed before T6 invalidates the fence. A mutation after T6 is later canonical history and does not retroactively mean the dispatch was never grounded.

Memory cannot generally make T6 and a remote service effect one transaction. External systems can change between T6 and T7. High-risk protocols can add conditional server writes, idempotency or quiescence; those are action-system semantics.

The memory guarantee is narrower and testable: **memory assumptions released to the consequence boundary were current at one defined point**, not checked at an unbounded earlier time.

# 386. Final argument and payload binding closes check-one/execute-another

A frame can be sufficient for “send the report,” while the eventual call adds a recipient, path or destination not known when the frame was compiled. A renderer can likewise append private provenance after a structured payload passed its flow check.

The use fence and flow receipt therefore bind a canonical semantic/serialization digest of the **actual payload crossing the sink**. For tools this includes tool identity/version and arguments after default resolution/canonicalization. For model/user output, policy can bind exact rendered bytes or a deterministic render profile.

Material post-check changes invalidate the binding:

```text
recipient a -> b
amount 10 -> 100
local path -> network URL
safe fields -> renderer appends private source
tool-v1 -> tool-v2 with changed parameter semantics
```

Not every whitespace change needs to invalidate a semantic fence; normalization/equivalence is profile-defined and tested. The executor cannot invent equivalence ad hoc.

The principle matches origin-bound evidence: prove the exact object being relied on, not a nearby earlier object.

# 387. Memory grounding and ordinary action authorization remain orthogonal

S34/S35 show that an action lifecycle can be locally correct while memory grounding is stale. The combined dispatch condition is:

```text
CurrentMemoryGrounding(C)
AND CurrentSinkInformationFlow(C)
AND CurrentHostActionAuthorization(C)
AND action-protocol preconditions
```

No operand subsumes another.

A valid use fence does not grant network/filesystem/payment capability. An action grant does not prove the remembered recipient or destructive-prevention rule remains current. An information-flow ALLOW does not prove memory adequacy.

Implementations may physically fuse these checks in one policy decision point, but audit outcomes remain separable: `MEMORY_DEPENDENCY_STALE`, `SINK_DISCLOSURE_DENIED`, `ACTION_UNAUTHORIZED`, `TOOL_PROFILE_STALE`, and so on.

This separation also makes retry safe. A stale frame triggers memory refresh; authorization denial does not manufacture new evidence; tool-profile drift may require both memory re-grounding and action re-authorization.

# 388. Trusted-time theorem: protected expiration cannot depend on an optional caller clock

S31 reveals the deeper category: a record can carry `expires_at` while expiry disappears when a caller omits `now`. For a protected same-process lease:

```text
issued_at  from trusted monotonic clock C
expires_at in C's domain
clock_epoch identifies boot/authority epoch

valid iff:
    trusted clock available
    current epoch == issued epoch
    issued_at <= now < expires_at
    non-time dependencies remain valid
```

If the operation cannot evaluate the required clock/epoch, it returns `CLOCK_AUTHORITY_REQUIRED`; absence of time input is not equivalent to “no expiry.”

Raw monotonic timestamps are not portable across process/host restart. A new process may restart the monotonic origin while old serialized numbers remain. Cross-host/persisted expiry therefore needs one declared alternative: a trusted wall/time authority with explicit uncertainty/skew, a signed authority-issued validity interval, or a logical/generation validity rule. A host that cannot satisfy the declared time profile downgrades the lease to unusable/unknown instead of reinterpreting the old number.

Clock **epoch** also matters during failover. Even two monotonic sources that both report `50.0` are not interchangeable if their zero points differ. The issuing clock identity/epoch is a material dependency of the lease. Clock-authority migration is a typed compatibility transition, not a string rename.

Fact valid time is a different product-state dimension. A currently true fact can have an expired permission-to-use lease; a live lease cannot resurrect an obsolete fact. Likewise a temporal fact correction does not itself extend an authorization deadline.

Conformance tests include equality at the exact deadline, missing clock, wrong epoch, restart with reused numeric timestamp, backward wall-clock adjustment under bounded-skew profiles, and a non-expiring lease. The reference convention for protected deadlines is half-open `[issued_at, expires_at)`, so `now == expires_at` is expired everywhere.

# 389. Operational Semantic Field Law turns metadata promises into contracts

A safety-looking field is not a safety property merely because it is serialized. The **Operational Semantic Field Law** requires every field used in a correctness claim to have an executable ownership record.

For each normative field the implementation must be able to answer:

```text
semantic owner
writer / transition that changes it
mandatory readers/evaluation boundaries
input authority needed to evaluate it
freshness revision/generation/cut
UNKNOWN/failure behavior
whether result is cached and how cache invalidates
conformance fixture proving the path is exercised
```

`expires_at` without mandatory time validation is advisory. `context-scoped` without context filtering is advisory. `invalidates_on` without event evaluation is advisory. `hard=true` without hard-cover preservation is advisory. `declassified` without a live policy/receipt generation is advisory. The same applies to `trusted`, `canonical`, `recoverable`, `current`, or any future field name whose surface wording sounds stronger than its runtime path.

The registry is not another truth store. It is a **schema-to-enforcement map** owned by the specification/implementation conformance layer. The authoritative value still lives in the primitive named by the Closure Matrix; the registry says where that value is obligatorily consumed.

This matters during migration. A legacy record can contain an `expires_at` field while the old runtime never enforced it. Migration must not upgrade that historical record to “was expiry-protected.” It can preserve the raw field as legacy metadata and require revalidation before current protected use.

Benchmark claims follow the same rule. “Supports scope-aware memory” requires a test in which foreign-scope memory would otherwise influence retrieval/use and is actually blocked. A schema screenshot or unit test of serialization is not evidence of enforcement.

This discipline prevents a giant spec from becoming checkbox inflation: rich metadata is useful, but only fields with owner, mandatory evaluator, currentness rule and failing counterexample participate in the trust theorem.

# 390. Applicability is re-evaluated where influence occurs

A procedure or lesson can be legitimately promoted as `context-scoped` and still be harmful if routing ignores the scope. S32 demonstrates that gap. Applicability is therefore evaluated where **influence actually occurs**, not frozen at creation/promotion.

A requested compatibility profile can include:

```text
authority domain / project
host/runtime
model/self-version
tool/profile
mission/task/episode
regime/environment
principal/use capability
input/output modality when material
```

A bound value must match or pass an explicit compatibility/refinement relation. `*` is an explicit wildcard. An omitted dimension is not automatically global. If a memory's profile does not mention a dimension that the consumer declares safety-critical, compatibility becomes `UNKNOWN` until policy supplies a default/proof.

This supports controlled generalization. A lesson learned on Linux/h1/model-A can initially remain narrow. Independent outcomes may later justify a broader scope revision such as “Linux/*/model-family-X.” The broader revision is a new claim about applicability with its own evidence, not a side effect of accumulating tags.

Effect/interference evidence follows the same algebra. “M hurt model A on task T” is not a global ban. A Linux success is not Windows support because tags were unioned. A procedure can be factually valid yet executor-incompatible because the new model/tool cannot perform its assumptions.

Routing implementations may pre-index profile dimensions for speed, but the final use fence still binds the actual requested profile generation. A stale route cache cannot survive a mission/model/tool change merely because the memory content did not change.

Conformance includes exact match, explicit wildcard, compatible model-family refinement, missing safety-critical dimension, conflicting regime, and a foreign context with high lexical/vector similarity. Relevance never overrides applicability.

# 391. Negative memory results have currentness dependencies too

A positive memory carries source dependencies. A negative result such as:

```text
NO_MATCH_COMPLETE_DOMAIN
no active blocker
no applicable counterexample
no newer preference
no revoked source in this dependency slice
```

is also a derived memory judgement whose truth can be invalidated by later writes.

`NegativeRecallDependencyRevision` binds:

```text
normalized predicate/query family
bounded query-domain identity
Recall Cut/vector
relevant domain/index frontier
absence-sensitive semantic generation(s)
query procedure + pagination/completeness capability
principal/access/applicability profile
```

A matching write after the cut invalidates the absence before current use. A write provably outside the predicate/domain need not. This is the **phantom** counterpart of source-revision validation: a frame can become stale because something new appeared, even though none of the rows it originally read changed.

This matters because absence often authorizes consequences. “There is no blocker,” “no newer correction,” or “no catastrophic counterexample” can be more dangerous than stale positive memory. A short TTL cannot make the absence safe; the matching write can arrive one microsecond later. Generation/frontier invalidation supplies correctness, while TTL remains an operational upper bound.

Implementations can maintain predicate-specific generations, coarse domain generations, exact ordered indexes, or query-domain watch sets. Coarser generations cause more false invalidation but are safe. A highly precise watch scheme must prove it cannot miss a matching insertion.

If a hard Recall role is discharged by complete absence—for example “no active revoke exists”—the negative dependency becomes part of D and therefore part of use-time validation. `NO_MATCH` without a completeness-capable query domain remains advisory and cannot close a hard role.

Differential fixtures include insert-after-NO_MATCH, revoke becoming active, insertion outside domain, access scope change revealing a previously hidden match, and lagging index with incomplete canonical delta.

# 392. Relevant and irrelevant changes require an explicit compatibility surface

Semantic OCC is useful only if the runtime can distinguish “memory changed” from “the conclusion's assumptions changed.” The classification surface is explicit and property-specific.

Examples:

- source lifecycle `ACTIVE -> REVOKED`: `INVALIDATING_CHANGE`;
- additional independent support under identical scope/authority: usually `COMPATIBLE_REFINEMENT`;
- unrelated episode in another semantic region/domain: `IRRELEVANT`;
- tool-schema revision changing meaning/default of a bound argument: `INVALIDATING_CHANGE`;
- tool patch changing an unused description field: compatible only with a declared validator;
- new counterexample outside the obligation's applicability region: irrelevant;
- access generation changes while equivalent capability is re-issued: compatible only if policy supplies an equivalence proof;
- representation is recompressed but preserves every required dimension under a new verified envelope: potentially compatible refinement.

There is no universal compatibility table because different properties have different semantics. A `SemanticDependencyValidatorProfile` (profile, not truth primitive) owns the comparison procedure for each dependency class. It binds its own revision, so changing the compatibility rule invalidates certificates that depended on the old rule where material.

Failure precedence is conservative. `INVALIDATING_CHANGE` dominates compatible changes. `UNKNOWN` dominates any assumption of compatibility at a strong boundary. An unrelated change cannot “cancel out” an invalidating change. Multiple refinements can be rebased only after every material dependency has a valid comparison result.

The runtime never infers compatibility from equal-looking prose. Equal payload bytes can coexist with revoked authority. Different payload bytes can be semantically equivalent under a verified normalization. Compatibility is a claim with a procedure/evidence basis.

This creates a safe optimization ladder: early implementations may invalidate on every generation change in D. Later ones add precise validators and demonstrate fewer retries through conformance and benchmark evidence. Performance improves without moving the correctness boundary.

# 393. Publication cycles preserve origins but expand causal dependency closure

Shared memory can form cycles:

```text
A publishes to B
B derives/republishes to C
C republishes to A
```

Two invariants must survive the cycle.

First, evidence independence follows **root origins**, not path count. Origin resolution traverses publication/derivation edges with visited logical/revision identities and returns a set of parentless/admitted roots. Encountering the same root through another path changes availability/provenance topology, not support cardinality. A cycle with no independently grounded incoming root remains ungrounded no matter how many times the assertion is echoed.

Second, causal-cut closure follows concrete publication/admission events. If an A recall includes the later C→A import, its cut vector must include the B/C/A predecessor revisions that causally produced that import. Closure can expand over several domains while leaving unrelated events unordered. If an edge refers to an unavailable domain or incarnation, the cut becomes partial/opaque rather than silently severing provenance.

A publication cycle therefore creates neither paradoxical time nor extra evidence. It creates a more connected dependency graph and may increase the cost of a strong multi-domain read. A weaker advisory profile can stop early and expose which frontiers are missing; a strong profile must close the required causal predecessors.

Revocation also follows roots/causal lineage. If the original root is compromised, downstream republishes do not remain independently healthy merely because they have local destination IDs. Independent new observations can preserve a claim through alternative justification; echoes cannot.

Conformance worlds include pure cycles without roots, one-root cycles, two-independent-root merges, destination revocation, and a cut that includes a downstream import while deliberately omitting one predecessor domain.

# 394. Information-flow receipts are use-time leases too

v0.6.1 made `FrameInformationFlowReceipt` bind the composed payload and sink. v0.6.3 adds a second dimension: **an ALLOW decision is a use-time lease over policy state**, not an eternal property of the bytes.

An ALLOW can depend on:

```text
principal/access generation
source confidentiality labels
declassification receipt revision
destination/tool identity and capability generation
purpose/mission/scope
exact rendered/serialized payload digest
policy procedure revision
```

The `MemoryUseFence` references the exact flow receipt and its material generations, or requests a fresh flow evaluation for the final payload. Revoking declassification, changing destination, narrowing export permission, changing tool identity, or mutating the payload invalidates the earlier ALLOW.

If policy offers a short-lived disclosure grant, its expiry follows the trusted-time theorem. The factual truth of the memory has no bearing on whether disclosure permission remains live.

This closes a compositional TOCTOU:

```text
T0 retrieve under allowed access
T1 compose payload and receive ALLOW
T2 access/declassification revoked
T3 attempt send/export
```

A revoke committed before use-fence consumption wins. A revoke committed after the linearization point is later history. If the policy source is temporarily unavailable at T3, a high-assurance sink cannot reuse T1 merely because the payload is unchanged; it returns `FLOW_POLICY_CURRENTNESS_UNKNOWN` or a stricter configured outcome.

Caching remains legal. The cache entry carries the exact policy/declassification/sink generations and payload digest. That makes information-flow performance optimizable without creating a second disclosure clock.

# 395. Resource pressure cannot make dependency validation optional

Semantic OCC adds correctness work immediately before a consequence: read dependency generations, perhaps refresh policy/tool profile, verify final payload/arguments and consume a fence. Under overload there will be pressure to skip these checks.

For any assurance profile that requires use-time grounding, this validation is **correctness-reserved work**. Optional associative exploration, speculative prospection, prefetch, broad candidate reranking and background consolidation are shed first. If current dependency state cannot be read, the result is `USE_VALIDATION_UNAVAILABLE`, `CUT_UNAVAILABLE`, `CLOCK_AUTHORITY_REQUIRED`, or another typed failure—not “the frame was compiled recently, so continue.”

Dependency scoping is the scalability mechanism. The runtime validates compact property generations/roots, not every memory object. Implementations may batch generation reads, use local coherent caches, or co-locate high-frequency policy generations with the dispatcher. Those optimizations need a frontier/fencing contract proving the read is current enough for the use linearization point.

If D itself becomes enormous, this signals either genuinely large decision dependency width or an over-conservative extractor. The host can stage the action, compile sub-decisions under a shared cut, pin repeatedly used hard witnesses, or improve dependency compression with a proof-preserving aggregate generation. It cannot silently truncate D while preserving the same assurance label.

Repeated invalidation can cause **use-time thrashing** even when context is small: compile, concurrent mutation, fail fence, recompile, repeat. The runtime may apply bounded retries, backoff, quiescence for selected high-risk domains, or ask the host to serialize the specific hot dependency. It does not escalate automatically to a global memory lock.

Performance benchmarks therefore report retry/false-invalidation rate and validation cost alongside correctness. A fast implementation that skips use-time checks is not an optimization of the same profile; it is a weaker profile.

# 396. V0.6.3 Use-Time / Causal-Cut Calculus

The new laws are encoded in an independent deterministic model-free harness:

```text
revision = NM-v0.6.3-use-time-causal-cut-calculus-1
property families = 34 / 34 passed
bounded/fuzz cases = 131,701
semantic failures = 0
digest = 6380d200cccddfdaaff72a3b83ecee7f82a0879095b05062d1c1813a25e3d3e5
```

The 34 families cover proposal dependency fencing, irrelevant-write tolerance, lifecycle generation separate from content bytes, final argument binding, policy/tool generation drift, trusted half-open lease expiry and clock epoch, single-use replay, principal/sink/frame binding, causal vector cuts, per-domain frontiers, index+delta strong reads, cut-consistent staged references, operational metadata ownership, applicability routing, negative-cache generations, missing-dependency fail-closed behavior, explicit rebase identity, publication-origin idempotence, action-authorization separation, payload binding and hard-role closure generation.

Four large randomized families contribute 120,000 cases: 40k use-time TOCTOU fence worlds, 30k proposal Semantic-OCC worlds, 30k multi-domain causal-cut worlds and 20k applicability-scope worlds. The remaining cases exhaust or enumerate small boundary spaces such as clock equality, principal/sink mismatch, policy/tool generations and cut closure.

The harness deliberately tests both directions: **relevant mutation must invalidate** and **irrelevant mutation must not**. A design that fails everything on every global write can be safe but does not satisfy the scalability hypothesis being evaluated.

The artifact is not production proof. It does not prove dependency extraction completeness, secure time deployment, distributed frontier availability, real-model action argument canonicalization, or acceptable latency. It demonstrates that the declared reference semantics are mutually consistent over the modeled worlds and supplies executable regressions for future kernels.

Any implementation claim stronger than that needs differential, fault-injection and real-agent evidence.

# 397. Fresh widened Nolane World regression: 319 green tests coexist with S31–S37

The final regression selects **76 packaged test files** covering memory/truth/recovery/checkpoint/handoff/anchor/mission/replay/epistemic/counterexample/research/security/scope/access/capability/journal/experience/lease/transfer/action-lifecycle/temporal/persistence/fencing/store surfaces.

```text
319 passed
0 failed
2 warnings
4.44 seconds
attestation digest = 75da6a7eeb8bf6957cefe4b14ffe19734576002904ad485ba182521658c1bae7
```

The two warnings are Python multiprocessing/fork deprecation warnings from meta-policy concurrency tests, not memory-semantic failures. The attestation records the exact 76 filenames, their ordered selection digest, command semantics, raw-log SHA-256 and exit code so the number cannot be detached from the executed corpus.

This result intentionally coexists with S31–S37. Packaged tests establish that existing tested mechanisms remain executable. The adversarial probes create interleavings and cross-component assumptions that the packaged suite does not currently encode. A green suite therefore does not waive a reproduced semantic counterexample.

Future unified-kernel regressions include:

```text
REG-LEASE-EXPIRY-CLOCK-REQUIRED
REG-CONTEXT-SCOPE-ROUTE-ENFORCED
REG-PROPOSAL-PROMOTION-STALE-SOURCE
REG-STRONG-QUERY-NO-TORN-REFRESH
REG-ACTION-MEMORY-GROUNDING-USE-TIME
```

Each regression stores the smallest interleaving, violated invariant and expected fail-visible outcome. Replacing the legacy class is not grounds to delete the test; the semantic law survives code organization.

Concurrency regressions must control interleaving rather than rely on sleep timing. S36 is modeled as explicit T1/T2/T3 state transitions. S37 forces a refresh between outer and nested reads. Future implementations should use barriers/hooks/model-checking schedules where possible so a rare race cannot escape merely because CI did not reproduce the timing that day.

# 398. Current research pressure supports the seam, not proof of Nolane

The v0.6.3 evidence register adds current work focused on this boundary.

**Capability Gates Are Not Authorization** pressures the distinction between exposing a tool and authorizing a concrete model-emitted call/value, supporting final-call binding rather than proving Nolane's fence.  
`https://arxiv.org/abs/2606.28679`

**STALE** and **When Memory Updates but Behavior Does Not** show complementary failures where updated information exists yet stale premises continue to govern downstream reasoning/output.  
`https://arxiv.org/abs/2605.06527`  
`https://arxiv.org/abs/2608.01619`

**When Memory Becomes Authority** pressures the consolidation boundary: derived content can retain semantics while source-authority limits disappear.  
`https://arxiv.org/abs/2608.01679`

**Supersede** treats correct current-value use after memory update as a distinct capability.  
`https://arxiv.org/abs/2606.27472`

**Governing Dynamic Capabilities** pressures binding consequential use to the tool/capability configuration actually authorized.  
`https://arxiv.org/abs/2603.14332`

**Governed Shared Memory** reports live multi-agent scope/pipeline ordering failures, supporting explicit scope/frontier semantics.  
`https://arxiv.org/abs/2606.24535`

Every allowed inference and anti-overclaim boundary is machine-recorded. These papers do not certify Nolane Memory.

# 399. W5 use-time / causal-cut campaign remains blocked

A depth-5 W5 session asks for the smallest semantics that keep frames, proposals and memory-grounded consequences sound from read/compile to promotion/use under concurrent change.

```text
depth = 5
required gates = 16
open epistemic debts = 9
closure = BLOCKED
blockers = 25
digest = 62fbbc243a24f63c894adcd86f93935e105bd352f96b8d851090c10225de69b5
```

Open debts:

| Debt | Severity | Meaning | W5 state |
|---|---:|---|---|
| `use-time-revalidation-completeness` | 0.995 | which dependency classes must be checked immediately before memory-grounded consequence | `open` |
| `proposal-dependency-fence` | 0.990 | derived proposals/certificates need revision-pinned dependencies and stale/rebase semantics at commit | `open` |
| `cut-consistent-staged-recall` | 0.990 | nested retrieval/conflict/page-fault reads cannot silently mix states from multiple cuts | `open` |
| `operational-metadata-enforcement` | 0.980 | correctness-bearing scope/expiry/invalidation/hardness fields need mandatory evaluation ownership | `open` |
| `action-argument-memory-binding` | 0.970 | memory adequacy and flow proof must bind final concrete action/tool arguments and be one-use or revalidated | `open` |
| `causal-cut-vector-closure` | 0.970 | strong multi-domain recall needs a causally closed frontier/cut rule without global consensus | `open` |
| `temporal-authority-clock-semantics` | 0.960 | expiry/TTL needs trusted clock identity, boundary convention and failure behavior when clock unavailable | `open` |
| `applicability-routing-enforcement` | 0.940 | context/task/model-scoped learned memory must be filtered by actual requested profile at use | `open` |
| `dependency-fence-minimality` | 0.880 | avoid global invalidation while proving unrelated writes cannot affect the bounded obligation | `open` |

The spec now gives each debt a bounded semantic home: dependency manifests, use-time validation, trusted clocks, causal vector cuts, operational metadata ownership and applicability routing. W5 remains blocked because dependency-extraction completeness, distributed performance, external validity and independent implementation evidence cannot be created by prose.

This is the intended confidence posture: an implementer should not invent what happens when source revocation races promotion, while the document still refuses to claim every real dependency will be discovered.

# 400. Closure Matrix changes: one new projection primitive, sharper existing owners

v0.6.3 deliberately avoids primitive inflation even though the audit found seven new source counterexamples.

`RecallCutRevision` is deepened from one canonical cut into a single-domain or causally closed multi-domain vector cut. No parallel distributed-memory cut object is introduced.

`RecallFrameDependencyManifestRevision` becomes the shared language for material semantic dependencies and currentness validation. Consolidation proposals, frame leases, recovery assessments and other derived certificates may embed/reference this schema without becoming new authority stores.

`NegativeRecallDependencyRevision` gains predicate/domain/vector/frontier generation semantics for absence currentness. `FrameInformationFlowReceipt` remains the sink-authorization receipt but is explicitly a current-use dependency. Consolidation proposal eligibility remains a derived state whose promotion authority is bounded by its dependency manifest.

Only **one** new projection primitive is admitted: `MemoryUseFence`. It owns the bounded claim that the exact consequence/payload was revalidated against the current memory dependencies, principal, sink, policy/tool generations and final argument digest and can be consumed according to the fence profile. It owns neither factual truth nor external action authorization.

This ownership decision matters for migration. A legacy action record with `authorization_ref` does not become a `MemoryUseFence`; it lacks the necessary dependency and argument binding. A legacy frame can be imported as historical/compile-time evidence but must be revalidated before it receives a current use fence.

The Closure Matrix must therefore show one writer/validator for fence state and no second “memory current enough to act” Boolean in action lifecycle, tool adapter or frame cache. If an implementation chooses not to materialize a fence object, it still must expose observationally equivalent validate/consume semantics at the consequence boundary.

Seven counterexamples producing one primitive and sharper existing transitions is the intended shape of vertical growth.

# 401. Differential-conformance fixtures must race the implementation, not only inspect final state

The future two-kernel corpus must race the implementation, not only inspect final snapshots. It gains at least these schedules:

```text
eligible proposal -> revoke source -> promote
strong outer query -> concurrent stale -> nested conflict/source lookup
frame compile -> access revoke -> same consequence
frame compile -> unrelated-region write -> same consequence
frame compile -> final recipient/amount/path mutation -> dispatch
use fence issue -> tool-schema generation change -> consume
protected lease -> no trusted clock / wrong clock epoch
context-scoped memory -> foreign profile route/use
destination import visible -> source-domain cut deliberately lagging
negative complete-domain result -> matching write -> cached absence use
```

Each fixture declares the semantic comparison mode and expected normalized result before execution. Relevant-mutation schedules should converge on `PROPOSAL_STALE`, `MEMORY_DEPENDENCY_STALE`, `CLOCK_AUTHORITY_REQUIRED`, `ACTION_ARGUMENT_MISMATCH`, `CUT_UNAVAILABLE`, `SCOPE_INCOMPATIBLE`, or another specified typed outcome. The unrelated-write fixture must remain valid, otherwise the implementation is conservatively correct but fails the dependency-minimality/scalability profile.

The corpus also checks retry behavior. After `PROPOSAL_STALE`, a fresh proposal built from current sources can succeed; the old proposal cannot be mutated in place. After a cut upgrade, all materially dependent output fields are recomputed. After a fence mismatch, ordinary action authorization is not consumed as though the action had executed.

Implementations can use MVCC, immutable logs, transactional databases, generation tables or in-memory snapshots. They are not required to share lock strategy. They must agree on **which interleaving changes semantic legality and where the use linearization point occurs**.

A disagreement is high-value research evidence: either one kernel is nonconforming or the spec still lacks a discriminating rule. That mismatch—not stylistic implementation difference—earns the next theory revision.

# 402. Final v0.6.3 statement and stop rule

Nolane Memory v0.6.3 extends the central continuity theorem into time-of-use:

> **It is not enough for memory to have been correct when retrieved. A long-lived agent needs a runtime that can prove the assumptions behind a memory-derived conclusion remained materially valid until the exact boundary where that conclusion is promoted, disclosed or acted upon.**

The runtime observes memory under an authenticated cut, compiles a bounded dependency manifest, lets reasoning proceed without a global lock, and revalidates only semantic properties capable of changing the bounded conclusion. Strong multi-domain reads use causal vector cuts. Protected expiry has a real clock owner. Applicability labels execute at route/use. Proposals are rechecked at promotion. Final tool/payload arguments are bound. A one-use `MemoryUseFence` can bridge the last TOCTOU gap without becoming an action credential.

This remains memory, not an external transaction engine, global consensus system or generic authorization service. It defines **memory currentness at the boundary where memory stops being passive history and begins influencing a consequence**.

The theory stop rule tightens again: another revision requires an executable counterexample that survives Semantic OCC/use fencing/cut closure, an independent-kernel mismatch, or a real experiment demonstrating a declared dependency/consistency guarantee is materially insufficient. “More memory features” remain inadmissible.


## Appendix S — Claim-Scoped Prior-Art and Internal Evidence Register

The machine-readable source register is `NOLANE-MEMORY-V0.6.3-CLAIM-SCOPED-EVIDENCE-REGISTER.json`. This rendered view is for audit/readability; source class and inference boundaries are normative from the JSON companion.

| ID | Class | Source | Allowed inference | Not established | Informs |
|---|---|---|---|---|---|
| `EA-01` | `ACL_MAIN_PEER_REVIEWED` | HeLa-Mem: Hebbian Learning and Associative Memory for LLM Agents — https://aclanthology.org/2026.acl-long.625/ | Associative graph structure, consolidation and spreading activation are credible retrieval mechanisms worth testing against flat similarity. | Does not establish that activation should own truth, authority, scope, or Nolane's preservation semantics. | association, region discovery |
| `EA-02` | `ACL_FINDINGS_PEER_REVIEWED` | Synapse: Empowering LLM Agents with Episodic-Semantic Memory via Spreading Activation — https://aclanthology.org/2026.findings-acl.1108/ | Spreading activation with inhibition/decay is a contemporary mechanism for associative episodic-semantic recall. | Does not prove associative activation is complete, safe under principal scope, or epistemically authoritative. | association, interference |
| `EA-03` | `ACL_MAIN_PEER_REVIEWED` | MAGMA: A Multi-Graph based Agentic Memory Architecture for AI Agents — https://aclanthology.org/2026.acl-long.1709/ | Semantic, temporal, causal and entity relations can provide complementary retrieval views. | Does not establish that four graphs are the canonical memory ontology or that learned traversal may omit hard Nolane roles. | multi-view discovery |
| `EA-04` | `ARXIV_PREPRINT` | MESA: Task-Adaptive Multi-Structure Evidence Selection for Long-Horizon Agent Memory — https://arxiv.org/abs/2608.10108 | Query/task-adaptive composition of multiple memory structures is an important efficiency/quality pressure. | Preprint results do not prove a learned selector is sound for hard correctness obligations or optimal across domains. | multi-view selection, context efficiency |
| `EA-05` | `ACL_FINDINGS_PEER_REVIEWED` | Memory Matters More: Event-Centric Memory as a Logic Map for Agent Searching and Reasoning — https://aclanthology.org/2026.findings-acl.1123/ | Event-centric logical relations can support structured long-horizon navigation beyond flat similarity. | Does not prove the event graph should be canonical authority or cover all memory relations. | event structure, region discovery |
| `EA-06` | `ACL_MAIN_PEER_REVIEWED` | Structured Episodic Event Memory — https://aclanthology.org/2026.acl-long.277/ | Structured episodes plus provenance expansion support coherent reconstruction from fragmented evidence. | Does not validate Nolane's historical-judgement, preservation-envelope or sufficiency contracts. | reconstruction, provenance |
| `EA-07` | `ACL_FINDINGS_PEER_REVIEWED` | Beyond Dialogue Time: Temporal Semantic Memory for Personalized LLM Agents — https://aclanthology.org/2026.findings-acl.1496/ | Occurrence-time semantics and durative memory address real temporal inaccuracy/fragmentation problems. | Does not establish exact interval coverage from sparse observations or Nolane's knowledge-time semantics. | temporal memory, durative state |
| `EA-08` | `ACL_FINDINGS_PEER_REVIEWED` | TiMem: Temporal-Hierarchical Memory Consolidation for Long-Horizon Conversational Agents — https://aclanthology.org/2026.findings-acl.1091/ | Hierarchical temporal consolidation is a serious contemporary strategy for long-horizon memory. | Does not make hierarchy itself authoritative or prove that abstraction preserves every query family. | temporal hierarchy, consolidation |
| `EA-09` | `ACL_MAIN_PEER_REVIEWED` | APEX-MEM: Agentic Semi-Structured Memory with Temporal Reasoning for Long-Term Conversational AI — https://aclanthology.org/2026.acl-long.749/ | Append-only temporal history and retrieval-time resolution are credible designs for evolving conversational facts. | Does not prove append-only storage alone solves concurrent write, authority, or preservation semantics. | temporal evolution, query-time conflict resolution |
| `EA-10` | `ARXIV_PREPRINT` | Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents — https://arxiv.org/abs/2606.06036 | Active iterative memory reconstruction is a credible alternative to static retrieve-then-reason. | Does not prove generated bridges are factual, exhaustive, or safe for high-assurance obligations. | active reconstruction |
| `EA-11` | `ARXIV_PREPRINT` | Beyond Semantic Organization: Memory as Execution State Management for Long-Horizon Agents — https://arxiv.org/abs/2606.06090 | Execution-state trajectories and revise/recovery structure are important for long-horizon agent memory. | Does not imply the memory layer should own planning/action authority or that its state tree is universally optimal. | execution state, recovery |
| `EA-12` | `ACL_FINDINGS_PEER_REVIEWED` | RecMem: Recurrence-based Memory Consolidation for Efficient and Effective Long-Running LLM Agents — https://aclanthology.org/2026.findings-acl.1619/ | Selective/recurrence-triggered consolidation can reduce eager-consolidation cost and motivates fast/slow memory formation. | Does not justify suppressing one-shot critical-event consolidation or make recurrence evidence of truth. | consolidation scheduling |
| `EA-13` | `ARXIV_PREPRINT` | LycheeMemory V2: Efficient Long-Term Memory for LLM Agents via Semantic Segment-Level Consolidation — https://arxiv.org/abs/2608.12990 | Consolidation granularity materially affects memory construction cost and retained evidence in the authors' experiments. | Does not prove semantic segmentation is decision-equivalent for all future queries. | consolidation granularity, preservation |
| `EA-14` | `ARXIV_PREPRINT` | WiCER: Wiki-memory Compile, Evaluate, Refine Iterative Knowledge Compilation for LLM Wiki Systems — https://arxiv.org/abs/2605.07068 | Blind compression/compilation can lose critical facts; diagnostic probes and targeted refinement are a credible correction loop. | Does not establish universal future-query preservation or that its reported benchmark gains transfer to agent memory. | counterexample-guided refinement, preservation |
| `EA-15` | `ARXIV_PREPRINT` | TRUSTMEM: Learning Trustworthy Memory Consolidation for LLM Agents with Long-Term Memory — https://arxiv.org/abs/2606.25161 | Memory updates have distinct omission, corruption and unsupported-addition failures; coverage/preservation/faithfulness are useful transition-verification axes. | Does not prove its verifier is complete, independent in every domain, or that Nolane's transition verifier should use the same training method. | transition verification |
| `EA-16` | `ACL_FINDINGS_PEER_REVIEWED` | Memp: Exploring Agent Procedural Memory — https://aclanthology.org/2026.findings-acl.866/ | Learnable/updateable procedural memory and migration of procedures across agents/models are meaningful research directions. | Does not establish unconditional procedure transfer or that procedural abstractions may omit applicability/counterexamples. | procedural memory |
| `EA-17` | `ACL_FINDINGS_PEER_REVIEWED` | Remember Me, Refine Me: A Dynamic Procedural Memory Framework for Experience-Driven Agent Evolution — https://aclanthology.org/2026.findings-acl.829/ | Procedural memory can benefit from failure-aware distillation, context-adaptive reuse and utility-based refinement. | Does not prove utility is epistemic authority or that pruning is safe without preservation/recoverability contracts. | procedural lifecycle |
| `EA-18` | `ARXIV_PREPRINT` | ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory — https://arxiv.org/abs/2509.25140 | Successful and failed trajectories can be distilled into reusable reasoning strategies, motivating experience-derived procedure candidates. | Does not prove self-judged experience is independent evidence or that repeated self-generated memories should gain authority. | self-evolving procedures |
| `EA-19` | `ARXIV_PREPRINT` | Managing Procedural Memory in LLM Agents: Control, Adaptation, and Evaluation (AFTER) — https://arxiv.org/abs/2606.23127 | Procedural transfer should be evaluated across tasks, roles and model backbones rather than assumed from local success. | Does not establish a universal transfer policy or calibrated applicability for Nolane. | procedure transfer, executor compatibility |
| `EA-20` | `ARXIV_PREPRINT` | Causal Intervention-Based Memory Selection for Long-Horizon LLM Agents — https://arxiv.org/abs/2605.17641 | Topical relevance and behavioral usefulness are different; controlled memory interventions are a plausible way to estimate effect. | Does not prove causal attribution under arbitrary multi-memory exposure or justify rewriting factual truth based on harmfulness. | memory effect, interference |
| `EA-21` | `ARXIV_PREPRINT` | Remembering More, Risking More: Longitudinal Safety Risks in Memory-Equipped LLM Agents — https://arxiv.org/abs/2605.17830 | Memory safety should be evaluated longitudinally across accumulated memory states and compared with no-memory counterfactuals. | Does not prove every memory system's risk monotonically grows or identify Nolane's causal failure mechanisms by itself. | longitudinal safety, effect evaluation |
| `EA-22` | `ARXIV_PREPRINT` | EvoMemBench: Benchmarking Agent Memory from a Self-Evolving Perspective — https://arxiv.org/abs/2605.18421 | No single memory approach currently dominates across memory scope/content settings; long-context baselines remain important. | Does not prove external memory is generally inferior or that benchmark rankings transfer to Nolane's target workloads. | baseline discipline, external validity |
| `EA-23` | `ARXIV_PREPRINT` | Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents — https://arxiv.org/abs/2607.08716 | Decision-relevant state can fail to influence behavior unless memory is selectively surfaced at the right time; proactive injection is a serious design pressure. | Does not prove when Nolane must recall, does not define completeness of hard obligations, and does not grant memory action authority. | proactive obligation, behavioral state decay |
| `EA-24` | `ACL_MAIN_PEER_REVIEWED` | Mem2ActBench: A Benchmark for Evaluating Long-Term Memory Utilization in Task-Oriented Autonomous Agents — https://aclanthology.org/2026.acl-long.370/ | Memory evaluation must include proactive application to tool selection and parameter grounding, not only explicit-question retrieval. | Does not prove Nolane's RecallBoundaryDescriptor is complete or that benchmark memory dependencies cover all consequential actions. | action-boundary recall, tool parameter grounding |
| `EA-25` | `ACL_MAIN_PEER_REVIEWED` | Controllable Memory Usage: Balancing Anchoring and Innovation in Long-Term Human–Agent Interaction — https://aclanthology.org/2026.acl-long.670/ | Memory reliance can itself be a controllable behavioral dimension and overuse can create anchoring in the studied setting. | Does not justify suppressing current hard constraints or equate fresh-start mode with epistemic forgetting. | memory reliance policy, interference |
| `EA-26` | `ARXIV_PREPRINT_WITH_MACHINE_CHECKED_MODEL` | Securing LLM-Agent Long-Term Memory Against Poisoning: Non-Malleable, Origin-Bound Authority with Machine-Checked Guarantees — https://arxiv.org/abs/2606.24322 | Self-summary, trusted-tool echo and manufactured corroboration are concrete laundering channels; write-time origin binding/non-malleable authority deserve explicit evaluation. | Its theorem is scoped to its formal model; it does not prove Nolane's full security architecture or every real-world information-flow path. | origin authority, security |
| `EA-27` | `ARXIV_PREPRINT` | When Agents Remember Too Much: Memory Poisoning Attacks on Large Language Model Agents (GhostWriter) — https://arxiv.org/abs/2607.06595 | Persistent memory creates delayed injection/activation attack surfaces in tested tool-using personal agents. | Reported attack rates are configuration-specific and do not prove Nolane is safe or unsafe. | lifecycle security, poisoning |
| `EA-28` | `ARXIV_PREPRINT` | MemSecBench: Tracking Agent Memory Poisoning from Persistence to Consequence and Repair — https://arxiv.org/abs/2607.27080 | Memory security should be evaluated across write, execution consequence and selective repair, not just initial injection. | Does not prove selective repair is complete or validate Nolane's repair algorithm. | security lifecycle, repair |
| `EA-29` | `ARXIV_PREPRINT` | FragFuse: Bypassing Access Control of Large Language Model Agents via Memory-Based Query Fragmentation and Fusion — https://arxiv.org/abs/2606.15609 | Individually benign-looking stored fragments can combine through later memory reconstruction to bypass tested access-control mechanisms; composition is a security boundary. | Does not prove every fragment composition is dangerous or that Nolane's proposed composition gate is sufficient. | compositional information flow, frame security |
| `EA-30` | `ARXIV_PREPRINT` | Isolated but Exposed: Persistence-Based Memory Extraction Attack on LLM Agents (SPORE) — https://arxiv.org/abs/2607.23444 | User-level memory isolation alone may not protect private memory when retrieved data can be serialized into malicious tool-call parameters. | Does not prove all tool interfaces leak or that per-record isolation is useless; it identifies a sink-boundary failure class. | tool sink disclosure, privacy |
| `EA-31` | `ARXIV_PREPRINT` | AgentSecBench: Measuring Prompt Injection, Privacy Leakage, and Tool-Use Integrity in LLM Agents — https://arxiv.org/abs/2605.26269 | Security policy should be enforced by projecting authorized observations/capabilities rather than prompt annotation alone. | Does not prove complete noninterference for arbitrary agents or directly validate Nolane's memory-specific access model. | authorized projection, tool capability boundary |
| `EA-32` | `ARXIV_PREPRINT` | Your LLM Agent Can Leak Your Data: Data Exfiltration via Backdoored Tool Use (Back-Reveal) — https://arxiv.org/abs/2604.05432 | Memory-access and tool-call composition can create persistent exfiltration channels in backdoored-agent threat models. | Does not imply ordinary agents are backdoored or quantify Nolane risk without matching threat assumptions. | memory-to-tool exfiltration |
| `EA-33` | `ACL_FINDINGS_PEER_REVIEWED` | AnchorMem: Anchored Facts with Associative Contexts for Building Memory in Large Language Models — https://aclanthology.org/2026.findings-acl.1736/ | Separating compact retrieval anchors from preserved original context is a credible memory design pressure. | Does not prove anchors are authority or that immutable context alone solves temporal, access or preservation semantics. | anchors, retrieval-context decoupling |
| `EA-34` | `ACL_FINDINGS_PEER_REVIEWED` | Text2Mem: A Unified Memory Operation Language for Memory Operating System — https://aclanthology.org/2026.findings-acl.100/ | Typed/validated memory operations and backend-independent execution fidelity are useful conformance pressures for memory runtimes. | Does not define Nolane's epistemic semantics or prove one operation language is sufficient for all memory transitions. | typed operations, backend conformance |
| `EA-35` | `ICLR_2026_WORKSHOP_OPENREVIEW` | New Frontiers in Associative Memory workshop paper (AIM) — https://openreview.net/pdf?id=Y7r5ZODl7l | Associative-memory-inspired interference tracking and pattern separation are plausible empirical tools for studying harmful retrieval. | Workshop evidence is not a universal theory of agent-memory interference and does not calibrate Nolane's production thresholds. | interference, association |
| `EA-36` | `ARXIV_PREPRINT` | GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memory Agents — https://arxiv.org/abs/2606.18829 | Shared-memory quality is not exhausted by recall utility: multi-principal authorization and active forgetting are independently testable governance surfaces, and current tested methods do not simultaneously solve utility, access control, and deletion behavior. | Does not prove Nolane's cross-domain publication protocol, confidentiality algebra, or forgetting semantics are sufficient or optimal. | multi-principal shared memory, cross-domain publication, access and deletion governance |
| `EA-37` | `ARXIV_POSITION_PAPER` | Multi-Agent Memory from a Computer Architecture Perspective: Visions and Challenges Ahead — https://arxiv.org/abs/2603.10062 | Memory consistency and structured access control are recognized open challenges for multi-agent memory; shared/distributed memory semantics should therefore be explicit rather than hidden behind one global store abstraction. | Does not establish a concrete consistency model for Nolane Memory and does not prove the single-correctness-writer-per-authority-domain choice is optimal. | multi-agent memory consistency, shared versus distributed memory boundary, access-control semantics |
| `EA-38` | `ARXIV_PREPRINT` | Deployment-Time Memorization in Foundation-Model Agents — https://arxiv.org/abs/2606.10062 | Deletion fidelity in persistent agent memory must be evaluated across derived tiers, not only the raw record. In the reported LongMemEval experiments, raw-only deletion left recoverable summary residue in about one fifth of instances, while stronger full-pipeline purge/tombstone-redaction strategies removed worst-tier residue in that setup. | Does not prove one universal purge algorithm, that every derived representation leaks at the same rate, or that Nolane's proposed erasure-barrier/rederivation semantics are sufficient. | derived deletion residue, erasure closure, backup/restore deletion dominance, privacy-versus-recoverability semantics |
| `EA-39` | `PMLR_PROCEEDINGS_2026` | Agent-Memory Protocol: A Privacy-Focused Protocol for LLM Agents and User Memory Interaction — https://proceedings.mlr.press/v317/wu26a.html | Agent-memory interaction benefits from an explicit privacy boundary between persistent user memory and the computation/model interface, supporting the need to treat memory disclosure/use interfaces as protocol surfaces. | Does not prove Nolane's confidentiality capability algebra, compositional sink gate, or recovery-erasure protocol. | memory interface privacy, model/sink disclosure boundary, persistent user memory governance |
| `EA-40` | `ARXIV_PREPRINT` | Hidden in Memory: Sleeper Memory Poisoning in LLM Agents — https://arxiv.org/abs/2605.15338 | Persistent memory can carry attacker-planted state across later sessions and influence future agentic behavior, so continuity artifacts and reactivated memories require provenance, delayed-trigger and revalidation semantics. | Does not show that every persistent memory is vulnerable, or that Nolane's origin/anchor/recovery controls eliminate sleeper poisoning. | cross-session poisoning, continuity-artifact revalidation, delayed trigger security |
| `EA-41` | `ARXIV_SURVEY` | A Survey on Long-Term Memory Security in LLM Agents: Attacks, Defenses, and Governance Across the Memory Lifecycle — https://arxiv.org/abs/2604.16548 | Long-term memory security spans Write, Store, Retrieve, Execute, Share/Propagate, and Forget/Rollback phases; security therefore requires lifecycle-level provenance, versioning, policy-aware retention and recoverable governance rather than a retrieval-only defense. | As a survey/framework paper it does not validate Nolane Memory, establish a single optimal lifecycle architecture, or prove the specific non-revivable-barrier semantics. | forget/rollback seam, lifecycle governance, provenance/versioning requirements |
| `EA-42` | `ARXIV_PREPRINT` | ChronoMem: Version Control and Semantic Rollback for Large Language Model Agent Memory — https://arxiv.org/abs/2607.27773 | Semantic versioning and rollback are meaningful first-class operations for agent memory, and post-exposure evaluation should test whether a rollback restores behavior consistent with the selected historical memory state. | Does not establish that semantic rollback should reverse privacy deletion, access revocation, source compromise or other governance barriers. Nolane explicitly treats those dimensions separately. | semantic rollback, historical memory versions, rollback-versus-governance-barrier distinction |
| `EA-43` | `ARXIV_PREPRINT` | Control-Plane Placement Shapes Forgetting: An Architectural Study of Agent Memory Across Thirteen System Configurations — https://arxiv.org/abs/2606.15903 | Forgetting behavior depends materially on where mutation/control logic is placed, and deletion correctness cannot be reduced to recall filtering; mutation-time control is a distinct architectural surface in the reported experiments. | Does not prove the reported architecture is universally best or that Nolane's retention/deletion control plane has correct real-world coverage. | forgetting control plane, mutation-time deletion semantics, active erasure enforcement |
| `EA-44` | `ACL_MAIN_PEER_REVIEWED` | How Memory Management Impacts LLM Agents: An Empirical Study of Experience-Following Behavior — https://aclanthology.org/2026.acl-long.27/ | Memory addition/deletion and similarity-driven experience reuse can materially alter agent behavior, including error propagation and misaligned experience replay; current-use effects must therefore remain separate from factual truth and be evaluated longitudinally. | Does not prove Nolane's effect ledger, interference thresholds, or deletion/recovery semantics. | memory deletion behavior, experience-following, error propagation |
| `EA-45` | `ARXIV_PREPRINT` | Capability Gates Are Not Authorization: Confused-Deputy Failures in LLM Agent Frameworks — https://arxiv.org/abs/2606.28679 | Tool exposure/capability gating is not equivalent to deterministic per-call authorization of the concrete model-emitted operation and argument values. Memory-grounded tool use therefore needs a use-time boundary check tied to the final call rather than relying only on tool availability. | Does not prove Nolane's MemoryUseFence sufficient, does not establish one universal PDP/PEP design, and evaluates pinned framework configurations rather than every agent deployment. | use-time action grounding, final argument binding, memory adequacy versus ordinary action authorization |
| `EA-46` | `ARXIV_PREPRINT` | STALE: Can LLM Agents Know When Their Memories Are No Longer Valid? — https://arxiv.org/abs/2605.06527 | Retrieving updated evidence is not enough: agents can continue accepting stale premises or acting under implicitly invalidated state. Current-use memory therefore requires explicit state adjudication and downstream policy/application checks, not retrieval recency alone. | Does not prove Nolane's temporal supersession, semantic dependency fence, or proactive use-time validator. | implicit stale dependencies, downstream policy adaptation, current-use revalidation |
| `EA-47` | `ARXIV_PREPRINT` | When Memory Becomes Authority: Benchmarking Authority Collapse at the Memory Consolidation Boundary — https://arxiv.org/abs/2608.01679 | Consolidation can preserve claim content while erasing source-authority constraints and thereby increase downstream action authority. Consolidation/promotion must preserve source authority and revalidate it at use. | Does not prove Nolane's authority algebra, proposal dependency fence, or all-action safety; reported reductions apply to the evaluated benchmark/configurations. | consolidation authority, proposal promotion fence, use-time authority preservation |
| `EA-48` | `ARXIV_PREPRINT` | When Memory Updates but Behavior Does Not: Repairing Implicit Stale Dependencies in Personalized Agent Responses — https://arxiv.org/abs/2608.01619 | A draft/action can remain anchored to stale assumptions even when the memory store contains a newer state; auditing from current state toward the proposed output is a distinct intervention surface from retrieval. | Does not establish general-purpose agent-memory correctness or prove that Nolane's use fence/draft revalidation will reproduce the paper's gains outside its evaluated settings. | output-side stale dependency audit, compile-to-use gap, current state to action validation |
| `EA-49` | `ARXIV_PREPRINT` | Supersede: Diagnosing and Training the Memory-Update Gap in LLM Agents — https://arxiv.org/abs/2606.27472 | Using the current superseding value is a distinct memory-maintenance capability whose failure can worsen with longer histories even when more memory space is provided; correctness therefore requires explicit supersession/currentness semantics. | Does not prove one deterministic supersession rule works for every relation or that Nolane's causal-cut and truth-maintenance semantics are empirically optimal. | current value selection, supersession, long-history stale memory |
| `EA-50` | `ARXIV_PREPRINT` | Governing Dynamic Capabilities: Cryptographic Binding and Reproducibility Verification for AI Agent Tool Use — https://arxiv.org/abs/2603.14332 | Runtime capability identity can change after earlier authorization, so a consequential call may need binding to the capability/tool configuration that was actually authorized and rechecking when that configuration changes. | Does not prove Nolane requires the paper's certificate design, that its benchmark covers all dynamic-capability attacks, or that memory-use fencing is cryptographically complete. | tool profile generation, capability drift, use-time tool binding |
| `EA-51` | `ARXIV_PREPRINT` | Governed Shared Memory for Multi-Agent LLM Systems — https://arxiv.org/abs/2606.24535 | Live multi-agent memory can expose asymmetric scope enforcement and pipeline-ordering conflicts that design-only evaluation misses; shared memory needs explicit propagation, provenance, supersession and access semantics. | Does not prove Nolane's causal-cut vector, publication saga or scope algebra sufficient, and the reported production-service observations are specific to the studied implementation. | multi-domain causal visibility, scope enforcement, publication/currentness |
| `EA-52` | `ARXIV_PREPRINT` | SuperLocalMemory 4.0: The Governed Memory Operating System for AI Agents — https://arxiv.org/abs/2608.08253 | Generation-fenced admission and per-projection apply/verify/compensate/erase ownership are practical mechanisms for making governed memory writes and derived projections fail-visible under fault injection. | Does not independently validate Nolane's semantic OCC, causal-cut model or end-to-end quality; its reported mechanism measurements are scoped to the released implementation/evidence bundle. | generation-fenced memory mutation, projection ownership, fault-injected governed writes |
| `EA-53` | `ARXIV_PREPRINT` | Agent Zero Memory: Provenance-Aware Long-Term Memory for LLM Agents — https://arxiv.org/abs/2608.29606 | Parallel memory representations can retain distinct strengths when reads remain provenance-grounded; citation-locked reading is useful pressure for ensuring an answer does not cite evidence the retrieval/reader never actually opened. | Does not prove Nolane's three-plane architecture, its benchmark superiority on other tasks, or that citation lock alone solves stale-use, authority, privacy or concurrency semantics. | provenance-grounded read discipline, multi-view representations, opened-evidence accountability |

### Internal/user-supplied evidence classes

| ID | Class | Source | Allowed inference | Not established |
|---|---|---|---|---|
| `IA-01` | `USER_SUPPLIED_RESEARCH_NOTE` | Tề Hạ character/intelligence analysis V3 (`02-TE-HA-GIAI-PHAU-NHAN-VAT-VA-KIEN-TRUC-TRI-TUE-V3-VERIFIED-COMPREHENSIVE.md`) | Inspirational structure: layered/external/social memory, anchor cues, future-self reconstruction, world scaffolding, self-model as prior. | Fictional/cognitive analysis does not establish production AI correctness, neuroscience equivalence, or empirical performance. |
| `IA-02` | `USER_SUPPLIED_ENGINEERING_RESEARCH_SPEC` | Tề Hạ to AI QX Agent Cognitive Harness V3 (`03-TE-HA-TO-AI-QX-AGENT-COGNITIVE-HARNESS-V3-VERIFIED-ENGINEERING-SPEC.md`) | Prior user research on layered memory, anchors, recovery bootloader and self-version handoff. | A prior spec is not an implementation or independent validation. |
| `IA-03` | `USER_SUPPLIED_REFERENCE_SPEC` | Nolane Plan Runtime Architecture v0.15 (`NOLANE-PLAN-RUNTIME-ARCHITECTURE-V0.15-PRINCIPAL-SCOPED-MULTI-AGENT-CLOSURE-SPEC(2).md`) | Research methodology: pre-code semantic oracles, closure matrices, mutation matrices, migration semantics, strict stop rule and evidence-level discipline. | Its planning ontology/architecture is not imported as Nolane Memory architecture. |
| `IA-04` | `USER_SUPPLIED_SOURCE_BUNDLE` | Nolane World 0.12.0 supplied source bundle (`Nolane-World-0.12.0-QX-380-ENGINEERING-SPEC-CLOSURE-VERIFIED-COMPLETE(2).zip`) | Executable source counterexamples, tested substrate patterns, W5 research scaffolding and migration/reuse constraints. | The supplied bundle is not proof of current upstream state, Nolane Memory implementation, or independent validation. |

### Evidence-register rules

- Publication class is explicit; arXiv/preprint/workshop evidence is never relabeled peer-reviewed.
- Allowed inference states the narrow pressure the source may place on Nolane Memory.
- Not-established states the inference the specification is forbidden to draw from that source alone.
- Reported empirical metrics, when mentioned, remain authors' reported results and are not Nolane validation.
- Internal user-supplied specs/source are distinguished from independent external evidence.

Current evidence-register internal digest: `cf5b4bd410497eb31ead0f5f87c52aa0c0467391dc0911b3f733e17015df647a`.
