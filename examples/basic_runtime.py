from __future__ import annotations

import tempfile
from pathlib import Path

from nolane_memory import LossState, MemoryRuntime, RecallRole


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "memory.db"
        rt = MemoryRuntime(str(db_path))
        rt.create_domain("personal", writer_epoch=1)
        rt.register_query_family("EXACT_VALUE", {"exact_number"})

        region = rt.create_region("personal", "deployment:latency", principal="alice")
        raw = rt.add_representation(
            "personal",
            region,
            kind="raw",
            payload={"exact_number": 97.36},
            loss={"exact_number": LossState.PRESERVED_EXACT},
            recoverable=set(),
            token_cost=40,
            principal="alice",
        )
        rt.add_representation(
            "personal",
            region,
            kind="summary",
            payload={"text": "roughly 100 ms"},
            source_representation_ids=[raw],
            loss={"exact_number": LossState.LOST},
            recoverable={"exact_number"},
            token_cost=5,
            principal="alice",
        )

        frame = rt.compile_recall(
            "personal",
            "alice",
            [RecallRole("need-exact", region, "EXACT_VALUE")],
            token_budget=50,
        )
        fragment = frame.fragments[0]
        print("frame:", frame.frame_id, frame.sufficiency, "tokens=", frame.token_cost)
        print("selected:", fragment.representation_id, "page_faulted=", fragment.page_faulted)
        print("payload:", fragment.payload)

        final_payload = {"target": "deploy", "latency_ms": fragment.payload["exact_number"]}
        fence = rt.issue_use_fence(
            frame,
            principal="alice",
            sink="tool:deploy",
            payload=final_payload,
        )
        rt.consume_use_fence(
            fence.fence_id,
            principal="alice",
            sink="tool:deploy",
            payload=final_payload,
        )
        print("use fence consumed:", fence.fence_id)
        print("canonical integrity:", rt.verify_integrity("personal"))
        rt.close()


if __name__ == "__main__":
    main()
