"""Exercise the merge queue reviewed-head check."""

import json
import unittest

from reviewed_head import DEPENDABOT, reviewed_head, verdict

HEAD = "a" * 40
OTHER = "b" * 40
REF = f"gh-readonly-queue/main/pr-12-{HEAD}"
MANIFEST = json.dumps({"files": {".github/pull_request_template.md": {}},
                       "blocks": {"ops": {"target": "AGENTS.md"}}})


def body(*heads, author="Claude Code / opus"):
    lines = [f"Author: {author}", "## Review"]
    lines += [f"리뷰한 head와 되돌리기: {head}, 쉬움" for head in heads]
    return "\n".join(lines)


class ReviewedHeadTests(unittest.TestCase):
    def test_matching_head_passes(self):
        self.assertIsNone(verdict(REF, "me@example.invalid", body(HEAD), ["src/a.py"], ""))

    def test_moved_head_fails(self):
        self.assertIn("다릅니다", verdict(REF, "me@example.invalid", body(OTHER), ["src/a.py"], ""))

    def test_last_review_round_wins(self):
        self.assertIsNone(verdict(REF, "x", body(OTHER, HEAD), ["a"], ""))
        self.assertIsNotNone(verdict(REF, "x", body(HEAD, OTHER), ["a"], ""))

    def test_missing_or_placeholder_review_fails(self):
        for text in ["", body(), "리뷰한 head와 되돌리기: <커밋 SHA>, <쉬움 | 어려움>"]:
            with self.subTest(text=text):
                self.assertIn("없습니다", verdict(REF, "x", text, ["a"], ""))

    def test_unreadable_queue_ref_fails(self):
        self.assertIn("읽지 못했습니다", verdict("main", "x", body(HEAD), ["a"], ""))

    def test_dependabot_passes_by_email_only(self):
        self.assertIsNone(verdict(REF, DEPENDABOT, "", ["a"], ""))
        self.assertIsNotNone(verdict(REF, "dependabot[bot]", "", ["a"], ""))

    def test_sync_pr_passes_only_on_managed_paths(self):
        sync = body(author="스크립트 / 없음 (repo-baseline tools/sync_consumers.py)")
        self.assertIsNone(verdict(REF, "x", sync, [".github/repo-baseline.json", "AGENTS.md"], MANIFEST))
        self.assertIsNotNone(verdict(REF, "x", sync, [".github/repo-baseline.json", "src/a.py"], MANIFEST))
        self.assertIsNotNone(verdict(REF, "x", sync, [".github/repo-baseline.json"], ""))
        self.assertIsNotNone(verdict(REF, "x", body(), [".github/repo-baseline.json"], MANIFEST))

    def test_reviewed_head_accepts_backticks_and_crlf(self):
        self.assertEqual(reviewed_head(f"x\r\n리뷰한 head와 되돌리기: `{HEAD}`, 어려움 (이유)\r\n"), HEAD)


if __name__ == "__main__":
    unittest.main()
