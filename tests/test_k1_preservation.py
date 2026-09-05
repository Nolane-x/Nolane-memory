import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import Answerability, LossState
from nolane_memory.errors import MemoryTransitionIncomplete


class K1PreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.region = self.rt.create_region("d", "r-procedure", principal="alice")
        self.rt.register_query_family("PROCEDURE_APPLICABILITY", {"precondition", "regime"})
        self.rt.register_query_family("EXACT_VALUE", {"exact_number"})

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_answerability_exact_rehydratable_unsupported(self):
        raw = self.rt.add_representation(
            "d", self.region, kind="raw", payload={"precondition": "safe", "regime": "linux", "n": 97.36},
            loss={"precondition": LossState.PRESERVED_EXACT, "regime": LossState.PRESERVED_EXACT, "exact_number": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=200, principal="alice",
        )
        summary = self.rt.add_representation(
            "d", self.region, kind="summary", payload={"text": "works on linux around 100"}, source_representation_ids=[raw],
            loss={"precondition": LossState.PRESERVED_EXACT, "regime": LossState.PRESERVED_EXACT, "exact_number": LossState.LOST},
            recoverable={"exact_number"}, token_cost=20, principal="alice",
        )
        self.assertEqual(self.rt.answerability(summary, "PROCEDURE_APPLICABILITY"), Answerability.EXACT)
        self.assertEqual(self.rt.answerability(summary, "EXACT_VALUE"), Answerability.REHYDRATABLE)

        no_source = self.rt.add_representation(
            "d", self.region, kind="detached", payload={},
            loss={"exact_number": LossState.LOST}, recoverable=set(), token_cost=5, principal="alice",
        )
        self.assertEqual(self.rt.answerability(no_source, "EXACT_VALUE"), Answerability.UNSUPPORTED)

    def test_pure_transform_cannot_self_recover_lost_dimension(self):
        base = self.rt.add_representation(
            "d", self.region, kind="summary", payload={},
            loss={"exact_number": LossState.LOST}, recoverable=set(), token_cost=10, principal="alice",
        )
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.add_representation(
                "d", self.region, kind="summary2", payload={"n": 97.36}, source_representation_ids=[base],
                transform_kind="PURE", loss={"exact_number": LossState.PRESERVED_EXACT},
                recoverable=set(), token_cost=10, principal="alice",
            )
        restored = self.rt.add_representation(
            "d", self.region, kind="rebase", payload={"n": 97.36}, source_representation_ids=[base],
            transform_kind="SOURCE_REBASE", loss={"exact_number": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=50, principal="alice",
        )
        self.assertEqual(self.rt.answerability(restored, "EXACT_VALUE"), Answerability.EXACT)


if __name__ == "__main__": unittest.main()

class K1RecoverabilityGroundingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d", writer_epoch=1)
        self.region = self.rt.create_region("d", "r", principal="alice")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_rehydratable_claim_requires_actual_source_witness(self):
        with self.assertRaises(MemoryTransitionIncomplete):
            self.rt.add_representation(
                "d", self.region, kind="orphan-summary", payload={"text": "about 100"},
                loss={"exact_number": LossState.LOST}, recoverable={"exact_number"},
                token_cost=5, principal="alice",
            )

    def test_one_preserving_source_can_legitimately_carry_dimension_through_multi_source_transform(self):
        exact = self.rt.add_representation(
            "d", self.region, kind="exact", payload={"n": 7},
            loss={"exact_number": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=5, principal="alice")
        lost = self.rt.add_representation(
            "d", self.region, kind="lossy", payload={},
            loss={"exact_number": LossState.LOST}, recoverable=set(), token_cost=5, principal="alice")
        out = self.rt.add_representation(
            "d", self.region, kind="combined", payload={"n": 7}, source_representation_ids=[lost, exact],
            transform_kind="PURE", loss={"exact_number": LossState.PRESERVED_EXACT},
            recoverable=set(), token_cost=5, principal="alice")
        self.assertIsInstance(out, str)
