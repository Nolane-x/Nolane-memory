import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale
from nolane_memory.types import LossState, RecallRole


class SemanticReadSetClosureRedTests(unittest.TestCase):
    """E0 preregistered RED reproduction for the v0.7 SRSC candidate seam.

    The consumer previously grounded one payload field from memory region B, then later
    compiles an otherwise-current frame over independent region A. If B changes while A's
    declared dependency set remains current, a strong consequence using the stale B value
    should not be accepted silently.

    This test is intentionally RED on v0.6.3rc4 if the hidden premise is outside the
    enumerated frame/fence read-set. It must not be made green by globally invalidating
    every unrelated write; the eventual treatment must bind the material consequence-side
    dependency itself.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("ACTION", {"intent"})
        self.rt.register_query_family("RECIPIENT", {"recipient"})

        self.region_a = self.rt.create_region("d", "action", principal="alice")
        self.rep_a = self.rt.add_representation(
            "d",
            self.region_a,
            kind="exact",
            payload={"intent": "send-status"},
            loss={"intent": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=5,
            principal="alice",
        )

        self.region_b = self.rt.create_region("d", "recipient", principal="alice")
        self.rep_b_old = self.rt.add_representation(
            "d",
            self.region_b,
            kind="exact",
            payload={"recipient": "old@example.com"},
            loss={"recipient": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=5,
            principal="alice",
        )

    def tearDown(self):
        self.rt.close()
        self.tmp.cleanup()

    def test_stale_host_held_memory_premise_cannot_escape_current_frame_read_set(self):
        # Earlier context legitimately retrieved B and the host/model retained the value.
        earlier_b = self.rt.compile_recall(
            "d",
            "alice",
            [RecallRole("recipient", self.region_b, "RECIPIENT")],
            20,
        )
        stale_recipient = earlier_b.fragments[0].payload["recipient"]
        self.assertEqual(stale_recipient, "old@example.com")

        # The current action frame depends only on A; B is not in its declared read-set.
        current_a = self.rt.compile_recall(
            "d",
            "alice",
            [RecallRole("action", self.region_a, "ACTION")],
            20,
        )
        self.assertFalse(
            any(
                dep.dep_class == "representation" and dep.dep_key == self.rep_b_old
                for dep in current_a.dependencies
            ),
            "E0 requires B to be absent from the current forward dependency manifest",
        )

        # B changes after the consumer retained the old value. This does not mutate A.
        self.rt.invalidate_representation("d", self.rep_b_old, principal="alice")
        self.rep_b_new = self.rt.add_representation(
            "d",
            self.region_b,
            kind="exact",
            payload={"recipient": "new@example.com"},
            loss={"recipient": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=5,
            principal="alice",
        )

        # The exact emitted consequence still contains the old B-derived value.
        payload = {"to": stale_recipient, "body": "status"}

        # Desired strong-use semantics: the stale material premise must be caught at the
        # consequence boundary even though the forward frame itself is still current.
        with self.assertRaises(MemoryDependencyStale):
            fence = self.rt.issue_use_fence(
                current_a,
                principal="alice",
                sink="tool:send",
                payload=payload,
            )
            self.rt.consume_use_fence(
                fence.fence_id,
                principal="alice",
                sink="tool:send",
                payload=payload,
            )


if __name__ == "__main__":
    unittest.main()
