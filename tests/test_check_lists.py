"""syw-adopt-overleaf/scripts/check_lists.py: push/pull lists against the inventory."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "syw-adopt-overleaf" / "scripts" / "check_lists.py"

INVENTORY = """# class\tpath\tnote
1\tms.tex\trenamed from main.tex
1\tbib.bib\trenamed from main.bib
2\tfigures/GD1/track.pdf\tplot_gd1.py
3\taastex701.cls\t
3\tpreamble/preamble-starkman.sty\t
4\tnotes/referee.md\tprivate
"""

CLEAN = """\
overleaf:
  id: abc
  gh_actions_sync: true
  push:
    - src/tex/figures
    - src/tex/output
    - src/tex/aastex701.cls
    - src/tex/preamble/preamble-starkman.sty
  pull:
    - src/tex/ms.tex
    - src/tex/bib.bib
"""


class CheckListsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "inventory.tsv").write_text(INVENTORY, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def run_check(self, lists):
        (self.dir / "lists.yml").write_text(lists, encoding="utf-8")
        p = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.dir / "lists.yml"), str(self.dir / "inventory.tsv")],
            capture_output=True,
            text=True,
        )
        return p.returncode, p.stdout + p.stderr

    def test_clean(self):
        code, out = self.run_check(CLEAN)
        self.assertEqual(code, 0, out)

    def test_same_path_in_both(self):
        code, out = self.run_check(CLEAN + "    - src/tex/aastex701.cls\n")
        self.assertEqual(code, 1)
        self.assertIn("aastex701.cls", out)

    def test_push_folder_covers_authored_text(self):
        code, out = self.run_check(CLEAN.replace("    - src/tex/figures\n", "    - src/tex\n", 1))
        self.assertEqual(code, 1)
        self.assertIn("ms.tex", out)

    def test_push_folder_covers_pulled_file(self):
        code, out = self.run_check(CLEAN + "    - src/tex/figures/GD1/track.pdf\n")
        self.assertEqual(code, 1)
        self.assertIn("figures/GD1/track.pdf", out)

    def test_class_4_pulled(self):
        code, out = self.run_check(CLEAN + "    - src/tex/notes\n")
        self.assertEqual(code, 1)
        self.assertIn("FAIL private: notes/referee.md", out)

    def test_class_4_pushed_by_name(self):
        code, out = self.run_check(CLEAN.replace("  pull:\n", "    - src/tex/notes/referee.md\n  pull:\n"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL private: notes/referee.md", out)

    def test_class_4_under_pushed_folder_is_deleted_not_failed(self):
        code, out = self.run_check(CLEAN.replace("  pull:\n", "    - src/tex/notes\n  pull:\n"))
        self.assertEqual(code, 0, out)
        self.assertIn("deleted: notes/referee.md", out)
        self.assertIn("deletes 1 file(s)", out)

    def test_inline_list_refused(self):
        code, out = self.run_check(CLEAN.replace("  push:\n", "  push: [src/tex]\n  old_push:\n"))
        self.assertEqual(code, 2, out)

    def test_full_showyourwork_yml(self):
        yml = "cache_on_zenodo: true\ndag:\n  render: false\n" + CLEAN + "ms_name: ms\nscripts:\n  py: python {script}\n"
        code, out = self.run_check(yml)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
