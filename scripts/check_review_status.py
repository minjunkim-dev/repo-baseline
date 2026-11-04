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
PROJECT_PATHS = ".github/trust-boundary-paths"
# POLICY.md §5 common paths. A pattern without "/" matches the file name at any depth.
COMMON_PATHS = (
    ".github/workflows/**", ".github/repository-settings.json", ".github/dependabot.yml", ".github/CODEOWNERS",
    PROJECT_PATHS, ".claude/settings.json", ".agents/skills/**", ".claude/skills/**", ".mcp.json",
    "Dockerfile", ".env*",
)
# Dependency manifests and lockfiles; a project adds other ecosystems to PROJECT_PATHS.
DEPENDENCY_FILES = (
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile",
    "Pipfile.lock", "requirements*.txt", "Gemfile", "Gemfile.lock", "Package.swift", "Package.resolved",
    "Podfile", "Podfile.lock", "build.gradle", "build.gradle.kts", "gradle.lockfile", "libs.versions.toml",
    "pubspec.yaml", "pubspec.lock", "composer.json", "composer.lock",
)
# shortcut: any number counts as a version, so a Dependabot line changing only a number passes; upgrade if
# Dependabot ever changes more than versions.
VERSION = re.compile(r"sha\d+[-:][A-Za-z0-9+/=]+|\b[0-9a-f]{7,}\b|v?\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?")


def read_api(endpoint):
    paged = ["--paginate", "--slurp"] if "per_page" in endpoint else []
    result = subprocess.run(["gh", "api", "--method", "GET", endpoint, *paged],
                            capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def matches(path, patterns):
    name = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatchcase(path if "/" in pattern else name, pattern) for pattern in patterns)


def project_paths(repo, base, read):
    try:
        found = read(f"repos/{repo}/contents/{PROJECT_PATHS}?ref={base}")
    except subprocess.CalledProcessError as error:
        if "404" in (error.stderr or ""):
            return ()
        raise
    lines = base64.b64decode(found["content"]).decode("utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip() and not line.startswith("#"))


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
    """POLICY.md §5 exception: Dependabot's own commits, changing only versions and hashes."""
    return (pull["user"]["login"] == DEPENDABOT
            and all((commit.get("author") or {}).get("login") == DEPENDABOT for commit in commits)
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
    statuses = read(f"repos/{repo}/commits/{head}/status")["statuses"]
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
