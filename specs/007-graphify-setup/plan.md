# Implementation Plan: graphify-setup skill

**Branch**: `claude/graphify-skill-docs-bcde3e` | **Date**: 2026-11-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-graphify-setup/spec.md`

## Summary

Add one local skill, `graphify-setup/`, whose `SKILL.md` is an ordered runbook for wiring
[graphify](https://github.com/Graphify-Labs/graphify) into a repository with the graph tracked in git,
and whose single `references/blocks.md` holds every block the runbook tells the reader to paste: the
rebuild hook, the drift workflow, the agent rules, the contributor section, the README line and the
docs-page addition.

The profile is upstream's own documented recipe, [Share a code graph with your team using
git](https://docs.graphify.com/guides/team-workflows), with five corrections found while reading a
repository already wired that way (see [research.md](./research.md)): pin the clustering engine and not
just the version, document the override for a commit that shrinks the graph, add the hook guards
upstream's shell version has and a hook-based one loses, drop a stale sentence about large diffs, and
raise the large-file commit check before the first graph is committed.

Content only. No script ships, no repository tooling changes, and the generated outputs are refreshed by
`scripts/build_index.py`.

## Technical Context

**Language/Version**: Markdown. Python 3 standard library for the repository's own tooling, unchanged.

**Primary Dependencies**: None added. `graphifyy` is the skill's subject, not a dependency of this
repository: nothing here installs, imports or tests against it. The runbook pins one `graphifyy`
release (0.9.119 at the time of writing) in the repository it wires.

**Storage**: Files in this repository. `index.json`, `.claude-plugin/marketplace.json` and the README's
marked sections are generated.

**Testing**: `python -m unittest discover tests`, `python scripts/build_index.py --check --remote`,
`claude plugin validate .` and `python scripts/personal_check.py`. No new unit test: `AGENTS.md`
requires one per script a skill ships, and this skill ships none. No end-to-end test either — that
pattern is for skills about fast-moving tools whose output can be asserted, and this skill's output is a
pull request against another repository.

**Target Platform**: Installed into Claude Code (marketplace), claude.ai (release zip) or by copying the
folder. The runbook acts on a Python repository on GitHub that uses pull requests, shared commit checks
and GitHub Actions.

**Project Type**: Agent-skill registry. One new local skill folder plus the regenerated outputs.

**Performance Goals**: Not applicable. The budget is reading length: `SKILL.md` under the 500-line
warning in `skillreg.SKILL_MD_LINES`, `description` under the 1024-character claude.ai limit.

**Constraints**:

- Nothing private: no repository, person, path or project name, since the skill is published. Verified by
  `scripts/personal_check.py`.
- Self-contained: skills install individually, so the runbook cannot defer to another skill here.
- Must not restate upstream's own agent guidance, which `graphify install` writes on the reader's
  machine; two copies of it would drift.
- One pinned version and one set of grouping options everywhere a graph is built, or the tracked graph
  churns between contributors.
- The skill is a runbook for an agent to execute, so each step has to say what to change and how to tell
  it worked, without assuming the agent can see the finished state of another repository.

**Scale/Scope**: One skill folder (`SKILL.md`, `references/blocks.md`, `card.json`), three generated
outputs refreshed, one spec folder. The runbook is written to be run once per repository, roughly ten
times, by an agent rather than by hand.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — still passing.*

| Principle | Check | Status |
|---|---|---|
| I. One source per skill | One local folder `graphify-setup/` with its `SKILL.md`. The name exists in neither the local folders nor `registry/`. Upstream's own skill is not copied in: it is installed by its own tool and only referenced. | Pass |
| II. Generated outputs never hand-edited | `index.json`, `.claude-plugin/marketplace.json` and the README's marked sections come from `scripts/build_index.py`. | Pass |
| III. Validated against the source | `SKILL.md` frontmatter `name` is `graphify-setup`, equal to the folder name and matching `[a-z0-9-]`; `description` under 1024 characters; `card.json` carries exactly `name` and `description`. Checked by `build_index.py --check`. | Pass |
| IV. Installable three ways | A plain folder: `release_zips.py` zips it with `rglob` (so `references/` is included, `card.json` excluded), and marketplace and folder-copy installs need nothing new. | Pass |
| V. `index.json` is a public contract | One entry added. No field added, removed or redefined, so `schema` stays `1`. | Pass |
| VI. Small and dependency-free | No script ships and none is added to `scripts/`. The skill is Markdown. | Pass |
| VII. Published skills only | Wiring graphify into a repository is useful to anyone using graphify, not internal tooling for this registry. | Pass |

Repository rules: squash merge; the skill gets a `card.json`; the next dated release picks it up because
a new zip appears.

No violations, so there is no Complexity Tracking section.

## Project Structure

### Documentation (this feature)

```text
specs/007-graphify-setup/
├── spec.md              # the specification
├── plan.md              # this file
├── research.md          # Phase 0: the profile decision and the five corrections
├── quickstart.md        # Phase 1: how to verify the skill, and the wiring it produces
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

No `data-model.md` and no `contracts/`: the spec's Key Entities already describe the four content roles,
and this change alters no interface. The `index.json` contract lives in
`specs/001-skills-registry/contracts/` and is untouched. This follows `specs/005-hybrid-compute/`, the
closest precedent.

### Source Code (repository root)

```text
graphify-setup/
├── SKILL.md             # the runbook: wire a repository, migrate one, repo variations, verify
├── card.json
└── references/
    └── blocks.md        # every paste-in block, in the order the runbook calls for it

index.json                      # regenerated
.claude-plugin/marketplace.json # regenerated
README.md                       # generated sections refreshed
```

**Structure Decision**: One reference file, not several. The runbook and the blocks are used in a single
pass over one repository — an agent that reaches step 4 needs the hook block, and by step 8 needs the
agent rules, with nothing in between that would make a second file worth loading separately. Splitting
the configuration snippets from the prose surfaces would only mean two files open at once for the whole
task. `SKILL.md` stays the decision-making text: what changes, in what order, and how to tell it worked;
`references/blocks.md` stays copy-paste material with no reasoning in it, so the two never disagree.

## Phase 0: Research

See [research.md](./research.md): why the tracked-graph profile wins over the untracked one, why the
rebuild belongs in the repository's shared commit checks rather than in a per-clone git hook, the five
corrections to upstream's recipe, and the confirmation that no tooling here needs to change
(`discover_local` wants only a top-level folder with `SKILL.md` and `card.json`; `write_zip` walks
subdirectories; `personal_check.py` walks the whole tree).

## Phase 1: Design

See [quickstart.md](./quickstart.md) for the verification path.

Design decisions beyond the structure above:

1. **One profile, stated as one.** `SKILL.md` opens with what the finished wiring looks like — five
   artefacts in five named places — and the untracked variant appears only as the starting state of the
   migration section. The spec forbids offering it as an equal option (FR-002), because a reader who
   picks differently per repository loses the uniformity that makes the pattern reviewable (SC-006).
2. **The pin has one home.** The version is written in the hook configuration; the scheduled job reads
   it back out of that file rather than repeating it, and every command the runbook gives a human or an
   agent to run names the same pin explicitly. The skill says to pin the release that is current when
   the repository is wired, with the version current at writing given as an example, so a reader is
   never told to install something older than the one the graph will record in itself.
3. **No optional extras in the pin.** The clustering engine is whatever the bare pin installs. The
   runbook says so, and says why, because the alternative — some contributors with the faster engine,
   some without — rewrites the whole graph on alternating commits.
4. **Every escape lives in the wired repository, not only in this skill.** The hook's skip switch, the
   override for a commit that shrinks the graph, and the recovery from a conflicted graph go into that
   repository's contributor section and agent rules. The skill is read once, by whoever wires the
   repository; the repository is read by everyone after.
5. **Verification exercises the two failures a maintainer meets first.** The runbook's last step makes a
   commit that deletes code and merges two branches that both changed code, rather than only checking
   that files exist.
6. **The README gets one line.** A pointer to the contributor section, not a section of its own: the
   README's readers are installing the package. The full explanation goes in the contributor section and
   the documentation site's contributing page.
7. **Departures from upstream's recipe are annotated in place.** Where the runbook differs — the
   repository's shared commit checks instead of `.git/hooks/pre-commit`, the added guards, no
   language-model naming pass — the reason is one sentence next to the step, so a reader comparing the
   runbook with upstream's page can tell a deliberate change from an outdated copy.
8. **Placeholders throughout.** `<version>`, `<default-branch>`, `<agent-guidance-file>`; no repository
   is named, including the ones this pattern came from.

## Risks

| Risk | Handling |
|---|---|
| The pinned version goes stale | Decision 2: the runbook pins what is current at wiring time and gives today's release as an example, so a stale number in the skill costs a reader nothing. The graph records the version that built it, and the weekly job is what notices drift. |
| Upstream changes its recipe | The runbook names the upstream page it tracks and annotates each departure (decision 7), so the two can be diffed by a reader rather than silently diverging. |
| `SKILL.md` crosses the 500-line warning | The runbook is ten steps plus two short sections; the paste-in material, which is the bulk, is in `references/blocks.md`. If `SKILL.md` approaches the limit, prose moves to the reference file, never the decisions. |
| The skill is followed in a repository whose shape differs | FR-014 is a named section: a different commit-check tool, a differently named agent-guidance file, no documentation site, several packages in one repository. Each gets the rule, not a worked example. |
| A tracked graph is committed without being read | The runbook's first-commit step says to read it first: it holds names and paths taken from the source. |
| An agent reads the runbook as a description rather than instructions | Each step is written as an action with a check, and the verification step fails loudly (a refused rebuild, a conflicted merge) rather than quietly. |
