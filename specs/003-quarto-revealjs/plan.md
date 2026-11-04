# Implementation Plan: quarto-revealjs — offline, archivable reveal.js decks with Quarto

**Branch**: `add-quarto-revealjs` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-quarto-revealjs/spec.md`. Written after the
implementation (pull request #25) to record it; the decisions and the evidence for them are in
[research.md](research.md).

## Summary

Add a local skill, `quarto-revealjs`: `SKILL.md` (setup, syntax cheat sheet, embedding apps,
checking, gotchas), `references/quarto-revealjs-guide.md` (every revealjs.com feature page with
Quarto syntax and tested status), `assets/` (deck-folder templates and two Playwright helpers),
`versions.json` and `UPDATING.md`. Add an end-to-end test under `tests/skills/quarto-revealjs/`
with its own weekly workflow, which compares a 46-check feature table with the guide in both
directions, checks the documented gotchas, and opens an issue on a scheduled failure or version
drift. Amend constitution principle VI (1.2.0) so such a test may install the tools its skill is
about.

## Technical Context

**Language/Version**: Markdown; Bash; Python 3.11+ (stdlib for `versions_check.py`; Playwright for
the browser checks); HTML/CSS/JS for the deck header.

**Primary Dependencies**: Quarto (latest release in CI; verified 1.11.9, bundling reveal.js 5.1.0),
MathJax 3.2.2 (`tex-svg-full.js`), plotly.py (verified 7.1.0), Playwright with Google Chrome,
ffmpeg (test media).

**Storage**: files only.

**Testing**: `tests/skills/quarto-revealjs/run.sh` (local and CI); repository unit tests unchanged.

**Target Platform**: decks for current Chromium browsers; tests on macOS (author) and ubuntu-latest
(CI, Chrome preinstalled).

**Project Type**: an agent skill (Markdown + templates) with an end-to-end test.

**Performance Goals**: the test finishes in under 10 minutes on a GitHub runner (about 4 observed).

**Constraints**: public repository (no personal data; the fixture app is a stand-in); the release
zip must not grow by vendored libraries (MathJax and plotly.js are fetched, not committed); test
media generated at run time.

**Scale/Scope**: one skill; one weekly workflow.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. One source per skill | New local folder `quarto-revealjs/`; unique name | ✅ |
| II. Generated outputs never hand-edited | `build_index.py` regenerates `index.json`, marketplace, README | ✅ |
| III. Validated against the source | `SKILL.md` name = folder; description 588 characters (≤ 1024) | ✅ |
| IV. Installable three ways | Local skill: marketplace, zip and folder come for free | ✅ |
| V. `index.json` is a public contract | One entry added; schema unchanged | ✅ |
| VI. Small and dependency-free | `scripts/` untouched; Playwright helpers are templates in `assets/`, run in the user's deck project; the end-to-end test installs Quarto, Playwright, Chrome and ffmpeg under the 1.2.0 exception; workflow uses only `GITHUB_TOKEN` | ✅ (after amendment, see Complexity Tracking) |
| VII. Published skills only | Meant for anyone making Quarto talks | ✅ |

Post-design re-check: all ✅.

## Project Structure

### Documentation (this feature)

```text
specs/003-quarto-revealjs/
├── spec.md  plan.md  research.md  tasks.md
└── checklists/requirements.md
```

No data-model.md or contracts/: the skill has no data model, and its only interfaces are the
command lines documented in `SKILL.md` and at the top of each test script.

### Source Code (repository root)

```text
quarto-revealjs/
├── SKILL.md  card.json  versions.json  UPDATING.md
├── references/quarto-revealjs-guide.md
└── assets/
    ├── _quarto.yml
    ├── _deck/header.html  _deck/setup.qmd
    └── make_pdf.py  check_offline.py
tests/skills/quarto-revealjs/
├── run.sh  versions_check.py  feature_check.py
└── fixture/
    ├── demo.qmd  reveal-features.qmd
    ├── apps/explorer.html            stand-in interactive app (no paper data)
    ├── _extensions/ping/             minimal reveal.js plugin as a Quarto extension
    └── gotchas/katex.qmd  gotchas/chalkboard.qmd
.github/workflows/test-quarto-revealjs.yml
.specify/memory/constitution.md       VI amended, 1.2.0
AGENTS.md                             "End-to-end tests of a skill"
index.json  .claude-plugin/marketplace.json  README.md   regenerated
```

**Structure Decision**: the skill follows the repository's local-skill shape (`SKILL.md`,
`references/`, `assets/`). Its browser helpers live in `assets/` as templates the user copies into
a deck folder, not in `scripts/`, so the skill ships no runtime dependency. The behaviour test
lives outside the skill folder (`tests/skills/`) so the release zip carries no fixtures.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Test installs Quarto, Playwright, Chrome, ffmpeg (principle VI as of 1.1.0) | The skill's claims are about browser behaviour of Quarto output; only rendering and driving a browser verifies them | Unit tests of the templates' text cannot detect a CDN request, a broken fragment or a changed Quarto default. Resolved by amending VI (1.2.0) to allow per-skill end-to-end tests, scoped so `scripts/`, the index and the zips stay dependency-free. |
