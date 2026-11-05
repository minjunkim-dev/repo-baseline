"""One author-line parser for the PR convention check and the review-evidence check.

Both scripts are copied into a consumer's scripts/ directory. This module is copied
with them, and each script imports it. There is no second copy of the rules.
"""

TOOLS = ("Claude Code", "Cursor 클라우드 에이전트", "Cursor", "사람")


def text_of(body):
    return (body or "").replace("\r\n", "\n").replace("\r", "\n")


def tool_name(value):
    for name in TOOLS:
        if value == name:
            return name
    return None


def parse_author(body):
    """(tool, model) or None, previous model names, and errors. The body is not executed."""
    author_tool = author_model = None
    tool_line = model_line = None
    previous = []
    for line in text_of(body).split("\n"):
        if line.startswith("Author:") and author_tool is None and "/" in line:
            tool_text, model_text = line[len("Author:"):].split("/", 1)
            found = tool_name(tool_text.strip())
            if found and model_text.strip():
                author_tool, author_model = found, model_text.strip()
        elif line.startswith("작성 도구:") and tool_line is None:
            tool_line = tool_name(line[len("작성 도구:"):].strip())
        elif line.startswith("작성 모델:") and model_line is None:
            value = line[len("작성 모델:"):].strip()
            if value:
                model_line = value
        elif line.startswith("이전 작성 모델:") and not previous:
            previous = [part.strip() for part in line[len("이전 작성 모델:"):].split(",") if part.strip()]
    errors = []
    if author_tool and tool_line and (author_tool != tool_line or author_model != model_line):
        errors.append("PR body: Author line and 작성 도구/작성 모델 disagree")
    tool = author_tool or tool_line
    model = author_model or model_line
    if not tool or not model:
        errors.append("PR body: Author line must be 'Author: <tool> / <model>' or 작성 도구 and 작성 모델")
        return None, previous, errors
    if tool == "사람" and model != "없음":
        errors.append("PR body: a person author uses model 없음")
    return (tool, model), previous, errors
