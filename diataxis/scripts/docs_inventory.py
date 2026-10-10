#!/usr/bin/env python3
"""Inventory a documentation tree and score each page against the four Diátaxis modes.

The scores are a *starting point for the compass*, not a verdict. This script counts words;
it does not know what a user needs. What it is genuinely good at:

  - ordering the work, so you read the most mixed pages first
  - flagging sections whose mode disagrees with their page (the SPLIT/EXTRACT seams)
  - finding pages nothing links to, and duplicate titles (the same content in two places)
  - giving you a per-heading breakdown, so you can apply the compass at section scale

Usage
-----
    python docs_inventory.py DOCS_ROOT [--format md|csv|json] [--out FILE]
                             [--sections] [--min-words N]

Stdlib only; no dependencies.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict

MODES = ("tutorial", "howto", "reference", "explanation")

MODE_LABEL = {
    "tutorial": "tutorial",
    "howto": "how-to",
    "reference": "reference",
    "explanation": "explanation",
    "unclear": "_no signal_",
    None: "—",
}

# --------------------------------------------------------------------------------------
# Signals
#
# Each entry is (compiled pattern, weight). Weights are deliberately coarse: strong phrases
# that only occur in one mode score 3, moderate cues 2, weak cues 1. The point is ranking
# and mixedness detection, not classification accuracy.
# --------------------------------------------------------------------------------------

def _rx(*alts: str) -> re.Pattern:
    return re.compile("|".join(alts), re.IGNORECASE)


SIGNALS: dict[str, list[tuple[re.Pattern, int]]] = {
    "tutorial": [
        (_rx(r"\bin this tutorial\b", r"\bthis tutorial\b"), 4),
        (_rx(r"\byou will learn\b", r"\bwe will (?:build|create|make|write|deploy)\b"), 3),
        (_rx(r"\blet'?s\b", r"\bwe'?ll\b", r"\bwe are going to\b"), 2),
        (_rx(r"\bnotice that\b", r"\byou should see\b", r"\bthe output should\b",
             r"\bshould look something like\b"), 3),
        (_rx(r"\bfirst,\b", r"\bnow,\b", r"\bnext,\b", r"\bfinally,\b"), 1),
        (_rx(r"\bby the end of this\b", r"\bcongratulations\b", r"\bwhat you'?ve? (?:built|learned)\b"), 3),
        (_rx(r"\bstep \d+\b"), 1),
        (_rx(r"\byour first\b", r"\bgetting started\b"), 2),
    ],
    "howto": [
        (_rx(r"\bhow to\b"), 3),
        (_rx(r"\bthis guide (?:shows|explains how|walks)\b", r"\bthis page shows you how\b"), 3),
        (_rx(r"\bif you want to\b", r"\bif you need to\b", r"\bto (?:enable|disable|configure|add|remove|change|set up|deploy|install) [a-z]"), 2),
        (_rx(r"\bin order to\b", r"\bso that you can\b"), 1),
        (_rx(r"\bprerequisites?\b", r"\bbefore you begin\b", r"\byou will need\b"), 2),
        (_rx(r"\btroubleshoot", r"\bif this fails\b", r"\bif you (?:see|get) (?:an? )?error\b"), 2),
        (_rx(r"\bworkaround\b", r"\brecommended approach\b"), 1),
    ],
    "reference": [
        (_rx(r"^\s*\|.*\|\s*$"), 2),                       # table rows
        (_rx(r"\bdefault:", r"\bdefault value\b", r"\btype:\s", r"\breturns?:\s", r"\braises?:\s"), 3),
        (_rx(r"\bparameters?\b", r"\barguments?\b", r"\boptions?\b", r"\bflags?\b",
             r"\battributes?\b", r"\bproperties\b"), 1),
        (_rx(r"^\s*[-*]?\s*`?--?[a-z][\w-]*`?[,:\s]"), 2),  # CLI flags in lists
        (_rx(r"\bmust not\b", r"\bmust be\b", r"\bis required\b", r"\bread-only\b",
             r"\bdeprecated\b", r"\bsince version\b"), 2),
        (_rx(r"\bsyntax\b", r"\bsignature\b", r"\bschema\b", r"\bexit code\b",
             r"\benvironment variable\b"), 2),
        (_rx(r"^\s*:\s+\S"), 2),                            # definition-list bodies
    ],
    "explanation": [
        (_rx(r"\bthe reason (?:for|why|that)\b", r"\bthis is because\b", r"\bwhich is why\b"), 3),
        (_rx(r"\bhistorically\b", r"\boriginally\b", r"\bdesign decision\b", r"\brationale\b"), 3),
        (_rx(r"\btrade-?offs?\b", r"\balternatively\b", r"\bthe alternative\b",
             r"\bcompared (?:to|with)\b", r"\bin contrast\b"), 2),
        (_rx(r"\bit (?:may|might) (?:be )?help(?:ful)? to think\b", r"\bconceptually\b",
             r"\byou can think of\b", r"\bunder the hood\b"), 2),
        (_rx(r"\bwhy\b"), 1),
        (_rx(r"\bsome users prefer\b", r"\bwe chose\b", r"\bwe decided\b", r"\bopinion\b"), 2),
        (_rx(r"\bit helps to understand\b", r"\bexists? because\b", r"\bearlier versions?\b",
             r"\bwas introduced\b", r"\bwhich meant\b", r"\bthe idea is\b",
             r"\bwhat this means\b", r"\bin practice\b", r"\bthink of (?:it|this) as\b"), 3),
        (_rx(r"\bbecause\b", r"\bhowever\b", r"\bwhereas\b", r"\bnevertheless\b"), 1),
    ],
}

# Title cues come in two kinds, and the distinction matters. An *anchored* cue describes the
# shape of the page ("How to…", "Understanding…") and is a strong mode signal. A *topic* cue is
# just a noun that happens to appear ("configuration", "API") and says almost nothing about
# mode — "Understanding the configuration model" is explanation, not reference. So topic cues
# are only consulted when no anchored cue matched.
TITLE_SHAPE: list[tuple[re.Pattern, str, int]] = [
    (_rx(r"^how to\b", r"^how do i\b"), "howto", 8),
    (_rx(r"^(?:about|understanding|why\b|concepts?|background|discussion|rationale)\b"),
     "explanation", 7),
    (_rx(r"^(?:tutorial|getting started|quick ?start|your first|build(?:ing)? your first)\b"),
     "tutorial", 6),
    (_rx(r"^(?:install(?:ing|ation)?|configur(?:e|ing)|deploy(?:ing)?|migrat(?:e|ing)|"
         r"upgrad(?:e|ing)|set(?:ting)? up|enabl(?:e|ing)|troubleshoot)\b"), "howto", 5),
]

TITLE_TOPIC: list[tuple[re.Pattern, str, int]] = [
    (_rx(r"\b(?:reference|api|cli|glossary|specification|schema|options|configuration|"
         r"settings|error codes|exit codes|parameters)\b"), "reference", 5),
    (_rx(r"\b(?:architecture|design|internals?|model)\b"), "explanation", 3),
]


def score_title(text: str, into: dict) -> None:
    """Add title cues to `into`. Shape cues win; topic cues only apply if no shape cue fired."""
    hit = False
    for pat, mode, weight in TITLE_SHAPE:
        if pat.search(text):
            into[mode] += weight
            hit = True
    if not hit:
        for pat, mode, weight in TITLE_TOPIC:
            if pat.search(text):
                into[mode] += weight

PATH_SIGNALS: list[tuple[re.Pattern, str, int]] = [
    (_rx(r"(^|/)tutorials?(/|$)"), "tutorial", 6),
    (_rx(r"(^|/)(how-?tos?|guides?|recipes?)(/|$)"), "howto", 5),
    (_rx(r"(^|/)(reference|api|apidocs?|cli|spec)(/|$)"), "reference", 6),
    (_rx(r"(^|/)(explanations?|concepts?|background|discussion|topics?|design)(/|$)"),
     "explanation", 6),
]

NON_PRACTITIONER = _rx(
    r"(^|/)(changelog|release[-_ ]?notes|contributing|code[-_ ]?of[-_ ]?conduct|license|"
    r"licence|security|governance|roadmap|adr|rfcs?|community|support|sponsors?)\b"
)

CODE_FENCE = re.compile(r"^(?:```|~~~)")
FRONT_MATTER = re.compile(r"^---\s*$")
MD_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RST_UNDERLINE = re.compile(r"^([=\-~^\"'`#*+_:.])\1{2,}\s*$")
ORDERED_ITEM = re.compile(r"^\s{0,3}\d+[.)]\s+\S")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
MYST_DOC_ROLE = re.compile(r"\{(?:doc|ref)\}`[^`<]*<?([^`>]+)>?`")
RST_TOCTREE_ENTRY = re.compile(r"^\s{2,}(\S+)\s*$")
IMPERATIVE_START = _rx(
    r"^\s*(?:run|open|click|type|create|add|edit|install|copy|paste|navigate|select|choose|"
    r"set|enter|save|start|stop|restart|execute|download|remove|delete|replace|check)\b"
)

SUFFIXES = (".md", ".markdown", ".mdx", ".rst", ".txt")
SKIP_DIRS = {"_build", "build", "site", "node_modules", ".git", ".tox", ".venv",
             "venv", "__pycache__", ".ipynb_checkpoints", "_static", "_templates"}


@dataclass
class Section:
    level: int
    title: str
    line: int
    words: int = 0
    scores: dict = field(default_factory=lambda: {m: 0 for m in MODES})

    @property
    def guess(self):
        """Winning mode, or None when there is no signal or the top score is tied.

        Returning None matters: a silent tie-break would label signal-free sections
        (a bare API signature, a code-only step) as whichever mode sorts first, and
        those false seams are exactly what erodes trust in the report."""
        top = max(self.scores.values())
        if top <= 0:
            return None
        winners = [m for m in MODES if self.scores[m] == top]
        return winners[0] if len(winners) == 1 else None


@dataclass
class Page:
    path: str
    title: str
    words: int
    headings: int
    code_blocks: int
    ordered_steps: int
    imperatives: int
    tables: int
    links_out: int
    scores: dict
    guess: str
    mix: float          # runner-up score / top score. 1.0 == perfectly ambiguous.
    mixed: bool
    runner_up: str
    non_practitioner: bool
    sections: list = field(default_factory=list)
    linked_from: int = 0

    @property
    def seams(self) -> list:
        """Substantial sections whose mode differs from the page's — SPLIT/EXTRACT targets."""
        return [s for s in self.sections
                if s.words >= 25 and s.guess is not None and s.guess != self.guess]


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def strip_front_matter(lines: list[str]) -> tuple[list[str], dict]:
    meta: dict = {}
    if lines and FRONT_MATTER.match(lines[0]):
        for i in range(1, len(lines)):
            if FRONT_MATTER.match(lines[i]):
                for raw in lines[1:i]:
                    if ":" in raw and not raw.lstrip().startswith("-"):
                        k, _, v = raw.partition(":")
                        meta[k.strip()] = v.strip().strip("\"'")
                return lines[i + 1:], meta
    return lines, meta


def score_line(line: str, bucket: dict) -> None:
    for mode, patterns in SIGNALS.items():
        for pat, weight in patterns:
            if pat.search(line):
                bucket[mode] += weight


def analyse(path: str, root: str) -> Page:
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    raw_lines = read_text(path).splitlines()
    lines, meta = strip_front_matter(raw_lines)

    scores = {m: 0 for m in MODES}
    # Content before the first heading is where instruction most often leaks into a
    # reference page, so it gets its own pseudo-section rather than being invisible.
    preamble = Section(level=1, title="(preamble, before first heading)", line=1)
    sections: list[Section] = [preamble]
    current: Section | None = preamble

    words = code_blocks = ordered_steps = imperatives = tables = 0
    headings = 0
    links: list[str] = []
    in_code = False
    title = meta.get("title", "")

    for idx, line in enumerate(lines):
        if CODE_FENCE.match(line.strip()):
            in_code = not in_code
            if in_code:
                code_blocks += 1
            continue
        if in_code:
            continue

        m = MD_HEADING.match(line)
        if not m and idx + 1 < len(lines) and line.strip() and RST_UNDERLINE.match(lines[idx + 1]):
            level = 1 if lines[idx + 1][0] in "=#*" else 2
            m = None
            heading_title = line.strip()
        elif m:
            level = len(m.group(1))
            heading_title = m.group(2).strip()
        else:
            heading_title = None

        if heading_title is not None:
            headings += 1
            if not title and level == 1:
                title = heading_title
            current = Section(level=level, title=heading_title, line=idx + 1)
            sections.append(current)
            # Heading text is a strong signal — weight it into its own section and the page.
            hb = {m_: 0 for m_ in MODES}
            score_line(heading_title, hb)
            for k in MODES:
                hb[k] *= 2
                scores[k] += hb[k]
                current.scores[k] += hb[k]
            tb = {m_: 0 for m_ in MODES}
            score_title(heading_title, tb)
            for k in MODES:
                scores[k] += tb[k]
                current.scores[k] += tb[k]
            continue

        n_words = len(line.split())
        words += n_words
        if current:
            current.words += n_words

        if line.strip().startswith("|") and line.count("|") >= 2:
            tables += 1
        if ORDERED_ITEM.match(line):
            ordered_steps += 1
        if IMPERATIVE_START.match(line) or IMPERATIVE_START.match(re.sub(r"^\s*[-*+]\s+", "", line)):
            imperatives += 1

        links.extend(MD_LINK.findall(line))
        links.extend(MYST_DOC_ROLE.findall(line))

        bucket = {m_: 0 for m_ in MODES}
        score_line(line, bucket)
        for k in MODES:
            scores[k] += bucket[k]
            if current:
                current.scores[k] += bucket[k]

    # Structural signals
    scores["howto"] += min(ordered_steps, 20) // 2
    scores["tutorial"] += min(imperatives, 30) // 3
    scores["reference"] += min(tables, 40) // 2

    if not title:
        title = os.path.splitext(os.path.basename(rel))[0].replace("-", " ").replace("_", " ")

    score_title(title, scores)
    for pat, mode, weight in PATH_SIGNALS:
        if pat.search(rel):
            scores[mode] += weight

    # Normalise by length so long pages don't dominate purely by word count.
    denom = max(words, 1) ** 0.5
    norm = {m: scores[m] / denom * 10 for m in MODES}
    ranked = sorted(MODES, key=lambda m: norm[m], reverse=True)
    top, second = ranked[0], ranked[1]
    # Mixedness: how close the runner-up gets to the winner. Directly interpretable —
    # 0.8 means the second-place mode scored 80% of the first, i.e. the page is doing
    # two jobs. Length-independent, unlike a margin over the total.
    mix = (norm[second] / norm[top]) if norm[top] > 0 else 0.0
    mixed = mix >= 0.55 and words >= 120
    if norm[top] <= 0:
        top = second = "unclear"

    return Page(
        path=rel,
        title=title,
        words=words,
        headings=headings,
        code_blocks=code_blocks,
        ordered_steps=ordered_steps,
        imperatives=imperatives,
        tables=tables,
        links_out=len(links),
        scores={m: round(norm[m], 2) for m in MODES},
        guess=top,
        mix=round(mix, 2),
        mixed=mixed,
        runner_up=second,
        non_practitioner=bool(NON_PRACTITIONER.search(rel)),
        sections=[s for s in sections if s.words >= 25],
    )


def walk(root: str) -> list[str]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(SUFFIXES):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def build_link_graph(pages: list[Page], root: str) -> None:
    index = {p.path: p for p in pages}
    stems = defaultdict(list)
    for p in pages:
        stems[os.path.splitext(p.path)[0]].append(p)
        stems[os.path.basename(os.path.splitext(p.path)[0])].append(p)

    for page in pages:
        full = os.path.join(root, page.path)
        text = read_text(full)
        targets = MD_LINK.findall(text) + MYST_DOC_ROLE.findall(text)
        for t in targets:
            t = t.split("#")[0].strip()
            if not t or t.startswith(("http://", "https://", "mailto:")):
                continue
            base = os.path.normpath(os.path.join(os.path.dirname(page.path), t)) if not t.startswith("/") \
                else t.lstrip("/")
            base = base.replace(os.sep, "/")
            hit = index.get(base)
            if hit is None:
                for cand in stems.get(os.path.splitext(base)[0], []) or \
                            stems.get(os.path.basename(os.path.splitext(base)[0]), []):
                    hit = cand
                    break
            if hit is not None and hit.path != page.path:
                hit.linked_from += 1


FACT_LINE = re.compile(r"^\s*(?:\||[-*]\s|:\s)")


def normalise_fact(line: str) -> str | None:
    """Reduce a table row or definition line to the *assertion* it makes, minus the name.

    Duplicated facts are what actually rot: a default restated on a second reference page
    drifts silently, and both copies look authoritative. Matching whole lines misses the
    common case, because the same fact is usually restated under a different key —
    `--log-level` in the CLI reference and `log.level` in the configuration reference carry
    identical type, default and value list. So for a table row we drop the first cell (the
    name) and compare what is asserted about it. That over-matches slightly on very generic
    rows, which is the right trade: a false positive costs one glance, a missed duplicate
    costs a contradiction six months from now.
    """
    t = re.sub(r"[`*_]", "", line.strip())
    if t.startswith("|"):
        cells = [c.strip() for c in t.strip("|").split("|")]
        if len(cells) >= 3:
            rest = [c for c in cells[1:] if c]
            if len(rest) < 2:
                return None
            t = " | ".join(rest)
        else:
            return None
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower() or None


def find_duplicate_facts(pages: list[Page], root: str, min_len: int = 25):
    """Table rows and definition lines asserted identically on more than one page."""
    sep = re.compile(r"^\s*\|[\s|:\-]+\|\s*$")
    seen: defaultdict[str, list] = defaultdict(list)
    for page in pages:
        with open(os.path.join(root, page.path), "r", encoding="utf-8",
                  errors="replace") as fh:
            lines = fh.read().splitlines()
        in_code = False
        for i, line in enumerate(lines, start=1):
            if CODE_FENCE.match(line.strip()):
                in_code = not in_code
                continue
            if in_code or not FACT_LINE.match(line):
                continue
            # A row followed by |---|---| is a header, not a fact. Every table on the site
            # shares its headers, so counting them buries the real duplicates in noise.
            if i < len(lines) and sep.match(lines[i]):
                continue
            if True:
                norm = normalise_fact(line)
                if norm is None or len(norm) < min_len or set(norm) <= set("-: |"):
                    continue
                if norm.startswith(("---", "===")):
                    continue
                seen[norm].append((page.path, i, line.strip()))
    return {k: v for k, v in seen.items()
            if len({p for p, _, _ in v}) > 1}


def render_md(pages: list[Page], root: str, show_sections: bool) -> str:
    out = io.StringIO()
    total = len(pages)
    orphans = [p for p in pages
               if p.linked_from == 0 and os.path.basename(p.path) not in ("index.md", "README.md")]
    dupes = defaultdict(list)
    for p in pages:
        dupes[p.title.strip().lower()].append(p.path)
    dupes = {k: v for k, v in dupes.items() if len(v) > 1 and k}

    counts = defaultdict(int)
    for p in pages:
        counts["non-practitioner" if p.non_practitioner else p.guess] += 1

    out.write(f"# Documentation inventory — `{root}`\n\n")
    out.write(f"{total} pages · {sum(p.words for p in pages):,} words\n\n")
    out.write("## Mode distribution (heuristic)\n\n")
    out.write("| Mode | Pages |\n|---|---|\n")
    for key in list(MODES) + ["non-practitioner"]:
        out.write(f"| {MODE_LABEL.get(key, key)} | {counts.get(key, 0)} |\n")
    out.write("\n")
    if counts.get("tutorial", 0) == 0:
        out.write("> **No page scores as a tutorial.** This is the most common gap in a doc set "
                  "and usually means real teaching material has to be written, not moved.\n\n")

    out.write("## Seams — sections that disagree with their page\n\n")
    out.write("**Start here.** Each row is a substantial section whose signals point at a "
              "different mode from the rest of its page. These are the EXTRACT, DRAIN and "
              "SPLIT candidates: the seams where two pieces of documentation have been fused "
              "together. Confirm each one with the compass before acting.\n\n")
    seam_pages = [p for p in pages if p.seams and not p.non_practitioner]
    if not seam_pages:
        out.write("_None detected. Either the doc set is unusually clean, or its pages are too "
                  "short for section-level signals — read them anyway._\n\n")
    else:
        out.write("| Page | Page reads as | Section | Line | Words | Section reads as |\n")
        out.write("|---|---|---|--:|--:|---|\n")
        for p in sorted(seam_pages, key=lambda x: -len(x.seams)):
            for s in p.seams:
                out.write(f"| `{p.path}` | {MODE_LABEL[p.guess]} | {s.title[:52]} | {s.line} | "
                          f"{s.words} | **{MODE_LABEL.get(s.guess, '—')}** |\n")
        out.write("\n")

    out.write("## All pages, ordered by how mixed they are\n\n")
    out.write("`mix` is the runner-up mode's score as a fraction of the winner's — 0.80 means "
              "the page is doing two jobs almost equally. The `reads as` column is a prompt for "
              "the compass, not a verdict; it counts words and cannot know what a user needs.\n\n")
    out.write("| Page | Title | Words | Reads as | Runner-up | mix | In-links | Code | Steps | Tables |\n")
    out.write("|---|---|--:|---|---|--:|--:|--:|--:|--:|\n")
    for p in sorted(pages, key=lambda x: (x.non_practitioner, -x.mix)):
        flag = " ⚠️" if p.mixed else ""
        guess = ("_n/a — not practitioner docs_" if p.non_practitioner
                 else MODE_LABEL.get(p.guess, "—"))
        runner = "" if p.non_practitioner else MODE_LABEL.get(p.runner_up, "—")
        mixcol = "" if p.non_practitioner else f"{p.mix:.2f}{flag}"
        out.write(f"| `{p.path}` | {p.title[:48]} | {p.words} | {guess} | {runner} | "
                  f"{mixcol} | {p.linked_from} | {p.code_blocks} | "
                  f"{p.ordered_steps} | {p.tables} |\n")
    out.write("\n")

    if orphans:
        out.write("## Pages nothing links to\n\n")
        out.write("Either genuinely unreachable, or reachable only through nav config. Worth "
                  "checking whether they are still wanted before you spend effort moving them.\n\n")
        for p in orphans:
            out.write(f"- `{p.path}` ({p.words} words)\n")
        out.write("\n")

    dup_facts = find_duplicate_facts(pages, root)
    if dup_facts:
        out.write("## Facts asserted on more than one page\n\n")
        out.write("Each entry below asserts the same thing — same type, same default, same "
                  "description — on two or more pages, even where the key it hangs off differs "
                  "(`--log-level` in a CLI reference and `log.level` in a config reference are "
                  "one fact, not two). Atomic facts belong in exactly one table, with every "
                  "other mention linking to it; duplicated copies drift apart and both look "
                  "authoritative. Pick the canonical home and LINK from the rest. Skim for "
                  "false positives — generic rows can collide harmlessly.\n\n")
        for norm, hits in sorted(dup_facts.items(), key=lambda kv: -len(kv[1]))[:40]:
            pages_hit = ", ".join(sorted({f"`{p}`:{i}" for p, i, _ in hits}))
            out.write(f"- `{hits[0][2][:90]}`\n  — {pages_hit}\n")
        out.write("\n")

    if dupes:
        out.write("## Duplicate titles\n\n")
        out.write("The same content may exist in more than one place — a LINK or MERGE candidate.\n\n")
        for title, paths in sorted(dupes.items()):
            out.write(f"- **{title}** — {', '.join('`' + x + '`' for x in paths)}\n")
        out.write("\n")

    if show_sections:
        candidates = [p for p in pages if not p.non_practitioner and len(p.sections) > 1]
        if candidates:
            out.write("## Full section breakdown\n\n")
            out.write("Apply the compass heading by heading. `⟵` marks a section that disagrees "
                      "with its page.\n\n")
            for p in sorted(candidates, key=lambda x: -x.mix):
                out.write(f"### `{p.path}` — page reads as {MODE_LABEL.get(p.guess, '—')} "
                          f"(mix {p.mix:.2f})\n\n")
                out.write("| Line | Heading | Words | Reads as |\n|--:|---|--:|---|\n")
                for s in p.sections:
                    mark = (" ⟵" if s.guess is not None and s.guess != p.guess
                            and s.words >= 25 else "")
                    indent = "&nbsp;&nbsp;" * (s.level - 1)
                    out.write(f"| {s.line} | {indent}{s.title[:56]} | {s.words} | "
                              f"{MODE_LABEL.get(s.guess, '—')}{mark} |\n")
                out.write("\n")

    out.write("---\n\nNext: read the flagged pages and fill in the migration map "
              "(`assets/audit-template.md`).\n")
    return out.getvalue()


def render_csv(pages: list[Page]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["path", "title", "words", "guess", "runner_up", "mix", "mixed",
                "linked_from", "code_blocks", "ordered_steps", "imperatives", "tables",
                "links_out", "non_practitioner",
                *[f"score_{m}" for m in MODES]])
    for p in sorted(pages, key=lambda x: -x.mix):
        w.writerow([p.path, p.title, p.words, p.guess, p.runner_up, p.mix, p.mixed,
                    p.linked_from, p.code_blocks, p.ordered_steps, p.imperatives, p.tables,
                    p.links_out, p.non_practitioner, *[p.scores[m] for m in MODES]])
    return buf.getvalue()


def render_json(pages: list[Page]) -> str:
    payload = []
    for p in pages:
        d = asdict(p)
        d["sections"] = [{"title": s.title, "level": s.level, "line": s.line,
                          "words": s.words, "guess": s.guess} for s in p.sections]
        payload.append(d)
    return json.dumps(payload, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="documentation root directory")
    ap.add_argument("--format", choices=("md", "csv", "json"), default="md")
    ap.add_argument("--out", help="write here instead of stdout")
    ap.add_argument("--sections", action="store_true", default=True,
                    help="include per-heading breakdown for mixed pages (default: on)")
    ap.add_argument("--no-sections", dest="sections", action="store_false")
    ap.add_argument("--min-words", type=int, default=0, help="ignore pages shorter than this")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"error: {args.root} is not a directory", file=sys.stderr)
        return 2

    paths = walk(root)
    if not paths:
        print(f"error: no documentation files found under {args.root}", file=sys.stderr)
        return 1

    pages = [analyse(p, root) for p in paths]
    pages = [p for p in pages if p.words >= args.min_words]
    build_link_graph(pages, root)

    if args.format == "md":
        text = render_md(pages, os.path.relpath(root), args.sections)
    elif args.format == "csv":
        text = render_csv(pages)
    else:
        text = render_json(pages)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.out} ({len(pages)} pages)", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
