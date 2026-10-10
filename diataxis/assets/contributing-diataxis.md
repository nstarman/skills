<!--
Drop-in section for a project's CONTRIBUTING guide or docs/about/contributing.md.
A restructure decays back to the mess it came from within a year unless the rule that produced
it is written down where contributors will see it. Replace the bracketed bits and ship it.
-->

## How our documentation is organised

Our docs follow [Diátaxis](https://diataxis.fr). Every page does exactly one of four jobs,
because a page that tries to teach *and* be looked up does neither well.

| Section | Serves | Answers | The reader is… |
| --- | --- | --- | --- |
| **Tutorials** | learning | "Can you teach me to…?" | new, at study, following along |
| **How-to guides** | a goal | "How do I…?" | competent, at work, interrupted |
| **Reference** | information | "What is…?" | at work, looking one thing up |
| **Explanation** | understanding | "Why…?" | away from the keyboard, thinking |

Anything that is not documentation *for practitioners* — changelog, contributor guide,
governance, support — lives in `[about/]` and is outside this scheme.

### Deciding where a page goes

Two questions:

1. Does it inform **action** (doing) or **cognition** (thinking)?
2. Does the reader need **acquisition** (study) or **application** (work)?

action + acquisition → tutorial · action + application → how-to ·
cognition + application → reference · cognition + acquisition → explanation

Ask them of each *section* of your page, not just the page. If different sections give
different answers, you are writing two pages — split them. That is normal and it is the most
useful thing this scheme does for you.

### What each mode must not do

- A **tutorial** must not explain, offer choices, or fail. If a reader can follow every step and
  not get the promised result, it is broken. It must run with no credentials, no cloud account
  and no placeholders to fill in.
- A **how-to** must not teach fundamentals or list every option — link to the reference instead.
  Titles start with "How to".
- **Reference** must not instruct or editorialise. Describe; mirror the product's own structure;
  keep every entry of a kind the same shape.
- **Explanation** must not contain procedures or exhaustive tables. It answers a *why*.

### House rules

- **One canonical home per fact.** A value with a type and a default lives in exactly one
  reference table; everywhere else links to it. If you are about to restate a default or repeat
  an explanation, link instead.
- **Never invent.** If you do not know a default, a flag or an error string, write
  `TODO(verify): …` rather than something plausible. An invented fact is indistinguishable from
  a real one to the next reader.
- **Expected output is real output.** Run it and paste what it printed.
- **Moving a page means adding a redirect.** `[<your mechanism>]` — CI will fail otherwise.

### Docs PR checklist

- [ ] This page is exactly one mode, and the title makes that obvious in a nav or a search result.
- [ ] It does not do the neighbouring mode's job (no explanation in the how-to, no instruction in
      the reference).
- [ ] Nothing here is duplicated from another page — I linked instead.
- [ ] Every fact is traceable to the source, or marked `TODO(verify)`.
- [ ] Any code block was run, and its output is what it actually printed.
- [ ] If I moved or renamed a page, there is a redirect.
- [ ] If it is a tutorial: no credentials, no branches, no placeholders, and I completed it myself
      from a clean state.

### Signs the structure is drifting

Raise an issue if you notice these — they are how doc sets slide back:

- A "Guides", "Advanced", "Concepts" or "Misc" section appearing. Those are difficulty levels and
  dumping grounds, not modes.
- A how-to growing an options table at the bottom. That table belongs in the reference.
- The same paragraph appearing on a third page.
- A tutorial acquiring a troubleshooting section — it means the tutorial does not reliably work.
- Anyone answering the same question in issues twice. That is a missing page, and the answer they
  typed is its first draft.
