#!/usr/bin/env python3
"""Check that the Matt Pocock skills this profile delegates to are installed, before review uses them.

Run it from the working tree of the repository under review:
    python3 -I <repo-baseline>/profiles/matt-skills/check_skills.py
Exit 0: every skill was found. 1: a skill is missing, the only skill with that name is a different one,
or the repository under review has its own copy (the harness loads that first, and the PR can change it).
"""

from pathlib import Path
import hashlib
import sys

# A phrase from each upstream SKILL.md tells Matt's skill apart from another skill with the same name.
# shortcut: a marker is not a version pin; if upstream rewrites the phrase, update it here.
SKILLS = {
    "code-review": "Two-axis review",
    "retro": "Implementation vs Review",
    "pr": "Merge Danger",
}


def roots(home):
    yield from (home / ".claude/skills", home / ".agents/skills")
    yield from sorted((home / ".claude/plugins/cache").glob("*/mattpocock-skills*/*/skills"))


def project_copies(name, cwd):
    return [p for p in (cwd / ".claude/skills" / name / "SKILL.md", cwd / ".agents/skills" / name / "SKILL.md") if p.is_file()]


def find(name, marker, home):
    """Return (path of Matt's SKILL.md or None, paths of same-name skills that are not Matt's)."""
    others = []
    for root in roots(home):
        skill = root / name / "SKILL.md"
        if not skill.is_file():
            continue
        if marker in skill.read_text(encoding="utf-8", errors="replace")[:20000]:
            return skill, others
        others.append(skill)
    return None, others


def main(cwd=None, home=None):
    cwd, home = Path(cwd or Path.cwd()), Path(home or Path.home())
    missing = 0
    for name, marker in SKILLS.items():
        copies = project_copies(name, cwd)
        if copies:
            missing += 1
            print(f"{name}: 저장소 안 사본이 있어 쓰지 않는다 ({', '.join(map(str, copies))}). PR이 바꿀 수 있다")
            continue
        skill, others = find(name, marker, home)
        if skill:
            digest = hashlib.sha256(skill.read_bytes()).hexdigest()[:12]
            print(f"{name}: {skill} (sha256 {digest})")
        else:
            missing += 1
            print(f"{name}: 없음" + (f" (다른 스킬만 있음: {', '.join(map(str, others))})" if others else ""))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
