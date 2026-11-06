"""diataxis/scripts/docs_inventory.py: formats, orphans, duplicate titles, flags, exit codes."""

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "diataxis" / "scripts" / "docs_inventory.py"

TUTORIAL = """# Getting started

In this tutorial we will build your first app. Let's begin. First, install it.
Next, run it. You should see a greeting. Congratulations, you built it.
"""

REFERENCE = """# CLI reference

| Option | Type | Description |
|---|---|---|
| `--verbose` | bool | Print more output while the command runs |

Default: off. Returns: nothing. Raises: nothing.
"""


class DocsInventoryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.docs = self.dir / "docs"
        self.docs.mkdir()
        (self.docs / "start.md").write_text(TUTORIAL, encoding="utf-8")
        (self.docs / "cli.md").write_text(REFERENCE + "\n[start](start.md)\n", encoding="utf-8")
        sub = self.docs / "more"
        sub.mkdir()
        (sub / "cli.md").write_text(REFERENCE, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_json_scores_modes_and_counts_inlinks(self):
        r = self.run_script(str(self.docs), "--format", "json")
        self.assertEqual(r.returncode, 0, r.stderr)
        pages = {p["path"]: p for p in json.loads(r.stdout)}
        self.assertEqual(set(pages), {"start.md", "cli.md", "more/cli.md"})
        self.assertEqual(pages["start.md"]["guess"], "tutorial")
        self.assertEqual(pages["cli.md"]["guess"], "reference")
        self.assertEqual(pages["start.md"]["linked_from"], 1)
        self.assertEqual(pages["cli.md"]["linked_from"], 0)

    def test_csv_has_header_and_one_row_per_page(self):
        r = self.run_script(str(self.docs), "--format", "csv")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = list(csv.DictReader(io.StringIO(r.stdout)))
        self.assertEqual(len(rows), 3)
        self.assertIn("score_tutorial", rows[0])

    def test_markdown_report_flags_orphans_and_duplicates(self):
        r = self.run_script(str(self.docs))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("## Pages nothing links to", r.stdout)
        self.assertIn("`more/cli.md`", r.stdout)
        self.assertIn("## Duplicate titles", r.stdout)
        self.assertIn("## Facts asserted on more than one page", r.stdout)

    def test_min_words_drops_short_pages_and_out_writes_file(self):
        (self.docs / "tiny.md").write_text("# Tiny\n\nhi\n", encoding="utf-8")
        out = self.dir / "sub" / "report.json"
        r = self.run_script(str(self.docs), "--format", "json", "--min-words", "5",
                            "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")
        paths = {p["path"] for p in json.loads(out.read_text(encoding="utf-8"))}
        self.assertNotIn("tiny.md", paths)
        self.assertIn("start.md", paths)

    def test_start_pages_are_orientation_not_scored_as_modes(self):
        start = self.docs / "start"
        start.mkdir()
        (start / "quickstart.md").write_text(TUTORIAL, encoding="utf-8")
        r = self.run_script(str(self.docs), "--format", "json")
        self.assertEqual(r.returncode, 0, r.stderr)
        pages = {p["path"]: p for p in json.loads(r.stdout)}
        self.assertTrue(pages["start/quickstart.md"]["orientation"])
        self.assertFalse(pages["start.md"]["orientation"])
        md = self.run_script(str(self.docs)).stdout
        self.assertIn("| orientation | 1 |", md)
        self.assertIn("_n/a — orientation_", md)

    def test_orientation_quickstart_does_not_mask_a_missing_tutorial(self):
        for page in self.docs.glob("*.md"):
            page.unlink()
        (self.docs / "cli.md").write_text(REFERENCE, encoding="utf-8")
        start = self.docs / "start"
        start.mkdir()
        (start / "quickstart.md").write_text(TUTORIAL, encoding="utf-8")
        md = self.run_script(str(self.docs)).stdout
        self.assertIn("No page scores as a tutorial", md)

    def test_exit_codes_for_bad_root_and_empty_tree(self):
        self.assertEqual(self.run_script(str(self.dir / "missing")).returncode, 2)
        empty = self.dir / "empty"
        empty.mkdir()
        self.assertEqual(self.run_script(str(empty)).returncode, 1)


if __name__ == "__main__":
    unittest.main()
