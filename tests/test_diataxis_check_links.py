"""diataxis/scripts/check_links.py: relative links, roles, anchors, formats, exit codes."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "diataxis" / "scripts" / "check_links.py"


class CheckLinksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        p = self.docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.docs), *args],
                              capture_output=True, text=True)

    def test_clean_tree_exits_zero(self):
        self.write("index.md", "# Home\n\n[cli](ref/cli.md#run-flags) [up](#home)\n"
                               "[web](https://example.com/x.md)\n{doc}`/ref/cli`\n")
        self.write("ref/cli.md", "# CLI\n\n## Run flags\n\n[home](../index.md)\n")
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("OK", r.stdout)
        self.assertEqual(self.run_script("--quiet").stdout, "")

    def test_broken_page_and_anchor_exit_one(self):
        self.write("index.md", "# Home\n\n[gone](missing.md)\n[bad](other.md#nope)\n"
                               "[self](#nope-either)\n")
        self.write("other.md", "# Other\n")
        r = self.run_script("--format", "json")
        self.assertEqual(r.returncode, 1)
        probs = json.loads(r.stdout)["problems"]
        self.assertEqual([(p["target"], p["kind"]) for p in probs],
                         [("missing.md", "link"), ("other.md#nope", "fragment"),
                          ("#nope-either", "fragment")])

    def test_roles_and_explicit_anchors(self):
        self.write("a.md", "(my-label)=\n# A\n\nSee {ref}`my-label` and {ref}`undefined-label`"
                           " and {doc}`b` and {doc}`nothing`.\n\n[x](b.md#custom-id)\n")
        self.write("b.md", "# B\n\n## Thing {#custom-id}\n")
        r = self.run_script("--format", "json")
        self.assertEqual(r.returncode, 1)
        targets = {p["target"] for p in json.loads(r.stdout)["problems"]}
        self.assertEqual(targets, {"undefined-label", "nothing"})

    def test_duplicate_headings_get_numbered_slugs_and_code_is_ignored(self):
        self.write("a.md", "# A\n\n## Setup\n\n## Setup\n\n[2](#setup-1)\n\n"
                           "```\n[ignored](nowhere.md)\n```\n")
        self.assertEqual(self.run_script().returncode, 0)

    def test_text_report_and_bad_root(self):
        self.write("a.md", "# A\n\n[x](gone.md)\n")
        r = self.run_script()
        self.assertEqual(r.returncode, 1)
        self.assertIn("1 unresolved link(s)", r.stdout)
        self.assertIn("gone.md", r.stdout)
        bad = subprocess.run([sys.executable, str(SCRIPT), str(self.docs / "nope")],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
