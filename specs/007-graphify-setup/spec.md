# Feature Specification: graphify-setup skill

**Feature Branch**: `claude/graphify-skill-docs-bcde3e`

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "A new local skill, graphify-setup, that wires graphify (github.com/Graphify-Labs/graphify, PyPI graphifyy) into a Python repository so that both humans and coding agents discover and use the repo's committed code graph. The skill encodes one profile: graphify-out/graph.json committed and tracked, rebuilt by a pinned pre-commit (prek) hook, union-merged by graphify's git merge driver, drift-repaired by a weekly CI workflow that opens a PR, and made discoverable through a rules block in AGENTS.md, a section in CONTRIBUTING.md, a one-line pointer in the README, and the docs site's contributing page. It also covers migrating a repo that has an older wiring where graphify-out/ is gitignored and built on demand, and per-repo variations (prek vs pre-commit, AGENTS.md vs CLAUDE.md, no docs site, monorepo). It ships no executable script. It does not teach day-to-day graphify usage, which upstream's own installed skill covers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Wire a repository that has no code graph (Priority: P1)

A maintainer opens a repository that has never used graphify and asks an agent to add it. Working from the
skill alone, the agent builds the first graph, decides what is tracked and what is ignored, installs the
rebuild hook, registers the merge driver, adds the drift-repair job, and writes the four pieces of guidance
(agent rules, contributor section, README pointer, docs page). The maintainer reviews one pull request and
every later clone of that repository starts with a usable graph.

**Why this priority**: This is the whole point of the skill and the case that will be run on every
repository. Everything else is a variation of it.

**Independent Test**: Run the skill against a repository with no graphify wiring, then clone that
repository fresh and confirm a graph query answers a question about the code without any build step.

**Acceptance Scenarios**:

1. **Given** a repository with no graphify wiring, **When** the skill's runbook is followed to the end,
   **Then** the repository has a tracked code graph, a hook that rebuilds it, a registered merge driver, a
   scheduled drift check, and guidance aimed at contributors and at agents.
2. **Given** that wiring is in place, **When** a contributor clones the repository and changes code,
   **Then** the commit carries a refreshed graph without the contributor doing anything beyond the
   repository's normal commit flow.
3. **Given** that wiring is in place, **When** anyone opens a pull request that touched code,
   **Then** the graph's change does not appear as reviewable noise in the diff.

---

### User Story 2 - An agent finds the graph on its own (Priority: P2)

A coding agent is dropped into a wired repository with no instructions beyond the repository's own files.
Reading those files, it learns that a code graph exists, that querying it comes before searching or reading
source, how to refresh it after changing code, and that the same rule must be passed on to any subagent it
dispatches to explore the code.

**Why this priority**: A graph nothing reads is wasted. This is what turns the committed artifact into
the behaviour the maintainer wants, and it is testable separately from the wiring.

**Independent Test**: Give a fresh agent only the wired repository and a question about the code, and
check whether its first move is a graph query rather than a search over files.

**Acceptance Scenarios**:

1. **Given** a wired repository, **When** an agent reads the repository's agent-guidance file, **Then** it
   finds the graph's location, the query-before-search rule, the refresh command and the subagent rule.
2. **Given** an agent that is about to dispatch a subagent to explore the code, **When** it writes that
   subagent's instructions, **Then** the query-before-search rule is repeated in them.
3. **Given** a human reading the README, **When** they look for how to work on the project, **Then** one
   line tells them a code graph exists and points to the full explanation, without the README selling a
   tool to people who only want to install the package.

---

### User Story 3 - Migrate a repository with an older, untracked wiring (Priority: P3)

A maintainer has a repository where the graph directory is ignored and rebuilt on demand by a named build
task, with no agent guidance. The skill converts it to the tracked profile without losing the explanatory
material that repository already had, and retires the now-redundant build task.

**Why this priority**: It applies to a minority of repositories, and only once each, but doing it by hand
risks leaving two ways to build the graph and two places that describe it.

**Independent Test**: Run the migration part of the skill against a repository whose graph is ignored, and
confirm afterwards that there is exactly one documented way to build the graph and that the graph is
tracked.

**Acceptance Scenarios**:

1. **Given** a repository that ignores its graph directory, **When** the migration is followed, **Then**
   the graph becomes tracked, the rest of the directory stays ignored, and the on-demand build task is
   either removed or justified in the pull request.
2. **Given** that repository's existing contributor documentation, **When** the migration rewrites it,
   **Then** the explanation of what the graph is and that nothing leaves the contributor's machine survives.
3. **Given** a repository whose commit checks reject large files, **When** the first graph is committed,
   **Then** the check has been adjusted in the same change rather than discovered as a failure.

---

### User Story 4 - A contributor is never blocked by the graph (Priority: P3)

A contributor who has not installed graphify, or who deletes a lot of code, or who is mid-merge, keeps
working. The failure modes the wiring can produce each have a documented escape that the repository itself
explains.

**Why this priority**: A rebuild hook that blocks commits for reasons nobody documented is worse than no
hook. This is what keeps the pattern tolerable across many repositories.

**Independent Test**: In a wired repository, make a commit that deletes a module, and separately merge two
branches that both changed code, following only the repository's own documentation to get through both.

**Acceptance Scenarios**:

1. **Given** a commit that removes enough code to shrink the graph, **When** the rebuild refuses to
   overwrite the larger graph, **Then** the repository's documentation names the override to use.
2. **Given** two branches that both changed code, **When** they are merged, **Then** the graph merges
   without a conflict, and if it does conflict the documented recovery is a rebuild rather than a hand edit.
3. **Given** a contributor who needs to commit without rebuilding, **When** they look for a way to skip the
   hook, **Then** the documentation names one.

---

### Edge Cases

- A contributor rebuilds the graph with a different clustering engine than the hook uses, so community
  grouping is reshuffled and the whole graph is rewritten on alternating commits.
- Someone commits with hooks disabled, so the tracked graph silently falls behind the code.
- An automated commit runs where graphify is not installed.
- A repository keeps its agent guidance in a differently named file, or has several such files.
- A repository publishes no documentation site, so there is no contributing page to extend.
- A repository holds several packages, so one graph covers all of them.
- The graph grows large enough that the repository's own size checks or a reviewer object.
- The graph is reviewed before its first commit, because it contains names and paths taken from the source.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The skill MUST be a local skill in this registry, discoverable by name and by the problem it
  solves, and installable by all three routes this registry supports.
- **FR-002**: The skill MUST describe exactly one wiring profile — the graph tracked in version control —
  and MUST NOT offer a second profile as an equal option.
- **FR-003**: The skill MUST give an ordered runbook that takes a repository from no graph to fully wired,
  in which each step states what is changed and how to tell it worked.
- **FR-004**: The skill MUST pin the graph-building tool to one version, and MUST require that every place
  that builds the graph — the commit hook, the scheduled job, and any command a human or agent is told to
  run — uses that same pinned version and the same options that affect grouping.
- **FR-005**: The skill MUST ensure only the graph itself is tracked, and that everything else the tool
  produces stays untracked.
- **FR-006**: The skill MUST keep the tracked graph out of reviewable diffs and collapsed in pull requests.
- **FR-007**: The skill MUST make the graph rebuild part of the repository's existing commit checks, shared
  through a committed configuration rather than a per-clone step, wherever the repository already has such
  checks.
- **FR-008**: The skill MUST provide escapes for the rebuild: a way to skip it, a way to proceed when the
  graph shrinks, and a statement of what happens in automated commits.
- **FR-009**: The skill MUST set up conflict-free merging of the graph between branches, and MUST state the
  recovery when a conflict happens anyway.
- **FR-010**: The skill MUST add a scheduled check that detects a graph that has fallen behind the code and
  proposes the fix as a reviewable change rather than committing to the default branch.
- **FR-011**: The skill MUST supply the text of the four discoverability surfaces: rules for agents,
  a section for contributors, a single-line pointer in the README, and a documentation-site page addition.
- **FR-012**: The agent rules MUST tell an agent to query the graph before searching or reading source for
  a question about the code, how to refresh it after changing code, how to carry the rule into subagents,
  and when not to bother.
- **FR-013**: The skill MUST cover converting a repository whose graph is untracked and built on demand,
  including what to carry over and what to retire.
- **FR-014**: The skill MUST say what to do when a repository differs from the assumed shape: a different
  commit-check tool, a differently named agent-guidance file, no documentation site, or several packages in
  one repository.
- **FR-015**: The skill MUST NOT restate how to use the graph day to day beyond the agent rules, because
  the tool installs its own guidance for that.
- **FR-016**: The skill MUST ship no executable script.
- **FR-017**: The skill's content MUST name no private repository, person, path or project, so that it is
  publishable from this registry.
- **FR-018**: The skill MUST state how a finished wiring is verified, including the two failure modes a
  maintainer would otherwise meet first: a commit that shrinks the graph, and a merge of two branches that
  both changed code.

### Key Entities

- **The code graph**: one tracked file holding the repository's symbols and the relationships between them,
  rebuilt from the source whenever the code changes, and the thing every query reads.
- **The untracked output**: the browsable and human-readable products the tool writes beside the graph,
  rebuilt locally and never reviewed.
- **The wiring**: the committed configuration that decides what is tracked, what rebuilds the graph and
  when, how it merges, and when drift is reported.
- **The guidance surfaces**: the four places a human or an agent can learn that the graph exists — agent
  rules, contributor documentation, the README pointer, the documentation site.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can take a repository from no graph to fully wired in one working session,
  reading only this skill and never the tool's own documentation.
- **SC-002**: A fresh clone of a wired repository can answer a question about the code from the graph with
  no build step and no tool configuration beyond installing the tool.
- **SC-003**: An agent given only a wired repository and a question about its code queries the graph before
  it searches or reads source files.
- **SC-004**: Two branches that both change code merge without a human resolving a conflict in the graph.
- **SC-005**: Every failure the wiring can cause — a blocked commit, a refused rebuild, a conflicted graph
  — is answered by a named escape in the repository's own documentation, with none left to the maintainer's
  memory.
- **SC-006**: Repeating the wiring across repositories produces the same five artefacts in the same places
  every time, so a reviewer can check one against another.
- **SC-007**: The skill passes this registry's checks on the first run: generated outputs fresh, limits
  respected, and no private details in the published content.

## Assumptions

- The target repositories are Python projects on GitHub whose default branch is protected enough that
  changes arrive by pull request.
- The target repositories already run commit checks through a shared, committed configuration, so the
  rebuild can be added there rather than installed per clone.
- Contributors and agents have, or can install, the graph tool; the repository does not vendor it and does
  not add it to the project's locked dependencies.
- The graph is built without the optional naming pass that calls a language model, so that every rebuild is
  reproducible and the tracked graph does not churn.
- A tracked graph of a few megabytes, rewritten whole when code changes, is an acceptable cost in these
  repositories; the skill states the cost rather than hiding it.
- The tool's own documented team recipe stays the basis of the profile; where this skill departs from it,
  the reason is written down.
- Each repository has, or will get, a file where agent guidance belongs.
