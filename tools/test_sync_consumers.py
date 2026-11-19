"""sync_only(): the deterministic proof that replaces a review for sync PRs."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_consumers  # noqa: E402
from sync_consumers import sync_only  # noqa: E402

OPS = sync_consumers.apply_baseline.OPS
README = (sync_consumers.HERE / "profiles/ops/README.md").read_text(encoding="utf-8")
BLOCK = OPS.ops_block(README, {})
MANIFEST = sync_consumers.apply_baseline.MANIFEST
HEAD_MANIFEST = {"files": {".github/pull_request_template.md": {}}, "blocks": {"ops": {"target": "AGENTS.md"}}}


def agents(block, tail="- 프로젝트 줄\n"):
    return "# app\n\n## 작업 방식\n\n" + block + "\n" + tail


class SyncOnlyTest(unittest.TestCase):
    def reasons(self, changed, base, head, manifest=HEAD_MANIFEST):
        base = {MANIFEST: "{}", **base}
        head = {MANIFEST: json.dumps(manifest), **head}
        return sync_only(changed, manifest, base, head)

    def test_block_and_recorded_file_changes_are_sync_only(self):
        old = BLOCK.replace("감시 대상 변경은", "감시 대상은")
        self.assertEqual(self.reasons([MANIFEST, "AGENTS.md", ".github/pull_request_template.md"],
                                      {"AGENTS.md": agents(old)}, {"AGENTS.md": agents(BLOCK)}), [])

    def test_change_outside_the_block_is_not(self):
        reasons = self.reasons(["AGENTS.md"], {"AGENTS.md": agents(BLOCK)},
                               {"AGENTS.md": agents(BLOCK, tail="- 다른 줄\n")})
        self.assertEqual(reasons, ["AGENTS.md changes outside its block"])

    def test_migration_unmanaged_and_sensitive_paths_are_not(self):
        reasons = sync_only([MANIFEST, "src/app.py", ".github/workflows/ci.yml"], HEAD_MANIFEST,
                            {MANIFEST: None}, {MANIFEST: json.dumps(HEAD_MANIFEST)})
        self.assertEqual(reasons, ["base has no manifest (migration)", ".github/workflows/ci.yml is sensitive",
                                   "src/app.py is not managed"])

    def test_base_without_markers_is_not(self):
        reasons = self.reasons(["AGENTS.md"], {"AGENTS.md": "### ops\n- 옛 문구\n"}, {"AGENTS.md": agents(BLOCK)})
        self.assertEqual(reasons, ["AGENTS.md changes outside its block"])

    def test_standing_order_is_declared(self):
        config = json.loads(sync_consumers.CONSUMERS.read_text(encoding="utf-8"))
        self.assertEqual(config["enqueue"], "sync-only")
        for consumer in config["consumers"]:
            self.assertRegex(consumer["repo"], r"^minjunkim-labs/[A-Za-z0-9._-]+$")
            for entry in consumer["manifest"].get("blocks", {}).values():
                OPS.ops_block(README, entry.get("exclude", {}))  # every exclusion names a table tool


if __name__ == "__main__":
    unittest.main()
