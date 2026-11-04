#!/usr/bin/env python3
"""Fail when a pull request head lacks the review statuses its changed paths need (POLICY.md §5).
Paths only: content signals stay a reviewer judgement. This shows the process ran on this exact
head; a status from the same account cannot tell a person from an agent, so it is no security boundary.
A base update creates a new head SHA. When the added and removed lines and binary blobs match a prior
success, that status covers this head. Reuse is still only a process record."""

import base64
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys

INDEPENDENT = "review/independent"
SECURITY = "review/security"
DEPENDABOT = "dependabot[bot]"
WEB_FLOW = "web-flow"
FORCE_PUSHES = "graphql://force-push-befores/"
PRIOR_LIMIT = 40
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
    if endpoint.startswith(FORCE_PUSHES):
        repo, number = endpoint[len(FORCE_PUSHES):].rsplit("/", 1)
        return force_push_befores(repo, number)
    paged = ["--paginate", "--slurp"] if "per_page" in endpoint else []
    result = subprocess.run(["gh", "api", "--method", "GET", endpoint, *paged],
                            capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def read_diff_api(endpoint):
    result = subprocess.run(
        ["gh", "api", "--method", "GET", "-H", "Accept: application/vnd.github.diff", endpoint],
        capture_output=True, text=True, check=True, timeout=60)
    return result.stdout


def force_push_befores(repo, number):
    """SHAs the pull request head pointed at before a rebase, newest first. Empty when the API is unavailable."""
    owner, name = repo.split("/", 1)
    query = (
        "query($owner:String!,$name:String!,$number:Int!){"
        "repository(owner:$owner,name:$name){pullRequest(number:$number){"
        "timelineItems(last:20,itemTypes:[HEAD_REF_FORCE_PUSHED_EVENT]){"
        "nodes{... on HeadRefForcePushedEvent{createdAt beforeCommit{oid}}}}}}}"
    )
    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}", "-f", f"owner={owner}",
             "-f", f"name={name}", "-F", f"number={int(number)}"],
            capture_output=True, text=True, check=True, timeout=60)
        nodes = json.loads(result.stdout)["data"]["repository"]["pullRequest"]["timelineItems"]["nodes"]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return []
    dated = []
    for node in nodes or []:
        oid = ((node or {}).get("beforeCommit") or {}).get("oid")
        if oid:
            dated.append((node.get("createdAt") or "", oid))
    dated.sort(reverse=True)
    return [oid for _, oid in dated]


def diff_identity(diff):
    """SHA-256 of the exact added and removed lines, file paths, modes, renames, and binary blob ids.
    Hunk positions and surrounding context do not count: a base update shifts them without changing the
    pull request. Whitespace does count. None means the diff is not safe to treat as unchanged."""
    if diff is None:
        return None
    text = diff.replace("\r\n", "\n")
    stripped = text.lstrip()
    if not stripped:
        return "empty"
    if stripped.startswith("{") or stripped.startswith("["):
        return None
    chunks = []
    current = index_line = None
    header, body = [], []
    binary = False

    def flush():
        nonlocal current, index_line, header, body, binary
        if current is None:
            return True
        if binary and not index_line:
            return False
        if binary:
            header.append(index_line)
        chunks.append((current, tuple(header), tuple(body)))
        current = index_line = None
        header, body, binary = [], [], False
        return True

    for line in text.splitlines():
        if line.startswith("diff --git "):
            if not flush():
                return None
            current = line
            continue
        if current is None:
            if line.strip() == "":
                continue
            return None
        if line.startswith("index "):
            index_line = line
            continue
        if line.startswith(("new file mode ", "deleted file mode ", "old mode ", "new mode ",
                            "rename from ", "rename to ", "copy from ", "copy to ")):
            header.append(line)
            continue
        if line.startswith(("--- ", "+++ ", "@@", "similarity index ", "dissimilarity index ")):
            continue
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            binary = True
            body.append(line)
            continue
        if line.startswith(("+", "-", "\\")):
            body.append(line)
            continue
        if line.startswith(" ") or line == "":
            continue
        return None
    if not flush() or not chunks:
        return None
    chunks.sort(key=lambda item: item[0])
    lines = []
    for path, kept_header, kept_body in chunks:
        lines.append(path)
        lines.extend(kept_header)
        lines.extend(kept_body)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


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


def latest_state(statuses, context):
    """The combined status lists the newest state of each context first."""
    for status in statuses:
        if status["context"] == context:
            return status["state"]
    return None


def prior_shas(repo, number, head, read):
    """Earlier heads, newest first: current commits, then rebase parents the commit list no longer has."""
    found = []
    try:
        commits = [commit for page in read(f"repos/{repo}/pulls/{number}/commits?per_page=100") for commit in page]
        for commit in reversed(commits):
            sha = commit.get("sha")
            if sha and sha != head and sha not in found:
                found.append(sha)
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError):
        pass
    try:
        for sha in read(FORCE_PUSHES + f"{repo}/{number}") or []:
            if isinstance(sha, str) and sha and sha != head and sha not in found:
                found.append(sha)
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError):
        pass
    return found[:PRIOR_LIMIT]


def identity_of(repo, base, sha, read_diff, cache):
    if sha not in cache:
        try:
            cache[sha] = diff_identity(read_diff(f"repos/{repo}/compare/{base}...{sha}"))
        except (OSError, subprocess.SubprocessError, ValueError, TypeError):
            cache[sha] = None
    return cache[sha]


def carried_contexts(repo, number, head, base, contexts, read, read_diff):
    """Contexts whose newest prior status is success and whose diff matches this head. Anything unverified stays put."""
    candidates = prior_shas(repo, number, head, read)
    if not candidates:
        return set()
    cache, fetched, carried = {}, {}, set()

    def state_at(sha, context):
        if sha not in fetched:
            try:
                pages = read(f"repos/{repo}/commits/{sha}/status?per_page=100")
                fetched[sha] = [status for page in pages for status in page["statuses"]]
            except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError):
                fetched[sha] = None
        # A failed lookup must not skip this SHA for an older success: its state is unknown.
        if fetched[sha] is None:
            return "unreadable"
        return latest_state(fetched[sha], context)

    for context in contexts:
        donor = None
        for sha in candidates:
            state = state_at(sha, context)
            if state is None:
                continue
            if state != "success":
                break
            current = identity_of(repo, base, head, read_diff, cache)
            prior = identity_of(repo, base, sha, read_diff, cache)
            if current is not None and current == prior:
                donor = sha
            break
        if donor:
            carried.add(context)
            print(f"review status carried {context} from {donor} onto {head}")
    return carried


def missing(repo, number, head, base, read=read_api, read_diff=None):
    pull = read(f"repos/{repo}/pulls/{number}")
    files = [entry for page in read(f"repos/{repo}/pulls/{number}/files?per_page=100") for entry in page]
    patterns = COMMON_PATHS + DEPENDENCY_FILES + project_paths(repo, base, read)
    touched = any(matches(entry.get(key, ""), patterns) for entry in files for key in ("filename", "previous_filename"))
    truncated = pull["changed_files"] > len(files)
    bump = False
    if not truncated and touched:
        commits = [commit for page in read(f"repos/{repo}/pulls/{number}/commits?per_page=100") for commit in page]
        bump = dependabot_bump(pull, commits, files)
    needed = []
    # The version-only Dependabot exception drops both reviews. A status posted anyway still has to be success.
    if not bump:
        needed.append(INDEPENDENT)
    # The files API stops listing at 3000: paths it hides cannot be ruled out.
    if truncated or (touched and not bump):
        needed.append(SECURITY)
    statuses = [status for page in read(f"repos/{repo}/commits/{head}/status?per_page=100") for status in page["statuses"]]
    present = {status["context"] for status in statuses}
    for context in (INDEPENDENT, SECURITY):
        if context not in needed and context in present:
            needed.append(context)
    passed = {status["context"] for status in statuses if status["state"] == "success"}
    absent = [context for context in needed if context not in passed]
    # A failure or pending state on this head stands. Only a missing context can reuse an unchanged diff.
    reusable = [context for context in absent if context not in present]
    if not reusable:
        return absent
    carried = carried_contexts(repo, number, head, base, reusable, read, read_diff or read_diff_api)
    return [context for context in absent if context not in carried]


def main(env=os.environ, read=read_api, read_diff=None):
    try:
        absent = missing(env["REPO"], env["PR_NUMBER"], env["HEAD_SHA"], env["BASE_SHA"], read, read_diff)
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
