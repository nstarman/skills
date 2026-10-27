---

description: "Task list for syw-adopt-overleaf"
---

# Tasks: syw-adopt-overleaf — move an existing Overleaf paper into showyourwork

**Input**: Design documents from `/specs/002-syw-adopt-overleaf/`

**Prerequisites**: plan.md, spec.md, design.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: included for the exact parts (FR-013, SC-006). Within a phase, test tasks come first
and must fail before the implementation that makes them pass.

**Organization**: by user story (spec.md). US3 (the runbook) is validated by the CP1 migration
itself, which runs after this change merges.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US6 from spec.md

## Reference material for every task

- Command lines and outputs: `specs/002-syw-adopt-overleaf/contracts/scripts.md`
- Formats (backup folder, inventory, MIGRATION.md): `specs/002-syw-adopt-overleaf/data-model.md`
- Decisions: `specs/002-syw-adopt-overleaf/research.md` (R1 dry run, R2 no `setup --overleaf`,
  R3 credential helper, R4 list rules, R5 diff method, R6 public check, R7 baseline, R8 tests)
- Rules: `.specify/memory/constitution.md` (stdlib only; no new secrets)

---

## Phase 1: Setup

- [X] T001 Create `syw-adopt-overleaf/` with `card.json` and empty `references/`, `scripts/`
- [X] T002 [P] Add `tests/pdfgen.py`: a stdlib writer for one- or multi-page PDFs with given text lines per page and an optional filled rectangle (research R8)
- [X] T003 [P] Add a step installing `poppler-utils` (apt) before the unit tests in `.github/workflows/check.yml`

---

## Phase 2: User Story 1 — Back up everything first (P1)

**Goal**: a verified five-part backup outside Dropbox/iCloud, no token anywhere.

**Independent Test**: quickstart step 4 (scratch repository and mirror; fails at `overleaf` without
access, nothing else changed).

- [X] T004 [US1] Write `syw-adopt-overleaf/scripts/backup.sh` per contracts/scripts.md: argument parsing, destination checks (must not exist, not under `~/Library/CloudStorage` or `~/Library/Mobile Documents`), bundle + verify, tar + list check, Overleaf clone via credential helper (R3) + `git fsck` + no-secret check of `.git/config`, baseline copy + `pdfinfo`, `gh secret list` names to `secrets.txt`; `ok`/`FAILED` lines
- [X] T005 [US1] Run quickstart step 4 against scratch data and record the output in the PR description

---

## Phase 3: User Story 2 — Show every PDF difference (P2)

**Goal**: `pdf_diff.py` reports pages, numbers, text and images; exit 0 only when identical.

**Independent Test**: `tests/test_pdf_diff.py`.

- [X] T006 [P] [US2] Write `tests/test_pdf_diff.py`: identical → 0; `0.43`→`0.44` → 1 and `0.43 → 0.44` in output; extra page → 1 and page counts in output; changed rectangle → 1, page flagged, both PNGs written with `--out`; skip when `pdftotext` missing
- [X] T007 [US2] Write `syw-adopt-overleaf/scripts/pdf_diff.py` per research R5 until T006 passes

---

## Phase 4: User Story 4 — Never push to Overleaf by accident (P4)

**Goal**: list check that fails on overlap, authored-text pushes and class-4 entries.

**Independent Test**: `tests/test_check_lists.py`.

- [X] T008 [P] [US4] Write `tests/test_check_lists.py`: clean CP2-shaped lists → 0; same path in both → 1; `src/tex` folder pushed covering `ms.tex` → 1; folder in push covering a pulled file → 1; class-4 path pulled → 1; `showyourwork.yml` with other sections parsed correctly
- [X] T009 [US4] Write `syw-adopt-overleaf/scripts/check_lists.py` per research R4 until T008 passes

---

## Phase 5: User Story 5 — Figures in subfolders (P5)

**Goal**: `check_build.sh` compares every figure under `src/tex/figures`, recursively.

**Independent Test**: `tests/test_check_build.py`.

- [X] T010 [P] [US5] Write `tests/test_check_build.py`: temp repo with `src/tex/figures/GD1/a.pdf` and `src/tex/figures/b.pdf`, mirror with only `figures/b.pdf` → output has `figure GD1/a.pdf: ABSENT` and `figure b.pdf: same`
- [X] T011 [US5] Change `syw-overleaf-dropbox/scripts/check_build.sh` to `find` figures recursively and compare by relative path until T010 passes

---

## Phase 6: User Story 6 — Check before going public (P6)

**Goal**: `public_check.sh` fails on shared commits, token-like strings, class-4 paths.

**Independent Test**: `tests/test_public_check.py`.

- [X] T012 [P] [US6] Write `tests/test_public_check.py`: old repo → bundle; new repo cloned from it → `FAIL shared commits`; fresh repo → 0; fresh repo with an `olp_…` string in one commit → fail naming commit and path, not the string; fresh repo that once committed a class-4 path → fail
- [X] T013 [US6] Write `syw-adopt-overleaf/scripts/public_check.sh` per research R6 until T012 passes

---

## Phase 7: User Story 3 — The runbook (P3)

**Goal**: the skill an agent follows to migrate a paper.

**Independent Test**: the CP1 migration (after merge), SC-001 to SC-005.

- [X] T014 [US3] Write `syw-adopt-overleaf/SKILL.md`: frontmatter (description ≤ 1024 characters), when to use, hard rules (no `setup --overleaf`, R2; signing; tokens; private; the author's own actions), phases 0–8 with ⛔ gates and the scripts each uses, the dry run on a non-`main` branch (R1), the baseline compiled outside the mirror (R7), hand-off to `syw-overleaf-dropbox` and `syw-site init`
- [X] T015 [P] [US3] Write `syw-adopt-overleaf/references/mapping.md`: the four classes, rules, inventory format, CP1 worked example
- [X] T016 [P] [US3] Write `syw-adopt-overleaf/references/rollback.md`: exact restore commands per phase
- [X] T017 [P] [US3] Write `syw-adopt-overleaf/references/lessons.md`: CP2 lessons (research R9)
- [X] T018 [P] [US3] Write `syw-adopt-overleaf/references/migration-template.md` (data-model.md sections)

---

## Phase 8: Polish

- [X] T019 Run `python scripts/build_index.py` and commit `index.json`, `.claude-plugin/marketplace.json`, `README.md`
- [X] T020 Run `python -m unittest discover tests` and `python scripts/build_index.py --check`; both pass
- [ ] T021 Mark this file's tasks done; open the pull request (squash merge)

---

## Dependencies

- T001 before everything in `syw-adopt-overleaf/`; T002 before T006 (T010 needs no real PDFs).
- Each story's test before its implementation (T006→T007, T008→T009, T010→T011, T012→T013).
- T014 after T004, T007, T009, T013 (it names their exact usage).
- T019–T021 last.

## Parallel examples

- After T001–T003: T006, T008, T010, T012 together (separate test files).
- T015–T018 together after T014's outline is fixed.

## Implementation strategy

MVP = US1 + US2 (backup and diff are what make the migration safe). Then US4, US5, US6, then the
runbook that ties them together. The runbook's real test is CP1, run in this session after the
pull request merges.
