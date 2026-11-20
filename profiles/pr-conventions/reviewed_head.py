"""Merge queue check: the queued PR head must be the head its review recorded (POLICY §5).

Run it in a `merge_group` job. GitHub names the queue branch `gh-readonly-queue/<base>/pr-<N>-<head SHA>`,
so the SHA the PR was queued at needs no API call. The script reads the PR body with `gh api` and compares
that SHA with the last 「리뷰한 head와 되돌리기:」 line in the body (prompts/review.md 「보고」).

This catches a head that moved after review. It is not a security boundary: anyone who can edit the PR body
can write any SHA there. Two kinds of PR carry no review and pass:
- Dependabot, by the queue commit's author email (no other account can claim that noreply address).
- repo-baseline sync PRs: the Author line names tools/sync_consumers.py and every changed path is the
  manifest or a path it records (POLICY §5 lets those go to the queue without review).

Usage (environment): QUEUE_REF, QUEUE_AUTHOR, BASE_SHA, GITHUB_REPOSITORY, GH_TOKEN.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

DEPENDABOT = "49699333+dependabot[bot]@users.noreply.github.com"
MANIFEST = ".github/repo-baseline.json"
SYNC_AUTHOR = "tools/sync_consumers.py"


def queued(ref):
    """(PR number, head SHA) from a merge queue branch name, or None."""
    match = re.fullmatch(r"gh-readonly-queue/.+/pr-([0-9]+)-([0-9a-f]{40})", ref or "")
    return (match.group(1), match.group(2)) if match else None


def reviewed_head(body):
    """The SHA on the last 「리뷰한 head와 되돌리기:」 line, or None. Later review rounds come last."""
    heads = re.findall(r"^리뷰한 head와 되돌리기:\s*`?([0-9a-f]{40})\b", (body or "").replace("\r\n", "\n"), re.M)
    return heads[-1] if heads else None


def managed_paths(manifest_text):
    """Paths a sync PR may change: the manifest, its copied files, and its block targets."""
    if not manifest_text:
        return set()
    manifest = json.loads(manifest_text)
    paths = {MANIFEST, *manifest.get("files", {})}
    paths.update(block["target"] for block in manifest.get("blocks", {}).values() if "target" in block)
    return paths


def is_sync(body, changed, manifest_text):
    author = next((line for line in (body or "").splitlines() if line.startswith("Author:")), "")
    allowed = managed_paths(manifest_text)
    return SYNC_AUTHOR in author and bool(changed) and set(changed) <= allowed


def verdict(ref, author_email, body, changed, manifest_text):
    """None when the queued head may merge, else the reason it may not."""
    parsed = queued(ref)
    if not parsed:
        return f"머지 큐 브랜치 이름을 읽지 못했습니다: {ref!r}"
    number, head = parsed
    if author_email == DEPENDABOT:
        return None
    if is_sync(body, changed, manifest_text):
        return None
    review = reviewed_head(body)
    if not review:
        return f"PR #{number} 본문 Review 칸에 「리뷰한 head와 되돌리기:」 SHA가 없습니다."
    if review != head:
        return (f"PR #{number}을 큐에 넣은 head {head[:12]}가 리뷰한 head {review[:12]}와 다릅니다. "
                "새 head를 다른 컨텍스트가 다시 리뷰하고 그 SHA로 큐에 넣습니다.")
    return None


def main():
    ref = os.environ.get("QUEUE_REF", "")
    parsed = queued(ref)
    body = ""
    changed = []
    if parsed:
        body = subprocess.check_output(["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/pulls/{parsed[0]}",
                                        "--jq", ".body // \"\""], text=True)
        changed = subprocess.check_output(["git", "diff", "--no-renames", "--name-only",
                                           os.environ["BASE_SHA"], "HEAD"], text=True).split()
    manifest = Path(MANIFEST)
    reason = verdict(ref, os.environ.get("QUEUE_AUTHOR", ""), body, changed,
                     manifest.read_text(encoding="utf-8") if manifest.exists() else "")
    if reason:
        print(f"::error::{reason}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
