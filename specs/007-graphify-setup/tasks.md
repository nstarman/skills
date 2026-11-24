# Tasks: graphify-setup skill

**Input**: Design documents from `specs/007-graphify-setup/`

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md),
[quickstart.md](./quickstart.md)

**Tests**: No test tasks. The skill ships no executable, so `AGENTS.md`'s per-script unit-test rule does
not apply, and the specification asked for none. Verification is [quickstart.md](./quickstart.md), run as
the Polish phase.

**Organization**: By user story, so each can be written and checked on its own. Every task below edits
content in `graphify-setup/`; the two files are `graphify-setup/SKILL.md` (decisions and order) and
`graphify-setup/references/blocks.md` (paste-in material, no reasoning), as decided in plan.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup

**Purpose**: The folder and its registry-visible metadata.

- [X] T001 Create `graphify-setup/` and `graphify-setup/references/`
- [X] T002 Write `graphify-setup/card.json` with exactly `name` (`graphify-setup`) and a one-or-two
      sentence present-tense `description` for people browsing, per `AGENTS.md`
- [X] T003 Write the frontmatter of `graphify-setup/SKILL.md`: `name: graphify-setup` matching the folder,
      and a `description` under 1024 characters that fires on "graphify", "code graph", "knowledge
      graph", "wire up graphify", "commit graph.json", "make the repo queryable for agents", and on a
      repository that already has `graphify-out/` — without firing on day-to-day graph queries, which
      upstream's own skill handles (FR-001, FR-015)

---

## Phase 2: Foundational

**Purpose**: The parts of `SKILL.md` every later section refers back to. Nothing else can be written
until the reader knows what the finished state is and what the placeholders mean.

**⚠️ CRITICAL**: T004–T006 block Phases 3–6.

- [X] T004 In `graphify-setup/SKILL.md`, write the opening section: what the finished wiring is — five
      artefacts in five named places — and that this is the one profile, with the untracked variant named
      only as the migration source (FR-002, plan.md decision 1)
- [X] T005 In `graphify-setup/SKILL.md`, write the placeholder conventions (`<version>`,
      `<default-branch>`, `<agent-guidance-file>`) and state that no example names a real repository
      (FR-017, plan.md decision 8)
- [X] T006 In `graphify-setup/SKILL.md`, write the pin policy as its own short section: one release, no
      optional extras, pinned in the hook configuration and read from there by everything else; pin what
      is current when wiring, with 0.9.119 as the example (FR-004, research.md R3, plan.md decision 2)
- [X] T007 [P] Write the heading skeleton of `graphify-setup/references/blocks.md` in the order the
      runbook will call for the blocks, so later tasks fill sections rather than append

---

## Phase 3: User Story 1 — Wire a repository that has no code graph (Priority: P1)

**Goal**: An agent takes a repository from no graph to wired, in order, with a check after each step.

**Independent test**: Run the runbook against a repository with no graphify wiring, then clone it fresh
and answer a question from the graph with no build step (quickstart.md section 2).

- [X] T008 [US1] Add the runbook step for installing the pinned tool and building the first graph to
      `graphify-setup/SKILL.md`, including reading the graph before committing it because it carries
      names and paths from the source (plan.md risk row)
- [X] T009 [US1] Add the runbook step for what is tracked: `graphify-out/*` ignored with
      `!graphify-out/graph.json` negated, and the check that a fresh clone has the graph (FR-005)
- [X] T010 [US1] Add the runbook step for keeping the graph out of review: the `.gitattributes` line with
      `merge=graphify linguist-generated=true -diff`, and the check that `git diff` does not print it
      (FR-006)
- [X] T011 [US1] Add the runbook step for raising or excluding the repository's large-file commit check,
      placed before the first graph commit (FR-003, research.md R7)
- [X] T012 [US1] Add the runbook step for the rebuild hook in the repository's shared commit-check
      configuration, with the one-sentence note on why not `graphify hook install` or a per-clone git
      hook (FR-007, research.md R2, plan.md decision 7)
- [X] T013 [US1] Add the runbook step for registering the merge driver per clone, marked as the one
      manual step and why git requires it (FR-009, research.md R2)
- [X] T014 [US1] Add the runbook step for the scheduled drift job: opens or updates one pull request
      against `<default-branch>`, never pushes to it, and reads the pin out of the hook configuration
      (FR-010)
- [X] T015 [P] [US1] Fill the `.gitignore`, `.gitattributes` and merge-driver blocks in
      `graphify-setup/references/blocks.md`
- [X] T016 [P] [US1] Fill the rebuild-hook block in `graphify-setup/references/blocks.md`, carrying
      upstream's guards: the skip switch, the nothing-but-the-graph-staged case, and the
      graph-must-exist case (FR-008, research.md R5)
- [X] T017 [P] [US1] Fill the scheduled-drift-job block in `graphify-setup/references/blocks.md`

---

## Phase 4: User Story 2 — An agent finds the graph on its own (Priority: P2)

**Goal**: The four guidance surfaces, written so a human or an agent reading only the wired repository
learns the graph exists and what to do with it.

**Independent test**: Give a fresh agent the wired repository and a question about the code; its first
move is a graph query. Separately, read the README as someone installing the package (quickstart.md).

- [X] T018 [US2] Add the runbook step for the agent-guidance file: where the block goes, and what to do
      when the repository has none or has several (FR-011, FR-014)
- [X] T019 [US2] Add the runbook steps for the contributor section, the one-line README pointer and the
      documentation-site contributing page, each saying what to write and where (FR-011, plan.md
      decision 6)
- [X] T020 [P] [US2] Fill the agent-rules block in `graphify-setup/references/blocks.md`: query the graph
      before searching or reading source, refresh after changing code with the pinned command, repeat the
      rule in every subagent prompt that explores code, when not to bother, and that the graph is
      generated and not to be reviewed — with no claim about diff size (FR-012, research.md R6)
- [X] T021 [P] [US2] Fill the contributor-section block in `graphify-setup/references/blocks.md`: what
      the graph is, that parsing is local and nothing leaves the machine, edges marked read-from-source
      or inferred, the commands, and every escape from Phase 6 (FR-011, research.md R9)
- [X] T022 [P] [US2] Fill the README-line and documentation-page blocks in
      `graphify-setup/references/blocks.md`

---

## Phase 5: User Story 3 — Migrate a repository with an older, untracked wiring (Priority: P3)

**Goal**: A short section that converts the untracked profile without leaving two ways to build the graph.

**Independent test**: Run it against a repository whose graph directory is ignored; afterwards the graph
is tracked and exactly one documented build path remains (quickstart.md section 3).

- [X] T023 [US3] Add the migration section to `graphify-setup/SKILL.md`: un-ignore the graph alone, carry
      over the existing explanation rather than rewriting it, retire the on-demand build task or justify
      keeping it, and adjust the large-file check in the same change (FR-013)
- [X] T024 [US3] Add the repository-variations section to `graphify-setup/SKILL.md`: a different
      commit-check tool, agent guidance under another name, no documentation site, several packages in
      one repository — one rule each, no worked examples (FR-014)

---

## Phase 6: User Story 4 — A contributor is never blocked by the graph (Priority: P3)

**Goal**: Every failure the wiring can produce has a named escape, written into the wired repository and
exercised before the pull request is opened.

**Independent test**: In a wired repository, commit a deletion and merge two branches that both changed
code, using only that repository's documentation (quickstart.md).

- [X] T025 [US4] Add the escapes to `graphify-setup/SKILL.md` as a named section: the hook skip switch,
      the override for a rebuild that would shrink the graph, the recovery from a conflicted graph, and
      what happens in automated commits — each stated as text that must end up in the wired repository,
      not only in this skill (FR-008, FR-009, research.md R4, plan.md decision 4)
- [X] T026 [US4] Add the verification step as the last step of the runbook: a commit that deletes code, a
      merge of two branches that both changed code, a fresh clone answering a question, and a run of the
      drift job (FR-018, plan.md decision 5)

---

## Phase 7: Polish & Cross-Cutting

- [X] T027 Read `graphify-setup/SKILL.md` end to end as an agent with no prior context: every step says
      what to change and how to tell it worked, and nothing requires graphify's own documentation open
      alongside (SC-001)
- [X] T028 Check the budgets: `SKILL.md` under 500 lines, `description` under 1024 characters, and the
      reasoning in `SKILL.md` not duplicated in `references/blocks.md`
- [X] T029 Run `python scripts/build_index.py` and commit the regenerated `index.json`,
      `.claude-plugin/marketplace.json` and README sections
- [X] T030 Run `python scripts/build_index.py --check --remote`, `python -m unittest discover tests`,
      `claude plugin validate .` and `python scripts/personal_check.py`
- [ ] T031 Open the pull request for squash merge, describing the profile and naming the five corrections
      to upstream's recipe

---

## Not yet done

T031, the pull request, is the only task left.

## Dependencies

- Phase 1 → Phase 2 → Phases 3, 4, 5, 6 → Phase 7.
- Phase 3 is the MVP: a repository wired without the guidance surfaces still has a working, tracked,
  mergeable graph. Phase 4 is what makes it discoverable, and depends on Phase 3 only for the pinned
  command it quotes.
- Phases 5 and 6 depend on Phase 3's steps existing to refer to, and are independent of Phase 4.
- Within Phase 3, T008–T014 are sequential (one ordered runbook, one file); T015–T017 are parallel with
  each other and with T008–T014, because they fill separate sections of the other file.
- Within Phase 4, T018–T019 are sequential; T020–T022 are parallel.

## Parallel Execution

```text
Phase 2:  T007 alongside T004–T006        (different files)
Phase 3:  T015, T016, T017 together       (separate sections of references/blocks.md)
Phase 4:  T020, T021, T022 together       (separate sections of references/blocks.md)
Phases:   Phase 5 and Phase 6 together    (different sections of SKILL.md, no shared text)
```

In practice one writer holds both files, so the parallel markers matter only if the work is split.

## Implementation Strategy

Write Phase 1–3 first and stop: that is a repository with a tracked, rebuilt, mergeable graph and nothing
telling anyone about it — useful on its own and the thing hardest to get right. Add Phase 4, which is why
the feature exists. Phases 5 and 6 are small and can land in the same pull request. Phase 7 is the gate:
the skill is not done until the quickstart has been run against a throwaway repository, because every
claim in the runbook is about a repository this skill cannot see.
