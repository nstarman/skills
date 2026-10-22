# Feature Specification: skills registry — nstarman/skills as the central clearinghouse

**Feature Branch**: `001-skills-registry`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "Aggregate my skills in nstarman/skills — including the ones that live
in other repositories (quax, unxt, figkit) — so it is my central skills aggregator and
clearinghouse: installable from Claude Code and claude.ai, and pulled into my website like the
`nstarman/skills/*/card.json` cards are today."

The agreed technical design (registry format, generated outputs, validation, website change,
zips and releases) is in [design.md](design.md), the input to `/speckit-plan`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a skill that lives in another repository (Priority: P1)

The author adds one small registry entry naming an external skill (e.g. unxt's skill in
`GalacticDynamics/unxt`), regenerates the outputs, and opens a pull request. CI confirms the skill
exists at the named place and version, and the skill then appears everywhere nstarman/skills is
read, without copying its files and without changing the other repository.

**Why this priority**: it is the capability that does not exist today and that every other story
builds on.

**Independent Test**: add the four initial entries (quax, unxt, figkit, figkit-upgrade), run the
generator, and check `index.json` lists them with correct links; break one entry's path and check
CI fails naming it.

**Acceptance Scenarios**:

1. **Given** a registry entry with a valid repository, path and ref, **When** the generator and CI
   run, **Then** the skill appears in `index.json` with its name, description, origin "external",
   a link to its folder at that ref, and its install id.
2. **Given** an entry whose path, ref or `SKILL.md` name is wrong, **When** CI runs, **Then** it
   fails with a message naming the entry and the problem.
3. **Given** a registry entry whose name equals a local skill's folder, **When** CI runs, **Then**
   it fails as a duplicate.
4. **Given** generated files edited by hand or left stale, **When** CI runs, **Then** it fails.

---

### User Story 2 - The website shows every skill (Priority: P2)

The website's Agent Skills section lists local and external skills together, each linking to
where its files live, external ones marked with their home repository.

**Why this priority**: the website is where people discover the skills; it is the user's explicit
goal.

**Independent Test**: run the website's collector against the registry branch and check the
generated website data lists all seven skills, with "from" set only on the four external ones; the
/tools/ page renders them.

**Acceptance Scenarios**:

1. **Given** `index.json` on nstarman/skills, **When** the website collector runs, **Then** its
   skills data lists every skill with name, description and link, and the home repository for
   external ones.
2. **Given** a missing or malformed `index.json`, **When** the collector runs, **Then** it fails and
   writes nothing, leaving the current section intact.

---

### User Story 3 - Install any skill in Claude Code (Priority: P3)

Anyone adds the marketplace once and installs any listed skill by name, local or external; an
external skill installs at its registered version.

**Why this priority**: the main way the author and collaborators use the skills.

**Independent Test**: add the marketplace from the branch, install one local and one external
skill, and confirm both load.

**Acceptance Scenarios**:

1. **Given** the marketplace, **When** a user installs `<name>@nstarman-skills` for a local and for
   an external skill, **Then** both install and their skills load.
2. **Given** a tag-pinned external skill, **When** installed, **Then** the installed files are those
   at that tag.

---

### User Story 4 - Install any skill in claude.ai (Priority: P4)

Anyone downloads a skill's zip from a stable link and uploads it to claude.ai.

**Why this priority**: claude.ai accepts skills only as uploads.

**Independent Test**: run the release workflow on the branch (or its script locally), unzip each
artifact and check its layout and frontmatter; upload one to claude.ai by hand.

**Acceptance Scenarios**:

1. **Given** a skill changed (locally, in the registry, or upstream on a tracked branch), **When**
   the release workflow runs, **Then** a new dated release holds a zip per skill, and
   `releases/latest/download/<name>.zip` serves the new one.
2. **Given** nothing changed, **When** the workflow runs, **Then** no release is made.
3. **Given** a zip, **When** unpacked, **Then** it holds one top-level folder named after the skill,
   with `SKILL.md` and its resource folders and without `card.json`.

---

### User Story 5 - Keep pinned versions current (Priority: P5)

When a tag-pinned source releases a new version (e.g. figkit v0.3.0), a pull request proposes
moving the entry to it.

**Why this priority**: keeps versioned skills current without manual tracking.

**Independent Test**: point an entry at an older tag and run the job; it proposes the latest tag.

**Acceptance Scenarios**:

1. **Given** a tag-pinned entry behind the repository's latest release, **When** the weekly job runs,
   **Then** it opens one pull request updating the ref and the generated files.
2. **Given** a branch-tracking entry, **When** the job runs, **Then** it is left alone.

### Edge Cases

- An external repository becomes private, is renamed or deletes the tag: CI and the weekly job fail
  naming the entry; the website keeps its last good data.
- A `SKILL.md` description written as a YAML block (`>` or `|`, as unxt's is) is read correctly.
- A description exceeds claude.ai's limit: CI fails naming the skill.
- The README table and install section are regenerated without touching the rest of the README.
- Spec Kit's own `.claude/skills/speckit-*` folders are not published skills.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST accept registry entries `registry/<name>.json` with exactly
  `name`, `description` and `source` (`repo`, `path`, `ref`); `name` equals the file name.
- **FR-002**: Local skills keep their folder, `SKILL.md` and `card.json` as today.
- **FR-003**: A generator MUST produce `index.json`, `.claude-plugin/marketplace.json` and the
  README's skill table and install section from local folders and registry entries.
- **FR-004**: `index.json` MUST list every skill with name, description, origin, link, source
  (repo, path, ref), Claude Code install id and zip link, sorted by name, with a schema version.
- **FR-005**: The marketplace MUST offer one plugin per skill; external skills fetched from their
  repository at the entry's ref.
- **FR-006**: CI MUST validate formats, name uniqueness, each skill's `SKILL.md` at its real
  location, claude.ai frontmatter limits, the marketplace file, and the freshness of generated files.
- **FR-007**: A release workflow MUST publish dated releases with one zip per skill when, and only
  when, any zip's content changed; triggered by relevant pushes, weekly, and by hand.
- **FR-008**: A weekly job MUST propose updating tag-pinned entries to their repository's latest
  release tag.
- **FR-009**: The website collector MUST read `index.json`, keep today's fail-without-writing
  behaviour, and add the home repository for external skills; /tools/ MUST show it.
- **FR-010**: `AGENTS.md` and the README MUST describe registering a skill, the generated files,
  installing, and the `index.json` contract.

### Key Entities

- **Local skill**: a top-level folder with `SKILL.md` and `card.json`.
- **Registry entry**: name, description and source (repo, path, ref) of a skill held elsewhere.
- **Index**: the generated list of all skills — the contract with the website.
- **Marketplace**: the generated Claude Code catalogue, one plugin per skill.
- **Release**: a dated set of zips, one per skill.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven skills (three local, four external) appear in `index.json`, the marketplace,
  the README table and, after the website change, on /tools/.
- **SC-002**: Registering a new external skill takes one new file plus regenerating, with no change
  to the source repository.
- **SC-003**: Every class of broken entry in the acceptance scenarios fails CI with a message naming
  the entry.
- **SC-004**: One local and one external skill install from the marketplace and load; every zip
  unpacks to a valid skill folder.
- **SC-005**: A run with no changes publishes no release and opens no pull request.

## Assumptions

- External repositories are public; reading them needs only the workflow's token.
- quax and unxt track `main`; figkit's two skills are pinned to `v0.2.0`.
- The website change ships after this repository's `index.json` exists, in its own pull request
  on nstarman/nstarman.github.io.
- Immediate cross-repository refresh of the website is out of scope (weekly plus manual remains).
