# Phase 0 Research: graphify-setup skill

Sources: graphify's [README](https://github.com/Graphify-Labs/graphify) and its
[team-workflows guide](https://docs.graphify.com/guides/team-workflows); `graphify --help` from the
installed CLI; `graphifyy` metadata on PyPI (0.9.119 current, Python 3.11.5–3.14, 30 optional extras);
and two already-wired repositories, one on each profile, read to see which parts hold up.

## R1. Track the graph in git, or rebuild it on demand?

**Decision**: Track `graphify-out/graph.json`; leave the rest of the directory untracked.

**Rationale**: The point of the feature is that an agent arriving in a fresh clone uses the graph
(SC-002, SC-003). With the graph untracked, the agent rules would promise a graph that is not there
until somebody runs a build, and nothing prompts anybody to run it. Tracking it also matches upstream's
documented team recipe, so the repository is on the supported path rather than a local invention.

**Cost, stated rather than hidden**: a graph of a few megabytes, rewritten whole whenever code changes.
Since 0.9.86 it is one line of compact JSON, and `.gitattributes` keeps it out of `git diff` and
collapses it in pull requests, so the cost is repository size, not review attention.

**Alternatives considered**: (a) Untracked, built by a named task on demand — the profile one of the
read repositories uses. Cheaper in bytes, but it leaves the agent rules unenforceable and gives two
places to describe the graph. (b) A hosted graph over the vendor's service — removes the commit
entirely, but adds an account and a network dependency for every contributor and every agent.

## R2. What rebuilds the graph?

**Decision**: A hook in the repository's shared, committed commit-check configuration, pinned to one
`graphifyy` release.

**Rationale**: It is committed, so every contributor gets it from the repository's normal setup step
with nothing to install per clone, and the pin means the graph is always built by the same version.

**Alternatives considered**: (a) `graphify hook install`, which upstream offers — it writes into
`.git/hooks` per clone, and upstream's own guide warns that it rebuilds *after* the commit, leaving the
refreshed graph uncommitted, which is wrong when the graph is tracked. (b) The hand-written
`.git/hooks/pre-commit` upstream's guide gives instead — correct in behaviour, but per clone, so it is
missed by exactly the contributor who most needs it. (c) Rebuilding only in CI — the graph would then
never match the commit that changed the code.

**Departure recorded**: the merge driver still has to be registered per clone, because git will not take
a driver command from a committed file. That one step stays manual and goes in the contributor section.

## R3. Correction 1 — pin the clustering engine, not just the version

**Finding**: Without the `leiden` extra, clustering silently falls back to networkx Louvain, and
upstream notes that switching between them "reshuffles every community". The wired repository pins a
bare `graphifyy` in its hook, but its agent rules tell agents to run `graphify update .` from whatever is
on `PATH` — and `uv tool install "graphifyy[leiden]"` is a normal way to have installed it.

**Consequence**: alternating commits rewrite the whole graph with different community ids, which is
exactly the churn the tracked profile cannot afford.

**Decision**: The runbook pins one release with no extras, and every command it hands a human or an
agent names that same pin (`uvx --from graphifyy==<version> graphify update .`), so the hook, the
scheduled job and manual rebuilds all cluster identically.

## R4. Correction 2 — a rebuild that would shrink the graph can be refused

**Finding**: `graphify update --force` exists to "overwrite graph.json even if the rebuild has fewer
nodes" (also `GRAPHIFY_FORCE=1`). Probing 0.9.101 on a throwaway repository (R13), deleting a file that
took the graph from 9 nodes to 7 was written without `--force`, so the guard does not fire on every
shrink and the threshold is not documented.

**Decision**: Treat it as an escape, not as a certainty. The runbook's verification step deletes a
module and says the rebuild "usually just shrinks the graph; if it refuses, commit again with
`GRAPHIFY_FORCE=1`", and the override is written into the wired repository's contributor section and
agent rules. Promising a refusal that may not come would be worse than naming the way out of one.

## R5. Correction 3 — keep upstream's hook guards, in the runner's own terms

**Finding**: Upstream's shell hook skips when `GRAPHIFY_SKIP_HOOK=1`, skips when the graph is the only
staged change, and requires the graph to exist already. A hook expressed in a commit-check configuration
drops all three — but two of them already exist in the runner.

**Decision**: Use the runner's mechanisms rather than re-implementing the shell test.
`exclude: ^graphify-out/` is the "only the graph is staged" guard, because `prek` / `pre-commit` skips a
hook no staged file matches. `SKIP=graphify-update` is the skip switch, and is better than a bespoke
environment variable because it is the one contributors already know. The graph-must-exist case does not
arise on a fresh wiring, where step 1 creates it.

## R6. Correction 4 — the "expect a huge diff" line is stale

**Finding**: One wired repository's agent rules tell reviewers that a large `graph.json` diff is expected
and not to flag it. With compact one-line JSON plus `-diff` and `linguist-generated=true`, the diff is
one line and is collapsed in pull requests.

**Decision**: The agent rules this skill ships say the graph is generated and not to review it, and leave
out the obsolete reassurance.

## R7. Correction 5 — three standard hooks fight the graph, not one

**Findings**: A repository running `check-added-large-files` rejects anything over 500 KB by default, and
the tracked graph is comfortably larger. Worse, the probe (R13) showed `graph.json` is a single line with
**no trailing newline** — so two more standard hooks collide with it:

- a JSON or general formatter (prettier, which handles `.json` by default) reformats that one line into
  as many lines as the graph has tokens, which destroys the compactness the whole profile depends on;
- `end-of-file-fixer` appends the newline the tool does not write, so hook and tool rewrite the file in
  turn on every commit.

**Decision**: "Make room for it in the commit checks" is its own runbook step, before the first commit,
covering all three, with the exclusions written out in the blocks file. This is the correction most
likely to have cost a day of confusion in an established repository.

## R8. No language-model naming pass

**Decision**: Build the graph without the optional naming pass.

**Rationale**: Reproducibility. Hub-derived names come out of the deterministic build; the naming pass
needs a model, and its labels survive re-clustering only while the community signature matches, so they
are a churn source in a tracked graph. `PYTHONHASHSEED=0` on every build keeps the rest deterministic.

## R9. Where humans are told

**Decision**: The contributor section and the documentation site's contributing page carry the
explanation; the README carries one line pointing at it.

**Rationale**: The author's call, and the README's audience is installing the package, not contributing
to it. The explanation itself is worth keeping from the untracked-profile repository, which says it
plainly: parsing is local tree-sitter work, nothing leaves the machine, and every edge is marked as read
from the source or inferred.

## R10. The skill ships no script

**Decision**: Runbook plus paste-in blocks; no executable.

**Rationale**: The reader is an agent, which is the thing that would run a script anyway. Repositories
differ enough (which commit-check tool, where agent guidance lives, whether there is a documentation
site, one package or several) that a script would be mostly branches, and `AGENTS.md` requires a unit
test for every script a skill ships — a test for a program nobody needs.

## R11. The skill stops at the wiring

**Decision**: Day-to-day use of the graph is out of scope.

**Rationale**: `graphify install` writes the vendor's own agent skill onto the reader's machine and keeps
it current. The only usage text this skill ships is the rules block that goes into the wired repository,
which exists so an agent with no skill installed still queries the graph first.

## R12. This registry's tooling needs no change

**Confirmed by reading the scripts**: `skillreg.discover_local` takes any top-level folder with a
`SKILL.md` that is not in `NOT_SKILLS`, and reads the description from `card.json`;
`validate_offline` enforces `[a-z0-9-]{1,64}` names, the 1024-character description limit and the
presence of `card.json`, and warns over `SKILL_MD_LINES = 500`; `release_zips.write_zip` walks the folder
with `rglob` and skips only `card.json` and `.DS_Store`, so `references/` is included;
`personal_check.py` walks the whole tree. A plain folder with a `references/` subdirectory is exactly the
shape three existing skills already have.

## R13. What was checked against the real tool

Run against a throwaway three-file Python repository with `graphifyy` 0.9.101, because the runbook tells
other people to run these commands:

- `graphify extract . --code-only` then `cluster-only . --no-label` builds the graph, the report and the
  HTML with no model call and no network. `extract` alone already assigns communities; `cluster-only`
  regenerates the report.
- `graph.json` is one line, no trailing newline, and carries `schema_version`, `graphify_version` and
  `built_at_commit`. Its node/edge keys are `nodes` and `links`.
- `graphify update .` regenerates `graph.json`, `graph.html` and `GRAPH_REPORT.md` together, so a
  separate on-demand build task is redundant once the hook runs (R10, and the migration's step 4).
- `update` with no code change reports "no code-graph topology changes detected" and leaves the outputs
  alone, so an unrelated commit does not rewrite the graph.
- Deleting a file shrank the graph without `--force` (see R4).

## R14. What the first real migration changed

The runbook was then followed end to end against a repository on the untracked profile
(GalacticDynamics/unxt#1057, a 5195-node graph, `graphifyy` 0.9.119). Eight corrections came back,
four of which would have broken any repository following the first draft. All of them are now in the
skill:

1. **Step 1 built a graph the hook would immediately rewrite.** `extract --code-only` plus
   `cluster-only --no-label` and `graphify update .` disagree — about 90 nodes, because `extract`
   deduplicates and `update` does not, and a fifth of the nodes in a different community. Step 1 now
   ends with `update . --force`, the same command the hook runs, and `cluster-only` is gone.
   `--no-label` was also described wrongly here: it leaves communities named literally `Community 0`,
   `Community 1` (reproduced on the probe repository), rather than giving deterministic hub-derived
   names.
2. **`update` has no `--code-only`, and the scope lives in an untracked cache.** A fresh clone — CI,
   the drift job — therefore indexed about 950 extra Markdown nodes, some down a path that wants an
   API key, so the committed graph was not reproducible. `.graphifyignore` is now its own step and
   the sixth artefact, with a byte-for-byte cold/warm check.
3. **The hook never ran on a deletion-only commit.** The runner passes only files that exist, so the
   hook reported "no files to check" and the deleted code stayed in the graph — step 12's own first
   test, failing silently. The hook now carries `always_run: true`, which makes `exclude:` inert.
4. **An incremental rebuild drifts from a full one** (5 stale nodes, 877 reclustered), so the weekly
   job would have opened a pull request every week. The hook now runs `update . --force`, about 13
   seconds against 2.
5. **The workflow's pin `grep` matched the empty string**, so a comment mentioning the package
   became a second pin and broke the `uvx` call — on wording this skill encourages. Reproduced
   exactly; now `grep -oE 'graphifyy==[0-9]+(\.[0-9]+)*' | head -1`, failing loudly when empty.
6. **The workflow assumed a writable `GITHUB_TOKEN`.** Where Actions cannot open pull requests, the
   job cannot work; the step now says to use the repository's own convention for bot pull requests.
7. **A git worktree builds a different graph from a plain clone.** `.git` is a file there, which
   shifts the scan's tie-breaking: 933 different community names and nine flipped `__init__.py`
   edges, varying between runs, where four plain clones agreed byte for byte. Step 1 now says to
   build the committed graph in a normal clone — which matters because agent sessions default to
   worktrees. This is an ordering quirk inside graphify, worked around rather than reported.
8. **Smaller fixes**: `git status --porcelain` collapses an untracked directory, so step 3's check
   needs `-uall` (reproduced); `trailing-whitespace` and `mixed-line-ending` need no exclusion while
   `codespell` does; the drift job cannot be dispatched before it is on the default branch;
   `built_at_commit` is written by `extract` only, so the report's staleness hint is misleading and
   the agent rules now say to ignore it; a docs page that `{include}`s CONTRIBUTING needs nothing
   written, but then the links in CONTRIBUTING must be absolute; and a union merge leaves the graph
   a few nodes fat until the next rebuild.

What held up unchanged: the `.gitignore` pair, `-diff` / `linguist-generated=true`, the exclusions
for the large-file, newline and formatter hooks, the extras-free pin, and the merge driver — which
proved load-bearing, since the same merge in a clone without it conflicted.

## R15. The graph is not byte-reproducible across operating systems

Found by the migration's CI, after R14 was written, and the most consequential finding of the lot:
it undercuts an assumption the profile rests on.

Same source, same pin, same `PYTHONHASHSEED=0`, no extras, `--force` both sides:

| platform | nodes | edges | communities |
|---|---|---|---|
| macOS | 5195 | **9674** | 353 |
| ubuntu-latest | 5195 | **9671** | 353 |

Nodes and communities agree exactly. The three differing edges are `__init__.py` re-export
classifications flipping between `re_exports`/`export` and `imports_from`/`import` — the same
unsorted-iteration instability as R14's worktree finding, and the two are probably one bug inside
graphify. Not reported upstream, by the author's decision: the skill documents the behaviour and
works around it rather than carrying a to-do that every reader is nudged to chase.

**Decision**: accept it and state it, rather than change the profile. A graph three edges off is
still a graph every clone and every agent can query, which is the point (SC-002, SC-003). What the
skill now says:

- Reproducibility holds on one platform from a plain clone, and the limits are tabulated rather than
  implied.
- **Never gate CI on a rebuild.** A repository-wide "every hook over every file" job — the shape
  that broke in the migration — must skip the rebuild hook, because it passes locally and fails on
  another platform. This is now a step-5 instruction and its own verification in step 12, since the
  original step-5 check could not have caught it.
- The weekly job will occasionally normalise the graph to its own platform, and its pull-request
  body now says so, so a reviewer does not read three edges as a bug.
- The commit hook is the only place the rebuild is enforced.

**Alternatives considered**: (a) a tolerant drift check comparing node sets rather than bytes —
nodes are the stable part, so this would work, but it is custom logic in the workflow and would miss
genuine edge-only drift; (b) pinning the drift job to the maintainers' platform, which moves the
churn onto everyone else; (c) going back to an untracked graph, which gives up the thing the feature
is for. Worth revisiting (a) if a later graphify release does not settle the ordering.

## R16. After the migration merged

The migrated repository's pull request merged, which made the last unverified claim testable and
corrected an earlier one.

**The drift workflow works, and R15's account of the platform difference was wrong.** Dispatched on
the default branch, the job finished green and opened a pull request through a GitHub App token, so
the app-token path and `peter-evans/create-pull-request` are both confirmed; the skill's block is now
that shape rather than the hand-rolled `gh pr list` version. The pull request's diff was then read
directly, both blobs fetched and compared here rather than taken on report:

| | before (macOS-built) | after (Linux rebuild) |
|---|---|---|
| bytes | 5,107,628 | 5,106,814 |
| nodes | 5195, identical ids | 5195, identical ids |
| community ids and names | identical | identical |
| edges | 9674 | 9671 |

The three edges are `imports_from`, two in one module and one in another, **removed and not
replaced**: none added, none reclassified, no `__init__.py` involved. So R15's description — a
re-export classification flip — described the *worktree* fault, not the cross-platform one. The
correct statement is narrower and more alarming: across operating systems clustering is perfectly
stable and edge extraction is not. The skill now separates the two faults, and the wrong wording is
out of it.

**Four more things the merge settled:**

- A squash merge does not touch the committed blob: the object on the branch tip and on the default
  branch are the same. Worth a sentence in the skill, because "will a squash mangle a 5 MB generated
  file" is the obvious reader question.
- A fresh shallow clone of the merged default branch answers `graphify query` and `graphify explain`
  with no build step — the feature working end to end, in the state a new contributor or agent meets.
- `graphify explain` on that graph prints a hub-derived community name rather than `Community 213`,
  which is the concrete argument for building with `update` instead of `cluster-only --no-label`.
  That example is now in step 8.
- **The runbook's order was its biggest remaining defect.** It built the graph in step 1, wired
  everything around it, and committed it in step 7 — but what it committed was built before the
  scope and the hook existed, so a careful reader following it in order could not get a correct
  result. The runbook is now reordered: step 1 builds a graph explicitly labelled a survey, whose
  only job is to tell step 2 what to put in `.graphifyignore`; the graph that gets committed is
  built in step 8, after the scope, the exclusions and the hook are in place, with the hook's own
  command.

**Two reframings, both from living with it:**

- The merge driver is no longer counted as an artefact "in a place". It is the one thing that cannot
  be committed, and listing it beside five files that can is what sends readers looking for it in
  the repository. The skill now says five committed artefacts plus one per-clone exception.
- The verification section says outright that its checks are not optional, and that every blocking
  defect found while wiring the first repository surfaced there or in CI rather than by reading. It
  gained a sixth check — a byte-identical rebuild in a fresh clone — which on its own would have
  caught three of the nine findings.

## R17. Merging the drift pull request exposed a tenth finding

Found after the skill shipped, by merging the drift workflow's own pull request in the migrated
repository — a step nothing earlier had reached.

**The weekly job's pull request is unmergeable under a `required_signatures` ruleset.**
`peter-evans/create-pull-request` pushes with plain git, as would the hand-rolled `git commit` the
block carried before, so the bot's commit is unsigned. With all required checks green and a
non-author approval recorded, the merge was still refused: "the base branch policy prohibits the
merge". The same ruleset's `require_extra_approval_for_unattributed_changes` is tripped independently
by a bot commit.

**Fix**: `sign-commits: true` on the action's step. It commits through the GitHub API, so GitHub
signs the commit, and it attributes the commit to the app, which clears the unattributed-changes
rule too. Verified here that the input exists at `v8` and is documented as "Sign commits as
`github-actions[bot]` when using `GITHUB_TOKEN`, or your own bot when using GitHub App tokens",
rather than taken on report.

**What this changes in the skill**: step 10 now states that the job has **two** dependencies on the
repository's shape rather than one — a token that may open a pull request, and commits that satisfy
whatever the default branch requires — and says plainly that the block satisfies neither in a
protected repository, that both are invisible until the job's first real run, and that the first real
run cannot happen until the wiring pull request has merged. So they are to be settled by reading the
branch's rules, not by waiting to be surprised.

**And a framing correction carried with it.** R15 and R16 described the cross-platform difference as
edges "macOS emits and Linux does not", which reads as though one platform were canonical. Once the
Linux rebuild merged, the committed graph became the Linux build and the direction reversed: a macOS
contributor's next commit adds those three edges back. The skill now says the committed graph carries
the flavour of whichever platform last built it, and that the difference runs both ways. The
measurement is unchanged; the framing was misleading.

## R18. The first repository wired with the published skill

A second repository went through the runbook — the first using the released skill rather than the
draft, and the first that is not the one the skill was built against. Twelve findings; these are the
ones that changed the skill.

**The reproducibility story was wrong, and this is the important one.** R14 and R16 blamed git
worktrees. The real variable is **which files are on disk**: a fresh clone and a built checkout of
the same commit produce different graphs, and a worktree is merely where an agent happens to have
run a build. Isolated by adding files to a plain clone one at a time: a 24-line generated
`_version.py`, from which graphify extracts **no nodes at all**, moved 310 of 699 nodes to a
different community id and reclassified one edge. `.graphifyignore` cannot suppress it — the scope
file filters symbol extraction, not the directory walk — which was checked rather than assumed.
Reproduced here independently on a scratch clone.

The consequence is a real cost, now stated in the skill rather than implied: every package using
hatch-vcs or setuptools_scm has a generated version file the moment it is installed, so a
contributor with a working environment rebuilds a different graph, their hook rewrites it, and the
weekly job normalises it back. The drift pull request is **most weeks**, not occasional. The skill
says to commit the fresh-clone flavour, because that is what CI and the drift job reproduce, and to
tell the repository so in CONTRIBUTING so the churn does not read as a bug. The explanation moved to
`references/reproducibility.md`, with the diagnostic for a rebuild that does not match.

**Four blockers in the runbook itself:**

1. Step 1's check named `GRAPH_REPORT.md`, which `extract` does not write — removing `cluster-only`
   earlier removed the thing that wrote it, so the survey step's only check could not be performed.
   It is now a node-count-per-file one-liner over `graph.json`, which is a sharper instrument anyway.
2. `check-useless-excludes` (a cookiecutter default, so expect it in every repository) fails when an
   `exclude:` matches no file — so the wiring commit fails until `graph.json` exists, while step 8's
   clone needs `.graphifyignore` committed first. Step 9 now gives the two-phase recipe: commit the
   wiring with that hook skipped, then fold the graph into the same commit with `--amend`.
3. Step 5 missed **pre-commit.ci**, which is configured by a `ci:` key in the file being edited —
   no workflow, nothing in `.github/`, invisible to the search the step described — and which is
   often a required check *and* autofixes by pushing a commit. One `ci: skip: [graphify-update]`
   line. The step also now says to grep for an existing `SKIP`, since a repository that runs hooks
   over everything usually skips something already, and that line is both the gate and the fix.
4. The hook inherited `default_stages: [pre-commit, pre-push]` and ran a second full rebuild on every
   push, failing it with nothing to fix in place. `stages: [pre-commit]`.

**Six smaller ones**: the drift job's commit message must match a `commitizen` convention
(`🧹 chore(graph): …` under cz-conventional-gitmoji, where plain `chore(graph):` is rejected); step 10
needed a third case for a repository that does **no** bot pull requests at all, with the
recommendation that a fleet gets one organization-level App rather than discovering this on the
eighth repository, plus the two-call `gh api …/rulesets` recipe; `CONTRIBUTING.md` is often at
`.github/CONTRIBUTING.md`, which breaks the README line's link and the block's heading level; the
scope list led with a paper repository's patterns when `*.yml` / `*.yaml` is the near-universal rule
for a library and `*.svg` matters more than `*.png`; editing `.graphifyignore` needs
`rm -rf graphify-out` first, because a scope change does not invalidate the AST cache; and a rebase
mid-task needs a graph refresh, which is now step 14.

To stay under the 500-line limit, the reproducibility explanation and the migration/variations
sections moved into `references/`, leaving the runbook and its decisions in `SKILL.md`.
