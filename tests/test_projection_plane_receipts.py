import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime, RecallObligation, RecallRole
from nolane_memory.errors import MemoryDependencyStale, MemoryRecallAmbiguous


class ProjectionPlaneReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("EXACT", {"x"})
        self.region = self.rt.create_region("d", "r", principal="alice")
        self.rep = self.rt.add_representation(
            "d", self.region, kind="source", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=2,
            principal="alice", transform_kind="SOURCE_REBASE", transform_profile="projection-source",
        )
        self.rt.index_representation_view("d", self.rep, "lexical", ["needle"])
        self.rt.advance_index_frontier("d", "lexical", through_sequence=self.rt.head("d").sequence, mode="EXACT")
        self.cut = self.rt.head("d")
        self.role = RecallRole("hard-x", self.region, "EXACT", True)

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_region_discovery_result_carries_reasons_and_frontier_receipts(self):
        result = self.rt.discover_regions_with_receipt(
            "d", principal="alice", view_keys={"lexical": ["needle"]}, cut=self.cut, require_exact=True,
        )
        self.assertEqual(result.candidate_region_ids, [self.region])
        self.assertIn("lexical:needle", result.reasons[self.region])
        self.assertEqual(result.frontier_receipts[0]["mode"], "EXACT")
        self.assertEqual(result.cut, self.cut)

    def test_representation_resolution_is_typed_and_binds_cut(self):
        resolution = self.rt.resolve_representation("d", principal="alice", role=self.role, cut=self.cut)
        self.assertEqual(resolution.selected_representation_id, self.rep)
        self.assertEqual(resolution.status, "DIRECT_EXACT")
        self.assertEqual(resolution.cut, self.cut)
        self.assertTrue(any(o["representation_id"] == self.rep for o in resolution.options))

    def test_reconstruction_surfaces_ambiguity_as_typed_result_before_raise(self):
        other = self.rt.add_representation(
            "d", self.region, kind="source", payload={"x": 2},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=3,
            principal="alice", transform_kind="SOURCE_REBASE", transform_profile="projection-source-2",
        )
        reconstruction = self.rt.reconstruct_role("d", principal="alice", role=self.role, cut=self.rt.head("d"))
        self.assertEqual(reconstruction.status, "AMBIGUOUS")
        self.assertEqual(set(reconstruction.candidate_representation_ids), {self.rep, other})
        with self.assertRaises(MemoryRecallAmbiguous):
            self.rt.active_reconstruct("d", principal="alice", role=self.role, token_budget=20)

    def test_sufficiency_assessment_and_dependency_manifest_are_derived_from_frame(self):
        frame = self.rt.compile_recall("d", "alice", [self.role], 20)
        obligation = RecallObligation(hard_roles=[self.role], optional_roles=[], closure_iterations=1)
        assessment = self.rt.assess_frame_sufficiency(frame, obligation)
        self.assertEqual(assessment.status, "SUFFICIENT")
        self.assertEqual(assessment.covered_hard_role_ids, ["hard-x"])
        manifest = self.rt.materialize_frame_dependency_manifest(frame)
        self.assertTrue(manifest.dependencies)
        self.assertTrue(self.rt.validate_frame_dependency_manifest(manifest.manifest_id))
        self.rt.invalidate_representation("d", self.rep, principal="alice")
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_frame_dependency_manifest(manifest.manifest_id)


if __name__ == "__main__": unittest.main()
