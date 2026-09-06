import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import LossState, RecallRole


class HiddenDependencyRaceRc4Reproduction(unittest.TestCase):
    """E0: reproduce a consequence that depends on stale memory omitted from the active frame.

    This is a baseline-reproduction test, not the v0.7 treatment.  The expected rc4
    observation is a false accept: the active frame/fence remains valid because the
    materially used contact-memory dependency came from prior host context and is not
    present in the active frame dependency manifest.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("e0", writer_epoch=1)
        self.rt.register_query_family("ACTION", {"intent"})
        self.rt.register_query_family("CONTACT", {"email"})

        self.action_region = self.rt.create_region("e0", "action", principal="alice")
        self.action_rep = self.rt.add_representation(
            "e0",
            self.action_region,
            kind="exact",
            payload={"intent": "send_status"},
            loss={"intent": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )

        self.contact_region = self.rt.create_region("e0", "contact", principal="alice")
        self.old_contact_rep = self.rt.add_representation(
            "e0",
            self.contact_region,
            kind="exact",
            payload={"email": "old@example.com"},
            loss={"email": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )

    def tearDown(self):
        self.rt.close()
        self.tmp.cleanup()

    def test_e0_reproduces_false_accept_for_hidden_stale_dependency(self):
        # B is first read into host/model context in a prior frame.
        prior_contact_frame = self.rt.compile_recall(
            "e0",
            "alice",
            [RecallRole("contact", self.contact_region, "CONTACT")],
            32,
        )
        stale_email = prior_contact_frame.fragments[0].payload["email"]
        self.assertEqual(stale_email, "old@example.com")

        # A later active frame covers only action intent.  B is intentionally absent.
        action_frame = self.rt.compile_recall(
            "e0",
            "alice",
            [RecallRole("action", self.action_region, "ACTION")],
            32,
        )
        deps = {(dep.dep_class, dep.dep_key) for dep in action_frame.dependencies}
        self.assertNotIn(("region", self.contact_region), deps)
        self.assertNotIn(("representation", self.old_contact_rep), deps)

        # B changes after the active frame was compiled.
        before_mutation = self.rt.head("e0")
        self.rt.invalidate_representation("e0", self.old_contact_rep, principal="alice")
        new_contact_rep = self.rt.add_representation(
            "e0",
            self.contact_region,
            kind="exact",
            payload={"email": "new@example.com"},
            loss={"email": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )
        after_mutation = self.rt.head("e0")
        self.assertGreater(after_mutation.sequence, before_mutation.sequence)

        # The active A frame is still considered current because B was never enumerated.
        self.assertTrue(self.rt.validate_frame(action_frame.frame_id))

        stale_payload = {"to": stale_email, "body": "status"}
        fence = self.rt.issue_use_fence(
            action_frame,
            principal="alice",
            sink="tool:send",
            payload=stale_payload,
        )
        accepted = self.rt.consume_use_fence(
            fence.fence_id,
            principal="alice",
            sink="tool:send",
            payload=stale_payload,
        )

        current_contact_frame = self.rt.compile_recall(
            "e0",
            "alice",
            [RecallRole("contact-current", self.contact_region, "CONTACT")],
            32,
        )
        current_email = current_contact_frame.fragments[0].payload["email"]

        # Oracle: the emitted address is stale relative to current B.
        self.assertEqual(current_email, "new@example.com")
        self.assertNotEqual(stale_payload["to"], current_email)
        self.assertTrue(accepted)
        self.assertNotEqual(new_contact_rep, self.old_contact_rep)


if __name__ == "__main__":
    unittest.main()
