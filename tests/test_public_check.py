"""syw-adopt-overleaf/scripts/public_check.sh: shared commits, token-like strings, class-4 files."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "syw-adopt-overleaf" / "scripts" / "public_check.sh"
ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}
FAKE_TOKEN = "olp_" + "x" * 30


def git(cwd, *args):
    subprocess.run(["git", "-c", "init.defaultBranch=main", *args], cwd=cwd, env=ENV, check=True, capture_output=True)


def commit(repo, path, text):
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"add {path}")


class PublicCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        old = self.dir / "old"
        old.mkdir()
        git(old, "init", "-q")
        commit(old, "ms.tex", "old paper\n")
        self.bundle = self.dir / "repo.bundle"
        git(old, "bundle", "create", "-q", str(self.bundle), "--all")
        self.inventory = self.dir / "inventory.tsv"
        self.inventory.write_text("1\tms.tex\t\n4\tnotes/referee.md\tprivate\n4\tuv.lock\tmoves to the repo root\n")
        self.new = self.dir / "new"
        self.new.mkdir()
        git(self.new, "init", "-q")
        commit(self.new, "src/tex/ms.tex", "old paper\n")  # same content as old: not a leak
        commit(self.new, "uv.lock", "lock\n")  # class 4 in Overleaf, but not private

    def tearDown(self):
        self._tmp.cleanup()

    def check(self, repo):
        p = subprocess.run(
            ["bash", str(SCRIPT), str(repo), str(self.bundle), str(self.inventory)],
            env=ENV,
            capture_output=True,
            text=True,
        )
        return p.returncode, p.stdout + p.stderr

    def test_clean(self):
        code, out = self.check(self.new)
        self.assertEqual(code, 0, out)

    def test_shared_commits(self):
        clone = self.dir / "clone"
        git(self.dir, "clone", "-q", str(self.bundle), str(clone))
        code, out = self.check(clone)
        self.assertEqual(code, 1)
        self.assertIn("FAIL shared commits", out)

    def test_token_in_history(self):
        commit(self.new, "config.txt", f"token={FAKE_TOKEN}\n")
        commit(self.new, "config.txt", "token removed\n")
        code, out = self.check(self.new)
        self.assertEqual(code, 1)
        self.assertIn("config.txt", out)
        self.assertNotIn(FAKE_TOKEN, out)

    def test_class_4_in_history(self):
        commit(self.new, "src/tex/notes/referee.md", "reply\n")
        git(self.new, "rm", "-q", "src/tex/notes/referee.md")
        git(self.new, "commit", "-q", "-m", "remove")
        code, out = self.check(self.new)
        self.assertEqual(code, 1)
        self.assertIn("notes/referee.md", out)


if __name__ == "__main__":
    unittest.main()
