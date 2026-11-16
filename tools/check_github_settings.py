#!/usr/bin/env python3
"""Read GitHub settings and report drift; never change repository settings."""

import copy
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
# Common values every project shares; a project file needs only what differs.
TEMPLATE = Path(__file__).resolve().parents[1] / "templates/github/repository-settings.json"


def placeholders(value, path=""):
    if isinstance(value, dict):
        return [found for key, item in value.items() for found in placeholders(item, f"{path}.{key}" if path else key)]
    if isinstance(value, list):
        return [found for item in value for found in placeholders(item, path)]
    return [path] if isinstance(value, str) and value.startswith("REPLACE") else []


def overlay(base, project):
    """Objects merge key by key and the project value wins; lists and other values are replaced whole."""
    if not isinstance(base, dict) or not isinstance(project, dict):
        return copy.deepcopy(project)
    result = copy.deepcopy(base)
    for key, value in project.items():
        result[key] = overlay(base[key], value) if key in base else copy.deepcopy(value)
    return result


def merged(project, template=None):
    """The project's settings on top of the template's common values.

    A full copy of the template merges to itself, so older project files still work.
    A template value under a path the project declares as an exception is dropped first.
    Template values the project must fill in ("REPLACE...") stop the run here.
    """
    if not isinstance(project, dict):
        raise ValueError("Baseline must be an object")
    template = json.loads(TEMPLATE.read_text(encoding="utf-8")) if template is None else copy.deepcopy(template)
    exceptions = project.get("exceptions", {})
    expected = template.get("expected", {})
    for path in exceptions if isinstance(exceptions, dict) else ():
        parts = path.split(".")
        chain = [expected]
        for part in parts[:-1]:
            chain.append(chain[-1].get(part) if isinstance(chain[-1], dict) else None)
        if isinstance(chain[-1], dict):
            chain[-1].pop(parts[-1], None)
        # An object left empty goes too: GitHub omits an unavailable feature rather than answering {}.
        for depth in range(len(parts) - 1, 0, -1):
            parent, child = chain[depth - 1], chain[depth]
            if isinstance(child, dict) and not child and isinstance(parent, dict):
                parent.pop(parts[depth - 1], None)
    profile = overlay(template, project)
    unfilled = placeholders(profile)
    if unfilled:
        raise ValueError("Fill in the template values first: " + ", ".join(unfilled))
    return profile


def differences(expected, actual, path=""):
    """Compare required fields; omitted required fields are drift, not false."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [path or "<root>"]
        result = []
        for key, value in expected.items():
            name = f"{path}.{key}" if path else key
            if key not in actual:
                result.append(name)
            else:
                result.extend(differences(value, actual[key], name))
        return result
    if type(expected) is not type(actual):
        return [path]
    if isinstance(expected, list):
        # API ordering is irrelevant; duplicates and extra entries still differ.
        expected = sorted(json.dumps(item, sort_keys=True) for item in expected)
        actual = sorted(json.dumps(item, sort_keys=True) for item in actual)
    return [] if expected == actual else [path]


def read_api(endpoint):
    result = subprocess.run(
        ["gh", "api", "--method", "GET", endpoint],
        capture_output=True, text=True, check=True, timeout=60,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


# Required controls cannot disappear when someone edits the baseline.
REQUIRED_FIELDS = {
    "repository": "default_branch visibility allow_merge_commit allow_rebase_merge allow_squash_merge allow_auto_merge delete_branch_on_merge allow_update_branch squash_merge_commit_title squash_merge_commit_message security_and_analysis.dependabot_security_updates.status security_and_analysis.secret_scanning.status security_and_analysis.secret_scanning_push_protection.status",
    "protection": "required_status_checks.strict required_status_checks.checks required_pull_request_reviews.required_approving_review_count required_pull_request_reviews.dismiss_stale_reviews required_pull_request_reviews.require_code_owner_reviews required_pull_request_reviews.require_last_push_approval enforce_admins.enabled required_linear_history.enabled required_conversation_resolution.enabled allow_force_pushes.enabled allow_deletions.enabled lock_branch.enabled",
    "rulesets": "",
    "actions": "enabled allowed_actions sha_pinning_required",
    "allowed_actions": "github_owned_allowed verified_allowed patterns_allowed",
    "workflow_token": "default_workflow_permissions can_approve_pull_request_reviews",
    "fork_policy": "approval_policy",
    "immutable_releases": "enabled",
    "private_vulnerability_reporting": "enabled",
    "dependabot_alerts": "enabled",
    "codeql": "state",
    "codeql_workflow": "path state",
}
# A ruleset as the baseline records it: the rule itself, not ids or timestamps.
RULESET_FIELDS = ("name", "target", "enforcement", "conditions", "rules", "bypass_actors")
# Only advanced setup has a workflow file; default setup must not list it.
ADVANCED_CODEQL = {"codeql_workflow"}
STRING_FIELDS = {
    "default_branch", "visibility", "squash_merge_commit_title", "squash_merge_commit_message",
    "status", "allowed_actions", "default_workflow_permissions", "approval_policy", "state", "path",
}


# Only feature availability can narrow coverage; repository identity and merge policy stay required.
EXCEPTION_PATHS = (set(REQUIRED_FIELDS) - {"repository"} - ADVANCED_CODEQL) | {
    "repository." + field for field in REQUIRED_FIELDS["repository"].split()
    if field.startswith("security_and_analysis.")
} | {"actions.sha_pinning_required"}


def validate_exceptions(profile):
    exceptions = profile.get("exceptions", {})
    if not isinstance(exceptions, dict):
        raise ValueError("Exceptions must be an object")
    for path, entry in exceptions.items():
        if path not in EXCEPTION_PATHS or not isinstance(entry, dict):
            raise ValueError(f"Invalid availability exception: {path}")
        if (set(entry) != {"status", "reason", "evidence"}
                or entry["status"] not in ("unsupported", "not_applicable")
                or any(not isinstance(entry[key], str) or not entry[key].strip()
                       for key in ("reason", "evidence"))):
            raise ValueError(f"Exception needs status, reason and evidence: {path}")
        if any(path.startswith(other + ".") for other in exceptions):
            raise ValueError(f"Overlapping availability exceptions: {path}")
        value = profile.get("expected", {})
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                break
            value = value[part]
        else:
            raise ValueError(f"Exception must be omitted from expected: {path}")
    return exceptions


def validate_profile(profile):
    if not isinstance(profile, dict):
        raise ValueError("Baseline must be an object")
    expected = profile.get("expected")
    if not isinstance(expected, dict):
        raise ValueError("Baseline must include every required control")
    if "codeql_main_source" in expected:
        # Every codeql-action bump rewrote the pinned blob sha and left the audit drifting.
        raise ValueError("codeql_main_source is no longer checked; remove it from the baseline")
    exceptions = validate_exceptions(profile)
    codeql = expected.get("codeql")
    default_setup = isinstance(codeql, dict) and codeql.get("state") == "configured"
    required = set(REQUIRED_FIELDS) - (ADVANCED_CODEQL if default_setup or "codeql" in exceptions else set())
    required -= {name for name in exceptions if "." not in name}
    if set(expected) != required:
        names = ", ".join(sorted(set(expected) ^ required))
        raise ValueError(f"Baseline must include every required control (missing or extra: {names})")
    for control, fields in REQUIRED_FIELDS.items():
        if control not in required:
            continue
        value = expected[control]
        if control == "rulesets":
            if not isinstance(value, list) or any(
                not isinstance(item, dict) or set(item) != set(RULESET_FIELDS)
                or not isinstance(item["name"], str) or not item["name"] for item in value
            ):
                raise ValueError("Rulesets must be a list of rulesets with " + ", ".join(RULESET_FIELDS))
            if len({item["name"] for item in value}) != len(value):
                raise ValueError("Ruleset names must be unique")
            continue
        if not isinstance(value, dict):
            raise ValueError(f"Invalid control: {control}")
        for field in fields.split():
            if f"{control}.{field}" in exceptions:
                continue
            current = value
            for part in field.split("."):
                if not isinstance(current, dict) or part not in current:
                    raise ValueError(f"Missing required setting: {control}.{field}")
                current = current[part]
            leaf = field.split(".")[-1]
            kind = str if leaf in STRING_FIELDS else int if leaf == "required_approving_review_count" else list if leaf in {"checks", "patterns_allowed"} else bool
            if type(current) is not kind:
                raise ValueError(f"Invalid setting type: {control}.{field}")
            if kind is str and not current:
                raise ValueError(f"Empty setting: {control}.{field}")
        checks = value["required_status_checks"]["checks"] if control == "protection" else None
        if checks is not None and (not checks or any(
            not isinstance(check, dict) or not isinstance(check.get("context"), str)
            or not check["context"] or type(check.get("app_id")) is not int
            for check in checks
        )):
            raise ValueError("Required checks must include names and App IDs")
    if type(profile.get("repository_id")) is not int or profile["repository_id"] <= 0:
        raise ValueError("Invalid repository ID")


def validate_target(profile):
    """Schema version, repository name and branch, checked before any request path is built."""
    if type(profile.get("schema_version")) is not int or profile["schema_version"] != 1:
        raise ValueError("Unsupported settings baseline version")
    repo = profile.get("repository")
    branch = profile.get("default_branch")
    if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]+", repo) or repo.split("/")[-1] in {".", ".."}:
        raise ValueError("Invalid repository identity")
    if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", branch) or ".." in branch or branch.endswith("."):
        raise ValueError("Invalid baseline branch")


def read_rulesets(read, prefix):
    """(id, ruleset) for each repository ruleset; the summary list omits the rules, so read each one."""
    summaries = read(f"{prefix}/rulesets?includes_parents=false") or []
    return [(item["id"], {key: detail.get(key) for key in RULESET_FIELDS})
            for item in summaries for detail in [read(f"{prefix}/rulesets/{item['id']}")]]


def known_parameters(expected, actual):
    """Drop rule parameters the baseline does not list; GitHub may add new ones.

    Extra rulesets, extra rules and differing listed parameters still differ.
    """
    listed = {ruleset["name"]: {rule["type"]: set(rule.get("parameters") or {}) for rule in ruleset["rules"]
                                if isinstance(rule, dict) and "type" in rule}
              for ruleset in expected if isinstance(ruleset.get("rules"), list)}
    result = []
    for ruleset in actual:
        if not isinstance(ruleset.get("rules"), list):
            result.append(ruleset)  # a missing or odd rules value must still differ
            continue
        keys = listed.get(ruleset.get("name"), {})
        rules = [{**rule, "parameters": {k: v for k, v in rule["parameters"].items() if k in keys[rule["type"]]}}
                 if isinstance(rule, dict) and rule.get("type") in keys and isinstance(rule.get("parameters"), dict)
                 else rule
                 for rule in ruleset["rules"]]
        result.append({**ruleset, "rules": rules})
    return result


def audit(profile, read=None):
    validate_profile(profile)
    read = read_api if read is None else read
    validate_target(profile)
    repo = profile["repository"]
    branch = profile["default_branch"]
    prefix = f"repos/{repo}"
    metadata = read(prefix)
    if not isinstance(metadata, dict) or metadata["id"] != profile["repository_id"] or metadata["full_name"] != repo:
        raise ValueError("Repository identity mismatch")
    paths = {
        "protection": f"branches/{branch}/protection",
        "actions": "actions/permissions",
        "allowed_actions": "actions/permissions/selected-actions",
        "workflow_token": "actions/permissions/workflow",
        "fork_policy": "actions/permissions/fork-pr-contributor-approval",
        "immutable_releases": "immutable-releases",
        "private_vulnerability_reporting": "private-vulnerability-reporting",
        "codeql": "code-scanning/default-setup",
        "codeql_workflow": "actions/workflows/codeql.yml",
    }
    result = []
    for name, expected in profile["expected"].items():
        if name == "repository":
            actual = metadata
        elif name == "dependabot_alerts":
            # A successful GET returns 204. Permission or API errors must fail.
            read(f"{prefix}/vulnerability-alerts")
            actual = {"enabled": True}
        elif name == "rulesets":
            actual = known_parameters(expected, [ruleset for _, ruleset in read_rulesets(read, prefix)])
        else:
            if name not in paths:
                raise ValueError(f"Unsupported settings endpoint: {name}")
            actual = read(f"{prefix}/{paths[name]}")
        result.extend(differences(expected, actual, name))
    return result


def main():
    try:
        profile = merged(json.loads((ROOT / ".github/repository-settings.json").read_text()))
        drift = audit(profile)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(f"UNVERIFIED: GitHub settings lookup failed ({type(error).__name__})", file=sys.stderr)
        return 2
    print(f"BASELINE: common values from {TEMPLATE}")
    exceptions = profile.get("exceptions", {})
    for path, entry in sorted(exceptions.items()):
        print(f"{entry['status'].upper()}: {path}: {entry['reason']} ({entry['evidence']})")
    if drift:
        print("DRIFT: " + ", ".join(drift))
        return 1
    if exceptions:
        print(f"LIMITED: {profile['repository']} checked settings match; declared exceptions were not verified; no writes performed")
    else:
        print(f"PASS: {profile['repository']} settings match baseline; no writes performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
