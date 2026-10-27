#!/usr/bin/env python3
"""Compare a paper's PDF before and after a migration: pages, numbers, text, images.

Usage:
    pdf_diff.py <baseline.pdf> <new.pdf> [--out DIR]

Needs poppler (pdfinfo, pdftotext, pdftoppm). Exit 0 only if nothing differs, 1 if anything
does, 2 on a usage or tool error. Accepting a difference is the author's call, never this script's.
"""

import argparse
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

NUMBER = re.compile(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
DPI = 100
LEVEL = 16  # a channel must differ by more than this to count (absorbs antialiasing)
FRACTION = 0.001  # a page is flagged when more than this fraction of its pixels differ


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def page_count(pdf):
    return int(re.search(r"^Pages:\s+(\d+)", run("pdfinfo", pdf), re.M).group(1))


def page_words(pdf, n):
    """[(page, word), ...] over the whole document, in reading order."""
    return [
        (p, w)
        for p in range(1, n + 1)
        for w in run("pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-").split()
    ]


def diff_runs(a, b):
    """Changed runs between two [(page, token)] lists, as printable lines."""
    sm = difflib.SequenceMatcher(None, [t for _, t in a], [t for _, t in b], autojunk=False)
    lines = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        page = a[i1][0] if i1 < len(a) else b[j1][0] if j1 < len(b) else "?"
        old = " ".join(t for _, t in a[i1:i2]) or "∅"
        new = " ".join(t for _, t in b[j1:j2]) or "∅"
        lines.append(f"p{page}: {old} → {new}")
    return lines


def read_ppm(path):
    """(width, height, bytes) of a binary PPM (P6, maxval 255) as pdftoppm writes it."""
    data = path.read_bytes()
    fields, pos = [], 0
    while len(fields) < 4:
        while data[pos : pos + 1].isspace():
            pos += 1
        if data[pos : pos + 1] == b"#":
            pos = data.index(b"\n", pos)
            continue
        end = pos
        while not data[end : end + 1].isspace():
            end += 1
        fields.append(data[pos:end])
        pos = end
    if fields[0] != b"P6" or fields[3] != b"255":
        raise ValueError(f"{path}: not an 8-bit P6 PPM")
    return int(fields[1]), int(fields[2]), data[pos + 1 :]


def render(pdf, page, prefix, png=False):
    run("pdftoppm", "-r", str(DPI), "-f", str(page), "-l", str(page), "-singlefile", *(["-png"] if png else []), pdf, str(prefix))
    return Path(f"{prefix}.{'png' if png else 'ppm'}")


def page_differs(a, b):
    wa, ha, pa = read_ppm(a)
    wb, hb, pb = read_ppm(b)
    if (wa, ha) != (wb, hb):
        return True
    if pa == pb:  # most pages: skip the slow per-pixel loop
        return False
    changed = sum(
        1
        for i in range(0, len(pa), 3)
        if max(abs(pa[i] - pb[i]), abs(pa[i + 1] - pb[i + 1]), abs(pa[i + 2] - pb[i + 2])) > LEVEL
    )
    return changed > FRACTION * wa * ha


def section(name, lines):
    print(f"== {name}: " + ("same" if not lines else f"{len(lines)} difference(s)"))
    for line in lines:
        print(f"  {line}")
    return bool(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("baseline")
    ap.add_argument("new")
    ap.add_argument("--out", type=Path, help="write PNGs of flagged pages here")
    args = ap.parse_args(argv)

    try:
        na, nb = page_count(args.baseline), page_count(args.new)
        wa, wb = page_words(args.baseline, na), page_words(args.new, nb)
        differs = section("pages", [] if na == nb else [f"{na} → {nb}"])
        nums = lambda words: [(p, t) for p, w in words for t in NUMBER.findall(w)]
        differs |= section("numbers", diff_runs(nums(wa), nums(wb)))
        differs |= section("text", diff_runs(wa, wb))

        flagged = []
        with tempfile.TemporaryDirectory() as tmp:
            for p in range(1, min(na, nb) + 1):
                if page_differs(render(args.baseline, p, Path(tmp) / "a"), render(args.new, p, Path(tmp) / "b")):
                    flagged.append(p)
        if args.out and flagged:
            args.out.mkdir(parents=True, exist_ok=True)
            for p in flagged:
                render(args.baseline, p, args.out / f"p{p}-baseline", png=True)
                render(args.new, p, args.out / f"p{p}-new", png=True)
        differs |= section("images", [f"p{p}" + (f" (see {args.out}/p{p}-*.png)" if args.out else "") for p in flagged])
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, AttributeError) as e:
        print(f"error: {getattr(e, 'stderr', '') or e}", file=sys.stderr)
        return 2
    return 1 if differs else 0


if __name__ == "__main__":
    sys.exit(main())
