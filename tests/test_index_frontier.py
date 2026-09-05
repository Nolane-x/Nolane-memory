import tempfile
import unittest

from nolane_memory import LossState, MemoryRuntime
from nolane_memory.errors import MemoryQueryCapabilityUnsupported


class IndexFrontierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")
        self.rt.register_query_family("X", {"x"})
        self.region = self.rt.create_region("d", "r", principal="alice")
        self.rep = self.rt.add_representation(
            "d", self.region, kind="fact", payload={"x": 1},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.index_representation_view("d", self.rep, "lexical", ["one"])

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_indexed_row_max_sequence_does_not_imply_contiguous_frontier(self):
        head = self.rt.head("d")
        status = self.rt.get_index_frontier("d", "lexical")
        self.assertEqual(status["frontier_sequence"], 0)
        self.assertGreater(head.sequence, 0)

    def test_exact_discovery_refuses_cut_above_declared_frontier(self):
        cut = self.rt.head("d")
        with self.assertRaises(MemoryQueryCapabilityUnsupported):
            self.rt.discover_regions_at_cut(
                "d", principal="alice", view_keys={"lexical": ["one"]}, cut=cut, require_exact=True
            )
        self.rt.advance_index_frontier("d", "lexical", through_sequence=cut.sequence, mode="EXACT")
        self.assertEqual(
            self.rt.discover_regions_at_cut(
                "d", principal="alice", view_keys={"lexical": ["one"]}, cut=cut, require_exact=True
            ),
            [self.region],
        )

    def test_approximate_index_cannot_serve_exact_hard_route_even_when_frontier_is_current(self):
        cut = self.rt.head("d")
        self.rt.advance_index_frontier("d", "lexical", through_sequence=cut.sequence, mode="APPROXIMATE")
        with self.assertRaises(MemoryQueryCapabilityUnsupported):
            self.rt.discover_regions_at_cut(
                "d", principal="alice", view_keys={"lexical": ["one"]}, cut=cut, require_exact=True
            )
        self.assertEqual(
            self.rt.discover_regions_at_cut(
                "d", principal="alice", view_keys={"lexical": ["one"]}, cut=cut, require_exact=False
            ),
            [self.region],
        )

    def test_cut_query_does_not_leak_representation_created_after_cut(self):
        old_cut = self.rt.head("d")
        later_region = self.rt.create_region("d", "later", principal="alice")
        later_rep = self.rt.add_representation(
            "d", later_region, kind="fact", payload={"x": 2},
            loss={"x": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1, principal="alice",
        )
        self.rt.index_representation_view("d", later_rep, "lexical", ["later"])
        self.rt.advance_index_frontier("d", "lexical", through_sequence=self.rt.head("d").sequence, mode="EXACT")
        self.assertEqual(
            self.rt.discover_regions_at_cut(
                "d", principal="alice", view_keys={"lexical": ["later"]}, cut=old_cut, require_exact=True
            ),
            [],
        )


if __name__ == "__main__": unittest.main()
