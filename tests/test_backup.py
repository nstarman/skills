"""syw-adopt-overleaf/scripts/backup.sh: verified backup parts, refusal of synced or existing destinations.

git (for the Overleaf clone only), gh, op and pdfinfo are stubs first on PATH; nothing touches a network.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "syw-adopt-overleaf" / "scripts" / "backup.sh"
REAL_GIT = shutil.which("git")
ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}
# git: a clone of git.overleaf.com copies $FAKE_OVERLEAF; everything else is the real git.
GIT = f"""#!/bin/bash
for a in "$@"; do
  case $a in https://git@git.overleaf.com/*)
    echo "overleaf clone $a" >> "$STUB_LOG"; exec {REAL_GIT} clone -q "$FAKE_OVERLEAF" "${{@: -1}}" ;;
  esac
done
exec {REAL_GIT} "$@"
"""
# gh: `repo clone` mirrors $FAKE_GITHUB; `secret list` prints names only.
GH = f"""#!/bin/bash
echo "gh $*" >> "$STUB_LOG"
case "$1 $2" in
  "repo clone") exec {REAL_GIT} clone --mirror -q "$FAKE_GITHUB" "$4" ;;
  "secret list") printf 'SECRET_A\\tUpdated\\n'; exit 0 ;;
esac
exit 1
"""
STUBS = {
    "git": GIT,
    "gh": GH,
    "op": '#!/bin/bash\necho "op $*" >> "$STUB_LOG"\necho olp_faketoken\n',
    "pdfinfo": "#!/bin/bash\necho 'Pages:          7'\n",
}


def git(cwd, *args):
    subprocess.run([REAL_GIT, "-c", "init.defaultBranch=main", *args], cwd=cwd, env=ENV, check=True, capture_output=True)


def make_repo(path, text):
    path.mkdir()
    git(path, "init", "-q")
    (path / "ms.tex").write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", text)


class BackupTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name).resolve()
        self.stubs = self.dir / "stubs"
        self.stubs.mkdir()
        for name, body in STUBS.items():
            (self.stubs / name).write_text(body)
            (self.stubs / name).chmod(0o755)
        self.log = self.dir / "stub.log"
        self.log.touch()
        self.repo = self.dir / "old"
        make_repo(self.repo, "paper")
        self.overleaf = self.dir / "overleaf-src"
        make_repo(self.overleaf, "paper")
        self.mirror = self.dir / "mirror"
        (self.mirror / "figs").mkdir(parents=True)
        (self.mirror / "ms.tex").write_text("paper\n")
        (self.mirror / "figs" / "a.png").write_text("png")
        (self.dir / "base.pdf").write_text("%PDF")
        self.dest = self.dir / "backups"
        self.env = {
            **ENV,
            "HOME": str(self.dir / "home"),
            "PATH": f"{self.stubs}{os.pathsep}{os.environ['PATH']}",
            "STUB_LOG": str(self.log),
            "FAKE_OVERLEAF": str(self.overleaf),
            "FAKE_GITHUB": str(self.repo),  # GitHub holds the same history by default
        }

    def tearDown(self):
        self._tmp.cleanup()

    def backup(self, dest=None, **env):
        return subprocess.run(
            ["bash", str(SCRIPT), "--repo", str(self.repo), "--mirror", str(self.mirror), "--overleaf-id", "abc123",
             "--op-ref", "op://<vault>/<item>", "--baseline", str(self.dir / "base.pdf"), "--github", "owner/paper",
             "--dest", str(dest or self.dest)],
            env={**self.env, **env}, capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )

    def test_full_backup_verifies_every_part(self):
        p = self.backup()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        for part in ("repo.bundle", "github.bundle not needed", "mirror.tar.gz (2 files)", "overleaf (1 commits", "baseline.pdf (7 pages)", "secrets.txt (1 names)"):
            self.assertIn(f"ok {part}", p.stdout)
        out = next(self.dest.glob("paper-*"))
        for f in ("repo.bundle", "mirror.tar.gz", "baseline.pdf", "secrets.txt", "overleaf/.git"):
            self.assertTrue((out / f).exists(), f)
        self.assertFalse((out / "github.bundle").exists())
        self.assertFalse((out / ".github.git").exists())
        # the token never appears in output, files, or any command line (op reads it via the env ref)
        self.assertNotIn("olp_", p.stdout + p.stderr + (out / "overleaf" / ".git" / "config").read_text())
        self.assertNotIn("olp_", self.log.read_text())

    def test_separate_github_history_gets_its_own_bundle(self):
        other = self.dir / "gh-src"
        make_repo(other, "different history")
        p = self.backup(FAKE_GITHUB=str(other))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ok github.bundle (", p.stdout)
        self.assertTrue((next(self.dest.glob("paper-*")) / "github.bundle").exists())

    def test_never_overwrites_a_backup(self):
        self.assertEqual(self.backup().returncode, 0)
        p = self.backup()
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAILED destination", p.stdout)
        self.assertIn("already exists", p.stdout)

    def test_refuses_a_synced_destination(self):
        p = self.backup(dest=self.dir / "Dropbox" / "backups")
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAILED destination", p.stdout)
        self.assertFalse((self.dir / "Dropbox").exists())

    def test_reports_the_first_failing_part(self):
        (self.dir / "base.pdf").unlink()
        p = self.backup()
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAILED baseline.pdf", p.stdout)
        self.assertNotIn("secrets.txt", p.stdout)

    def test_missing_arguments_exit_2(self):
        p = subprocess.run(["bash", str(SCRIPT), "--repo", str(self.repo)], env=self.env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
