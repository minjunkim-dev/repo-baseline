#!/usr/bin/env python3
"""Bring every consumer repo in tools/consumers.json up to this repo-baseline commit.

Usage: python3 tools/sync_consumers.py [--open-prs | --enqueue]

Run it from a clean checkout whose HEAD is origin/main.
- No flag (plan): clone each consumer, apply hash-copy (profiles/hash-copy/apply_baseline.py),
  and print what would change. Nothing is pushed.
- --open-prs: push the change to baseline/sync-<sha7> and open a PR. A consumer without
  .github/repo-baseline.json gets the manifest from consumers.json (a migration PR).
- --enqueue: queue each open sync PR that is sync-only (sync_only() below) at its head SHA.
  This is the standing order in consumers.json ("enqueue": "sync-only", POLICY §5). Running
  this mode is the pipeline carrying out that order, as the repo-office engine does; it is
  not an agent merging on its own. A PR that is not sync-only is left for review and the owner.
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "profiles/hash-copy"))
import apply_baseline  # noqa: E402

CONSUMERS = HERE / "tools/consumers.json"
PREFIX = "baseline/sync-"
PASSING = {"SUCCESS", "SKIPPED", "NEUTRAL"}
# Bots whose PR comments are summaries, not review findings.
SUMMARY_BOTS = {"coderabbitai[bot]", "coderabbitai"}
# Paths a sync PR must never touch without a person reading it (POLICY §4 sensitive paths).
SENSITIVE = re.compile(
    r"\.github/(workflows/|dependabot\.yml$|repository-settings\.json$)"
    r"|(?:.*/)?\.(claude|agents|codex|cursor)/"
    r"|(?:.*/)?(CODEOWNERS|\.mcp\.json|package\.json|go\.mod|go\.sum|Cargo\.toml|pyproject\.toml"
    r"|[^/]*\.lock|[^/]*-lock\.(json|yaml))$")


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def gh_json(*args):
    return json.loads(run("gh", *args) or "null")


def strip_block(text):
    """The text with the ops block taken out, or None when it has no markers."""
    span = apply_baseline.OPS.find_block(text)
    return text[:span[0]] + text[span[1]:] if span else None


def policy(manifest):
    """The manifest without the fields apply_baseline records, so only what to sync remains.

    A file entry's "source" picks what is copied, so it stays; only the top-level source and
    source_commit and each entry's sha256 are records.
    """
    if not isinstance(manifest, dict):
        return manifest
    kept = {k: v for k, v in manifest.items() if k not in ("source", "source_commit")}
    for key in ("files", "blocks"):
        if isinstance(kept.get(key), dict):
            kept[key] = {name: {k: v for k, v in entry.items() if k != "sha256"} if isinstance(entry, dict) else entry
                         for name, entry in kept[key].items()}
    return kept


def sync_only(changed, base, head):
    """Reasons the change is not sync-only; [] when it is.

    changed: every path that differs between base and head (git diff --no-renames).
    base, head: {path: text or None} for every changed path and the manifest.
    The allowlist comes from the base manifest, and the head manifest may differ from it only
    in recorded hashes and commit, so a PR cannot widen what counts as managed.
    """
    reasons = []
    base_text, head_text = base.get(apply_baseline.MANIFEST), head.get(apply_baseline.MANIFEST)
    if base_text is None:
        return ["base has no manifest (migration)"]
    try:
        manifest = json.loads(base_text)
        if policy(json.loads(head_text or "null")) != policy(manifest):
            reasons.append("the manifest changes what is synced (files, blocks or exclude)")
    except (ValueError, AttributeError):
        return ["a manifest is not valid JSON"]
    allowed = {apply_baseline.MANIFEST, *manifest.get("files", {})}
    targets = {entry["target"] for entry in manifest.get("blocks", {}).values()}
    for path in sorted(changed):
        if SENSITIVE.match(path):
            reasons.append(f"{path} is sensitive")
        elif path in targets:
            before, after = strip_block(base.get(path) or ""), strip_block(head.get(path) or "")
            if before is None or after is None or before != after:
                reasons.append(f"{path} changes outside its block")
        elif path not in allowed:
            reasons.append(f"{path} is not managed")
    return reasons


def changelog_since(commit):
    """changelog.d fragments added after commit (none when commit is unknown or not a SHA)."""
    if not (isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit)):
        return []
    try:
        names = run("git", "log", "--diff-filter=A", "--name-only", "--format=", "--end-of-options",
                    f"{commit}..HEAD", "--", "changelog.d", cwd=HERE).split()
    except subprocess.CalledProcessError:
        names = []
    return [(HERE / name).read_text(encoding="utf-8").strip() for name in sorted(set(names)) if (HERE / name).is_file()]


def body(sha, before, migration, changed, check_output):
    door = "어려움" if any(SENSITIVE.match(p) for p in changed) else "쉬움"
    notes = "\n".join(changelog_since(before)) or "- (변경 기록 없음)"
    kind = ("이전 PR이다. hash-copy manifest를 처음 둔다. 기록한 파일은 이미 원본과 같다. 동기화 전용이 아니므로 리뷰를 거친다."
            if migration and set(changed) == {apply_baseline.MANIFEST} else
            "이전 PR이다. hash-copy manifest를 처음 두고, 기록한 파일과 관리 블록을 원본으로 맞춘다. 바뀐 파일은 Evidence에 있다. 동기화 전용이 아니므로 리뷰를 거친다."
            if migration else "동기화 전용 PR이다. 바뀐 바이트는 모두 관리 블록과 해시가 기록된 파일 안에 있다.")
    return f"""Author: 스크립트 / 없음 (repo-baseline tools/sync_consumers.py)

## Summary
repo-baseline `{sha[:7]}`의 공통 파일과 관리 블록으로 맞춘다. {kind}

옮긴 변경 기록:
{notes}

완료 기준: 이 head에서 `apply_baseline.py --check`가 `SAME`이다. 관리 블록과 기록된 파일 밖은 바뀌지 않는다.

## Evidence
- `python3 <repo-baseline>/profiles/hash-copy/apply_baseline.py . --check` → `{check_output}`
- 바뀐 파일: {", ".join(f"`{p}`" for p in sorted(changed))}

## Merge Danger
되돌리기: {door}
영향 범위: repo-baseline이 관리하는 파일과 블록.
되돌리는 법: 이 커밋을 revert한다.
민감한 파일: {", ".join(p for p in sorted(changed) if SENSITIVE.match(p)) or "없음"}

## Review
리뷰어(구현과 다른 컨텍스트, 도구/모델):
고친 것:
남은 지적:
"""


def prepare(consumer, folder):
    """Clone, apply and return (path, migration, previous source_commit, changed paths) or raise."""
    repo = consumer["repo"]
    path = Path(folder) / repo.split("/")[1]
    run("gh", "repo", "clone", repo, str(path), "--", "--quiet", "--depth", "50")
    manifest_path = path / apply_baseline.MANIFEST
    migration = not manifest_path.is_file()
    if migration:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(consumer["manifest"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        before = None
    else:
        before = json.loads(manifest_path.read_text(encoding="utf-8")).get("source_commit")
    apply_baseline.apply(path, force=migration)
    changed = run("git", "diff", "--name-only", "HEAD", cwd=path).splitlines()
    changed += run("git", "ls-files", "--others", "--exclude-standard", cwd=path).splitlines()
    return path, migration, before, sorted(changed)


def open_pr(consumer, path, sha, migration, before, changed, user):
    branch = PREFIX + sha[:7]
    if run("git", "ls-remote", "--heads", "origin", branch, cwd=path):
        return f"skip: {branch} already exists"
    # One open sync PR per consumer: an older one is stale once repo-baseline moves.
    for old in gh_json("pr", "list", "--repo", consumer["repo"], "--state", "open", "--author", user,
                       "--json", "number,headRefName"):
        if old["headRefName"].startswith(PREFIX):
            run("gh", "pr", "close", str(old["number"]), "--repo", consumer["repo"], "--delete-branch",
                "--comment", f"repo-baseline {sha[:7]} 동기화 PR로 대체한다.")
    check = "SAME" if apply_baseline.apply(path, check=True) == [] else "DIFFERS"
    run("git", "switch", "--quiet", "-c", branch, cwd=path)
    run("git", "add", "--all", cwd=path)
    run("git", "commit", "--quiet", "-m", f"chore(baseline): sync with repo-baseline {sha[:7]}", cwd=path)
    run("git", "push", "--quiet", "-u", "origin", branch, cwd=path)
    note = path.parent / "body.md"
    note.write_text(body(sha, before, migration, changed, check), encoding="utf-8")
    return run("gh", "pr", "create", "--repo", consumer["repo"], "--base", "main", "--head", branch,
               "--title", f"chore(baseline): sync with repo-baseline {sha[:7]}", "--body-file", str(note))


def decide(user, pr, detail, comments, threads, commit_authors, sync_reasons, check_differs):
    """Reasons to leave a sync PR for the owner; [] means queue it at its head."""
    reasons = []
    if pr["author"]["login"] != user or pr["isCrossRepository"]:
        reasons.append("not opened by this pipeline")
    if any(login != user for login in commit_authors):
        reasons.append("has commits from someone else")
    checks = [c.get("conclusion") or c.get("state") for c in detail["statusCheckRollup"]]
    if not checks or any(c not in PASSING for c in checks):
        reasons.append("CI not passed")
    if detail["reviews"] or threads:
        reasons.append("has reviews or review threads to judge")
    if any(login not in SUMMARY_BOTS for login in comments):
        reasons.append("has comments to judge")
    if check_differs:
        reasons.append("head differs from this repo-baseline commit")
    return reasons + sync_reasons


def enqueue(repo, folder, user):
    results = []
    owner, name = repo.split("/")
    prs = gh_json("pr", "list", "--repo", repo, "--state", "open", "--json",
                  "number,id,headRefName,headRefOid,author,isCrossRepository")
    for pr in prs:
        if not pr["headRefName"].startswith(PREFIX):
            continue
        number, head = pr["number"], pr["headRefOid"]
        detail = gh_json("pr", "view", str(number), "--repo", repo, "--json",
                         "statusCheckRollup,reviews,baseRefOid,comments,commits")
        threads = gh_json("api", "graphql", "-f", "query=query($o:String!,$n:String!,$p:Int!){repository(owner:$o,name:$n)"
                          "{pullRequest(number:$p){reviewThreads(first:1){totalCount}}}}",
                          "-f", f"o={owner}", "-f", f"n={name}", "-F", f"p={number}")
        thread_count = threads["data"]["repository"]["pullRequest"]["reviewThreads"]["totalCount"]
        comments = [c["author"]["login"] for c in detail["comments"]]
        authors = [a.get("login") for commit in detail["commits"] for a in commit.get("authors", [])]
        path = Path(folder) / f"{name}-{number}"
        run("git", "clone", "--quiet", f"https://github.com/{repo}.git", str(path))
        run("git", "fetch", "--quiet", "origin", head, detail["baseRefOid"], cwd=path)
        run("git", "checkout", "--quiet", head, cwd=path)
        changed = run("git", "diff", "--no-renames", "--name-only", detail["baseRefOid"], head, cwd=path).splitlines()

        def show(rev, file):
            try:
                return run("git", "show", f"{rev}:{file}", cwd=path)
            except subprocess.CalledProcessError:
                return None
        names = set(changed) | {apply_baseline.MANIFEST}
        base = {n: show(detail["baseRefOid"], n) for n in names}
        tip = {n: show(head, n) for n in names}
        try:
            differs = bool(apply_baseline.apply(path, check=True))
        except ValueError:
            differs = True
        reasons = decide(user, pr, detail, comments, thread_count, authors, sync_only(changed, base, tip), differs)
        if reasons:
            results.append(f"#{number}: left for the owner ({'; '.join(reasons)})")
            continue
        run("gh", "api", "graphql", "-f", "query=mutation($id:ID!,$sha:GitObjectID!){enqueuePullRequest("
            "input:{pullRequestId:$id,expectedHeadOid:$sha}){mergeQueueEntry{position}}}",
            "-f", f"id={pr['id']}", "-f", f"sha={head}")
        results.append(f"#{number}: queued at {head}")
    return results


def main(argv):
    mode = argv[1] if len(argv) == 2 else None
    if len(argv) > 2 or mode not in (None, "--open-prs", "--enqueue"):
        print(__doc__, file=sys.stderr)
        return 2
    config = json.loads(CONSUMERS.read_text(encoding="utf-8"))
    run("git", "fetch", "--quiet", "origin", "main", cwd=HERE)
    sha = run("git", "rev-parse", "HEAD", cwd=HERE)
    if run("git", "status", "--porcelain", cwd=HERE) or sha != run("git", "rev-parse", "origin/main", cwd=HERE):
        print("FAILED: run from a clean checkout whose HEAD is origin/main", file=sys.stderr)
        return 2
    if mode == "--enqueue" and config.get("enqueue") != "sync-only":
        print("FAILED: consumers.json has no sync-only standing order", file=sys.stderr)
        return 2
    user = run("gh", "api", "user", "--jq", ".login")
    failed = False
    for consumer in config["consumers"]:
        repo = consumer["repo"]
        with tempfile.TemporaryDirectory() as folder:
            try:
                if mode == "--enqueue":
                    lines = enqueue(repo, folder, user)
                else:
                    path, migration, before, changed = prepare(consumer, folder)
                    if not changed:
                        lines = ["same"]
                    elif mode == "--open-prs":
                        lines = [open_pr(consumer, path, sha, migration, before, changed, user)]
                    else:
                        lines = [("migration: " if migration else "would change: ") + ", ".join(changed)]
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                failed = True
                detail = getattr(error, "stderr", "") or ""
                lines = [f"FAILED: {error} {detail}".strip()]
        for line in lines or ["nothing to do"]:
            print(f"{repo}: {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
