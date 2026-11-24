---
name: graphify-setup
description: >-
  Wire graphify (the code-knowledge-graph CLI, PyPI `graphifyy`) into a repository so the graph is
  committed, rebuilt on every commit, merged without conflicts, and found by both contributors and
  coding agents. Use when asked to add, set up, wire up or standardise graphify or a code graph /
  knowledge graph in a repository, to commit `graphify-out/graph.json`, to make a repository
  queryable by agents instead of grepped, or to make an existing graphify setup match the other
  repositories. Also use when a repository has `graphify-out/` but nothing in AGENTS.md,
  CONTRIBUTING.md or the docs says it is there, when a committed graph conflicts on merge or churns
  between contributors, or when a graph rebuild blocks a commit. Not for day-to-day graph queries:
  `graphify install` writes the vendor's own skill for that.
---

# Wire graphify into a repository

[graphify](https://github.com/Graphify-Labs/graphify) turns a repository into a queryable knowledge
graph with local tree-sitter parsing. This skill wires one repository so the graph is **committed**,
so every clone and every agent has it without a build step, and so the people and agents who should
use it are told it exists.

It does not teach graph queries. `graphify install` writes the vendor's own skill onto the reader's
machine and keeps it current; the only usage text here is the rules block that goes into the wired
repository, for agents arriving without that skill.

## What the finished wiring looks like

Five artefacts, in five places. A repository either has all five or is half-wired.

| | Where | What it does |
|---|---|---|
| 1 | `.gitignore`, `.gitattributes` | tracks `graphify-out/graph.json` and nothing else from that folder, and marks it generated |
| 2 | the repository's commit-check config | rebuilds the graph when code changes, pinned to one release |
| 3 | per clone: `git config merge.graphify.*` | union-merges the graph instead of conflicting |
| 4 | `.github/workflows/graphify.yml` | weekly: opens a pull request if the graph drifted |
| 5 | `<agent-guidance-file>`, `CONTRIBUTING.md`, `README.md`, docs | tells agents and humans the graph is there |

This is the one profile. Upstream's
[team-workflows guide](https://docs.graphify.com/guides/team-workflows) is its basis; where this
runbook departs from that page, the step says why. The older arrangement — `graphify-out/` ignored
and rebuilt on demand — appears here only as something to migrate away from.

## Conventions

`<version>` is the pinned `graphifyy` release, `<default-branch>` the repository's default branch,
and `<agent-guidance-file>` whatever that repository uses (`AGENTS.md`, `CLAUDE.md`, both). Replace
them; never leave a placeholder in a file you commit, and never copy another repository's name into
one.

Paste-in material lives in [references/blocks.md](references/blocks.md), one section per block. This
file holds the decisions and the order; that file holds the text. If they ever disagree, this file
is wrong.

## The pin

Every place that builds the graph uses **one** `graphifyy` release with **no optional extras**:

- the commit hook, where the version is written down (this is the pin's only home);
- the weekly workflow, which reads the version back out of that file rather than repeating it;
- any command this runbook gives a human or an agent, as
  `uvx --from graphifyy==<version> graphify ...`.

Two reasons, both learned the hard way. Without the `leiden` extra, clustering falls back to
networkx Louvain, and upstream warns that switching between the two "reshuffles every community" —
so one contributor with `graphifyy[leiden]` installed rewrites the whole graph on every commit they
make. And community numbering depends on hash ordering, so every build also needs
`PYTHONHASHSEED=0`.

Pin the release that is current when you wire the repository (0.9.119 at the time of writing).
Don't carry an old pin into a new repository: the graph records the version that built it.

---

## Runbook

### 1. Install the pinned tool and build the first graph

```bash
uv tool install "graphifyy==<version>"   # or run it with uvx, as above
cd <repo>
PYTHONHASHSEED=0 graphify extract . --code-only
PYTHONHASHSEED=0 graphify cluster-only . --no-label
```

`--code-only` keeps it to source files. `--no-label` skips the optional naming pass, which calls a
language model: hub-derived names are deterministic, model-written ones are not, and in a committed
graph a renamed community is a whole-file rewrite.

**Check**: `graphify-out/` now holds `graph.json`, `GRAPH_REPORT.md`, `graph.html` and some caches.
**Read `GRAPH_REPORT.md` before you commit anything.** The graph carries names and paths taken
from the source, and this is the moment to notice if it indexed something it should not have
(add a `.graphifyignore` if so).

### 2. Track the graph and nothing else

Append to `.gitignore` (block: *gitignore*):

```gitignore
graphify-out/*
!graphify-out/graph.json
```

**Check**: `git status --porcelain graphify-out/` lists `graph.json` and no other path.

### 3. Mark it generated

Append to `.gitattributes` (block: *gitattributes*):

```gitattributes
graphify-out/graph.json merge=graphify linguist-generated=true -diff
```

`-diff` keeps it out of `git diff`, `linguist-generated=true` collapses it in pull requests, and
`merge=graphify` names the driver registered in step 6.

**Check**: after the first commit, `git diff HEAD~1` does not print graph contents.

### 4. Make room for it in the commit checks

The graph is one long line of compact JSON, a few megabytes, with no trailing newline. Three kinds
of standard hook will fight it, and all three must be dealt with **before** the first commit:

- **a large-file check** (`check-added-large-files`, 500 KB by default) rejects it outright;
- **a JSON or general formatter** (prettier, and anything else that formats `.json`) reformats one
  line into hundreds of thousands, which destroys the whole point of the file;
- **`end-of-file-fixer`** appends the newline the tool does not write, so the hook and the tool
  rewrite the file in turn, forever.

Exclude `graphify-out/graph.json` from each of them, or raise the size limit. Block:
*commit-check exclusions*.

**Check**: run the repository's full check suite with the graph staged; nothing modifies or rejects
it.

### 5. Rebuild the graph on every commit

Add the hook to the repository's committed commit-check configuration (block: *rebuild hook*). It
is a `local` hook pinned to `<version>` with `pass_filenames: false` and
`exclude: ^graphify-out/`.

Three notes, since this is where the runbook leaves upstream's page:

- **The hook is committed, not installed per clone.** Upstream offers `graphify hook install` and a
  hand-written `.git/hooks/pre-commit`. Both are per clone, so they are missed by exactly the
  contributor who most needs them — and `graphify hook install` rebuilds *after* the commit, which
  leaves the refreshed graph uncommitted and is wrong when the graph is tracked.
- **`exclude: ^graphify-out/` is upstream's "skip when only the graph is staged" guard**, expressed
  in the hook runner's own matching rules instead of a shell test.
- **The hook does not stage the result.** Like a formatter, it rebuilds and fails; you
  `git add graphify-out/graph.json` and commit again. Say this in CONTRIBUTING (step 10) or every
  contributor meets it as a mystery.

**Check**: change a function, commit, and watch the hook rebuild and stop the commit; stage the
graph and commit again. The graph and the code it describes are now in one commit.

### 6. Register the merge driver

Once per clone, and it cannot be committed — git refuses to take a merge-driver command from a
tracked file, which is a security property, not an oversight:

```bash
PY="$(sed -n '1s/^#!//p' "$(command -v graphify)")"
git config merge.graphify.name "graphify graph.json union merge"
git config merge.graphify.driver "\"$PY\" -m graphify merge-driver %O %A %B"
```

Pointing at the interpreter rather than the `graphify` script means merges also work in GUI git
clients, where `PATH` is not the shell's.

**Check**: `git config merge.graphify.driver` prints the command. This step goes in CONTRIBUTING
as a one-time setup line, because every clone needs it.

### 7. Commit the wiring and the graph

```bash
git add .gitignore .gitattributes <commit-check-config> graphify-out/graph.json
git commit -m "chore: commit the graphify code graph"
```

**Check**: a fresh clone of the branch has `graphify-out/graph.json` and nothing else under
`graphify-out/`.

### 8. Watch for drift

Add `.github/workflows/graphify.yml` (block: *drift workflow*). Weekly and on demand, it rebuilds
with the pin read out of the commit-check config and, if the graph moved, opens or updates **one**
pull request against `<default-branch>`. It must never push to the default branch: the graph is
code-derived, but a bad rebuild is still a change nobody reviewed.

**Check**: run it by hand with the graph deliberately stale; it opens a pull request. Run it again;
it updates the same one.

### 9. Tell the agents

Add the rules block to `<agent-guidance-file>` (block: *agent rules*). It tells an agent to query
the graph before searching or reading source, how to refresh it, to repeat that rule in every
subagent prompt that explores code, when to skip the graph, and not to review the generated file.

If the repository has no such file, create `AGENTS.md`. If it has several, put the block in the one
the repository's own tooling reads and have the others point at it; do not maintain two copies.

**Check**: the block names the graph's path, the pinned refresh command, the subagent rule and the
skip conditions — all four, or an agent will do only the part it remembers.

### 10. Tell the humans

Three places, in descending length (blocks: *contributor section*, *README line*, *docs page*):

- **`CONTRIBUTING.md`** gets the real explanation: what the graph is, that parsing is local
  tree-sitter work and nothing leaves the machine, that each edge is marked as read from the source
  or inferred, the one-time merge-driver setup from step 6, the rebuild-and-stage loop from step 5,
  and every escape from the section below.
- **`README.md`** gets **one line** pointing at CONTRIBUTING. The README's readers are installing
  the package; a section selling someone else's tool is noise to them.
- **the documentation site** gets the CONTRIBUTING text on its contributing or development page, if
  it has one.

**Check**: read the README as someone who only wants to install the package. One line, pointing
elsewhere.

### 11. Verify, by breaking it

File checks prove nothing about a wiring. Do these four, in the repository you just wired:

1. **A commit that deletes code.** Remove a module and commit. The rebuild usually just shrinks the
   graph; if it refuses, because a rebuild with fewer nodes is not written by default, commit again
   with `GRAPHIFY_FORCE=1`. Either way, confirm CONTRIBUTING names that override.
2. **A merge of two branches that both changed code.** Branch twice from one commit, change
   different files, commit both, merge. There must be no conflict in `graph.json`. If there is, the
   driver is not registered in this clone (step 6).
3. **A fresh clone answers a question**:
   `uvx --from graphifyy==<version> graphify query "how does X work"` with no build step first.
4. **The drift workflow**, as in step 8.

Then open the pull request. Describe the five artefacts, not the commits.

---

## Escapes, which must end up in the repository

Every one of these belongs in the wired repository's CONTRIBUTING and agent rules. The skill is
read once, by whoever wires the repository; the repository is read by everyone afterwards.

| Situation | Escape |
|---|---|
| Commit without rebuilding | `SKIP=graphify-update git commit ...` — the hook runner's own mechanism |
| A rebuild refuses because the graph would shrink | `GRAPHIFY_FORCE=1 git commit ...`, or `graphify update . --force` |
| The graph conflicts on merge anyway | Rebuild rather than hand-edit: `rm graphify-out/graph.json && graphify update . && git add graphify-out/graph.json` |
| An automated commit runs where graphify is not installed | Install it in that job, or set `SKIP=graphify-update` for those commits |
| The graph has fallen behind the code | `PYTHONHASHSEED=0 uvx --from graphifyy==<version> graphify update .`, then commit it |

Never resolve a graph conflict by picking a side: the file is generated, so the answer is always to
rebuild it from the merged code.

## Migrating a repository that builds the graph on demand

Some repositories ignore all of `graphify-out/` and rebuild it with a named task
(`nox -s graph` or similar). Convert it, do not wire it twice:

1. Replace the `graphify-out/` ignore line with the two lines from step 2, so the graph alone is
   tracked.
2. Do steps 3 to 8 as written. Step 4 matters more here: an established repository is the kind that
   has a large-file check and a formatter waiting.
3. **Keep the explanation that repository already has.** A repository on this older arrangement
   usually documented what the graph is better than a fresh one does; move that prose into the
   CONTRIBUTING section rather than replacing it with the block's wording.
4. Retire the on-demand build task. The hook now builds the graph, the report and the HTML on every
   commit, so a second build path is one more thing to keep pinned — and the two will drift. Keep
   it only if it does something the hook does not (a wiki build, the naming pass), and say so in
   the pull request.
5. Drop any instruction to run the build task from the agent rules and the docs.

**Check**: search the repository for the old task name. No hits outside the changelog.

## When the repository is shaped differently

- **A different commit-check tool.** The hook block is for `prek` / `pre-commit` configuration. For
  anything else, keep the four properties: committed rather than per clone, pinned to `<version>`,
  not run when only the graph is staged, and failing rather than staging for you. Then point the
  drift workflow's `grep` at whatever file now holds the pin — it reads the version out of the
  commit-check config by name.
- **No shared commit checks at all.** Use upstream's `.git/hooks/pre-commit` script and say in
  CONTRIBUTING that every clone must install it. Weaker, and the weekly drift job is then the only
  thing keeping the graph honest.
- **Agent guidance under another name.** Step 9 covers it: one copy, others point at it.
- **No documentation site.** Skip the docs page. CONTRIBUTING and the README line are enough.
- **Several packages in one repository.** One graph at the repository root covers all of them;
  `graphify extract .` from the root is right. Do not wire each package.
- **A repository where the graph would be enormous.** Check `graph.json`'s size after step 1. Past
  a few megabytes, narrow what is indexed with `.graphifyignore` before committing it, rather than
  committing a graph nobody wants to pull.
