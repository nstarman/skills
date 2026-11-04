---

description: "Task list for quarto-revealjs"
---

# Tasks: quarto-revealjs — offline, archivable reveal.js decks with Quarto

**Input**: Design documents from `/specs/003-quarto-revealjs/`

**Prerequisites**: plan.md, spec.md, research.md

**Tests**: the end-to-end test (FR-007, SC-001–SC-003) is part of the feature.

**Organization**: by user story (spec.md). Recorded after implementation (pull request #25); all
tasks are done.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md

---

## Phase 1: Setup

- [X] T001 Create `quarto-revealjs/` with `card.json` and `versions.json` (Quarto 1.11.9, reveal.js 5.1.0, MathJax 3.2.2, plotly 7.1.0)
- [X] T002 [P] Add `tests/skills/quarto-revealjs/` with `fixture/` (stand-in app, ping plugin)

## Phase 2: User Story 1 — A deck that works offline (P1)

- [X] T003 [US1] `assets/_quarto.yml`: `embed-resources`, math plugin URL `about:blank`, header include, `_output/`
- [X] T004 [US1] `assets/_deck/header.html`: MathJax 3.2.2 full SVG build and plotly.js loaded once from `_vendor/` (research R2)
- [X] T005 [P] [US1] `assets/_deck/setup.qmd`: plotly renderer emitting bare divs
- [X] T006 [US1] `assets/check_offline.py`: network requests, missing local files, page errors, raw TeX
- [X] T007 [US1] `SKILL.md` setup steps with fetch commands; "why each piece exists"

## Phase 3: User Story 2 — PDF of what was shown (P2)

- [X] T008 [US2] `assets/make_pdf.py`: `?print-pdf&showNotes=separate-page`, reveal.js page size, network blocked
- [X] T009 [US2] `.print-only` / `.print-hide` in the header; stills for live content (research R4, R5)

## Phase 4: User Story 3 — The feature guide (P3)

- [X] T010 [US3] `references/quarto-revealjs-guide.md`: table for every revealjs.com page, sections, gotchas (research R6)
- [X] T011 [US3] `fixture/reveal-features.qmd` and `feature_check.py` exercising every row; `EXPECTED_FAIL` mirrors the ✗ rows

## Phase 5: User Story 4 — Embedded apps (P4)

- [X] T012 [US4] Header: fragments in equations (`Reveal.sync`), iframe keyboard hand-back (research R3, R5)
- [X] T013 [US4] `SKILL.md` and guide: inline and background embedding, theme pinning, print stills
- [X] T014 [P] [US4] Checks: app draws inline and as background, theme under system dark mode, keyboard after a click

## Phase 6: User Story 5 — Upstream changes (P5)

- [X] T015 [US5] `versions_check.py`: bundled reveal.js change fails; Quarto/plotly drift warns and sets `drift`
- [X] T016 [US5] `run.sh`: folder from assets, render, offline, PDF (6 pages + still), feature table, gotchas (`fixture/gotchas/`)
- [X] T017 [US5] `.github/workflows/test-quarto-revealjs.yml`: weekly latest Quarto, PRs, manual tag; read-only test job; `remind` job opens an issue on failure or drift
- [X] T018 [US5] `UPDATING.md`: what signals an update and what to change for each kind of failure

## Phase 7: Polish

- [X] T019 Constitution 1.2.0 (VI exception for per-skill end-to-end tests); `AGENTS.md` section
- [X] T020 `build_index.py`, unit tests, `personal_check.py`, `claude plugin validate .`
- [X] T021 Independent audit (tests and content) and fixes (research R8)
- [X] T022 First CI run on ubuntu: zoom modifier is Ctrl on Linux; guide and check updated

## Dependencies

Phase 1 → Phases 2–5 (US1 before US2–US4, which use its header) → Phase 6 (tests the rest) → Phase 7.
