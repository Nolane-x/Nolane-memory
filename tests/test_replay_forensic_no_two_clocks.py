import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime, RecallRole


class ReplayForensicAndNoTwoClocksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_historical_causal_cut_preserves_incarnation_and_new_incarnation_invalidates_pin(self):
        self.rt.register_query_family("X", {"x"})
        region = self.rt.create_region("d", "r", principal="alice")
        rep = self.rt.add_representation(
            "d", region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice",
        )
        old_head = self.rt.head("d")
        pin = self.rt.create_continuity_pin(
            "d", principal="alice", hard_roles=[RecallRole("x", region, "X")], stable_refs=[rep],
        )
        self.rt.start_new_incarnation("d", principal="alice", reason="restore-test", operation_id="inc-1")
        historical = self.rt.close_causal_cut({"d": old_head.sequence})["d"]
        self.assertEqual(historical.incarnation, old_head.incarnation)
        assessment = self.rt.assess_recovery("d", pin_id=pin.pin_id, principal="alice")
        self.assertEqual(assessment.layers["R3_NON_REVIVAL_BARRIER"], "BLOCKED")

    def test_replay_assessment_distinguishes_exact_historical_and_governance_barrier(self):
        h = self.rt._head_row("d")
        ev = self.rt.capture_evidence(
            domain_id="d", operation_id="e1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity="evt-1", content={"x": 1}, principal="alice", origin_roots=["origin:1"],
        ).object_id
        cut = self.rt.head("d")
        a = self.rt.assess_replay("d", cut, principal="alice", required_refs=[ev])
        self.assertIn("EXACT_SEMANTIC_REPLAY", a.available_modes)
        self.assertEqual(a.current_use_mode, "CURRENT_REEVALUATION")
        self.rt.erase_evidence("d", ev, principal="alice", policy_ref="privacy-delete")
        b = self.rt.assess_replay("d", cut, principal="alice", required_refs=[ev])
        self.assertIn("HISTORICAL_JUDGEMENT_REPLAY", b.available_modes)
        self.assertEqual(b.current_use_mode, "UNAVAILABLE_BY_POLICY")
        self.assertTrue(b.barriers)

    def test_live_connector_without_snapshot_is_non_hermetic_replay_dependency(self):
        self.rt.register_connector_profile(
            "d", "api", revision=1,
            capabilities={"stable_event_ids": True, "point_in_time_snapshot": False,
                          "pagination_guarantee": False, "update_delete_visibility": True},
            transport_authority="TRUSTED_TRANSPORT", content_authority="UNTRUSTED_CONTENT",
        )
        q = self.rt.record_connector_query(
            "d", connector_id="api", principal="alice", predicate={"q": "x"}, snapshot_id=None,
            pages_seen=1, pagination_complete=False, result_capped=False, result_ids=[], provider_error=None,
        )
        a = self.rt.assess_replay(
            "d", q.cut, principal="alice", connector_receipt_ids=[q.receipt_id]
        )
        self.assertEqual(a.current_use_mode, "NON_HERMETIC_REPLAY")

    def test_no_two_writable_clocks_audit_detects_current_history_drift(self):
        self.rt.set_access_profile("d", "alice", ["READ_EXACT"])
        clean = self.rt.audit_no_two_writable_clocks("d")
        self.assertTrue(clean.passed)
        # Simulate corruption/legacy duplicate authority by mutating the current mirror without a revision.
        self.rt.db.execute(
            "UPDATE access_profiles SET revision=99, capabilities_json='[\"*\"]' WHERE domain_id='d' AND principal='alice'"
        )
        bad = self.rt.audit_no_two_writable_clocks("d")
        self.assertFalse(bad.passed)
        self.assertTrue(any(v["kind"] == "ACCESS_CURRENT_HISTORY_DIVERGENCE" for v in bad.violations))


if __name__ == "__main__":
    unittest.main()
