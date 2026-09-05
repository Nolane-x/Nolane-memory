import tempfile
import unittest

from nolane_memory import EffectTier, LossState, MemoryRuntime, RecallRole
from nolane_memory.errors import MemoryTransitionIncomplete


class EffectExposureChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})
        self.region = self.rt.create_region("d", "r", principal="alice")
        self.a = self.rt.add_representation("d", self.region, kind="a", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice")
        self.b = self.rt.add_representation("d", self.region, kind="b", payload={"x": 1}, loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
        self.frame = self.rt.compile_recall("d", "alice", [RecallRole("x", self.region, "X")], 10)

    def tearDown(self): self.rt.close(); self.tmp.cleanup()

    def test_exposure_preserves_stage_order_and_lineage(self):
        exposure = self.rt.record_memory_exposure(
            "d", frame_id=self.frame.frame_id, consumer="model-v1", task="deploy", regime="prod", rendering="json",
            candidate_representation_ids=[self.b, self.a, self.b], selected_representation_ids=[self.a],
            rendered_representation_ids=[self.a], referenced_representation_ids=[self.a],
        )
        self.assertEqual(exposure.candidate_representation_ids, [self.b, self.a])
        self.assertEqual(exposure.selected_representation_ids, [self.a])
        self.assertEqual(exposure.rendered_representation_ids, [self.a])
        self.assertEqual(exposure.referenced_representation_ids, [self.a])

    def test_stage_chain_cannot_reference_memory_that_was_not_available_upstream(self):
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.record_memory_exposure(
                "d", frame_id=self.frame.frame_id, consumer="m", task="t", regime="r", rendering="text",
                candidate_representation_ids=[self.a], selected_representation_ids=[self.b],
                rendered_representation_ids=[self.b], referenced_representation_ids=[],
            )

    def test_effect_evidence_binds_matching_exposure_scope_and_rendered_set(self):
        exposure = self.rt.record_memory_exposure(
            "d", frame_id=self.frame.frame_id, consumer="model-v1", task="deploy", regime="prod", rendering="json",
            candidate_representation_ids=[self.a, self.b], selected_representation_ids=[self.a],
            rendered_representation_ids=[self.a], referenced_representation_ids=[],
        )
        effect = self.rt.record_effect_evidence(
            "d", [self.a], consumer="model-v1", task="deploy", regime="prod", rendering="json",
            outcome_dimension="success", tier=EffectTier.E3, effect=-0.4, confidence=0.9,
            exposure_id=exposure.exposure_id,
        )
        self.assertEqual(effect.exposure_id, exposure.exposure_id)
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.record_effect_evidence(
                "d", [self.a], consumer="other-model", task="deploy", regime="prod", rendering="json",
                outcome_dimension="success", tier=EffectTier.E3, effect=-0.4, confidence=0.9,
                exposure_id=exposure.exposure_id,
            )


if __name__ == "__main__": unittest.main()
