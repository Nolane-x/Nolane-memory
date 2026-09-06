import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale
from nolane_memory.types import LossState, RecallRole


class SemanticReadSetClosureTests(unittest.TestCase):
    """E0 control + E1 structured-grounding treatment for the v0.7 SRSC seam."""

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

    def _earlier_recipient_frame(self):
        return self.rt.compile_recall(
            "d",
            "alice",
            [RecallRole("recipient", self.region_b, "RECIPIENT")],
            20,
        )

    def _current_action_frame(self):
        return self.rt.compile_recall(
            "d",
            "alice",
            [RecallRole("action", self.region_a, "ACTION")],
            20,
        )

    def _supersede_recipient(self):
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

    def test_e0_control_unbound_hidden_dependency_is_accepted_by_v063_fence(self):
        earlier_b = self._earlier_recipient_frame()
        stale_recipient = earlier_b.fragments[0].payload["recipient"]
        current_a = self._current_action_frame()
        self.assertFalse(
            any(
                dep.dep_class == "representation" and dep.dep_key == self.rep_b_old
                for dep in current_a.dependencies
            ),
            "E0 requires B to be absent from the current forward dependency manifest",
        )

        self._supersede_recipient()
        payload = {"to": stale_recipient, "body": "status"}

        # This is the frozen rc4 control reproduced by CI at c4ea736f: the ordinary
        # forward-only fence accepts because B is outside current_a.dependencies.
        fence = self.rt.issue_use_fence(
            current_a,
            principal="alice",
            sink="tool:send",
            payload=payload,
        )
        self.assertTrue(
            self.rt.consume_use_fence(
                fence.fence_id,
                principal="alice",
                sink="tool:send",
                payload=payload,
            )
        )

    def test_e1_structured_grounding_binds_prior_memory_atom_and_blocks_stale_source(self):
        earlier_b = self._earlier_recipient_frame()
        stale_recipient = earlier_b.fragments[0].payload["recipient"]

        # G3 candidate: a deterministic host projection binds the outgoing /to atom to
        # the exact earlier memory fragment that supplied its value. The model does not
        # self-declare the dependency.
        grounding = self.rt.ground_consequence_atom(
            earlier_b,
            role_id="recipient",
            source_field="recipient",
            atom_path="/to",
        )
        current_a = self._current_action_frame()
        self._supersede_recipient()
        payload = {"to": stale_recipient, "body": "status"}

        with self.assertRaises(MemoryDependencyStale):
            self.rt.issue_use_fence(
                current_a,
                principal="alice",
                sink="tool:send",
                payload=payload,
                consequence_groundings=[grounding],
                required_grounding_paths={"/to"},
            )


if __name__ == "__main__":
    unittest.main()
