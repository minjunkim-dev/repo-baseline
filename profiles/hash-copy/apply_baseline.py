#!/usr/bin/env python3
"""Copy shared files from this repository into a project and record their hashes.

Usage: profiles/hash-copy/apply_baseline.py <project> [--check | --force]

The project's .github/repo-baseline.json lists each copied file as
{"<path in project>": {"source": "<path here>"}}. Applying copies every source,
then records source_commit and sha256. --check only reports files that differ.

Applying stops before writing anything when it would overwrite content the
manifest did not record: a target that differs from its recorded sha256 (a
deleted target counts), or an existing target with no recorded sha256. A target
that already equals the new content never stops. --force overwrites anyway.

An entry with "ecosystems" is generated instead of copied: the source (the
github-actions Dependabot config) gets one profiles/hash-copy/dependabot-ecosystem.yml
block per {"package-ecosystem": ..., "directory": ...} item.

"blocks" lists marked blocks inside a project file, {"<kind>": {"target": "AGENTS.md",
"exclude": {"<tool>": "<reason>"}}}. Only the text between the kind's marker lines is
written; the rest of the file stays as the project has it. The only kind is "ops", made by
tools/check_ops.py ops_block(). A block without markers stops unless --force, which
replaces an unmarked "### ops" section or adds the block at the end of 「작업 방식」.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
from string import Template
import subprocess
import sys

HERE = Path(__file__).resolve().parents[2]
MANIFEST = ".github/repo-baseline.json"
ECOSYSTEM_TEMPLATE = "profiles/hash-copy/dependabot-ecosystem.yml"


def ops_module():
    spec = importlib.util.spec_from_file_location("check_ops", HERE / "tools/check_ops.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OPS = ops_module()


def git(*args):
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True, text=True).stdout.strip()


def inside(base, path):
    """A real (non-symlink) path that resolves under base."""
    return not path.is_symlink() and base in path.resolve().parents


def load(project):
    if not inside(project, project / MANIFEST):
        raise ValueError(f"{MANIFEST} must be a regular file inside the project")
    manifest = json.loads((project / MANIFEST).read_text(encoding="utf-8"))
    files = manifest.setdefault("files", {}) if isinstance(manifest, dict) else None
    blocks = manifest.setdefault("blocks", {}) if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or not isinstance(blocks, dict) or not (files or blocks):
        raise ValueError(f"{MANIFEST} must list files to copy or blocks to write")
    for kind, entry in blocks.items():
        exclude = entry.get("exclude", {}) if isinstance(entry, dict) else None
        if kind != "ops" or not isinstance(entry.get("target"), str) or not isinstance(exclude, dict) or any(
                not isinstance(k, str) or not isinstance(v, str) or not v.strip() or "\n" in v
                for k, v in exclude.items()):
            raise ValueError(f"Invalid block {kind!r}")
        target_ok(project, entry["target"])
        if not (project / entry["target"]).is_file():
            raise ValueError(f"Block target is missing: {entry['target']!r}")
        block_text(entry)  # unknown excluded tools stop here
    for name, entry in files.items():
        source = entry.get("source") if isinstance(entry, dict) else None
        sources = [source, ECOSYSTEM_TEMPLATE] if isinstance(entry, dict) and "ecosystems" in entry else [source]
        for path in sources:
            if not isinstance(path, str) or not inside(HERE, HERE / path) or not (HERE / path).is_file():
                raise ValueError(f"Unknown source for {name!r}: {path!r}")
            try:
                git("--literal-pathspecs", "ls-files", "--error-unmatch", "--", path)
            except subprocess.CalledProcessError:
                raise ValueError(f"Source is not tracked in repo-baseline: {path!r}") from None
        target_ok(project, name)
        if "ecosystems" in entry:
            ecosystems = entry["ecosystems"]
            if not isinstance(ecosystems, list) or any(
                    not isinstance(item, dict) or set(item) != {"package-ecosystem", "directory"}
                    or not re.fullmatch(r"[a-z][a-z0-9-]*", str(item["package-ecosystem"]))
                    or item["package-ecosystem"] == "github-actions"
                    or not re.fullmatch(r"/[A-Za-z0-9._/-]*", str(item["directory"]))
                    for item in ecosystems) or len({json.dumps(i, sort_keys=True) for i in ecosystems}) != len(ecosystems):
                raise ValueError(f"Invalid ecosystems for {name!r}")
    return manifest


def target_ok(project, name):
    if not inside(project, project / name):
        raise ValueError(f"Target escapes the project: {name!r}")
    resolved = (project / name).resolve().relative_to(project.resolve())
    if any(part.lower() == ".git" for part in Path(name).parts + resolved.parts):
        # An overwritten hook keeps its exec bit, so a copy there would run.
        # The resolved parts catch a symlinked folder that points into .git.
        raise ValueError(f"Target is inside .git: {name!r}")


def block_text(entry):
    return OPS.ops_block((HERE / "profiles/ops/README.md").read_text(encoding="utf-8"), entry.get("exclude", {}))


def with_block(text, entry, force):
    """The target text with the block written, or None when it has no markers and force is off."""
    new = block_text(entry)
    span = OPS.find_block(text)
    if span:
        return text[:span[0]] + new + text[span[1]:]
    if not force:
        return None
    if OPS.BEGIN in text or OPS.END in text:
        # A broken marker pair would survive the rewrite and leave two markers.
        raise ValueError("ops markers are not exactly one pair; fix them by hand first")
    section = re.search(r"^### ops[ \t]*\n.*?(?=^#{1,3} |\Z)", text, re.M | re.S)
    if section:
        tail = "\n" if section.end() < len(text) else ""
        return text[:section.start()] + new + tail + text[section.end():]
    work = text.find("\n## 작업 방식\n")
    end = text.find("\n## ", work + 1) if work >= 0 else -1
    if end < 0:
        return text.rstrip("\n") + "\n\n" + new
    return text[:end].rstrip("\n") + "\n\n" + new + text[end:]


def current_block(project, entry):
    path = project / entry["target"]
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    span = OPS.find_block(text)
    return text[span[0]:span[1]] if span else None


def content(entry):
    data = (HERE / entry["source"]).read_bytes()
    block = Template((HERE / ECOSYSTEM_TEMPLATE).read_text(encoding="utf-8"))
    for item in entry.get("ecosystems", []):
        data += block.substitute(ecosystem=item["package-ecosystem"], directory=item["directory"]).encode()
    return data


def local_edits(project, manifest):
    """Targets whose overwrite would lose content the manifest did not record, with the reason."""
    edits = []
    for name, entry in sorted(manifest["files"].items()):
        path, recorded = project / name, entry.get("sha256")
        exists = path.is_file()
        if exists and path.read_bytes() == content(entry):
            continue
        if recorded is None:
            if exists:
                edits.append(f"{name} (exists, no recorded sha256)")
        elif not exists:
            edits.append(f"{name} (deleted)")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != recorded:
            edits.append(f"{name} (differs from recorded sha256)")
    for kind, entry in sorted(manifest["blocks"].items()):
        block, recorded = current_block(project, entry), entry.get("sha256")
        label = f"{entry['target']} block {kind}"
        if block == block_text(entry):
            continue
        if block is None:
            edits.append(f"{label} (no markers)")
        elif recorded is None:
            edits.append(f"{label} (exists, no recorded sha256)")
        elif hashlib.sha256(block.encode()).hexdigest() != recorded:
            edits.append(f"{label} (differs from recorded sha256)")
    return edits


def apply(project, check=False, force=False):
    project = project.resolve()
    manifest = load(project)
    differ = sorted(name for name, entry in manifest["files"].items()
                    if not (project / name).is_file() or (project / name).read_bytes() != content(entry))
    differ += sorted(f"{entry['target']}#{kind}" for kind, entry in manifest["blocks"].items()
                     if current_block(project, entry) != block_text(entry))
    if check:
        return differ
    if git("status", "--porcelain"):
        raise ValueError("Commit repo-baseline changes first; source_commit must name the copied content")
    edits = [] if force else local_edits(project, manifest)
    if edits:
        raise ValueError("Project changed these files; nothing was written. Reflect the change in repo-baseline"
                         " and apply again, or apply with --force to discard it: " + ", ".join(edits))
    for name, entry in manifest["files"].items():
        data = content(entry)
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_bytes(data)
        entry["sha256"] = hashlib.sha256(data).hexdigest()
    for kind, entry in manifest["blocks"].items():
        path = project / entry["target"]
        if not path.is_file():
            raise ValueError(f"Block target is missing: {entry['target']!r}")
        text = with_block(path.read_text(encoding="utf-8"), entry, force=True)
        path.write_text(text, encoding="utf-8")
        entry["sha256"] = hashlib.sha256(block_text(entry).encode()).hexdigest()
    manifest["source"] = "minjunkim-labs/repo-baseline"
    manifest["source_commit"] = git("rev-parse", "HEAD")
    (project / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return differ


def main(argv):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] not in ("--check", "--force")):
        print(__doc__, file=sys.stderr)
        return 2
    check = argv[2:] == ["--check"]
    try:
        differ = apply(Path(argv[1]), check, force=argv[2:] == ["--force"])
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    if check:
        print("DIFFERS: " + ", ".join(differ) if differ else "SAME: project copies match repo-baseline")
        return 1 if differ else 0
    print("Updated: " + (", ".join(differ) if differ else "none (hashes refreshed)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
