# Feature Specification: quarto-revealjs — lessons from a real talk

**Feature Branch**: `claude/quizzical-shamir-010e53`

**Created**: 2026-11-04

**Status**: Implemented; folded into [../003-quarto-revealjs/spec.md](../003-quarto-revealjs/spec.md)
(user stories 6–12 there), the area specification for the skill)

**Input**: User description: "Fold the lessons from building a 45-slide Quarto reveal.js talk
without the skill into the skill: trigger on plain talk requests; inline background-iframe apps as
blob: URLs (a data: iframe stayed blank) and `<object>` files as data: URIs; build the shared copy
with a Quarto profile, without notes; an overflow check; Safari/WebKit pitfalls and WebKit runs of
the checks; animation patterns that do not shift layout and a skip key; a paper-icon citation
shortcode and a Zotero bibliography generator; the author's talk conventions; deck hygiene; the
check scripts launch headless only, with bundled Chromium as a fallback."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start every talk from the skill (Priority: P1)

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

### User Story 2 - One file really is one file (Priority: P1)

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

### User Story 3 - Nothing spills off a slide (Priority: P2)

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

### User Story 4 - Works in Safari too (Priority: P2)

The deck is presented on a Mac in Safari. Animations, icons and checks behave as in Chrome.

**Why this priority**: Safari lacks CSS path animation and treats file-loaded CSS masks differently;
both broke the talk silently.

**Independent Test**: the offline and overflow checks run headless in WebKit on the fixture decks.

**Acceptance Scenarios**:

1. **Given** the fixture decks, **When** the offline check runs in WebKit, **Then** it passes as in
   Chromium.
2. **Given** a path-shape animation, **When** the guide is followed, **Then** it has a SMIL fallback.

---

### User Story 5 - Animations that do not jump (Priority: P3)

Fragments fade in without moving anything; a slide sequence that builds one figure keeps the
figure fixed and adds layers; a long animation can be skipped with one key.

**Independent Test**: the guide states each pattern with a snippet; the skip-key script is in the
template and bound to "]".

**Acceptance Scenarios**:

1. **Given** a slide with many fragment steps, **When** the presenter presses "]", **Then** the slide
   jumps to its last step; pressed again, the deck moves on.

---

### User Story 6 - Citations and a bibliography slide (Priority: P3)

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

### User Story 7 - No visible browser, wherever Chrome is missing (Priority: P2)

Checks and PDF printing never open a browser window, and they still run on a machine with only
Playwright's bundled Chromium.

**Acceptance Scenarios**:

1. **Given** a machine without Google Chrome, **When** a check script runs, **Then** it uses the bundled
   Chromium headless.
2. **Given** the skill, **When** an agent reads it, **Then** it states that no visible browser window may
   be opened.

### Edge Cases

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

- **Share build**: `_quarto-share.yml` profile, output `_share/`, notes stripped, apps inlined.
- **Citation**: URL, authors label, year, title; inline or corner.
- **Collection**: the talk's reference-manager collection, the single source of the bibliography.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: A fixture deck with a background-iframe app, moved alone into an empty folder, passes
  the offline check with 0 missing files.
- **SC-102**: The overflow check flags exactly 1 slide of the fixture deck (the deliberate one), in
  both engines.
- **SC-103**: The share build of the fixture contains 0 speaker notes; the archive build keeps all.
- **SC-104**: The offline check passes in WebKit on every fixture deck that passes in Chromium.
- **SC-105**: 0 scripts in the skill open a visible browser window.

## Assumptions

- Zotero is the reference manager; its local API (`localhost:23119`) is enabled in Zotero's
  settings. Other managers are out of scope.
- Safari behaviour is checked through Playwright's WebKit, which is close to but not Safari.
- The talk's own scripts are the working reference; the skill generalises them, without the talk's
  paper names, collection IDs or paths.
- The PDF route stays Chromium-only (WebKit in Playwright cannot print to PDF).
