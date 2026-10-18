#!/usr/bin/env python3
"""Copy shared files from this repository into a project and record their hashes.

Usage: tools/apply_baseline.py <project> [--check]

The project's .github/repo-baseline.json lists each copied file as
{"<path in project>": {"source": "<path here>"}}. Applying copies every source,
then records source_commit and sha256. --check only reports files that differ.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
MANIFEST = ".github/repo-baseline.json"


def git(*args):
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True, text=True).stdout.strip()


def load(project):
    manifest = json.loads((project / MANIFEST).read_text(encoding="utf-8"))
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or not files:
        raise ValueError(f"{MANIFEST} must list files to copy")
    for name, entry in files.items():
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, str) or not (HERE / source).is_file():
            raise ValueError(f"Unknown source for {name!r}: {source!r}")
        if project.resolve() not in (project / name).resolve().parents:
            raise ValueError(f"Target escapes the project: {name!r}")
    return manifest


def apply(project, check=False):
    project = project.resolve()
    manifest = load(project)
    differ = sorted(name for name, entry in manifest["files"].items()
                    if not (project / name).is_file()
                    or (project / name).read_bytes() != (HERE / entry["source"]).read_bytes())
    if check:
        return differ
    if git("status", "--porcelain"):
        raise ValueError("Commit repo-baseline changes first; source_commit must name the copied content")
    for name, entry in manifest["files"].items():
        data = (HERE / entry["source"]).read_bytes()
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_bytes(data)
        entry["sha256"] = hashlib.sha256(data).hexdigest()
    manifest["source"] = "minjunkim-dev/repo-baseline"
    manifest["source_commit"] = git("rev-parse", "HEAD")
    (project / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return differ


def main(argv):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--check"):
        print(__doc__, file=sys.stderr)
        return 2
    check = len(argv) == 3
    try:
        differ = apply(Path(argv[1]), check)
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
