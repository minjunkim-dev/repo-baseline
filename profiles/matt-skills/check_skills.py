#!/usr/bin/env python3
"""Check that the Matt Pocock skills this profile delegates to are installed, before review uses them.

Run it from the working tree of the repository under review:
    python3 -I <repo-baseline>/profiles/matt-skills/check_skills.py
Exit 0: every skill was found. 1: a skill is missing, the only skill with that name is a different one,
or the repository under review has its own copy (the harness loads that first, and the PR can change it).
"""

from pathlib import Path
import hashlib
import subprocess
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


HARNESS_DIRS = {".claude", ".agents", ".codex", ".cursor"}


def frontmatter_names(text):
    """The `name:` values in the frontmatter, or None when they can't be read unambiguously."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None
    names = []
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if sep and key.strip().strip("'\"").lower() == "name":
            value = value.strip().strip("'\"")
            if not value or value[0] in "|>&*!{[" or line[:1].isspace():
                return None
            names.append(value.lower())
    return names if len(names) == 1 else None


def project_copies(name, cwd):
    """Repository files a harness could load as this skill. Fails closed: unclear cases count as copies."""
    out = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if out.returncode != 0:
        return [f"{cwd} (git 저장소 루트를 찾지 못함)"]
    root = Path(out.stdout.strip())
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-s", "-z"], capture_output=True, check=True).stdout
    copies = []
    for entry in listed.decode("utf-8", "surrogateescape").split("\0"):
        if not entry:
            continue
        mode, _, path = entry.partition("\t")
        parts = path.split("/")
        lowered = [x.lower() for x in parts]
        harness = [i for i, x in enumerate(lowered) if x in HARNESS_DIRS]
        if not harness:
            continue
        if mode.startswith("120000"):  # a symlink inside a harness folder can point anywhere
            copies.append(f"{path} (symlink)")
            continue
        if lowered[-1] != "skill.md" or "skills" not in lowered[harness[0] + 1:]:
            continue
        names = frontmatter_names((root / path).read_text(encoding="utf-8", errors="replace"))
        if names is None:
            copies.append(f"{path} (name을 하나로 읽을 수 없음)")
        elif name in names or lowered[-2] == name:
            copies.append(path)
    return copies


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
