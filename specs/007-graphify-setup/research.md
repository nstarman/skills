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
   worktrees. This looks like an upstream ordering bug worth reporting.
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
