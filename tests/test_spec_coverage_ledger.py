import tempfile
import unittest
from pathlib import Path

from nolane_memory.spec_coverage import build_spec_coverage_ledger


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'docs' / 'NOLANE-MEMORY-V0.6.3-SPEC.md'


class SpecCoverageLedgerTests(unittest.TestCase):
    def test_ledger_is_one_to_one_for_all_402_numbered_sections(self):
        ledger = build_spec_coverage_ledger(SPEC, ROOT)
        self.assertEqual(ledger['section_count'], 402)
        self.assertEqual([x['section'] for x in ledger['sections']], list(range(1, 403)))
        self.assertEqual(ledger['duplicate_sections'], [])
        self.assertEqual(ledger['missing_section_numbers'], [])

    def test_every_implementation_testable_section_has_executable_traceability(self):
        ledger = build_spec_coverage_ledger(SPEC, ROOT)
        self.assertEqual(ledger['implementation_missing'], [], ledger['implementation_missing'])
        self.assertEqual(ledger['implementation_partial'], [], ledger['implementation_partial'])
        impl = [x for x in ledger['sections'] if x['classification'] == 'IMPLEMENTATION_TESTABLE']
        self.assertGreater(len(impl), 180)
        for row in impl:
            self.assertEqual(row['status'], 'COMPLETE', row)
            ev = row['evidence']
            self.assertTrue(ev['code_paths'], row)
            self.assertTrue(ev['test_paths'], row)
            self.assertTrue(ev['methods'], row)

    def test_external_and_reference_boundaries_are_not_self_certified(self):
        ledger = build_spec_coverage_ledger(SPEC, ROOT)
        by = {x['section']: x for x in ledger['sections']}
        self.assertEqual(by[305]['classification'], 'RESEARCH_EXTERNAL')
        self.assertEqual(by[305]['status'], 'EXTERNAL')
        self.assertEqual(by[399]['classification'], 'RESEARCH_EXTERNAL')
        self.assertEqual(by[399]['status'], 'EXTERNAL')
        self.assertEqual(by[402]['classification'], 'REFERENCE_NARRATIVE')
        self.assertEqual(by[402]['status'], 'REFERENCE')
        self.assertGreater(ledger['external_count'], 10)

    def test_recent_normative_sections_have_direct_campaign_evidence(self):
        ledger = build_spec_coverage_ledger(SPEC, ROOT)
        by = {x['section']: x for x in ledger['sections']}
        self.assertIn('run_temporal_acceptance_campaign', by[263]['evidence']['methods'])
        self.assertIn('run_recovery_privacy_acceptance_campaign', by[373]['evidence']['methods'])
        self.assertIn('run_use_time_causal_cut_calculus', by[396]['evidence']['methods'])
        self.assertIn('run_use_time_race_campaign', by[401]['evidence']['methods'])
        self.assertIn('run_full_spec_release_gate', by[331]['evidence']['methods'])


if __name__ == '__main__':
    unittest.main()
