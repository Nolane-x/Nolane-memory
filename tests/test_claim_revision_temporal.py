import tempfile
import unittest
from datetime import datetime, timezone, timedelta

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryWriteConflict


class ClaimRevisionTemporalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = datetime(2026, 9, 5, 1, 0, tzinfo=timezone.utc)
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db", clock=lambda: self.now)
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _evidence(self, op, sid, value):
        h = self.rt._head_row("d")
        return self.rt.capture_evidence(
            domain_id="d", operation_id=op, expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), source_event_identity=sid,
            content={"value": value}, principal="alice",
        ).object_id

    def _create(self, evidence_id, value):
        h = self.rt._head_row("d")
        return self.rt.create_claim(
            domain_id="d", operation_id="claim-create", expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), logical_id="status",
            proposition={"value": value}, valid_from=None, valid_to=None,
            support_paths=[[evidence_id]], principal="alice",
        ).object_id

    def test_revision_preserves_predecessor_and_moves_current_pointer(self):
        e1 = self._evidence("e1", "source:1", "old")
        old = self._create(e1, "old")
        self.now += timedelta(hours=1)
        e2 = self._evidence("e2", "source:2", "new")
        h = self.rt._head_row("d")
        new = self.rt.revise_claim(
            domain_id="d", operation_id="claim-revise", expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), logical_id="status",
            expected_predecessor_revision_id=old, proposition={"value": "new"},
            valid_from=None, valid_to=None, support_paths=[[e2]], principal="alice",
        ).object_id
        self.assertNotEqual(old, new)
        self.assertEqual(self.rt.get_claim_revision("d", old)["proposition"], {"value": "old"})
        self.assertIsNotNone(self.rt.get_claim_revision("d", old)["superseded_seq"])
        self.assertEqual(self.rt.get_claim_revision("d", new)["proposition"], {"value": "new"})
        self.assertIsNone(self.rt.get_claim_revision("d", new)["superseded_seq"])

    def test_stale_predecessor_cannot_overwrite_newer_revision(self):
        e1 = self._evidence("e1", "source:1", "old"); old = self._create(e1, "old")
        self.now += timedelta(hours=1)
        e2 = self._evidence("e2", "source:2", "new")
        h = self.rt._head_row("d")
        self.rt.revise_claim(
            domain_id="d", operation_id="r1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="status", expected_predecessor_revision_id=old, proposition={"value": "new"},
            valid_from=None, valid_to=None, support_paths=[[e2]], principal="alice",
        )
        e3 = self._evidence("e3", "source:3", "stale-writer")
        h = self.rt._head_row("d")
        with self.assertRaises(MemoryWriteConflict):
            self.rt.revise_claim(
                domain_id="d", operation_id="r2", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
                logical_id="status", expected_predecessor_revision_id=old, proposition={"value": "stale-writer"},
                valid_from=None, valid_to=None, support_paths=[[e3]], principal="alice",
            )

    def test_known_by_selects_historical_revision_without_future_correction_leak(self):
        t_old = self.now
        e1 = self._evidence("e1", "source:1", "old"); old = self._create(e1, "old")
        self.now += timedelta(hours=2)
        t_before_correction = self.now - timedelta(minutes=1)
        e2 = self._evidence("e2", "source:2", "new")
        h = self.rt._head_row("d")
        new = self.rt.revise_claim(
            domain_id="d", operation_id="r1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="status", expected_predecessor_revision_id=old, proposition={"value": "new"},
            valid_from=None, valid_to=None, support_paths=[[e2]], principal="alice",
        ).object_id
        self.assertEqual(self.rt.claim_as_known_by("d", "status", t_before_correction)["claim_revision_id"], old)
        self.assertEqual(self.rt.claim_as_known_by("d", "status", self.now + timedelta(seconds=1))["claim_revision_id"], new)
        self.assertIsNone(self.rt.claim_as_known_by("d", "status", t_old - timedelta(seconds=1)))

    def test_historical_judgement_remains_addressable_after_claim_correction(self):
        e1 = self._evidence("e1", "source:1", "old"); old = self._create(e1, "old")
        self.now += timedelta(minutes=30)
        judgement = self.rt.record_historical_judgement(
            "d", claim_revision_id=old, principal="alice", judgement="ACCEPTED", reason="basis-at-the-time"
        )
        self.now += timedelta(minutes=30)
        e2 = self._evidence("e2", "source:2", "new")
        h = self.rt._head_row("d")
        self.rt.revise_claim(
            domain_id="d", operation_id="r1", expected_seq=int(h["sequence"]), writer_epoch=int(h["writer_epoch"]),
            logical_id="status", expected_predecessor_revision_id=old, proposition={"value": "new"},
            valid_from=None, valid_to=None, support_paths=[[e2]], principal="alice",
        )
        got = self.rt.judgement_as_of("d", "status", self.now + timedelta(seconds=1), principal="alice")
        self.assertIsNotNone(got)
        self.assertEqual(got.judgement_id, judgement.judgement_id)
        self.assertEqual(got.claim_revision_id, old)


if __name__ == "__main__": unittest.main()
