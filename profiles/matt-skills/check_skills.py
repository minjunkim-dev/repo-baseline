#!/usr/bin/env python3
"""Decide whether review may delegate to the Matt Pocock skills, before it uses them.

Run it from the working tree of the repository under review, after the review preflight:
    python3 -I <repo-baseline>/profiles/matt-skills/check_skills.py <base ref>
Exit 0: delegate. 1: a skill is not installed (stop the review).
2: do not delegate (review it directly): the PR touched files a harness loads, or the answer is unclear.

Scope: this decides delegation only. Instruction files the PR changed (AGENTS.md, rule files, what they import)
reach the reviewer's harness with or without delegation, so the lists below are a best effort, not a guard.
Harness folders are a trust boundary (POLICY §4), so a person reads those diffs; changed instruction
files are read as data, not instructions (prompts/review.md step 2).
"""

from pathlib import Path
import hashlib
import os
import re
import subprocess
import sys
import unicodedata

# A phrase from each upstream SKILL.md tells Matt's skill apart from another skill with the same name.
# shortcut: a marker is not a version pin; if upstream rewrites the phrase, update it here.
SKILLS = {
    "code-review": "Two-axis review",
    "retro": "Implementation vs Review",
    "pr": "Merge Danger",
}
HARNESS_DIRS = {".claude", ".agents", ".codex", ".cursor", ".gemini", ".windsurf"}
HARNESS_FILES = {"agents.md", "agents.override.md", "claude.md", "claude.local.md", "gemini.md", ".mcp.json",
                 ".cursorrules", ".windsurfrules", "copilot-instructions.md"}
IMPORT = re.compile(r"(?<![^\s(])@([^\s)`]+)")


def fold(name):
    return unicodedata.normalize("NFKC", name).casefold()


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout.decode("utf-8", "surrogateescape")


def harness_path(path):
    parts = [fold(p) for p in path.split("/")]
    return any(p in HARNESS_DIRS for p in parts) or parts[-1] in HARNESS_FILES


def refusals(base):
    """Reasons not to delegate. The PR controls what it changed, and a harness loads these files first."""
    try:
        os.chdir(git("rev-parse", "--show-toplevel").strip())  # ls-files and @imports are root-relative
        # The three-dot diff and every commit (--cc for merges), as the review preflight reads them.
        changed = git("diff", "-z", "--raw", "--no-renames", f"{base}...HEAD")
        changed += git("log", "-z", "--raw", "--no-renames", "--format=", "--cc", f"{base}..HEAD")
        tracked = git("ls-files", "-s", "-z")
    except (subprocess.CalledProcessError, OSError) as error:
        return [f"git 실행 실패: {getattr(error, 'stderr', b'') or error}"]
    reasons, fields = [], [f for f in changed.split("\0") if f.strip("\n")]
    changed_paths = {fields[i + 1] for i, f in enumerate(fields[:-1]) if f.lstrip("\n").startswith(":")}
    reasons += imported_changes(tracked, changed_paths)
    for i, field in enumerate(fields):
        if field.lstrip("\n").startswith(":"):  # --raw header ":<modes> <shas> <status>"; the path follows
            path = fields[i + 1] if i + 1 < len(fields) else ""
            if "160000" in field:
                reasons.append(f"{path}: PR이 서브모듈을 바꿨다")
            elif harness_path(path):
                reasons.append(f"{path}: PR이 하네스가 읽는 파일을 바꿨다")
    for entry in tracked.split("\0"):
        mode, _, path = entry.partition("\t")
        if not path or not harness_path(path):
            continue
        if mode.startswith("120000"):
            reasons.append(f"{path}: 하네스 폴더 안 symlink")
        if any(fold(p) in SKILLS for p in path.split("/")):
            reasons.append(f"{path}: 저장소 안에 같은 이름의 스킬이 있다")
    return sorted(set(reasons))


def imported_changes(tracked, changed_paths):
    """Files the tracked harness instruction files pull in with `@path`, followed transitively, that the PR changed."""
    files = {e.partition("\t")[2] for e in tracked.split("\0") if e.partition("\t")[2]}
    queue = [f for f in files if harness_path(f) and not f.endswith(".json")]
    seen, reasons = set(queue), []
    while queue:
        current = queue.pop()
        try:
            text = Path(current).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Check the token with and without trailing punctuation: unclear endings count both ways.
        targets = {v for t in IMPORT.findall(text) for v in (t, t.rstrip(".,;:!?'\""))}
        for target in targets:
            path = os.path.normpath(os.path.join(os.path.dirname(current), target))
            if path in changed_paths:
                reasons.append(f"{path}: PR이 바꾼 파일을 {current}가 @로 불러온다")
            if path in files and path not in seen:
                seen.add(path)
                queue.append(path)
    return reasons


def find(name, marker, home):
    """Return (path of Matt's SKILL.md or None, paths of same-name skills that are not Matt's)."""
    others = []
    roots = [home / ".claude/skills", home / ".agents/skills"]
    roots += sorted((home / ".claude/plugins/cache").glob("*/mattpocock-skills*/*/skills"))
    for root in roots:
        skill = root / name / "SKILL.md"
        if not skill.is_file():
            continue
        if marker in skill.read_text(encoding="utf-8", errors="replace"):
            return skill, others
        others.append(skill)
    return None, others


def main(argv=None, home=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__.strip())
        return 2
    home, missing = Path(home or Path.home()), 0
    for name, marker in SKILLS.items():
        skill, others = find(name, marker, home)
        if skill:
            print(f"{name}: {skill} (sha256 {hashlib.sha256(skill.read_bytes()).hexdigest()[:12]})")
        else:
            missing += 1
            print(f"{name}: 없음" + (f" (다른 스킬만 있음: {', '.join(map(str, others))})" if others else ""))
    if missing:
        return 1
    reasons = refusals(args[0])
    for reason in reasons:
        print(f"위임하지 않음: {reason}")
    return 2 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
