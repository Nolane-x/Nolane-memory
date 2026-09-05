import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryRecallInsufficient
from nolane_memory.types import LossState, RecallBoundaryDescriptor, RecallRole


class ApplicabilityUseSiteContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _rep(self, label, applicability):
        region = self.rt.create_region("d", label, principal="alice")
        rep = self.rt.add_representation(
            "d", region, kind="structured", payload={"x": label},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
            principal="alice", applicability=applicability,
        )
        return region, rep

    def _boundary(self, region, profile, critical):
        return RecallBoundaryDescriptor(
            task="use", principal="alice", explicit_roles=[RecallRole("x", region, "X")],
            token_budget=10, compatibility_profile=profile, safety_critical_dimensions=set(critical),
        )

    def test_exact_match_and_explicit_wildcard_are_usable(self):
        exact_region, _ = self._rep("exact", {"environment_revision": "linux", "self_version": "model-A"})
        wildcard_region, _ = self._rep("wild", {"environment_revision": "*", "self_version": "model-A"})
        profile = {"environment_revision": "linux", "self_version": "model-A"}
        for region in (exact_region, wildcard_region):
            frame, _ = self.rt.compile_boundary_recall(
                "d", self._boundary(region, profile, {"environment_revision", "self_version"})
            )
            self.assertEqual(frame.sufficiency, "SUFFICIENT")

    def test_revisioned_refinement_policy_allows_declared_model_family(self):
        region, _ = self._rep("family", {"self_version": "model-family-X"})
        self.rt.register_applicability_compatibility_profile(
            revision=1,
            refinements=[{"dimension": "self_version", "declared": "model-family-X", "requested": "model-X-v2"}],
        )
        frame, _ = self.rt.compile_boundary_recall(
            "d", self._boundary(region, {"self_version": "model-X-v2"}, {"self_version"})
        )
        self.assertEqual(frame.sufficiency, "SUFFICIENT")

    def test_missing_safety_critical_dimension_and_conflicting_regime_fail_closed(self):
        missing_region, _ = self._rep("missing", {"environment_revision": "linux"})
        conflict_region, _ = self._rep("conflict", {"environment_revision": "windows", "self_version": "model-A"})
        profile = {"environment_revision": "linux", "self_version": "model-A"}
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_boundary_recall(
                "d", self._boundary(missing_region, profile, {"environment_revision", "self_version"})
            )
        with self.assertRaises(MemoryRecallInsufficient):
            self.rt.compile_boundary_recall(
                "d", self._boundary(conflict_region, profile, {"environment_revision", "self_version"})
            )

    def test_foreign_high_similarity_candidate_is_filtered_before_discovery_influence(self):
        foreign_region, foreign_rep = self._rep(
            "foreign", {"environment_revision": "windows", "self_version": "model-A"}
        )
        local_region, local_rep = self._rep(
            "local", {"environment_revision": "linux", "self_version": "model-A"}
        )
        for rep in (foreign_rep, local_rep):
            self.rt.index_representation_view("d", rep, "lexical", ["identical-high-score"])
        self.rt.advance_index_frontier("d", "lexical", through_sequence=self.rt.head("d").sequence, mode="EXACT")
        found = self.rt.discover_regions_at_cut(
            "d", principal="alice", view_keys={"lexical": ["identical-high-score"]}, cut=self.rt.head("d"), require_exact=True,
            compatibility_profile={"environment_revision": "linux", "self_version": "model-A"},
            safety_critical_dimensions={"environment_revision", "self_version"},
        )
        self.assertEqual(found, [local_region])
        self.assertNotIn(foreign_region, found)


if __name__ == "__main__":
    unittest.main()
