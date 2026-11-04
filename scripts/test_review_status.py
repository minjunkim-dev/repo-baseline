"""Which review statuses a pull request head needs, from its changed paths."""

import base64
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_review_status as tool


def api(files, statuses=(), author="alice", commits=("alice",), project=None, changed=None, verified=True,
        committer=tool.WEB_FLOW, commit_shas=None, extra_status=None, force_pushes=None):
    pull = {"user": {"login": author}, "changed_files": len(files) if changed is None else changed}
    routes = {
        "repos/o/n/pulls/1": pull,
        "repos/o/n/pulls/1/files?per_page=100": [files],
        "repos/o/n/pulls/1/commits?per_page=100": [[{"author": {"login": name}, "committer": {"login": committer},
                                                    "commit": {"verification": {"verified": verified}}} for name in commits]],
        "repos/o/n/commits/HEAD/status?per_page=100": [{
            "statuses": [{"context": context, "state": state} for context, state in statuses]}],
    }
    if project is not None:
        routes[f"repos/o/n/contents/{tool.PROJECT_PATHS}?ref=BASE"] = {
            "content": base64.b64encode(project.encode()).decode()}
    if commit_shas is not None:
        names = list(commits)
        routes["repos/o/n/pulls/1/commits?per_page=100"] = [[{
            "sha": sha, "author": {"login": names[index] if index < len(names) else author},
            "committer": {"login": committer}, "commit": {"verification": {"verified": verified}},
        } for index, sha in enumerate(commit_shas)]]
    if extra_status:
        for sha, pairs in extra_status.items():
            routes[f"repos/o/n/commits/{sha}/status?per_page=100"] = [{
                "statuses": [{"context": context, "state": state} for context, state in pairs]}]
    if force_pushes is not None:
        routes[tool.FORCE_PUSHES + "o/n/1"] = list(force_pushes)

    def read(endpoint):
        if endpoint not in routes:
            raise subprocess.CalledProcessError(1, "gh", stderr="gh: Not Found (HTTP 404)")
        return routes[endpoint]
    return read


def run(read):
    return tool.missing("o/n", "1", "HEAD", "BASE", read)


OK = (tool.INDEPENDENT, "success")
BUMP = "@@ -1 +1 @@\n-  uses: actions/checkout@aaaaaaa # v1.0.0\n+  uses: actions/checkout@bbbbbbb # v1.1.0"
ADDED = """diff --git a/src/app.py b/src/app.py
index 1111111..2222222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
 def f():
     return 1
+    return 2
"""
SHIFTED = """diff --git a/src/app.py b/src/app.py
index aaaaaaa..bbbbbbb 100644
--- a/src/app.py
+++ b/src/app.py
@@ -20,3 +20,4 @@
 def f():
     return 0
+    return 2
"""


def diffs(mapping):
    def read_diff(endpoint):
        sha = endpoint.rsplit("...", 1)[-1]
        if sha not in mapping:
            raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 404")
        return mapping[sha]
    return read_diff


class ReviewStatusTests(unittest.TestCase):
    def test_every_pull_request_needs_the_independent_review(self):
        files = [{"filename": "src/app.py"}]
        self.assertEqual(run(api(files)), [tool.INDEPENDENT])
        self.assertEqual(run(api(files, [OK])), [])
        self.assertEqual(run(api(files, [(tool.INDEPENDENT, "failure")])), [tool.INDEPENDENT])

    def test_a_posted_security_failure_blocks_even_when_paths_do_not_need_it(self):
        files = [{"filename": "src/app.py"}]
        self.assertEqual(run(api(files, [OK, (tool.SECURITY, "failure")])), [tool.SECURITY])
        self.assertEqual(run(api(files, [OK, (tool.SECURITY, "success")])), [])

    def test_trust_boundary_paths_also_need_security(self):
        for path in (".github/workflows/ci.yml", ".github/actions/x/action.yml", "scripts/check_review_status.py",
                     ".github/repo-baseline.json", "api/.env.local", "svc/Dockerfile", "web/package-lock.json",
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
        literal = [{"filename": "app/[id]/route.ts"}]
        for spelling in ("app/[id]/**", "app/[id]/route.ts", "/app/[id]/route.ts"):
            with self.subTest(spelling):
                self.assertEqual(run(api(literal, [OK], project=spelling + "\n")), [tool.SECURITY])
        self.assertEqual(run(api([{"filename": "x/[id].ts"}], [OK], project="[id].ts\n")), [tool.SECURITY])
        for spelling in ("/src", "src/auth", "src/auth/", "/src/auth/", "/src/auth/**"):
            with self.subTest(spelling):
                self.assertEqual(run(api(files, [OK], project=spelling + "\n")), [tool.SECURITY])

    def test_more_files_than_the_api_lists_needs_security(self):
        self.assertEqual(run(api([{"filename": "src/app.py"}], [OK], changed=5000)), [tool.SECURITY])

    def test_dependabot_version_bump_is_not_a_trust_boundary_change(self):
        files = [{"filename": ".github/workflows/ci.yml", "patch": BUMP},
                 {"filename": "package.json", "patch": '@@ -1 +1 @@\n-  "x": "^1.2.3",\n+  "x": "^1.3.0",'}]
        files.append({"filename": "go.sum", "patch": "@@\n-x/net v0.1.0 h1:abc+/=\n+x/net v0.2.0 h1:xyz9=\n"})
        files.append({"filename": "Cargo.lock", "patch": '@@\n-version = "1.2.3"\n-checksum = "aaaaaaa"\n'
                                                          '+version = "1.3.0"\n+checksum = "bbbbbbb"'})
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
            "amended by a person": (api([{"filename": ".github/workflows/ci.yml", "patch": BUMP}], [OK],
                                        author=bot, commits=[bot], committer="alice"),),
            "forged author": (api([{"filename": ".github/workflows/ci.yml", "patch": BUMP}], [OK],
                                  author=bot, commits=[bot], verified=False),),
            "other action": (api([{"filename": ".github/workflows/ci.yml",
                                   "patch": "@@\n-  uses: owner1/a@aaaaaaa\n+  uses: owner2/a@bbbbbbb"}], [OK],
                                 author=bot, commits=[bot]),),
            "other host": (api([{"filename": "package-lock.json",
                                 "patch": "@@\n-https://evil1.example/x-1.0.0.tgz\n+https://evil2.example/x-1.0.0.tgz"}],
                               [OK], author=bot, commits=[bot]),),
            "package name": (api([{"filename": "Cargo.lock", "patch": '@@\n-name = "pkg-2"\n+name = "pkg-3"'}], [OK],
                                 author=bot, commits=[bot]),),
            "package name like a hash": (api([{"filename": "Cargo.lock",
                                               "patch": '@@\n-name = "pkg-1234567"\n+name = "pkg-7654321"'}], [OK],
                                             author=bot, commits=[bot]),),
            "package name with underscore": (api([{"filename": "Cargo.lock", "patch": '@@\n-name = "pkg_2"\n+name = "pkg_3"'}],
                                                 [OK], author=bot, commits=[bot]),),
            "file name": (api([{"filename": "package-lock.json",
                                "patch": "@@\n-https://r/x/-/x-1.0.0.tgz\n+https://r/x/-/x-1.1.0.tgz"}], [OK],
                              author=bot, commits=[bot]),),
            "no patch": (api([{"filename": "package-lock.json"}], [OK], author=bot, commits=[bot]),),
            "other path": (api([{"filename": "Dockerfile", "patch": "@@\n-FROM a:1\n+FROM a:2"}], [OK],
                               author=bot, commits=[bot]),),
        }
        for name, (read,) in cases.items():
            with self.subTest(name):
                self.assertEqual(run(read), [tool.SECURITY])

    def test_dependabot_version_bump_needs_no_independent_review(self):
        bot = tool.DEPENDABOT
        files = [{"filename": ".github/workflows/ci.yml", "patch": BUMP}]
        self.assertEqual(run(api(files, author=bot, commits=[bot])), [])
        self.assertEqual(run(api(files, [(tool.INDEPENDENT, "failure")], author=bot, commits=[bot])), [tool.INDEPENDENT])
        self.assertEqual(run(api(files, [OK, (tool.SECURITY, "failure")], author=bot, commits=[bot])), [tool.SECURITY])

    def test_an_unchanged_diff_reuses_the_prior_success(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, commit_shas=["OLD", "HEAD"], extra_status={"OLD": [OK]})
        same = diffs({"OLD": ADDED, "HEAD": SHIFTED})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, same), [])
        indent = SHIFTED.replace("+    return 2", "+        return 2")
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, diffs({"OLD": ADDED, "HEAD": indent})),
                         [tool.INDEPENDENT])

    def test_a_failure_on_this_head_is_not_replaced_by_an_older_success(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, [(tool.INDEPENDENT, "failure")], commit_shas=["OLD", "HEAD"], extra_status={"OLD": [OK]})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, diffs({"OLD": ADDED, "HEAD": SHIFTED})),
                         [tool.INDEPENDENT])

    def test_a_newer_failed_status_blocks_an_older_match(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, commit_shas=["OLDER", "MID", "HEAD"], extra_status={
            "OLDER": [OK], "MID": [(tool.INDEPENDENT, "failure")]})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, diffs({"OLDER": ADDED, "HEAD": SHIFTED})),
                         [tool.INDEPENDENT])

    def test_a_rebase_parent_can_carry_the_status(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, commit_shas=["HEAD"], force_pushes=["OLD"], extra_status={"OLD": [OK]})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, diffs({"OLD": ADDED, "HEAD": SHIFTED})), [])

    def test_security_reuses_the_same_diff_and_does_not_borrow_a_different_context(self):
        files = [{"filename": ".github/workflows/ci.yml", "patch": "@@\n-run: a\n+run: b"}]
        both = {"OLD": [OK, (tool.SECURITY, "success")]}
        read = api(files, commit_shas=["OLD", "HEAD"], extra_status=both)
        same = diffs({"OLD": ADDED, "HEAD": SHIFTED})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, same), [])
        only_independent = api(files, commit_shas=["OLD", "HEAD"], extra_status={"OLD": [OK]})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", only_independent, same), [tool.SECURITY])

    def test_an_unreadable_newer_status_does_not_fall_through(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, commit_shas=["OLDER", "MID", "HEAD"], extra_status={"OLDER": [OK]})
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, diffs({"OLDER": ADDED, "HEAD": SHIFTED})),
                         [tool.INDEPENDENT])

    def test_an_unreadable_diff_does_not_reuse_a_status(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, commit_shas=["OLD", "HEAD"], extra_status={"OLD": [OK]})

        def boom(endpoint):
            raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 406")
        self.assertEqual(tool.missing("o/n", "1", "HEAD", "BASE", read, boom), [tool.INDEPENDENT])
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": "HEAD", "BASE_SHA": "BASE"}
        self.assertEqual(tool.main(env, read, boom), 1)

    def test_diff_identity_ignores_position_and_keeps_whitespace_and_binary_blobs(self):
        self.assertEqual(tool.diff_identity(ADDED), tool.diff_identity(SHIFTED))
        self.assertNotEqual(tool.diff_identity(ADDED), tool.diff_identity(SHIFTED.replace("+    return 2", "+        return 2")))
        self.assertEqual(tool.diff_identity(""), "empty")
        self.assertIsNone(tool.diff_identity('{"message":"diff too large"}'))
        self.assertIsNone(tool.diff_identity("diff --git a/a b/a\nnot a diff line\n"))
        binary = "diff --git a/a.bin b/a.bin\nindex 1111111..2222222 100644\nBinary files a/a.bin and b/a.bin differ\n"
        other = binary.replace("1111111..2222222", "1111111..3333333")
        self.assertNotEqual(tool.diff_identity(binary), tool.diff_identity(other))
        self.assertIsNone(tool.diff_identity(binary.replace("index 1111111..2222222 100644\n", "")))
        swapped = SHIFTED + ADDED.replace("src/app.py", "src/b.py")
        reverse = ADDED.replace("src/app.py", "src/b.py") + SHIFTED
        self.assertEqual(tool.diff_identity(swapped), tool.diff_identity(reverse))
        removed = ("diff --git a/a.sql b/a.sql\nindex 1111111..2222222 100644\n--- a/a.sql\n+++ b/a.sql\n"
                   "@@ -1 +1 @@\n--- note\n+-- note 2\n")
        self.assertNotEqual(tool.diff_identity(removed), tool.diff_identity(removed.replace("+-- note 2", "+-- note 3")))
        self.assertEqual(tool.diff_identity(removed), tool.diff_identity(removed.replace("--- a/a.sql", "--- a/other")))
        plus = ("diff --git a/a.hs b/a.hs\nindex 1111111..2222222 100644\n--- a/a.hs\n+++ b/a.hs\n"
                "@@ -1 +1 @@\n-x\n+++ x\n")
        self.assertNotEqual(tool.diff_identity(plus), tool.diff_identity(plus.replace("+++ x", "+++ y")))
        one_line = "diff --git a/a b/a\n@@ -1 +1 @@\n+a\u2028+b\n"
        two_lines = "diff --git a/a b/a\n@@ -1 +1 @@\n+a\n+b\n"
        self.assertNotEqual(tool.diff_identity(one_line), tool.diff_identity(two_lines))
        self.assertIsNotNone(tool.diff_identity("diff --git a/a b/a\n@@ -1 +1 @@\n \x0c\n+x\n"))

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
