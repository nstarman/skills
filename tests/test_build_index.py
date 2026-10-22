"""build_index.py: generating index.json, the marketplace and the README; --check; --remote."""

import contextlib
import io
import json
import unittest
from unittest import mock

from helpers import TempRepo, skill_md

import build_index
import skillreg


def run(root, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = build_index.main(list(args), root=root)
    return code, out.getvalue() + err.getvalue()


class BuildIndexTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.local("zeta", description="Zeta does z.")
        self.repo.local("alpha", description="Alpha does a.")
        self.repo.external("mid", repo="Org/mid", path="skills/mid", ref="v1.2.0", description="Mid does m.")
        self.repo.external("beta", repo="o/beta", path="beta", ref="main", description="Beta does b.")
        self.root = self.repo.root

    def tearDown(self):
        self.repo.close()

    def index(self):
        return json.loads((self.root / "index.json").read_text(encoding="utf-8"))

    def test_index_json(self):
        code, msg = run(self.root)
        self.assertEqual(code, 0, msg)
        doc = self.index()
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["marketplace"], "nstarman-skills")
        self.assertIn("Do not edit", doc["$comment"])
        self.assertEqual([s["name"] for s in doc["skills"]], ["alpha", "beta", "mid", "zeta"])
        alpha, mid = doc["skills"][0], doc["skills"][2]
        self.assertEqual(alpha, {
            "name": "alpha", "description": "Alpha does a.", "origin": "local",
            "href": "https://github.com/nstarman/skills/tree/main/alpha",
            "source": {"repo": "nstarman/skills", "path": "alpha", "ref": "main"},
            "install": "alpha@nstarman-skills",
            "zip": "https://github.com/nstarman/skills/releases/latest/download/alpha.zip"})
        self.assertEqual(mid["origin"], "external")
        self.assertEqual(mid["href"], "https://github.com/Org/mid/tree/v1.2.0/skills/mid")
        self.assertEqual(mid["source"], {"repo": "Org/mid", "path": "skills/mid", "ref": "v1.2.0"})
        text = (self.root / "index.json").read_text(encoding="utf-8")
        self.assertTrue(text.endswith("}\n") and '\n  "skills"' in text)  # 2-space, trailing newline

    def test_readme_sections(self):
        run(self.root)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# skills\n\nIntro.\n") and readme.rstrip().endswith("Footer."))
        table = readme.split("<!-- skills:table:start -->")[1].split("<!-- skills:table:end -->")[0]
        self.assertIn("| [`alpha`](alpha/) | Alpha does a. |  |", table)
        self.assertIn("| [`mid`](https://github.com/Org/mid/tree/v1.2.0/skills/mid) | Mid does m. | "
                      "[Org/mid](https://github.com/Org/mid) |", table)
        install = readme.split("<!-- skills:install:start -->")[1].split("<!-- skills:install:end -->")[0]
        self.assertIn("/plugin marketplace add nstarman/skills", install)
        self.assertIn("/plugin install <name>@nstarman-skills", install)
        self.assertIn("releases/latest", install)

    def test_marketplace(self):
        run(self.root)
        m = json.loads((self.root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(m["name"], "nstarman-skills")
        self.assertEqual(m["owner"]["name"], "Nathaniel Starkman")
        plugins = {p["name"]: p for p in m["plugins"]}
        self.assertEqual(list(plugins), ["alpha", "beta", "mid", "zeta"])
        self.assertEqual(plugins["alpha"], {
            "name": "alpha", "description": "Alpha does a.", "source": "./alpha", "skills": ["./"],
            "homepage": "https://github.com/nstarman/skills/tree/main/alpha"})
        self.assertEqual(plugins["mid"]["source"],
                         {"source": "git-subdir", "url": "Org/mid", "path": "skills/mid", "ref": "v1.2.0"})
        self.assertEqual(plugins["mid"]["skills"], ["./"])

    def test_check(self):
        self.assertEqual(run(self.root, "--check")[0], 1)  # nothing generated yet
        run(self.root)
        self.assertEqual(run(self.root, "--check"), (0, run(self.root, "--check")[1]))
        p = self.root / "index.json"
        p.write_text(p.read_text(encoding="utf-8").replace("Alpha does a.", "Edited."), encoding="utf-8")
        code, msg = run(self.root, "--check")
        self.assertEqual(code, 1)
        self.assertIn("index.json", msg)
        self.assertIn("Edited.", p.read_text(encoding="utf-8"))  # --check reports, never writes

    def test_invalid_input_writes_nothing(self):
        self.repo.external("alpha")  # duplicate of a local skill
        code, msg = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("alpha:", msg)
        self.assertFalse((self.root / "index.json").exists())

    def test_remote(self):
        good = {"mid": skill_md("mid"), "beta": skill_md("beta")}
        with mock.patch.object(skillreg, "fetch_skill_md", side_effect=lambda s, token=None: good[s.name]):
            self.assertEqual(run(self.root, "--remote")[0], 0)

        bad = {"mid": skill_md("other"), "beta": skill_md("beta", "x" * 1025)}
        with mock.patch.object(skillreg, "fetch_skill_md", side_effect=lambda s, token=None: bad[s.name]):
            code, msg = run(self.root, "--remote")
        self.assertEqual(code, 1)
        self.assertRegex(msg, r"mid.*name 'other'")
        self.assertRegex(msg, r"beta.*1024")

        def missing(s, token=None):
            raise skillreg.SkillError(f"{s.name}: {s.repo}/{s.path}/SKILL.md not found at {s.ref}")
        with mock.patch.object(skillreg, "fetch_skill_md", side_effect=missing):
            code, msg = run(self.root, "--remote")
        self.assertEqual(code, 1)
        self.assertIn("mid: Org/mid/skills/mid/SKILL.md not found at v1.2.0", msg)


if __name__ == "__main__":
    unittest.main()
