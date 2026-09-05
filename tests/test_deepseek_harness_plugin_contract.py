from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "deepseek-harness"


class DeepSeekHarnessPluginContractTests(unittest.TestCase):
    def test_package_pins_current_developer_preview_contract(self):
        package = json.loads((PLUGIN / "package.json").read_text())
        self.assertEqual(package["type"], "module")
        self.assertEqual(package["engines"]["node"], "^22.19.0 || >=24.0.0")
        self.assertEqual(package["peerDependencies"]["@deepseek-ai/cordis"], "4.0.2")
        self.assertEqual(package["peerDependencies"]["@deepseek-ai/dsh-tools"], "0.1.3-alpha.1")
        self.assertEqual(package["peerDependencies"]["@deepseek-ai/schemastery"], "3.18.2")

    def test_package_has_explicit_deepseek_workspace_typecheck_contract(self):
        package = json.loads((PLUGIN / "package.json").read_text())
        self.assertEqual(
            package["scripts"]["typecheck:dsh-workspace"],
            "tsc -b tsconfig.dsh-workspace.json --pretty false",
        )
        config = json.loads((PLUGIN / "tsconfig.dsh-workspace.json").read_text())
        self.assertEqual(config["extends"], "../../../tsconfig.base.json")
        self.assertEqual(config["compilerOptions"]["rootDir"], "src")
        self.assertEqual(config["compilerOptions"]["outDir"], "lib/types")
        self.assertEqual(config["include"], ["src"])
        self.assertEqual(
            [ref["path"] for ref in config["references"]],
            ["../../../vendor/cordis", "../../../vendor/schemastery", "../../core/tools"],
        )

    def test_plugin_uses_documented_cordis_shape_and_registers_expected_tools(self):
        text = (PLUGIN / "src" / "index.ts").read_text()
        self.assertRegex(text, r"export const name\s*=\s*['\"]nolane-memory['\"]")
        self.assertRegex(text, r"export const inject\s*=\s*\[['\"]tools['\"]\]")
        self.assertIn("export interface Config", text)
        self.assertIn("export const Config", text)
        self.assertIn("export function apply", text)
        self.assertGreaterEqual(text.count("ctx.tools.register(defineTool({"), 4)
        for tool in (
            "nolane_memory_status", "nolane_memory_capture", "nolane_memory_recall",
            "nolane_memory_verify", "nolane_memory_release_gate",
        ):
            self.assertIn(f"name: '{tool}'", text)

    def test_subprocess_bridge_is_shell_free_and_model_cannot_choose_db_domain_or_principal(self):
        text = (PLUGIN / "src" / "index.ts").read_text()
        self.assertIn("spawn(", text)
        self.assertIn("shell: false", text)
        self.assertNotIn("exec(", text)
        parameter_blocks = re.findall(r"parameters:\s*\{(.*?)\n\s*\},\n\s*output:", text, flags=re.S)
        self.assertTrue(parameter_blocks)
        joined = "\n".join(parameter_blocks)
        for forbidden in ("database:", "domain:", "principal:", "pythonExecutable:"):
            self.assertNotIn(forbidden, joined)

    def test_bridge_imports_only_public_nolane_package_surface(self):
        text = (PLUGIN / "python" / "nolane_memory_bridge.py").read_text()
        self.assertIn("from nolane_memory import", text)
        self.assertNotRegex(text, r"from nolane_memory\.(runtime|research|governance|effects_security|continuity|evolution)")

    def test_example_overlay_mounts_system_prompt_tools_and_plugin(self):
        text = (PLUGIN / "cordis.patch.yml").read_text()
        self.assertIn("@deepseek-ai/dsh-system-prompt", text)
        self.assertIn("@deepseek-ai/dsh-tools", text)
        self.assertIn("./src/index.ts", text)


if __name__ == "__main__":
    unittest.main()
