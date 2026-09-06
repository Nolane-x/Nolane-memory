import tempfile
import unittest
from dataclasses import replace

from nolane_memory import GroundingCompleteness, MemoryRuntime
from nolane_memory.errors import (
    ActionArgumentMismatch,
    MemoryDependencyStale,
    MemoryGroundingIncomplete,
    MemoryIntegrityError,
)
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

    def _ground_recipient(self, frame):
        return self.rt.ground_consequence_atom(
            frame,
            role_id="recipient",
            source_field="recipient",
            atom_path="/to",
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

        # Frozen rc4 control: the ordinary forward-only fence accepts because B is
        # outside current_a.dependencies. This keeps the discriminating counterexample.
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
        grounding = self._ground_recipient(earlier_b)
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

    def test_grounded_dependency_mutation_after_issue_is_caught_at_consume(self):
        earlier_b = self._earlier_recipient_frame()
        stale_recipient = earlier_b.fragments[0].payload["recipient"]
        grounding = self._ground_recipient(earlier_b)
        current_a = self._current_action_frame()
        payload = {"to": stale_recipient, "body": "status"}

        fence = self.rt.issue_use_fence(
            current_a,
            principal="alice",
            sink="tool:send",
            payload=payload,
            consequence_groundings=[grounding],
            required_grounding_paths={"/to"},
        )
        self._supersede_recipient()

        with self.assertRaises(MemoryDependencyStale):
            self.rt.consume_use_fence(
                fence.fence_id,
                principal="alice",
                sink="tool:send",
                payload=payload,
            )

    def test_unrelated_mutation_does_not_invalidate_grounded_fence(self):
        self.rt.register_query_family("UNRELATED", {"value"})
        region_c = self.rt.create_region("d", "unrelated", principal="alice")
        rep_c = self.rt.add_representation(
            "d",
            region_c,
            kind="exact",
            payload={"value": "c0"},
            loss={"value": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=3,
            principal="alice",
        )
        earlier_b = self._earlier_recipient_frame()
        grounding = self._ground_recipient(earlier_b)
        current_a = self._current_action_frame()
        payload = {"to": "old@example.com", "body": "status"}
        fence = self.rt.issue_use_fence(
            current_a,
            principal="alice",
            sink="tool:send",
            payload=payload,
            consequence_groundings=[grounding],
            required_grounding_paths={"/to"},
        )

        self.rt.invalidate_representation("d", rep_c, principal="alice")
        self.assertTrue(
            self.rt.consume_use_fence(
                fence.fence_id,
                principal="alice",
                sink="tool:send",
                payload=payload,
            )
        )

    def test_payload_atom_must_equal_persisted_grounded_value(self):
        earlier_b = self._earlier_recipient_frame()
        grounding = self._ground_recipient(earlier_b)
        current_a = self._current_action_frame()
        payload = {"to": "tampered@example.com", "body": "status"}

        with self.assertRaises(ActionArgumentMismatch):
            self.rt.issue_use_fence(
                current_a,
                principal="alice",
                sink="tool:send",
                payload=payload,
                consequence_groundings=[grounding],
                required_grounding_paths={"/to"},
            )

    def test_required_grounding_path_fails_closed_when_missing(self):
        current_a = self._current_action_frame()
        with self.assertRaises(MemoryGroundingIncomplete):
            self.rt.issue_use_fence(
                current_a,
                principal="alice",
                sink="tool:send",
                payload={"to": "old@example.com", "body": "status"},
                consequence_groundings=[],
                required_grounding_paths={"/to"},
            )

    def test_model_proposed_grounding_cannot_self_upgrade_to_strong_use(self):
        earlier_b = self._earlier_recipient_frame()
        grounding = replace(
            self._ground_recipient(earlier_b),
            completeness=GroundingCompleteness.MODEL_PROPOSED.value,
        )
        current_a = self._current_action_frame()
        with self.assertRaises(MemoryGroundingIncomplete):
            self.rt.issue_use_fence(
                current_a,
                principal="alice",
                sink="tool:send",
                payload={"to": "old@example.com", "body": "status"},
                consequence_groundings=[grounding],
                required_grounding_paths={"/to"},
            )

    def test_forged_role_representation_binding_is_rejected(self):
        earlier_b = self._earlier_recipient_frame()
        forged = replace(
            self._ground_recipient(earlier_b),
            source_representation_id=self.rep_a,
        )
        current_a = self._current_action_frame()
        with self.assertRaises(MemoryIntegrityError):
            self.rt.issue_use_fence(
                current_a,
                principal="alice",
                sink="tool:send",
                payload={"to": "old@example.com", "body": "status"},
                consequence_groundings=[forged],
                required_grounding_paths={"/to"},
            )


if __name__ == "__main__":
    unittest.main()
