import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryIdentityCollision


class OriginBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close()
        self.tmp.cleanup()

    def _capture(self, op, sid, *, root, common_mode, authority="UNTRUSTED_CONTENT"):
        h = self.rt._head_row("d")
        return self.rt.capture_evidence(
            domain_id="d", operation_id=op,
            expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            source_event_identity=sid, content={"sid": sid}, principal="alice",
            origin_roots=[root], transport_channel="browser:https",
            external_identity=f"https://example.test/{sid}",
            source_authority_class=authority,
            common_mode_group=common_mode,
            scope_ceiling=["alice"], binder_procedure="test-capture-v1",
        )

    def test_capture_creates_non_malleable_origin_binding_at_capture_boundary(self):
        rec = self._capture("op1", "evt1", root="origin:article:1", common_mode="publisher:one")
        bindings = self.rt.get_origin_bindings("d", rec.object_id)
        self.assertEqual(len(bindings), 1)
        b = bindings[0]
        self.assertEqual(b.origin_identity, "origin:article:1")
        self.assertEqual(b.transport_channel, "browser:https")
        self.assertEqual(b.external_identity, "https://example.test/evt1")
        self.assertEqual(b.authority_class, "UNTRUSTED_CONTENT")
        self.assertEqual(b.common_mode_group, "publisher:one")
        self.assertEqual(b.scope_ceiling, ["alice"])
        self.assertEqual(b.binder_procedure, "test-capture-v1")
        self.assertEqual(b.raw_evidence_digest, self.rt.db.execute(
            "SELECT content_digest FROM evidence WHERE evidence_id=?", (rec.object_id,)
        ).fetchone()[0])
        self.assertIsNone(b.revoked_seq)

    def test_same_semantic_event_cannot_rebind_origin_authority(self):
        first = self._capture("op1", "evt1", root="origin:one", common_mode="cm:one")
        h = self.rt._head_row("d")
        with self.assertRaises(MemoryIdentityCollision):
            self.rt.capture_evidence(
                domain_id="d", operation_id="op2", expected_seq=int(h["sequence"]),
                writer_epoch=int(h["writer_epoch"]), source_event_identity="evt1",
                content={"sid": "evt1"}, principal="alice", origin_roots=["origin:one"],
                transport_channel="trusted-memory-writer", external_identity="agent:copy",
                source_authority_class="TRUSTED_FACT", common_mode_group="cm:one",
                scope_ceiling=["alice"], binder_procedure="laundering-attempt",
            )
        self.assertEqual(len(self.rt.get_origin_bindings("d", first.object_id)), 1)

    def test_common_mode_group_prevents_false_independence_across_distinct_origin_labels(self):
        e1 = self._capture("op1", "evt1", root="origin:mirror:a", common_mode="upstream:wire-7").object_id
        e2 = self._capture("op2", "evt2", root="origin:mirror:b", common_mode="upstream:wire-7").object_id
        result = self.rt.evaluate_evidence_independence("d", [e1, e2])
        self.assertEqual(result["dependence"], "DEPENDENT")
        self.assertEqual(result["independent_root_count"], 1)
        self.assertEqual(result["common_mode_groups"], ["upstream:wire-7"])

    def test_revoked_binding_makes_dependence_unknown_instead_of_optimistically_independent(self):
        e1 = self._capture("op1", "evt1", root="origin:a", common_mode="cm:a").object_id
        e2 = self._capture("op2", "evt2", root="origin:b", common_mode="cm:b").object_id
        self.assertEqual(self.rt.evaluate_evidence_independence("d", [e1, e2])["dependence"], "INDEPENDENT")
        binding = self.rt.get_origin_bindings("d", e1)[0]
        self.rt.revoke_origin_binding("d", binding.binding_id, principal="alice", reason="issuer-key-compromise")
        result = self.rt.evaluate_evidence_independence("d", [e1, e2])
        self.assertEqual(result["dependence"], "UNKNOWN_DEPENDENCE")
        self.assertEqual(result["independent_root_count"], 0)


if __name__ == "__main__":
    unittest.main()
