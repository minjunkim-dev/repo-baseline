#!/usr/bin/env python3

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_preflight import changed_paths, classify


class ClassifyTest(unittest.TestCase):
    def test_env_in_any_folder_or_file_name_is_a_hit(self):
        hits, examples = classify([
            ".env", "app/.env.local", ".envrc", "sub/.env", ".env.d/settings.txt",
            ".env.example", "web/.env.example", ".env.d/.env.example", "src/env.py", "README.md",
        ])
        self.assertEqual(hits, [".env", ".env.d/.env.example", ".env.d/settings.txt", ".envrc",
                                "app/.env.local", "sub/.env"])
        self.assertEqual(examples, [".env.example", "web/.env.example"])


class ChangedPathsTest(unittest.TestCase):
    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       check=True, capture_output=True)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        Path("README.md").write_text("x\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("checkout", "-qb", "pr")

    def test_env_added_then_renamed_inside_the_pr_is_still_found(self):
        Path("sub").mkdir()
        Path("sub/.env").write_text("SECRET=1\n")
        self.git("add", ".")
        self.git("commit", "-qm", "add")
        self.git("mv", "sub/.env", "sub/config.txt")
        self.git("commit", "-qm", "rename")
        paths = changed_paths("main", "pr")
        self.assertIn("sub/.env", paths)
        self.assertEqual(classify(paths)[0], ["sub/.env"])

    def test_names_with_spaces_and_non_ascii_are_not_quoted(self):
        Path("한글 파일.txt").write_text("x\n")
        self.git("add", ".")
        self.git("commit", "-qm", "add")
        self.assertEqual(changed_paths("main", "pr"), {"한글 파일.txt"})


if __name__ == "__main__":
    unittest.main()
