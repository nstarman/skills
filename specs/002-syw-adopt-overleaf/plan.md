# Implementation Plan: syw-adopt-overleaf — move an existing Overleaf paper into showyourwork

**Branch**: `syw-adopt-overleaf` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-syw-adopt-overleaf/spec.md`; agreed design in
[design.md](design.md).

## Summary

Add a local skill, `syw-adopt-overleaf`: a phased runbook (survey → backup → freeze → build the
layout → build and compare → new repository → rename and first sync → prune → hand off) with ⛔
gates, plus four small scripts for the parts that must be exact — `backup.sh`, `pdf_diff.py`,
`check_lists.py`, `public_check.sh`. Ship in the same change the recursive figure check in
`syw-overleaf-dropbox/scripts/check_build.sh`. Research ([research.md](research.md)) settled the
open point from the review: SYW has no dry run, but syncs only on branch `main`, so the dry run is
done on another branch with a separate Overleaf clone (R1); and `showyourwork setup --overleaf` is
never used on an existing project (R2).

## Technical Context

**Language/Version**: Python ≥ 3.11 (standard library only), POSIX sh / Bash.

**Primary Dependencies**: `git`, `gh`, `op` (1Password CLI), poppler (`pdftotext`, `pdftoppm`,
`pdfinfo`); showyourwork dev (`showyourwork-main` env, 44d15103f) during a migration only.

**Storage**: files — the backup folder, `inventory.tsv`, `MIGRATION.md` (data-model.md).

**Testing**: `python -m unittest discover tests`; PDF tests skip without poppler; CI installs
`poppler-utils`.

**Target Platform**: macOS (the author's machine: Dropbox mirror, 1Password); CI on ubuntu for the
tests.

**Project Type**: an agent skill (Markdown runbook + scripts) in a content repository.

**Performance Goals**: `pdf_diff.py` on a 40-page paper in under a minute.

**Constraints**: no token in any argv, file or log (R3); pre-arXiv content private; signing never
bypassed; every irreversible step gated.

**Scale/Scope**: one paper at a time; CP1 first, CP2-like papers next.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. One source per skill | New local folder `syw-adopt-overleaf/`; unique name | ✅ |
| II. Generated outputs never hand-edited | `build_index.py` regenerates `index.json`, marketplace, README | ✅ |
| III. Validated against the source | `SKILL.md` name = folder; description ≤ 1024 characters | ✅ |
| IV. Installable three ways | Local skill, so marketplace, zip and folder come for free | ✅ |
| V. `index.json` is a public contract | One entry added; schema unchanged | ✅ |
| VI. Small and dependency-free | stdlib Python and sh; poppler is called as a tool, installed in CI by apt; no new secrets | ✅ |
| VII. Published skills only | Meant for others with SYW + Overleaf papers | ✅ |

Post-design re-check: all ✅.

## Project Structure

### Documentation (this feature)

```text
specs/002-syw-adopt-overleaf/
├── design.md  spec.md  plan.md  research.md  data-model.md  quickstart.md
├── contracts/scripts.md     command lines and outputs of the four scripts + check_build change
├── checklists/requirements.md
└── tasks.md                 (Phase 2)
```

### Source Code (repository root)

```text
syw-adopt-overleaf/
├── SKILL.md                 the phased runbook, gates, hard rules, hand-off
├── card.json
├── references/
│   ├── mapping.md           four classes, rules, CP1 worked example
│   ├── rollback.md          restore commands per phase
│   ├── lessons.md           CP2 lessons (R9) and later migrations
│   └── migration-template.md  MIGRATION.md skeleton (data-model.md)
└── scripts/
    ├── backup.sh  pdf_diff.py  check_lists.py  public_check.sh
syw-overleaf-dropbox/scripts/check_build.sh   recursive figures
tests/
├── pdfgen.py                tiny stdlib PDF writer for the tests
├── test_pdf_diff.py  test_check_lists.py  test_check_build.py  test_public_check.py
.github/workflows/check.yml  + apt install poppler-utils
index.json  .claude-plugin/marketplace.json  README.md   regenerated
```

**Structure Decision**: same shape as `syw-overleaf-dropbox` (runbook + `references/` +
`scripts/`). `migration-template.md` is added to design.md's layout so `MIGRATION.md` has a fixed
shape the gates can be checked against. Tests live in the repository's `tests/` and import the
skill's scripts by path, as the existing tests import `scripts/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| (none) | | |
