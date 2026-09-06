import tempfile
import unittest

from nolane_memory import MemoryRuntime
from nolane_memory.types import LossState, RecallBoundaryDescriptor, RecallRole


class HiddenTransformDependencyRaceRc4Reproduction(unittest.TestCase):
    """E0-v2: test hidden transform input after a conformant action-boundary recall.

    Unlike the original E0 trace, this test does not omit the direct action/tool input
    role.  The active consequence frame is compiled with ``compile_boundary_recall``;
    the invoice amount is an ``action_tool_role`` and is therefore forced hard by the
    existing rc4 contract.  The candidate seam is narrower: a previously retained
    conversion rate materially influences the final structured amount but is not an
    enumerated role or a declared hard dependency of the invoice representation.

    This remains a baseline reproduction experiment, not an SRSC treatment and not a
    universal dependency-completeness claim.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rt = MemoryRuntime(f"{self.tmp.name}/memory.db")
        self.rt.create_domain("e0v2", writer_epoch=1)
        self.rt.register_query_family("ACTION", {"intent"})
        self.rt.register_query_family("INVOICE", {"amount_minor"})
        self.rt.register_query_family("RATE", {"multiplier"})

        self.action_region = self.rt.create_region("e0v2", "action", principal="alice")
        self.action_rep = self.rt.add_representation(
            "e0v2",
            self.action_region,
            kind="exact",
            payload={"intent": "charge_invoice"},
            loss={"intent": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )

        self.invoice_region = self.rt.create_region("e0v2", "invoice", principal="alice")
        self.invoice_rep = self.rt.add_representation(
            "e0v2",
            self.invoice_region,
            kind="exact",
            payload={"amount_minor": 10_000},
            loss={"amount_minor": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )

        self.rate_region = self.rt.create_region("e0v2", "conversion-rate", principal="alice")
        self.old_rate_rep = self.rt.add_representation(
            "e0v2",
            self.rate_region,
            kind="exact",
            payload={"multiplier": 0.90},
            loss={"multiplier": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )

    def tearDown(self):
        self.rt.close()
        self.tmp.cleanup()

    def test_e0v2_conformant_boundary_can_miss_hidden_transform_input(self):
        # Hidden transform input B is retained from a prior, independently valid frame.
        prior_rate_frame = self.rt.compile_recall(
            "e0v2",
            "alice",
            [RecallRole("rate", self.rate_region, "RATE")],
            32,
        )
        stale_multiplier = prior_rate_frame.fragments[0].payload["multiplier"]
        self.assertEqual(stale_multiplier, 0.90)

        # The active consequence uses the rc4 consequence-bound API.  The direct
        # structured action inputs are declared and must become hard obligations.
        boundary = RecallBoundaryDescriptor(
            task="charge invoice in converted currency",
            principal="alice",
            explicit_roles=[RecallRole("action", self.action_region, "ACTION")],
            action_tool_roles=[RecallRole("invoice-amount", self.invoice_region, "INVOICE", False)],
            sink="tool:charge",
            token_budget=64,
        )
        action_frame, obligation = self.rt.compile_boundary_recall("e0v2", boundary)

        hard_role_ids = {role.role_id for role in obligation.hard_roles}
        self.assertIn("action", hard_role_ids)
        self.assertIn("invoice-amount", hard_role_ids)
        self.assertNotIn("rate", hard_role_ids)

        deps = {(dep.dep_class, dep.dep_key) for dep in action_frame.dependencies}
        self.assertIn(("region", self.invoice_region), deps)
        self.assertIn(("representation", self.invoice_rep), deps)
        self.assertNotIn(("region", self.rate_region), deps)
        self.assertNotIn(("representation", self.old_rate_rep), deps)

        invoice_fragment = next(f for f in action_frame.fragments if f.role_id == "invoice-amount")
        base_amount_minor = invoice_fragment.payload["amount_minor"]

        # B changes after the conformant action-boundary frame was compiled.  A and the
        # direct invoice input remain unchanged.
        self.rt.invalidate_representation("e0v2", self.old_rate_rep, principal="alice")
        new_rate_rep = self.rt.add_representation(
            "e0v2",
            self.rate_region,
            kind="exact",
            payload={"multiplier": 1.10},
            loss={"multiplier": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=4,
            principal="alice",
        )

        # The active boundary frame remains current because the transform input B was
        # never represented in the semantic read-set.
        self.assertTrue(self.rt.validate_frame(action_frame.frame_id))

        stale_payload = {
            "amount_minor": round(base_amount_minor * stale_multiplier),
            "currency": "EUR",
        }
        fence = self.rt.issue_use_fence(
            action_frame,
            principal="alice",
            sink="tool:charge",
            payload=stale_payload,
        )
        accepted = self.rt.consume_use_fence(
            fence.fence_id,
            principal="alice",
            sink="tool:charge",
            payload=stale_payload,
        )

        current_rate_frame = self.rt.compile_recall(
            "e0v2",
            "alice",
            [RecallRole("rate-current", self.rate_region, "RATE")],
            32,
        )
        current_multiplier = current_rate_frame.fragments[0].payload["multiplier"]
        current_amount_minor = round(base_amount_minor * current_multiplier)

        # Oracle: exact payload binding succeeded, but the bound amount is stale with
        # respect to the current hidden transform input.
        self.assertEqual(current_multiplier, 1.10)
        self.assertEqual(stale_payload["amount_minor"], 9_000)
        self.assertEqual(current_amount_minor, 11_000)
        self.assertNotEqual(stale_payload["amount_minor"], current_amount_minor)
        self.assertTrue(accepted)
        self.assertNotEqual(new_rate_rep, self.old_rate_rep)


if __name__ == "__main__":
    unittest.main()
