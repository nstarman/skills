# Implementation Plan: One hybrid-compute skill with per-cluster profiles

**Branch**: `005-hybrid-compute` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-hybrid-compute/spec.md`

## Summary

Merge `engaging-hybrid-compute` and `submit-hybrid-compute` into one local skill,
`hybrid-compute/`, whose `SKILL.md` carries the cluster-independent workflow once and whose
`clusters/<name>.md` files carry only what differs per site. Add the two missing cluster-independent
sections — the git/rsync reviewability rule and the phase-boundary squash procedure — to the shared
workflow. Delete the two old folders, collapse the duplicated shell scripts to one parameterised
copy each, point `tests/test_hybrid_compute.py` at the single skill, and regenerate the registry
outputs.

The whole change is content plus a small amount of test surgery. No new scripts, no new tooling, no
schema change.

## Technical Context

**Language/Version**: Markdown (skill content) and Bash for the shipped scripts; Python 3 standard
library for the repository's own tooling and tests.

**Primary Dependencies**: None added. The existing `scripts/skillreg.py`, `scripts/build_index.py`,
`scripts/release_zips.py` and `scripts/personal_check.py` already handle this shape unchanged (see
[research.md](./research.md)).

**Storage**: Files in the repository. `index.json`, `.claude-plugin/marketplace.json` and the
README's marked sections are generated.

**Testing**: `python -m unittest discover tests`, plus
`python scripts/build_index.py --check --remote` and `claude plugin validate .` as CI runs them.
`tests/test_hybrid_compute.py` exercises the shipped scripts with PATH stubs for `ssh`, `uv`,
`timeout`, `sleep` and `osascript`.

**Target Platform**: The skill is installed into Claude Code (marketplace), claude.ai (release zip)
or by copying the folder. Its scripts run on macOS/Linux locally and on Slurm login nodes.

**Project Type**: Agent-skill registry. Single local skill folder plus the repository's generated
outputs and unit tests.

**Performance Goals**: Not applicable. The relevant budget is reading length: `SKILL.md` must stay
under the 500-line soft limit `skillreg.SKILL_MD_LINES` warns at, and the skill's `description` under
the 1024-character claude.ai limit.

**Constraints**:

- Skills install individually and nothing expresses a dependency between them, so the one skill must
  be self-contained.
- Every site-specific fact in the two retired skills must survive into the matching profile.
- No personal details anywhere; placeholders such as `<kerb>` only.
- The two Engaging-only helper scripts keep the file names they are installed under
  (`engaging-connect` calls `duo-askpass` by name), so they cannot be renamed to mark their site.

**Scale/Scope**: One new skill folder (about 6 files), two folders deleted (12 files), one test file
reworked, three generated outputs refreshed. Two clusters today; the shape is chosen for dozens.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — still passing.*

| Principle | Check | Status |
|---|---|---|
| I. One source per skill | One local folder `hybrid-compute/` with its `SKILL.md`; name unique across folders and `registry/`. The retired names are removed outright, not left as entries pointing at nothing. | Pass |
| II. Generated outputs never hand-edited | `index.json`, `.claude-plugin/marketplace.json` and the README's marked sections come from `scripts/build_index.py`; the plan never edits them directly. | Pass |
| III. Validated against the source | `SKILL.md` frontmatter `name` equals the folder name; `description` within 1024 characters. `card.json` has exactly `name` and `description`. Checked by `build_index.py --check`. | Pass |
| IV. Installable three ways | `release_zips.py` zips the folder with `rglob`, so `clusters/` and `scripts/` are included and `card.json` excluded; marketplace and folder-copy install need nothing new. | Pass |
| V. `index.json` is a public contract | One entry replaces two. No field added, removed or redefined, so `schema` stays `1`. The website collector sees one fewer skill, which it already handles. | Pass |
| VI. Small and dependency-free | No new scripts. The reworked test stays standard-library `unittest` with PATH stubs. | Pass |
| VII. Published skills only | `hybrid-compute` is meant for others to install. | Pass |

Repository rules: squash merge; the skill gets a `card.json`; the next dated release picks the
change up automatically because the zip contents change.

No violations, so there is no Complexity Tracking section.

## Project Structure

### Documentation (this feature)

```text
specs/005-hybrid-compute/
├── spec.md              # approved specification
├── plan.md              # this file
├── research.md          # Phase 0: decisions and what the existing tooling already supports
├── quickstart.md        # Phase 1: how to verify the change end to end
├── checklists/
│   └── requirements.md  # spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

No `data-model.md` and no `contracts/`: the spec's Key Entities already describe the four content
roles, and this change alters no interface. The `index.json` contract lives in
`specs/001-skills-registry/contracts/` and is untouched. This follows
`specs/003-quarto-revealjs/`, the closest precedent, which is also a skill change.

### Source Code (repository root)

```text
hybrid-compute/
├── SKILL.md                    # the shared workflow; entry point, lists the profiles
├── setup.md                    # cluster-independent one-time setup
├── card.json
├── clusters/
│   ├── engaging.md             # Engaging: connecting, storage, partitions, site breakage
│   └── submit.md               # subMIT: the same four headings
└── scripts/
    ├── run_modes.sh            # one copy; partition and paths are marked placeholders
    ├── push_results.sh         # one copy; the clone path is a marked placeholder
    ├── watch_jobs.sh           # one copy; host and repo become required arguments
    └── engaging/
        ├── engaging-connect    # Engaging only, installed name unchanged
        └── duo-askpass         # Engaging only, installed name unchanged

tests/test_hybrid_compute.py    # retargeted at the single skill

engaging-hybrid-compute/        # deleted
submit-hybrid-compute/          # deleted

index.json                      # regenerated
.claude-plugin/marketplace.json # regenerated
README.md                       # generated sections refreshed
```

**Structure Decision**: One local skill folder, with site-specific content isolated two ways — prose
in `clusters/<name>.md`, one file per cluster, and site-only scripts in `scripts/<cluster>/`. A
cluster's prose profile is one file so that adding a cluster is one file; the `scripts/<cluster>/`
subfolder exists only for clusters that need their own helpers, which today is Engaging alone. The
subfolder is what marks those two scripts as Engaging's without renaming them, satisfying FR-008
under the constraint that `engaging-connect` invokes `duo-askpass` by name.

The shared scripts stay templates the reader copies into their own repository and edits, as they are
today. `sbatch` directives cannot take shell variables, so the partition and resource lines remain
marked placeholders; the cluster profile is what tells the reader which values to put there.

## Phase 0: Research

See [research.md](./research.md). It records the three decisions taken with the author before the
spec (one skill rather than generated per-cluster skills; squashing at phase boundaries on `main`
rather than moving results to a branch; retiring the old names without stubs), and the findings that
mean no repository tooling has to change: `discover_local` only requires a top-level folder with
`SKILL.md` and `card.json`, `write_zip` includes subdirectories, and `personal_check.py` walks the
whole tree.

## Phase 1: Design

See [quickstart.md](./quickstart.md) for the verification path: the content checks that prove no
workflow paragraph is duplicated and that every site-specific fact survived, then the mechanical
checks (unit tests, index freshness, plugin validation, personal-details check).

Design decisions beyond the structure above:

1. **`SKILL.md` opens with the cluster pointer.** First instruction: read `clusters/<name>.md` for
   the cluster in use, with the known profiles listed by name and a line on what to do when the
   cluster has no profile yet (work from the nearest one and write a new one).
2. **The shared workflow refers to profile values, never to one cluster's.** Where today's text says
   `mit_quicktest` or `/work/submit/<kerb>`, the shared text says "the short-test partition your
   profile names" or "the project filesystem your profile names".
3. **Each profile has the same four headings** — Connecting, Storage, Partitions and caps,
   Site-specific breakage — so a new cluster has a form to fill in and a reader knows where to look.
4. **The two new sections live in `SKILL.md`.** The transport rule sits next to the daily loop,
   because the loop's review-before-pull step is its justification. The squash procedure sits in
   Bookkeeping, next to the end-of-phase cleanup it extends.
5. **Setup splits by variance, not by convenience.** Local SSH key, deploy key, branch ruleset, repo
   layout, `.gitignore`, the project `CLAUDE.md` block and end-of-phase cleanup stay in `setup.md`;
   account creation, storage tables, partition tables and the connection recipe move to the
   profiles.
6. **The test file drops its per-skill class generation.** With one skill the `for _skill in SKILLS`
   loop and the `ClusterScripts` mixin collapse into one `TestCase`; the `retargeted` helper stays,
   because the scripts still carry placeholder lines to rewrite.
7. **`watch_jobs.sh` takes host and repo as required arguments.** Today Engaging's copy defaults them
   to Engaging's values. With one copy there is no sensible default, and the existing tests already
   pass both explicitly.

## Risks

| Risk | Handling |
|---|---|
| A site-specific fact is lost in the merge | The quickstart lists a fact-by-fact diff of both retired `SKILL.md` and `setup.md` files against the new tree, run before the old folders are deleted. Delete last. |
| The merged `SKILL.md` crosses the 500-line warning | The real limit is `skillreg.SKILL_MD_LINES` = 500, which `build_index.py` warns at. **Delivered: `SKILL.md` 330 lines, `setup.md` 129, `engaging.md` 150, `submit.md` 140.** The pre-writing guess in this row was 200 for the workflow and 80 per profile; it was too low, because the two new sections are about 90 lines that existed in neither retired skill, and the merged "Submitting jobs well" and "Fair share" sections are the union of two versions rather than either one. Nothing was cut to meet a number that was never the constraint. |
| The trigger description stops firing on one cluster's name | The description names both clusters and the generic terms; the spec's FR-009 covers it, and `/speckit-analyze` or a manual read is the check. |
| Retiring the names breaks an install | Accepted and recorded in the spec's Assumptions. The author is the only user. |
