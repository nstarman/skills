# Examples, code, and interweaving

Examples are where documentation is actually judged. They are also the fastest way to
contaminate a mode, because a code block carries an implicit purpose and that purpose is
rarely stated. This file covers what an example is *for* in each mode, how to keep examples
from rotting, and how to make examples across a whole site accumulate into something rather
than restarting on every page.

**The diagnostic.** Ask of any code block: *what happens if the reader ignores it?*

- They cannot continue → tutorial.
- They cannot complete their task → how-to.
- They can still look up what they needed → reference.
- They still get the point, but less vividly → explanation.

If the answer does not match the page's mode, the example is contaminating it.

**Contents**

- [The same snippet, four jobs](#the-same-snippet-four-jobs)
- [Per-mode example design](#per-mode-example-design)
- [One worked domain across the site](#one-worked-domain-across-the-site)
- [Keeping examples true](#keeping-examples-true)
- [Output, errors, and placeholders](#output-errors-and-placeholders)
- [Diagrams](#diagrams)
- [Review checklist](#review-checklist)

---

## The same snippet, four jobs

Take one API call. Here is how it changes shape by mode — and note that the code barely
changes while everything around it does.

**Tutorial** — the example is the spine. It is embedded in a running narrative, uses the
tutorial's own domain, and is followed by what the learner should see.

> Now let's fetch the first page of results. Add this to `main.py`:
>
> ```python
> results = client.search("comet", limit=5)
> for r in results:
>     print(r.title)
> ```
>
> Run it again with `python main.py`. You should see five titles printed, beginning with
> something like `Comet Hale-Bopp`. Notice that the search returned instantly this time —
> the client cached the connection it opened in the previous step.

**How-to** — the example is a template the reader adapts, wrapped in conditional imperatives
and stripped of narrative.

> To restrict results to a single catalogue, pass `source`:
>
> ```python
> results = client.search("comet", source="mpc", limit=5)
> ```
>
> If you need results from several catalogues in one call, pass a list instead. For the full
> set of accepted sources, see the `search` reference.

**Reference** — the example illustrates the signature; it does not instruct. It sits inside a
consistent entry structure and would make no sense as a step.

> ### `search(query, *, source=None, limit=100)`
>
> Returns a `ResultPage`. Raises `QueryError` if `query` is empty.
>
> | Parameter | Type | Default | Description |
> | --- | --- | --- | --- |
> | `query` | `str` | — | Free-text query. Must be non-empty. |
> | `source` | `str \| list[str] \| None` | `None` | Restrict to catalogues. `None` searches all. |
> | `limit` | `int` | `100` | Maximum results. Values above 1000 are clamped. |
>
> ```python
> client.search("comet", source=["mpc", "jpl"], limit=5)
> ```

**Explanation** — the example is evidence in an argument. It often shows two things side by
side, and it may show code you should *not* write.

> The client caches connections per host rather than per query, which is why the second call
> below is roughly twenty times faster than the first:
>
> ```python
> client.search("comet")    # opens a connection
> client.search("asteroid") # reuses it
> ```
>
> This is a deliberate trade against memory: a long-lived client holds one socket per host it
> has ever touched. Libraries that cache per query instead get better cold-start behaviour and
> much worse behaviour in a loop, which is the pattern we expect most users to write.

---

## Per-mode example design

### Tutorial examples

- **Cumulative, not standalone.** Each block builds on the last. The learner ends with one
  artifact they made, which is what makes it feel like an achievement.
- **Show the file, not just the fragment.** When a snippet is added to a growing file, make
  clear where it goes. Show the whole file at the milestones.
- **Always follow with the result — the real one.** A step whose outcome is invisible teaches
  nothing, and an outcome you made up teaches something false. Run the snippet and paste what it
  actually prints. If you genuinely cannot run it, mark the block as illustrative and say so in
  your summary; never write "your output will match this exactly" for output you have not seen.
  This applies to derived claims too: row counts, timings, and cache-hit narration are all
  assertions the learner will check against their screen within seconds.
- **No placeholders and no credentials.** See the tutorial preflight in SKILL.md — this is a
  precondition on the whole page, not a style note. A fixture file or a step that generates local
  data is the fix; "sign up for a free tier" is not.
- **Copy-pasteable, one block at a time.** Do not require assembling fragments.

### How-to examples

- **Minimal and adaptable.** Show the smallest change that solves the stated problem, with
  the varying part obvious.
- **Realistic values, clearly substitutable.** `source="mpc"` beats `source="foo"`, because it
  shows the shape of a real value; make it obvious it is an example.
- **One example per branch of a conditional imperative**, so readers can jump to their case.
- **No setup preamble.** Competence is assumed. Link to installation, do not repeat it.

### Reference examples

- **One per entry, same position every time.** Predictability is the point.
- **Non-instructional.** A bare call, not "first do X then Y."
- **Exercise the signature**, especially defaults, unusual parameter combinations, and the
  error condition if there is a common one.
- **Never build a scenario.** The moment an example needs two steps, it wants to be a how-to.

### Explanation examples

- **Comparative.** Two approaches side by side, or before/after.
- **May be non-runnable.** Pseudocode, a partial sketch, a diagram, or an anti-example are all
  legitimate here — mark anti-examples unmistakably so nobody copies them.
- **Illustrate the claim you just made**, and say what the reader should conclude.

---

## One worked domain across the site

Choose a single realistic domain and use it everywhere. A reader who has met your `orders`
table in the tutorial recognizes it instantly in a how-to, and spends their attention on the
new idea rather than on re-parsing an unfamiliar scenario.

Pick something that stresses the product honestly — real-world messiness, plausible field
names, enough entities to show relationships. `foo`/`bar` teach nothing and quietly signal that
nobody thought about the reader. A domain that is too cute (`SpaceCatsAPI`) burns the reader's
patience.

Keep a fixture repository under `docs/examples/` holding the data and scripts that every mode
draws from. Then a tutorial, three how-tos and the reference all cite the same file, and a
change to the product updates one place.

**But keep interweaving to links, not inlined content.** The point of separate modes is that
each stays lean by delegating. Cross-linking is how a mode stays honest:

- Tutorial → links out to reference for the details it deliberately skipped, and to
  explanation for the "why" it deliberately skipped. Put these at the *end*, so they do not
  invite the learner to leave mid-lesson.
- How-to → a "see also" pointing at the reference for full options and at the explanation for
  the reasoning. Inline links only where the reader might genuinely need to detour.
- Reference → minimal outbound links; glossary terms and related entries.
- Explanation → dense links into all three. This is the mode whose whole job is connection.

A single canonical definition per concept, linked from everywhere, is what stops the "same
three paragraphs on four pages" problem. When you find yourself explaining something twice,
that is a signal an explanation page is missing, not that you should copy-paste better.

---

## Keeping examples true

Documentation examples rot faster than prose because they encode exact interfaces. Rotted
examples do more damage than missing ones — they destroy trust, and in a tutorial they cause
outright failure.

- **Include from real files, not by transcription.** Sphinx: `literalinclude` with
  `:start-after:`/`:end-before:` sentinels. Line-number ranges (`:lines: 12-30`) rot silently
  the moment the source file is edited — never use them for docs you intend to maintain.
  Zensical: `pymdownx.snippets` with section markers.
- **When you move a block, move what makes it run.** Imports, `try`/`except` wrappers, doctest
  skip markers and directives, and any earlier block that defined a name it uses. A page whose
  examples executed in their old home and raise `NameError` in the new one has quietly deleted
  test coverage and shipped a broken lesson, and neither a link check nor a docs build will say
  so. A block that mutated global state under a skip marker is worse: unskipped, it corrupts
  every example that runs after it.
- **Run the examples in CI.** Doctest, `pytest --doctest-glob='*.md'`, `markdown-exec`, or a
  script that extracts and executes fenced blocks. This is the only thing that actually holds —
  and note that sentinel includes only pay for themselves if something executes the source file.
  A snippet file nothing runs is a transcription with extra steps; either make it runnable or
  inline the code and accept the maintenance.
- **Test tutorials end to end.** They are the highest-cost failure and the most brittle,
  because a product change ripples along the whole narrative.
- **Pin versions in examples** where behaviour differs across versions, and say which version
  the example is for.
- **Prefer sentinels over line numbers everywhere.** This applies to config excerpts too.

---

## Output, errors, and placeholders

- **Show output whenever the reader would look for it** — always in tutorials, usually in
  how-tos, rarely in reference. Truncate long output with an explicit `…` and say what was cut.
- **Distinguish input from output by putting them in separate blocks**, so the command block
  stays copy-pasteable. Do not use a `$` prompt to do this job: it breaks copy-paste, which is the
  one thing the block is for. (If the project's existing docs already use `$` consistently and its
  renderer strips it, follow the project — consistency beats this rule.)
- **Placeholders**: pick one convention (`<your-project-id>` or `YOUR_PROJECT_ID`) and hold it
  site-wide. Say immediately where the value comes from. In tutorials, eliminate them entirely.
- **Error examples belong in reference and how-tos.** Showing the exact error text is one of
  the highest-value things a doc set can do, because it is what people paste into search. Give
  errors their own reference page keyed by message.

---

## Diagrams

A diagram is an example in a different medium, and the same mode rules apply. **Explanation** is
their natural home — architecture, data flow, state machines, trade-off spaces. **Reference**
takes structural diagrams: schemas, class hierarchies, protocol formats. **How-to** takes one only
when the spatial relationship *is* the task. **Tutorials** rarely need them: a diagram is
abstraction, and abstraction is what the tutorial is deliberately withholding — a screenshot of
the expected result is a different thing and often valuable.

Prefer diagrams-as-code so they diff and review with the docs, and give every one a text
alternative.

## Review checklist

- Does every code block's job match the mode of its page?
- Did you run everything you could run, and is every "expected output" real?
- Would a reader who ignored a given block still be served appropriately for that mode?
- Are tutorial examples cumulative, placeholder-free, and followed by expected output?
- Do how-to examples show the varying part clearly and link out for full option lists?
- Are reference examples uniform in position and shape across entries, and non-instructional?
- Do explanation examples support a claim, and are anti-examples unmistakably marked?
- Is one worked domain used consistently across modes?
- Is anything included by line number that should use sentinels?
- Is anything duplicated that should be a link?
- Does anything execute in CI, and if not, what is the plan for keeping it true?
