# Feature Specification: quarto-revealjs — offline, archivable reveal.js decks with Quarto

**Feature Branch**: `add-quarto-revealjs`

**Created**: 2026-11-04

**Status**: Implemented (pull request #25). This specification was written after the
implementation, to record it as the constitution's governance section requires; the design was
settled by testing (see [research.md](research.md)).

**Input**: User description: "Distil what we learned about building reveal.js presentations in
Quarto into a skill: decks that stay openable in a browser for a very long time, as local files,
with math, Python/Plotly figures, speaker notes, transitions and embedded interactive paper
webapps, plus a PDF backup. Include a guide to which reveal.js features Quarto supports and how to
write them. Test the skill periodically in CI, and record how to update it as Quarto and reveal.js
change."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a deck that works with no network (Priority: P1)

An author asks an agent for a presentation. The agent sets up a deck folder from the skill and
renders the author's `.qmd` into one HTML file that opens in a browser with the network off: math
typeset, Plotly figures drawn, speaker notes available, nothing fetched from a CDN.

**Why this priority**: it is the point of the skill; a default Quarto deck silently depends on
CDNs even with `embed-resources: true`.

**Independent Test**: follow `SKILL.md` in an empty folder, render a deck with an equation, a
Plotly cell and notes, and open it with the network blocked.

**Acceptance Scenarios**:

1. **Given** an empty folder and the skill, **When** the agent follows the setup steps and renders,
   **Then** each deck is one HTML file and opening it with the network blocked makes no request
   that leaves the machine, raises no page error and leaves no raw TeX.
2. **Given** a deck without any Plotly figure, **When** it is opened offline, **Then** its math
   still renders (math must not depend on a figure's scripts).
3. **Given** a deck that references a file not shipped beside it (background video, background
   iframe), **When** it is checked, **Then** the check names the missing file.

---

### User Story 2 - Keep a PDF of exactly what was shown (Priority: P2)

The author gets a PDF printed from the same HTML: one page per slide, one page per fragment step,
speaker notes on their own pages, and a still image where a slide holds live content.

**Why this priority**: the PDF is the backup that outlasts any browser stack.

**Independent Test**: print the test deck and count pages and raster images.

**Acceptance Scenarios**:

1. **Given** a rendered deck, **When** the PDF is made, **Then** fragment steps and notes are separate
   pages and nothing needs the network.
2. **Given** a slide with an embedded WebGL or canvas app, **When** printed, **Then** the page shows
   the app's still image instead of a blank area.
3. **Given** the live talk, **When** it is presented, **Then** notes are not shown to the audience.

---

### User Story 3 - Know which reveal.js features work and how to write them (Priority: P3)

The author (or agent) looks up any reveal.js feature page and finds the Quarto syntax, whether it
works, whether it survives as one offline file, and the workaround where one exists.

**Why this priority**: most of reveal.js works through Quarto, but several features fail in ways
that look like success (links, previews, keyboard, postMessage).

**Independent Test**: every claim in the guide's table is exercised in a browser by the test suite.

**Acceptance Scenarios**:

1. **Given** a feature the guide marks as working, **When** the test deck exercises it, **Then** it
   works.
2. **Given** a feature the guide marks as not working, **When** exercised, **Then** it explicitly
   does not work (a check that crashes does not count as "not working").

---

### User Story 4 - Embed the author's interactive paper webapps (Priority: P4)

The author places a single-file interactive app (e.g. a figpress-apps build) on a slide or as a
full-slide background; it is interactive, matches the deck's theme, does not trap the keyboard,
and prints as a still.

**Why this priority**: the motivating use; it needs several non-obvious steps.

**Independent Test**: the test deck embeds a stand-in app both ways and checks drawing, theme
under system dark mode, keyboard after a click, and the PDF still.

**Acceptance Scenarios**:

1. **Given** an app embedded inline, **When** the deck is opened offline, **Then** the app draws and
   responds to dragging, and the deck stays one file.
2. **Given** the system is in dark mode and the deck is light, **When** the app shows, **Then** it is
   light.
3. **Given** the presenter clicks into the app, **When** they press an arrow key, **Then** the deck
   changes slide.

---

### User Story 5 - Learn when upstream changes break or improve the skill (Priority: P5)

The maintainer is told, without having to look, when a new Quarto, reveal.js or plotly release
breaks the skill, makes a documented limitation go away, or simply moves past the verified
versions; and has written steps to bring the skill current.

**Why this priority**: the skill documents a moving target; unverified claims rot.

**Independent Test**: the version check fails on a simulated reveal.js change; a scheduled failure
or version drift opens an issue.

**Acceptance Scenarios**:

1. **Given** Quarto bundles a different reveal.js, **When** the weekly run executes, **Then** it fails
   and points to `UPDATING.md`.
2. **Given** a newer Quarto or plotly with all checks passing, **When** the weekly run executes,
   **Then** a reminder issue says to bump the recorded versions.
3. **Given** a documented gotcha stops holding, **When** the run executes, **Then** it fails naming it.

### Edge Cases

- Linux and macOS differ (the zoom plugin's modifier key is Ctrl on Linux, Alt elsewhere).
- Media requests are cancelled when a slide's video unloads; that is not a missing file.
- `jupyter:` in `_quarto.yml` was observed to be ignored; the kernel is set per deck.
- The chalkboard plugin cannot be single-file; multiplex needs a hosted server.
- Public repository: no paper names, data or personal paths in the skill or its fixtures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The skill MUST provide templates that make a Quarto reveal.js deck load MathJax and
  plotly.js exactly once, from local copies, inlined at render time, with no CDN request at view
  time.
- **FR-002**: The skill MUST say where to obtain those libraries (versions pinned in
  `versions.json`) and how to fetch them.
- **FR-003**: The skill MUST support fragments inside equations and keep the arrow keys working
  after a click into an embedded iframe.
- **FR-004**: The skill MUST provide a PDF route that uses reveal.js's own print view, puts notes
  only in the PDF, and substitutes stills for live content.
- **FR-005**: The skill MUST provide an offline check reporting network requests, missing local
  files, page errors and raw TeX.
- **FR-006**: The guide MUST cover every revealjs.com feature page with Quarto syntax and a tested
  status, including the bundled reveal.js version.
- **FR-007**: The repository MUST test the skill end to end: set up a folder from the skill's assets
  as `SKILL.md` instructs, render fixtures, check offline, check the PDF, compare every feature
  check with the guide in both directions, and check the documented gotchas.
- **FR-008**: The test MUST run weekly against the latest Quarto release and on pull requests that
  touch the skill, and a scheduled failure or version drift MUST open or update an issue.
- **FR-009**: `UPDATING.md` MUST describe how to bring the skill current for each kind of failure.
- **FR-010**: Nothing personal or unpublished (paper names, data, home paths) may be committed.

### Key Entities

- **Deck folder**: `_quarto.yml`, `_deck/` (header, Plotly setup), `_vendor/` (MathJax, plotly.js),
  `apps/`, `media/`, decks at top level, `_output/`.
- **Verified versions** (`versions.json`): Quarto, bundled reveal.js, MathJax, plotly, date.
- **Expected failures**: the guide's ✗ rows, mirrored in the feature check's `EXPECTED_FAIL`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A deck built by following `SKILL.md` makes 0 network requests and shows 0 raw TeX when
  opened with the network blocked.
- **SC-002**: Every row of the guide's table is exercised by the test; results match the guide.
- **SC-003**: The demo deck's PDF has exactly the expected pages (6) including the app still.
- **SC-004**: An upstream change to the bundled reveal.js is reported within a week, as an issue.
- **SC-005**: The personal-details scan finds nothing in the skill, fixtures or tests.

## Assumptions

- Decks are viewed in a current Chromium-based browser; the tests use Google Chrome. Other browsers
  are not tested.
- Authors render with Python available (Plotly via plotly.py); R and Julia cells are out of scope.
- MathJax 3.2.2 stays the pinned math engine until a newer one is verified (UPDATING.md).
- Quarto's own visual editors (VS Code, Positron) are not covered by the skill.
