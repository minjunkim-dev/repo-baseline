"""Validate a real clean source snapshot and copied tests in disposable projects."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from test_github_settings import BASELINE, advanced


class DistributionTests(unittest.TestCase):
    def run_command(self, *args, cwd, expected=0):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def test_own_dependabot_config_matches_the_template(self):
        own = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8").splitlines()
        template = (ROOT / "templates/dependabot.yml").read_text(encoding="utf-8").splitlines()
        self.assertEqual(own[1:], template[1:])

    def test_fresh_install_copied_tests_provenance_drift_and_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            source.mkdir()
            # Snapshot the working copy, including new files, without modifying the real Git index.
            paths = self.run_command("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", cwd=ROOT)
            for name in set(paths.split("\0")) - {""}:
                path = ROOT / name
                if path.is_file():
                    target = source / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
            self.run_command("git", "init", "--quiet", cwd=source)
            self.run_command("git", "add", ".", cwd=source)
            self.run_command("git", "-c", "user.name=Baseline test", "-c", "user.email=test@example.invalid",
                             "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                             "commit", "--quiet", "-m", "Fixture snapshot", cwd=source)
            head = self.run_command("git", "rev-parse", "HEAD", cwd=source).strip()
            for mode in ("default", "advanced", "unsupported"):
                with self.subTest(mode=mode):
                    project = root / mode
                    (project / ".github").mkdir(parents=True)
                    shutil.copyfile(source / "templates/repo-baseline.json", project / ".github/repo-baseline.json")
                    apply = (sys.executable, str(source / "tools/apply_baseline.py"), str(project))
                    self.run_command(*apply, cwd=source)
                    manifest = json.loads((project / ".github/repo-baseline.json").read_text())
                    self.assertEqual(manifest["source_commit"], head)
                    profile = copy.deepcopy(BASELINE)
                    if mode == "advanced":
                        profile = advanced(profile)
                        workflow = project / profile["expected"]["codeql_main_source"]["path"]
                        workflow.parent.mkdir(parents=True)
                        data = ("steps:\n  - uses: github/codeql-action/analyze@" + "a" * 40 + "\n").encode()
                        workflow.write_bytes(data)
                        profile["expected"]["codeql_main_source"]["sha"] = hashlib.sha1(
                            b"blob %d\0" % len(data) + data).hexdigest()
                    elif mode == "unsupported":
                        del profile["expected"]["codeql"]
                        del profile["expected"]["protection"]
                        profile["exceptions"] = {name: {
                            "status": "unsupported", "reason": "Synthetic unavailable feature",
                            "evidence": "Offline distribution test fixture",
                        } for name in ("codeql", "protection")}
                    (project / ".github/repository-settings.json").write_text(json.dumps(profile))
                    self.run_command(sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py", cwd=project)
                    checker = project / "scripts/check_repo_baseline.py"
                    self.run_command(sys.executable, str(checker), cwd=project)
                    self.run_command(*apply, "--check", cwd=source)
                    checker.write_text(checker.read_text() + "\n# drift probe\n")
                    self.run_command(sys.executable, str(checker), cwd=project, expected=1)
                    self.run_command(*apply, "--check", cwd=source, expected=1)
                    self.run_command(*apply, cwd=source)
                    self.run_command(sys.executable, str(checker), cwd=project)
                    # Consumer CI must detect a CodeQL workflow edit independently of the copy hashes.
                    if mode == "advanced":
                        workflow.write_bytes(data + b"# stale workflow pin\n")
                        self.run_command(sys.executable, "-m", "unittest", "discover", "-s", "scripts",
                                         "-p", "test_github_settings.py", cwd=project, expected=1)


class TrustBoundaryPathTests(unittest.TestCase):
    def test_policy_codeowners_and_review_check_list_the_same_common_paths(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_review_status import COMMON_PATHS
        owners = [line.split()[0].lstrip("/") for line in (ROOT / "templates/CODEOWNERS").read_text().splitlines()
                  if line.strip() and not line.startswith("#")]
        self.assertEqual(sorted(path.removesuffix("**") for path in COMMON_PATHS), sorted(owners))
        row = next(line for line in (ROOT / "POLICY.md").read_text().splitlines() if line.startswith("| 공통 경로 |"))
        for path in COMMON_PATHS:
            self.assertIn(f"`{path}`", row)

    def test_owner_approval_paths_match_policy_section_10(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_review_status import ONE_WAY_PATHS, TEAM_LINE
        text = (ROOT / "POLICY.md").read_text(encoding="utf-8")
        section = text.split("## 10. 문 판정", 1)[1]
        for path in ONE_WAY_PATHS:
            self.assertIn(f"`{path}`", section)
        self.assertIn(TEAM_LINE, text.split("## 9. 프로필", 1)[1].split("## 10.", 1)[0])

    def test_review_status_workflow_does_not_rerun_on_comments(self):
        text = (ROOT / "templates/review-status.yml").read_text(encoding="utf-8")
        policy = (ROOT / "templates/review-status-policy.json").read_text(encoding="utf-8")
        on_block = text.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertNotIn("issue_comment", on_block)
        self.assertIn("pull_request_target:", on_block)
        self.assertNotIn("scripts/rerun_review_status.py", text)
        self.assertIn("types: [opened, synchronize, reopened, ready_for_review, edited]", text)
        self.assertIn("pull_request_target:\n    branches: [main]\n", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertNotIn("github.event.pull_request.head.ref", text)
        self.assertNotIn("github.event.comment.body", text)
        self.assertNotIn("actions: write", text)
        self.assertNotIn("checks: write", text)
        self.assertNotIn("contents: write", text)
        self.assertEqual(text, (ROOT / ".github/workflows/review-status.yml").read_text(encoding="utf-8"))
        self.assertNotIn("ref: ${{ github.event.pull_request.head.sha }}", text)
        self.assertIn("does not subscribe to issue_comment", text)
        self.assertIn('"issue_comment"', policy)
        self.assertIn('"pull_request_target"', policy)
        conventions = (ROOT / "templates/pr-policy.yml").read_text(encoding="utf-8")
        self.assertEqual(conventions, (ROOT / ".github/workflows/pr-policy.yml").read_text(encoding="utf-8"))
        self.assertNotIn("\n  pull_request_target:", conventions)
        self.assertIn("\n  pull_request:", conventions)
        self.assertIn("types: [opened, edited, synchronize, reopened, ready_for_review]", conventions)
        self.assertIn("pull_request:\n    branches: [main]\n", conventions)
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", conventions)
        self.assertIn("if [ -f policy-base/scripts/workflow_policy.py ]; then", conventions)
        self.assertIn('python3 "$checker" --pr --root policy-head', conventions)
        self.assertNotIn("github.event.pull_request.head.sha", conventions)
        protected = json.loads((ROOT / ".github/workflow-policy.json").read_text(encoding="utf-8"))["protected_paths"]
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_review_status import ONE_WAY_PATHS, COMMON_PATHS, matches
        for path in ("scripts/workflow_policy.py", "scripts/pr_author.py", ".github/workflow-policy.json"):
            self.assertIn(path, protected)
            self.assertTrue(matches(path, ONE_WAY_PATHS))
            self.assertTrue(matches(path, COMMON_PATHS))

    def test_a_policy_that_excludes_review_status_is_not_a_parent_block(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 tools/review_status_policy.py", readme)
        self.assertNotIn("def inc:", readme)
        excluded = {
            "enforcement": "active",
            "source_type": "Organization",
            "conditions": {"workflow_path": {
                "include": ["~ALL"],
                "exclude": [".github/workflows/review-status.yml"],
            }},
            "rules": [{"type": "restrict_action_events", "parameters": {"allowed_events": ["pull_request_target"]}}],
        }
        self.assertEqual(self.policy_kind(excluded), "other")
        empty = json.loads(json.dumps(excluded))
        empty["conditions"]["workflow_path"]["include"] = []
        self.assertEqual(self.policy_kind(empty), "other")
        blocked = json.loads(json.dumps(excluded))
        blocked["conditions"]["workflow_path"]["exclude"] = []
        self.assertEqual(self.policy_kind(blocked), "parent")
        globbed = json.loads(json.dumps(blocked))
        globbed["conditions"]["workflow_path"]["include"] = [".github/workflows/**"]
        self.assertEqual(self.policy_kind(globbed), "parent")

    def policy_kind(self, policy):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/review_status_policy.py")],
            input=json.dumps(policy), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
