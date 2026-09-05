import inspect
import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.independent_kernel import IndependentSemanticKernel


class MutantKernel(IndependentSemanticKernel):
    def answerability(self, representation_name, family_id):
        return "EXACT"


class IndependentDifferentialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_second_kernel_does_not_import_or_delegate_to_primary_runtime(self):
        source = inspect.getsource(IndependentSemanticKernel)
        self.assertNotIn("MemoryRuntime", source)
        self.assertNotIn(".runtime", source)
        self.assertNotIn("sqlite", source.lower())

    def test_frozen_and_generated_differential_corpus_match(self):
        report = self.rt.run_independent_differential(seed=73, cases=128)
        self.assertEqual(report.failed, 0)
        self.assertGreater(report.passed, 128)
        self.assertEqual(report.details["implementation"], "pure-python-independent-kernel")
        self.assertGreater(report.details["frozen_steps"], 0)
        self.assertEqual(report.details["classification_counts"].get("implementation_bug", 0), 0)

    def test_deliberate_semantic_mutant_is_detected_and_classified(self):
        report = self.rt.run_independent_differential(seed=73, cases=16, kernel_factory=MutantKernel)
        self.assertGreater(report.failed, 0)
        self.assertGreater(report.details["classification_counts"]["implementation_bug"], 0)
        self.assertFalse(report.details["equivalent"])


if __name__ == "__main__": unittest.main()
