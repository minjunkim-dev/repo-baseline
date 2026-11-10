#!/usr/bin/env python3

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "profiles" / "matt-skills"))
import check_skills


class CheckSkillsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cwd, self.home = Path(tmp.name, "repo"), Path(tmp.name, "home")

    def skill(self, root, name, text):
        path = root / name / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")

    def run_check(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = check_skills.main(self.cwd, self.home)
        return code, out.getvalue()

    def test_all_skills_found_in_home_and_plugin_cache(self):
        self.skill(self.home / ".agents/skills", "code-review", "x Two-axis review x")
        self.skill(self.home / ".claude/skills", "retro", "## Implementation vs Review")
        self.skill(self.home / ".claude/plugins/cache/mattpocock/mattpocock-skills/1.3.2/skills", "pr", "## Merge Danger")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("pr: " + str(self.home / ".claude/plugins/cache"), out)

    def test_same_name_skill_from_elsewhere_does_not_count(self):
        self.skill(self.cwd / ".claude/skills", "code-review", "Review for bugs and security.")
        self.skill(self.home / ".agents/skills", "retro", "Implementation vs Review")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("code-review: 없음 (다른 스킬만 있음: " + str(self.cwd / ".claude/skills/code-review/SKILL.md"), out)
        self.assertIn("pr: 없음\n", out)

    def test_project_copy_wins_over_home(self):
        self.skill(self.cwd / ".agents/skills", "code-review", "Two-axis review (project copy)")
        self.skill(self.home / ".agents/skills", "code-review", "Two-axis review (home copy)")
        skill, _ = check_skills.find("code-review", "Two-axis review", self.cwd, self.home)
        self.assertEqual(skill, self.cwd / ".agents/skills/code-review/SKILL.md")


if __name__ == "__main__":
    unittest.main()
