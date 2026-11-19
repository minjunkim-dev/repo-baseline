"""Apply shared files into a scratch project, then verify them with the copied checker."""

import contextlib
import hashlib
import io
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import apply_baseline

CHECKER = "scripts/check_repo_baseline.py"
SOURCE = "profiles/hash-copy/check_repo_baseline.py"


def fake_git(*args):
    return "" if args[0] == "status" else "c" * 40


class ApplyBaselineTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.project = Path(folder.name)
        (self.project / ".github").mkdir()
        self.write_manifest({"files": {CHECKER: {"source": SOURCE}}, "project_note": "keep"})

    def write_manifest(self, data):
        (self.project / apply_baseline.MANIFEST).write_text(json.dumps(data))

    def run_checker(self):
        return subprocess.run([sys.executable, str(self.project / CHECKER)], capture_output=True, text=True)

    def test_apply_copies_records_hashes_and_keeps_project_keys(self):
        with patch.object(apply_baseline, "git", fake_git):
            self.assertEqual(apply_baseline.apply(self.project), [CHECKER])
        manifest = json.loads((self.project / apply_baseline.MANIFEST).read_text())
        self.assertEqual(manifest["source_commit"], "c" * 40)
        self.assertEqual(manifest["project_note"], "keep")
        self.assertEqual(len(manifest["files"][CHECKER]["sha256"]), 64)
        self.assertEqual(apply_baseline.apply(self.project, check=True), [])
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_edit_is_drift_for_both_tools(self):
        with patch.object(apply_baseline, "git", fake_git):
            apply_baseline.apply(self.project)
        with (self.project / CHECKER).open("a") as file:
            file.write("# local edit\n")
        self.assertEqual(apply_baseline.apply(self.project, check=True), [CHECKER])
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        self.assertIn("DRIFT: " + CHECKER, result.stdout)

    def run_main(self, *flags):
        err = io.StringIO()
        with patch.object(apply_baseline, "git", fake_git), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(err):
            code = apply_baseline.main(["apply_baseline.py", str(self.project), *flags])
        return code, err.getvalue()

    def two_files(self, edited):
        """A clean old copy that needs updating, plus the given text in a second target."""
        template = ".github/pull_request_template.md"
        files = {CHECKER: {"source": SOURCE, "sha256": hashlib.sha256(b"old\n").hexdigest()},
                 template: {"source": template, "sha256": hashlib.sha256(b"old\n").hexdigest()}}
        self.write_manifest({"files": files, "source_commit": "a" * 40})
        (self.project / "scripts").mkdir()
        (self.project / CHECKER).write_text("old\n")
        (self.project / template).write_text(edited)
        return template

    def test_local_edit_stops_before_writing_anything(self):
        template = self.two_files("old\nlocal edit\n")
        manifest = (self.project / apply_baseline.MANIFEST).read_bytes()
        code, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn(template + " (differs from recorded sha256)", err)
        self.assertIn("--force", err)
        self.assertNotIn(CHECKER, err)
        self.assertEqual((self.project / CHECKER).read_text(), "old\n")
        self.assertEqual((self.project / template).read_text(), "old\nlocal edit\n")
        self.assertEqual((self.project / apply_baseline.MANIFEST).read_bytes(), manifest)

    def test_force_overwrites_local_edit_and_records_new_hashes(self):
        template = self.two_files("old\nlocal edit\n")
        self.assertEqual(self.run_main("--force"), (0, ""))
        new = (apply_baseline.HERE / template).read_bytes()
        self.assertEqual((self.project / template).read_bytes(), new)
        manifest = json.loads((self.project / apply_baseline.MANIFEST).read_text())
        self.assertEqual(manifest["files"][template]["sha256"], hashlib.sha256(new).hexdigest())
        self.assertEqual(manifest["source_commit"], "c" * 40)

    def test_unchanged_copy_and_copy_already_equal_to_new_content_do_not_stop(self):
        template = ".github/pull_request_template.md"
        # A change already reflected in repo-baseline: the file equals the new content, not the record.
        self.two_files((apply_baseline.HERE / template).read_text())
        self.assertEqual(self.run_main(), (0, ""))
        self.assertEqual((self.project / CHECKER).read_bytes(), (apply_baseline.HERE / SOURCE).read_bytes())

    def test_deleted_target_and_existing_file_without_record_stop(self):
        template = ".github/pull_request_template.md"
        self.two_files("old\n")
        (self.project / template).unlink()
        code, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn(template + " (deleted)", err)
        self.assertFalse((self.project / template).exists())
        # First adoption over a file the project already had.
        self.write_manifest({"files": {CHECKER: {"source": SOURCE}}})
        code, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn(CHECKER + " (exists, no recorded sha256)", err)
        self.assertEqual((self.project / CHECKER).read_text(), "old\n")

    def test_edited_generated_dependabot_config_stops(self):
        target = ".github/dependabot.yml"
        ecosystems = [{"package-ecosystem": "cargo", "directory": "/"}]
        self.write_manifest({"files": {target: {"source": "templates/github/dependabot.yml", "ecosystems": ecosystems}}})
        self.assertEqual(self.run_main(), (0, ""))
        text = (self.project / target).read_text()
        (self.project / target).write_text(text.replace('"10:00"', '"09:00"'))
        code, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn(target + " (differs from recorded sha256)", err)
        self.assertIn('"09:00"', (self.project / target).read_text())

    def test_unknown_flag_is_rejected(self):
        code, err = self.run_main("--yes")
        self.assertEqual(code, 2)
        self.assertIn("Usage:", err)

    def test_dirty_source_unknown_source_and_escaping_target_fail(self):
        with patch.object(apply_baseline, "git", lambda *args: " M scripts/x.py"):
            with self.assertRaisesRegex(ValueError, "Commit repo-baseline"):
                apply_baseline.apply(self.project)
        for files in [{"x.py": {"source": "missing.py"}}, {"x.py": {"source": "/etc/hosts"}},
                      {"x.py": {"source": "../outside.py"}}, {"../x.py": {"source": SOURCE}},
                      {".git/hooks/pre-commit": {"source": SOURCE}}, {"sub/.GIT/x.py": {"source": SOURCE}}, {}]:
            with self.subTest(files=files):
                self.write_manifest({"files": files})
                with self.assertRaises(ValueError):
                    apply_baseline.apply(self.project, check=True)

    def test_target_through_symlinked_folder_into_git_fails(self):
        (self.project / ".git" / "hooks").mkdir(parents=True)
        (self.project / "hooks").symlink_to(".git/hooks")
        self.write_manifest({"files": {"hooks/pre-commit": {"source": SOURCE}}})
        with self.assertRaisesRegex(ValueError, "inside .git"):
            apply_baseline.apply(self.project, check=True)
        self.assertFalse((self.project / ".git" / "hooks" / "pre-commit").exists())

    def test_dependabot_config_is_generated_per_ecosystem(self):
        target = ".github/dependabot.yml"
        ecosystems = [{"package-ecosystem": "cargo", "directory": "/services/api"}]
        self.write_manifest({"files": {target: {"source": "templates/github/dependabot.yml", "ecosystems": ecosystems}}})
        with patch.object(apply_baseline, "git", fake_git):
            apply_baseline.apply(self.project)
        text = (self.project / target).read_text()
        self.assertTrue(text.startswith((apply_baseline.HERE / "templates/github/dependabot.yml").read_text()))
        self.assertIn("  - package-ecosystem: cargo\n    directory: /services/api\n", text)
        self.assertEqual(text.count("interval: weekly"), 2)
        self.assertIn("      minor-and-patch:\n        update-types: [minor, patch]\n", text)
        self.assertEqual(apply_baseline.apply(self.project, check=True), [])
        (self.project / target).write_text(text.replace('"10:00"', '"09:00"'))
        self.assertEqual(apply_baseline.apply(self.project, check=True), [target])

    def test_invalid_ecosystems_fail(self):
        bad = [{"package-ecosystem": "github-actions", "directory": "/"},
               {"package-ecosystem": "npm", "directory": "/\n  labels: []"},
               {"package-ecosystem": "npm"}]
        for item in bad + [None]:
            with self.subTest(item=item):
                ecosystems = [item] if item is not None else [bad[1] | {"directory": "/a"}] * 2
                self.write_manifest({"files": {".github/dependabot.yml":
                                               {"source": "templates/github/dependabot.yml", "ecosystems": ecosystems}}})
                with self.assertRaisesRegex(ValueError, "Invalid ecosystems"):
                    apply_baseline.apply(self.project, check=True)

    def test_ignored_file_named_like_a_pathspec_is_not_tracked(self):
        # Without --literal-pathspecs, ":(exclude)…" matched other tracked files and passed.
        folder = Path(tempfile.mkdtemp(prefix=":(exclude)", dir=apply_baseline.HERE))
        self.addCleanup(shutil.rmtree, folder)  # only the folder this test created
        source = f"{folder.name}/__pycache__/payload.py"
        (folder / "__pycache__").mkdir()
        (apply_baseline.HERE / source).write_text("payload\n")
        self.write_manifest({"files": {"x.py": {"source": source}}})
        with self.assertRaisesRegex(ValueError, "not tracked"):
            apply_baseline.apply(self.project, check=True)

    def test_untracked_source_and_symlinked_manifest_fail(self):
        def untracked(*args):
            raise subprocess.CalledProcessError(1, ["git", *args])
        with patch.object(apply_baseline, "git", untracked):
            with self.assertRaisesRegex(ValueError, "not tracked"):
                apply_baseline.apply(self.project, check=True)
        with tempfile.TemporaryDirectory() as other:
            target = Path(other) / "repo-baseline.json"
            manifest = self.project / apply_baseline.MANIFEST
            target.write_text(manifest.read_text())
            manifest.unlink()
            manifest.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "regular file inside"):
                apply_baseline.apply(self.project, check=True)



class BlockTests(unittest.TestCase):
    """The ops block in AGENTS.md, written with tools/check_ops.py ops_block()."""

    AGENTS = "# app\n\n## 작업 방식\n\n- 규칙\n\n### ops\n\n- 옛 문구\n\n## 하지 않는 것\n\n- 없음\n"

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.project = Path(folder.name)
        (self.project / ".github").mkdir()
        (self.project / "AGENTS.md").write_text(self.AGENTS, encoding="utf-8")
        self.manifest({"ops": {"target": "AGENTS.md", "exclude": {"Cloudflare": "웹 도메인이 없다"}}})

    def manifest(self, blocks):
        (self.project / apply_baseline.MANIFEST).write_text(json.dumps({"blocks": blocks}, ensure_ascii=False))

    def agents(self):
        return (self.project / "AGENTS.md").read_text(encoding="utf-8")

    def apply(self, **kwargs):
        with patch.object(apply_baseline, "git", fake_git):
            return apply_baseline.apply(self.project, **kwargs)

    def test_unmarked_section_stops_until_forced_then_matches_check_ops(self):
        with self.assertRaisesRegex(ValueError, "no markers"):
            self.apply()
        self.assertEqual(self.agents(), self.AGENTS)
        self.assertEqual(self.apply(force=True), ["AGENTS.md#ops"])
        text = self.agents()
        self.assertNotIn("옛 문구", text)
        self.assertTrue(text.startswith("# app\n\n## 작업 방식\n\n- 규칙\n\n" + apply_baseline.OPS.BEGIN))
        self.assertTrue(text.endswith(apply_baseline.OPS.END + "\n\n## 하지 않는 것\n\n- 없음\n"))
        readme = (apply_baseline.HERE / "profiles/ops/README.md").read_text(encoding="utf-8")
        self.assertEqual(apply_baseline.OPS.check(self.project, readme), [])
        self.assertEqual(self.apply(check=True), [])

    def test_block_is_added_to_work_section_when_there_is_none(self):
        (self.project / "AGENTS.md").write_text("# app\n\n## 작업 방식\n\n- 규칙\n\n## 하지 않는 것\n", encoding="utf-8")
        self.apply(force=True)
        text = self.agents()
        self.assertLess(text.index("- 규칙"), text.index(apply_baseline.OPS.BEGIN))
        self.assertLess(text.index(apply_baseline.OPS.END), text.index("## 하지 않는 것"))

    def test_edit_inside_block_stops_and_outside_is_kept(self):
        self.apply(force=True)
        (self.project / "AGENTS.md").write_text(self.agents() + "\n- 프로젝트 줄\n", encoding="utf-8")
        self.assertEqual(self.apply(), [])
        self.assertTrue(self.agents().endswith("- 프로젝트 줄\n"))
        edited = self.agents().replace("감시 대상 변경은", "감시 대상은")
        (self.project / "AGENTS.md").write_text(edited, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from recorded sha256"):
            self.apply()
        self.assertEqual(self.apply(check=True), ["AGENTS.md#ops"])

    def test_invalid_blocks_stop(self):
        for blocks in ({"ops": {"target": "AGENTS.md", "exclude": {"Datadog": "x"}}},
                       {"pstack": {"target": "AGENTS.md"}},
                       {"ops": {"target": "MISSING.md"}},
                       {"ops": {"target": "../AGENTS.md"}}):
            self.manifest(blocks)
            with self.assertRaises(ValueError):
                self.apply(force=True)

if __name__ == "__main__":
    unittest.main()
