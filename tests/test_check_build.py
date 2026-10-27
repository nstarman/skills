"""syw-overleaf-dropbox/scripts/check_build.sh: figures in subfolders are compared too."""

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "syw-overleaf-dropbox" / "scripts" / "check_build.sh"


class CheckBuildTest(unittest.TestCase):
    def test_recursive_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, mirror = Path(tmp) / "repo", Path(tmp) / "mirror"
            (repo / "src/tex/figures/GD1").mkdir(parents=True)
            (repo / "src/tex/ms.tex").write_text("no variables\n")
            (repo / "src/tex/figures/GD1/a.pdf").write_bytes(b"a")
            (repo / "src/tex/figures/b.pdf").write_bytes(b"b")
            (mirror / "figures").mkdir(parents=True)
            (mirror / "figures/b.pdf").write_bytes(b"b")
            out = subprocess.run(["sh", str(SCRIPT), str(mirror)], cwd=repo, capture_output=True, text=True).stdout
        self.assertIn("figure GD1/a.pdf: ABSENT", out)
        self.assertIn("figure b.pdf: same", out)

    def test_variables_in_comments_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            (repo / "src/tex/output").mkdir(parents=True)
            (repo / "src/tex/ms.tex").write_text(
                "% `\\variable{output/x.tex}` inserts a value\n"
                "Rate \\variable{output/rate.tex}\\% here. % \\variable{output/y.tex}\n"
                "Gone \\variable{output/missing.tex}.\n"
            )
            (repo / "src/tex/output/rate.tex").write_text("3")
            out = subprocess.run(["sh", str(SCRIPT), tmp], cwd=repo, capture_output=True, text=True).stdout
        self.assertIn("MISSING variable file: output/missing.tex", out)
        self.assertNotIn("output/x.tex", out)
        self.assertNotIn("output/y.tex", out)
        self.assertNotIn("output/rate.tex", out)


if __name__ == "__main__":
    unittest.main()
