from datetime import datetime, timedelta, timezone
import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryDependencyStale, MemoryTransitionIncomplete


class ProspectiveTriggerLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = datetime(2026, 9, 5, 0, 0, tzinfo=timezone.utc)
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db", clock=lambda: self.now)
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})
        self.region = self.rt.create_region("d", "r", principal="alice")
        self.source = self.rt.add_representation(
            "d", self.region, kind="source", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=4,
            principal="alice",
        )
        self.role = RecallRole("future-x", self.region, "X", hard=True)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_trigger_expires_half_open_and_does_not_fire_at_expiry(self):
        expiry = self.now + timedelta(hours=1)
        tid = self.rt.register_prospective_trigger(
            "d", "deploy", owner="alice", roles=[self.role], expires_at=expiry,
            source_representation_ids=[self.source],
        )
        self.assertEqual([r.role_id for r in self.rt.fire_prospective_triggers("d", "deploy", principal="alice")], ["future-x"])
        self.now = expiry
        self.assertEqual(self.rt.fire_prospective_triggers("d", "deploy", principal="alice"), [])
        self.assertEqual(self.rt.get_prospective_trigger(tid)["status"], "EXPIRED")

    def test_source_lineage_invalidation_makes_trigger_ineligible(self):
        tid = self.rt.register_prospective_trigger(
            "d", "deploy", owner="alice", roles=[self.role],
            source_representation_ids=[self.source],
        )
        self.rt.invalidate_representation("d", self.source, principal="alice")
        self.assertEqual(self.rt.fire_prospective_triggers("d", "deploy", principal="alice"), [])
        self.assertEqual(self.rt.get_prospective_trigger(tid)["status"], "SOURCE_STALE")

    def test_revoke_is_sticky_and_reactivation_is_explicit_transition(self):
        tid = self.rt.register_prospective_trigger("d", "deploy", owner="alice", roles=[self.role])
        self.rt.revoke_prospective_trigger("d", tid, principal="alice", reason="cancelled")
        self.assertEqual(self.rt.fire_prospective_triggers("d", "deploy", principal="alice"), [])
        same = self.rt.register_prospective_trigger("d", "deploy", owner="alice", roles=[self.role])
        self.assertEqual(same, tid)
        self.assertEqual(self.rt.fire_prospective_triggers("d", "deploy", principal="alice"), [])
        self.rt.reactivate_prospective_trigger("d", tid, principal="alice", reason="new authorization")
        self.assertEqual([r.role_id for r in self.rt.fire_prospective_triggers("d", "deploy", principal="alice")], ["future-x"])

    def test_causal_frontier_blocks_until_all_required_domains_cover_it(self):
        self.rt.create_domain("other")
        required = {"d": self.rt.head("d").sequence, "other": 1}
        tid = self.rt.register_prospective_trigger(
            "d", "deploy", owner="alice", roles=[self.role], causal_frontier=required,
        )
        self.assertEqual(self.rt.fire_prospective_triggers("d", "deploy", principal="alice"), [])
        self.rt.create_region("other", "o", principal="alice")
        self.assertEqual([r.role_id for r in self.rt.fire_prospective_triggers("d", "deploy", principal="alice")], ["future-x"])
        self.assertEqual(self.rt.get_prospective_trigger(tid)["status"], "ACTIVE")


if __name__ == "__main__": unittest.main()
