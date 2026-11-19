"""check_ops.py against the real ops README: its own 「켜기」 snippet must pass."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_ops import README, check, tools  # noqa: E402

README_TEXT = README.read_text(encoding="utf-8")
SNIPPET = README_TEXT.split("## 켜기", 1)[1].split("```markdown\n", 1)[1].split("```", 1)[0]
ENV = "SENTRY_DSN=\nSENTRY_AUTH_TOKEN=\nPOSTHOG_KEY=\nPOSTHOG_HOST=\n"
AGENTS = "# app\n\n## 작업 방식\n\n- 규칙\n\n{ops}\n## 하지 않는 것\n\n- 없음\n"


class CheckOpsTest(unittest.TestCase):
    def repo(self, ops=SNIPPET, env=ENV):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "AGENTS.md").write_text(AGENTS.format(ops=ops), encoding="utf-8")
        if env is not None:
            (root / ".env.example").write_text(env, encoding="utf-8")
        return root

    def problems(self, **kwargs):
        return check(self.repo(**kwargs), README_TEXT)

    def test_table_has_every_tool(self):
        self.assertEqual(len(tools(README_TEXT)), 8)

    def test_snippet_as_copied_passes(self):
        self.assertEqual(self.problems(), [])

    def test_missing_section_fails(self):
        self.assertEqual(self.problems(ops=""), ["AGENTS.md에 `### ops` 절이 없다"])

    def test_dropped_tool_needs_exclusion_line(self):
        ops = SNIPPET.replace("도메인은 Cloudflare에 ", "").replace("DNS, Cloudflare, ", "DNS, ")
        self.assertEqual(self.problems(ops=ops), ["ops 절에 없고 `뺀 도구:` 줄도 없다: Cloudflare"])
        ops += "- 뺀 도구: Cloudflare — 웹 도메인이 없는 데스크톱 게임\n"
        self.assertEqual(self.problems(ops=ops), [])

    def test_exclusion_line_format_and_name(self):
        problems = self.problems(ops=SNIPPET + "- 뺀 도구: Cloudflare\n- 뺀 도구: Datadog — 비싸다\n")
        self.assertEqual(len(problems), 2)
        self.assertIn("형식", problems[0])
        self.assertIn("Datadog", problems[1])

    def test_env_example_names(self):
        self.assertEqual(self.problems(env=None)[0], ".env.example에 SENTRY_DSN 칸이 없다")
        self.assertEqual(self.problems(env=ENV.replace("POSTHOG_HOST=\n", "")), [".env.example에 POSTHOG_HOST 칸이 없다"])
        self.assertEqual(self.problems(env=ENV.replace("POSTHOG_KEY=", "NEXT_PUBLIC_POSTHOG_KEY=")), [])
        self.assertEqual(self.problems(env=ENV.replace("SENTRY_AUTH_TOKEN=", "SENTRY_AUTH_TOKEN=abc")),
                         [".env.example의 SENTRY_AUTH_TOKEN에 값이 있다. 빈 칸으로 둔다"])

    def test_excluded_tool_skips_its_names(self):
        ops = SNIPPET.replace("에러 추적은 Sentry, ", "") + "- 뺀 도구: Sentry — 서버가 없는 정적 페이지\n"
        self.assertEqual(self.problems(ops=ops, env="POSTHOG_KEY=\nPOSTHOG_HOST=\n"), [])


if __name__ == "__main__":
    unittest.main()
