"""sync_only() and decide(): the deterministic proof that replaces a review for sync PRs."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_consumers  # noqa: E402
from sync_consumers import changelog_since, decide, sync_only  # noqa: E402

OPS = sync_consumers.apply_baseline.OPS
README = (sync_consumers.HERE / "profiles/ops/README.md").read_text(encoding="utf-8")
BLOCK = OPS.ops_block(README, {})
MANIFEST = sync_consumers.apply_baseline.MANIFEST
POLICY = {"files": {".github/pull_request_template.md": {"source": ".github/pull_request_template.md"}},
          "blocks": {"ops": {"target": "AGENTS.md"}}}


def recorded(policy, sha):
    data = json.loads(json.dumps(policy))
    data["source_commit"] = sha * 40
    data["blocks"]["ops"]["sha256"] = sha * 64
    return json.dumps(data)


def agents(block, tail="- 프로젝트 줄\n"):
    return "# app\n\n## 작업 방식\n\n" + block + "\n" + tail


class SyncOnlyTest(unittest.TestCase):
    def reasons(self, changed, base, head, head_policy=POLICY):
        return sync_only(changed, {MANIFEST: recorded(POLICY, "a"), **base}, {MANIFEST: recorded(head_policy, "b"), **head})

    def test_block_and_recorded_file_changes_are_sync_only(self):
        old = BLOCK.replace("감시 대상 변경은", "감시 대상은")
        self.assertEqual(self.reasons([MANIFEST, "AGENTS.md", ".github/pull_request_template.md"],
                                      {"AGENTS.md": agents(old)}, {"AGENTS.md": agents(BLOCK)}), [])

    def test_change_outside_the_block_is_not(self):
        reasons = self.reasons(["AGENTS.md"], {"AGENTS.md": agents(BLOCK)},
                               {"AGENTS.md": agents(BLOCK, tail="- 다른 줄\n")})
        self.assertEqual(reasons, ["AGENTS.md changes outside its block"])

    def test_manifest_policy_change_is_not(self):
        # A new exclusion deletes rules from the consumer; that needs a review.
        wider = json.loads(json.dumps(POLICY))
        wider["blocks"]["ops"]["exclude"] = {"Sentry": "필요 없다"}
        self.assertIn("the manifest changes what is synced (files, blocks or exclude)",
                      self.reasons([MANIFEST], {}, {}, head_policy=wider))
        added = json.loads(json.dumps(POLICY))
        added["files"]["src/app.py"] = {"source": "README.md"}
        reasons = self.reasons([MANIFEST, "src/app.py"], {}, {}, head_policy=added)
        self.assertIn("the manifest changes what is synced (files, blocks or exclude)", reasons)
        self.assertIn("src/app.py is not managed", reasons)
        # A file entry's source decides what is copied, so it is policy, not a record.
        moved = json.loads(json.dumps(POLICY))
        moved["files"][".github/pull_request_template.md"]["source"] = "README.md"
        self.assertIn("the manifest changes what is synced (files, blocks or exclude)",
                      self.reasons([MANIFEST, ".github/pull_request_template.md"], {}, {}, head_policy=moved))

    def test_migration_unmanaged_and_sensitive_paths_are_not(self):
        self.assertEqual(sync_only([MANIFEST], {MANIFEST: None}, {MANIFEST: recorded(POLICY, "b")}),
                         ["base has no manifest (migration)"])
        self.assertEqual(self.reasons(["src/app.py", ".github/workflows/ci.yml"], {}, {}),
                         [".github/workflows/ci.yml is sensitive", "src/app.py is not managed"])
        # Every POLICY §4 path stays with a person even when the manifest manages it.
        for path in [".github/CODEOWNERS", ".claude/settings.json", "app/.cursor/rules.md", ".mcp.json",
                     "web/package.json", "uv.lock", "pnpm-lock.yaml"]:
            self.assertEqual(self.reasons([path], {}, {}), [f"{path} is sensitive"])

    def test_base_without_markers_is_not(self):
        reasons = self.reasons(["AGENTS.md"], {"AGENTS.md": "### ops\n- 옛 문구\n"}, {"AGENTS.md": agents(BLOCK)})
        self.assertEqual(reasons, ["AGENTS.md changes outside its block"])

    def test_changelog_range_takes_only_a_full_sha(self):
        self.assertEqual(changelog_since("--output=/tmp/x"), [])
        self.assertEqual(changelog_since(None), [])

    def test_standing_order_is_declared(self):
        config = json.loads(sync_consumers.CONSUMERS.read_text(encoding="utf-8"))
        self.assertEqual(config["enqueue"], "sync-only")
        for consumer in config["consumers"]:
            self.assertRegex(consumer["repo"], r"^minjunkim-labs/[A-Za-z0-9._-]+$")
            for entry in consumer["manifest"].get("blocks", {}).values():
                OPS.ops_block(README, entry.get("exclude", {}))  # every exclusion names a table tool


class DecideTest(unittest.TestCase):
    PR = {"author": {"login": "bot"}, "isCrossRepository": False}
    DETAIL = {"statusCheckRollup": [{"conclusion": "SUCCESS"}, {"state": "SKIPPED"}], "reviews": []}

    def decide(self, **changes):
        args = {"user": "bot", "pr": self.PR, "detail": self.DETAIL, "comments": ["coderabbitai[bot]"],
                "threads": 0, "commit_authors": ["bot"], "sync_reasons": [], "check_differs": False}
        args.update(changes)
        return decide(**args)

    def test_clean_sync_pr_is_queued(self):
        self.assertEqual(self.decide(), [])

    def test_each_gate_leaves_it_for_the_owner(self):
        cases = {
            "not opened by this pipeline": {"pr": {"author": {"login": "someone"}, "isCrossRepository": False}},
            "has commits from someone else": {"commit_authors": ["bot", "someone"]},
            "CI not passed": {"detail": {"statusCheckRollup": [{"conclusion": "FAILURE"}], "reviews": []}},
            "has reviews or review threads to judge": {"threads": 1},
            "has comments to judge": {"comments": ["coderabbitai[bot]", "owner"]},
            "head differs from this repo-baseline commit": {"check_differs": True},
            "AGENTS.md changes outside its block": {"sync_reasons": ["AGENTS.md changes outside its block"]},
        }
        for reason, change in cases.items():
            self.assertIn(reason, self.decide(**change), reason)
        self.assertIn("CI not passed", self.decide(detail={"statusCheckRollup": [], "reviews": []}))


if __name__ == "__main__":
    unittest.main()
