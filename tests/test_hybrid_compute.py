"""{engaging,submit}-hybrid-compute/scripts: run_modes, push_results, watch_jobs, engaging-connect, duo-askpass.

Every external command (ssh, timeout, sleep, osascript, uv) is a stub first on PATH that logs its argv.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("engaging-hybrid-compute", "submit-hybrid-compute")
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}
# ssh: -O check succeeds only once a login has "happened"; FAKE_SSH_FAIL makes logins fail;
# squeue counts come from the lines of $FAKE_COUNTS (popped one per call; a number, or "rc=N").
SSH = r"""#!/bin/bash
echo "ssh $*" >> "$STUB_LOG"
case "$*" in
  *"-O check"*) [ -e "$STUB_DIR/up" ]; exit $? ;;
  *squeue*)
    line=$(head -n 1 "$FAKE_COUNTS"); sed 1d "$FAKE_COUNTS" > "$FAKE_COUNTS.new"; mv "$FAKE_COUNTS.new" "$FAKE_COUNTS"
    case $line in rc=*) exit "${line#rc=}" ;; esac
    echo "$line"; [ "$line" != 0 ]; exit $? ;;
  *"cd "*) echo "== fit_a-1_0.out"; exit 0 ;;
esac
[ -z "${FAKE_SSH_FAIL-}" ] || exit 255
touch "$STUB_DIR/up"
"""
LOGGER = '#!/bin/bash\necho "$(basename "$0") $*" >> "$STUB_LOG"\n'
STUBS = {
    "ssh": SSH,
    "timeout": '#!/bin/bash\nshift\nexec "$@"\n',
    "sleep": "#!/bin/bash\nexit 0\n",
    "osascript": LOGGER,
}


class Sandbox(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name).resolve()
        self.home = self.dir / "home"
        (self.home / ".ssh").mkdir(parents=True)
        self.stubs = self.dir / "stubs"
        self.stubs.mkdir()
        self.log = self.dir / "stub.log"
        self.log.touch()
        for name, body in STUBS.items():
            self.stub(name, body)
        self.env = {
            **os.environ,
            **GIT_ENV,
            "HOME": str(self.home),
            "PATH": f"{self.stubs}{os.pathsep}{os.environ['PATH']}",
            "STUB_LOG": str(self.log),
            "STUB_DIR": str(self.dir),
            "FAKE_COUNTS": str(self.dir / "counts"),
        }
        self.env.pop("FAKE_SSH_FAIL", None)

    def tearDown(self):
        self._tmp.cleanup()

    def stub(self, name, body, where=None):
        p = (where or self.stubs) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
        p.chmod(0o755)

    def logged(self):
        return self.log.read_text().splitlines()

    def run_script(self, path, *args, **env):
        return subprocess.run(
            ["bash", str(path), *args],
            env={**self.env, **env},
            capture_output=True,
            text=True,
            cwd=self.dir,
            stdin=subprocess.DEVNULL,
        )

    def retargeted(self, skill, script, pattern, line):
        """Copy a script with the hard-coded cluster path (a line matching `pattern`) replaced."""
        out = self.dir / skill / script
        out.parent.mkdir(exist_ok=True)
        text = (ROOT / skill / "scripts" / script).read_text()
        lines = [line if l.startswith(pattern) else l for l in text.splitlines()]
        out.write_text("\n".join(lines) + "\n")
        return out


class ClusterScripts:
    """Tests shared by both cluster skills; one subclass per skill is generated below."""

    skill = ""

    def test_run_modes_picks_the_mode_of_its_array_task(self):
        skill = self.skill
        repo = self.dir / "clone"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, env=self.env, check=True)
        self.stub("uv", LOGGER, self.home / ".local" / "bin")
        script = self.retargeted(skill, "run_modes.sh", "REPO_DIR=", f"REPO_DIR={repo}")
        p = self.run_script(script, "fit.py", "modeA", "modeB", "modeC", SLURM_ARRAY_TASK_ID="1", SEED="3")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("task 1: fit.py modeB", p.stdout)
        self.assertIn("SEED=3", p.stdout.splitlines())
        self.assertIn("MODE=modeB", p.stdout.splitlines())
        self.assertEqual(self.logged(), ["uv run --frozen python fit.py modeB"])

    def test_run_modes_fails_when_the_clone_is_missing(self):
        skill = self.skill
        script = self.retargeted(skill, "run_modes.sh", "REPO_DIR=", f"REPO_DIR={self.dir}/nope")
        p = self.run_script(script, "fit.py", "modeA", SLURM_ARRAY_TASK_ID="0")
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(self.logged(), [])

    def test_push_results_commits_only_result_files(self):
        skill = self.skill
        git = lambda cwd, *a: subprocess.run(["git", "-c", "init.defaultBranch=main", *a], cwd=cwd, env=self.env, check=True, capture_output=True)
        origin, work = self.dir / "origin.git", self.dir / "clone"
        git(self.dir, "init", "-q", "--bare", str(origin))
        git(self.dir, "init", "-q", str(work))
        (work / "README").write_text("x\n")
        git(work, "add", "-A")
        git(work, "commit", "-q", "-m", "init")
        git(work, "remote", "add", "origin", str(origin))
        git(work, "push", "-q", "-u", "origin", "HEAD:main")
        (work / "01_exp").mkdir()
        (work / "01_exp" / "fig.png").write_text("png")
        (work / "01_exp" / "run.log").write_text("log")
        (work / "notes").mkdir()
        (work / "notes" / "fig.png").write_text("not an experiment folder")
        script = self.retargeted(skill, "push_results.sh", "cd ", f"cd {work}")
        p = self.run_script(script, "seeds 0-4")
        self.assertEqual(p.returncode, 0, p.stderr)
        shown = subprocess.run(["git", "--git-dir", str(origin), "show", "--name-only", "--format=%s", "main"], capture_output=True, text=True, env=self.env).stdout.split()
        self.assertIn("01_exp/fig.png", shown)
        self.assertNotIn("01_exp/run.log", shown)
        self.assertNotIn("notes/fig.png", shown)
        self.assertIn("results:", shown)
        again = self.run_script(script, "again")
        self.assertEqual((again.returncode, again.stdout.strip()), (0, "nothing to commit"))
        self.assertNotEqual(self.run_script(script).returncode, 0)  # message is required

    def test_watch_jobs_waits_for_the_queue_then_prints_logs(self):
        skill = self.skill
        (self.dir / "counts").write_text("2\n1\n0\n")
        p = self.run_script(ROOT / skill / "scripts" / "watch_jobs.sh", "^(fit_|lap_)", "cl", "~/proj", "0")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("== fit_a-1_0.out", p.stdout)
        calls = self.logged()
        self.assertEqual(len(calls), 4)  # three squeue polls, one log read
        self.assertTrue(all(c.startswith("ssh -o BatchMode=yes cl ") for c in calls))
        self.assertIn("squeue --me", calls[0])
        self.assertIn("cd ~/proj/slurm/logs", calls[3])

    def test_watch_jobs_stops_when_ssh_fails(self):
        skill = self.skill
        (self.dir / "counts").write_text("rc=255\n")
        p = self.run_script(ROOT / skill / "scripts" / "watch_jobs.sh", "fit_", "cl", "~/proj", "0")
        self.assertEqual(p.returncode, 1)
        self.assertIn("ssh failed (rc=255)", p.stdout)

    def test_watch_jobs_refuses_values_that_could_break_out(self):
        skill = self.skill
        script = ROOT / skill / "scripts" / "watch_jobs.sh"
        for args in (("a'b", "cl", "~/p", "0"), ("fit", "cl; rm -rf x", "~/p", "0"), ("fit", "cl", "~/p; x", "0"), ("fit", "cl", "~/p", "1 2")):
            p = self.run_script(script, *args)
            self.assertEqual(p.returncode, 2, args)
        self.assertEqual(self.logged(), [])  # nothing reached ssh


for _skill in SKILLS:
    _name = "".join(w.title() for w in _skill.split("-")) + "Test"
    globals()[_name] = type(_name, (ClusterScripts, Sandbox), {"skill": _skill})


class EngagingConnectTest(Sandbox):
    script = ROOT / "engaging-hybrid-compute" / "scripts" / "engaging-connect"

    def test_noop_when_connection_is_up(self):
        (self.dir / "up").touch()
        p = self.run_script(self.script)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "connection already up"))
        self.assertEqual(self.logged(), ["ssh -O check orcd-login"])

    def test_one_attempt_then_cooldown_after_failure(self):
        p = self.run_script(self.script, FAKE_SSH_FAIL="1")
        self.assertEqual(p.returncode, 1)
        self.assertTrue((self.home / ".ssh" / "engaging-connect.lastfail").exists())
        p = self.run_script(self.script, FAKE_SSH_FAIL="1")
        self.assertEqual(p.returncode, 2)  # refused within 10 minutes
        self.assertEqual(len([c for c in self.logged() if "-fN" in c]), 1)  # no second login
        p = self.run_script(self.script, "--force")  # --force tries again, and succeeds
        self.assertEqual((p.returncode, p.stdout.splitlines()[-1]), (0, "connected"))
        self.assertFalse((self.home / ".ssh" / "engaging-connect.lastfail").exists())

    def test_login_uses_the_duo_askpass_helper(self):
        self.stub("ssh", SSH.replace('echo "ssh $*"', 'echo "ssh askpass=$SSH_ASKPASS require=$SSH_ASKPASS_REQUIRE $*"'))
        self.run_script(self.script)
        login = [c for c in self.logged() if "-fN" in c]
        self.assertEqual(len(login), 1)
        self.assertIn(f"askpass={self.home}/.local/bin/duo-askpass require=force", login[0])


class DuoAskpassTest(Sandbox):
    script = ROOT / "engaging-hybrid-compute" / "scripts" / "duo-askpass"

    def test_answers_only_the_duo_menu(self):
        for prompt in ("Passcode or option (1-3): ", "Duo two-factor login for <kerb>"):
            p = self.run_script(self.script, prompt)
            self.assertEqual((p.returncode, p.stdout.strip()), (0, "push"), prompt)
        for prompt in ("<kerb>@host's password: ", "Enter passphrase for key '/x/id': ", "Are you sure you want to continue connecting (yes/no)? "):
            p = self.run_script(self.script, prompt)
            self.assertEqual((p.returncode, p.stdout), (1, ""), prompt)
        self.assertEqual(len((self.home / ".ssh" / "engaging-connect.log").read_text().splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
