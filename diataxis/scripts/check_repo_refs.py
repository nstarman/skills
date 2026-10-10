#!/usr/bin/env python3
"""Find everything OUTSIDE docs/ that still points at a doc page you moved or deleted.

This is the failure that survives every docs-only check. A restructure passes the link
checker, builds clean, and then breaks the repo, because the docs are not the only thing
that references the docs:

  - tests that read a doc file (a spec/code drift gate parsing `docs/spec.md`)
  - noxfile.py / tox.ini / Makefile targets and `sphinx-apidoc -o docs/api`
  - CI workflows naming doc paths
  - README.md, AGENTS.md, CONTRIBUTING.md linking to `docs/dev.md`
  - .readthedocs.yaml, mkdocs.yml, pyproject metadata, package docs in subprojects

Every one of those is a 404 on GitHub or a red CI run on first push, and none of them is
visible from inside `docs/`. Run this before you call a restructure done.

Usage
-----
    # what the tree used to contain vs what it contains now
    python check_repo_refs.py REPO_ROOT --old-docs /path/to/pristine/docs --new-docs ./docs

    # or, if you moved docs in place and have the old paths in a redirect map
    python check_repo_refs.py REPO_ROOT --map audit/migration-map.md --new-docs ./docs

Exit code 0 when nothing dangles, 1 otherwise. Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {".git", "_build", "build", "dist", "site", "node_modules", ".tox", ".nox",
             ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
             ".ipynb_checkpoints", "htmlcov", ".eggs"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", ".gz", ".whl",
            ".so", ".pyc", ".woff", ".woff2", ".ttf", ".inv", ".parquet", ".npy"}
DOC_EXT = (".md", ".markdown", ".rst", ".txt", ".ipynb")
# A redirect map's whole job is to name paths that no longer exist. Scanning it reports
# every entry as a defect, which buries the real hits.
SKIP_NAMES = {"redirects.txt", "redirect_map.txt", "_redirects", "rediraffe.txt"}

# A reference looks like a path ending in a doc extension. Capture generously and filter
# later — a false candidate costs one lookup, a missed one costs a broken repo.
REF = re.compile(r"""(?<![\w/.-])((?:[\w.@-]+/)*[\w.@-]+\.(?:md|markdown|rst|txt|ipynb))""")


def walk_files(root: str, docs_dirs: set[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".egg")]
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        # Skip the docs tree itself — check_links.py covers inside-docs links.
        if any(rel_dir == d or rel_dir.startswith(d + "/") for d in docs_dirs):
            continue
        for name in filenames:
            if os.path.splitext(name)[1].lower() in SKIP_EXT or name in SKIP_NAMES:
                continue
            yield os.path.join(dirpath, name)


def doc_paths(docs_root: str, repo_root: str) -> set[str]:
    """Every doc file under docs_root, as a repo-relative path and as a bare basename."""
    out: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(docs_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith(DOC_EXT):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, repo_root).replace(os.sep, "/")
                out.add(rel)
    return out


def parse_map_old_paths(map_path: str) -> set[str]:
    out: set[str] = set()
    with open(map_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            for cell in line.strip().strip("|").split("|"):
                m = re.search(r"`([^`]+\.(?:md|rst|markdown|txt|ipynb))`", cell)
                if m:
                    out.add(m.group(1).lstrip("./"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo_root")
    ap.add_argument("--old-docs", help="pristine docs tree (before the restructure)")
    ap.add_argument("--map", help="migration map, to read old paths from instead")
    ap.add_argument("--new-docs", required=True, help="docs tree as it is now")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo_root)
    new_docs = os.path.abspath(args.new_docs)
    if not os.path.isdir(repo) or not os.path.isdir(new_docs):
        print("error: repo_root and --new-docs must be directories", file=sys.stderr)
        return 2

    now = doc_paths(new_docs, repo)
    now_basenames = {os.path.basename(p) for p in now}

    gone: set[str] = set()
    if args.old_docs and os.path.isdir(args.old_docs):
        before = doc_paths(os.path.abspath(args.old_docs), repo)
        # old-docs may live outside the repo; normalise on the docs-relative part.
        old_rel = {os.path.relpath(os.path.join(os.path.abspath(args.old_docs), ""), repo)}
        before = {p for p in before}
        gone = {p for p in before if p not in now}
        if not gone:
            # old-docs was outside the repo: compare on the path below the docs dir
            b2 = {os.path.relpath(os.path.join(dp, f), os.path.abspath(args.old_docs))
                  .replace(os.sep, "/")
                  for dp, dn, fs in os.walk(os.path.abspath(args.old_docs))
                  for f in fs if f.lower().endswith(DOC_EXT)}
            n2 = {os.path.relpath(os.path.join(dp, f), new_docs).replace(os.sep, "/")
                  for dp, dn, fs in os.walk(new_docs)
                  for f in fs if f.lower().endswith(DOC_EXT)}
            docs_name = os.path.relpath(new_docs, repo).replace(os.sep, "/")
            gone = {f"{docs_name}/{p}" for p in (b2 - n2)}
    if args.map:
        gone |= {p for p in parse_map_old_paths(args.map) if p not in now}

    if not gone:
        print("error: could not determine which doc paths went away. Pass --old-docs "
              "pointing at a pristine copy, or --map pointing at the migration map.",
              file=sys.stderr)
        return 2

    gone_basenames = defaultdict(set)
    for p in gone:
        gone_basenames[os.path.basename(p)].add(p)

    # Skip the docs tree itself, whether --new-docs points inside the repo or at a staged
    # copy elsewhere — in the latter case the repo's own docs dir still needs skipping.
    docs_dirs = {os.path.relpath(new_docs, repo).replace(os.sep, "/"),
                 os.path.basename(new_docs.rstrip("/"))}
    docs_dirs = {d for d in docs_dirs if d and not d.startswith("..")}
    hits: list[dict] = []
    scanned = 0

    for path in walk_files(repo, docs_dirs):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        scanned += 1
        rel = os.path.relpath(path, repo).replace(os.sep, "/")
        for i, line in enumerate(lines, start=1):
            # A markdown link writes the path twice ([`docs/x.md`](docs/x.md)); report once.
            for cand in dict.fromkeys(REF.findall(line)):
                c = cand.lstrip("./")
                base = os.path.basename(c)
                # Direct hit on a path that no longer exists.
                if c in gone:
                    hits.append({"file": rel, "line": i, "ref": cand,
                                 "why": "path no longer exists"})
                    continue
                # A bare or partial reference whose basename only ever existed in the old tree.
                if base in gone_basenames and base not in now_basenames:
                    if any(c.endswith(g) or g.endswith(c) for g in gone_basenames[base]):
                        hits.append({"file": rel, "line": i, "ref": cand,
                                     "why": f"{base} was removed from the docs tree"})

    if hits:
        print(f"{len(hits)} stale reference(s) to moved or deleted doc pages, "
              f"in {len({h['file'] for h in hits})} file(s) outside the docs tree:\n")
        by_file: defaultdict[str, list] = defaultdict(list)
        for h in hits:
            by_file[h["file"]].append(h)
        for f in sorted(by_file):
            print(f"  {f}")
            for h in sorted(by_file[f], key=lambda x: x["line"]):
                print(f"    line {h['line']:>4}  {h['ref']}  — {h['why']}")
            print()
        print("Fix these before calling the restructure done. A test or noxfile that reads a "
              "doc path fails CI on the first push; a README or AGENTS.md link 404s on GitHub.")
    elif not args.quiet:
        print(f"OK — scanned {scanned} files outside the docs tree; no stale doc references. "
              f"({len(gone)} doc paths moved or were deleted.)")

    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
