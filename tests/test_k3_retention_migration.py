import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import Answerability, LossState
from nolane_memory.errors import MemoryRetentionBlocked


class K3RetentionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.rt.register_query_family("EXACT", {"exact_number"})
        self.region = self.rt.create_region("d", "r", principal="alice")
        self.rt.protect_region_obligation("d", self.region, "EXACT", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_redundant_witness_can_be_deleted_safely(self):
        a = self.rt.add_representation("d", self.region, kind="exact-a", payload={"exact_number": 1},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
        b = self.rt.add_representation("d", self.region, kind="exact-b", payload={"exact_number": 1},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=9, principal="alice")
        decision = self.rt.consider_delete_representation("d", a, principal="alice")
        self.assertEqual(decision.status, "SAFE_DELETE")
        self.assertEqual(decision.uncovered_families, [])
        self.assertEqual(self.rt.answerability(b, "EXACT"), Answerability.EXACT)
        row = self.rt.db.execute("SELECT invalidated_seq FROM representations WHERE representation_id=?", (a,)).fetchone()
        self.assertIsNotNone(row[0])

    def test_last_witness_deletion_is_blocked_without_policy_override(self):
        only = self.rt.add_representation("d", self.region, kind="exact", payload={"exact_number": 1},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
        with self.assertRaises(MemoryRetentionBlocked):
            self.rt.consider_delete_representation("d", only, principal="alice")
        self.assertEqual(self.rt.answerability(only, "EXACT"), Answerability.EXACT)

    def test_policy_override_records_irrecoverable_gap_debt(self):
        only = self.rt.add_representation("d", self.region, kind="exact", payload={"exact_number": 1},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
        decision = self.rt.consider_delete_representation(
            "d", only, principal="alice", allow_irreversible=True, policy_ref="privacy-delete-7")
        self.assertEqual(decision.status, "IRREVERSIBLE_GAP")
        self.assertEqual(decision.uncovered_families, ["EXACT"])
        self.assertIsNotNone(decision.debt_id)
        debt = self.rt.get_semantic_debt(decision.debt_id)
        self.assertEqual(debt.kind, "SOURCE_RECOVERABILITY_LOST")
        self.assertEqual(self.rt.answerability(only, "EXACT"), Answerability.UNSUPPORTED)

    def test_legacy_import_with_unknown_provenance_does_not_invent_exactness(self):
        rep = self.rt.import_legacy_representation(
            "d", self.region, source_kind="legacy-summary", source_id="old:42",
            payload={"text": "about one hundred"}, dimensions={"exact_number", "negation"},
            principal="alice")
        row = self.rt.db.execute("SELECT loss_json,transform_kind FROM representations WHERE representation_id=?", (rep,)).fetchone()
        self.assertIn('"exact_number":"UNKNOWN"', row[0])
        self.assertEqual(row[1], "LEGACY_UNKNOWN_TRANSFORM")
        debts = self.rt.list_open_semantic_debts("d", subject_id=rep)
        self.assertEqual(len(debts), 1)
        self.assertEqual(debts[0].kind, "MISSING_LEGACY_PROVENANCE")

    def test_probe_checkpoint_captures_normalized_runtime_state(self):
        self.rt.add_representation("d", self.region, kind="exact", payload={"exact_number": 1},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=10, principal="alice")
        cp = self.rt.capture_probe_checkpoint("d", "after-one-rep")
        self.assertEqual(cp.label, "after-one-rep")
        self.assertEqual(cp.cut.sequence, self.rt.head("d").sequence)
        self.assertEqual(cp.vector["current_representations"], 1)
        self.assertIn("open_debts", cp.vector)


if __name__ == "__main__": unittest.main()
