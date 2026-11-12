# Feature Specification: One hybrid-compute skill with per-cluster profiles

**Feature Branch**: `005-hybrid-compute`

**Created**: 2026-11-12

**Status**: Draft

**Input**: Replace `engaging-hybrid-compute` and `submit-hybrid-compute` with a single
`hybrid-compute` skill that holds the cluster-independent workflow once and one profile file per
cluster, and add the two missing pieces of workflow guidance: when to use git versus rsync, and how
to squash the result commits that accumulate.

## Why

Two published skills describe the same workflow against two clusters. Their `SKILL.md` files are
about 130 lines each and roughly 70% identical prose; the three shell scripts differ only in
partition names, paths and one `echo` line. Every improvement to the shared workflow has to be made
twice, and the author expects to work on many more clusters over the years. Each additional cluster
under the current shape means another near-identical copy to maintain and another marketplace card
for a machine almost nobody else can log into.

The shared prose also has two gaps, both cluster-independent, both currently unwritten:

- Both skills say big things go by `rsync` and small results go through git, but neither says how to
  decide which a given file is, nor how to run the `rsync` safely.
- `push_results.sh` commits figures and small arrays on every collection, so a long project
  accumulates hundreds of commits carrying binary blobs. Nothing in either skill addresses that.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One edit improves every cluster (Priority: P1)

The author improves the shared workflow — a better monitoring habit, a sharper rule about queued
jobs reading code at start time — and every cluster the skill covers inherits it from a single edit,
with no second file to keep in step.

**Why this priority**: This is the reason the change exists. Without it the restructure is only
rearrangement.

**Independent Test**: Change one sentence of workflow guidance and confirm that no other file in the
repository states the same thing, so there is no second copy that could drift.

**Acceptance Scenarios**:

1. **Given** the published skills, **When** a reader looks for the daily loop, the rules about
   queued jobs, fair-share discipline, monitoring or bookkeeping, **Then** each is stated in exactly
   one place.
2. **Given** a cluster-independent improvement to the workflow, **When** it is made, **Then** one
   file changes and every cluster the skill covers is covered by the new text.
3. **Given** the repository, **When** the shared workflow prose is searched for duplicated
   paragraphs, **Then** no paragraph of workflow guidance appears in two files.

---

### User Story 2 - Adding a cluster is one file (Priority: P1)

The author gains access to a new cluster. They add one profile file describing how to connect, where
storage lives, which partitions exist and what breaks there, and the whole existing workflow applies
to it with nothing copied.

**Why this priority**: The maintenance cost of the next dozen clusters is decided here, and it is
equal in importance to collapsing today's duplication.

**Independent Test**: Add a profile for a third, hypothetical cluster and confirm that no file
outside that profile and the skill's own trigger description needs to change.

**Acceptance Scenarios**:

1. **Given** the skill, **When** a cluster is added, **Then** the only new content is one profile
   file, and the only edits elsewhere are the skill's trigger description, its list of known
   clusters, and the generated registry outputs.
2. **Given** a profile file, **When** its contents are reviewed, **Then** it contains only what
   differs between sites: connecting, storage, partitions and caps, and site-specific breakage.
3. **Given** a profile file, **When** it is read for workflow guidance such as how to watch jobs,
   **Then** it does not restate that guidance but relies on the shared workflow.

---

### User Story 3 - Working on one cluster loads only that cluster (Priority: P2)

Someone working on subMIT follows the skill and reads the shared workflow plus the subMIT profile.
Engaging's Duo and ControlMaster machinery never enters the picture, and no step is silently missing
because it lived in the other skill.

**Why this priority**: It is what makes a single skill at least as good to use as two, rather than a
compromise accepted for maintenance reasons.

**Independent Test**: Follow the skill for one cluster end to end and confirm that every step needed
is reachable and that no other cluster's specifics are required reading.

**Acceptance Scenarios**:

1. **Given** the skill, **When** it is opened, **Then** its first instruction is to read the profile
   for the cluster in use, and the known profiles are listed by name.
2. **Given** a cluster in use, **When** the shared workflow needs a site-specific value such as a
   storage path or a partition name, **Then** it refers to the profile rather than naming one
   cluster's value.
3. **Given** work on one cluster, **When** the skill is followed, **Then** no instruction requires
   reading another cluster's profile.

---

### User Story 4 - Deciding between git and rsync (Priority: P2)

Facing a new kind of output — a checkpoint directory, a 200 MB snapshot, a one-page summary table —
the reader can tell from the skill which transport it belongs in, and why, and can run the `rsync`
without destroying anything on either side.

**Why this priority**: It is a real gap in today's guidance, and it is cluster-independent, so it is
also the first demonstration that the new shape pays off.

**Independent Test**: Take several example outputs of different sizes and purposes and confirm the
skill's rule assigns each to git or rsync without the reader having to guess.

**Acceptance Scenarios**:

1. **Given** an output file, **When** the skill's rule is applied, **Then** it lands in git if it is
   something to inspect in a diff before trusting, and in rsync if it would only ever be looked at
   whole.
2. **Given** the rule, **When** a reader asks why small results go through git at all, **Then** the
   skill answers that the review-before-pull check on cluster commits depends on it.
3. **Given** a transfer of large files, **When** the skill is followed, **Then** it states the
   exclusions to use and warns that a `--delete` sync must never be pointed at the cluster-only
   Slurm folder.

---

### User Story 5 - Squashing accumulated result commits (Priority: P3)

After months of runs the repository is heavy with `results:` commits carrying superseded figures. At
the end of a project phase the author compacts them to one commit, knowing what to do about the
branch protection that exists precisely to prevent history rewrites, and without leaving either
working copy broken.

**Why this priority**: It matters over a long project but is needed rarely, and the daily loop works
without it.

**Independent Test**: Walk the procedure on a scratch repository with a protected branch and confirm
each step is stated, in order, with the irreversible ones marked as the author's to perform.

**Acceptance Scenarios**:

1. **Given** the branch protection that setup instructs the author to add, **When** the squash
   procedure is read, **Then** it names the conflict plainly and gives the steps to relax the
   protection and restore it afterwards, marked as steps only the author can do.
2. **Given** the procedure, **When** it is read for timing, **Then** it says to squash when nothing
   is in flight — no queued or running jobs, no unpushed commits in the cluster clone — and gives a
   size trigger for squashing before a phase closes.
3. **Given** a completed squash, **When** the procedure is followed to the end, **Then** it covers
   reclaiming space locally and bringing the cluster clone back onto the rewritten history.
4. **Given** the procedure, **When** an agent reads it, **Then** the force push and the protection
   changes are the author's to run, not the agent's.

---

### Edge Cases

- A reader has the skill but is on a cluster with no profile: the skill says what to do (work from
  the nearest profile and write a new one), rather than failing silently.
- A reader installed one of the retired skills: its install command and release zip stop working.
  The change is a rename, so the old names must not be left in the registry pointing at nothing.
- The cluster clone has unpushed result commits when a squash starts: the procedure's
  nothing-in-flight precondition catches it, and the recovery step for the clone is destructive, so
  the precondition must be checked first.
- A profile needs a value the shared scripts hard-code: the scripts take such values as variables,
  so a new cluster needs no script edits.
- The shared scripts still carry one cluster's defaults as examples: they must be identifiable as
  placeholders to edit, not as values that work everywhere.

## Requirements *(mandatory)*

### Functional Requirements

**Structure**

- **FR-001**: The repository MUST publish exactly one skill for this workflow, named
  `hybrid-compute`, and MUST NOT retain `engaging-hybrid-compute` or `submit-hybrid-compute`.
- **FR-002**: The skill MUST state the cluster-independent workflow exactly once: the daily loop,
  the git/rsync division, result-commit squashing, how to submit jobs well, fair-share discipline,
  monitoring, and bookkeeping.
- **FR-003**: The skill MUST carry one profile per cluster, each containing only site-specific
  material: how to connect, storage paths and quotas, partitions and caps, and known site-specific
  breakage.
- **FR-004**: The skill MUST ship profiles for Engaging and subMIT, preserving the site-specific
  facts both retired skills carried, including for Engaging the Duo-plus-ControlMaster connection,
  the OnDemand login requirement, the gated reconnect helpers and the free-tier partitions; and for
  subMIT the key-only portal login, the round-robin login nodes, the small home quota that forces
  environments elsewhere, the partition whose CPUs lack the instruction set that common numerical
  wheels need, and the requirement to always pass an explicit time limit.
- **FR-005**: The skill's entry point MUST instruct the reader to read the profile for the cluster
  in use before acting, and MUST list the available profiles by name.
- **FR-006**: The shared workflow MUST refer to site-specific values through the profile rather than
  naming one cluster's value.
- **FR-007**: The one-time setup MUST separate cluster-independent steps, which stay with the shared
  content, from site-specific steps, which go in the profiles.
- **FR-008**: The skill MUST ship one copy of each shared script, taking cluster-specific values as
  variables; scripts that only make sense at one site MUST be identifiable as belonging to that
  site.
- **FR-009**: The skill's trigger description MUST name the clusters it covers and MUST also trigger
  on cluster-generic terms, so that naming either cluster, or describing the workflow without naming
  a cluster, reaches it.

**New guidance**

- **FR-010**: The skill MUST state the git/rsync division as a reviewability rule — git for what is
  worth seeing in a diff before trusting, rsync for what would only be looked at whole — with
  examples on both sides, and MUST explain that the review-before-pull check on cluster commits is
  why small results go through git.
- **FR-011**: The skill MUST say how to run a large transfer safely, including which paths to
  exclude and the warning never to point a deleting sync at the cluster-only Slurm folder.
- **FR-012**: The skill MUST give a procedure for squashing accumulated result commits at project-
  phase boundaries, covering: the conflict with the branch protection that setup adds, relaxing and
  restoring that protection as author-only steps, the force push with lease, reclaiming space
  locally, and bringing the cluster clone onto the rewritten history.
- **FR-013**: The squash procedure MUST state its precondition — nothing in flight, meaning no
  queued or running jobs and no unpushed commits in the cluster clone — and MUST give a trigger for
  squashing earlier than a phase boundary when the repository has grown too heavy.
- **FR-014**: The squash procedure MUST mark the force push and the branch-protection changes as
  steps the author performs, not the agent.

**Registry integrity**

- **FR-015**: The generated outputs — the index, the marketplace manifest and the README skill table
  — MUST be regenerated so they list `hybrid-compute` and no longer list the retired names.
- **FR-016**: The skill MUST carry a card describing it for people browsing, in the same format the
  other skills use.
- **FR-017**: The existing automated checks MUST cover the single skill's scripts rather than the
  two retired folders, and MUST continue to pass.
- **FR-018**: All content MUST remain free of personal details, using placeholders for usernames and
  paths, and MUST pass the repository's personal-details check.

### Key Entities

- **Shared workflow**: the cluster-independent guidance — daily loop, transport division, squashing,
  submitting, fair share, monitoring, bookkeeping. One copy, the thing an improvement edits.
- **Cluster profile**: one per site. Connecting, storage, partitions and caps, site-specific
  breakage. The unit of work for adding a cluster.
- **Shared setup**: one-time steps that do not vary by site — local key, private repository with a
  write-scoped deploy key, branch protection, repository layout, ignore rules, the project-level
  instructions for Claude, end-of-phase cleanup.
- **Shared scripts**: the array runner, the results committer and the job watcher, parameterised so
  one copy serves every cluster.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No paragraph of workflow guidance appears in more than one file; the duplication
  between the two retired skills, about 70% of each entry point, is gone.
- **SC-002**: A cluster-independent improvement to the workflow requires editing exactly one file.
- **SC-003**: Adding a cluster requires one new profile file plus the trigger description and the
  generated outputs — no copying of workflow prose and no script changes.
- **SC-004**: Every site-specific fact carried by either retired skill is present in the
  corresponding profile; a reader of one profile plus the shared workflow can complete the loop for
  that cluster with nothing missing.
- **SC-005**: Given an output file, the transport rule assigns it to git or rsync without the reader
  having to guess, and states why.
- **SC-006**: The squash procedure can be followed start to finish without consulting anything
  outside the skill, with every irreversible step marked as the author's.
- **SC-007**: The repository's checks pass: unit tests, index freshness and validation against the
  install targets, and the personal-details check.
- **SC-008**: Browsing the registry shows one card for this workflow instead of two.

## Assumptions

- The author is the only current user of the retired skill names, so retiring them needs no
  deprecation period, redirect or stub skill. The change is a rename; the old install commands and
  zip URLs stop working, which is accepted.
- The two existing clusters are the only ones in scope. The profiles for further clusters come later,
  one file at a time, which is the point of the shape.
- The site-specific facts in the retired skills are current and are carried over as written rather
  than re-verified against each cluster's live documentation; where a skill already tells the reader
  to check live values, that instruction is preserved.
- Per-cluster marketplace cards are not wanted. A generator that stitches standalone per-cluster
  skills was considered and rejected; it remains the fallback if separate cards ever become
  necessary.
- The daily loop itself is unchanged by this work, as is the decision to keep results on `main`
  rather than a separate branch.
- Skills install individually and nothing in the registry expresses a dependency between them, so
  each published skill has to be self-contained. This is what rules out a thin per-cluster skill
  that defers to a shared one.
- A profile is a page, not a document: if one grows to restate workflow guidance, that guidance
  belongs in the shared workflow instead.
