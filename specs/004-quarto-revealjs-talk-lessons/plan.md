# Implementation Plan: quarto-revealjs — lessons from a real talk

**Branch**: `claude/quizzical-shamir-010e53` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-quarto-revealjs-talk-lessons/spec.md`, folded into
the area specification `/specs/003-quarto-revealjs/spec.md` when implemented.

## Summary

Generalise what a 45-slide talk built without the skill had to work out, and correct one wrong
claim. New assets: `inline_apps.py` (background-iframe and iframe apps as `blob:` URLs from base64
in the deck, `<object>` files as `data:` URIs, `--strip-notes` for the shared copy),
`check_overflow.py`, `bibliography.py` (Zotero collection → bibliography list),
`_extensions/paper/` (citation shortcode with its CSS), `_deck/skip-steps.html` ("]" key),
`_quarto-share.yml` (share profile) and `.gitignore`. Changed: `check_offline.py` and `make_pdf.py`
launch headless, prefer Chrome, fall back to bundled Chromium; the two checks take `--webkit`.
`SKILL.md` gains the wider description, deck hygiene, the share build, the overflow check and the
no-visible-browser rule; the guide corrects background iframes and adds Safari/WebKit and
layout-stable animation sections; new `references/style.md` holds the author's conventions. The
end-to-end test gains a fixture deck and steps for each; stdlib scripts get unit tests.

## Technical Context

**Language/Version**: Markdown; Python 3.11+ (stdlib for `inline_apps.py`, `bibliography.py`;
Playwright for the browser checks); Lua (Quarto shortcode); HTML/CSS/JS.

**Primary Dependencies**: Quarto (verified 1.11.9), Playwright (Chromium and WebKit), Zotero's local
API (`http://localhost:23119/api/`, Zotero 7) for `bibliography.py` only.

**Storage**: files only.

**Testing**: `python -m unittest discover tests` (new `tests/test_quarto_revealjs.py`, stub Zotero API
through a patched `urlopen`); `tests/skills/quarto-revealjs/run.sh` end to end.

**Target Platform**: decks for current Chromium and Safari; tests on macOS and ubuntu-latest.

**Project Type**: agent skill (Markdown + templates) with an end-to-end test.

**Performance Goals**: the end-to-end test stays under 10 minutes on a runner.

**Constraints**: public repository: no paper names, collection IDs, people or paths from the talk;
no visible browser window anywhere (scripts are headless).

**Scale/Scope**: one skill, about ten files changed or added.

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I. One source per skill | Existing local folder; no copies | ✅ |
| II. Generated outputs never hand-edited | Description change → `build_index.py` regenerates | ✅ |
| III. Validated against the source | Description stays ≤ 1024 characters | ✅ |
| IV. Installable three ways | Unchanged | ✅ |
| V. `index.json` contract | Description text only; schema unchanged | ✅ |
| VI. Small and dependency-free | New asset scripts run in the user's deck folder; the two stdlib ones are unit-tested with stdlib; Playwright WebKit is installed only by the skill's own workflow (exception) | ✅ |
| VII. Published skills only | Unchanged | ✅ |

Post-design re-check: all ✅. No complexity tracking needed.

## Project Structure

```text
quarto-revealjs/
├── SKILL.md                         # description, setup + hygiene, share build, checks, rule
├── references/quarto-revealjs-guide.md   # background-iframe fix, Safari, animation patterns
├── references/style.md              # new: the author's talk conventions
└── assets/
    ├── _quarto.yml                  # + include-after-body skip-steps
    ├── _quarto-share.yml            # new: share profile
    ├── .gitignore                   # new
    ├── _deck/skip-steps.html        # new
    ├── _extensions/paper/           # new: _extension.yml, paper.lua, paper.css
    ├── inline_apps.py, check_overflow.py, bibliography.py   # new
    └── check_offline.py, make_pdf.py                        # headless + fallback (+ --webkit)
tests/
├── test_quarto_revealjs.py          # new: inline_apps, bibliography
└── skills/quarto-revealjs/          # run.sh steps; fixture/lessons.qmd, apps/background.html
.github/workflows/test-quarto-revealjs.yml   # install Playwright Chromium + WebKit
```

## Complexity Tracking

None.
