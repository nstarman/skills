"""Temporary repositories shaped like nstarman/skills, for the tests."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

README = """# skills

Intro.

<!-- skills:table:start -->
<!-- skills:table:end -->

## Installing

<!-- skills:install:start -->
<!-- skills:install:end -->

Footer.
"""


def skill_md(name, description="Does a thing.", extra_lines=0):
    body = "\n".join(f"line {i}" for i in range(extra_lines))
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n{body}\n"


class TempRepo:
    """A scratch repository: add local skills and registry entries, then point the code at it."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "README.md").write_text(README, encoding="utf-8")
        (self.root / "registry").mkdir()

    def close(self):
        self._tmp.cleanup()

    def local(self, name, description="A local skill.", card=None, md=None, files=()):
        d = self.root / name
        d.mkdir()
        (d / "SKILL.md").write_text(md if md is not None else skill_md(name), encoding="utf-8")
        card = {"name": name, "description": description} if card is None else card
        if card is not False:
            (d / "card.json").write_text(json.dumps(card), encoding="utf-8")
        for f in files:
            (d / f).parent.mkdir(parents=True, exist_ok=True)
            (d / f).write_text(f"content of {f}\n", encoding="utf-8")
        return d

    def external(self, name, repo="owner/repo", path=None, ref="main", description="An external skill.",
                 entry=None, filename=None):
        entry = entry if entry is not None else {
            "name": name, "description": description,
            "source": {"repo": repo, "path": path or f"skills/{name}", "ref": ref}}
        p = self.root / "registry" / f"{filename or name}.json"
        p.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        return p
