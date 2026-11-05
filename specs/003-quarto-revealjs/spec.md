# Feature Specification: quarto-revealjs — offline, archivable reveal.js decks with Quarto

**Feature Branch**: `add-quarto-revealjs`

**Created**: 2026-11-04

**Status**: Implemented (pull request #25). This specification was written after the
implementation, to record it as the constitution's governance section requires; the design was
settled by testing (see [research.md](research.md)).

**Amended**: 2026-11-04, lessons from a 45-slide talk built without the skill (user stories 6–12,
FR-101–FR-110, SC-101–SC-105); planned in [../004-quarto-revealjs-talk-lessons/](../004-quarto-revealjs-talk-lessons/plan.md).

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

### User Story 6 - Start every talk from the skill (Priority: P1)

An author says "make me a talk on X" (no mention of Quarto or reveal.js). The agent picks the skill,
sets up the deck folder from its template, initialises version control, and follows the author's
talk conventions from the first slide.

**Why this priority**: the talk that taught these lessons was built without the skill because the
request did not mention Quarto; every later lesson is worthless if the skill is not loaded.

**Independent Test**: read the skill's description and the conventions file; the description names
plain talk/presentation/slides requests, and the conventions file holds each of the author's rules.

**Acceptance Scenarios**:

1. **Given** a request "make a presentation about …", **When** the agent chooses skills, **Then** the
   skill's description matches it.
2. **Given** a new deck folder, **When** the agent sets it up, **Then** it is a git repository from day
   one and ignores virtual environments, cloned data repositories and render caches.
3. **Given** the author's conventions, **When** the agent writes slides and notes, **Then** it follows
   them (abbreviation in body text, spoken first-person notes with detail after a divider, paper
   icon top-right on result slides, grey background and disclaimer on out-of-expertise slides,
   backup section at the end, every citation checked against its source).

---

### User Story 7 - One file really is one file (Priority: P1)

The author shares or archives a deck whose full-slide app (background iframe) and title-slide
`<object>` must work from the single HTML file, with nothing beside it.

**Why this priority**: the skill wrongly said background iframes cannot be inlined, so decks
shipped an `apps/` folder or lost the app.

**Independent Test**: inline the apps of a rendered fixture deck, move the file to an empty folder,
and check it offline: no missing files, the app draws.

**Acceptance Scenarios**:

1. **Given** a rendered deck with a background-iframe app, **When** the inlining step runs, **Then**
   the deck opened alone, offline, shows the app and requests no local file.
2. **Given** a deck with `<object data="local.svg">`, **When** inlined, **Then** the object shows from
   inside the file.
3. **Given** the shared build, **When** it is made, **Then** it has no speaker notes, and the
   archived build still has them.
4. **Given** a deck whose front matter sets `embed-resources`, **When** the share build runs, **Then**
   the skill has warned that front matter overrides profiles and `-M`, and says to keep it out.

---

### User Story 8 - Nothing spills off a slide (Priority: P2)

The author runs one check that names every element lying outside the slide box, on any slide, in
Chromium and in WebKit, without false alarms from notes, SVG internals or MathJax.

**Why this priority**: overflow is invisible until the projector; eyeballing 45 slides misses it.

**Independent Test**: a fixture deck with one deliberately overflowing slide and slides with math,
notes and SVG; the check flags exactly the overflowing slide.

**Acceptance Scenarios**:

1. **Given** a slide with content past its bottom edge, **When** checked, **Then** the report names the
   slide and the element with its position in slide coordinates.
2. **Given** slides with equations, long notes, SVG figures and a clipped embedded app, **When**
   checked, **Then** none is reported.

---

### User Story 9 - Works in Safari too (Priority: P2)

The deck is presented on a Mac in Safari. Animations, icons and checks behave as in Chrome.

**Why this priority**: Safari lacks CSS path animation and treats file-loaded CSS masks differently;
both broke the talk silently.

**Independent Test**: the offline and overflow checks run headless in WebKit on the fixture decks.

**Acceptance Scenarios**:

1. **Given** the fixture decks, **When** the offline check runs in WebKit, **Then** it passes as in
   Chromium.
2. **Given** a path-shape animation, **When** the guide is followed, **Then** it has a SMIL fallback.

---

### User Story 10 - Animations that do not jump (Priority: P3)

Fragments fade in without moving anything; a slide sequence that builds one figure keeps the
figure fixed and adds layers; a long animation can be skipped with one key.

**Independent Test**: the guide states each pattern with a snippet; the skip-key script is in the
template and bound to "]".

**Acceptance Scenarios**:

1. **Given** a slide with many fragment steps, **When** the presenter presses "]", **Then** the slide
   jumps to its last step; pressed again, the deck moves on.

---

### User Story 11 - Citations and a bibliography slide (Priority: P3)

The author cites a paper on a slide as "[icon] Name et al. (year)" linking to it, or as a bare icon
in the top-right corner of a result slide, and regenerates a bibliography slide from the talk's
reference-manager collection.

**Independent Test**: render the fixture's citation slide; unit-test the generator against a stub
of the reference manager's local API.

**Acceptance Scenarios**:

1. **Given** a citation with URL, authors and year, **When** rendered, **Then** the slide shows the icon
   and "Name et al. (year)" as one link with the title on hover, offline.
2. **Given** a collection with two papers by the same first author and year, **When** the generator
   runs, **Then** they are labelled "2021a" and "2021b", sorted, each linking to its DOI (else URL).

---

### User Story 12 - No visible browser, wherever Chrome is missing (Priority: P2)

Checks and PDF printing never open a browser window, and they still run on a machine with only
Playwright's bundled Chromium.

**Acceptance Scenarios**:

1. **Given** a machine without Google Chrome, **When** a check script runs, **Then** it uses the bundled
   Chromium headless.
2. **Given** the skill, **When** an agent reads it, **Then** it states that no visible browser window may
   be opened.

### Edge Cases

- Linux and macOS differ (the zoom plugin's modifier key is Ctrl on Linux, Alt elsewhere).
- Media requests are cancelled when a slide's video unloads; that is not a missing file.
- `jupyter:` in `_quarto.yml` was observed to be ignored; the kernel is set per deck.
- The chalkboard plugin cannot be single-file; multiplex needs a hosted server.
- Public repository: no paper names, data or personal paths in the skill or its fixtures.
- An app file referenced by a background iframe but missing on disk: the inlining step reports it
  and leaves the reference alone (the offline check then names it).
- A deck with no apps: inlining changes nothing but the notes (share build).
- MathJax assistive MathML and zero-width strut elements sit outside the visible math; they must
  not count as overflow. Content inside a clipping container (the 2× scaled app pattern) is
  checked only as the container.
- Fragments hidden at the start still take space; overflow is measured with all fragments shown.
- Public repository: the conventions file names no paper, collection ID or person.

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
- **FR-101**: The skill's description MUST also match plain requests to make a talk, presentation or
  slides.
- **FR-102**: The skill MUST provide an inlining step that makes background-iframe and iframe apps
  load from a `blob:` URL built from data embedded in the deck, and `<object>` files from `data:`
  URIs, and MUST correct the guide's claim that background iframes cannot be inlined.
- **FR-103**: The skill MUST provide a share build via a Quarto profile whose output has no speaker
  notes, and MUST state that deck front matter overrides `_quarto.yml`, profiles and `-M`.
- **FR-104**: The skill MUST provide an overflow check reporting elements outside the slide box in
  slide coordinates, ignoring notes, SVG internals, MathJax internals and clipped content.
- **FR-105**: The offline and overflow checks MUST run headless in Chromium and in WebKit; the guide
  MUST document the Safari pitfalls (CSS path animation, CSS masks from files).
- **FR-106**: The guide MUST document the layout-stable animation patterns, and the template MUST
  include a skip-to-last-step key ("]").
- **FR-107**: The skill MUST provide a citation shortcode (inline and corner forms) and a generator
  that writes a bibliography slide from a reference-manager collection through its local API.
- **FR-108**: The skill MUST include the author's talk conventions in `references/style.md` and deck
  hygiene steps (version control on day one, what to keep out, prune unused figures).
- **FR-109**: Every browser-driving script MUST launch headless, prefer Google Chrome and fall back
  to bundled Chromium; the skill MUST say no visible browser window may be opened.
- **FR-110**: The end-to-end test MUST cover FR-102 to FR-107 on fixtures; new scripts that run
  without a browser MUST have unit tests run by `check.yml`.

### Key Entities

- **Deck folder**: `_quarto.yml`, `_deck/` (header, Plotly setup), `_vendor/` (MathJax, plotly.js),
  `apps/`, `media/`, decks at top level, `_output/`.
- **Verified versions** (`versions.json`): Quarto, bundled reveal.js, MathJax, plotly, date.
- **Expected failures**: the guide's ✗ rows, mirrored in the feature check's `EXPECTED_FAIL`.
- **Share build**: `_quarto-share.yml` profile, output `_share/`, notes stripped, apps inlined.
- **Citation**: URL, authors label, year, title; inline or corner.
- **Collection**: the talk's reference-manager collection, the single source of the bibliography.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A deck built by following `SKILL.md` makes 0 network requests and shows 0 raw TeX when
  opened with the network blocked.
- **SC-002**: Every row of the guide's table is exercised by the test; results match the guide.
- **SC-003**: The demo deck's PDF has exactly the expected pages (6) including the app still.
- **SC-004**: An upstream change to the bundled reveal.js is reported within a week, as an issue.
- **SC-005**: The personal-details scan finds nothing in the skill, fixtures or tests.
- **SC-101**: A fixture deck with a background-iframe app, moved alone into an empty folder, passes
  the offline check with 0 missing files.
- **SC-102**: The overflow check flags exactly 1 slide of the fixture deck (the deliberate one), in
  both engines.
- **SC-103**: The share build of the fixture contains 0 speaker notes; the archive build keeps all.
- **SC-104**: The offline check passes in WebKit on every fixture deck that passes in Chromium.
- **SC-105**: 0 scripts in the skill open a visible browser window.

## Assumptions

- Decks are viewed in a current Chromium-based browser or Safari; the tests use Google Chrome (or
  Playwright's Chromium) and Playwright's WebKit. Firefox is not tested.
- Authors render with Python available (Plotly via plotly.py); R and Julia cells are out of scope.
- MathJax 3.2.2 stays the pinned math engine until a newer one is verified (UPDATING.md).
- Quarto's own visual editors (VS Code, Positron) are not covered by the skill.
- Zotero is the reference manager; its local API (`localhost:23119`) is enabled in Zotero's
  settings. Other managers are out of scope.
- The talk's own scripts are the working reference; the skill generalises them, without the talk's
  paper names, collection IDs or paths.
