#!/usr/bin/env python3
"""Check that a consumer repo carries the ops profile; never changes files or calls a service.

Usage: python3 <repo-baseline clone>/tools/check_ops.py [--sdk] [consumer repo path, default .]
Without --sdk it checks the AGENTS.md ops section, which setup adds before any .env file exists.
With --sdk it also checks the .env.example names, which the first-deploy SDK PR adds.
The rules and the tool list come from profiles/ops/README.md in this clone, so the README stays the only source.
Exit 0 when every check passes, 1 with one line per problem otherwise.
"""

from pathlib import Path
import re
import sys

README = Path(__file__).resolve().parents[1] / "profiles/ops/README.md"
# Each secret name belongs to the tool whose table cell contains this word.
NAMES = {"SENTRY_DSN": "Sentry", "SENTRY_AUTH_TOKEN": "Sentry", "POSTHOG_KEY": "PostHog", "POSTHOG_HOST": "PostHog"}
EXCLUSION = re.compile(r"\s*-?\s*뺀 도구:")


def tools(readme_text):
    """Tool cells of the 「도구」 table, in order."""
    section = readme_text.split("## 도구", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    return [row.split("|")[2].strip() for row in rows[2:]]


def rules(readme_text):
    """Bullet lines of the 「켜기」 snippet, which a consumer copies as is."""
    snippet = readme_text.split("## 켜기", 1)[1].split("```markdown\n", 1)[1].split("```", 1)[0]
    return [line.rstrip() for line in snippet.splitlines() if line.startswith("- ")]


def mentions(tool, text):
    """The tool cell and the tool's secret names that appear in the text."""
    return [word for word in [tool] + [name for name, owner in NAMES.items() if owner in tool] if word in text]


def ops_section(agents_text):
    """Text under `### ops` up to the next heading of level 1-3, or None."""
    match = re.search(r"^### ops[ \t]*\n(.*?)(?=^#{1,3} |\Z)", agents_text, re.M | re.S)
    return match.group(1) if match else None


def check(repo, readme_text, sdk=False):
    known = tools(readme_text)
    agents = repo / "AGENTS.md"
    if not agents.is_file():
        return ["AGENTS.md가 없다"]
    section = ops_section(agents.read_text(encoding="utf-8"))
    if section is None:
        return ["AGENTS.md에 `### ops` 절이 없다"]
    problems = []
    excluded = set()
    for line in section.splitlines():
        if not EXCLUSION.match(line):
            continue  # the rule line that explains the format quotes it mid-line
        match = re.fullmatch(r"\s*-?\s*뺀 도구: (.+?) — (\S.*)", line)
        if not match:
            problems.append(f"형식이 `뺀 도구: <도구> — <이유>`가 아니다: {line.strip()}")
        elif match.group(1) not in known:
            problems.append(f"표에 없는 도구를 뺐다: {match.group(1)}")
        else:
            excluded.add(match.group(1))
    present = {line.rstrip() for line in section.splitlines()}
    # An exclusion reason must not count as another tool still being named.
    named = "\n".join(line for line in section.splitlines() if not EXCLUSION.match(line))
    for rule in rules(readme_text):
        if not any(mentions(tool, rule) for tool in excluded):
            if rule not in present:
                problems.append(f"ops 절에 「켜기」 절의 줄이 그대로 없다: {rule}")
            continue
        # A rule naming an excluded tool may be reworded, but its other tools stay named.
        for tool in known:
            if tool in excluded:
                continue
            for word in mentions(tool, rule):
                if word not in named:
                    problems.append(f"ops 절에 없고 `뺀 도구:` 줄도 없다: {word}")
    if sdk:
        problems += env_problems(repo, excluded)
    return problems


def env_problems(repo, excluded):
    example = repo / ".env.example"
    lines = example.read_text(encoding="utf-8").splitlines() if example.is_file() else []
    problems = []
    for name, owner in NAMES.items():
        if any(owner in tool for tool in excluded):
            continue
        # A framework prefix such as NEXT_PUBLIC_ is allowed in front of the name.
        found = [line for line in lines if re.match(rf"\s*(?:export\s+)?(?:[A-Z0-9]+_)*{name}\s*=", line)]
        if not found:
            problems.append(f".env.example에 {name} 칸이 없다")
        elif any(line.split("=", 1)[1].strip().strip("'\"") for line in found):
            problems.append(f".env.example의 {name}에 값이 있다. 빈 칸으로 둔다")
    return problems


def main(argv):
    args = argv[1:]
    sdk = "--sdk" in args
    paths = [arg for arg in args if arg != "--sdk"]
    repo = Path(paths[0] if paths else ".")
    problems = check(repo, README.read_text(encoding="utf-8"), sdk=sdk)
    for problem in problems:
        print(problem)
    if not problems:
        print("ops: 통과")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
