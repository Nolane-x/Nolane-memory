import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from nolane_memory import MemoryRuntime
from nolane_memory.errors import IdempotencyConflict


class InjectedCrash(RuntimeError):
    pass


class WriteIntentLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2035, 1, 1, tzinfo=timezone.utc)
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/m.db", clock=lambda: self.now)
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _capture(self, operation_id="op", content=None):
        h = self.rt._head_row("d")
        return self.rt.capture_evidence(
            domain_id="d", operation_id=operation_id, expected_seq=int(h["sequence"]),
            writer_epoch=int(h["writer_epoch"]), source_event_identity="evt",
            content=content or {"x": 1}, principal="alice",
        )

    def test_precommit_crash_leaves_pending_durable_intent_but_no_truth(self):
        def fail(point, context):
            if point == "after_mutation_before_journal":
                raise InjectedCrash(point)
        self.rt.set_fault_injector(fail)
        with self.assertRaises(InjectedCrash):
            self._capture()
        self.rt.set_fault_injector(None)
        intent = self.rt.get_write_intent("d", "op")
        self.assertEqual(intent.status, "PENDING")
        self.assertEqual(self.rt.count_evidence("d"), 0)
        self.assertEqual(self.rt.head("d").sequence, 0)

    def test_retry_reconciles_same_intent_to_committed_exactly_once(self):
        fired = {"v": False}
        def fail_once(point, context):
            if point == "after_journal_before_receipt" and not fired["v"]:
                fired["v"] = True
                raise InjectedCrash(point)
        self.rt.set_fault_injector(fail_once)
        with self.assertRaises(InjectedCrash):
            self._capture()
        self.rt.set_fault_injector(None)
        receipt = self._capture()
        intent = self.rt.get_write_intent("d", "op")
        self.assertEqual(intent.status, "COMMITTED")
        self.assertEqual(intent.commit_seq, receipt.commit_seq)
        self.assertEqual(self.rt.count_evidence("d"), 1)
        self.assertEqual(len(self.rt.list_write_intents("d")), 1)

    def test_intent_identity_rejects_same_operation_id_with_different_request(self):
        self._capture(content={"x": 1})
        h = self.rt._head_row("d")
        with self.assertRaises(IdempotencyConflict):
            self.rt.capture_evidence(
                domain_id="d", operation_id="op", expected_seq=int(h["sequence"]),
                writer_epoch=int(h["writer_epoch"]), source_event_identity="evt",
                content={"x": 2}, principal="alice",
            )
        self.assertEqual(len(self.rt.list_write_intents("d")), 1)

    def test_expiring_pending_intent_does_not_change_canonical_truth(self):
        intent = self.rt.prepare_write_intent(
            "d", operation_id="future", kind="CAPTURE_EVIDENCE", object_id="candidate",
            request={"semantic": "request"}, expires_at=self.now + timedelta(minutes=1),
        )
        self.assertEqual(intent.status, "PENDING")
        self.now += timedelta(minutes=2)
        expired = self.rt.reconcile_write_intent("d", "future")
        self.assertEqual(expired.status, "EXPIRED")
        self.assertEqual(self.rt.head("d").sequence, 0)
        self.assertEqual(self.rt.count_evidence("d"), 0)


if __name__ == "__main__": unittest.main()
