import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.errors import MemoryDependencyStale


class ConnectorOpacityFrontierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("d")

    def tearDown(self):
        self.rt.close(); self.tmp.cleanup()

    def _profile(self, revision=1, **overrides):
        caps = {
            "stable_event_ids": True,
            "point_in_time_snapshot": True,
            "pagination_guarantee": True,
            "update_delete_visibility": True,
            "source_versioning": True,
            "authorization_scope": "principal",
            "raw_evidence_retention": True,
        }
        caps.update(overrides)
        return self.rt.register_connector_profile(
            "d", "gmail", revision=revision, capabilities=caps,
            transport_authority="AUTHENTICATED_PROVIDER_TRANSPORT",
            content_authority="UNTRUSTED_CONTENT",
        )

    def test_capped_or_incomplete_pagination_can_never_prove_absence(self):
        self._profile()
        q = self.rt.record_connector_query(
            "d", connector_id="gmail", principal="alice", predicate={"label": "never"},
            snapshot_id="snap-1", pages_seen=10, pagination_complete=False,
            result_capped=True, result_ids=[], provider_error=None,
        )
        self.assertEqual(q.completeness, "PARTIAL")
        self.assertEqual(q.status, "NO_MATCH_PARTIAL_DOMAIN")

    def test_complete_snapshot_and_pagination_can_issue_bounded_absence_receipt(self):
        self._profile()
        q = self.rt.record_connector_query(
            "d", connector_id="gmail", principal="alice", predicate={"label": "never"},
            snapshot_id="snap-1", pages_seen=3, pagination_complete=True,
            result_capped=False, result_ids=[], provider_error=None,
        )
        self.assertEqual(q.completeness, "COMPLETE")
        self.assertEqual(q.status, "NO_MATCH_COMPLETE_DOMAIN")
        self.assertTrue(self.rt.validate_connector_query_receipt(q.receipt_id))

    def test_connector_profile_revision_stales_old_completeness_receipt(self):
        self._profile()
        q = self.rt.record_connector_query(
            "d", connector_id="gmail", principal="alice", predicate={"q": "x"},
            snapshot_id="snap-1", pages_seen=1, pagination_complete=True,
            result_capped=False, result_ids=[], provider_error=None,
        )
        self._profile(revision=2, pagination_guarantee=False)
        with self.assertRaises(MemoryDependencyStale):
            self.rt.validate_connector_query_receipt(q.receipt_id)

    def test_transport_authority_is_not_content_authority(self):
        self._profile()
        q = self.rt.record_connector_query(
            "d", connector_id="gmail", principal="alice", predicate={"q": "x"},
            snapshot_id="snap-1", pages_seen=1, pagination_complete=True,
            result_capped=False, result_ids=["m1"], provider_error=None,
        )
        self.assertEqual(q.transport_authority, "AUTHENTICATED_PROVIDER_TRANSPORT")
        self.assertEqual(q.content_authority, "UNTRUSTED_CONTENT")
        self.assertEqual(q.status, "SUPPORT_FOR_EXISTENCE")

    def test_opaque_provider_error_is_not_partial_or_complete_absence(self):
        self._profile()
        q = self.rt.record_connector_query(
            "d", connector_id="gmail", principal="alice", predicate={"q": "x"},
            snapshot_id=None, pages_seen=0, pagination_complete=False,
            result_capped=False, result_ids=[], provider_error="permission-redacted",
        )
        self.assertEqual(q.completeness, "OPAQUE")
        self.assertEqual(q.status, "OPAQUE_OR_INCOMPLETE")


if __name__ == "__main__": unittest.main()
