"""bump_refs.py: propose newer release tags for tag-pinned registry entries."""

import contextlib
import io
import json
import unittest
from unittest import mock

from helpers import TempRepo

import bump_refs
import skillreg


def run(root, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = bump_refs.main(list(args), root=root)
    return code, out.getvalue()


TAGS = {"o/fig": {"v0.1.0", "v0.2.0", "v0.10.0"}, "o/cur": {"v1.0.0"}}
LATEST = {"o/fig": "v0.10.0", "o/cur": "v1.0.0", "o/main": "v9.9.9"}


class BumpRefsTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.external("fig", repo="o/fig", ref="v0.2.0")
        self.repo.external("cur", repo="o/cur", ref="v1.0.0")
        self.repo.external("tracker", repo="o/main", ref="main")
        self.patches = [
            mock.patch.object(bump_refs, "is_tag", side_effect=lambda repo, ref: ref in TAGS.get(repo, set())),
            mock.patch.object(bump_refs, "latest_release", side_effect=lambda repo: LATEST[repo]),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.repo.close()

    def ref(self, name):
        return json.loads((self.repo.root / "registry" / f"{name}.json").read_text(encoding="utf-8"))["source"]["ref"]

    def test_bumps_only_tag_pinned_entries_that_are_behind(self):
        code, msg = run(self.repo.root)
        self.assertEqual(code, 0)
        self.assertEqual(msg.strip(), "fig: v0.2.0 -> v0.10.0")
        self.assertEqual((self.ref("fig"), self.ref("cur"), self.ref("tracker")), ("v0.10.0", "v1.0.0", "main"))
        text = (self.repo.root / "registry" / "fig.json").read_text(encoding="utf-8")
        self.assertTrue(text.endswith("}\n") and '\n  "source"' in text)  # same formatting as before

    def test_dry_run_writes_nothing(self):
        code, msg = run(self.repo.root, "--dry-run")
        self.assertEqual((code, msg.strip()), (0, "fig: v0.2.0 -> v0.10.0"))
        self.assertEqual(self.ref("fig"), "v0.2.0")

    def test_current_prints_nothing(self):
        run(self.repo.root)
        self.assertEqual(run(self.repo.root), (0, ""))

    def test_never_moves_backwards(self):
        LATEST["o/fig"] = "v0.1.0"
        try:
            self.assertEqual(run(self.repo.root), (0, ""))
        finally:
            LATEST["o/fig"] = "v0.10.0"

    def test_api_error_is_reported_and_others_continue(self):
        def boom(repo):
            if repo == "o/cur":
                raise skillreg.SkillError("cur: cannot read the latest release of o/cur")
            return LATEST[repo]
        with mock.patch.object(bump_refs, "latest_release", side_effect=boom):
            code, msg = run(self.repo.root)
        self.assertEqual(code, 1)
        self.assertIn("cur: cannot read", msg)
        self.assertIn("fig: v0.2.0 -> v0.10.0", msg)
        self.assertEqual(self.ref("fig"), "v0.10.0")


if __name__ == "__main__":
    unittest.main()
