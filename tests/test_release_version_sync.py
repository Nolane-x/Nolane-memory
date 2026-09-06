import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rc4_python_and_deepseek_plugin_versions_are_synchronized():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    plugin = json.loads((ROOT / "plugins/deepseek-harness/package.json").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == "0.6.3rc4"
    assert plugin["version"] == "0.6.3-rc.4"
