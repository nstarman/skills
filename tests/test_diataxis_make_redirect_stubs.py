"""diataxis/scripts/make_redirect_stubs.py: map parsing and the stub/netlify/nginx/etc. emitters."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "diataxis" / "scripts" / "make_redirect_stubs.py"

MAP = """# Migration map

| Page | Old URL | New URL | Action |
|---|---|---|---|
| usage | `/usage/` | `/how-to/use/` | MOVE |
| usage | `/usage/#pipeline` | `/reference/api/#pipeline` | SPLIT |
| same | `/same/` | `/same/` | KEEP |
| gone | `/gone/` | — | DELETE |
"""


class MakeRedirectStubsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.map = self.dir / "map.md"
        self.map.write_text(MAP, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, *args, map_path=None):
        return subprocess.run([sys.executable, str(SCRIPT), "--map", str(map_path or self.map),
                               *args], capture_output=True, text=True)

    def test_stubs_dirhtml_merge_anchors_per_old_page(self):
        out = self.dir / "out"
        r = self.run_script("--emit", "stubs", "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.html"))
        self.assertEqual(files, ["usage/index.html"])      # identity and em-dash rows skipped
        html = (out / "usage" / "index.html").read_text(encoding="utf-8")
        self.assertIn('var DEFAULT = "/how-to/use/";', html)
        self.assertIn('"pipeline": "/reference/api/#pipeline"', html)

    def test_stubs_flat_style(self):
        out = self.dir / "out"
        self.run_script("--emit", "stubs", "--out", str(out), "--url-style", "flat")
        self.assertTrue((out / "usage.html").is_file())

    def test_host_emitters_drop_anchored_rows_with_warning(self):
        r = self.run_script("--emit", "netlify")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "/usage/  /how-to/use/  301!\n")
        self.assertIn("anchored", r.stderr)
        r = self.run_script("--emit", "nginx")
        self.assertEqual(r.stdout, "location = /usage { return 301 /how-to/use/; }\n")

    def test_rediraffe_and_reredirects_keep_all_pairs(self):
        r = self.run_script("--emit", "rediraffe")
        self.assertIn('"/usage/#pipeline" "/reference/api/#pipeline"', r.stdout)
        out = self.dir / "r.py"
        self.run_script("--emit", "reredirects", "--out", str(out))
        ns = {}
        exec(out.read_text(encoding="utf-8"), ns)
        self.assertEqual(ns["redirects"]["/usage/"], "/how-to/use/")
        self.assertEqual(len(ns["redirects"]), 2)

    def test_plain_two_column_file(self):
        plain = self.dir / "r.txt"
        plain.write_text("# comment\n/old/ /new/\n", encoding="utf-8")
        r = self.run_script("--emit", "netlify", map_path=plain)
        self.assertEqual(r.stdout, "/old/  /new/  301!\n")

    def test_missing_map_and_empty_map_errors(self):
        self.assertEqual(self.run_script(map_path=self.dir / "nope.md").returncode, 2)
        empty = self.dir / "empty.md"
        empty.write_text("# only a comment\n", encoding="utf-8")
        self.assertEqual(self.run_script(map_path=empty).returncode, 1)


if __name__ == "__main__":
    unittest.main()
