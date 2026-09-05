import json
import os
import subprocess
import sys
import tempfile
import unittest


class CLIFullProfileTests(unittest.TestCase):
    def run_cli(self, db, *args):
        env = dict(os.environ); env["PYTHONPATH"] = "src"
        cp = subprocess.run([sys.executable, "-m", "nolane_memory.cli", "--db", db, *args],
                            cwd=os.path.dirname(os.path.dirname(__file__)), env=env,
                            text=True, capture_output=True, check=True)
        return json.loads(cp.stdout)

    def test_status_lab_fuzz_and_debts_commands(self):
        with tempfile.TemporaryDirectory() as td:
            db = f"{td}/m.db"
            self.run_cli(db, "init", "d")
            status = self.run_cli(db, "status")
            self.assertEqual(status["research_closure"], "BLOCKED")
            debts = self.run_cli(db, "debts", "d")
            self.assertEqual(debts, [])
            lab = self.run_cli(db, "lab")
            self.assertEqual(lab["failed"], 0)
            fuzz = self.run_cli(db, "fuzz", "--seed", "7", "--cases", "100")
            self.assertEqual(fuzz["failed"], 0)


if __name__ == "__main__": unittest.main()
