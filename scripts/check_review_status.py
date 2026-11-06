#!/usr/bin/env python3
"""Fail when a pull request head lacks the review statuses its changed paths need (POLICY.md §5).
Paths only: content signals stay a reviewer judgement. On a 1-person profile, review/independent
and review/security count only when creator.login is the repository owner or a login in
STATUS_ACTORS (empty). The review-gate app is not listed: it posts review/gate only.
Another creator is failure, not a missing context, so an older success on this SHA is not used.
The same account still cannot tell a person from an agent. A team profile does not look at the creator.
A new head SHA needs success posted on that exact SHA. A prior head, an identical diff, a line-number
shift, a base update, and a force-push do not inherit it. Diff text and post-change blob ids are not evidence.
A 1-person pull request that changes a POLICY.md §10 gate path also needs the repository owner's
approval comment on this head. Dependabot follows the same evidence table, review statuses, and
owner comment as any other author. A version or hash bump is not a separate success path.
That comment is not reused from an older head. An edited comment
is not approval when REST updated_at differs from created_at. Timestamps are whole seconds, so a
same-second edit is not distinguished. Post a new comment, then re-run this job or post the gate
by hand. A comment does not re-run this checker.
The first line must be the current prefix or the deprecated prefix, then the full head SHA.
Both prefixes share this match.
The pull request body is parsed for the review evidence table. It is never executed.
The pull request base ref must be the repository default branch, and the event base SHA must be
that branch or an ancestor of it. A pull request with a different base is not evidence."""

import base64
import fnmatch
import json
import os
import re
import subprocess
import sys

from pr_author import parse_author

INDEPENDENT = "review/independent"
SECURITY = "review/security"
# Not a commit status. The job fails with this name when the owner comment is missing.
# A status posted under this name does not count: the same account can post one without the comment.
OWNER = "review/owner-approval"
# Not a commit status. The job fails with this name when the evidence table does not match this head.
EVIDENCE = "review/evidence"
# Not a commit status. The job fails with this name when this pull request does not target the
# repository default branch. A status posted under this name does not count.
BASE_REF = "review/base-branch"
TEAM_LINE = "프로필: 팀"
# Solo-profile logins that may post review/independent and review/security, besides the
# repository owner. The review-gate app is not added here. This file runs from the default
# branch, so a pull request cannot add a login. A team profile does not read this tuple.
STATUS_ACTORS = ()
# Exact first-line prefixes. The second is deprecated and means the same approval.
APPROVAL_LINE = re.compile(
    r"(?:되돌리기 어려움 승인:|한쪽 문 승인:)"
    r"[ \t]*([0-9a-fA-F]{40})(?:[ \t].*)?\Z")
PROJECT_PATHS = ".github/trust-boundary-paths"
# POLICY.md §5 common paths. A pattern without "/" matches the file name at any depth.
COMMON_PATHS = (
    ".github/workflows/**", ".github/actions/**", ".github/repository-settings.json", ".github/dependabot.yml",
    ".github/dependabot.yaml", ".github/CODEOWNERS", ".github/repo-baseline.json", ".github/workflow-policy.json",
    PROJECT_PATHS, "scripts/check_*.py",
    "scripts/workflow_policy.py", "scripts/pr_author.py",
    "tools/post_review_gate.py", "tools/apply_github_settings.py", "docs/review-gate-app.md",
    ".claude/settings.json", ".claude/hooks/**", ".claude/agents/**", ".claude/commands/**", ".agents/skills/**",
    ".claude/skills/**", ".mcp.json", "Dockerfile", ".env*",
)
# POLICY.md §10 gate paths. A change here needs the 1-person owner comment, including a Dependabot
# pull request. Other hard-to-reverse decisions (money, account, migration) are not in this list.
ONE_WAY_PATHS = (
    ".github/workflows/**", "templates/review-status.yml", "templates/pr-policy.yml",
    "scripts/check_review_status.py", "scripts/workflow_policy.py", "scripts/pr_author.py",
    "tools/post_review_gate.py", "tools/apply_github_settings.py",
    "docs/review-gate-app.md", ".github/workflow-policy.json",
    "templates/review-status-policy.json", ".github/repository-settings.json", "templates/repository-settings.json",
)
# Dependency manifests and lockfiles; a project adds other ecosystems to PROJECT_PATHS.
DEPENDENCY_FILES = (
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile",
    "Pipfile.lock", "requirements*.txt", "Gemfile", "Gemfile.lock", "Package.swift", "Package.resolved",
    "Podfile", "Podfile.lock", "build.gradle", "build.gradle.kts", "gradle.lockfile", "libs.versions.toml",
    "pubspec.yaml", "pubspec.lock", "composer.json", "composer.lock",
)


def read_api(endpoint):
    paged = ["--paginate", "--slurp"] if "per_page" in endpoint else []
    result = subprocess.run(["gh", "api", "--method", "GET", endpoint, *paged],
                            capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def full_oid(value):
    """True for a full Git object id. An abbreviated index line is not one."""
    return isinstance(value, str) and len(value) == 40 and all(char in "0123456789abcdefABCDEF" for char in value)


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


def approval_sha(body):
    """Full SHA when the first line is exactly one approval prefix plus that SHA. None otherwise."""
    if not isinstance(body, str) or body == "":
        return None
    # GitHub's web UI stores comment bodies with CRLF. A leftover CR is not whitespace in APPROVAL_LINE.
    found = APPROVAL_LINE.fullmatch(re.split(r"\r\n|\n|\r", body, maxsplit=1)[0])
    if not found:
        return None
    return found.group(1).lower()


def same_login(left, right):
    return isinstance(left, str) and isinstance(right, str) and left.casefold() == right.casefold()


def one_way(files, truncated):
    """True when a gate path changed, or the file list is short so a gate path could be hidden."""
    if truncated:
        return True
    return any(matches(entry.get(key) or "", ONE_WAY_PATHS)
               for entry in files for key in ("filename", "previous_filename"))


def profile_line_changes(files):
    """True when a diff adds or removes the team line, or that diff cannot be read.
    The base file decides the profile, so a pull request must not be able to opt out without the comment."""
    for entry in files:
        names = {entry.get("filename") or "", entry.get("previous_filename") or ""}
        if "AGENTS.md" not in names:
            continue
        patch = entry.get("patch")
        if not isinstance(patch, str):
            return True
        for line in patch.splitlines():
            if line[:1] in "+-" and line[1:].strip() == TEAM_LINE:
                return True
    return False


def blob_has_team_line(repo, ref, read):
    """True when that ref's AGENTS.md has the exact team line. A missing file does not."""
    try:
        found = read(f"repos/{repo}/contents/AGENTS.md?ref={ref}")
    except subprocess.CalledProcessError as error:
        if "404" in (error.stderr or ""):
            return False
        raise
    if not isinstance(found, dict) or "content" not in found:
        raise ValueError("AGENTS.md")
    text = base64.b64decode(found["content"]).decode("utf-8")
    return any(line.strip() == TEAM_LINE for line in text.splitlines())


def team_profile(repo, base, read):
    """The profile comes from the base branch. The pull request head cannot opt out."""
    return blob_has_team_line(repo, base, read)


def pinned_change(repo, base, head, read):
    """Files and commits for this base...head. None files means the compare is too large to trust.
    The open pull request's current file list can move after the event SHA and is not used here."""
    try:
        found = read(f"repos/{repo}/compare/{base}...{head}")
    except subprocess.CalledProcessError as error:
        if "406" in (error.stderr or ""):
            return None, None
        raise
    if not isinstance(found, dict):
        raise ValueError("compare")
    files = found.get("files")
    commits = found.get("commits")
    # Compare returns at most 300 files and 250 commits. A full list is not a complete diff.
    if not isinstance(files, list) or len(files) >= 300:
        return None, None
    if not isinstance(commits, list) or len(commits) >= 250:
        commits = None
    return files, commits


def touches_agents(files):
    return any((entry.get("filename") or "") == "AGENTS.md" or (entry.get("previous_filename") or "") == "AGENTS.md"
               for entry in files)


def default_base(repo, pull, read):
    """Default branch name when this pull request targets it. None for another base.
    A pull request with a different base is not evidence. Raises when either name cannot be read."""
    info = read(f"repos/{repo}")
    default = info.get("default_branch") if isinstance(info, dict) else None
    base = pull.get("base") if isinstance(pull, dict) else None
    ref = base.get("ref") if isinstance(base, dict) else None
    if not isinstance(default, str) or default == "" or not isinstance(ref, str) or ref == "":
        raise ValueError("default branch")
    if ref != default:
        print(f"review status: base {ref} is not the default branch {default}")
        return None
    return default


def event_base_on_default(repo, base, default, read):
    """True when the event base SHA is the default branch tip or an ancestor of it.
    compare(base...default) is ahead when that branch has moved past this SHA, and identical
    at the tip. behind or diverged means the SHA is not on the branch. A rerun keeps the
    original BASE_SHA, so retargeting onto the default branch must not pass the old SHA."""
    found = read(f"repos/{repo}/compare/{base}...{default}")
    if not isinstance(found, dict):
        raise ValueError("base branch")
    status = found.get("status")
    if status in ("ahead", "identical"):
        return True
    if status in ("behind", "diverged"):
        print(f"review status: event base {base} is not on the default branch {default} ({status})")
        return False
    raise ValueError("base branch")


def repository_owner(repo, read):
    info = read(f"repos/{repo}")
    owner = (info.get("owner") or {}).get("login") if isinstance(info, dict) else None
    if not isinstance(owner, str) or owner == "":
        raise ValueError("repository owner")
    return owner


def status_actors(repo, read):
    """Owner plus STATUS_ACTORS. Blank entries are not logins. Solo profile only."""
    extra = tuple(login for login in STATUS_ACTORS if isinstance(login, str) and login != "")
    return (repository_owner(repo, read), *extra)


def bot_creator(login):
    """True for a GitHub App or Actions login. Those accounts do not post review evidence."""
    return isinstance(login, str) and login.casefold().endswith("[bot]")


def status_actor(status):
    creator = status.get("creator") if isinstance(status, dict) else None
    login = creator.get("login") if isinstance(creator, dict) else None
    if not isinstance(login, str) or login == "":
        return None
    return login


def reviewed_state(status, allowed):
    """State that counts for one review context.

    A [bot] login is failure on every profile, including a team profile where allowed is None.
    allowed is None on a team profile: a human creator is not checked.
    On a 1-person profile, a creator outside allowed is failure. The newest state per
    context on this SHA counts. Dropping that status would reveal an older success
    on the same SHA."""
    actor = status_actor(status)
    if bot_creator(actor):
        print(f"review status untrusted {status.get('context')} from {actor} is not success")
        return "failure"
    if allowed is None:
        return status["state"]
    if any(same_login(actor, login) for login in allowed):
        return status["state"]
    print(f"review status untrusted {status.get('context')} from {actor or 'unknown'} is not success")
    return "failure"


def comment_unedited(comment):
    """True when REST updated_at is the same non-empty string as created_at.

    GitHub REST timestamps are whole seconds. A same-second edit keeps the strings
    equal and is not distinguished. Do not edit an approval comment. Post a new one,
    then re-run Review status or post the gate by hand. Extra keys are ignored."""
    if not isinstance(comment, dict):
        return False
    created = comment.get("created_at")
    updated = comment.get("updated_at")
    return isinstance(created, str) and created != "" and created == updated


def owner_approved(repo, number, head, read):
    """True when the owner has an unedited issue comment for this exact head.
    REST updated_at must equal created_at. A different timestamp is not approval.
    Post a new comment. A same-second edit is not distinguished."""
    owner = repository_owner(repo, read)
    pages = read(f"repos/{repo}/issues/{number}/comments?per_page=100")
    if not isinstance(pages, list):
        raise ValueError("approval comments")
    wanted = head.lower()
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("approval comments")
        for comment in page:
            if not isinstance(comment, dict):
                continue
            user = comment.get("user")
            login = user.get("login") if isinstance(user, dict) else None
            if bot_creator(login):
                continue
            if (same_login(login, owner) and comment_unedited(comment)
                    and approval_sha(comment.get("body")) == wanted):
                return True
    return False


def status_list(pages):
    """Newest-first status objects from GET /commits/{sha}/statuses.

    Each page is a list. The combined status object is a dict and has no creator,
    so it is not this list and must not count as success."""
    if not isinstance(pages, list):
        raise ValueError("commit statuses")
    flat = []
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("commit statuses")
        for status in page:
            if not isinstance(status, dict) or "context" not in status:
                raise ValueError("commit statuses")
            flat.append(status)
    return flat


# Alias, then family. Opus and Sonnet are both Claude. Two families in one name is unknown.
FAMILY_ALIASES = (
    ("composer", "composer"),
    ("gemini", "gemini"),
    ("sonnet", "claude"),
    ("opus", "claude"),
    ("claude", "claude"),
    ("grok", "grok"),
    ("gpt", "gpt"),
)
FAMILY_NAMES = "Claude, Grok, Composer, Gemini, or GPT"
COLUMN_NAMES = {
    "axis": "axis", "축": "axis", "model": "model", "모델": "model", "effort": "effort",
    "head sha": "sha", "p0": "p0", "p1": "p1", "p2": "p2", "result": "result", "결과": "result",
}
TABLE_COLUMNS = ("axis", "model", "effort", "sha", "p0", "p1", "p2")
AXIS_KEYS = {
    "standards": "standards", "spec": "spec", "security": "security",
    "버그 찾기": "bug", "bug-finding": "bug", "bug finding": "bug",
}
BODY_LIMIT = 200000


def model_family(name):
    """Family of a model name, or None when it is empty, mixed, or not in the alias table."""
    if not isinstance(name, str):
        return None
    text = name.strip().lower()
    if not text or "chatgpt" in text or re.search(r"(?<![a-z0-9])codex(?![a-z0-9])", text):
        return None
    found = set()
    for alias, family in FAMILY_ALIASES:
        if re.search(rf"(?<![a-z0-9]){alias}(?![a-z0-9])", text):
            found.add(family)
    if len(found) != 1:
        return None
    return found.pop()


def _cells(line):
    stripped = line.strip()
    if len(stripped) < 2 or not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _separator(cells):
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _integer(value):
    return re.fullmatch(r"0|[1-9][0-9]*", value.strip()) is not None


def _not_applicable(model):
    text = model.strip()
    return text.startswith("해당 없음:") and text.split(":", 1)[1].strip() != ""


def evidence_table(body):
    """Rows of the last evidence table. An earlier table does not hide a later one. Parse only."""
    lines = body.split("\n")
    chosen = None
    index = 0
    while index < len(lines):
        cells = _cells(lines[index])
        mapped = [COLUMN_NAMES.get(cell.lower()) for cell in cells] if cells else []
        named = [name for name in mapped if name]
        if not cells or any(column not in named for column in TABLE_COLUMNS) or len(named) != len(set(named)):
            index += 1
            continue
        # A later header replaces any earlier table. A broken later table does not keep the old one.
        chosen = None
        rows = []
        broken = False
        index += 1
        while index < len(lines):
            row = _cells(lines[index])
            if row is None:
                break
            if _separator(row):
                index += 1
                continue
            if len(row) != len(cells):
                broken = True
                break
            rows.append({mapped[i]: row[i] for i in range(len(cells)) if mapped[i]})
            index += 1
        if not broken:
            chosen = rows
    return chosen


def evidence_problems(body, head):
    """Why the evidence table does not cover this head. Empty means it does. The body is not executed."""
    if not isinstance(body, str):
        return ["body"]
    text = body.replace("\r\n", "\n").replace("\r", "\n")[:BODY_LIMIT]
    problems = []
    record, previous, author_errors = parse_author(text)
    if any("person author" in error for error in author_errors):
        problems.append("author-model")
        families = set()
        tool = model = None
    elif record is None or any("disagree" in error or "conflicts" in error for error in author_errors):
        problems.append("author")
        families = set()
        tool = model = None
    else:
        tool, model = record
    if tool == "사람" and model == "없음":
        families = set()
    elif tool:
        families = set()
        author = model_family(model)
        if author is None:
            problems.append("unknown-family")
        else:
            families.add(author)
    for name in previous:
        family = model_family(name)
        if family is None:
            problems.append("unknown-family")
        else:
            families.add(family)
    rows = evidence_table(text)
    if rows is None:
        problems.append("table")
        return problems
    seen = {}
    for row in rows:
        key = AXIS_KEYS.get(row.get("axis", "").strip().lower())
        if key is None:
            problems.append("axis-name")
            continue
        if key in seen:
            problems.append("duplicate")
        seen[key] = row
    wanted = (head or "").lower()
    for key in ("standards", "spec", "bug", "security"):
        row = seen.get(key)
        if row is None:
            problems.append("axis-" + key)
            continue
        reviewer = row.get("model", "")
        if _not_applicable(reviewer):
            if key in ("standards", "spec"):
                problems.append("not-applicable")
            if any(row.get(column, "").strip() != "0" for column in ("p0", "p1", "p2")):
                problems.append("p0")
        elif reviewer.strip() == "" or reviewer.strip() == "미실행":
            problems.append("model")
        else:
            family = model_family(reviewer)
            if family is None:
                problems.append("unknown-family")
            elif family in families:
                problems.append("same-family")
            if not _integer(row.get("p0", "")):
                problems.append("p0")
            if not _integer(row.get("p1", "")):
                problems.append("p1")
        sha = row.get("sha", "").strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha) or sha.lower() != wanted:
            problems.append("sha")
    return problems


def missing(repo, number, head, base, read=read_api):
    pull = read(f"repos/{repo}/pulls/{number}")
    # This pull request's base ref only. A different base is not evidence. The event base SHA
    # is then checked against the default branch, because a rerun keeps the old BASE_SHA.
    default = default_base(repo, pull, read)
    if default is None or not event_base_on_default(repo, base, default, read):
        return [BASE_REF]
    # None means a team profile: any creator still counts. A 1-person profile counts the owner
    # and STATUS_ACTORS only, and treats every other creator as failure.
    solo = not team_profile(repo, base, read)
    allowed = status_actors(repo, read) if solo else None
    # The open pull request's file and commit lists follow its current head, which can move
    # after this event. review/independent and review/security follow compare(base, head).
    patterns = COMMON_PATHS + DEPENDENCY_FILES + project_paths(repo, base, read)
    pinned, _ = pinned_change(repo, base, head, read)
    if pinned is None:
        touched = True
    else:
        touched = any(matches(entry.get(key, ""), patterns) for entry in pinned
                      for key in ("filename", "previous_filename"))
    needed = [INDEPENDENT]
    # Compare stops at 300 files. A hidden path cannot be ruled out.
    # Dependabot uses this same path rule. A version bump is not exempt.
    if pinned is None or touched:
        needed.append(SECURITY)
    statuses = status_list(read(f"repos/{repo}/commits/{head}/statuses?per_page=100"))
    # The list is newest first. An older success does not erase a newer failure.
    # An untrusted creator is failure, so it also does not reveal an older trusted success.
    newest = {}
    for status in statuses:
        context = status["context"]
        if context in newest:
            continue
        if context in (INDEPENDENT, SECURITY):
            newest[context] = reviewed_state(status, allowed)
        else:
            newest[context] = status["state"]
    present = set(newest)
    for context in (INDEPENDENT, SECURITY):
        if context not in needed and context in present:
            needed.append(context)
    passed = {context for context, state in newest.items() if state == "success"}
    # Success counts only when it is posted on this head. A prior SHA is not evidence.
    result = [context for context in needed if context not in passed]
    # The owner comment is tied to this SHA. A posted status under another name does not replace it.
    if pinned is None:
        needs_owner = True
    else:
        introduced = touches_agents(pinned) and blob_has_team_line(repo, head, read)
        needs_owner = one_way(pinned, False) or profile_line_changes(pinned) or introduced
    if needs_owner and solo and not owner_approved(repo, number, head, read):
        result.append(OWNER)
    # The body is the current pull request text. This run's head is the event SHA, not a later push.
    # Dependabot is included. An empty body is not evidence.
    if isinstance(pull, dict):
        found = evidence_problems(pull.get("body"), head)
        if found:
            detail = ", ".join(found)
            if "unknown-family" in found:
                detail += "; expected family " + FAMILY_NAMES
            print("review evidence: " + detail)
            result.append(EVIDENCE)
    return result


def main(env=os.environ, read=read_api):
    try:
        repo, number = env["REPO"], env["PR_NUMBER"]
        head, base = env.get("HEAD_SHA") or "", env.get("BASE_SHA") or ""
        # A caller without the event SHAs reads the current head, so a new push invalidates an older comment.
        if head == "" or base == "":
            pull = read(f"repos/{repo}/pulls/{number}")
            head = head or pull["head"]["sha"]
            base = base or pull["base"]["sha"]
        absent = missing(repo, number, head, base, read)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"review status UNVERIFIED: {error}", file=sys.stderr)
        return 2
    if absent:
        if BASE_REF in absent:
            print(f"review status FAIL on {head}: base is not the repository default branch")
        else:
            print(f"review status MISSING on {head}: " + ", ".join(absent)
                  + "; run the review, set the status on this head, then re-run this job")
        return 1
    print(f"review status PASS on {head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
