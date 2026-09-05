import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryClockAuthorityRequired, MemoryFenceExpired


class MutableClock:
    def __init__(self, now):
        self.now = now
    def __call__(self):
        return self.now


class TrustedTimeFenceTests(unittest.TestCase):
    def _frame(self, rt):
        rt.create_domain("d")
        rt.register_query_family("X", {"x"})
        region = rt.create_region("d", "r", principal="alice")
        rt.add_representation(
            "d", region, kind="raw", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice",
        )
        return rt.compile_recall("d", "alice", [RecallRole("x", region, "X", hard=True)], 20)

    def test_expiring_fence_requires_declared_clock_authority(self):
        with tempfile.TemporaryDirectory() as td:
            clock = MutableClock(datetime(2026, 9, 5, tzinfo=timezone.utc))
            rt = MemoryRuntime(f"{td}/m.db", clock=clock, clock_authority_id=None, clock_epoch=None)
            frame = self._frame(rt)
            with self.assertRaises(MemoryClockAuthorityRequired):
                rt.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 1},
                                   expires_at=clock.now + timedelta(seconds=10))
            rt.close()

    def test_wrong_clock_epoch_after_restart_blocks_persisted_expiring_fence(self):
        with tempfile.TemporaryDirectory() as td:
            path = f"{td}/m.db"
            clock = MutableClock(datetime(2026, 9, 5, tzinfo=timezone.utc))
            rt = MemoryRuntime(path, clock=clock, clock_authority_id="trusted-wall", clock_epoch="boot-a")
            frame = self._frame(rt)
            fence = rt.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 1},
                                       expires_at=clock.now + timedelta(minutes=5))
            rt.close()

            rt2 = MemoryRuntime(path, clock=clock, clock_authority_id="trusted-wall", clock_epoch="boot-b")
            with self.assertRaises(MemoryClockAuthorityRequired):
                rt2.consume_use_fence(fence.fence_id, principal="alice", sink="model", payload={"x": 1})
            rt2.close()

    def test_exact_deadline_is_expired_and_backward_clock_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            clock = MutableClock(datetime(2026, 9, 5, tzinfo=timezone.utc))
            rt = MemoryRuntime(f"{td}/m.db", clock=clock, clock_authority_id="trusted-wall", clock_epoch="boot-a")
            frame = self._frame(rt)
            deadline = clock.now + timedelta(seconds=10)
            fence = rt.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 1}, expires_at=deadline)
            clock.now = deadline
            with self.assertRaises(MemoryFenceExpired):
                rt.consume_use_fence(fence.fence_id, principal="alice", sink="model", payload={"x": 1})

            clock.now = datetime(2026, 9, 5, tzinfo=timezone.utc)
            fence2 = rt.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 2},
                                        expires_at=clock.now + timedelta(seconds=10))
            clock.now = clock.now - timedelta(seconds=1)
            with self.assertRaises(MemoryClockAuthorityRequired):
                rt.consume_use_fence(fence2.fence_id, principal="alice", sink="model", payload={"x": 2})
            rt.close()

    def test_non_expiring_fence_does_not_require_time_authority(self):
        with tempfile.TemporaryDirectory() as td:
            clock = MutableClock(datetime(2026, 9, 5, tzinfo=timezone.utc))
            rt = MemoryRuntime(f"{td}/m.db", clock=clock, clock_authority_id=None, clock_epoch=None)
            frame = self._frame(rt)
            fence = rt.issue_use_fence(frame, principal="alice", sink="model", payload={"x": 1})
            self.assertTrue(rt.consume_use_fence(fence.fence_id, principal="alice", sink="model", payload={"x": 1}))
            rt.close()


if __name__ == "__main__":
    unittest.main()
