import tempfile
import unittest
from datetime import datetime, timezone, timedelta

from nolane_memory import MemoryRuntime
from nolane_memory.errors import IdempotencyConflict, MemoryWriteConflict, MemoryStaleWriter, MemoryScopeBlocked


class K0CanonicalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("personal", writer_epoch=7)

    def tearDown(self):
        self.rt.close()
        self.tmp.cleanup()

    def test_operation_id_is_idempotent_and_digest_bound(self):
        first = self.rt.capture_evidence(
            domain_id="personal", operation_id="op-1", expected_seq=0, writer_epoch=7,
            source_event_identity="email:42", content={"value": "A"}, principal="alice",
        )
        again = self.rt.capture_evidence(
            domain_id="personal", operation_id="op-1", expected_seq=0, writer_epoch=7,
            source_event_identity="email:42", content={"value": "A"}, principal="alice",
        )
        self.assertEqual(first.commit_seq, again.commit_seq)
        self.assertEqual(first.root, again.root)
        with self.assertRaises(IdempotencyConflict):
            self.rt.capture_evidence(
                domain_id="personal", operation_id="op-1", expected_seq=0, writer_epoch=7,
                source_event_identity="email:42", content={"value": "B"}, principal="alice",
            )

    def test_expected_base_and_writer_fence_are_enforced(self):
        self.rt.capture_evidence(
            domain_id="personal", operation_id="op-a", expected_seq=0, writer_epoch=7,
            source_event_identity="evt:a", content={"x": 1}, principal="alice",
        )
        with self.assertRaises(MemoryWriteConflict):
            self.rt.capture_evidence(
                domain_id="personal", operation_id="op-b", expected_seq=0, writer_epoch=7,
                source_event_identity="evt:b", content={"x": 2}, principal="alice",
            )
        with self.assertRaises(MemoryStaleWriter):
            self.rt.capture_evidence(
                domain_id="personal", operation_id="op-c", expected_seq=1, writer_epoch=6,
                source_event_identity="evt:c", content={"x": 3}, principal="alice",
            )

    def test_duplicate_transport_delivery_does_not_multiply_evidence(self):
        r1 = self.rt.capture_evidence(
            domain_id="personal", operation_id="op-1", expected_seq=0, writer_epoch=7,
            source_event_identity="provider:777", transport_delivery_id="delivery-1",
            content={"body": "same"}, principal="alice",
        )
        r2 = self.rt.capture_evidence(
            domain_id="personal", operation_id="op-2", expected_seq=r1.commit_seq, writer_epoch=7,
            source_event_identity="provider:777", transport_delivery_id="delivery-2",
            content={"body": "same"}, principal="alice",
        )
        self.assertEqual(self.rt.count_evidence("personal"), 1)
        self.assertEqual(self.rt.count_deliveries("personal", "provider:777"), 2)
        self.assertGreater(r2.commit_seq, r1.commit_seq)

    def test_claim_valid_time_is_distinct_from_knowledge_time(self):
        past = datetime(2026, 1, 1, tzinfo=timezone.utc)
        before_ingest = datetime.now(timezone.utc) - timedelta(days=1)
        ev = self.rt.capture_evidence(
            domain_id="personal", operation_id="e1", expected_seq=0, writer_epoch=7,
            source_event_identity="log:late", content={"status": "broken"}, principal="alice",
            world_time=past,
        )
        claim = self.rt.create_claim(
            domain_id="personal", operation_id="c1", expected_seq=ev.commit_seq, writer_epoch=7,
            logical_id="service-status", proposition={"status": "broken"},
            valid_from=past, valid_to=None, support_paths=[[ev.object_id]], principal="alice",
        )
        self.assertTrue(self.rt.claim_valid_at("personal", "service-status", past + timedelta(hours=1)))
        self.assertFalse(self.rt.claim_known_by("personal", "service-status", before_ingest))
        self.assertTrue(self.rt.claim_known_by("personal", "service-status", datetime.now(timezone.utc) + timedelta(seconds=1)))

    def test_exact_read_obeys_principal_scope(self):
        ev = self.rt.capture_evidence(
            domain_id="personal", operation_id="private", expected_seq=0, writer_epoch=7,
            source_event_identity="secret:1", content={"secret": 9}, principal="alice",
            allowed_principals=["alice"],
        )
        self.assertEqual(self.rt.get_evidence("personal", ev.object_id, principal="alice")["secret"], 9)
        with self.assertRaises(MemoryScopeBlocked):
            self.rt.get_evidence("personal", ev.object_id, principal="bob")


if __name__ == "__main__":
    unittest.main()
