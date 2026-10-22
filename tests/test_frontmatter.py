"""skillreg.parse_frontmatter: the subset of YAML that SKILL.md frontmatter uses (research R3)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from skillreg import SkillError, parse_frontmatter  # noqa: E402


def fm(body: str) -> str:
    return f"---\n{body}---\n\n# Title\n"


class FrontmatterTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_frontmatter(fm("name: quax\ndescription: Use quax well.\n")),
                         {"name": "quax", "description": "Use quax well."})

    def test_quoted(self):
        got = parse_frontmatter(fm('name: "a-b"\ndescription: \'It\'\'s "quoted": yes\'\n'))
        self.assertEqual(got, {"name": "a-b", "description": 'It\'s "quoted": yes'})
        got = parse_frontmatter(fm('name: x\ndescription: "a \\"b\\" c\\\\d"\n'))
        self.assertEqual(got["description"], 'a "b" c\\d')

    def test_folded_block_like_unxt(self):
        body = ("name: unxt\ndescription: >\n"
                "  Use when writing code that imports unxt (Quantity, units). Also use when a\n"
                "  dimension mismatch error like \"'yr' (time) and 'km' (length)\" appears.\n")
        got = parse_frontmatter(fm(body))
        self.assertEqual(got["description"],
                         "Use when writing code that imports unxt (Quantity, units). Also use when a "
                         "dimension mismatch error like \"'yr' (time) and 'km' (length)\" appears.\n")

    def test_block_chomping_and_paragraphs(self):
        body = "name: x\ndescription: >-\n  one\n  two\n\n  three\n"
        self.assertEqual(parse_frontmatter(fm(body))["description"], "one two\nthree")
        body = "name: x\ndescription: |\n  line one\n  line two\n"
        self.assertEqual(parse_frontmatter(fm(body))["description"], "line one\nline two\n")
        body = "name: x\ndescription: |+\n  keep\n\n"
        self.assertEqual(parse_frontmatter(fm(body))["description"], "keep\n\n")

    def test_plain_multiline(self):
        body = "name: x\ndescription: first part\n  continues here\n"
        self.assertEqual(parse_frontmatter(fm(body))["description"], "first part continues here")

    def test_other_keys_are_skipped(self):
        body = "name: x\nallowed-tools:\n  - Bash\n  - Read\nmetadata:\n  a: b\ndescription: d\n"
        got = parse_frontmatter(fm(body))
        self.assertEqual((got["name"], got["description"]), ("x", "d"))

    def test_missing_delimiters(self):
        with self.assertRaises(SkillError):
            parse_frontmatter("name: x\n")
        with self.assertRaises(SkillError):
            parse_frontmatter("---\nname: x\n")

    def test_unsupported_value_names_the_file(self):
        with self.assertRaisesRegex(SkillError, "foo/SKILL.md"):
            parse_frontmatter(fm("name: [a, b]\ndescription: d\n"), source="foo/SKILL.md")
        with self.assertRaisesRegex(SkillError, "foo/SKILL.md"):
            parse_frontmatter(fm('name: x\ndescription: "unterminated\n'), source="foo/SKILL.md")


if __name__ == "__main__":
    unittest.main()
