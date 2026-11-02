"""personal_check.py: personal strings in a local skill fail the check."""

import contextlib
import io
import unittest

from helpers import TempRepo

import personal_check


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = personal_check.main(list(args), root=root)
    return code, out.getvalue()


class PersonalCheckTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.addCleanup(self.repo.close)
        d = self.repo.local("ok", files=("references/a.md",))
        (d / "references" / "a.md").write_text("Backups go to ~/Documents Mine/backups.\n", encoding="utf-8")
        self.patterns = self.repo.root.parent / f"{self.repo.root.name}-patterns.txt"
        self.addCleanup(self.patterns.unlink, missing_ok=True)

    def test_match_fails_with_location(self):
        self.patterns.write_text("# mine\n\ndocuments mine\n", encoding="utf-8")
        code, out = run(self.repo.root, "--patterns", str(self.patterns))
        self.assertEqual(code, 1)
        self.assertIn("ok/references/a.md:1:", out)

    def test_no_match_passes(self):
        self.patterns.write_text("someone-else\n", encoding="utf-8")
        self.assertEqual(run(self.repo.root, "--patterns", str(self.patterns))[0], 0)

    def test_missing_patterns_file_skips(self):
        code, out = run(self.repo.root, "--patterns", str(self.patterns))
        self.assertEqual(code, 0)
        self.assertIn("skipped", out)


if __name__ == "__main__":
    unittest.main()
