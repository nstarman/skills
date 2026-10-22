---

description: "Task list for the skills registry"
---

# Tasks: skills registry — nstarman/skills as the central clearinghouse

**Input**: Design documents from `/specs/001-skills-registry/`

**Prerequisites**: plan.md, spec.md, design.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: included — the plan specifies stdlib `unittest` tests, and constitution Principle III
requires validation against real sources. Within each phase, test tasks come first and must fail
before the implementation that makes them pass.

**Organization**: by user story (spec.md) so each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md
- Paths are relative to the repository root (`nstarman/skills`) unless a task names
  `nstarman/nstarman.github.io`

## Reference material for every task

- Formats: `specs/001-skills-registry/contracts/` (registry-entry.md, index-json.md, marketplace.md, scripts.md)
- Entities and rules: `specs/001-skills-registry/data-model.md`
- Decisions: `specs/001-skills-registry/research.md` (R1 plugin form, R2 limits, R3 frontmatter,
  R4 fetching, R5 deterministic zips, R6 bumping, R7 CLI in CI, R8 tests)
- Rules: `.specify/memory/constitution.md` (stdlib only; no new secrets; no copies of external skills)

---

## Phase 1: Setup

- [X] T001 Create folders `registry/`, `scripts/`, `tests/`, and `tests/__init__.py` (empty); add `__pycache__/` to `.gitignore`
- [X] T002 [P] Add README markers around the skill table and an install section in `README.md`: `<!-- skills:table:start -->` … `<!-- skills:table:end -->` and `<!-- skills:install:start -->` … `<!-- skills:install:end -->` (contents filled by the generator later)

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: one shared module that reads both kinds of skill the same way

### Tests (write first, must fail)

- [X] T003 [P] Write `tests/test_frontmatter.py` for `skillreg.parse_frontmatter(text)`: plain `key: value`; single- and double-quoted values; folded `>` and literal `|` block scalars with `-`/`+` chomping and indentation (use unxt's real description shape: `description: >` then an indented paragraph); missing opening/closing `---` raises; unsupported constructs for `name`/`description` raise `SkillError` naming the file
- [X] T004 [P] Write `tests/test_skillreg.py` with temporary repos: `discover_local(root)` finds only top-level folders containing `SKILL.md` and ignores `.claude/`, `.specify/`, `.github/`, `registry/`, `scripts/`, `specs/`, `tests/`; `load_registry(root)` reads `registry/*.json`; `validate_offline(skills)` reports: card/entry keys not exactly as in contracts/registry-entry.md, empty strings, `name` not matching `^[a-z0-9-]{1,64}$`, file stem ≠ name, folder ≠ name, local `SKILL.md` name ≠ folder name, local `SKILL.md` description empty or "at most 1024 characters" exceeded, duplicate names across local and registry, `source.path` with a leading `/` or `..`; `SKILL.md` over 500 lines is a warning, not an error; every message names the skill or file

### Implementation

- [X] T005 Implement `scripts/skillreg.py` (stdlib only): `SkillError`; dataclass `Skill(name, description, origin, repo, path, ref)` with properties `href`, `install` (`<name>@nstarman-skills`), `zip` (`https://github.com/nstarman/skills/releases/latest/download/<name>.zip`) per data-model.md; `parse_frontmatter`; `discover_local`; `load_registry`; `validate_offline(root) -> (errors, warnings)`; make T003 and T004 pass
- [X] T006 Add `fetch_skill_md(repo, path, ref, token=os.environ.get("GITHUB_TOKEN"))` to `scripts/skillreg.py`: GitHub contents API via `urllib` with `Accept: application/vnd.github.raw+json`, raising `SkillError("<name>: <repo>/<path>/SKILL.md not found at <ref>")` on 404 (research R4)

**Checkpoint**: `python -m unittest discover tests` passes

---

## Phase 3: User Story 1 — Register a skill that lives in another repository (P1) 🎯 MVP

**Goal**: four registry entries, a generated `index.json` and README table, validated in CI.

**Independent Test**: quickstart.md steps 1–2.

### Tests (write first, must fail)

- [ ] T007 [P] [US1] Write `tests/test_build_index.py`: in a temporary repo with two local skills and two registry entries, `build_index.main([])` writes `index.json` exactly per contracts/index-json.md (`schema: 1`, `marketplace: "nstarman-skills"`, skills sorted by name, every field present, local `href`/`source` pointing at `nstarman/skills` `main`), rewrites only the README text between the markers, and `--check` exits 1 listing stale files after a hand edit and 0 when fresh; a duplicate name or a malformed entry exits 1 without writing
- [ ] T008 [P] [US1] Add to `tests/test_build_index.py` a `--remote` test with `skillreg.fetch_skill_md` patched: mismatched `SKILL.md` name, missing file (`SkillError`), and description over 1024 characters each exit 1 with a line naming the entry

### Implementation

- [ ] T009 [P] [US1] Create `registry/quax.json` (`nstarman/quax`, `skills/quax`, `main`), `registry/unxt.json` (`GalacticDynamics/unxt`, `skills/unxt`, `main`), `registry/figkit.json` and `registry/figkit-upgrade.json` (`nstarman/figkit`, `skills/<name>`, `v0.2.0`), each with a one- or two-sentence plain-text `description` for people browsing the website (written from the skill's own `SKILL.md`), 2-space indented, trailing newline
- [ ] T010 [US1] Implement `scripts/build_index.py` per contracts/scripts.md: offline validation (exit 1 on errors, warnings printed), `--remote` (fetch and validate each external `SKILL.md`: name equals entry, description non-empty and ≤ 1024 characters), generate `index.json` (2-space JSON, trailing newline) and the README skill table (columns: skill linked to `href`, description, from — the repo for external skills, blank for local) between the table markers; `--check` writes nothing and reports stale files; make T007 and T008 pass
- [ ] T011 [US1] Run `python scripts/build_index.py` and `python scripts/build_index.py --check --remote`; commit the generated `index.json` and README; confirm 7 skills, 4 external
- [ ] T012 [US1] Add `.github/workflows/check.yml` (on pull_request and push to main, `permissions: contents: read`): Python 3.11, `python -m unittest discover tests`, `python scripts/build_index.py --check --remote` with `GITHUB_TOKEN`; delete `.github/workflows/check-cards.yml` (its card checks are now in `validate_offline`)
- [ ] T013 [US1] Run quickstart.md step 2's failure checks in a scratch copy (bad path, bad ref, wrong name, extra key, hand-edited `index.json`, registry name equal to a local folder) and confirm each exits 1 naming the entry

**Checkpoint**: US1 complete — the registry works and CI guards it

---

## Phase 4: User Story 3 — Install any skill in Claude Code (P3)

*(Ordered before US2 because it changes this repository only; US2 is a separate repository.)*

**Goal**: a generated marketplace offering every skill, validated in CI.

**Independent Test**: quickstart.md step 3.

- [ ] T014 [P] [US3] Add to `tests/test_build_index.py`: the generated `.claude-plugin/marketplace.json` matches contracts/marketplace.md — name `nstarman-skills`, owner, one plugin per skill named after it, local `source: "./<name>"`, external `{"source": "git-subdir", "url": <repo>, "path": <path>, "ref": <ref>}`, `"skills": ["./"]` and `homepage` = `href` on every plugin; included in `--check`
- [ ] T015 [US3] Extend `scripts/build_index.py` to write `.claude-plugin/marketplace.json` (2-space JSON, trailing newline) and the README install section (Claude Code: `/plugin marketplace add nstarman/skills`, `/plugin install <name>@nstarman-skills`; claude.ai: download `<name>.zip` from the latest release and upload under Customize → Skills; by hand: copy the folder from its link into `~/.claude/skills/`) between the install markers; make T014 pass; regenerate and commit
- [ ] T016 [US3] Add to `.github/workflows/check.yml`: `actions/setup-node`, `npm install -g @anthropic-ai/claude-code@2.1.259` (pinned), `claude plugin validate .` (research R7)
- [ ] T017 [US3] Run quickstart.md step 3 with a temporary `CLAUDE_CONFIG_DIR`: `claude plugin validate .`, add the marketplace from the working tree, install `diataxis@nstarman-skills` and `unxt@nstarman-skills`, check `claude plugin details` shows one skill each; record the result in `specs/001-skills-registry/quickstart.md` notes

---

## Phase 5: User Story 4 — Install any skill in claude.ai (P4)

**Goal**: dated releases with one zip per skill, only when content changed.

**Independent Test**: quickstart.md step 4.

- [ ] T018 [P] [US4] Write `tests/test_release_zips.py`: for local skills in a temporary repo, each zip has a single top-level `<name>/` folder with `SKILL.md` and resource folders and no `card.json`; building twice gives byte-identical zips (sorted entries, timestamps 1980-01-01, fixed permissions — research R5); `hashes.json` maps name → sha256; with `--previous` the last line is `unchanged` for identical inputs and `changed` (names listed before it) after editing a file, adding or removing a skill; external fetching is patched
- [ ] T019 [US4] Implement `scripts/release_zips.py` per contracts/scripts.md: local skills zipped from their folder without `card.json`; external skills via `git clone --depth 1 --branch <ref> --filter=blob:none --sparse https://github.com/<repo>` + `git sparse-checkout set <path>` in a temporary directory (research R4); deterministic zips; `hashes.json`; `--previous` comparison; make T018 pass
- [ ] T020 [US4] Add `.github/workflows/release.yml` (on push to main with paths `*/SKILL.md`, `*/**`, `registry/**`, `scripts/**`; weekly schedule; workflow_dispatch; `permissions: contents: write`): download the latest release's `hashes.json` if any (`gh release download --pattern hashes.json`), run `release_zips.py dist --previous …`, and on `changed` create release `vYYYY.MM.DD` (or `vYYYY.MM.DD.N` if that tag exists) with every `dist/*` asset via `gh release create`
- [ ] T021 [US4] Run quickstart.md step 4 locally (`release_zips.py` twice, `unzip -l`), then trigger `release.yml` by hand after merge and check `https://github.com/nstarman/skills/releases/latest/download/unxt.zip` downloads a valid zip; upload one zip to claude.ai by hand (author)

---

## Phase 6: User Story 5 — Keep pinned versions current (P5)

**Goal**: a weekly pull request when a tag-pinned source releases a new version.

**Independent Test**: quickstart.md step 5.

- [ ] T022 [P] [US5] Write `tests/test_bump_refs.py` with `git ls-remote --tags` and the releases API patched: a tag-pinned entry behind the latest release is rewritten (`name: old -> new` printed); `--dry-run` writes nothing; branch-tracking entries (ref not a tag) are untouched; a current entry prints nothing; an API error for one entry is reported without touching others
- [ ] T023 [US5] Implement `scripts/bump_refs.py` per contracts/scripts.md (research R6); make T022 pass
- [ ] T024 [US5] Add `.github/workflows/bump-refs.yml` (weekly + workflow_dispatch; `permissions: contents: write, pull-requests: write`): run `bump_refs.py`; if any file changed, run `build_index.py` and `build_index.py --check --remote` and the unit tests, then commit to branch `bump-refs` and open or update one pull request with `gh pr create`/`gh pr edit`, its body listing the bumps and noting that checks must be re-run before merging (pull requests opened with `GITHUB_TOKEN` don't trigger CI — research R6)
- [ ] T025 [US5] Run quickstart.md step 5 (`registry/figkit.json` at `v0.1.0`, `bump_refs.py --dry-run` proposes the latest tag); restore the file

---

## Phase 7: User Story 2 — The website shows every skill (P2)

**Goal**: the website reads `index.json`. Separate pull request on `nstarman/nstarman.github.io`, after this repository's `index.json` is on `main`.

**Independent Test**: quickstart.md step 6.

- [ ] T026 [US2] In `nstarman/nstarman.github.io`, change `scripts/collect-skills.mjs` to fetch `index.json` (contents API at `SKILLS_REF`, default `main`), require `schema === 1` and a non-empty `skills` array whose items have non-empty string `name`, `description`, `href` and `origin` ∈ {`local`, `external`}, and write `config/skills.json` as `{name, description, href}` plus `from` (= `source.repo`) only for external skills; throw and write nothing on any problem (contracts/index-json.md "Website mapping"); update the header comment
- [ ] T027 [US2] In `nstarman/nstarman.github.io`, show "from <repo>" on external skill cards in `src/pages/tools/index.astro` and one line under the Agent Skills heading linking to the install section of `https://github.com/nstarman/skills#readme`; follow that repo's AGENTS.md (tests, card styles, `npm test`)
- [ ] T028 [US2] In `nstarman/nstarman.github.io`, run `SKILLS_REF=main node scripts/collect-skills.mjs`, check 7 skills with `from` on exactly the 4 external ones, run its test suite, and open the pull request (its CI posts a Cloudflare preview of /tools/)

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T029 [P] Rewrite `AGENTS.md`: layout (local skills, `registry/`, generated files, scripts, Spec Kit), adding a local skill, registering an external one, regenerating, the checks, releases and zips, the weekly bump PR, and "How it reaches the website" around `index.json` schema 1 and its compatibility rule (constitution Principle V)
- [ ] T030 [P] Update `README.md` prose around the generated sections: what the repository is (the registry and clearinghouse), the three ways to install, and where external skills live
- [ ] T031 Run all of quickstart.md; record results in `specs/001-skills-registry/quickstart.md`
- [ ] T032 Open the pull request for `001-skills-registry` into `main` (squash), get CI green, merge; then trigger `release.yml` by hand (T021) and start Phase 7 on the website

---

## Dependencies & Execution Order

- Setup → Foundational → US1 (MVP) → US3 → US4 → US5 → Polish → US2 (other repository, needs `index.json` on `main`)
- US3, US4 and US5 depend only on Foundational + US1's generator; they can proceed in parallel
  after T010 (they touch different files except `build_index.py`, which only US3 extends).
- Within each story: tests → implementation → run the story's quickstart step.

### Parallel opportunities

- T002 with T001's follow-ups; T003 ∥ T004; T007 ∥ T008 ∥ T009
- After T010: T014, T018, T022 (tests of three stories) in parallel
- T029 ∥ T030

## Implementation Strategy

1. **MVP**: Phases 1–3 — the registry, `index.json` and README, guarded by CI. Stop and check
   quickstart steps 1–2.
2. US3 marketplace → US4 zips → US5 bumping, each verified by its quickstart step.
3. Polish, merge, first release.
4. US2 on the website once `index.json` is on `main`.
