"""Layout checks for the redesigned baseline (redesign plan §7: https://github.com/minjunkim-dev/repo-baseline/blob/c3f6d569871f51b83c1405dee34db6850a0b30e3/docs/archive/redesign-2026-11.md)."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ["AGENTS.md", "REVIEW.md", "gitignore", "pull_request_template.md"]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def docs():
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", "graft/")):
            continue
        yield path


class DistributionTests(unittest.TestCase):
    def test_core_is_small_copyable_files_without_python(self):
        core = ROOT / "templates/core"
        self.assertEqual(sorted(p.name for p in core.iterdir()), sorted(CORE))
        self.assertLessEqual(len((core / "AGENTS.md").read_text(encoding="utf-8").splitlines()), 60)

    def test_own_pr_template_is_the_core_template(self):
        self.assertEqual((ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8"),
                         (ROOT / "templates/core/pull_request_template.md").read_text(encoding="utf-8"))

    def test_own_coderabbit_config_is_the_template(self):
        template = (ROOT / "templates/github/.coderabbit.yaml").read_text(encoding="utf-8")
        self.assertEqual((ROOT / ".coderabbit.yaml").read_text(encoding="utf-8"), template)
        self.assertIn('\nlanguage: "ko-KR"\n', template)
        self.assertIn("\ninheritance: true\n", template)

    def test_changelog_fragments_are_one_short_entry(self):
        bad = []
        for path in sorted((ROOT / "changelog.d").iterdir()):
            lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md", path.name) \
                    or not 1 <= len(lines) <= 3 or not lines[0].startswith("- "):
                bad.append(path.name)
        self.assertEqual(bad, [])

    def test_policy_stays_one_page(self):
        self.assertLessEqual(len((ROOT / "POLICY.md").read_text(encoding="utf-8")), 10000)

    def test_relative_links_resolve(self):
        missing = []
        for path in docs():
            for target in LINK.findall(path.read_text(encoding="utf-8")):
                if re.match(r"[a-z]+:", target):
                    continue
                if not (path.parent / target).exists():
                    missing.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_no_model_names_in_core_or_policy(self):
        for rel in ["POLICY.md", "templates/core/AGENTS.md", "templates/core/REVIEW.md"]:
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            for word in ("opus", "sonnet", "composer", "grok"):
                self.assertNotIn(word, text, rel)

    def test_default_settings_do_not_require_the_gate(self):
        for rel in ["templates/github/repository-settings.json", ".github/repository-settings.json"]:
            self.assertNotIn('"review/gate"', (ROOT / rel).read_text(encoding="utf-8"), rel)


    def test_contract_table_matches_the_settings_template(self):
        readme = (ROOT / "templates/github/README.md").read_text(encoding="utf-8")
        table = readme.split("## 계약 값", 1)[1].split("\n## ", 1)[0]
        written = dict(re.findall(r"`([a-z_]+)=([^`]+)`", table))
        template = json.loads((ROOT / "templates/github/repository-settings.json").read_text(encoding="utf-8"))
        expected = template["expected"]
        queue = next(rule["parameters"] for ruleset in expected["rulesets"] if ruleset["name"] == "merge-queue"
                     for rule in ruleset["rules"] if rule["type"] == "merge_queue")
        values = {**queue, "strict": expected["protection"]["required_status_checks"]["strict"],
                  "app_id": expected["protection"]["required_status_checks"]["checks"][0]["app_id"],
                  **{key: expected["repository"][key] for key in
                     ("allow_squash_merge", "allow_merge_commit", "allow_rebase_merge",
                      "allow_auto_merge", "delete_branch_on_merge")}}
        self.assertEqual(written, {key: str(value).lower() if isinstance(value, bool) else str(value)
                                   for key, value in values.items()})

if __name__ == "__main__":
    unittest.main()
