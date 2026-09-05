import tempfile
import unittest

from nolane_memory import MemoryRuntime


EXPECTED = {
    "MemoryAuthorityDomainRevision","MemoryWriterFenceRevision","MemoryWriteIntentRevision","MemoryCommitReceipt",
    "RetentionEventRevision","MemoryErasureClosureReceipt","ExperienceTraceRevision","MemoryOriginBindingReceipt",
    "MemoryIntegrityAuthorityProfileRevision","MemoryConfidentialityProfileRevision","MemoryDeclassificationReceipt",
    "MemoryPublicationPolicyRevision","MemoryPublicationReceipt","ClaimRevision","HistoricalJudgementRevision",
    "MemoryJustificationRevision","EvidenceIndependenceRevision","MemorySupportBundleRevision",
    "CounterexampleApplicabilityRevision","PrincipalMemoryAccessProfileRevision","MemoryRegimeRevision","SelfVersionProfileRevision",
    "SemanticRegionRevision","RepresentationRevision","TransformationContractRevision","SemanticLossVectorRevision",
    "PreservationEnvelopeRevision","RecoverabilityCertificateRevision","MemorySemanticDebtRevision",
    "MemoryQueryCounterexampleRevision","MemoryEffectEvidenceRevision","MemoryActivationGuardReceipt",
    "RecallBoundaryDescriptor","RecallObligation","RecallCutRevision","MemoryQueryDomainRevision",
    "QuerySnapshotCompletenessReceipt","NegativeRecallDependencyRevision","RegionDiscoveryResult","RepresentationResolution",
    "RecallReconstruction","RecallSufficiencyAssessment","RecallFrameDependencyManifestRevision","RecallFrameDescriptor",
    "FrameInformationFlowReceipt","MemoryUseFence","ContinuityPinRevision","RecoveryResumeAssessment",
}


class FullSpecOwnershipAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def test_manifest_covers_every_normative_closure_primitive(self):
        manifest = self.rt.full_spec_ownership_manifest()
        self.assertEqual(set(manifest), EXPECTED)
        self.assertTrue(all(v["status"] == "EXECUTABLE" for v in manifest.values()))
        self.assertTrue(all(v["mandatory_readers"] for v in manifest.values()))

    def test_clean_runtime_passes_dynamic_ownership_audit(self):
        audit = self.rt.audit_full_spec_ownership()
        self.assertTrue(audit["passed"], audit)
        self.assertEqual(audit["missing_primitives"], [])
        self.assertEqual(audit["missing_tables"], [])
        self.assertEqual(audit["missing_methods"], [])

    def test_missing_storage_surface_fails_audit(self):
        self.rt.db.execute("DROP TABLE frame_dependency_manifests")
        audit = self.rt.audit_full_spec_ownership()
        self.assertFalse(audit["passed"])
        self.assertIn("frame_dependency_manifests", audit["missing_tables"])


if __name__ == "__main__": unittest.main()
