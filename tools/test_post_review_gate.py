"""Mac-side review/gate poster. HTTP is mocked. No key material is committed."""

import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import post_review_gate as gate
import check_review_status as review

HEAD = "a" * 40
OTHER = "c" * 40
BASE = "b" * 40
REPO = "minjunkim-dev/repo-baseline"
OWNER = "minjunkim-dev"
API = "https://api.github.com"


def evidence(head, security="해당 없음: 신뢰 경계 변경 아님", standards="Sonnet 5.5"):
    lines = [
        "Author: Cursor 클라우드 에이전트 / grok-4.7", "",
        "| axis | model | effort | head SHA | P0 | P1 | P2 | result |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| Standards | {standards} | high | {head} | 0 | 0 | 0 | pass |",
        f"| Spec | Sonnet 5.5 | high | {head} | 0 | 0 | 0 | pass |",
        f"| 버그 찾기 | Opus 5.5 | high | {head} | 0 | 0 | 0 | pass |",
        f"| Security | {security} | 해당 없음 | {head} | 0 | 0 | 0 | pass |",
    ]
    return "\n".join(lines) + "\n"


def pull(head=HEAD, state="open", body=None, user=OWNER, files_commit_count=1, ref="main"):
    return {
        "state": state,
        "body": evidence(head) if body is None else body,
        "user": {"login": user},
        "head": {"sha": head},
        "base": {"sha": BASE, "ref": ref},
        "commits": files_commit_count,
    }


def status(context, state="success", login=OWNER):
    return {"context": context, "state": state, "creator": {"login": login}}


def comment(head, login=OWNER, edited=False):
    stamp = "2026-11-06T00:00:00Z"
    return {
        "user": {"login": login},
        "body": f"되돌리기 어려움 승인: {head}\n",
        "created_at": stamp,
        "updated_at": "2026-11-06T00:00:01Z" if edited else stamp,
    }


class Scripted:
    """Checker-shaped read. Status and comment endpoints are already page lists."""

    def __init__(self, repo_pull, files, statuses, comments=None, commits=None):
        self.pull = repo_pull
        self.files = files
        self.statuses = statuses
        self.comments = comments or []
        self.commits = commits or [{"sha": HEAD, "commit": {"committer": {"date": "2026-11-06T00:00:00Z"}}}]
        self.agents = None

    def read(self, endpoint):
        if endpoint == f"repos/{REPO}/pulls/7":
            return self.pull
        if endpoint == f"repos/{REPO}":
            return {"default_branch": "main", "owner": {"login": OWNER}}
        if endpoint == f"repos/{REPO}/compare/{BASE}...main":
            return {"status": "identical"}
        if endpoint.startswith(f"repos/{REPO}/contents/"):
            if self.agents is not None and "AGENTS.md" in endpoint:
                return {"content": base64.b64encode(self.agents.encode()).decode(), "encoding": "base64"}
            raise subprocess.CalledProcessError(1, endpoint, stderr="HTTP 404")
        if endpoint == f"repos/{REPO}/compare/{BASE}...{self.pull['head']['sha']}":
            return {"files": self.files, "commits": self.commits}
        if endpoint == f"repos/{REPO}/commits/{self.pull['head']['sha']}/statuses?per_page=100":
            return [self.statuses]
        if endpoint == f"repos/{REPO}/issues/7/comments?per_page=100":
            return [self.comments]
        if endpoint == f"repos/{REPO}/pulls/7/commits?per_page=100":
            return [self.commits]
        raise AssertionError(endpoint)


def decide(scripted, sha=HEAD):
    return gate.decide(REPO, "7", sha, scripted.read)


class DecideTests(unittest.TestCase):
    def test_posts_success_from_the_evidence_table_without_review_statuses(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        found = decide(Scripted(pull(), files, []))
        self.assertEqual(found.kind, "success")
        self.assertEqual(found.sha, HEAD)
        self.assertNotIn(review.INDEPENDENT, found.detail)
        self.assertNotIn(review.SECURITY, found.detail)

    def test_a_security_model_in_the_table_does_not_require_a_security_status(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        body = evidence(HEAD, security="Opus 5.5")
        found = decide(Scripted(pull(body=body), files, []))
        self.assertEqual(found.kind, "success")
        failed = [status(review.INDEPENDENT, state="failure"), status(review.SECURITY, state="failure")]
        self.assertEqual(decide(Scripted(pull(body=body), files, failed)).kind, "success")

    def test_a_trust_boundary_path_needs_the_owner_comment(self):
        files = [{"filename": ".github/repository-settings.json", "patch": "@@\n-a\n+b\n"}]
        bare = decide(Scripted(pull(), files, []))
        self.assertEqual(bare.kind, "failure")
        self.assertIn(review.OWNER, bare.detail)
        self.assertNotIn(review.SECURITY, bare.detail)
        approved = decide(Scripted(pull(), files, [], comments=[comment(HEAD)]))
        self.assertEqual(approved.kind, "success")
        edited = decide(Scripted(pull(), files, [], comments=[comment(HEAD, edited=True)]))
        self.assertEqual(edited.kind, "failure")
        source = Path(gate.__file__).read_text(encoding="utf-8")
        self.assertNotIn("graphql", source)
        self.assertNotIn("lastEditedAt", source)

    def test_head_mismatch_and_a_closed_pull_do_not_count_as_evidence_failure(self):
        files = [{"filename": "README.md"}]
        mismatch = decide(Scripted(pull(head=OTHER), files, [status(review.INDEPENDENT)]), sha=HEAD)
        self.assertEqual(mismatch.kind, "skip")
        self.assertEqual(mismatch.detail, "head")
        closed = decide(Scripted(pull(state="closed"), files, [status(review.INDEPENDENT)]))
        self.assertEqual(closed.kind, "skip")
        self.assertEqual(closed.detail, "closed")

    def test_a_team_profile_ignores_a_bot_review_status(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        scripted = Scripted(pull(), files, [status(review.INDEPENDENT, login="github-actions[bot]")])
        scripted.agents = "프로필: 팀\n"
        found = decide(scripted)
        self.assertEqual(found.kind, "success")
        self.assertNotIn(review.INDEPENDENT, found.detail)

    def test_same_family_evidence_fails_and_an_actions_status_does_not(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        same = decide(Scripted(pull(body=evidence(HEAD, standards="grok-4.7")), files, []))
        self.assertEqual(same.kind, "failure")
        self.assertIn(review.EVIDENCE, same.detail)
        forged = [status(review.INDEPENDENT, login="github-actions[bot]"), status(review.INDEPENDENT)]
        found = decide(Scripted(pull(), files, forged))
        self.assertEqual(found.kind, "success")
        self.assertNotIn(review.INDEPENDENT, found.detail)

    def test_dependabot_pin_bump_needs_the_same_gate_as_any_author(self):
        patch = "\n".join([
            "@@ -1 +1 @@",
            "-        uses: actions/checkout@" + "a" * 40 + " # v4.2.1",
            "+        uses: actions/checkout@" + "b" * 40 + " # v4.2.1",
        ])
        files = [{"filename": ".github/workflows/check.yml", "status": "modified", "patch": patch}]
        bot = pull(user="dependabot[bot]")
        bare = decide(Scripted(bot, files, []))
        self.assertEqual(bare.kind, "failure")
        self.assertIn(review.OWNER, bare.detail)
        self.assertNotIn(review.INDEPENDENT, bare.detail)
        self.assertNotIn(review.SECURITY, bare.detail)
        empty = pull(body="", user="dependabot[bot]")
        statuses = [status(review.INDEPENDENT), status(review.SECURITY)]
        missing_table = decide(Scripted(empty, files, statuses, comments=[comment(HEAD)]))
        self.assertEqual(missing_table.kind, "failure")
        self.assertIn(review.EVIDENCE, missing_table.detail)
        approved = decide(Scripted(bot, files, statuses, comments=[comment(HEAD)]))
        self.assertEqual(approved.kind, "success")
        person = pull()
        self.assertEqual(decide(Scripted(person, files, [])).kind, "failure")
        self.assertEqual(decide(Scripted(person, files, statuses, comments=[comment(HEAD)])).kind, "success")

    def test_a_different_base_posts_nothing(self):
        files = [{"filename": "README.md"}]
        found = decide(Scripted(pull(ref="side"), files, [status(review.INDEPENDENT)]))
        self.assertEqual(found.kind, "skip")
        self.assertEqual(found.detail, "base")


def _key(mode=0o600):
    directory = tempfile.TemporaryDirectory()
    path = Path(directory.name) / "review-gate.pem"
    path.write_text("not a real key\n", encoding="utf-8")
    os.chmod(path, mode)
    return directory, path


class FakeHub:
    def __init__(self, repo_pull, files, statuses):
        self.pull = repo_pull
        self.files = files
        self.statuses = statuses
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, dict(headers), body))
        path = url[len(API):]
        if path == f"/repos/{REPO}/pulls/7":
            return self._json(self.pull)
        if path == f"/repos/{REPO}":
            return self._json({"default_branch": "main", "owner": {"login": OWNER}})
        if path == f"/repos/{REPO}/compare/{BASE}...main":
            return self._json({"status": "identical"})
        if path == f"/repos/{REPO}/compare/{BASE}...{self.pull['head']['sha']}":
            return self._json({"files": self.files, "commits": []})
        if path.startswith(f"/repos/{REPO}/contents/"):
            return 404, {}, b""
        if path == f"/repos/{REPO}/commits/{self.pull['head']['sha']}/statuses?per_page=100":
            return self._json(self.statuses)
        if path == f"/repos/{REPO}/installation":
            return self._json({"id": 99})
        if path == "/app/installations/99/access_tokens":
            return self._json({"token": "ghs_test_token"})
        if path == f"/repos/{REPO}/statuses/{self.pull['head']['sha']}":
            return 201, {}, json.dumps({"context": body["context"], "state": body["state"]}).encode()
        raise AssertionError(path)

    @staticmethod
    def _json(payload, status=200):
        return status, {}, json.dumps(payload).encode()


class HttpTests(unittest.TestCase):
    def env(self, key):
        return {
            "GH_TOKEN": "ghp_mac_read",
            "REVIEW_GATE_APP_ID": "424242",
            "REVIEW_GATE_APP_KEY": str(key),
            "REVIEW_GATE_API": API,
        }

    def hub(self, head=HEAD, statuses=None, state="open"):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        statuses = [status(review.INDEPENDENT)] if statuses is None else statuses
        return FakeHub(pull(head=head, state=state), files, statuses)

    def test_dry_run_reads_evidence_and_does_not_mint_or_post(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--dry-run"],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 0)
        urls = [url for _, url, _, _ in hub.calls]
        self.assertTrue(any(url.endswith("/pulls/7") for url in urls))
        self.assertFalse(any("access_tokens" in url or "/statuses/" in url or "check-runs" in url for url in urls))
        auths = {headers["Authorization"] for _, _, headers, _ in hub.calls}
        self.assertEqual(auths, {"Bearer ghp_mac_read"})

    def test_success_posts_one_status_with_the_installation_token(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 0)
        posts = [item for item in hub.calls if item[0] == "POST" and item[1].endswith(f"/statuses/{HEAD}")]
        self.assertEqual(len(posts), 1)
        _, url, headers, body = posts[0]
        self.assertEqual(body, {
            "state": "success", "context": "review/gate", "description": f"review/gate success {HEAD}",
        })
        self.assertEqual(headers["Authorization"], "Bearer ghs_test_token")
        self.assertNotIn("check-runs", url)
        minted = [item for item in hub.calls if item[1].endswith("/access_tokens")]
        self.assertEqual(len(minted), 1)
        self.assertEqual(minted[0][3], {
            "repositories": ["repo-baseline"], "permissions": {"statuses": "write"},
        })
        self.assertEqual(minted[0][2]["Authorization"].count("."), 2)
        reads = [item for item in hub.calls if item[0] == "GET" and "/installation" not in item[1]]
        self.assertTrue(reads)
        self.assertTrue(all(item[2]["Authorization"] == "Bearer ghp_mac_read" for item in reads))
        self.assertTrue(all(item[2]["Authorization"] != "Bearer ghs_test_token" for item in hub.calls if item[0] == "GET"))

    def test_bad_evidence_posts_failure_for_that_sha_only(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub(statuses=[status(review.INDEPENDENT, login="github-actions[bot]")])
        hub.pull = pull(body=evidence(HEAD, standards="grok-4.7"))
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 1)
        posts = [item for item in hub.calls if item[0] == "POST" and item[1].endswith(f"/statuses/{HEAD}")]
        self.assertEqual(posts[0][3]["state"], "failure")
        self.assertEqual(posts[0][3]["context"], "review/gate")
        self.assertFalse(any(item[0] == "GET" and "/commits/" in item[1] and "/statuses" in item[1] for item in hub.calls))

    def test_head_mismatch_does_not_post(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub(head=OTHER)
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 1)
        self.assertFalse(any("/statuses/" in url or "access_tokens" in url for _, url, _, _ in hub.calls))

    def test_actions_runtime_and_a_world_readable_key_do_not_post(self):
        def boom(*_args, **_kwargs):
            raise AssertionError("request")
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--dry-run"],
            {"GITHUB_ACTIONS": "true", "GH_TOKEN": "ghp_mac_read"}, boom)
        self.assertEqual(code, 2)
        directory, key = _key(0o644)
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 2)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in hub.calls))

    def test_rejects_a_key_inside_the_repository_or_a_symlink(self):
        inside = gate.ROOT / ".review-gate-test.pem"
        inside.write_text("x\n", encoding="utf-8")
        self.addCleanup(inside.unlink)
        os.chmod(inside, 0o600)
        self.assertEqual(gate.key_problem(inside, gate.ROOT), "inside repository")
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        link = Path(directory.name) / "link.pem"
        link.symlink_to(key)
        self.assertEqual(gate.key_problem(link, gate.ROOT), "symlink")
        self.assertIsNone(gate.key_problem(key, gate.ROOT))

    def test_jwt_claims_and_openssl_signature(self):
        token = gate.build_jwt(424242, "ignored", 1700000000, sign=lambda data, path: b"\x01\x02")
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        self.assertEqual(claims, {"iat": 1700000000 - 60, "exp": 1700000000 - 60 + 540, "iss": "424242"})
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        key = Path(directory.name) / "app.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(key)],
            check=True, capture_output=True)
        os.chmod(key, 0o600)
        signed = gate.build_jwt(7, key, 1700000000).encode()
        header, body, signature = signed.split(b".")
        signing = header + b"." + body
        sig = base64.urlsafe_b64decode(signature + b"=" * (-len(signature) % 4))
        pub = Path(directory.name) / "pub.pem"
        subprocess.run(["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(pub)], check=True, capture_output=True)
        sig_path = Path(directory.name) / "sig.bin"
        sig_path.write_bytes(sig)
        data_path = Path(directory.name) / "data.bin"
        data_path.write_bytes(signing)
        verified = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(pub), "-signature", str(sig_path), str(data_path)],
            check=True, capture_output=True, text=True)
        self.assertIn("Verified OK", verified.stdout)


if __name__ == "__main__":
    unittest.main()
