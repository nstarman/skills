# Implementation Plan: skills registry — nstarman/skills as the central clearinghouse

**Branch**: `001-skills-registry` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-skills-registry/spec.md`; agreed design in
[design.md](design.md).

## Summary

Add a registry for skills held in other repositories, and generate from it and the local skill
folders an `index.json` (the website's contract), a Claude Code marketplace and the README's skill
table. CI validates every skill where its files live and keeps generated files fresh; a release
workflow publishes claude.ai zips only when they change; a weekly job proposes newer tags for pinned
entries. The website's collector then reads `index.json` (separate pull request, after this ships).
Research ([research.md](research.md)) settled the one open question: each plugin's source is the
skill folder itself with `"skills": ["./"]`, verified by installing local and external skills.

## Technical Context

**Language/Version**: Python ≥ 3.11, standard library only; Bash in workflows.

**Primary Dependencies**: none at runtime; `git` and `gh` (preinstalled on GitHub runners); Claude
Code CLI (npm, pinned) in CI only, for `claude plugin validate`.

**Storage**: files — `registry/*.json`, generated `index.json`, `.claude-plugin/marketplace.json`,
README markers; release assets (`<name>.zip`, `hashes.json`).

**Testing**: `python -m unittest discover tests`; remote validation (`--remote`) in CI.

**Target Platform**: GitHub (Actions, Releases); consumers: Claude Code ≥ 2.1, claude.ai, the
website (Astro, Node) via `index.json`.

**Project Type**: repository tooling (scripts + workflows) around a content repository.

**Performance Goals**: CI under 2 minutes; remote validation one API request per external entry.

**Constraints**: no new secrets; no copies of external skills; generated files committed; scripts
stdlib-only.

**Scale/Scope**: 7 skills now (3 local, 4 external), designed for tens.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. One source per skill | Registry points to repo/path/ref; nothing copied; unique names enforced | ✅ |
| II. Generated outputs never hand-edited | `build_index.py` writes; `--check` in CI fails on drift | ✅ |
| III. Validated against the source | Local and remote `SKILL.md` checks; claude.ai limits (R2) | ✅ |
| IV. Installable three ways | Marketplace (R1), zips (R5), folder links in README/index | ✅ |
| V. `index.json` is a public contract | `schema: 1`; contract in contracts/index-json.md; AGENTS.md section | ✅ |
| VI. Small and dependency-free | stdlib Python, `GITHUB_TOKEN` only (R6 caveat accepted) | ✅ |
| VII. Published skills only | Only the four public skills registered; `.github/skills/*` excluded | ✅ |

Post-design re-check: all ✅. One accepted limitation (R6): bump pull requests opened with
`GITHUB_TOKEN` do not trigger CI; the job validates before opening them.

## Project Structure

### Documentation (this feature)

```text
specs/001-skills-registry/
├── spec.md  design.md  plan.md  research.md  data-model.md  quickstart.md
├── contracts/
│   ├── registry-entry.md    registry/<name>.json and card.json
│   ├── index-json.md        index.json, schema 1 (the website's contract)
│   ├── marketplace.md       generated .claude-plugin/marketplace.json
│   └── scripts.md           build_index.py, release_zips.py, bump_refs.py command lines
├── checklists/requirements.md
└── tasks.md                 (Phase 2)
```

### Source Code (repository root)

```text
registry/                    quax.json unxt.json figkit.json figkit-upgrade.json
scripts/
├── skillreg.py              shared: load local skills + registry, frontmatter parser, validation, GitHub fetch
├── build_index.py           generate / --check / --remote validation
├── release_zips.py          build deterministic zips + hashes.json; decide whether to release
└── bump_refs.py             find newer tags for tag-pinned entries; rewrite registry files
tests/                       unittest: test_frontmatter.py test_build_index.py test_release_zips.py test_bump_refs.py
.github/workflows/
├── check.yml                replaces check-cards.yml: unit tests, build --check, --remote, claude plugin validate
├── release.yml              zips → dated release when changed (push to main, weekly, manual)
└── bump-refs.yml            weekly: propose newer tags as one pull request
index.json  .claude-plugin/marketplace.json  README.md (generated sections)  AGENTS.md (updated)
```

**Structure Decision**: one shared stdlib module (`scripts/skillreg.py`) and three thin command
scripts, so validation, generation, zipping and bumping read skills the same way. Workflows call
the scripts; no logic in YAML beyond orchestration.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| (none) | | |
