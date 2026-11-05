# Tasks: quarto-revealjs — lessons from a real talk

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[contracts/scripts.md](contracts/scripts.md). Tests are requested (FR-110).

## Phase 1: Setup

- [X] T001 Add the fixture deck `tests/skills/quarto-revealjs/fixture/lessons.qmd` (math slide with long notes, SVG figure, `<object data>` SVG, citation slide inline + corner, build-up slide, clipped 2× app, background-iframe app `apps/background.html`, slide `#too-long` that overflows), `fixture/apps/background.html`, `fixture/media/header.svg`

## Phase 2: Foundational

- [X] T002 Browser launch: headless, `channel="chrome"` with fallback to bundled Chromium, `--webkit` in `quarto-revealjs/assets/check_offline.py`; headless + fallback in `quarto-revealjs/assets/make_pdf.py` and `tests/skills/quarto-revealjs/feature_check.py`

## Phase 3: US1 — Start every talk from the skill (P1)

- [X] T003 [US1] Widen the description and add deck hygiene (git init, `.gitignore`, prune figures) and the no-visible-browser rule in `quarto-revealjs/SKILL.md`; add `quarto-revealjs/assets/.gitignore`
- [X] T004 [P] [US1] Write `quarto-revealjs/references/style.md` (the author's conventions) and point to it from `SKILL.md`

## Phase 4: US2 — One file really is one file (P1)

- [X] T005 [US2] Unit tests for inlining in `tests/test_quarto_revealjs.py` (background iframe, iframe src/data-src, object → data URI, missing file reported, `--strip-notes`, loader placed before `Reveal.initialize`)
- [X] T006 [US2] Implement `quarto-revealjs/assets/inline_apps.py` per contracts/scripts.md
- [X] T007 [US2] Add `quarto-revealjs/assets/_quarto-share.yml` (output `_share`); document the share build and front-matter precedence in `SKILL.md`; correct the background-iframe rows and packaging section in `quarto-revealjs/references/quarto-revealjs-guide.md`
- [X] T008 [US2] `run.sh`: inline `lessons.html`, copy alone to an empty folder, offline check; share build has no notes, archive build keeps them

## Phase 5: US3 — Nothing spills off a slide (P2)

- [X] T009 [US3] Implement `quarto-revealjs/assets/check_overflow.py` (skips per research R4; `--webkit`)
- [X] T010 [US3] `run.sh`: overflow check flags exactly `#too-long` in `lessons.html` and nothing in `demo.html`; document in `SKILL.md`

## Phase 6: US4 + US7 — Safari, headless only (P2)

- [X] T011 [US4] Safari/WebKit section in the guide (CSS `d: path()` + SMIL fallback, data-URI masks with both properties)
- [X] T012 [US4] `run.sh`: offline and overflow checks with `--webkit`; workflow installs Playwright Chromium + WebKit in `.github/workflows/test-quarto-revealjs.yml`

## Phase 7: US5 — Animations that do not jump (P3)

- [X] T013 [P] [US5] Add `quarto-revealjs/assets/_deck/skip-steps.html`, include it from `assets/_quarto.yml`; layout-stable animation section in the guide
- [X] T014 [US5] `tests/skills/quarto-revealjs/lessons_check.py`: "]" jumps to the last fragment, then the next slide

## Phase 8: US6 — Citations and a bibliography slide (P3)

- [X] T015 [US6] Unit tests for `bibliography.py` in `tests/test_quarto_revealjs.py` (labels, `a`/`b` suffixes, arXiv-DOI fallback, attachments skipped, paging)
- [X] T016 [US6] Implement `quarto-revealjs/assets/bibliography.py` and `quarto-revealjs/assets/_extensions/paper/` (`_extension.yml`, `paper.lua`, `paper.css`)
- [X] T017 [US6] `lessons_check.py`: rendered `lessons.html` has the citation link and corner icon; document in `SKILL.md`

## Phase 9: Polish

- [X] T018 Fold spec into `specs/003-quarto-revealjs/spec.md`; update `quarto-revealjs/UPDATING.md` for the added checks
- [X] T019 `python scripts/build_index.py`, `python -m unittest discover tests`, `python scripts/personal_check.py`, full `run.sh`

## Phase 10: Audit fixes (independent review of the pull request)

- [X] T020 `inline_apps.py`: skip a deck that is already inlined (no duplicate apps on a second run); `--strip-notes` removes notes with extra classes; look up `%`-encoded paths and drop `?query`/`#hash`; unit tests for each
- [X] T021 `run.sh`: WebKit offline check on the inlined deck and the share build; share build checked offline (app inlined)
- [X] T022 Guide and `SKILL.md`: mark claims the test does not exercise as observed (print of live apps, Safari path animation and masks, `data:` iframe blank, "]" in the help overlay)

- [X] T023 Merge-readiness audit nits: `inline_apps.py` keeps each app's file type and takes `--root`; `bibliography.py` warns on an item with no DOI or URL; `UPDATING.md` says to copy `_deck/` with `_quarto.yml`; the guide's SMIL fallback is labelled a sketch; `style.md` applies only to the author's own talks

## Dependencies

T001 → T008/T010/T012/T014/T017; T002 → T009/T012; T005 → T006; T015 → T016. US1, US5 and US6
docs are independent of each other.

## Implementation strategy

US1 + US2 first (wrong claim and triggering); then checks (US3, US4/US7); then patterns and
citations.
