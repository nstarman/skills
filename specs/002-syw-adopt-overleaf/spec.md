# Feature Specification: syw-adopt-overleaf — move an existing Overleaf paper into showyourwork

**Feature Branch**: `syw-adopt-overleaf`

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "A new skill, `syw-adopt-overleaf`, that migrates an existing paper —
one with a live Overleaf project and a private git repository — into a fresh showyourwork
repository without losing or silently changing anything, so that `syw-overleaf-dropbox` and
`syw-site init` work on it afterwards. First case: Convexity Paper 1 (CP1)."

The agreed design (phases, mapping, scripts, layout) is in [design.md](design.md), the input to
`/speckit-plan`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Back up everything before anything changes (Priority: P1)

Before a migration touches anything, the author gets one backup folder, outside Dropbox and
iCloud, holding the old repository with all branches and tags, the Dropbox mirror of the Overleaf
project, a clone of the Overleaf project with its own history, the currently compiled paper
(`baseline.pdf`) and the names (not values) of the old repository's secrets. The backup checks
itself and says loudly if any part is incomplete.

**Why this priority**: a submitted paper with co-authors cannot be put at risk; every later step
relies on being able to restore.

**Independent Test**: run the backup on a scratch repository and a scratch mirror folder; check
that each part is present and verifies, and that breaking one part (e.g. an unreadable mirror)
makes the backup fail naming it.

**Acceptance Scenarios**:

1. **Given** an old repository, a mirror folder and access to the Overleaf project, **When** the
   backup runs, **Then** the folder holds all five parts, each verified, and nothing was written
   to the repository, the mirror or Overleaf.
2. **Given** any part fails to verify, **When** the backup runs, **Then** it stops with an error
   naming the part and the migration does not continue.
3. **Given** the backup ran, **When** its logs and files are inspected, **Then** no token value
   appears in any of them.

---

### User Story 2 - Show every difference the migration makes to the paper (Priority: P2)

After the paper is rebuilt from code in its new layout, the author sees every difference between
the pre-migration PDF and the new one: changed words, changed numbers listed one by one, pages
whose figures look different (with both versions to view), and a change in page count. Nothing
counts as accepted until the author says so.

**Why this priority**: the paper is submitted; a silently changed number or figure is the main
risk of regenerating it from code.

**Independent Test**: compare two small generated PDFs — identical; one number changed; one extra
page — and check the report and the result (no differences vs differences) for each.

**Acceptance Scenarios**:

1. **Given** two identical PDFs, **When** compared, **Then** the result reports no differences.
2. **Given** a PDF where one number changed (e.g. 0.43 → 0.44), **When** compared, **Then** that
   change is listed explicitly and the result reports differences.
3. **Given** a PDF with an extra page or a changed figure, **When** compared, **Then** the page
   count change, or the affected page with images of both versions, is reported.

---

### User Story 3 - Run the migration as a guided runbook with checkpoints (Priority: P3)

The author asks the agent to adopt a paper. The agent follows the runbook phase by phase —
survey, backup, freeze, build the new layout, build and compare, create the new repository,
rename and first sync, prune, hand off — recording findings and decisions in `MIGRATION.md`, and
stops for the author's explicit yes before every step that cannot be undone or that reaches
outside the machine.

**Why this priority**: it delivers the migration itself; it depends on stories 1 and 2.

**Independent Test**: migrate CP1 with the skill; at the end, `syw-overleaf-dropbox`'s build check
is clean on the new repository and mirror, and `MIGRATION.md` records every gate's approval.

**Acceptance Scenarios**:

1. **Given** a paper with an Overleaf project and an old private repository, **When** the
   migration completes, **Then** a new private repository `paper-<slug>` exists whose history
   starts at `[showyourwork] first commit` and shares no commit with the old repository, and the
   Overleaf project (same project, same co-authors) compiles `ms.tex` with `bib.bib`.
2. **Given** a gated step (backup confirmation, accepting PDF differences, repository creation,
   main-document change, first sync, pruning, archiving), **When** the agent reaches it, **Then**
   it stops and acts only after the author's explicit yes.
3. **Given** the migration completes, **When** `syw-overleaf-dropbox` is used for daily work,
   **Then** it works without changes beyond the recursive figure check (User Story 5).

---

### User Story 4 - Never push to Overleaf by accident (Priority: P4)

Until the first sync is approved, no build — local or CI on the new repository — can pull from or
push to Overleaf. Before the first sync, the author sees exactly which Overleaf files the push will
write, and that the text the build pulls is identical to what is in Overleaf after the rename.
The push and pull lists never overlap and never let a build overwrite authored text.

**Why this priority**: an unintended push overwrites co-authors' text in a live project.

**Independent Test**: check the lists against an inventory where one push pattern matches an
authored `.tex` file, and against a clean inventory; the first fails naming the file, the second
passes.

**Acceptance Scenarios**:

1. **Given** push and pull lists where a path is in both, or a push pattern matches an authored
   file, **When** checked, **Then** the check fails naming the path.
2. **Given** clean lists, **When** checked, **Then** the check passes.
3. **Given** the new repository before the first-sync phase, **When** it builds locally or in CI,
   **Then** it does not contact Overleaf.

---

### User Story 5 - Figure check finds figures in subfolders (Priority: P5)

`syw-overleaf-dropbox`'s build check compares every figure under the figures folder, including
subfolders (CP1 keeps figures in folders such as `figures/GD1/`).

**Why this priority**: without it the hand-off check passes while figures in subfolders are
missing or stale.

**Independent Test**: run the check on a layout with a figure only in a subfolder that is missing
from the mirror; it reports the figure.

**Acceptance Scenarios**:

1. **Given** a figure in a subfolder of the figures folder, missing from the mirror, **When** the
   check runs, **Then** it reports that figure.

---

### User Story 6 - Check before the new repository goes public (Priority: P6)

Before the author makes the new repository public (typically at arXiv), a check confirms that
nothing in it comes from the old repository's history, that no token-like strings are in its files
or history, and that no Overleaf-only private files (notes, referee replies) were committed.

**Why this priority**: making it public is later and is the author's call, but must never leak the
old history or private notes.

**Independent Test**: run the check on a repository that contains an object from the old
repository's backup, and on a clean one.

**Acceptance Scenarios**:

1. **Given** a new repository containing a commit or file from the old repository's history, a
   token-like string, or a private Overleaf-only file, **When** checked, **Then** it fails naming it.
2. **Given** a clean new repository, **When** checked, **Then** it passes.

### Edge Cases

- The Overleaf project uses a shared preamble as a git submodule: it is copied in as plain files;
  the new repository has no submodules unless the author asks.
- The paper defines its own `\variable` macro: it is replaced by showyourwork's, and the paths in
  the text stay unchanged.
- A co-author edits Overleaf during the freeze: the latest Overleaf commit recorded at the freeze
  differs from the current one; the agent stops and reconciles before the first sync.
- Signing a commit fails (1Password locked): the agent asks the author to unlock it and never
  bypasses signing.
- A difference between the PDFs cannot be resolved by the code (e.g. a hand-tuned figure): the
  author decides, and the decision is recorded.
- Overleaf's compiled PDF after the rename differs from the baseline: the first sync does not
  proceed.
- The migration has to be abandoned at any phase: each phase has documented restore commands; the
  old repository is unchanged until the final archive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST ship a local skill `syw-adopt-overleaf` (folder, `SKILL.md`,
  `card.json`) registered and validated like the other local skills.
- **FR-002**: The skill MUST describe the migration as ordered phases (survey, backup, freeze,
  build layout, build and compare, create repository, rename and first sync, prune, hand off) and
  name every step that waits for the author's explicit yes.
- **FR-003**: The skill MUST keep the existing Overleaf project, rename its main text to `ms.tex`
  and its bibliography to `bib.bib`, and leave the main-document setting to the author.
- **FR-004**: The skill MUST create a new private repository `paper-<slug>` (slug confirmed by the
  author) whose history starts at `[showyourwork] first commit` and that never fetches from the
  old repository; the old repository is archived only at the end, on the author's yes.
- **FR-005**: A backup tool MUST write and verify the five backup parts outside Dropbox and iCloud,
  fail naming any part that does not verify, and never write, print or log a token.
- **FR-006**: A comparison tool MUST report text, number, image and page-count differences between
  two PDFs, write both versions of differing pages for viewing, and report success only when
  nothing differs; it never accepts differences.
- **FR-007**: A list check MUST fail when a path is in both the push and the pull list, or a push
  pattern matches an authored file in the inventory.
- **FR-008**: The skill MUST keep the new repository from contacting Overleaf until the first-sync
  phase, and show the exact push and the pulled text's identity to the author before that sync.
- **FR-009**: The skill MUST classify every Overleaf file into one of four classes (authored text,
  build output, static support, not needed) and prune class 4 only from a list the author approves.
- **FR-010**: A public-readiness check MUST fail on commits from the old history, token-like
  strings, or committed private Overleaf-only files. (Identical file contents are not a leak.)
- **FR-011**: `syw-overleaf-dropbox`'s build check MUST include figures in subfolders.
- **FR-012**: The skill MUST document exact restore steps for each phase and record findings,
  decisions and approvals in `MIGRATION.md` in the backup folder.
- **FR-013**: The comparison and list checks MUST have automated tests run with the repository's
  test suite.

### Key Entities

- **Old repository**: the paper's private repository before the migration; never modified except
  the final archive.
- **New repository**: `paper-<slug>`, private, fresh history, showyourwork layout.
- **Overleaf project and its Dropbox mirror**: the live text co-authors edit; kept in place.
- **Backup folder**: the five verified parts plus `MIGRATION.md`.
- **Inventory**: every Overleaf file with its class and destination.
- **Baseline PDF**: the paper as compiled before the migration; the reference for every comparison.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: CP1 is migrated with the skill; the new repository shares zero commits with the old
  one, and the Overleaf project, co-authors and history are unchanged apart from the rename and
  the pruned files.
- **SC-002**: Every difference between CP1's baseline PDF and the migrated PDF is listed and
  accepted by the author, with zero unlisted differences.
- **SC-003**: The build check from `syw-overleaf-dropbox` reports nothing on the migrated CP1.
- **SC-004**: Every gated step in the migration has a recorded approval; zero irreversible or
  outward-facing steps happen without one.
- **SC-005**: No token value appears in any file, log or output produced during the migration.
- **SC-006**: Every acceptance scenario of stories 2, 4, 5 and 6 is covered by an automated test,
  except story 4's third (no Overleaf contact before the first sync), which follows from the
  configuration and is checked during the migration.

## Assumptions

- The author has Overleaf git access (token in 1Password), the GitHub CLI, poppler and the
  showyourwork development environment used for CP2.
- The new repository stays private until arXiv; the paper site is out of scope beyond pointing to
  `syw-site init`.
- A scripted one-command migration is out of scope until 2–3 migrations show what repeats.
- Renaming existing showyourwork repositories (e.g. CP2) to `paper-*` is out of scope.
