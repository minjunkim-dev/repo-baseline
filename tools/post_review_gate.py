#!/usr/bin/env python3
"""Post the review/gate commit status for one pull request head (POLICY.md §5).

The status is the branch-protection context pinned to a dedicated GitHub App.
Only that App's app_id satisfies the pin. A workflow GITHUB_TOKEN posts as
app 15368, so the same context name from Actions does not. This file runs on
the owner's Mac (later the Mac Studio server). It refuses to run under
GITHUB_ACTIONS. The private key path is REVIEW_GATE_APP_KEY and is never
written here. Reads use GH_TOKEN, the gate account's read-only token, not the
developer gh token. The installation token is used for the
single status POST and is requested only for this repository's statuses.

--dry-run reads and does not mint a token, post a status, or merge.
A plain real run never posts success. Passing evidence posts pending, which
replaces an older success from this App. Failing evidence posts failure.
--merge is the only success path. It requires a ready pull request, no armed
auto-merge, every other required check green, and no unresolved review thread.
review/gate itself may still be pending. It posts success only then, re-reads
the parsed author, table, and approval snapshot, and squash-merges with
--match-head-commit. A failed recheck or a failed merge posts failure on that
same SHA. This is not an atomic freshness guarantee: a crash after the success
post can leave it, and a body edit can race the recheck. There is no webhook
and no new App permission. The installation token is used for the status POST
only and is never given to gh. gh merge uses the developer login, not GH_TOKEN.
"""

import argparse
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_review_status as review  # noqa: E402

CONTEXT = "review/gate"
API = "https://api.github.com"
POLL_LIMIT = 3
POLL_WAIT = 2
# Other required checks only. Approval comments stay on REST updated_at.
READINESS_QUERY = """
query($owner:String!,$name:String!,$number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      reviewDecision
      reviewThreads(first:100) {
        pageInfo { hasNextPage }
        nodes { isResolved }
      }
      commits(last:1) {
        nodes {
          commit {
            oid
            statusCheckRollup {
              contexts(first:100) {
                pageInfo { hasNextPage }
                nodes {
                  __typename
                  ... on CheckRun { name conclusion status isRequired }
                  ... on StatusContext { context state isRequired }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
ACCEPT = "application/vnd.github+json"
USER_AGENT = "repo-baseline-review-gate"


class Decision:
    """What to tell the operator, and whether a status POST is allowed."""

    def __init__(self, kind, detail, sha):
        self.kind = kind  # success, failure, skip, unverified
        self.detail = detail
        self.sha = sha

    @property
    def posts(self):
        return self.kind in ("success", "failure")

    @property
    def state(self):
        return "success" if self.kind == "success" else "failure"

    @property
    def code(self):
        if self.kind == "success":
            return 0
        if self.kind == "unverified":
            return 2
        return 1


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def sign_rs256(signing_input, key_path):
    """RS256 signature. The key stays in the file openssl opens. It is not an argument value."""
    result = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(key_path), "-binary"],
        input=signing_input, capture_output=True, check=True, timeout=15)
    if not result.stdout:
        raise ValueError("empty signature")
    return result.stdout


def build_jwt(app_id, key_path, now, sign=None):
    """App JWT. iat is 60s in the past. exp is eight minutes ahead, under GitHub's ten."""
    issued = int(now) - 60
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64url(json.dumps(
        {"iat": issued, "exp": issued + 540, "iss": str(app_id)}, separators=(",", ":")).encode())
    signing = f"{header}.{body}".encode()
    signature = (sign or sign_rs256)(signing, key_path)
    return signing.decode() + "." + b64url(signature)


def key_problem(path, repo_root):
    """None when path is a regular 0600 file outside this repository. Otherwise a short reason."""
    if path.is_symlink():
        return "symlink"
    if not path.is_file():
        return "missing"
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != 0o600:
            return f"mode {mode:04o}"
        return None
    return "inside repository"


def parse_app_id(value):
    if not isinstance(value, str) or not value.isdigit() or value.startswith("0"):
        return None
    number = int(value)
    return number if number > 0 else None


def http_request(method, url, headers, body, timeout=30):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def _headers(token, accept=ACCEPT, json_body=False):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


class Reader:
    """REST GET with the read token. 404 and 406 raise CalledProcessError so the checker can branch."""

    def __init__(self, base, token, request):
        self.base = base.rstrip("/")
        self.token = token
        self.request = request

    def _json(self, method, path, body=None, accept=ACCEPT):
        status, headers, raw = self.request(
            method, self.base + path, _headers(self.token, accept, body is not None), body)
        if status in (404, 406):
            raise subprocess.CalledProcessError(1, path, stderr=f"HTTP {status}")
        if status < 200 or status >= 300:
            raise subprocess.CalledProcessError(1, path, stderr=f"HTTP {status}")
        text = raw.decode() if raw else ""
        if accept != ACCEPT:
            return text, headers
        return (json.loads(text) if text else None), headers

    def read(self, endpoint):
        if "per_page" in endpoint:
            return self._pages("/" + endpoint)
        payload, _ = self._json("GET", "/" + endpoint)
        return payload

    def _pages(self, path):
        pages = []
        while path:
            payload, headers = self._json("GET", path)
            if not isinstance(payload, list):
                raise ValueError("page")
            pages.append(payload)
            path = self._next_link(headers.get("Link") or headers.get("link"))
        return pages

    def _next_link(self, header):
        if not isinstance(header, str):
            return None
        for part in header.split(","):
            if 'rel="next"' not in part:
                continue
            start, end = part.find("<"), part.find(">")
            if start == -1 or end < start:
                raise ValueError("link")
            url = part[start + 1:end]
            prefix = self.base + "/"
            if not url.startswith(prefix):
                raise ValueError("link")
            return url[len(self.base):]
        return None


def decide(repo, number, sha, read):
    """Evidence for this owner/repo/PR/SHA. skip and unverified must not POST."""
    notes = io.StringIO()
    try:
        with redirect_stdout(notes):
            return _decide(repo, number, sha, read)
    finally:
        text = notes.getvalue()
        if text:
            print(text, file=sys.stderr, end="" if text.endswith("\n") else "\n")


def _decide(repo, number, sha, read):
    try:
        pull = read(f"repos/{repo}/pulls/{number}")
        if not isinstance(pull, dict):
            raise ValueError("pull request")
        head = (pull.get("head") or {}).get("sha")
        if not isinstance(head, str) or not review.full_oid(head) or head.lower() != sha.lower():
            return Decision("skip", "head", sha)
        if pull.get("state") != "open":
            return Decision("skip", "closed", head)
        base = (pull.get("base") or {}).get("sha")
        if not isinstance(base, str) or not review.full_oid(base):
            raise ValueError("base")
        absent = review.missing(repo, number, head, base, read)
        if review.BASE_REF in absent:
            return Decision("skip", "base", head)
        gaps = [item for item in absent if item != review.BASE_REF]
        if gaps:
            return Decision("failure", ",".join(gaps), head)
        return Decision("success", "", head)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        return Decision("unverified", f"{type(error).__name__}", sha)


def status_description(state, sha, digest=None):
    """Commit-status description. At most 140 characters. The digest is not rechecked by GitHub."""
    text = f"review/gate {state} {sha}"
    if digest:
        text = f"{text} {digest}"
    if len(text) > 140:
        raise ValueError("description")
    return text


def evidence_snapshot(body, head, comment_pages, owner):
    """Parsed author, table, and unedited owner approvals. None when that parse is incomplete.

    HTML comments and other prose are not part of the snapshot. Callers compare this object,
    not the raw pull request body."""
    if not isinstance(body, str) or not review.full_oid(head):
        return None
    text = review.visible_text(body.replace("\r\n", "\n").replace("\r", "\n"))
    if text is None:
        return None
    record, previous, _errors = review.parse_author(text[:review.BODY_LIMIT])
    rows = review.evidence_table(text[:review.BODY_LIMIT])
    if rows is None:
        return None
    by_axis = {}
    for row in rows:
        key = review.AXIS_KEYS.get(str(row.get("axis", "")).strip().lower())
        if key:
            by_axis[key] = row
    canonical = []
    for key in ("standards", "spec", "bug", "security"):
        row = by_axis.get(key)
        if row is None:
            return None
        canonical.append({
            "axis": key,
            "model": str(row.get("model", "")).strip(),
            "effort": str(row.get("effort", "")).strip(),
            "sha": str(row.get("sha", "")).strip().lower(),
            "p0": str(row.get("p0", "")).strip(),
            "p1": str(row.get("p1", "")).strip(),
            "p2": str(row.get("p2", "")).strip(),
            "result": str(row.get("result") or "").strip(),
        })
    approvals = []
    wanted = head.lower()
    for page in comment_pages or []:
        if not isinstance(page, list):
            return None
        for comment in page:
            if not isinstance(comment, dict) or not review.comment_unedited(comment):
                continue
            user = comment.get("user")
            login = user.get("login") if isinstance(user, dict) else None
            if review.bot_creator(login) or not review.same_login(login, owner):
                continue
            if review.approval_sha(comment.get("body")) != wanted:
                continue
            approvals.append({
                "login": login,
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
                "sha": wanted,
            })
    approvals.sort(key=lambda item: (str(item["created_at"]), str(item["login"])))
    payload = {
        "head": wanted,
        "author": [record[0], record[1]] if record else None,
        "previous": list(previous),
        "rows": canonical,
        "approvals": approvals,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return payload, hashlib.sha256(raw).hexdigest()


def _comment_pages(repo, number, read):
    pages = read(f"repos/{repo}/issues/{number}/comments?per_page=100")
    if not isinstance(pages, list):
        raise ValueError("comments")
    return pages


def take_snapshot(repo, number, sha, read):
    pull = read(f"repos/{repo}/pulls/{number}")
    if not isinstance(pull, dict):
        raise ValueError("pull request")
    owner = review.repository_owner(repo, read)
    return evidence_snapshot(pull.get("body"), sha, _comment_pages(repo, number, read), owner)


def parse_readiness(payload):
    """Normalize one GraphQL payload. None when the shape cannot prove the pull request is ready."""
    if not isinstance(payload, dict) or payload.get("errors"):
        return None
    pull = ((payload.get("data") or {}).get("repository") or {}).get("pullRequest")
    if not isinstance(pull, dict):
        return None
    threads = pull.get("reviewThreads") if isinstance(pull.get("reviewThreads"), dict) else {}
    nodes = (pull.get("commits") or {}).get("nodes") if isinstance(pull.get("commits"), dict) else None
    commit = nodes[0].get("commit") if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict) else None
    rollup = commit.get("statusCheckRollup") if isinstance(commit, dict) else None
    contexts = rollup.get("contexts") if isinstance(rollup, dict) else None
    return {
        "review": pull.get("reviewDecision"),
        "threads": threads.get("nodes") if isinstance(threads.get("nodes"), list) else None,
        "threads_more": bool((threads.get("pageInfo") or {}).get("hasNextPage")) if isinstance(threads.get("pageInfo"), dict) else True,
        "head": commit.get("oid") if isinstance(commit, dict) else None,
        "contexts": contexts.get("nodes") if isinstance(contexts, dict) and isinstance(contexts.get("nodes"), list) else None,
        "contexts_more": bool((contexts.get("pageInfo") or {}).get("hasNextPage")) if isinstance(contexts, dict) and isinstance(contexts.get("pageInfo"), dict) else True,
    }


def _required_ok(ctx):
    if ctx.get("name"):
        return ctx.get("status") == "COMPLETED" and ctx.get("conclusion") == "SUCCESS"
    return ctx.get("state") == "SUCCESS"


def _required_pending(ctx):
    if ctx.get("name"):
        return ctx.get("status") in {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED"} or (
            ctx.get("status") != "COMPLETED" and not ctx.get("conclusion"))
    return ctx.get("state") in {"PENDING", "EXPECTED", None, ""}


def readiness_problems(pull, view, sha):
    """Blockers other than this App's own review/gate status. Pending checks are separate from hard failures."""
    problems = []
    if not isinstance(pull, dict) or not isinstance(view, dict):
        return ["checks-unknown"]
    if pull.get("draft") is True:
        problems.append("draft")
    if pull.get("auto_merge"):
        problems.append("auto-merge")
    head = view.get("head")
    if not isinstance(head, str) or head.lower() != sha.lower():
        problems.append("head")
    review_state = view.get("review")
    if review_state in {"CHANGES_REQUESTED", "REVIEW_REQUIRED"}:
        problems.append("review")
    if view.get("threads_more") or not isinstance(view.get("threads"), list):
        problems.append("threads-unknown")
    elif any(not isinstance(item, dict) or item.get("isResolved") is not True for item in view["threads"]):
        problems.append("thread")
    if view.get("contexts_more") or not isinstance(view.get("contexts"), list):
        problems.append("checks-unknown")
    else:
        failed = pending = False
        seen_other = False
        for ctx in view["contexts"]:
            if not isinstance(ctx, dict) or ctx.get("isRequired") is not True:
                continue
            name = ctx.get("name") or ctx.get("context")
            if name == CONTEXT:
                continue
            seen_other = True
            if _required_ok(ctx):
                continue
            if _required_pending(ctx):
                pending = True
            else:
                failed = True
        if not seen_other:
            problems.append("checks-unknown")
        elif failed:
            problems.append("checks-failed")
        elif pending:
            problems.append("checks-pending")
    return problems


def fetch_readiness(base, token, request, repo, number):
    owner, name = repo.split("/", 1)
    status, _, raw = request(
        "POST", base + "/graphql",
        {**_headers(token), "Content-Type": "application/json"},
        {"query": READINESS_QUERY, "variables": {"owner": owner, "name": name, "number": int(number)}})
    if status != 200:
        raise subprocess.CalledProcessError(1, "readiness", stderr=f"HTTP {status}")
    payload = json.loads(raw.decode() or "null")
    parsed = parse_readiness(payload)
    if parsed is None:
        raise ValueError("readiness")
    return parsed


def poll_readiness(base, token, request, repo, number, read, sha, sleep, polls, wait):
    """Re-read pending required checks a bounded number of times. Do not arm auto-merge."""
    last = ["checks-unknown"]
    for attempt in range(polls):
        pull = read(f"repos/{repo}/pulls/{number}")
        view = fetch_readiness(base, token, request, repo, number)
        last = readiness_problems(pull, view, sha)
        if "checks-pending" not in last or any(item != "checks-pending" for item in last):
            return last
        if attempt + 1 == polls:
            return last
        sleep(wait)
    return last


def merge_command(argv, env):
    """Developer gh. The caller strips tokens from env. stderr is returned, not trusted."""
    result = subprocess.run(argv, env=env, capture_output=True, timeout=120)
    return result.returncode, result.stderr.decode("utf-8", "replace")


def merge_child_env(env, secrets):
    """gh's own login. GH_TOKEN and the App key must not ride along, and no secret value is copied."""
    blocked = {"GH_TOKEN", "GITHUB_TOKEN", "REVIEW_GATE_APP_KEY", "REVIEW_GATE_APP_ID"}
    hidden = [item for item in secrets if isinstance(item, str) and item]
    child = {}
    for key, value in env.items():
        if key in blocked or not isinstance(value, str):
            continue
        if any(secret in value for secret in hidden):
            continue
        child[key] = value
    child["GH_PROMPT_DISABLED"] = "1"
    return child


def _redact(text, secrets):
    cleaned = text
    for secret in secrets:
        if isinstance(secret, str) and secret:
            cleaned = cleaned.replace(secret, "[redacted]")
    return cleaned


def mint_and_post(base, app_id, key_path, repo, sha, state, request, now, sign=None, digest=None):
    """Installation token for this repository's statuses only, then one POST to this SHA."""
    jwt = build_jwt(app_id, key_path, now, sign)
    name = repo.split("/", 1)[1]
    installation, _ = _jwt_json(base, "GET", f"/repos/{repo}/installation", jwt, request, None)
    installation_id = installation.get("id") if isinstance(installation, dict) else None
    if type(installation_id) is not int or installation_id <= 0:
        raise ValueError("installation")
    minted, _ = _jwt_json(
        base, "POST", f"/app/installations/{installation_id}/access_tokens", jwt, request,
        {"repositories": [name], "permissions": {"statuses": "write"}})
    token = minted.get("token") if isinstance(minted, dict) else None
    if not isinstance(token, str) or token == "" or token == jwt:
        raise ValueError("token")
    body = {"state": state, "context": CONTEXT, "description": status_description(state, sha, digest)}
    status, _, raw = request(
        "POST", f"{base}/repos/{repo}/statuses/{sha}",
        {**_headers(token), "Content-Type": "application/json"}, body)
    if status not in (200, 201):
        raise subprocess.CalledProcessError(1, "statuses", stderr=f"HTTP {status}")
    posted = json.loads(raw.decode() or "{}")
    if posted.get("context") != CONTEXT or posted.get("state") != state:
        raise ValueError("posted status")
    return posted


def _jwt_json(base, method, path, jwt, request, body):
    headers = _headers(jwt, json_body=body is not None)
    status, response_headers, raw = request(method, base + path, headers, body)
    if status < 200 or status >= 300:
        raise subprocess.CalledProcessError(1, path, stderr=f"HTTP {status}")
    return json.loads(raw.decode() or "null"), response_headers


def _repo_ok(repo):
    return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]+", repo or "") is not None and repo.split("/")[-1] not in {".", ".."}


def _key_ready(env):
    app_id = parse_app_id(env.get("REVIEW_GATE_APP_ID"))
    key = Path(env.get("REVIEW_GATE_APP_KEY") or "")
    if app_id is None:
        return None, None, "REVIEW_GATE_APP_ID"
    if not env.get("REVIEW_GATE_APP_KEY"):
        return None, None, "REVIEW_GATE_APP_KEY"
    problem = key_problem(key, ROOT)
    if problem:
        return None, None, problem
    return app_id, key, None


def _emit(report, code):
    print(json.dumps(report, ensure_ascii=False))
    return code


def _invalidate(base, app_id, key, repo, sha, request, now, sign):
    """Post failure on the SHA that received success. Return the cleanup exception, or None."""
    try:
        mint_and_post(base, app_id, key, repo, sha, "failure", request, now, sign)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"review gate cleanup failed: {type(error).__name__}", file=sys.stderr)
        return error
    return None


def run(argv, env, request, now=None, sign=None, merge=None, sleep=None, polls=POLL_LIMIT, poll_wait=POLL_WAIT):
    parser = argparse.ArgumentParser(description="Post review/gate for one pull request head.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args(argv)
    now = time.time if now is None else now
    sleep = time.sleep if sleep is None else sleep
    merge = merge_command if merge is None else merge
    if env.get("GITHUB_ACTIONS"):
        print("review gate refused: GITHUB_ACTIONS is set", file=sys.stderr)
        return 2
    if not _repo_ok(args.repo) or not args.pr.isdigit() or args.pr.startswith("0") or not review.full_oid(args.sha):
        print("review gate refused: repo, pr, or sha", file=sys.stderr)
        return 2
    token = env.get("GH_TOKEN") or ""
    if not token:
        print("review gate refused: GH_TOKEN must be the gate account read-only token", file=sys.stderr)
        return 2
    base = (env.get("REVIEW_GATE_API") or API).rstrip("/")
    reader = Reader(base, token, request)
    decision = decide(args.repo, args.pr, args.sha, reader.read)
    report = {"result": "dry-run" if args.dry_run else "merge" if args.merge else "post",
              "kind": decision.kind, "state": decision.state if decision.posts else None,
              "context": CONTEXT, "repo": args.repo, "sha": decision.sha, "detail": decision.detail}
    if args.dry_run or not decision.posts:
        if args.dry_run and args.merge and decision.kind == "success":
            try:
                problems = poll_readiness(
                    base, token, request, args.repo, args.pr, reader.read, decision.sha, sleep, 1, 0)
            except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                report["kind"] = "unverified"
                report["state"] = None
                report["detail"] = type(error).__name__
                print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
                return _emit(report, 2)
            if problems:
                report["kind"] = "blocked"
                report["state"] = None
                report["detail"] = ",".join(problems)
                if "auto-merge" in problems:
                    print("review gate refused: auto-merge is armed; disable it with "
                          f"gh pr merge {args.pr} --repo {args.repo} --disable-auto", file=sys.stderr)
                return _emit(report, 1)
        print(json.dumps(report, ensure_ascii=False))
        if not args.dry_run and decision.kind == "unverified":
            print(f"review gate UNVERIFIED: {decision.detail}", file=sys.stderr)
        return decision.code
    app_id, key, problem = _key_ready(env)
    if problem:
        print(f"review gate refused: {problem}", file=sys.stderr)
        return 2
    secrets = [token, str(key)]
    if decision.kind == "failure":
        try:
            mint_and_post(base, app_id, key, args.repo, decision.sha, "failure", request, now(), sign)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
            return 2
        return _emit(report, decision.code)
    # Passing evidence. A plain run posts pending and does not merge.
    snapshot = None
    try:
        snapshot = take_snapshot(args.repo, args.pr, decision.sha, reader.read)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        snapshot = None
    digest = snapshot[1] if snapshot else None
    if not args.merge:
        try:
            mint_and_post(base, app_id, key, args.repo, decision.sha, "pending", request, now(), sign, digest)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
            return 2
        report["kind"] = "pending"
        report["state"] = "pending"
        report["detail"] = "run --merge to post success and squash-merge this sha"
        return _emit(report, 0)
    try:
        problems = poll_readiness(
            base, token, request, args.repo, args.pr, reader.read, decision.sha, sleep, polls, poll_wait)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
        report["kind"] = "unverified"
        report["state"] = None
        report["detail"] = type(error).__name__
        return _emit(report, 2)
    if problems:
        report["kind"] = "blocked"
        report["state"] = None
        report["detail"] = ",".join(problems)
        if "auto-merge" in problems:
            print("review gate refused: auto-merge is armed; disable it with "
                  f"gh pr merge {args.pr} --repo {args.repo} --disable-auto", file=sys.stderr)
        elif "checks-pending" in problems:
            print("review gate refused: required checks still pending; re-run --merge when they pass. "
                  "Do not arm auto-merge.", file=sys.stderr)
        return _emit(report, 1)
    if snapshot is None:
        print("review gate UNVERIFIED: snapshot", file=sys.stderr)
        return 2
    try:
        mint_and_post(base, app_id, key, args.repo, decision.sha, "success", request, now(), sign, digest)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
        return 2
    try:
        again = decide(args.repo, args.pr, decision.sha, reader.read)
        checked = take_snapshot(args.repo, args.pr, decision.sha, reader.read)
        if again.kind != "success" or again.sha.lower() != decision.sha.lower() or checked is None or checked[0] != snapshot[0]:
            raise ValueError("recheck")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        cleanup = _invalidate(base, app_id, key, args.repo, decision.sha, request, now(), sign)
        print(f"review gate recheck failed: {type(error).__name__}", file=sys.stderr)
        report["kind"] = "failure"
        report["state"] = None if cleanup else "failure"
        report["detail"] = "recheck" if cleanup is None else "recheck; cleanup failed"
        return _emit(report, 2 if cleanup else 1)
    argv = ["gh", "pr", "merge", args.pr, "--repo", args.repo, "--squash", "--match-head-commit", decision.sha]
    child = merge_child_env(env, secrets)
    try:
        code, stderr = merge(argv, child)
    except (OSError, subprocess.SubprocessError) as error:
        code, stderr = 1, type(error).__name__
    if code != 0:
        cleanup = _invalidate(base, app_id, key, args.repo, decision.sha, request, now(), sign)
        print(f"review gate merge failed: {code} {_redact(stderr, secrets)}", file=sys.stderr)
        report["kind"] = "failure"
        report["state"] = None if cleanup else "failure"
        report["detail"] = "merge" if cleanup is None else "merge; cleanup failed"
        return _emit(report, 2 if cleanup else 1)
    report["kind"] = "success"
    report["state"] = "success"
    report["detail"] = digest
    return _emit(report, 0)


def main(argv=None, env=None, request=None, now=None, sign=None, merge=None, sleep=None,
         polls=POLL_LIMIT, poll_wait=POLL_WAIT):
    return run(argv if argv is not None else sys.argv[1:], env if env is not None else os.environ,
               request or http_request, now, sign, merge, sleep, polls, poll_wait)


if __name__ == "__main__":
    raise SystemExit(main())
