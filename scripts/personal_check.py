"""Fail if a file in the repository contains a personal detail (username, path, project name, ...).

    python scripts/personal_check.py [--patterns FILE]

The patterns are personal themselves, so they live outside the repository: one regular
expression per line (case-insensitive; blank lines and `#` comments ignored), by default in
~/.config/skills/personal-strings.txt. Without that file this prints a note and exits 0, so CI
skips it. Prints "path:line: text" per match; exit 1 if any.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = Path.home() / ".config" / "skills" / "personal-strings.txt"


def load(path: Path) -> re.Pattern | None:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    pats = [ln for ln in lines if ln and not ln.startswith("#")]
    return re.compile("|".join(f"(?:{p})" for p in pats), re.IGNORECASE) if pats else None


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--patterns", type=Path, default=DEFAULT)
    args = ap.parse_args(argv)
    if not args.patterns.is_file():
        print(f"no {args.patterns}; personal-details check skipped")
        return 0
    rx = load(args.patterns)
    if rx is None:
        return 0
    hits = []
    # Everything is public, not only the skills; .git and .claude (worktrees, local settings) are not.
    files = (p for p in root.rglob("*") if p.is_file() and not {".git", ".claude"} & set(p.relative_to(root).parts))
    for f in sorted(files):
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append(f"{f.relative_to(root)}:{n}: {line.strip()[:160]}")
    print("\n".join(hits) if hits else "no personal details found")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
