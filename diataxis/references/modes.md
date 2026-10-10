# Writing in each Diátaxis mode

Full guidance for the four modes. Read the section for the mode you are writing before you
write. Quotations are from https://diataxis.fr.

**Contents**

- [Tutorials](#tutorials)
- [How-to guides](#how-to-guides)
- [Reference](#reference)
- [Explanation](#explanation)
- [The four boundaries](#the-four-boundaries)
- [After any rewrite](#after-any-rewrite)

---

## Tutorials

**Learning-oriented. Action + acquisition. Answers "Can you teach me to…?"**

> "A tutorial is an experience that takes place under the guidance of a tutor. A tutorial is
> always learning-oriented."

Run the **tutorial preflight in SKILL.md before drafting** — runnability, no credentials, no
branches, no placeholders, real output. Nothing below matters if the tutorial cannot be completed.

### Checklist

Can a newcomer complete it with no prior knowledge and no decisions? Does every step show a
result? Does it work from a clean state, today, twice in a row? Is every explanatory paragraph
gone or shrunk to a clause with a link? Are there zero optional branches? Does it say what the
reader will *do*, not what they will learn? Is every "notice that…" claim actually true given what
the learner just did?

### The point of a tutorial is not its product

"While a student will learn by doing, what the student does is not necessarily what they learn."
Design the activity for what it *teaches*, not for what it produces. A tutorial that builds
something trivial but teaches the shape of the system beats one that builds something impressive
by copy-paste.

**Installation is not a lesson.** At the end of the page, has the learner built or run something,
or is the software merely installed? If the latter it is an install how-to, whatever the title
says. A page whose final step is "verify the installation succeeded" contains no lesson.

The tutor carries almost all the responsibility — for what is learned, for the activity that
teaches it, and for the learner's success. There is "no responsibility on the pupil to learn,
understand or remember." A tutorial with one broken step is not slightly flawed; it has failed,
because nobody is there to rescue the reader.

### What a tutorial must do

- **Show the destination up front.** "In this tutorial we will create and deploy a scalable web
  application." Not "in this tutorial you will learn…", which presumes on the learner.
- **Produce a visible result at every step.** "Every step the learner follows should produce a
  comprehensible result, however small." Cause and effect is where the learning happens.
- **Narrate.** *"You will notice that…"*, *"After a few moments, the server responds with…"* Show
  actual expected output. Flag states that look wrong but are fine.
- **Direct attention.** "Point out what the learner should notice" — observation needs prompting.
  A shifted shell prompt or a new file goes unseen unless you name it.
- **Keep every claim true.** If you say a run was faster because the cache was reused, make sure
  the learner did not just edit the file that invalidates the cache. Fabricated "notice that"
  moments teach the wrong model and are caught immediately.
- **Be repeatable.** "Repetition is not the best teacher — sometimes it's the only teacher."
- **Work every time.** "A tutorial must inspire confidence. Confidence can only be built up layer
  by layer, and is easily shaken."

### What a tutorial must not do

- **Explain.** "A tutorial is not the place for explanation." A clause is fine — *"We're using
  HTTPS because it's more secure"* — with a link at the end. A paragraph is not.
- **Link out mid-lesson.** Every inline link is an invitation to leave and not come back. Links
  belong at the end.
- **Offer choices.** Alternatives, platform matrices, optional steps. Each is a decision the
  learner cannot make and a branch you cannot guarantee. Pick one path.
- **Generalize.** "By maintaining focus on the concrete and particular… the general and abstract
  will emerge." Minds extract patterns from examples on their own.
- **Be exhaustive.** *Usefully* complete — the actions, concepts and tools the learner needs.

### Language

Use: *We…* · *In this tutorial, we will…* · *First, do x. Now, do y.* · *Notice that…* ·
*Let's check…* · *The output should look something like…*

Avoid: *In this tutorial you will learn…* · *You may wish to…* · *Depending on your setup…* ·
*If this fails, try…* (fix the tutorial instead).

### Titles

Name the destination, not the subject. *Build and deploy your first pipeline* beats *Pipelines*.
Avoid "Getting started" unless it really is a lesson — that title is where install how-tos hide.

### Failure modes

1. **It is actually a how-to guide.** Does the reader already know what they want to accomplish?
   Then it is a how-to. A tutorial's reader does not yet know enough to have a goal.
2. **It over-explains.** Natural — once you understand something you reach for abstraction — but
   abstraction is exactly what the learner cannot yet parse.
3. **It has not been watched.** "You won't discover them all by yourself." Someone new must run it
   while you watch in silence.
4. **It rots quietly.** A product change forces rewrites along the whole narrative arc, not just
   one paragraph. Budget for it; test tutorials in CI where you can.

## How-to guides

**Goal-oriented. Action + application. Answers "How do I…?"**

> How-to guides are "**directions** that guide the reader through a problem or towards a
> result. How-to guides are **goal-oriented**."

The reader is at work, competent, and interrupted. They have a problem. Everything that does
not help them solve it is in the way.

### Checklist

Does the title start with "How to" and name a real task? Is competence assumed? Are alternatives
expressed as conditional imperatives rather than one rigid path? Does it link out for full option
lists instead of inlining them? Could a reader in a slightly different situation still follow it?

### What a how-to guide must do

- **Address a real, specific problem.** *How to calibrate the radar array*, not *How to build
  a web application*. Real user tasks, not tool operations.
- **Assume competence.** You are not teaching. Assumed knowledge is a feature: it is what keeps
  the guide short.
- **Use conditional imperatives.** *"If you want x, do y. To achieve w, do z."* This is the
  characteristic form of the mode, and it is what makes a guide adaptable to the reader's
  actual situation rather than only to your example.
- **Sequence for flow.** Order steps by both practical dependency and the way the reader thinks.
  Minimize context-switching; anticipate the next question before it is asked.
- **Omit.** "Practical usability is more helpful than completeness." Unlike a tutorial, a how-to
  need not run end to end, and need not cover every case.
- **Delegate.** *"Refer to the x reference guide for a full list of options."* This single move
  keeps how-tos lean and keeps reference authoritative.

### What a how-to guide must not do

- Teach fundamentals (tutorial's job), explain design decisions (explanation's job), or
  enumerate every option (reference's job).
- Describe mechanical operations divorced from purpose. "Turn the tap clockwise" is tool-focused;
  ground the guidance in what the human is actually trying to achieve.

### Language

Use: *This guide shows you how to…* · *If you want x, do y.* · *To achieve w, do z.* ·
*Refer to the x reference for a full list of options.*

Avoid: *In this guide you will learn…* · *Before we begin, it's worth understanding…* ·
*Here is the complete list of flags…*

### Titles

Start with "How to". This is not a stylistic preference — it is what makes the mode legible in
a nav and a search result.

- Good: *How to integrate application performance monitoring*
- Bad: *Integrating application performance monitoring* (is it instruction or description?)
- Very bad: *Application performance monitoring* (unclear it is instructional at all)

The title should complete "How do I…?" or "How do I… with…?"

### Failure modes

1. **It is really a tutorial.** If it starts by installing things and creating a project from
   scratch, it is teaching. Split or reclassify.
2. **It swallowed the reference.** A trailing "Options" table means the how-to has become the
   place people look things up, which starves the reference page. DRAIN it.
3. **Too broad to be actionable.** *How to configure the system* is a section, not a guide.
4. **A single rigid path.** Real problems vary. Conditional imperatives are what let one guide
   serve many situations.

Recipes are the model: they address a specific question, assume basic competence, exclude
teaching, and do not pretend to be a cookery course.

---

## Reference

**Information-oriented. Cognition + application. Answers "What is…?"**

> "The only purpose of a reference guide is to describe, as succinctly as possible, and in an
> orderly way."

Reference is the only mode not led by user need — it is led by the product. Users consult it
while working; they do not read it.

### Checklist

Does the structure mirror the product? Is every entry of a kind shaped the same? Are there zero
instructions and zero opinions? Is each entry a fact you can point at in the source, rather than
a plausible-looking guess? Does each entry have a small illustrative example?

### What reference must do

- **Mirror the product.** "The structure of the documentation should mirror the structure of
  the product," so the reader navigates both at once. If the code has modules, the reference
  has modules. Do not impose a narrative order.
- **Be austere.** "Neutrality, objectivity, factuality." No persuasion, no speculation, no
  marketing, no hedging. The reader needs certainty.
- **Be consistent.** Every entry of the same kind has the same shape — same fields, same order,
  same level of detail. Predictability is what makes reference scannable.
- **State facts.** *Net weight: 1000g.* *You must not apply b unless c.* *Default: `false`.*
  *Raises `ValueError` if n is negative.*
- **Be complete within its scope — with what is true.** Completeness is a real obligation here: a
  missing flag makes the reader distrust the page. But that pressure is exactly what tempts you to
  fill gaps with plausible invention, and an invented default is indistinguishable from a real one
  to every future reader. When the source does not give you a fact, write
  `TODO(verify): <what is missing>` and carry it into the summary. Narrow the stated scope rather
  than widening the guesswork.
- **Include examples that illustrate.** Show usage; do not walk the reader through it. See
  `examples.md`.
- **Carry warnings and limits.** Constraints, deprecations, version applicability.

### What reference must not do

Instruct, explain, interpret, editorialize, or speculate. When description feels insufficient
and you are tempted toward instruction — link to the how-to instead. That temptation is the
signal that the how-to should exist.

### Titles and structure

Name the thing. *Configuration file*, *CLI*, *`Client` class*, *Error codes*. Nouns, not verbs.

Common structures: alphabetical (glossaries, error codes), product-mirroring (API, modules),
or task-surface-mirroring (CLI commands, config keys). Tables and definition lists carry
reference well; long prose does not.

### Failure modes

1. **Assuming generated docs are enough.** Autodoc output is reference, but reference is more
   than autodoc output: CLI, configuration, file formats, error codes, environment variables,
   limits and compatibility matrices are usually hand-written. See `architecture.md` for how
   generated and hand-written reference coexist.
2. **Docstrings that teach.** A docstring full of narrative becomes a bad tutorial embedded in
   the API reference. Keep them descriptive; link out.
3. **Inconsistent entries.** Three fields on one function and eight on the next reads as
   incompleteness even when it is not.
4. **No examples at all.** Austere does not mean bare. A short illustrative snippet per entry
   is reference, not instruction.

---

## Explanation

**Understanding-oriented. Cognition + acquisition. Answers "Why…?"**

> Explanation is "a discursive treatment of a subject, that permits *reflection*."

It is the mode read away from the keyboard. It "joins things together" — the connective tissue
that turns a pile of facts into understanding. It is "less urgent than the other three" but
"no less *important*. It's not a luxury."

### Checklist

Does the page answer a stated *why*? Are alternatives and trade-offs discussed? Are there zero
numbered procedures and zero exhaustive tables? Does it link to the tutorial, how-tos and
reference it contextualizes?

### What explanation must do

- **Answer a why.** Anchor every page to a real or imagined *why* question. This is also the
  fix for the mode's characteristic scope problem: unlike the other three, explanation has no
  natural boundary, so the question supplies one.
- **Give context.** "Design decisions, historical reasons, technical constraints."
- **Make connections.** Within the subject and beyond it — comparisons to other tools,
  relationships between components, the shape of the problem domain.
- **Discuss alternatives.** "Explanation can and must consider alternatives, counter-examples
  or multiple different approaches."
- **Admit opinion.** Uniquely among the modes, explanation may take a position and weigh
  contrary ones, "since all human activity and knowledge is invested within opinion."

### What explanation must not do

Instruct, or list facts. When "instruction and technical description creep in," they
"interfere with the explanation itself, and remove them from view in the correct place" —
you damage the explanation *and* you hide the how-to and the reference where nobody will
find them.

### Language

Use: *The reason for x is that historically, y…* · *W is better than z, because…* ·
*Some users prefer w; this can be a good approach, but…* · *This is a trade-off between…* ·
*It may be helpful to think of x as…*

Avoid: numbered steps, complete option lists, *first… then… finally…*

### Titles

Titles should read with an implicit "About" in front: *About user authentication* rather than
*User authentication*. Explicit *Why…* titles are excellent when the page really answers one.
The section itself need not be called "Explanation" — *Discussion*, *Background*,
*Concepts*, *Topics* all work.

### Failure modes

1. **It is a feature list.** The commonest impostor. Test each page: does it answer a *why*?
   If it says *what*, it is reference.
2. **Unbounded scope.** Symptom: the page keeps growing and nobody can say when it is done.
   Fix: name the question it answers, in the page, and cut what does not serve it.
3. **Treated as optional and starved.** Then how-tos bloat, because the *why* has to live
   somewhere and it ends up wedged into procedures.
4. **Written for the author, not the reader.** Architecture-diagram-as-explanation only explains
   to people who already understand.

---

## The four boundaries

The failure is never random — modes blur along their shared axes, and each pair blurs in a
characteristic way. Knowing which boundary you are standing on tells you which move to make.

| Boundary | Shared axis | How it blurs | The test |
| --- | --- | --- | --- |
| Tutorial ↔ How-to | both are action | A tutorial acquires choices and edge cases; a how-to starts from scratch | Does the reader already have a goal? Yes → how-to. |
| Reference ↔ Explanation | both are cognition | Explanation drifts into enumeration; reference drifts into rationale | Does it answer *what* or *why*? |
| Tutorial ↔ Explanation | both are acquisition | The tutorial pauses to explain | Is the reader's hand on the keyboard right now? |
| How-to ↔ Reference | both are application | The how-to grows an options table | Is the reader executing a sequence, or looking one thing up? |

The diagonals (tutorial ↔ reference, how-to ↔ explanation) share no axis and rarely blur. When
they seem to, the page is usually three things, not two.

---

## After any rewrite

Is the mode obvious from the title alone? Would a reader arriving from a search engine, mid-page,
know what kind of page they are on? Does any fact on this page also live on another page — and if
so, which copy is canonical? Is everything you asserted traceable to the source material, with
anything you inferred marked `TODO(verify)`?
