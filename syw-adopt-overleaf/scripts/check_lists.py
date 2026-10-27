#!/usr/bin/env python3
"""Check showyourwork's Overleaf push/pull lists against the migration inventory.

Usage:
    check_lists.py <overleaf block or showyourwork.yml> <inventory.tsv>

Fails (exit 1), naming each path, when:
  both     a path is in both lists, or a folder in one list covers a path in the other;
  authored a push entry covers a class-1 (authored) file, so a build would overwrite it;
  private  any entry covers a class-4 file (notes, referee replies, ...).
Paths are compared relative to src/tex/; an entry covers a path it equals or is a folder of.
"""

import re
import sys
from pathlib import Path


def read_lists(text):
    """The `push:` and `pull:` item lists under `overleaf:` (a minimal reader, no YAML library)."""
    lists, key, in_overleaf = {"push": [], "pull": []}, None, False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            in_overleaf, key = line.startswith("overleaf:"), None
            continue
        if not in_overleaf:
            continue
        m = re.match(r"\s*(push|pull)\s*:\s*(#.*)?$", line)
        if m:
            key = m.group(1)
        elif re.match(r"\s*(push|pull)\s*:", line):
            # an inline list (`push: [a, b]`) would otherwise be skipped and the check pass
            raise ValueError(f"write the list as one '- path' line per entry: {line.strip()}")
        elif re.match(r"\s*-\s", line) and key:
            item = line.split("-", 1)[1].split(" #")[0].strip().strip("'\"")
            lists[key].append(("/" + item.rstrip("/")).removeprefix("/src/tex").lstrip("/"))
        elif not line.lstrip().startswith("-"):
            key = None
    return lists["push"], lists["pull"]


def read_inventory(path):
    classes = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            cls, rel = line.split("\t")[:2]
            classes[rel.strip()] = cls.strip()
    return classes


def covers(entry, path):
    return path == entry or path.startswith(entry + "/") or entry in ("", ".")


def problems(push, pull, classes):
    out = []
    for a in push:
        for b in pull:
            if covers(a, b) or covers(b, a):
                out.append(("both", b if covers(a, b) else a))
    for path, cls in sorted(classes.items()):
        if cls == "1" and any(covers(e, path) for e in push):
            out.append(("authored", path))
        if cls == "4" and any(covers(e, path) for e in push + pull):
            out.append(("private", path))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        push, pull = read_lists(Path(argv[0]).read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    found = problems(push, pull, read_inventory(argv[1]))
    for rule, path in found:
        print(f"FAIL {rule}: {path}")
    if not found:
        print(f"ok: {len(push)} push, {len(pull)} pull entries")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
