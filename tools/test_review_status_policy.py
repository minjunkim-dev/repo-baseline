"""Event-policy classification, including workflow_path globs."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import review_status_policy as policy
from tools import rerun_review_status as rerun

TARGET = policy.TARGET


def rule(events):
    return [{"type": "restrict_action_events", "parameters": {"allowed_events": events}}]


def sample(include, exclude=None, events=None, source="Organization"):
    return {
        "enforcement": "active",
        "source_type": source,
        "conditions": {"workflow_path": {"include": include, "exclude": exclude or []}},
        "rules": rule(events or ["pull_request_target"]),
    }


class PolicyTests(unittest.TestCase):
    def test_a_directory_glob_that_allows_only_pull_request_target_stops_the_install(self):
        for pattern in (".github/workflows/**", ".github/workflows/*", "**", "**.yml"):
            with self.subTest(pattern=pattern):
                self.assertEqual(policy.classify(sample([pattern])), "parent")

    def test_a_star_does_not_cross_a_slash(self):
        self.assertEqual(policy.classify(sample([".github/*"])), "other")
        self.assertTrue(policy.matches(".github/workflows/review-status.yml?", TARGET))
        self.assertFalse(policy.matches(".github/workflows/review-status.ym?", TARGET))

    def test_a_glob_that_allows_both_events_is_already_enough(self):
        both = ["issue_comment", "pull_request_target"]
        self.assertEqual(policy.classify(sample([".github/workflows/**"], events=both)), "both")

    def test_exclude_glob_does_not_make_an_all_workflows_policy_apply(self):
        item = sample(["~ALL"], exclude=[".github/workflows/**"])
        self.assertEqual(policy.classify(item), "other")
        item["conditions"]["workflow_path"]["include"] = []
        self.assertEqual(policy.classify(item), "other")

    def test_exact_repository_policy_can_be_updated(self):
        item = sample([TARGET], source="Repository")
        self.assertEqual(policy.classify(item), "narrow")

    def test_an_unevaluable_pattern_is_not_treated_as_absent(self):
        with self.assertRaises(policy.UnrecognizedPattern):
            policy.classify(sample([".github/workflows/review-status.[yml"]))

    def test_cli_stops_on_an_unevaluable_pattern(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[1] / "tools/review_status_policy.py")],
            input=json.dumps(sample([".github/workflows/{review-status.yml}"])),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


class RerunCommandTests(unittest.TestCase):
    def run_main(self, number, sha, pages):
        calls = []

        def execute(command, input=None):
            calls.append((list(command), input))

            class Result:
                stdout = sha + "\n"

            return Result()

        env = {"PR_NUMBER": str(number), "REPO": "owner/repo"}
        code = rerun.main(env, execute, pages=pages)
        return code, calls

    def test_a_fork_head_is_re_run_and_a_fork_author_is_not(self):
        fork = "a" * 40
        pages = [[
            {"id": 8, "status": "completed", "head_sha": "b" * 40, "pull_requests": []},
            {"id": 9, "status": "completed", "head_sha": fork, "pull_requests": []},
        ]]
        code, calls = self.run_main(4, fork, pages)
        self.assertEqual(code, 0)
        self.assertEqual(calls[1][0], ["gh", "run", "rerun", "9", "--repo", "owner/repo"])
        self.assertFalse(rerun.comment_triggers(True, "open", "fork-user", "owner"))

    def test_a_concurrent_push_waits_instead_of_re_running_the_old_head(self):
        pages = [[
            {"id": 2, "status": "in_progress", "head_sha": "c" * 40, "pull_requests": []},
            {"id": 1, "status": "completed", "head_sha": "d" * 40, "pull_requests": []},
        ]]
        code, calls = self.run_main(7, "c" * 40, pages)
        self.assertEqual(code, 2)
        self.assertEqual(len(calls), 1)

    def test_editing_or_deleting_the_approval_re_runs_the_completed_run(self):
        sha = "e" * 40
        pages = [[{"id": 5, "status": "completed", "head_sha": sha, "pull_requests": []}]]
        for _name in ("edited", "deleted"):
            code, calls = self.run_main(1, sha, pages)
            self.assertEqual(code, 0)
            self.assertEqual(calls[1][0][3], "5")
        self.assertTrue(rerun.comment_triggers(True, "open", "owner", "owner"))

    def test_a_run_past_the_page_cap_posts_a_failing_review_status_check(self):
        filler = {"id": 1, "status": "completed", "head_sha": "f" * 40, "pull_requests": []}
        code, calls = self.run_main(1, "d" * 40, [[filler] * 100])
        self.assertEqual(code, 1)
        posted = calls[1]
        self.assertIn("check-runs", " ".join(posted[0]))
        body = json.loads(posted[1])
        self.assertEqual(body["name"], "Review status")
        self.assertEqual(body["head_sha"], "d" * 40)
        self.assertEqual(body["conclusion"], "failure")
        self.assertNotIn("review/independent", posted[1])
        self.assertNotIn("review/security", posted[1])


class RerunTests(unittest.TestCase):
    def test_a_fork_pull_request_run_is_selected_by_its_head(self):
        fork = "a" * 40
        runs = [
            {"id": 8, "status": "completed", "head_sha": "b" * 40, "pull_requests": []},
            {"id": 9, "status": "completed", "pull_requests": [{"number": 4, "head": {"sha": fork}}]},
        ]
        self.assertEqual(rerun.plan(runs, 4, fork), ("rerun", 9))
        self.assertFalse(rerun.comment_triggers(True, "open", "fork-user", "owner"))
        self.assertTrue(rerun.comment_triggers(True, "open", "owner", "owner"))

    def test_a_newer_push_is_not_satisfied_by_the_previous_head(self):
        runs = [
            {"id": 2, "status": "in_progress", "head_sha": "NEW", "pull_requests": []},
            {"id": 1, "status": "completed", "head_sha": "OLD", "pull_requests": []},
        ]
        self.assertEqual(rerun.plan(runs, 7, "NEW"), ("wait", None))
        self.assertEqual(rerun.plan(runs, 7, "OLD"), ("rerun", 1))

    def test_an_edited_or_deleted_approval_re_runs_the_completed_run(self):
        sha = "c" * 40
        runs = [{"id": 5, "status": "completed", "head_sha": sha, "pull_requests": []}]
        self.assertEqual(rerun.plan(runs, 1, sha), ("rerun", 5))
        self.assertTrue(rerun.comment_triggers(True, "open", "owner", "owner"))
        self.assertFalse(rerun.comment_triggers(True, "closed", "owner", "owner"))

    def test_a_missing_run_asks_for_a_failing_check_on_that_head(self):
        self.assertEqual(rerun.plan([], 1, "d" * 40), ("missing", None))
        body = rerun.fail_closed_body("d" * 40)
        self.assertEqual(body["name"], "Review status")
        self.assertEqual(body["conclusion"], "failure")
        self.assertNotIn("review/independent", json.dumps(body))
        pages = [[{"id": 1, "status": "completed", "pull_requests": []}] * 100]
        _runs, complete = rerun.collect(pages)
        self.assertFalse(complete)


if __name__ == "__main__":
    unittest.main()
