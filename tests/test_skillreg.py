"""skillreg: discovering local skills, reading the registry, offline validation."""

import unittest

from helpers import TempRepo, skill_md

import skillreg


class SkillregTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.close()

    def validate(self):
        return skillreg.validate_offline(self.repo.root)

    def test_discovers_only_top_level_skill_folders(self):
        self.repo.local("alpha")
        for hidden in (".claude/skills/speckit-plan", ".specify", ".github/skills/code-review", "scripts",
                       "specs", "tests"):
            d = self.repo.root / hidden
            d.mkdir(parents=True, exist_ok=True)
            (d / "SKILL.md").write_text(skill_md("x"), encoding="utf-8")
        (self.repo.root / "notes").mkdir()  # a folder without SKILL.md is not a skill
        self.assertEqual([s.name for s in skillreg.discover_local(self.repo.root)], ["alpha"])

    def test_valid_repo(self):
        self.repo.local("alpha")
        self.repo.external("beta", repo="o/r", path="skills/beta", ref="v1.0.0")
        errors, warnings, skills = self.validate()
        self.assertEqual((errors, warnings), ([], []))
        by = {s.name: s for s in skills}
        self.assertEqual(by["alpha"].origin, "local")
        self.assertEqual((by["alpha"].repo, by["alpha"].path, by["alpha"].ref), ("nstarman/skills", "alpha", "main"))
        self.assertEqual(by["beta"].href, "https://github.com/o/r/tree/v1.0.0/skills/beta")
        self.assertEqual(by["beta"].install, "beta@nstarman-skills")
        self.assertEqual(by["beta"].zip, "https://github.com/nstarman/skills/releases/latest/download/beta.zip")
        self.assertEqual(by["alpha"].href, "https://github.com/nstarman/skills/tree/main/alpha")

    def assert_error(self, pattern):
        errors, _, _ = self.validate()
        self.assertTrue(any(__import__("re").search(pattern, e) for e in errors), errors)

    def test_card_problems(self):
        self.repo.local("alpha", card={"name": "alpha", "description": "d", "extra": 1})
        self.assert_error(r"^alpha/card\.json: .*exactly")

    def test_card_missing(self):
        self.repo.local("alpha", card=False)
        self.assert_error(r"^alpha: no card\.json")

    def test_empty_description(self):
        self.repo.local("alpha", description="  ")
        self.assert_error(r"^alpha/card\.json: .*non-empty")

    def test_bad_names(self):
        self.repo.local("Alpha")
        self.assert_error(r"^Alpha: name .*\[a-z0-9-\]")

    def test_folder_and_skill_md_names_must_match(self):
        self.repo.local("alpha", md=skill_md("other"))
        self.assert_error(r"^alpha/SKILL\.md: name 'other' .*folder")

    def test_skill_md_description_limit(self):
        self.repo.local("alpha", md=skill_md("alpha", "x" * 1025))
        self.assert_error(r"^alpha/SKILL\.md: description .*1024")

    def test_long_skill_md_is_a_warning(self):
        self.repo.local("alpha", md=skill_md("alpha", extra_lines=520))
        errors, warnings, _ = self.validate()
        self.assertEqual(errors, [])
        self.assertTrue(any("500 lines" in w for w in warnings), warnings)

    def test_registry_entry_keys(self):
        self.repo.external("beta", entry={"name": "beta", "description": "d",
                                          "source": {"repo": "o/r", "path": "p", "ref": "main"}, "x": 1})
        self.assert_error(r"^registry/beta\.json: .*exactly")
        self.repo.external("gamma", entry={"name": "gamma", "description": "d", "source": {"repo": "o/r", "path": "p"}})
        self.assert_error(r"^registry/gamma\.json: source .*exactly")

    def test_registry_file_stem(self):
        self.repo.external("beta", filename="other")
        self.assert_error(r"^registry/other\.json: name 'beta' .*file name")

    def test_registry_repo_and_path(self):
        self.repo.external("beta", repo="not-a-repo")
        self.assert_error(r"^registry/beta\.json: source\.repo")
        self.repo.external("gamma", path="../escape")
        self.assert_error(r"^registry/gamma\.json: source\.path")
        self.repo.external("delta", path="/abs")
        self.assert_error(r"^registry/delta\.json: source\.path")

    def test_duplicate_names(self):
        self.repo.local("alpha")
        self.repo.external("alpha")
        self.assert_error(r"^alpha: .*both a local skill and a registry entry")

    def test_invalid_json(self):
        (self.repo.root / "registry" / "beta.json").write_text("{nope", encoding="utf-8")
        self.assert_error(r"^registry/beta\.json: not valid JSON")


if __name__ == "__main__":
    unittest.main()
