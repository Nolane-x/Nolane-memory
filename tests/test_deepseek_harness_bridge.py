from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nolane_memory import LossState, MemoryRuntime

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "plugins" / "deepseek-harness" / "python" / "nolane_memory_bridge.py"


def call_bridge(request: dict) -> dict:
    cp = subprocess.run(
        [sys.executable, str(BRIDGE)],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        env={**__import__('os').environ, "PYTHONPATH": str(ROOT / "src")},
        timeout=30,
        check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(f"bridge process failed: {cp.returncode}\nstdout={cp.stdout}\nstderr={cp.stderr}")
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise AssertionError(f"bridge emitted {len(lines)} protocol lines: {cp.stdout!r}; stderr={cp.stderr!r}")
    return json.loads(lines[0])


class DeepSeekHarnessBridgeTests(unittest.TestCase):
    def test_status_is_fail_visible_for_missing_domain_without_creating_it(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "memory.db")
            response = call_bridge({"id": "1", "method": "status", "params": {"db": db, "domain": "agent"}})
            self.assertTrue(response["ok"])
            self.assertFalse(response["result"]["domain_exists"])
            rt = MemoryRuntime(db)
            try:
                count = rt.db.execute("SELECT COUNT(*) FROM domains").fetchone()[0]
                self.assertEqual(count, 0)
            finally:
                rt.close()

    def test_capture_can_create_configured_domain_and_defaults_authority_to_unspecified(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "memory.db")
            request = {
                "id": "cap-1",
                "method": "capture",
                "params": {
                    "db": db,
                    "domain": "agent",
                    "principal": "deepseek-agent",
                    "auto_create_domain": True,
                    "source_event_identity": "session:1:message:1",
                    "content": {"text": "remember the exact value 42"},
                },
            }
            first = call_bridge(request)
            second = call_bridge(request)
            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertEqual(first["result"]["object_id"], second["result"]["object_id"])
            rt = MemoryRuntime(db)
            try:
                bindings = rt.db.execute(
                    "SELECT authority_class,binder_procedure FROM origin_bindings WHERE domain_id='agent'"
                ).fetchall()
                self.assertEqual(len(bindings), 1)
                self.assertEqual(bindings[0][0], "UNSPECIFIED")
                self.assertEqual(bindings[0][1], "deepseek-harness-bridge-v1")
                self.assertEqual(rt.count_evidence("agent"), 1)
                self.assertTrue(rt.verify_integrity("agent"))
            finally:
                rt.close()

    def test_recall_compiles_only_predeclared_contracts_and_returns_typed_frame(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "memory.db")
            rt = MemoryRuntime(db)
            try:
                rt.create_domain("agent")
                rt.register_query_family("exact_text", {"text"})
                region = rt.create_region("agent", "session-memory", principal="deepseek-agent")
                rep = rt.add_representation(
                    "agent", region, kind="raw", payload={"text": "alpha"},
                    loss={"text": LossState.PRESERVED_EXACT}, recoverable=set(), token_cost=1,
                    principal="deepseek-agent",
                )
            finally:
                rt.close()
            response = call_bridge({
                "id": "recall-1",
                "method": "recall",
                "params": {
                    "db": db,
                    "domain": "agent",
                    "principal": "deepseek-agent",
                    "roles": [{"role_id": "r1", "region_id": region, "query_family": "exact_text", "hard": True}],
                    "token_budget": 32,
                    "page_fault_budget": 2,
                },
            })
            self.assertTrue(response["ok"])
            self.assertEqual(response["result"]["sufficiency"], "SUFFICIENT")
            self.assertEqual(response["result"]["fragments"][0]["representation_id"], rep)
            self.assertEqual(response["result"]["fragments"][0]["payload"], {"text": "alpha"})

    def test_verify_returns_integrity_and_single_clock_audit(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "memory.db")
            rt = MemoryRuntime(db)
            try:
                rt.create_domain("agent")
            finally:
                rt.close()
            response = call_bridge({"id": "v1", "method": "verify", "params": {"db": db, "domain": "agent"}})
            self.assertTrue(response["ok"])
            self.assertTrue(response["result"]["integrity"])
            self.assertTrue(response["result"]["no_two_writable_clocks"]["ok"])

    def test_unknown_method_is_protocol_error_not_success_payload(self):
        with tempfile.TemporaryDirectory() as td:
            response = call_bridge({"id": "bad", "method": "invent_authority", "params": {"db": str(Path(td)/'x.db')}})
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["type"], "BridgeMethodNotAllowed")


if __name__ == "__main__":
    unittest.main()
