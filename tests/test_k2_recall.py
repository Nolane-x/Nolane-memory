import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import LossState, RecallRole
from nolane_memory.errors import MemoryViewOverflow


class K2RecallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("EXACT_VALUE", {"exact_number"})
        self.rt.register_query_family("PREF", {"polarity"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_recall_page_faults_to_stronger_representation(self):
        region = self.rt.create_region("d", "r1", principal="alice")
        raw = self.rt.add_representation(
            "d", region, kind="raw", payload={"exact_number": 97.36},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=40, principal="alice")
        self.rt.add_representation(
            "d", region, kind="summary", payload={"text": "roughly 100"}, source_representation_ids=[raw],
            loss={"exact_number": LossState.LOST}, recoverable={"exact_number"}, token_cost=5, principal="alice")
        frame = self.rt.compile_recall(
            domain_id="d", principal="alice", roles=[RecallRole("need-exact", region, "EXACT_VALUE")], token_budget=50)
        self.assertEqual(frame.sufficiency, "SUFFICIENT")
        self.assertTrue(frame.fragments[0].page_faulted)
        self.assertEqual(frame.fragments[0].representation_id, raw)

    def test_hard_roles_over_budget_overflow_instead_of_truncation(self):
        roles = []
        for i in range(3):
            region = self.rt.create_region("d", f"r{i}", principal="alice")
            self.rt.add_representation(
                "d", region, kind="exact", payload={"polarity": "yes"},
                loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
            roles.append(RecallRole(f"role-{i}", region, "PREF"))
        with self.assertRaises(MemoryViewOverflow):
            self.rt.compile_recall(domain_id="d", principal="alice", roles=roles, token_budget=20)

    def test_private_representation_has_zero_candidate_influence(self):
        region = self.rt.create_region("d", "private-region", principal="alice", allowed_principals=["alice"])
        self.rt.add_representation(
            "d", region, kind="exact", payload={"polarity": "yes"},
            loss={"polarity": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5,
            principal="alice", allowed_principals=["alice"])
        frame = self.rt.compile_recall(
            domain_id="d", principal="bob", roles=[RecallRole("pref", region, "PREF", hard=False)], token_budget=20)
        self.assertEqual(frame.fragments, [])
        self.assertEqual(frame.sufficiency, "SUFFICIENT")


if __name__ == "__main__": unittest.main()
