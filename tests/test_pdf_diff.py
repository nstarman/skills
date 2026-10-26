"""syw-adopt-overleaf/scripts/pdf_diff.py: pages, numbers, text and image differences."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pdfgen import write_pdf

SCRIPT = Path(__file__).resolve().parents[1] / "syw-adopt-overleaf" / "scripts" / "pdf_diff.py"
PAGE = ["The fraction is 0.43 of 1,200 streams.", "Nothing else changes."]


def run(*args):
    p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


@unittest.skipUnless(shutil.which("pdftotext") and shutil.which("pdftoppm"), "poppler not installed")
class PdfDiffTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.base = self.dir / "base.pdf"
        write_pdf(self.base, [(PAGE, (100, 100, 200, 200))])

    def tearDown(self):
        self._tmp.cleanup()

    def new(self, pages):
        path = self.dir / "new.pdf"
        write_pdf(path, pages)
        return path

    def test_identical(self):
        code, out = run(self.base, self.new([(PAGE, (100, 100, 200, 200))]))
        self.assertEqual(code, 0, out)

    def test_changed_number(self):
        page = [PAGE[0].replace("0.43", "0.44"), PAGE[1]]
        code, out = run(self.base, self.new([(page, (100, 100, 200, 200))]))
        self.assertEqual(code, 1)
        self.assertIn("p1: 0.43 → 0.44", out)

    def test_extra_page(self):
        code, out = run(self.base, self.new([(PAGE, (100, 100, 200, 200)), ["Appendix"]]))
        self.assertEqual(code, 1)
        self.assertIn("1 → 2", out)

    def test_changed_figure(self):
        out_dir = self.dir / "out"
        code, out = run(self.base, self.new([(PAGE, (300, 100, 200, 200))]), "--out", out_dir)
        self.assertEqual(code, 1)
        self.assertIn("p1", out.split("images")[1])
        self.assertTrue((out_dir / "p1-baseline.png").exists())
        self.assertTrue((out_dir / "p1-new.png").exists())


if __name__ == "__main__":
    unittest.main()
