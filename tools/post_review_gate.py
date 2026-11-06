#!/usr/bin/env python3
"""Post the review/gate commit status for one pull request head (POLICY.md §5).

The status is the branch-protection context pinned to a dedicated GitHub App.
Only that App's app_id satisfies the pin. A workflow GITHUB_TOKEN posts as
app 15368, so the same context name from Actions does not. This file runs on
the owner's Mac (later the Mac Studio server). It refuses to run under
GITHUB_ACTIONS. The private key path is REVIEW_GATE_APP_KEY and is never
written here. Reads use GH_TOKEN. The installation token is used for the
single status POST and is requested only for this repository's statuses.

--dry-run reads the evidence and prints the decision. It does not mint a
token and does not POST. A conclusive failure on a real run POSTs state
failure on that head so an older success from this App does not remain.
A head mismatch, a closed pull request, or a base that is not the default
branch posts nothing. Transport and key errors post nothing.
"""

import argparse
import base64
from contextlib import redirect_stdout
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
    """GET/GraphQL with the read token. 404 and 406 raise CalledProcessError so the checker can branch."""

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
        if endpoint.startswith(review.FORCE_PUSHES):
            return self._force_pushes(endpoint[len(review.FORCE_PUSHES):])
        comments = review.comment_list_target(endpoint)
        if comments is not None:
            return self._comments(*comments)
        if "per_page" in endpoint:
            return self._pages("/" + endpoint)
        payload, _ = self._json("GET", "/" + endpoint)
        return payload

    def read_diff(self, endpoint):
        payload, _ = self._json("GET", "/" + endpoint, accept="application/vnd.github.diff")
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

    def _comments(self, repo, number):
        owner, name = repo.split("/", 1)
        query = (
            "query($owner:String!,$name:String!,$number:Int!,$cursor:String){"
            "repository(owner:$owner,name:$name){pullRequest(number:$number){"
            "comments(first:100,after:$cursor){nodes{author{login} body createdAt updatedAt "
            "lastEditedAt includesCreatedEdit}pageInfo{hasNextPage endCursor}}}}}"
        )
        pages = []
        cursor = None
        for _ in range(20):
            variables = {"owner": owner, "name": name, "number": int(number), "cursor": cursor}
            payload, _ = self._json("POST", "/graphql", {"query": query, "variables": variables})
            try:
                connection = payload["data"]["repository"]["pullRequest"]["comments"]
                nodes = connection["nodes"]
                info = connection["pageInfo"]
            except (TypeError, KeyError):
                raise ValueError("approval comments") from None
            pages.append([review.comment_record(node) for node in nodes])
            if not info.get("hasNextPage"):
                return pages
            cursor = info.get("endCursor")
            if not isinstance(cursor, str) or cursor == "":
                raise ValueError("approval comments")
        raise ValueError("approval comments")

    def _force_pushes(self, suffix):
        repo, number = suffix.rsplit("/", 1)
        owner, name = repo.split("/", 1)
        query = (
            "query($owner:String!,$name:String!,$number:Int!){"
            "repository(owner:$owner,name:$name){pullRequest(number:$number){"
            "timelineItems(last:20,itemTypes:[HEAD_REF_FORCE_PUSHED_EVENT]){"
            "nodes{... on HeadRefForcePushedEvent{createdAt beforeCommit{oid}}}}}}}"
        )
        payload, _ = self._json(
            "POST", "/graphql",
            {"query": query, "variables": {"owner": owner, "name": name, "number": int(number)}})
        try:
            nodes = payload["data"]["repository"]["pullRequest"]["timelineItems"]["nodes"]
        except (TypeError, KeyError):
            raise ValueError("force pushes") from None
        return review.force_push_events(nodes)


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


def _security_row_needs_status(body):
    if not isinstance(body, str):
        return True
    rows = review.evidence_table(body.replace("\r\n", "\n").replace("\r", "\n")[:review.BODY_LIMIT])
    if not rows:
        return True
    for row in rows:
        if review.AXIS_KEYS.get(row.get("axis", "").strip().lower()) != "security":
            continue
        return not review._not_applicable(row.get("model", ""))
    return True


def _on_head(repo, head, base, pull, read):
    """Review statuses that must be success on this SHA. A carried status is not enough.
    A version-only Dependabot bump is the checker's exemption and needs neither."""
    pinned, commits = review.pinned_change(repo, base, head, read)
    bump = pinned is not None and commits is not None and review.dependabot_bump(pull, commits, pinned)
    if bump:
        return []
    patterns = review.COMMON_PATHS + review.DEPENDENCY_FILES + review.project_paths(repo, base, read)
    touched = pinned is None or any(
        review.matches(entry.get(key) or "", patterns)
        for entry in pinned for key in ("filename", "previous_filename"))
    solo = not review.team_profile(repo, base, read)
    allowed = review.status_actors(repo, read) if solo else None
    newest = {}
    for status in review.status_list(read(f"repos/{repo}/commits/{head}/statuses?per_page=100")):
        context = status["context"]
        if context in newest or context not in (review.INDEPENDENT, review.SECURITY):
            continue
        newest[context] = review.reviewed_state(status, allowed)
    gaps = []
    if newest.get(review.INDEPENDENT) != "success":
        gaps.append(review.INDEPENDENT)
    need_security = touched or _security_row_needs_status(pull.get("body")) or review.SECURITY in newest
    if need_security and newest.get(review.SECURITY) != "success":
        gaps.append(review.SECURITY)
    return gaps


def decide(repo, number, sha, read, read_diff):
    """Evidence for this owner/repo/PR/SHA. skip and unverified must not POST."""
    notes = io.StringIO()
    try:
        with redirect_stdout(notes):
            return _decide(repo, number, sha, read, read_diff)
    finally:
        text = notes.getvalue()
        if text:
            print(text, file=sys.stderr, end="" if text.endswith("\n") else "\n")


def _decide(repo, number, sha, read, read_diff):
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
        absent = review.missing(repo, number, head, base, read, read_diff)
        if review.BASE_REF in absent:
            return Decision("skip", "base", head)
        gaps = [item for item in absent if item != review.BASE_REF]
        gaps.extend(item for item in _on_head(repo, head, base, pull, read) if item not in gaps)
        if gaps:
            return Decision("failure", ",".join(gaps), head)
        return Decision("success", "", head)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        return Decision("unverified", f"{type(error).__name__}", sha)


def mint_and_post(base, app_id, key_path, repo, sha, state, request, now, sign=None):
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
    body = {"state": state, "context": CONTEXT, "description": f"review/gate {state} {sha}"}
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


def run(argv, env, request, now=None, sign=None):
    parser = argparse.ArgumentParser(description="Post review/gate for one pull request head.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    now = time.time if now is None else now
    if env.get("GITHUB_ACTIONS"):
        print("review gate refused: GITHUB_ACTIONS is set", file=sys.stderr)
        return 2
    if not _repo_ok(args.repo) or not args.pr.isdigit() or args.pr.startswith("0") or not review.full_oid(args.sha):
        print("review gate refused: repo, pr, or sha", file=sys.stderr)
        return 2
    token = env.get("GH_TOKEN") or ""
    if not token:
        print("review gate refused: GH_TOKEN must be the Mac gh token", file=sys.stderr)
        return 2
    base = (env.get("REVIEW_GATE_API") or API).rstrip("/")
    reader = Reader(base, token, request)
    decision = decide(args.repo, args.pr, args.sha, reader.read, reader.read_diff)
    report = {"result": "dry-run" if args.dry_run else "post", "kind": decision.kind,
              "state": decision.state if decision.posts else None, "context": CONTEXT,
              "repo": args.repo, "sha": decision.sha, "detail": decision.detail}
    if args.dry_run or not decision.posts:
        print(json.dumps(report, ensure_ascii=False))
        if not args.dry_run and decision.kind == "unverified":
            print(f"review gate UNVERIFIED: {decision.detail}", file=sys.stderr)
        return decision.code
    problem = None
    app_id = parse_app_id(env.get("REVIEW_GATE_APP_ID"))
    key = Path(env.get("REVIEW_GATE_APP_KEY") or "")
    if app_id is None:
        problem = "REVIEW_GATE_APP_ID"
    elif env.get("REVIEW_GATE_APP_KEY"):
        problem = key_problem(key, ROOT)
    else:
        problem = "REVIEW_GATE_APP_KEY"
    if problem:
        print(f"review gate refused: {problem}", file=sys.stderr)
        return 2
    try:
        mint_and_post(base, app_id, key, args.repo, decision.sha, decision.state, request, now(), sign)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return decision.code


def main(argv=None, env=None, request=None, now=None, sign=None):
    return run(argv if argv is not None else sys.argv[1:], env if env is not None else os.environ,
               request or http_request, now, sign)


if __name__ == "__main__":
    raise SystemExit(main())
