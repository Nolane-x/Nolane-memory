import tempfile
import unittest
from datetime import datetime, timezone, timedelta

from nolane_memory import MemoryRuntime
from nolane_memory.types import LossState, RecallRole
from nolane_memory.errors import MemoryDependencyStale, ActionArgumentMismatch, MemoryFenceReplay, MemoryFenceExpired


class FakeClock:
    def __init__(self): self.now = datetime(2026, 9, 5, 3, 0, tzinfo=timezone.utc)
    def __call__(self): return self.now


class UseTimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = FakeClock()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db", clock=self.clock)
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("PREF", {"polarity"})
        self.region = self.rt.create_region("d", "r1", principal="alice")
        self.rep = self.rt.add_representation(
            "d", self.region, kind="exact", payload={"polarity": "yes"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5, principal="alice")

    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def _frame(self):
        return self.rt.compile_recall("d", "alice", [RecallRole("pref", self.region, "PREF")], 20)

    def test_irrelevant_write_does_not_invalidate_frame(self):
        frame = self._frame()
        other = self.rt.create_region("d", "unrelated", principal="alice")
        self.rt.add_representation(
            "d", other, kind="exact", payload={"polarity": "no"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5, principal="alice")
        fence = self.rt.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"to": "x", "body": "ok"})
        self.assertTrue(self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"to": "x", "body": "ok"}))

    def test_relevant_dependency_change_invalidates_frame(self):
        frame = self._frame()
        self.rt.invalidate_representation("d", self.rep, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"x": 1})

    def test_final_payload_is_bound_and_fence_is_single_use(self):
        frame = self._frame()
        fence = self.rt.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"amount": 10})
        with self.assertRaises(ActionArgumentMismatch):
            self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"amount": 11})
        self.assertTrue(self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"amount": 10}))
        with self.assertRaises(MemoryFenceReplay):
            self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"amount": 10})

    def test_expiry_uses_runtime_trusted_clock_and_half_open_boundary(self):
        frame = self._frame()
        expiry = self.clock.now + timedelta(seconds=5)
        fence = self.rt.issue_use_fence(frame, principal="alice", sink="tool:send", payload={"x": 1}, expires_at=expiry)
        self.clock.now = expiry
        with self.assertRaises(MemoryFenceExpired):
            self.rt.consume_use_fence(fence.fence_id, principal="alice", sink="tool:send", payload={"x": 1})


if __name__ == "__main__": unittest.main()
