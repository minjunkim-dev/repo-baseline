"""The copied repo-baseline files in this repository must match the manifest."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_repo_baseline import MANIFEST, ROOT, drift, mcp_secrets
import subprocess


class RepoBaselineTests(unittest.TestCase):
    def test_cli_pass_drift_and_missing_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scripts").mkdir()
            checker = root / "scripts/check_repo_baseline.py"
            checker.write_bytes((ROOT / "scripts/check_repo_baseline.py").read_bytes())
            def run():
                return subprocess.run([sys.executable, str(checker)], capture_output=True, text=True)
            self.assertEqual(run().returncode, 2)
            (root / ".github").mkdir()
            (root / "a.py").write_text("print(1)\n")
            (root / MANIFEST).write_text(json.dumps({"source_commit": "a" * 40, "files": {
                "a.py": {"sha256": hashlib.sha256(b"print(1)\n").hexdigest()}}}))
            self.assertEqual(run().returncode, 0)
            (root / "a.py").write_text("print(2)\n")
            self.assertEqual(run().returncode, 1)

    def test_changed_missing_and_invalid_entries_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".github").mkdir()
            (root / "a.py").write_text("print(1)\n")

            def write(files, commit="0" * 40):
                (root / MANIFEST).write_text(json.dumps({"source_commit": commit, "files": files}))

            good = hashlib.sha256(b"print(1)\n").hexdigest()
            write({"a.py": {"sha256": good}})
            self.assertEqual(drift(root), [])
            (root / "a.py").write_text("print(2)\n")
            write({"a.py": {"sha256": good}, "gone.py": {"sha256": good}})
            self.assertEqual(drift(root), ["a.py", "gone.py"])
            for bad in [{}, {"../x.py": {"sha256": good}}]:
                with self.subTest(files=bad):
                    write(bad)
                    with self.assertRaises(ValueError):
                        drift(root)
            write({"a.py": {"sha256": good}}, commit=None)
            with self.assertRaises(ValueError):
                drift(root)

    def test_mcp_json_values_must_reference_variables(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(mcp_secrets(root), [])
            (root / ".mcp.json").write_text(json.dumps({"mcpServers": {
                "ok": {"env": {"TOKEN": "${API_TOKEN}"}, "headers": {"Authorization": "Bearer ${API_TOKEN}"}},
                "bad": {"env": {"TOKEN": "sk-123"}, "headers": {"Authorization": "Bearer sk-123"}},
            }}))
            self.assertEqual(mcp_secrets(root), ["bad.env.TOKEN", "bad.headers.Authorization"])
            (root / ".mcp.json").write_text("[]")
            with self.assertRaises(ValueError):
                mcp_secrets(root)


if __name__ == "__main__":
    unittest.main()
