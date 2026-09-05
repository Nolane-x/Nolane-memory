import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from nolane_memory import MemoryRuntime
from nolane_memory.errors import (
    ActionArgumentMismatch,
    MemoryFlowPolicyCurrentnessUnknown,
    MemoryUseValidationUnavailable,
)
from nolane_memory.types import FlowDecision, LossState, RecallRole


class InformationFlowUseTimeLeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
        self.rt = MemoryRuntime(
            f"{self.tmp.name}/m.db",
            clock=lambda: self.now,
            clock_authority_id="clock:trusted",
            clock_epoch="epoch:1",
        )
        self.rt.create_domain("d")
        self.rt.register_query_family("Q", {"x"})
        self.rt.set_access_profile(
            "d", "alice",
            {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE", "DISCLOSE_TO_TOOL"},
            sink_capabilities={"tool:send": ["DISCLOSE_TO_TOOL"]},
        )
        region = self.rt.create_region("d", "r", principal="alice")
        self.rep = self.rt.add_representation(
            "d", region, kind="exact", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice",
        )
        self.frame = self.rt.compile_recall("d", "alice", [RecallRole("r", region, "Q")], 20)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_allow_receipt_is_a_policy_generation_lease(self):
        receipt = self.rt.check_information_flow(
            self.frame, principal="alice", sink="tool:send", payload={"x": 1}
        )
        self.assertEqual(receipt.decision, FlowDecision.ALLOW.value)
        self.assertTrue(receipt.dependencies)
        self.assertTrue(self.rt.validate_information_flow_receipt(
            receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1}
        ))

        self.rt.set_access_profile("d", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        with self.assertRaises(MemoryFlowPolicyCurrentnessUnknown):
            self.rt.validate_information_flow_receipt(
                receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1}
            )

    def test_flow_receipt_binds_exact_payload_and_sink(self):
        receipt = self.rt.check_information_flow(
            self.frame, principal="alice", sink="tool:send", payload={"recipient": "A"}
        )
        with self.assertRaises(ActionArgumentMismatch):
            self.rt.validate_information_flow_receipt(
                receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"recipient": "B"}
            )
        with self.assertRaises(MemoryFlowPolicyCurrentnessUnknown):
            self.rt.validate_information_flow_receipt(
                receipt.flow_receipt_id, principal="alice", sink="tool:other", payload={"recipient": "A"}
            )

    def test_policy_currentness_unavailable_fails_closed(self):
        receipt = self.rt.check_information_flow(
            self.frame, principal="alice", sink="tool:send", payload={"x": 1}
        )
        self.rt.set_capability_availability("d", "flow_policy_currentness", False)
        with self.assertRaises(MemoryFlowPolicyCurrentnessUnknown):
            self.rt.validate_information_flow_receipt(
                receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1}
            )

    def test_expiring_allow_receipt_uses_trusted_half_open_time(self):
        expiry = self.now + timedelta(minutes=1)
        receipt = self.rt.check_information_flow(
            self.frame, principal="alice", sink="tool:send", payload={"x": 1}, expires_at=expiry
        )
        self.assertEqual(receipt.clock_authority_id, "clock:trusted")
        self.assertEqual(receipt.clock_epoch, "epoch:1")
        self.now = expiry
        with self.assertRaises(MemoryFlowPolicyCurrentnessUnknown):
            self.rt.validate_information_flow_receipt(
                receipt.flow_receipt_id, principal="alice", sink="tool:send", payload={"x": 1}
            )

    def test_use_fence_references_and_revalidates_exact_flow_receipt(self):
        fence = self.rt.issue_use_fence(
            self.frame, principal="alice", sink="tool:send", payload={"x": 1}
        )
        self.assertIsNotNone(fence.flow_receipt_id)
        self.rt.set_access_profile("d", "alice", {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE"})
        with self.assertRaises(MemoryFlowPolicyCurrentnessUnknown):
            self.rt.consume_use_fence(
                fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1}
            )

    def test_section_394_information_flow_campaign(self):
        report = self.rt.run_information_flow_use_time_campaign(seed=394)
        self.assertTrue(report["passed"])
        self.assertEqual(report["fixture_count"], 6)
        self.assertEqual(report["failed"], 0)



class ResourcePressureUseValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("Q", {"x"})
        self.rt.set_access_profile(
            "d", "alice",
            {"DISCOVER", "USE_FOR_LOCAL_REASONING", "DERIVE", "DISCLOSE_TO_TOOL"},
            sink_capabilities={"tool:send": ["DISCLOSE_TO_TOOL"]},
        )
        region = self.rt.create_region("d", "r", principal="alice")
        self.rt.add_representation(
            "d", region, kind="exact", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice",
        )
        self.frame = self.rt.compile_recall("d", "alice", [RecallRole("r", region, "Q")], 20)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_resource_pressure_never_skips_use_validation(self):
        fence = self.rt.issue_use_fence(
            self.frame, principal="alice", sink="tool:send", payload={"x": 1}
        )
        self.rt.set_capability_availability("d", "use_validation", False)
        with self.assertRaises(MemoryUseValidationUnavailable):
            self.rt.consume_use_fence(
                fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1}
            )
        row = self.rt.db.execute("SELECT consumed_at FROM fences WHERE fence_id=?", (fence.fence_id,)).fetchone()
        self.assertIsNone(row["consumed_at"])

        self.rt.set_capability_availability("d", "use_validation", True)
        self.assertTrue(self.rt.consume_use_fence(
            fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1}
        ))

    def test_section_395_resource_pressure_campaign(self):
        report = self.rt.run_resource_pressure_use_validation_campaign(seed=395)
        self.assertTrue(report["passed"])
        self.assertEqual(report["fixture_count"], 4)
        self.assertEqual(report["failed"], 0)



if __name__ == "__main__":
    unittest.main()
