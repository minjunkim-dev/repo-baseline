"""check_ops.py against the real ops README: its own 「켜기」 block must pass."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_ops import BEGIN, END, README, check, main, mentions, ops_block, snippet, tools  # noqa: E402

README_TEXT = README.read_text(encoding="utf-8")
BLOCK = ops_block(README_TEXT, {})
ENV = "SENTRY_DSN=\nSENTRY_AUTH_TOKEN=\nPOSTHOG_KEY=\nPOSTHOG_HOST=\n"
AGENTS = "# app\n\n## 작업 방식\n\n- 규칙\n\n{ops}\n## 하지 않는 것\n\n- 없음\n"


class CheckOpsTest(unittest.TestCase):
    def repo(self, ops=BLOCK, env=None):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "AGENTS.md").write_text(AGENTS.format(ops=ops), encoding="utf-8")
        if env is not None:
            (root / ".env.example").write_text(env, encoding="utf-8")
        return root

    def problems(self, sdk=False, **kwargs):
        return check(self.repo(**kwargs), README_TEXT, sdk=sdk)

    def test_readme_parts_are_found(self):
        self.assertEqual(len(tools(README_TEXT)), 8)
        lines = snippet(README_TEXT)
        self.assertEqual((lines[0], lines[-1]), (BEGIN, END))

    def test_every_rule_line_names_at_most_one_tool(self):
        # One tool per line is what makes an exclusion a plain line deletion.
        for line in snippet(README_TEXT):
            named = [tool for tool in tools(README_TEXT) if mentions(tool, line)]
            self.assertLessEqual(len(named), 1, line)

    def test_block_as_copied_passes(self):
        self.assertEqual(self.problems(), [])

    def test_missing_markers_fail(self):
        self.assertEqual(len(self.problems(ops=BLOCK.replace(END + "\n", ""))), 1)
        self.assertEqual(len(self.problems(ops="### ops\n")), 1)

    def test_any_edit_inside_the_block_fails(self):
        dropped = BLOCK.replace("- 배포한 URL은 UptimeRobot에 소유자가 등록한다.\n", "")
        self.assertNotEqual(dropped, BLOCK)
        self.assertEqual(self.problems(ops=dropped), ["블록에 없다: - 배포한 URL은 UptimeRobot에 소유자가 등록한다."])
        body = BLOCK.splitlines()[3:-1]
        reordered = BLOCK.replace("\n".join(body), "\n".join(reversed(body)))
        self.assertTrue(self.problems(ops=reordered))

    def test_exclusion_drops_that_tools_lines_only(self):
        block = ops_block(README_TEXT, {"Cloudflare": "웹 도메인이 없는 데스크톱 게임"})
        self.assertNotIn("Cloudflare에", block)
        self.assertIn("UptimeRobot", block)
        self.assertIn("- 뺀 도구: Cloudflare — 웹 도메인이 없는 데스크톱 게임\n" + END, block)
        self.assertEqual(self.problems(ops=block), [])
        # An exclusion line without deleting the tool's lines is not the generated block.
        kept = BLOCK.replace(END, "- 뺀 도구: Cloudflare — 이유\n" + END)
        self.assertTrue(any("있으면 안 된다" in p for p in self.problems(ops=kept)))

    def test_secret_names_go_with_their_tool(self):
        block = ops_block(README_TEXT, {"Sentry": "서버가 없는 정적 페이지"})
        self.assertNotIn("SENTRY_", block)
        self.assertIn("POSTHOG_KEY", block)

    def test_exclusion_line_format_and_name(self):
        self.assertIn("표에 없는 도구", self.problems(ops=BLOCK.replace(END, "- 뺀 도구: Datadog — 비싸다\n" + END))[0])
        self.assertIn("형식", self.problems(ops=BLOCK.replace(END, "- 뺀 도구: Cloudflare\n" + END))[0])

    def test_sdk_stage_checks_env_example(self):
        self.assertEqual(self.problems(sdk=True)[0], ".env.example에 SENTRY_DSN 칸이 없다")
        self.assertEqual(self.problems(sdk=True, env=ENV), [])
        self.assertEqual(self.problems(sdk=True, env=ENV.replace("POSTHOG_KEY=", "NEXT_PUBLIC_POSTHOG_KEY=")), [])
        self.assertEqual(self.problems(sdk=True, env=ENV.replace("SENTRY_AUTH_TOKEN=", "SENTRY_AUTH_TOKEN=abc")),
                         [".env.example의 SENTRY_AUTH_TOKEN에 값이 있다. 빈 칸으로 둔다"])
        block = ops_block(README_TEXT, {"Sentry": "정적 페이지"})
        self.assertEqual(self.problems(sdk=True, ops=block, env="POSTHOG_KEY=\nPOSTHOG_HOST=\n"), [])

    def test_cli_flag_and_path(self):
        root = self.repo()
        with redirect_stdout(StringIO()):
            self.assertEqual(main(["check_ops.py", str(root)]), 0)
            self.assertEqual(main(["check_ops.py", "--sdk", str(root)]), 1)


if __name__ == "__main__":
    unittest.main()
