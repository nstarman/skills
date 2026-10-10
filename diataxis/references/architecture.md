# Documentation site architecture

The four modes are the load-bearing structure. This file covers everything built on top:
the tree, landing pages, navigation, cross-linking discipline, the material that is not
practitioner documentation, and what to do when the doc set has a second dimension.

**Contents**

- [The default tree](#the-default-tree)
- [Section landing pages](#section-landing-pages)
- [Navigation](#navigation)
- [Naming the sections](#naming-the-sections)
- [Cross-linking discipline](#cross-linking-discipline)
- [Reference: generated and hand-written](#reference-generated-and-hand-written)
- [What is not practitioner documentation](#what-is-not-practitioner-documentation)
- [Two-dimensional doc sets](#two-dimensional-doc-sets)
- [Scale](#scale)
- [Keeping it that way](#keeping-it-that-way)

---

## The default tree

```
docs/
  index.md                  # site landing page
  tutorials/
    index.md                # section landing page
    first-pipeline.md
    ...
  how-to/
    index.md
    authenticate.md
    deploy-to-kubernetes.md
    ...
  reference/
    index.md
    cli.md
    configuration.md
    errors.md
    api/                    # generated
  explanation/
    index.md
    architecture.md
    why-immutable-configs.md
  about/                    # not practitioner docs — see below
    changelog.md
    contributing.md
```

Folder-per-mode is the default because it makes the mode a property of the path, which means
tooling can see it, contributors cannot accidentally file things wrong, and nav generation is
free. Flat trees with grouped nav entries work for small sites but lose all of that.

Create a folder when it has content — or, on a greenfield site where the tree *is* the
deliverable, when its landing page is fully written and names what is not yet there. What you
must never ship is a folder of confident-looking empty pages that nothing acknowledges: a reader
clicks Explanation, finds one stub, and stops trusting the nav.

---

## Section landing pages

Every section needs an index page, and its job is not to list its children — the nav already
does that. Its job is to tell a reader **whether they are in the right place**, in the
vocabulary of their situation rather than yours.

A good section index does four things:

1. **States what this section is for, in one sentence, in user terms.** Not "This section
   contains how-to guides" — say "Solutions to specific problems, for people who already have
   the system running."
2. **Points elsewhere when this is the wrong place.** "If you have never used X before, start
   with the tutorial instead." This single line prevents most misnavigation, and it is the
   cheapest quality improvement available in a doc set.
3. **Groups its contents meaningfully** when there are more than about seven — by task family
   for how-tos, by subsystem for reference, by theme for explanation. Tutorials get a sequence,
   because order matters there and nowhere else.
4. **Says what is missing.** A "Not yet written" list is required whenever the section contains
   pages you did not write, and it is worth having even when it does not. An honest "we have no
   guide for X yet" costs nothing and buys enormous credibility; a section that silently implies
   completeness it does not have costs you the reader's trust in the whole nav.

Card grids look good and work well here, but the words matter more than the layout. A plain
annotated list with a good orienting sentence beats a beautiful grid of bare titles.

The **root** index page has a different job: route a stranger to the right mode within a few
seconds. Four entries, each with a one-line description phrased as the reader's own situation
("I want to learn the basics", "I need to get something done", "I need to look something up",
"I want to understand how it works"). Add whatever the site's single most common entry point
is — usually install, or the tutorial.

---

## Navigation

- **Four top-level entries**, plus a home for non-practitioner material. When something resists
  classification it is usually two things fused, not a fifth mode.
- **Two visible levels is usually right.** Section → page. A third level of nesting means a
  reader has to open two things to see whether the page they want exists.
- **Group lists longer than about seven.** Diátaxis notes that "lists longer than a few items
  are very hard for humans to read." A how-to section with forty guides needs task-family
  subgroups.
- **Sort by mode's own logic.** Tutorials in sequence (order is pedagogical). How-tos by
  frequency or task family rather than alphabetically, so the common cases surface first.
  Reference mirrors the product. Explanation from foundational to specialised.
- **Titles carry the mode.** How-tos begin "How to". Explanation reads with an implicit "About".
  Reference is a noun. If nav titles differ from page titles, keep them consistent in mode
  signalling.
- **Make the current mode visible** in the chrome — breadcrumbs, a highlighted section, a
  per-section sidebar. Most readers arrive mid-site from a search engine and need to know what
  kind of page they landed on.

---

## Naming the sections

The mode names are for authors; the section names are for readers. "Tutorials", "How-to guides"
and "Reference" are clear enough to use verbatim. "Explanation" is the one that reads oddly to
users — Diátaxis explicitly permits *Discussion*, *Background*, *Conceptual guides* or *Topics*.

What matters is that the name signals the *kind* of reading, not the subject. Names that fail
this test: "Guides" (which mode?), "Documentation" (all of it?), "Advanced" (a difficulty
level, not a mode — and reliably a dumping ground), "User Guide" (usually tutorial + how-to +
reference fused).

---

## Cross-linking discipline

Separation only works if delegation works. Each mode stays lean by pointing at the others, and
the link pattern is asymmetric by design:

| From | To | When |
| --- | --- | --- |
| Tutorial | Reference | At the end. "You used `search()`; here are all its options." |
| Tutorial | Explanation | At the end. "Curious why the client caches connections?" |
| How-to | Reference | Inline, wherever you deliberately did not enumerate options. |
| How-to | Explanation | In a "see also" at the end. |
| How-to | Tutorial | At the top, only as a prerequisite signpost. |
| Reference | Reference | Freely — related entries, glossary terms. |
| Reference | How-to | Sparingly, when a task is the obvious next question. |
| Explanation | everything | Freely. Connection is the mode's whole job. |

Rules that keep this from degrading:

- **Do not link out of the middle of a tutorial.** Every mid-lesson link is an invitation to
  leave and not come back.
- **One canonical home per concept, and one table row per fact.** When you are about to explain
  something a second time, link instead — repeated explanation is the leading indicator of a
  missing explanation page. The same holds for atomic facts: a value with a type and a default
  lives in exactly one reference table, and every other mention links to it. Reference↔reference
  duplication is the most damaging kind, because both copies look authoritative and they drift
  apart silently.
- **A glossary in reference, `term`-linked from everywhere.** This is the cheapest way to stop
  definitions duplicating across modes.
- **Prefer stable explicit anchors to heading-derived slugs** for cross-mode links. Heading text
  changes; explicit targets do not.
- **Fail the build on broken internal links.** Cross-linking is only load-bearing if it is
  enforced.

---

## Reference: generated and hand-written

Generated API docs are reference, but they are not all of reference. A complete reference
section usually contains:

- Generated API documentation (autodoc/autoapi/autodoc2, or the equivalent).
- CLI reference — commands, arguments, flags, exit codes.
- Configuration reference — every key, type, default, and constraint.
- Error and message reference, keyed by the exact text users will paste into a search engine.
- File format and schema reference.
- Environment variables, limits, compatibility and version matrices.
- Glossary.

Put generated output **inside** the reference section, not beside it:

```
reference/
  index.md          # cards/list covering all of the below
  cli.md
  configuration.md
  errors.md
  api/              # generated output lands here
```

The trap: most API-doc generators inject their own top-level nav entry by default, producing a
fifth section outside your four modes. Turn that off and place the generated index yourself.
The stack-specific setting is in `sphinx-myst.md`.

Docstrings are reference prose and inherit reference's constraints: describe, do not instruct,
do not explain, keep every entry of a kind the same shape. A docstring that teaches is a tutorial
hiding in the API.

---

## What is not practitioner documentation

SKILL.md lists the categories and says to give them an `about/` home. Three nuances that are not
obvious:

- **A version migration guide is genuinely a how-to guide** ("How to upgrade from 2.x to 3.0") and
  can live in either place. Pick one and be consistent.
- **Contributor documentation is a complete Diátaxis set of its own**, for a different
  practitioner. If it is substantial, give it its own four sections rather than mixing contributor
  how-tos into user how-tos.
- **An FAQ is almost always a symptom.** Each entry is a how-to, an explanation, or a reference
  fact that failed to get filed. Redistribute them and keep the FAQ only as a routing page of
  links — and if you do that, it must hold no answers of its own, or you have simply created a
  second home for the same facts.

## Two-dimensional doc sets

Documentation often has a second axis: multiple products, user roles (operator vs developer vs
end user), deployment targets (cloud vs self-hosted), or languages/SDKs. Diátaxis addresses
this directly and permissively — "Let documentation be complex if necessary."

Three shapes, and how to choose:

**Mode first, then dimension** (`how-to/kubernetes/…`, `how-to/docker/…`)
Choose when readers span the dimension — a single person deploys to both, and the mode is what
they are choosing between.

**Dimension first, then mode** (`self-hosted/how-to/…`, `cloud/how-to/…`)
Choose when readers are firmly on one side and rarely cross. Separate audiences get separate
doc sets that happen to share a domain.

**Mode first, dimension as tabs within a page**
Choose when the difference is a few commands, not a different task. One how-to with
per-platform tabs beats four near-identical how-tos, and keeps them from drifting apart.

The mistake is mixing shapes within one section. Pick per section if you must, but be explicit.

---

## Scale

For large doc sets, Diátaxis's advice is to add layers rather than flatten: group into
subsections of around seven items, and let hierarchy grow where it is genuinely needed. The
structure should follow "how users actually perceive the product, not how creators designed
it."

Practical consequences at scale:

- The **how-to section grows fastest and is the first to need subgrouping**. Group by user task
  family, not by internal component.
- **Reference grows with the product** and should track the product's own structure, so it
  mostly organizes itself.
- **Tutorials should stay few.** A doc set with twenty tutorials has how-to guides mislabelled.
  A well-served product often needs two or three: a first-contact lesson and one or two deeper
  ones per major capability.
- **Explanation grows with the interesting decisions**, not with the feature count.

If a section is unmanageable even after grouping, that is often a signal the *product* has two
audiences, and the two-dimensional shapes above apply.

---

## Keeping it that way

A restructure decays back to the mess it came from within a year unless the discipline is
written down and enforced.

- **Put the compass in the contributing guide**, with the four-row table and a sentence on
  where each mode lives. Most contributors will follow a rule they can see.
- **Add a docs PR checklist**: which mode is this page, does the title signal it, does it link
  out rather than duplicate, does it avoid the neighbouring mode's job.
- **Enforce mechanically what can be**: strict builds, link checking, example execution in CI,
  and a lint on titles if you can manage it (how-tos start with "How to").
- **Use issue templates that name the mode** — "missing how-to", "reference gap", "unclear
  explanation" — so incoming requests arrive pre-classified.
- **Re-run the inventory scan periodically.** Rising mixedness scores are an early warning that
  pages are re-fusing.
