"""End-to-end deterministic K0-K5 support demo for Nolane Memory v0.6.3."""
from tempfile import TemporaryDirectory

from nolane_memory import EffectTier, LossState, MemoryRuntime, RecallRole


with TemporaryDirectory() as td:
    rt = MemoryRuntime(f"{td}/memory.db")
    rt.create_domain("personal", writer_epoch=1)
    rt.register_query_family("EXACT_VALUE", {"exact_number"})
    rt.set_runtime_compatibility("personal", mission_revision="mission:1", environment_revision="env:1")
    rt.set_self_version("personal", "agent:v1", {"context_window": 64_000})
    rt.set_access_profile(
        "personal", "alice",
        {"DISCOVER", "READ_EXACT", "USE_FOR_LOCAL_REASONING", "DERIVE", "HYDRATE_SOURCE",
         "DISCLOSE_TO_TOOL", "CHANGE_RETENTION", "PUBLISH_TO_DOMAIN"},
        sink_capabilities={"tool:deploy": ["DISCLOSE_TO_TOOL"]},
    )

    h = rt.head("personal")
    evidence = rt.capture_evidence(
        domain_id="personal", operation_id="capture-1", expected_seq=h.sequence, writer_epoch=1,
        source_event_identity="benchmark:latency:1", content={"exact_number": 97.36}, principal="alice",
    )
    region = rt.create_region("personal", "deployment:latency", principal="alice")
    raw = rt.add_representation(
        "personal", region, kind="raw", payload={"exact_number": 97.36},
        loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=40,
        principal="alice", source_evidence_ids=[evidence.object_id], transform_kind="SOURCE_REBASE",
    )
    compact = rt.add_representation(
        "personal", region, kind="summary", payload={"text": "roughly 100 ms"},
        source_representation_ids=[raw], loss={"exact_number": LossState.LOST},
        recoverable={"exact_number"}, token_cost=5, principal="alice",
    )
    rt.index_representation_view("personal", compact, "objective", ["deployment-latency"])

    role = RecallRole("need-exact", region, "EXACT_VALUE", hard=True)
    frame = rt.compile_recall("personal", "alice", [role], token_budget=50)
    assert frame.fragments[0].representation_id == raw
    assert frame.fragments[0].page_faulted

    rt.record_effect_evidence(
        "personal", [compact], consumer="agent:v1", task="deploy", regime="env:1", rendering="narrative",
        outcome_dimension="accuracy", tier=EffectTier.E0, effect=-0.2, confidence=0.6,
    )
    guarded, guard = rt.apply_interference_guard(
        frame, consumer="agent:v1", task="deploy", regime="env:1", rendering="narrative")
    assert guarded.sufficiency == "SUFFICIENT" and not guard.inhibited_optional_representation_ids

    payload = {"latency_ms": 97.36, "target": "deploy"}
    flow = rt.check_information_flow(frame, principal="alice", sink="tool:deploy", payload=payload)
    assert flow.decision == "ALLOW"
    fence = rt.issue_use_fence(frame, principal="alice", sink="tool:deploy", payload=payload)
    assert rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:deploy", payload=payload)

    pin = rt.create_continuity_pin("personal", principal="alice", hard_roles=[role], stable_refs=[evidence.object_id, raw])
    recovery = rt.assess_recovery("personal", pin_id=pin.pin_id, principal="alice")
    assert recovery.resume_allowed

    lab = rt.run_preservation_lab()
    fuzz = rt.run_lifelong_fuzz(seed=73, cases=2_000)
    assert lab.failed == 0 and fuzz.failed == 0

    print({
        "frame": frame.sufficiency,
        "flow": flow.decision,
        "recovery": recovery.resume_allowed,
        "formal_cases": lab.cases,
        "fuzz_cases": fuzz.cases,
        "research_closure": rt.k5_profile_status()["research_closure"],
    })
    rt.close()
