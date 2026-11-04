"""syw-overleaf-dropbox/scripts/mirror_edit.py: exact-once edits, all or nothing, never src/tex."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "syw-overleaf-dropbox" / "scripts" / "mirror_edit.py"


class MirrorEditTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.tex = self.dir / "mirror" / "ms.tex"
        self.tex.parent.mkdir()
        self.tex.write_text("alpha beta\nbeta gamma\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def run_edit(self, edits, path=None):
        f = self.dir / "edits.json"
        f.write_text(json.dumps(edits), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path or self.tex), str(f)], capture_output=True, text=True
        )

    def test_applies_every_edit(self):
        p = self.run_edit([{"old": "alpha", "new": "A"}, {"old": "gamma", "new": "G"}])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.tex.read_text(encoding="utf-8"), "A beta\nbeta G\n")

    def test_ambiguous_or_missing_text_writes_nothing(self):
        for bad in ("beta", "absent"):  # twice, never
            p = self.run_edit([{"old": "alpha", "new": "A"}, {"old": bad, "new": "x"}])
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("edit 1", p.stderr)
            self.assertEqual(self.tex.read_text(encoding="utf-8"), "alpha beta\nbeta gamma\n")

    def test_refuses_src_tex(self):
        repo_copy = self.dir / "src" / "tex" / "ms.tex"
        repo_copy.parent.mkdir(parents=True)
        repo_copy.write_text("alpha\n", encoding="utf-8")
        p = self.run_edit([{"old": "alpha", "new": "A"}], path=repo_copy)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("src/tex", p.stderr)
        self.assertEqual(repo_copy.read_text(encoding="utf-8"), "alpha\n")


if __name__ == "__main__":
    unittest.main()
