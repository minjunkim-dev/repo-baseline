"""Which review statuses a pull request head needs, from its changed paths."""

import base64
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_review_status as tool


def api(files, statuses=(), author="alice", commits=("alice",), project=None, changed=None):
    pull = {"user": {"login": author}, "changed_files": len(files) if changed is None else changed}
    routes = {
        "repos/o/n/pulls/1": pull,
        "repos/o/n/pulls/1/files?per_page=100": [files],
        "repos/o/n/pulls/1/commits?per_page=100": [[{"author": {"login": name}} for name in commits]],
        "repos/o/n/commits/HEAD/status": {
            "statuses": [{"context": context, "state": state} for context, state in statuses]},
    }
    if project is not None:
        routes[f"repos/o/n/contents/{tool.PROJECT_PATHS}?ref=BASE"] = {
            "content": base64.b64encode(project.encode()).decode()}

    def read(endpoint):
        if endpoint not in routes:
            raise subprocess.CalledProcessError(1, "gh", stderr="gh: Not Found (HTTP 404)")
        return routes[endpoint]
    return read


def run(read):
    return tool.missing("o/n", "1", "HEAD", "BASE", read)


OK = (tool.INDEPENDENT, "success")
BUMP = "@@ -1 +1 @@\n-  uses: actions/checkout@aaaaaaa # v1.0.0\n+  uses: actions/checkout@bbbbbbb # v1.1.0"


class ReviewStatusTests(unittest.TestCase):
    def test_every_pull_request_needs_the_independent_review(self):
        files = [{"filename": "src/app.py"}]
        self.assertEqual(run(api(files)), [tool.INDEPENDENT])
        self.assertEqual(run(api(files, [OK])), [])
        self.assertEqual(run(api(files, [(tool.INDEPENDENT, "failure")])), [tool.INDEPENDENT])

    def test_trust_boundary_paths_also_need_security(self):
        for path in (".github/workflows/ci.yml", "api/.env.local", "svc/Dockerfile", "web/package-lock.json",
                     ".claude/skills/x/SKILL.md", ".mcp.json", tool.PROJECT_PATHS):
            with self.subTest(path=path):
                self.assertEqual(run(api([{"filename": path}], [OK])), [tool.SECURITY])
                self.assertEqual(run(api([{"filename": path}], [OK, (tool.SECURITY, "success")])), [])

    def test_renaming_a_file_out_of_a_trust_boundary_path_still_counts(self):
        files = [{"filename": "docs/x.yml", "previous_filename": ".github/workflows/x.yml"}]
        self.assertEqual(run(api(files, [OK])), [tool.SECURITY])

    def test_project_paths_come_from_the_base_commit(self):
        files = [{"filename": "src/auth/login.py"}]
        self.assertEqual(run(api(files, [OK], project="# comment\nsrc/auth/**\n")), [tool.SECURITY])
        self.assertEqual(run(api(files, [OK], project="src/billing/**\n")), [])

    def test_more_files_than_the_api_lists_needs_security(self):
        self.assertEqual(run(api([{"filename": "src/app.py"}], [OK], changed=5000)), [tool.SECURITY])

    def test_dependabot_version_bump_is_not_a_trust_boundary_change(self):
        files = [{"filename": ".github/workflows/ci.yml", "patch": BUMP},
                 {"filename": "package.json", "patch": '@@ -1 +1 @@\n-  "x": "^1.2.3",\n+  "x": "^1.3.0",'}]
        bot = tool.DEPENDABOT
        self.assertEqual(run(api(files, [OK], author=bot, commits=[bot])), [])

    def test_anything_else_in_a_dependabot_pull_request_needs_security(self):
        bot = tool.DEPENDABOT
        cases = {
            "other author": (api([{"filename": "package.json", "patch": "@@\n-1.0.0\n+1.1.0"}], [OK]),),
            "added commit": (api([{"filename": ".github/workflows/ci.yml", "patch": BUMP}], [OK],
                                 author=bot, commits=[bot, "alice"]),),
            "other line": (api([{"filename": "package.json", "patch": '@@\n-"x": "1.0.0"\n+"y": "1.0.0"'}], [OK],
                               author=bot, commits=[bot]),),
            "added line": (api([{"filename": "package.json", "patch": '@@\n+"y": "1.0.0"'}], [OK],
                               author=bot, commits=[bot]),),
            "workflow line": (api([{"filename": ".github/workflows/ci.yml", "patch": "@@\n-run: a 1\n+run: a 2"}], [OK],
                                  author=bot, commits=[bot]),),
            "no patch": (api([{"filename": "package-lock.json"}], [OK], author=bot, commits=[bot]),),
            "other path": (api([{"filename": "Dockerfile", "patch": "@@\n-FROM a:1\n+FROM a:2"}], [OK],
                               author=bot, commits=[bot]),),
        }
        for name, (read,) in cases.items():
            with self.subTest(name):
                self.assertEqual(run(read), [tool.SECURITY])

    def test_cli_exit_codes(self):
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": "HEAD", "BASE_SHA": "BASE"}
        self.assertEqual(tool.main(env, api([{"filename": "a"}], [OK])), 0)
        self.assertEqual(tool.main(env, api([{"filename": "a"}])), 1)

        def broken(endpoint):
            raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 403")
        self.assertEqual(tool.main(env, broken), 2)
        self.assertEqual(tool.main({}, api([])), 2)


if __name__ == "__main__":
    unittest.main()
