#!/usr/bin/env python3
"""Turn the migration map's redirect table into redirect artifacts, from one source of truth.

A restructure changes every URL. Hand-maintaining a redirect list alongside the migration map
means two lists that drift, and hand-rolling the `dirhtml` vs `html` path rule is where these
go wrong. This reads the redirect table straight out of `audit/migration-map.md` (or any
Markdown table, or a plain two-column file) and emits whichever artifact the stack needs.

Emitters
--------
  stubs      Fragment-preserving meta-refresh HTML at each old path. Works anywhere, including
             stacks with no redirect support at all (Zensical). Copy into the built site, or
             point the SSG's "extra files" setting at the output directory.
  netlify    A `_redirects` file — real 301s on Netlify, Cloudflare Pages, and compatible hosts.
  nginx      `location` blocks for a server-side 301.
  rediraffe  A `redirects.txt` for sphinxext-rediraffe (source filenames both sides).
  reredirects  A Python dict literal for sphinx-reredirects' `redirects =` setting.

Input format
------------
Any Markdown table with a column whose header contains "old" and one containing "new"; other
columns are ignored, so the migration map's own table works unmodified. Anchors are supported
and preserved: `/usage/#pipeline-methods` → `/reference/api/#pipeline-methods`. Lines in a
plain text file are `<old> <new>` pairs, `#` for comments.

Usage
-----
    python make_redirect_stubs.py --map audit/migration-map.md --out redirects/ --emit stubs
    python make_redirect_stubs.py --map audit/migration-map.md --emit netlify
    python make_redirect_stubs.py --map redirects.tsv --emit stubs --out site/ --url-style flat

Stdlib only.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys

ROW = re.compile(r"^\s*\|(.+)\|\s*$")
CODE_SPAN = re.compile(r"`([^`]*)`")
SEPARATOR = re.compile(r"^[\s|:\-]+$")

STUB = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved</title>
<link rel="canonical" href="{to}">
<meta name="robots" content="noindex">
<noscript><meta http-equiv="refresh" content="0; url={to}"></noscript>
<script>
// A split page sends different anchors to different destinations, so the fragment decides
// where we land. Deep links carry anchors; dropping them strands the reader at the top of
// a long page with no idea why.
var DEFAULT = "{to}";
var ANCHORS = {anchors};
var hash = window.location.hash.replace(/^#/, "");
var target = (hash && Object.prototype.hasOwnProperty.call(ANCHORS, hash))
  ? ANCHORS[hash]
  : (hash && DEFAULT.indexOf("#") === -1 ? DEFAULT + "#" + hash : DEFAULT);
window.location.replace(target);
</script>
</head>
<body>
<p>This page has moved to <a href="{to}">{to_text}</a>.</p>
</body>
</html>
"""


def clean(cell: str) -> str:
    cell = cell.strip()
    m = CODE_SPAN.search(cell)
    if m:
        cell = m.group(1)
    cell = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell)
    return cell.strip().strip("`").strip()


def parse_map(path: str) -> list[tuple[str, str]]:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    pairs: list[tuple[str, str]] = []
    header: list[str] | None = None
    old_i = new_i = None

    for raw in lines:
        m = ROW.match(raw)
        if not m:
            if not raw.strip().startswith("|"):
                header = None
                old_i = new_i = None
            if raw.strip() and not raw.lstrip().startswith(("#", "|")) and "\t" in raw or \
               (raw.strip() and not raw.lstrip().startswith(("#", "|")) and re.match(r"^\S+\s+\S+$", raw.strip())):
                a, b = raw.split()[:2]
                pairs.append((a, b))
            continue

        cells = [c.strip() for c in m.group(1).split("|")]
        if SEPARATOR.match(m.group(1)):
            continue
        lowered = [c.lower() for c in cells]
        if header is None or old_i is None:
            cand_old = next((i for i, c in enumerate(lowered) if "old" in c), None)
            cand_new = next((i for i, c in enumerate(lowered)
                             if "new" in c or "destination" in c or "target" in c), None)
            if cand_old is not None and cand_new is not None:
                header, old_i, new_i = cells, cand_old, cand_new
                continue
            continue

        if max(old_i, new_i) >= len(cells):
            continue
        old, new = clean(cells[old_i]), clean(cells[new_i])
        if not old or not new or old.lower().startswith("old"):
            continue
        if old in ("—", "-", "n/a") or new in ("—", "-", "n/a"):
            continue
        pairs.append((old, new))

    seen = set()
    unique = []
    for a, b in pairs:
        if a == b:
            continue          # identity rows are no-ops and would loop
        if a not in seen:
            seen.add(a)
            unique.append((a, b))
    return unique


def url_to_stub_path(url: str, style: str) -> str:
    """Where the stub file goes for an old URL. This is the rule everyone gets wrong by hand."""
    path = url.split("#")[0].split("?")[0].lstrip("/")
    if not path:
        return "index.html"
    if path.endswith(".html"):
        return path
    if style == "flat":
        return path.rstrip("/") + ".html"
    return path.rstrip("/") + "/index.html"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", required=True, help="migration-map.md, or a two-column text file")
    ap.add_argument("--emit", default="stubs",
                    choices=("stubs", "netlify", "nginx", "rediraffe", "reredirects"))
    ap.add_argument("--out", help="output directory (stubs) or file; default stdout for text emitters")
    ap.add_argument("--url-style", choices=("dirhtml", "flat"), default="dirhtml",
                    help="dirhtml: /page/ -> page/index.html (MkDocs, Zensical, sphinx dirhtml). "
                         "flat: /page.html -> page.html (sphinx default html builder)")
    args = ap.parse_args()

    if not os.path.exists(args.map):
        print(f"error: {args.map} not found", file=sys.stderr)
        return 2

    pairs = parse_map(args.map)
    if not pairs:
        print(f"error: no redirect rows found in {args.map}. Expected a Markdown table with "
              f"an 'Old URL' column and a 'New URL' column.", file=sys.stderr)
        return 1

    if args.emit == "stubs":
        out = args.out or "redirects"
        # Group by the old page: several rows can share one old path when a split page sends
        # different anchors to different destinations. One file, one anchor map.
        grouped: dict[str, dict] = {}
        for old, new in pairs:
            base, _, frag = old.partition("#")
            g = grouped.setdefault(base, {"default": None, "anchors": {}})
            if frag:
                g["anchors"][frag] = new
            else:
                g["default"] = new
        written = 0
        for base, g in grouped.items():
            default = g["default"]
            if default is None:
                # Only anchored rows for this page: send the bare URL to the most common target.
                default = max(set(g["anchors"].values()),
                              key=list(g["anchors"].values()).count)
                print(f"note: {base} had only anchored rows; bare URL -> {default}",
                      file=sys.stderr)
            dest = os.path.join(out, url_to_stub_path(base, args.url_style))
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            anchors_js = "{" + ", ".join(
                f'"{html.escape(k, quote=True)}": "{html.escape(v, quote=True)}"'
                for k, v in sorted(g["anchors"].items())) + "}"
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(STUB.format(to=html.escape(default, quote=True),
                                     to_text=html.escape(default), anchors=anchors_js))
            written += 1
        print(f"wrote {written} stub(s) under {out}/", file=sys.stderr)
        print("Copy these into the built site (or point the SSG's extra-files setting here). "
              "Meta-refresh is a fallback: prefer server-side 301s where you control the host.",
              file=sys.stderr)
        return 0

    # Servers never see the fragment, so host-level rules can only act on the base path.
    # Anchored rows are dropped here and reported, because silently emitting a rule that
    # cannot fire is how a redirect map comes to look complete while losing deep links.
    anchored = [old for old, _ in pairs if "#" in old]
    base_pairs = [(o, n) for o, n in pairs if "#" not in o]
    if anchored and args.emit in ("netlify", "nginx"):
        print(f"warning: {len(anchored)} anchored row(s) cannot be expressed as host rules "
              f"(servers do not receive the fragment). Emit --emit stubs as well to preserve "
              f"them: {', '.join(anchored[:5])}" + (" …" if len(anchored) > 5 else ""),
              file=sys.stderr)

    if args.emit == "netlify":
        body = "\n".join(f"{old}  {new}  301!" for old, new in base_pairs) + "\n"
    elif args.emit == "nginx":
        body = "\n".join(
            f'location = {old.rstrip("/") or "/"} {{ return 301 {new}; }}'
            for old, new in base_pairs) + "\n"
    elif args.emit == "rediraffe":
        body = ("# sphinxext-rediraffe: source filenames on both sides\n"
                + "\n".join(f'"{old}" "{new}"' for old, new in pairs) + "\n")
    else:
        rows = "\n".join(f'    "{old}": "{new}",' for old, new in pairs)
        body = f"redirects = {{\n{rows}\n}}\n"

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"wrote {args.out} ({len(pairs)} entries)", file=sys.stderr)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
