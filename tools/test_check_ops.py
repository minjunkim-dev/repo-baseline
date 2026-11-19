"""check_ops.py against the real ops README: its own 「켜기」 snippet must pass."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_ops import README, check, main, rules, tools  # noqa: E402

README_TEXT = README.read_text(encoding="utf-8")
SNIPPET = README_TEXT.split("## 켜기", 1)[1].split("```markdown\n", 1)[1].split("```", 1)[0]
ENV = "SENTRY_DSN=\nSENTRY_AUTH_TOKEN=\nPOSTHOG_KEY=\nPOSTHOG_HOST=\n"
AGENTS = "# app\n\n## 작업 방식\n\n- 규칙\n\n{ops}\n## 하지 않는 것\n\n- 없음\n"
NO_CLOUDFLARE = SNIPPET.replace(", 도메인은 Cloudflare에", "").replace("DNS, Cloudflare, ", "DNS, ")
CLOUDFLARE_OUT = NO_CLOUDFLARE + "- 뺀 도구: Cloudflare — 웹 도메인이 없는 데스크톱 게임\n"


class CheckOpsTest(unittest.TestCase):
    def repo(self, ops=SNIPPET, env=None):
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
        self.assertGreater(len(rules(README_TEXT)), 5)

    def test_setup_state_passes_without_env_example(self):
        # prompts/setup.md pastes the section and creates no .env* file.
        self.assertEqual(self.problems(), [])

    def test_missing_section_fails(self):
        self.assertEqual(self.problems(ops=""), ["AGENTS.md에 `### ops` 절이 없다"])

    def test_dropped_rule_fails_even_if_tool_named_elsewhere(self):
        ops = SNIPPET.replace("- 배포한 URL은 UptimeRobot에, 도메인은 Cloudflare에 소유자가 등록한다.\n", "")
        self.assertNotEqual(ops, SNIPPET)
        problems = self.problems(ops=ops)
        self.assertEqual(len(problems), 1)
        self.assertIn("UptimeRobot", problems[0])

    def test_excluded_tool_may_be_reworded(self):
        self.assertEqual(len(self.problems(ops=NO_CLOUDFLARE)), 2)
        self.assertEqual(self.problems(ops=CLOUDFLARE_OUT), [])

    def test_exclusion_keeps_other_tools_on_the_same_line(self):
        ops = CLOUDFLARE_OUT.replace("배포한 URL은 UptimeRobot에 소유자가 등록한다.", "소유자가 등록한다.")
        self.assertEqual(self.problems(ops=ops), ["ops 절에 없고 `뺀 도구:` 줄도 없다: UptimeRobot"])
        ops = ops.replace("데스크톱 게임", "데스크톱 게임, UptimeRobot과 무관")
        self.assertEqual(self.problems(ops=ops), ["ops 절에 없고 `뺀 도구:` 줄도 없다: UptimeRobot"])

    def test_exclusion_line_format_and_name(self):
        problems = self.problems(ops=SNIPPET + "- 뺀 도구: Cloudflare\n- 뺀 도구: Datadog — 비싸다\n")
        self.assertEqual(len(problems), 2)
        self.assertIn("형식", problems[0])
        self.assertIn("Datadog", problems[1])

    def test_sdk_stage_checks_env_example(self):
        self.assertEqual(self.problems(sdk=True)[0], ".env.example에 SENTRY_DSN 칸이 없다")
        self.assertEqual(self.problems(sdk=True, env=ENV), [])
        self.assertEqual(self.problems(sdk=True, env=ENV.replace("POSTHOG_HOST=\n", "")),
                         [".env.example에 POSTHOG_HOST 칸이 없다"])
        self.assertEqual(self.problems(sdk=True, env=ENV.replace("POSTHOG_KEY=", "NEXT_PUBLIC_POSTHOG_KEY=")), [])
        self.assertEqual(self.problems(sdk=True, env=ENV.replace("SENTRY_AUTH_TOKEN=", "SENTRY_AUTH_TOKEN=abc")),
                         [".env.example의 SENTRY_AUTH_TOKEN에 값이 있다. 빈 칸으로 둔다"])

    def test_excluded_tool_skips_its_names(self):
        ops = SNIPPET.replace("에러 추적은 Sentry, ", "") + "- 뺀 도구: Sentry — 서버가 없는 정적 페이지\n"
        self.assertEqual(self.problems(sdk=True, ops=ops, env="POSTHOG_KEY=\nPOSTHOG_HOST=\n"), [])
        # Lines that name Sentry only through its secret names may be reworded too.
        ops = (ops.replace("`SENTRY_DSN`, `SENTRY_AUTH_TOKEN`, ", "")
               .replace("- `SENTRY_AUTH_TOKEN`은 GitHub secrets에만 둔다.\n", ""))
        self.assertEqual(self.problems(ops=ops), [])
        dropped = "\n".join(line for line in ops.splitlines() if not line.startswith("- 개인 정보는"))
        self.assertEqual(len(self.problems(ops=dropped)), 1)

    def test_cli_flag_and_path(self):
        root = self.repo()
        with redirect_stdout(StringIO()):
            self.assertEqual(main(["check_ops.py", str(root)]), 0)
            self.assertEqual(main(["check_ops.py", "--sdk", str(root)]), 1)


if __name__ == "__main__":
    unittest.main()
