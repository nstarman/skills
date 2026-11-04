"""diataxis/scripts/check_repo_refs.py: stale doc-path references outside the docs tree."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "diataxis" / "scripts" / "check_repo_refs.py"

MAP = """| Old | New |
|---|---|
| `docs/usage.md` | `docs/how-to/use.md` |
"""


class CheckRepoRefsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        self.write("docs/how-to/use.md", "# Use\n")
        self.write("docs/keep.md", "# Keep\n")
        self.map = Path(self._tmp.name) / "map.md"   # outside the repo, like a staged audit
        self.map.write_text(MAP, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.repo), *args],
                              capture_output=True, text=True)

    def with_map(self, *extra):
        return self.run_script("--map", str(self.map),
                               "--new-docs", str(self.repo / "docs"), *extra)

    def test_stale_reference_is_reported(self):
        self.write("README.md", "See [usage](docs/usage.md) and docs/keep.md.\n")
        self.write("noxfile.py", "session.run('sphinx-build', 'docs/usage.md')\n")
        r = self.with_map()
        self.assertEqual(r.returncode, 1)
        self.assertIn("README.md", r.stdout)
        self.assertIn("noxfile.py", r.stdout)
        self.assertIn("docs/usage.md", r.stdout)
        self.assertNotIn("keep.md  —", r.stdout)

    def test_clean_repo_passes_and_skips_docs_and_maps(self):
        self.write("README.md", "See docs/how-to/use.md.\n")
        self.write("docs/stale.md", "Old link: docs/usage.md\n")   # inside docs: not our job
        self.write("redirects.txt", "docs/usage.md docs/how-to/use.md\n")
        r = self.with_map()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("OK", r.stdout)

    def test_old_docs_tree_defines_removed_paths(self):
        old = Path(self._tmp.name) / "old-docs"
        (old).mkdir()
        (old / "keep.md").write_text("# Keep\n", encoding="utf-8")
        (old / "usage.md").write_text("# Usage\n", encoding="utf-8")
        self.write("README.md", "See docs/usage.md\n")
        r = self.run_script("--old-docs", str(old), "--new-docs", str(self.repo / "docs"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("docs/usage.md", r.stdout)

    def test_usage_errors_exit_two(self):
        # no way to tell what moved
        r = self.run_script("--new-docs", str(self.repo / "docs"))
        self.assertEqual(r.returncode, 2)
        # new-docs is not a directory
        r = self.run_script("--map", str(self.map),
                            "--new-docs", str(self.repo / "nope"))
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
