import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import EffectTier, LossState, RecallRole


class K4EffectsProspectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("PREF", {"polarity"})
        self.r1 = self.rt.create_region("d", "r1", principal="alice")
        self.r2 = self.rt.create_region("d", "r2", principal="alice")
        self.hard_rep = self.rt.add_representation(
            "d", self.r1, kind="exact", payload={"polarity": "yes"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
        self.optional_rep = self.rt.add_representation(
            "d", self.r2, kind="exact", payload={"polarity": "no"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _frame(self):
        return self.rt.compile_recall("d", "alice", [
            RecallRole("hard", self.r1, "PREF", hard=True),
            RecallRole("optional", self.r2, "PREF", hard=False),
        ], 20)

    def test_observational_harm_cannot_veto_even_optional_memory(self):
        frame = self._frame()
        self.rt.record_effect_evidence(
            "d", [self.optional_rep], consumer="model-a", task="coding", regime="r1", rendering="narrative",
            outcome_dimension="accuracy", tier=EffectTier.E0, effect=-1.0, confidence=1.0)
        guarded, receipt = self.rt.apply_interference_guard(
            frame, consumer="model-a", task="coding", regime="r1", rendering="narrative")
        self.assertEqual({f.representation_id for f in guarded.fragments}, {self.hard_rep, self.optional_rep})
        self.assertEqual(receipt.inhibited_optional_representation_ids, [])

    def test_strong_scoped_harm_can_inhibit_optional_but_never_hard_role(self):
        frame = self._frame()
        self.rt.record_effect_evidence(
            "d", [self.optional_rep], consumer="model-a", task="coding", regime="r1", rendering="narrative",
            outcome_dimension="accuracy", tier=EffectTier.E4, effect=-0.8, confidence=0.95)
        self.rt.record_effect_evidence(
            "d", [self.hard_rep], consumer="model-a", task="coding", regime="r1", rendering="narrative",
            outcome_dimension="accuracy", tier=EffectTier.E4, effect=-0.9, confidence=0.99)
        guarded, receipt = self.rt.apply_interference_guard(
            frame, consumer="model-a", task="coding", regime="r1", rendering="narrative")
        self.assertEqual([f.representation_id for f in guarded.fragments], [self.hard_rep])
        self.assertEqual(receipt.inhibited_optional_representation_ids, [self.optional_rep])
        self.assertEqual(receipt.blocked_hard_role_ids, ["hard"])

        # No transfer to another consumer without evidence.
        other, other_receipt = self.rt.apply_interference_guard(
            frame, consumer="model-b", task="coding", regime="r1", rendering="narrative")
        self.assertEqual(len(other.fragments), 2)
        self.assertEqual(other_receipt.inhibited_optional_representation_ids, [])

    def test_prospective_trigger_adds_roles_not_actions_and_deduplicates(self):
        role = RecallRole("revalidate-pref", self.r1, "PREF", hard=True)
        self.rt.register_prospective_trigger("d", "sdk-changed", owner="alice", roles=[role, role])
        fired = self.rt.fire_prospective_triggers("d", "sdk-changed", principal="alice")
        self.assertEqual(fired, [role])
        self.assertFalse(hasattr(fired[0], "execute"))

    def test_self_version_change_does_not_reuse_old_effect_scope(self):
        old = self.rt.set_self_version("d", "model-a:v1", {"context": 32_000})
        self.rt.record_effect_evidence(
            "d", [self.optional_rep], consumer=old, task="coding", regime="r1", rendering="narrative",
            outcome_dimension="accuracy", tier=EffectTier.E4, effect=-0.7, confidence=0.99)
        new = self.rt.set_self_version("d", "model-a:v2", {"context": 64_000})
        frame = self._frame()
        guarded, receipt = self.rt.apply_interference_guard(
            frame, consumer=new, task="coding", regime="r1", rendering="narrative")
        self.assertEqual(len(guarded.fragments), 2)
        self.assertEqual(receipt.inhibited_optional_representation_ids, [])


if __name__ == "__main__": unittest.main()
