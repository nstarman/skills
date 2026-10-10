---
name: diataxis
description: >-
  Restructure and rewrite documentation to follow the Diátaxis framework — tutorials, how-to
  guides, reference, explanation. Use whenever someone wants to audit, reorganize, restructure,
  split, or improve documentation or a docs/ folder, and whenever they mention Diátaxis, divio, or
  the four-quadrant docs model. Trigger for "our docs are a mess", "this page is doing too much",
  "split up the getting-started guide", "where should this page live", "write a tutorial / how-to
  / reference page for X", "plan our docs information architecture", or "make the docs easier to
  navigate" — even when the user never says Diátaxis. Also when a page mixes teaching with
  reference material, when generated API reference and narrative docs must coexist, or when moving
  docs between Sphinx/MyST, MkDocs and Zensical. Covers audit, migration map, the rewrites, cross-
  linking, landing pages, and redirects so links survive.
---

# Diátaxis documentation refactoring

Paths below are relative to this skill's own directory, not the user's project.

## Which job is this?

| Request | What to do |
| --- | --- |
| A whole docs tree; "our docs are a mess" | Full workflow: audit → map → refactor |
| "Split this page" / "where does this belong?" | Skip the scanner. Compass the page section by section, then apply moves |
| "Write a tutorial / how-to / reference page for X" | Skip phases 1–2. Read `references/modes.md` for that mode and write. Tutorials: run the preflight below first |
| Docs from scratch | Greenfield — no audit, no map. Tree + landing pages are the deliverable |

## The compass

Two questions, asked of a sentence, a section, a page, or a site:

1. Am I serving **action** or **cognition**?
2. Does this user need **acquisition** (study) or **application** (work)?

| If the content…  | …and serves the user's… | …then it must belong to… |
| ---------------- | ----------------------- | ------------------------ |
| informs action   | acquisition of skill    | a tutorial               |
| informs action   | application of skill    | a how-to guide           |
| informs cognition| application of skill    | reference                |
| informs cognition| acquisition of skill    | explanation              |

**Apply it at section scale, not page scale.** Real documentation rarely contains a misfiled
page; it contains a how-to guide with three paragraphs of explanation wedged into step 4 and a
table of every config flag at the bottom. A page-level audit records "how-to, fine." A
section-level audit records "how-to + explanation §2 + reference §5 — three destinations." The
second one is a work order; the first is a shrug.

## Ground rules

These bind on every job, and two of them are what separates a real refactor from a
plausible-looking one.

**Facts move; they are not manufactured.** A restructure relocates existing content. It does not
license inventing API surface, config keys, error strings, defaults, version matrices or CLI
flags to make a table look finished. When the source does not supply a fact the destination
seems to need, write `TODO(verify): <what is missing>` and list it in the summary. A reference
table with four real rows is worth more than one with twelve rows of which eight are guesses,
because the guesses are indistinguishable from the truth to every future reader. This pressure
is strongest in reference, where completeness feels obligatory — resist it there hardest.

**Move the machinery with the content.** A code block is not just its text. When you EXTRACT or
SPLIT, carry everything the block depended on: its imports, its `try`/`except` wrapper, doctest
skip markers and directives, fixtures, and any earlier block that defined a name it uses. A
snippet that ran inside its old page and raises `NameError` inside its new one is the most common
way a "verbatim" restructure breaks a project's test suite — and the page still looks right.

**A page moved unchanged can still be wrong.** Verbatim relocation preserves the source's
mistakes. When you move a page that gives commands — a contributing guide, an install page, a
testing page — check its commands against what the repo actually uses now (`nox` vs `tox`, PEP
735 dependency groups vs extras, task names, paths). Fix them or mark them `TODO(verify)`; do not
carry a broken command into a nicer folder and record the move as "mechanical, no contaminants".

**Never claim a verification you did not perform, and keep the claims out of the docs.** If you
write "expected output" in a tutorial, either run the command and paste the real bytes, or mark
the block as illustrative and say in the summary that it needs replacing. Never assert
determinism ("your numbers will match these") for output you have not observed.

Verification claims belong in your summary, naming the exact command you ran — never baked into
a file that ships: not a comment in `conf.py` or `zensical.toml`, not a line of page prose. A
config comment saying "verified against version X" is false the moment anything changes, and
nobody will ever go back and delete it. The summary is dated and disposable; the repo is not.

**Every file you create either has real content or is declared missing.** No silent stubs. A page
you did not write must appear on its section landing page under "Not yet written" *and* in the
summary's gap list with a line on what it needs. A tree of confident-looking empty files with a
summary that does not mention them is the worst output this skill can produce — a reader clicks
Explanation, finds one stub, and stops trusting the nav. Forced symmetry is where stubs come
from: one page per mode per feature yields four thin pages where one good one belongs. Modes
need not be balanced; a healthy doc set often has fifteen how-tos and two tutorials.

**One canonical home per fact.** Concepts get one explanation page; *atomic facts* get one table
row. A value with a type and a default — `runtime.workers`, "clamped above 64", the list of
supported formats — belongs in exactly one reference table, and everywhere else links to it.
Duplicated facts drift, and reference↔reference duplication is the worst kind because both
copies look authoritative. Note that the same fact often hides under two names: `--log-level` in
a CLI reference and `log.level` in a config reference are one fact, not two. The scanner's
**Facts asserted on more than one page** section finds these — run it over the *finished* tree,
not just the source, because a restructure is where duplicates get created. It matches table rows
and definition lines only, so a clean report means "no duplicated table row", not "no duplicated
fact"; prose duplication still needs your eyes, and claiming otherwise on the strength of a silent
tool is its own kind of false verification.

## Tutorial preflight

Run this **before writing a line** of any tutorial. A tutorial that cannot be completed is not a
flawed tutorial, it is a failed one — you are required to be present but condemned to be absent,
so nobody is there to rescue the learner.

- [ ] Runs on a laptop with nothing but the product installed. **No cloud account, no API key, no
      bucket, no hosted database, no signup, no paid resource.**
- [ ] Needs no network beyond installing the product. If the product's whole point is a remote
      service, use its local/offline/sandbox mode or a fixture — and if none exists, narrow the
      tutorial to the part that runs locally and name the gap.
- [ ] Zero placeholders. `YOUR_API_KEY`, `<your-project>`, "your region" each make it fail.
- [ ] Zero branches. No per-platform sections, no "if you prefer", no optional steps.
- [ ] Every step prints something, and you have written what it prints — from an actual run
      where you could run it.
- [ ] Anything you assert about state (a cache hit, a timing improvement) is consistent with what
      the learner actually did in the preceding steps.
- [ ] The learner ends holding something they made and can re-run from clean.

**Installation is not a lesson.** Test on the artifact, not the intent: at the end of the page,
has the learner *built or run something*, or is the software merely installed? If the latter, it
is `how-to/install.md` whatever the title says. A tutorial installs in step one and spends the
rest of the page making something work; a page whose final step is "verify the installation
succeeded" has no lesson in it.

**Before writing or rewriting any page, read `references/modes.md`** for that mode. It carries
the constraints, language patterns and failure modes that decide whether the page works.

## Workflow

**Map everything; execute in slices.** Reading and classifying the whole tree is cheap and
read-only, and without it your local decisions fight each other. Editing is expensive and hard to
reverse, so ship it in increments that each stand alone. (Diátaxis's "don't try to work on the
big picture" argues against withholding fixes pending a grand plan — not against knowing what
you have.)

### Phase 1 — Inventory and audit

Run the bundled scanner first; it gives you a work-ordered starting point and the seam list:

```bash
python <skill-dir>/scripts/docs_inventory.py <docs-root> --format md --out audit/inventory.md
```

Its **Seams** table — sections whose signals disagree with their page — is the output that
matters; those are the EXTRACT and SPLIT targets. Treat its `reads as` column as a prompt for the
compass, never a verdict: it counts words and cannot know what a user needs.

Then read the pages, working down each heading tree with the compass. Alongside, settle four
site-level questions:

- Where does a brand-new user actually land, and does anything there teach them?
- **Is there any real tutorial?** Usually there is not — there is a "Getting Started" page that
  is an installation how-to. This is the most common gap in a doc set, and it is a writing job,
  not a moving job.
- Where does reference live, and is it generated, hand-written, or both?
- What is **not practitioner documentation at all**? Changelog, release notes, contributor guide,
  ADRs, governance, support, licence. Legitimate, and outside the four modes — give them their
  own top-level home (`about/`) rather than mangling them into a quadrant.

### Phase 2 — The migration map

One table covering every page; template in `assets/audit-template.md`.

**Every source file gets exactly one row and one destination. No blanks.** The legal destinations
are: one of the four mode sections; the non-practitioner section; *dissolved into* N named pages;
or *deleted, with a redirect*. There is no fifth option and no "leave it at the root." A page
that will not fit is either two things fused (SPLIT) or not practitioner documentation. Before
calling the map done, count its rows against the source file count and state both numbers.

Order the work by leverage: entry points first (a contaminated entry point costs more than a
contaminated appendix), then the most mixed pages, then missing tutorials, then the rest.

**Greenfield is the exception to all of this.** Starting from nothing there is no audit and no
map; the tree plus the landing pages *are* the deliverable, so you do create the four sections
before the content exists. Write the landing pages fully, in reader terms — they are not stubs.
Everything unwritten goes in a "Not yet written" list on its section landing page and in the
summary. Do not generate placeholder pages for content you are not writing.

Present the map, then proceed — do not stop and wait unless the user asked for a plan only. Stop
for confirmation on exactly one class of action: deletions and anything else that loses the only
copy of content. Moves and rewrites are recoverable from git; deletions are not.

### Phase 3 — Refactor

One destination page at a time, finished before the next: apply the moves, rewrite in the target
mode's voice, fix the links.

## The refactoring moves

| Move | What it does | Typical trigger |
| --- | --- | --- |
| **SPLIT** | One page becomes two or more, one per mode | Page scores high on two modes |
| **EXTRACT** | Lift a passage out and rehome it, leaving a link — with its imports, skip markers and setup | Explanation embedded in a how-to |
| **DRAIN** | Pull scattered facts out of prose into a reference table | Options/defaults mentioned inline across a narrative |
| **MOVE** | Whole page is fine, wrong section | Correctly written, misfiled |
| **RETITLE** | Fix the title so the mode is legible from the nav | "Application performance monitoring" → "How to integrate application performance monitoring" |
| **DEMOTE** | Tutorial → how-to guide | It assumes competence and solves a task; it never taught anything |
| **PROMOTE** | How-to → tutorial | It is a newcomer's first contact and needs to build confidence |
| **LINK** | Replace duplicated content with a cross-reference | The same explanation or default appears in three places |
| **MERGE** | Several fragments become one coherent page | Three thin how-tos that are really one task |
| **STUB** | Create a section landing page | A new section needs an entry point |
| **DELETE** | Remove it, redirect the URL | Superseded or duplicated verbatim. Needs sign-off |

EXTRACT and DRAIN do most of the real work. A doc set "reorganized" without them has only moved
contaminated pages into tidier folders.

## Contamination smells

| Smell | What it means | Move |
| --- | --- | --- |
| Page called "Getting Started" that only installs things | An installation how-to, not a tutorial | DEMOTE, and note the missing tutorial |
| "You can either A or B, depending on…" inside a tutorial | Choice — kills tutorial flow | Pick one; EXTRACT alternatives to a how-to |
| A tutorial with troubleshooting sections | It does not reliably work; tutorials must not fail | Fix the tutorial; move edge cases to a how-to |
| "Note: this only works if…" scattered through prose | Reference facts homeless in narrative | DRAIN |
| A table of every option mid-walkthrough | Reference fused to a tutorial or how-to | DRAIN + LINK |
| An "Advanced" or "Guides" section | Unsorted overflow bucket, not a mode | Re-audit its contents individually |

## Examples, architecture, toolchain

- **Writing or reviewing examples and code blocks** → `references/examples.md`. An example that
  would be excellent in one mode is a defect in another; that file has the per-mode rules and the
  practices that stop examples rotting.
- **Planning the tree, writing landing pages, nav depth, cross-linking, a second dimension
  (products/roles/platforms), or keeping the structure from decaying** → `references/architecture.md`.
  Templates: `assets/landing-page-template.md`, `assets/contributing-diataxis.md`.
- **Sphinx / MyST** → `references/sphinx-myst.md`. **Zensical** → `references/zensical.md`.
  Other stacks: the modes and moves are unchanged; find their equivalents for nav, section index
  pages, cross-file links, and redirects.

## Don't break links

A restructure changes every URL, and inbound links live in issue trackers, Stack Overflow and
bookmarks you cannot edit. Three rules:

1. **Confirm the stack can redirect before anything moves.** If it cannot (Zensical cannot), say
   so and agree a mitigation — host-level rules, generated stub pages, or keeping URLs stable —
   rather than silently shipping breakage.
2. **Every old URL gets a redirect, fragments included**, since deep links carry anchors. Generate
   them from the map with `scripts/make_redirect_stubs.py` rather than by hand.
3. **Make broken links fail the build**, and verify before you claim it. `scripts/check_links.py`
   checks the source tree stack-agnostically; the toolchain files cover CI wiring. Pick one
   redirect mechanism and make it work — three overlapping half-configured layers is worse than
   one that is tested.

## The repo references the docs too

This is the failure that survives every docs-only check, and it is the one most likely to
embarrass whoever ships your work. A restructure can pass the link checker, build clean, and
still break the project, because things outside `docs/` name doc paths:

- **tests** that read a doc file (a spec/code drift gate parsing `docs/spec.md` — delete that
  file and the whole suite aborts at collection, so every test is now red)
- **`noxfile.py` / `tox.ini` / `Makefile`** targets, and generators like `sphinx-apidoc -o docs/api`
  which will happily recreate the directory you just dissolved
- **CI workflows** naming doc paths
- **`README.md`, `AGENTS.md`, `CONTRIBUTING.md`** — every stale link here is a 404 on GitHub, and
  `AGENTS.md` is usually the first file a new contributor or agent is pointed at
- **`.readthedocs.yaml`**, packaging metadata, and docs inside sub-packages

Run the bundled checker over the whole repo, not just the docs tree:

```bash
python <skill-dir>/scripts/check_repo_refs.py <repo-root> \
    --old-docs <pristine-copy-of-docs> --new-docs docs/
```

Then **run the project's own gate** — its test suite, its doctest/Sybil run over the docs, its
docs build. Not a substitute harness you wrote: the real one, the way CI runs it. If it will not
run, work at it before you conclude it cannot — a missing interpreter version, an editable
install, or a dependency group is usually the whole obstacle, and "I could not run the tests" is
a claim you have to earn just like any other. When it genuinely cannot run, say exactly what
stopped you.

Compare the example count before and after. A restructure that quietly drops fifty executed
examples has removed test coverage, whatever the page count says.

## Deliverables

1. `audit/inventory.md` — scanner output.
2. `audit/migration-map.md` — the per-page table, including redirects (`assets/audit-template.md`).
3. The refactored pages, landing pages, and updated nav config.
4. A summary following `assets/summary-template.md` — which requires a *Facts I invented or
   inferred* section and a *Gaps found and not filled* section. Both are mandatory; write "none"
   only if it is true.

## Before you say you're done

- Map rows = source file count, and both numbers are stated.
- No practitioner page sits outside the four mode sections.
- Every created file has real content or appears in the gap list.
- Every moved URL has a redirect, or the no-redirect mitigation is written down.
- `check_links.py` passes, and the scanner reports no duplicated table rows across the new tree
  (prose duplication you checked by reading).
- `check_repo_refs.py` is clean: nothing outside `docs/` still points at a page you moved.
- The project's own test/doctest/build gate runs green, or you have said precisely what stopped
  you from running it. Example counts did not silently drop.
- Every redirect target actually resolves in the new tree. A stub that 404s is worse than no
  stub, and an anchor map that rewrites paths it should have left alone manufactures 404s on
  links that used to work.
- Any build or run you claim to have done, you actually did — and the claim is in the summary,
  not in a shipped config comment or page.
- Every tutorial passes the preflight.
- No fifth mode in the nav.
