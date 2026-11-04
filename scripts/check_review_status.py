#!/usr/bin/env python3
"""Fail when a pull request head lacks the review statuses its changed paths need (POLICY.md §5).
Paths only: content signals stay a reviewer judgement. This shows the process ran on this exact
head; a status from the same account cannot tell a person from an agent, so it is no security boundary."""

import base64
import fnmatch
import json
import os
import re
import subprocess
import sys

INDEPENDENT = "review/independent"
SECURITY = "review/security"
DEPENDABOT = "dependabot[bot]"
WEB_FLOW = "web-flow"
PROJECT_PATHS = ".github/trust-boundary-paths"
# POLICY.md §5 common paths. A pattern without "/" matches the file name at any depth.
COMMON_PATHS = (
    ".github/workflows/**", ".github/actions/**", ".github/repository-settings.json", ".github/dependabot.yml",
    ".github/dependabot.yaml", ".github/CODEOWNERS", ".github/repo-baseline.json", PROJECT_PATHS, "scripts/check_*.py",
    ".claude/settings.json", ".claude/hooks/**", ".claude/agents/**", ".claude/commands/**", ".agents/skills/**",
    ".claude/skills/**", ".mcp.json", "Dockerfile", ".env*",
)
# Dependency manifests and lockfiles; a project adds other ecosystems to PROJECT_PATHS.
DEPENDENCY_FILES = (
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile",
    "Pipfile.lock", "requirements*.txt", "Gemfile", "Gemfile.lock", "Package.swift", "Package.resolved",
    "Podfile", "Podfile.lock", "build.gradle", "build.gradle.kts", "gradle.lockfile", "libs.versions.toml",
    "pubspec.yaml", "pubspec.lock", "composer.json", "composer.lock",
)
# A number or hash right after a word character, "." or "-" is part of a name (pkg-2), so changing it needs Security. That
# also catches file names such as x-1.0.0.tgz, so an npm or yarn lockfile bump needs Security too: the safe side.
# shortcut: any other number counts as a version, so a Dependabot line changing only a number passes; upgrade if
# Dependabot ever changes more than versions.
VERSION = re.compile(r"(?:sha\d+[-:]|h1:)[A-Za-z0-9+/=]+|(?<![\w.-])[0-9a-f]{7,}\b"
                     r"|(?<![\w.-])v?\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?")


def read_api(endpoint):
    paged = ["--paginate", "--slurp"] if "per_page" in endpoint else []
    result = subprocess.run(["gh", "api", "--method", "GET", endpoint, *paged],
                            capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def matches(path, patterns):
    name = path.rsplit("/", 1)[-1]
    # With "/" a pattern is a path from the root, also read literally (in app/[id]/route.ts, [id] is no glob).
    rooted = (pattern.lstrip("/") for pattern in patterns if "/" in pattern)
    return (any(path == pattern or fnmatch.fnmatchcase(path, pattern)
                or path.startswith(pattern.removesuffix("/**") + "/") for pattern in rooted)
            or any(name == pattern or fnmatch.fnmatchcase(name, pattern) for pattern in patterns if "/" not in pattern))


def project_paths(repo, base, read):
    try:
        found = read(f"repos/{repo}/contents/{PROJECT_PATHS}?ref={base}")
    except subprocess.CalledProcessError as error:
        if "404" in (error.stderr or ""):
            return ()
        raise
    lines = base64.b64decode(found["content"]).decode("utf-8").splitlines()
    # CODEOWNERS spellings work too: /src/auth/ means src/auth/**, and /auth stays a root path.
    return tuple(re.sub(r"/$", "/**", line.strip()) for line in lines
                 if line.strip() and not line.startswith("#"))


def only_versions(entry):
    """True when a file's diff replaces lines with the same lines apart from version and hash values."""
    is_workflow = entry["filename"].startswith(".github/workflows/")
    if not is_workflow and not matches(entry["filename"], DEPENDENCY_FILES):
        return False
    lines = [line for line in entry.get("patch", "").splitlines() if line[:1] in ("-", "+")]
    if not lines or (is_workflow and not all(re.match(r"[-+]\s*(-\s+)?uses:", line) for line in lines)):
        return False
    normal = [VERSION.sub("V", line[1:]) for line in lines]
    return (sorted(text for line, text in zip(lines, normal) if line[0] == "-")
            == sorted(text for line, text in zip(lines, normal) if line[0] == "+"))


def dependabot_bump(pull, commits, files):
    """POLICY.md §5 exception: Dependabot's own commits, changing only versions and hashes.
    An author login follows the commit email and a signature only matches the committer, so both
    must show GitHub made the commit: web-flow as committer, verified. A person's amend fails this."""
    return (pull["user"]["login"] == DEPENDABOT
            and all((commit.get("author") or {}).get("login") == DEPENDABOT
                    and (commit.get("committer") or {}).get("login") == WEB_FLOW
                    and commit["commit"]["verification"]["verified"] for commit in commits)
            and all(only_versions(entry) for entry in files))


def missing(repo, number, head, base, read=read_api):
    pull = read(f"repos/{repo}/pulls/{number}")
    files = [entry for page in read(f"repos/{repo}/pulls/{number}/files?per_page=100") for entry in page]
    patterns = COMMON_PATHS + DEPENDENCY_FILES + project_paths(repo, base, read)
    touched = any(matches(entry.get(key, ""), patterns) for entry in files for key in ("filename", "previous_filename"))
    needed = [INDEPENDENT]
    # The files API stops listing at 3000: paths it hides cannot be ruled out.
    if pull["changed_files"] > len(files):
        needed.append(SECURITY)
    elif touched:
        commits = [commit for page in read(f"repos/{repo}/pulls/{number}/commits?per_page=100") for commit in page]
        if not dependabot_bump(pull, commits, files):
            needed.append(SECURITY)
    statuses = [status for page in read(f"repos/{repo}/commits/{head}/status?per_page=100") for status in page["statuses"]]
    # A Security review the paths did not require still counts: a posted failure blocks.
    if SECURITY not in needed and any(status["context"] == SECURITY for status in statuses):
        needed.append(SECURITY)
    passed = {status["context"] for status in statuses if status["state"] == "success"}
    return [context for context in needed if context not in passed]


def main(env=os.environ, read=read_api):
    try:
        absent = missing(env["REPO"], env["PR_NUMBER"], env["HEAD_SHA"], env["BASE_SHA"], read)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"review status UNVERIFIED: {error}", file=sys.stderr)
        return 2
    if absent:
        print(f"review status MISSING on {env['HEAD_SHA']}: " + ", ".join(absent)
              + "; run the review, set the status on this head, then re-run this job")
        return 1
    print(f"review status PASS on {env['HEAD_SHA']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
