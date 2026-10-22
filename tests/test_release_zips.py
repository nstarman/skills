"""release_zips.py: deterministic per-skill zips, hashes.json, and the release decision."""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from helpers import TempRepo, skill_md

import release_zips
import skillreg


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = release_zips.main(list(args), root=root)
    return code, out.getvalue()


class ReleaseZipsTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.local("alpha", files=("references/a.md", "scripts/run.py"))
        self.repo.external("beta", repo="o/beta", path="skills/beta", ref="v1.0.0")
        self.tmp = Path(tempfile.mkdtemp())

        def fake_fetch(skill, dest):  # stands in for the sparse git clone
            dest.mkdir(parents=True)
            (dest / "SKILL.md").write_text(skill_md(skill.name), encoding="utf-8")
            (dest / "card.json").write_text("{}", encoding="utf-8")  # an upstream card is dropped too
        self.patch = mock.patch.object(release_zips, "fetch_external", side_effect=fake_fetch)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.repo.close()
        shutil.rmtree(self.tmp)

    def test_zip_layout(self):
        code, msg = run(self.repo.root, str(self.tmp / "a"))
        self.assertEqual(code, 0, msg)
        with zipfile.ZipFile(self.tmp / "a" / "alpha.zip") as z:
            names = z.namelist()
        self.assertEqual(sorted(names), ["alpha/SKILL.md", "alpha/references/a.md", "alpha/scripts/run.py"])
        with zipfile.ZipFile(self.tmp / "a" / "beta.zip") as z:
            self.assertEqual(z.namelist(), ["beta/SKILL.md"])
        hashes = json.loads((self.tmp / "a" / "hashes.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(hashes), ["alpha", "beta"])
        self.assertTrue(all(len(h) == 64 for h in hashes.values()))

    def test_deterministic(self):
        run(self.repo.root, str(self.tmp / "a"))
        (self.repo.root / "alpha" / "SKILL.md").touch()  # a newer mtime must not change the bytes
        run(self.repo.root, str(self.tmp / "b"))
        for n in ("alpha.zip", "beta.zip", "hashes.json"):
            self.assertEqual((self.tmp / "a" / n).read_bytes(), (self.tmp / "b" / n).read_bytes(), n)

    def test_release_decision(self):
        run(self.repo.root, str(self.tmp / "a"))
        prev = str(self.tmp / "a" / "hashes.json")
        code, msg = run(self.repo.root, str(self.tmp / "b"), "--previous", prev)
        self.assertEqual((code, msg.strip().splitlines()[-1]), (0, "unchanged"))

        (self.repo.root / "alpha" / "references" / "a.md").write_text("new\n", encoding="utf-8")
        code, msg = run(self.repo.root, str(self.tmp / "c"), "--previous", prev)
        lines = msg.strip().splitlines()
        self.assertEqual(lines[-1], "changed")
        self.assertIn("alpha", lines[-2])

        self.repo.local("gamma")  # an added skill is a change
        code, msg = run(self.repo.root, str(self.tmp / "d"), "--previous", prev)
        self.assertEqual(msg.strip().splitlines()[-1], "changed")

    def test_missing_previous_is_a_change(self):
        code, msg = run(self.repo.root, str(self.tmp / "a"), "--previous", str(self.tmp / "nope.json"))
        self.assertEqual(msg.strip().splitlines()[-1], "changed")

    def test_failed_fetch_fails_the_run(self):
        self.patch.stop()
        with mock.patch.object(release_zips, "fetch_external",
                               side_effect=skillreg.SkillError("beta: cannot fetch o/beta@v1.0.0")):
            code, msg = run(self.repo.root, str(self.tmp / "a"))
        self.patch.start()
        self.assertEqual(code, 1)
        self.assertIn("beta: cannot fetch", msg)
        self.assertFalse((self.tmp / "a" / "hashes.json").exists())  # no partial set


if __name__ == "__main__":
    unittest.main()
