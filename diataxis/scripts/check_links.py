#!/usr/bin/env python3
"""Check every internal link and anchor in a docs tree — before any build, on any stack.

A Diátaxis restructure moves every page, so internal links and heading anchors break in bulk.
Each toolchain has its own build-time checker (`sphinx-build -W -n`, `zensical build --strict`),
but you need the answer *while editing*, on trees that do not build yet, and on stacks whose
checker does not verify fragments. This does that with no dependencies.

What it resolves:
  - relative Markdown links: [text](../reference/cli.md#flags)
  - MyST/Sphinx roles: {doc}`/reference/cli`, {ref}`cli-run-flags`
  - reStructuredText :doc:/:ref: roles
  - fragments, against GitHub-style heading slugs plus explicit anchors:
      (label)=          MyST target
      {#custom-id}      attr_list / attrs_block
      .. _label:        rST target
      :name: label      directive option

Usage
-----
    python check_links.py DOCS_ROOT [--format text|json] [--quiet]

Exit code 0 when clean, 1 when anything is unresolved — so it drops straight into CI.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict

SUFFIXES = (".md", ".markdown", ".mdx", ".rst")
SKIP_DIRS = {"_build", "build", "site", "node_modules", ".git", ".tox", ".venv",
             "venv", "__pycache__", ".ipynb_checkpoints"}

CODE_FENCE = re.compile(r"^\s*(?:```|~~~)")
FRONT_MATTER = re.compile(r"^---\s*$")

MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(\s*<?([^)>\s]+)>?\s*(?:\"[^\"]*\")?\s*\)")
MD_REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)")
DOC_ROLE = re.compile(r"[:{](?:doc)[:}]`([^`]+)`")
REF_ROLE = re.compile(r"[:{](?:ref)[:}]`([^`]+)`")
ROLE_TARGET = re.compile(r"<([^>]+)>\s*$")

MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
RST_UNDERLINE = re.compile(r"^([=\-~^\"'`#*+_:.])\1{2,}\s*$")
MYST_TARGET = re.compile(r"^\((\S+?)\)=\s*$")
ATTR_ID = re.compile(r"\{#([A-Za-z0-9_.:-]+)")
RST_TARGET = re.compile(r"^\.\.\s+_([^:]+):\s*$")
NAME_OPTION = re.compile(r"^\s*:name:\s*(\S+)\s*$")

EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)


def slugify(text: str) -> str:
    """GitHub-style heading slug — the convention myst_heading_anchors and most SSGs follow."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"[\s]+", "-", text).strip("-")


def walk(root: str) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(SUFFIXES):
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def strip_front_matter(lines: list[str]) -> list[str]:
    if lines and FRONT_MATTER.match(lines[0]):
        for i in range(1, len(lines)):
            if FRONT_MATTER.match(lines[i]):
                return lines[i + 1:]
    return lines


def scan(path: str, root: str):
    """Return (anchors, global_labels, links) for one file."""
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = strip_front_matter(fh.read().splitlines())

    anchors: set[str] = set()
    labels: set[str] = set()
    links: list[tuple[int, str]] = []
    pending_target: str | None = None
    in_code = False
    seen_slugs: defaultdict[str, int] = defaultdict(int)

    for idx, raw in enumerate(lines, start=1):
        if CODE_FENCE.match(raw):
            in_code = not in_code
            continue
        if in_code:
            continue

        m = MYST_TARGET.match(raw) or RST_TARGET.match(raw)
        if m:
            label = m.group(1).strip()
            labels.add(label)
            anchors.add(label)
            pending_target = label
            continue

        m = NAME_OPTION.match(raw)
        if m:
            labels.add(m.group(1))
            anchors.add(m.group(1))

        for aid in ATTR_ID.findall(raw):
            anchors.add(aid)

        heading = None
        m = MD_HEADING.match(raw)
        if m:
            heading = m.group(2)
        elif idx < len(lines) and raw.strip() and RST_UNDERLINE.match(lines[idx]):
            heading = raw.strip()

        if heading is not None:
            base = slugify(re.sub(r"\{#[^}]*\}", "", heading))
            if base:
                seen_slugs[base] += 1
                anchors.add(base if seen_slugs[base] == 1 else f"{base}-{seen_slugs[base] - 1}")
            pending_target = None
            continue

        if raw.strip():
            pending_target = pending_target if MYST_TARGET.match(raw) else pending_target

        for target in MD_LINK.findall(raw):
            links.append((idx, target))
        m = MD_REF_DEF.match(raw)
        if m:
            links.append((idx, m.group(1)))
        for role_body in DOC_ROLE.findall(raw):
            mt = ROLE_TARGET.search(role_body)
            links.append((idx, "\0doc\0" + (mt.group(1) if mt else role_body).strip()))
        for role_body in REF_ROLE.findall(raw):
            mt = ROLE_TARGET.search(role_body)
            links.append((idx, "\0ref\0" + (mt.group(1) if mt else role_body).strip()))

    return rel, anchors, labels, links


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--quiet", action="store_true", help="only report failures")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"error: {args.root} is not a directory", file=sys.stderr)
        return 2

    paths = walk(root)
    files: dict[str, dict] = {}
    global_labels: dict[str, str] = {}
    for p in paths:
        rel, anchors, labels, links = scan(p, root)
        files[rel] = {"anchors": anchors, "links": links}
        for lb in labels:
            global_labels.setdefault(lb, rel)

    # Index every way a page might be addressed: with suffix, without, and as a directory URL.
    index: dict[str, str] = {}
    for rel in files:
        stem = os.path.splitext(rel)[0]
        index[rel] = rel
        index[stem] = rel
        index["/" + rel] = rel
        index["/" + stem] = rel
        if os.path.basename(stem) in ("index", "README"):
            parent = os.path.dirname(stem)
            index[parent or "."] = rel
            index["/" + parent if parent else "/"] = rel

    problems: list[dict] = []

    for rel, data in files.items():
        here = os.path.dirname(rel)
        for line, target in data["links"]:
            kind = "link"
            if target.startswith("\0doc\0"):
                kind, target = "doc-role", target[5:]
            elif target.startswith("\0ref\0"):
                label = target[5:]
                if label not in global_labels:
                    problems.append({"file": rel, "line": line, "target": label,
                                     "kind": "ref-role", "reason": "no such label anywhere"})
                continue

            if not target or EXTERNAL.match(target) or target.startswith(("#", "{", "%")):
                if target.startswith("#"):
                    frag = target[1:]
                    if frag and frag not in data["anchors"] and frag not in global_labels:
                        problems.append({"file": rel, "line": line, "target": target,
                                         "kind": "fragment", "reason": "no such anchor on this page"})
                continue

            path_part, _, frag = target.partition("#")
            path_part = path_part.strip()
            if not path_part:
                continue

            if path_part.startswith("/"):
                cand = path_part.lstrip("/")
                resolved = index.get(cand) or index.get("/" + cand)
            else:
                joined = os.path.normpath(os.path.join(here, path_part)).replace(os.sep, "/")
                resolved = index.get(joined)
                if resolved is None and joined.endswith("/"):
                    resolved = index.get(joined.rstrip("/"))

            if resolved is None:
                # A link to a real non-doc asset (image, .py, .csv) is fine if it exists on disk.
                disk = os.path.normpath(os.path.join(root, here, path_part))
                if os.path.exists(disk):
                    continue
                problems.append({"file": rel, "line": line, "target": target, "kind": kind,
                                 "reason": "no such page"})
                continue

            if frag:
                if frag not in files[resolved]["anchors"] and frag not in global_labels:
                    problems.append({"file": rel, "line": line, "target": target, "kind": "fragment",
                                     "reason": f"no anchor '{frag}' in {resolved}"})

    if args.format == "json":
        print(json.dumps({"root": os.path.relpath(root), "files": len(files),
                          "problems": problems}, indent=2))
    else:
        if problems:
            print(f"{len(problems)} unresolved link(s) across {len(files)} files:\n")
            by_file: defaultdict[str, list] = defaultdict(list)
            for p in problems:
                by_file[p["file"]].append(p)
            for f in sorted(by_file):
                print(f"  {f}")
                for p in sorted(by_file[f], key=lambda x: x["line"]):
                    print(f"    line {p['line']:>4}  {p['target']}  — {p['reason']}")
                print()
        elif not args.quiet:
            print(f"OK — {len(files)} files, every internal link and anchor resolves.")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
