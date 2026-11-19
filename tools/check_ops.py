#!/usr/bin/env python3
"""Check that a consumer repo carries the ops profile; never changes files or calls a service.

Usage: python3 <repo-baseline clone>/tools/check_ops.py [--sdk] [consumer repo path, default .]
Without --sdk it checks the AGENTS.md ops block, which setup adds before any .env file exists.
With --sdk it also checks the .env.example names, which the first-deploy SDK PR adds.
The block must equal ops_block(): the 「켜기」 snippet of profiles/ops/README.md in this clone,
minus the lines that name an excluded tool, plus one `뺀 도구:` line per excluded tool.
hash-copy (profiles/hash-copy/apply_baseline.py) writes the block with the same function.
Exit 0 when every check passes, 1 with one line per problem otherwise.
"""

from pathlib import Path
import re
import sys

README = Path(__file__).resolve().parents[1] / "profiles/ops/README.md"
BEGIN, END = "<!-- repo-baseline:ops -->", "<!-- /repo-baseline:ops -->"
# Each secret name belongs to the tool whose table cell contains this word.
NAMES = {"SENTRY_DSN": "Sentry", "SENTRY_AUTH_TOKEN": "Sentry", "POSTHOG_KEY": "PostHog", "POSTHOG_HOST": "PostHog"}
EXCLUSION = re.compile(r"- 뺀 도구: (.+?) — (\S.*)")


def tools(readme_text):
    """Tool cells of the 「도구」 table, in order."""
    section = readme_text.split("## 도구", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    return [row.split("|")[2].strip() for row in rows[2:]]


def snippet(readme_text):
    """Lines of the 「켜기」 code block, markers included."""
    text = readme_text.split("## 켜기", 1)[1].split("```markdown\n", 1)[1].split("```", 1)[0]
    return text.rstrip("\n").split("\n")


def mentions(tool, line):
    return tool in line or any(owner in tool and name in line for name, owner in NAMES.items())


def ops_block(readme_text, exclude):
    """The block text for these exclusions ({tool: reason}, in any order)."""
    known = tools(readme_text)
    unknown = [tool for tool in exclude if tool not in known]
    if unknown:
        raise ValueError(f"표에 없는 도구를 뺐다: {', '.join(unknown)}")
    lines = [line for line in snippet(readme_text)
             if not (line.startswith("- ") and any(mentions(tool, line) for tool in exclude))]
    extra = [f"- 뺀 도구: {tool} — {exclude[tool]}" for tool in known if tool in exclude]
    return "\n".join(lines[:-1] + extra + lines[-1:]) + "\n"


def find_block(text):
    """(start, end) offsets of the marked block including the end marker line, or None."""
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        return None
    start, end = text.find(BEGIN + "\n"), text.find(END + "\n")
    if start < 0 or end < start:
        return None
    return start, end + len(END) + 1


def exclusions(block_text):
    """{tool: reason} from the `뺀 도구:` lines, and lines that look like one but break the format."""
    found, broken = {}, []
    for line in block_text.splitlines():
        if not line.startswith("- 뺀 도구:"):
            continue
        match = EXCLUSION.fullmatch(line)
        if match:
            found[match.group(1)] = match.group(2)
        else:
            broken.append(line)
    return found, broken


def check(repo, readme_text, sdk=False):
    agents = repo / "AGENTS.md"
    if not agents.is_file():
        return ["AGENTS.md가 없다"]
    text = agents.read_text(encoding="utf-8")
    span = find_block(text)
    if span is None:
        return [f"AGENTS.md에 `{BEGIN}`·`{END}` 표시 줄이 한 쌍 없다"]
    block = text[span[0]:span[1]]
    excluded, broken = exclusions(block)
    problems = [f"형식이 `뺀 도구: <도구> — <이유>`가 아니다: {line}" for line in broken]
    try:
        expected = ops_block(readme_text, excluded)
    except ValueError as error:
        return problems + [str(error)]
    if block != expected:
        have, want = block.splitlines(), expected.splitlines()
        problems += [f"블록에 없다: {line}" for line in want if line not in have]
        problems += [f"블록에 있으면 안 된다: {line}" for line in have if line not in want]
        if not problems:
            problems.append("블록의 줄 순서나 빈 줄이 「켜기」 블록과 다르다")
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
