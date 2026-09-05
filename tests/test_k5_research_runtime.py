import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryRecallAmbiguous, MemoryRecallInsufficient
from nolane_memory.types import EffectTier, LossState, RecallRole


class K5ResearchRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("EXACT", {"x"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _rep(self, key, value, *, allowed=None, token=2):
        r = self.rt.create_region("d", key, principal="alice", allowed_principals=allowed)
        rep = self.rt.add_representation("d", r, kind="structured", payload={"x": value},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=token,
            principal="alice", allowed_principals=allowed)
        return r, rep

    def test_multiple_discovery_views_union_regions_without_private_hidden_influence(self):
        r1, a = self._rep("a", 1)
        r2, b = self._rep("b", 2)
        r3, c = self._rep("private", 3, allowed=["bob"])
        self.rt.index_representation_view("d", a, "temporal", ["today"])
        self.rt.index_representation_view("d", b, "causal", ["deploy-failure"])
        self.rt.index_representation_view("d", c, "objective", ["secret-goal"])
        regions = self.rt.discover_regions("d", principal="alice", view_keys={
            "temporal": ["today"], "causal": ["deploy-failure"], "objective": ["secret-goal"]})
        self.assertEqual(regions, [r1, r2])

    def test_degraded_source_hydration_downgrades_instead_of_silent_approximation(self):
        region = self.rt.create_region("d", "rehydrate", principal="alice")
        raw = self.rt.add_representation("d", region, kind="raw", payload={"x": 97.36},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=20, principal="alice")
        self.rt.add_representation("d", region, kind="summary", payload={"text": "about 100"},
            source_representation_ids=[raw], loss={"x": LossState.LOST}, recoverable={"x"}, token_cost=2, principal="alice")
        role = RecallRole("x", region, "EXACT", True)
        self.rt.set_capability_availability("d", "source_hydration", False)
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_recall("d", "alice", [role], 50)
        self.rt.set_capability_availability("d", "source_hydration", True)
        frame = self.rt.compile_recall("d", "alice", [role], 50)
        self.assertEqual(frame.fragments[0].representation_id, raw)

    def test_degraded_effect_ledger_disables_learned_inhibition(self):
        r1, rep = self._rep("optional", 1)
        frame = self.rt.compile_recall("d", "alice", [RecallRole("opt", r1, "EXACT", False)], 10)
        self.rt.record_effect_evidence("d", [rep], consumer="m", task="t", regime="r", rendering="n",
            outcome_dimension="accuracy", tier=EffectTier.E4, effect=-1, confidence=1)
        self.rt.set_capability_availability("d", "effect_ledger", False)
        guarded, receipt = self.rt.apply_interference_guard(frame, consumer="m", task="t", regime="r", rendering="n")
        self.assertEqual(len(guarded.fragments), 1)
        self.assertEqual(receipt.decision, "DEGRADED_EFFECT_LEDGER_UNAVAILABLE")

    def test_active_reconstruction_surfaces_decision_distinct_ambiguity(self):
        region = self.rt.create_region("d", "ambiguous", principal="alice")
        self.rt.add_representation("d", region, kind="exact-a", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
        self.rt.add_representation("d", region, kind="exact-b", payload={"x": 2},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
        with self.assertRaises(MemoryRecallAmbiguous):
            self.rt.active_reconstruct("d", principal="alice", role=RecallRole("x", region, "EXACT"), token_budget=20)

    def test_formal_lab_and_lifelong_fuzz_are_reproducible_and_green(self):
        lab = self.rt.run_preservation_lab()
        self.assertEqual(lab.failed, 0)
        self.assertGreaterEqual(lab.cases, 200)
        fuzz1 = self.rt.run_lifelong_fuzz(seed=73, cases=5000)
        fuzz2 = self.rt.run_lifelong_fuzz(seed=73, cases=5000)
        self.assertEqual(fuzz1.failed, 0)
        self.assertEqual(fuzz1.details, fuzz2.details)

    def test_k5_profile_exposes_benchmarks_ablations_and_preserves_research_debt(self):
        portfolio = self.rt.benchmark_ablation_portfolio()
        self.assertIn("no_persistent_memory", portfolio["baselines"])
        self.assertIn("long_context", portfolio["baselines"])
        self.assertIn("preservation_envelope_x_source_rehydration", portfolio["ablations"])
        status = self.rt.k5_profile_status()
        self.assertTrue(status["executable_support"]["K5"])
        self.assertEqual(status["research_closure"], "BLOCKED")
        self.assertIn("external-validity", status["residual_debts"])
        self.assertFalse(status["independent_validation_claimed"])

    def test_conformance_vector_normalizes_internal_ids(self):
        other_tmp = tempfile.TemporaryDirectory()
        other = MemoryRuntime(f"{other_tmp.name}/other.db")
        try:
            other.create_domain("d", writer_epoch=1)
            other.register_query_family("EXACT", {"x"})
            for rt in (self.rt, other):
                region = rt.create_region("d", "same", principal="alice")
                rt.add_representation("d", region, kind="structured", payload={"x": 4},
                    loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2, principal="alice")
            self.assertEqual(self.rt.conformance_vector("d"), other.conformance_vector("d"))
            self.assertTrue(self.rt.differential_conformance(other, "d")["equivalent"])
        finally:
            other.close(); other_tmp.cleanup()


if __name__ == "__main__": unittest.main()
