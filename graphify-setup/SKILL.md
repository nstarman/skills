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

Follow the steps in order. The order is not cosmetic: the scope and the rebuild hook have to exist
*before* the graph that gets committed is built, or you commit a graph the hook immediately rewrites.

## What the finished wiring looks like

| | Where | What it does |
|---|---|---|
| 1 | `.gitignore`, `.gitattributes` | tracks `graphify-out/graph.json` and nothing else from that folder, and marks it generated |
| 2 | `.graphifyignore` | fixes what is indexed, so every rebuild anywhere produces the same graph |
| 3 | the repository's commit-check config | rebuilds the graph when code changes, pinned to one release |
| 4 | `.github/workflows/graphify.yml` | weekly: opens a pull request if the graph drifted |
| 5 | `<agent-guidance-file>`, `CONTRIBUTING.md`, `README.md`, docs | tells agents and humans the graph is there |

Five committed artefacts, plus one thing that **cannot** be committed: the merge driver, which is a
per-clone `git config` (step 7). Git deliberately refuses to take a merge-driver command from a
tracked file, so it is documented in CONTRIBUTING for every contributor to run once. Don't go
looking for it in the repository, and don't count it when you describe what the change adds.

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

## What the graph is reproducible across, and what it is not

Pin, `PYTHONHASHSEED=0`, `.graphifyignore` and `--force` buy you a graph that is byte-identical **on
one platform, from a plain clone**. They do not buy more than that:

| same | result |
|---|---|
| same OS, plain clone, same pin | byte-identical, warm cache or cold, across independent clones |
| different OS | a few edges missing, nothing else: 3 of 9,674 on a 5,000-node repository |
| git worktree instead of a clone | far worse: hundreds of community names, and some edges reclassified |

The two are different faults, and it is worth knowing which is which:

- **Across operating systems, clustering is perfectly stable and edge extraction is not.** Measured
  on a 5,000-node repository: identical node ids, identical community ids, identical community
  names, and exactly three `imports_from` edges that macOS emits and Linux does not — a pure
  omission, with nothing added and nothing reclassified.
- **In a worktree, the instability is broader**, because `.git` is a file rather than a directory
  and gets scanned as one more entry: hundreds of community names move and some edges change
  relation. It also varied between runs.

Treat both as how the tool behaves today. Three things follow, and the runbook depends on all three:

- **Never gate CI on a rebuild.** A job that rebuilds and compares fails permanently for everyone
  not on the platform that built the committed graph.
- **A repository-wide "run every hook over every file" job must skip this hook** (step 5). That is
  the shape of gate that will bite: it passes on your machine and fails in CI.
- **The weekly job will occasionally normalise the graph to its own platform** (step 10). It is a
  real pull request that changes three edges and nothing else. Expected, not a bug — but say so in
  the pull request, or a reviewer will read it as one.

The commit hook is therefore the only place the rebuild is enforced, and a graph a few edges off is
accepted rather than fought.

---

## Runbook

### 1. Install the pinned tool and look before you wire

```bash
uv tool install "graphifyy==<version>"   # or run it with uvx, as above
cd <repo>
PYTHONHASHSEED=0 graphify extract . --code-only
```

**This graph is a survey, not the one you commit.** You are building it to find out what graphify
indexes in this repository, which is what step 2 needs. The graph that gets committed is built in
step 8, after the scope and the hook exist.

**Check**: read `graphify-out/GRAPH_REPORT.md`. Two questions. Is anything indexed that should not
be — names, paths, anything the graph should not carry? And what is in there that is not code? On
one repository a quarter of the graph was YAML keys from forty near-identical CI workflows. Both
answers go into step 2.

### 2. Pin the scope in `.graphifyignore`

`graphify update` has **no** `--code-only` flag, and the scope `extract --code-only` used is
remembered in `graphify-out/.graphify_analysis.json`, which step 3 does not track. So a fresh
clone — which is what CI and the drift workflow are — rebuilds with a wider scope: on a
5,000-node repository that was about 950 extra nodes from 127 Markdown files, some of them down a
path that wants an API key. The committed graph is then not reproducible and the weekly job opens a
pull request on every run.

Write the scope into `.graphifyignore`, which is committed and which both `extract` and `update`
honour (block: *graphifyignore*):

```gitignore
*.md
*.tex
*.bib
*.pdf
*.png
```

Add whatever step 1 showed as noise rather than code; `.github/` is a common entry.

**Check**: this is verified in step 8, once there is a committed graph to compare against.

### 3. Track the graph and nothing else

Append to `.gitignore` (block: *gitignore*):

```gitignore
graphify-out/*
!graphify-out/graph.json
```

**Check**: `git status --porcelain -uall graphify-out/` lists `graph.json` and no other path. The
`-uall` matters: without it git collapses the whole untracked directory to `?? graphify-out/` and
the check tells you nothing.

### 4. Mark it generated

Append to `.gitattributes` (block: *gitattributes*):

```gitattributes
graphify-out/graph.json merge=graphify linguist-generated=true -diff
```

`-diff` keeps it out of `git diff`, `linguist-generated=true` collapses it in pull requests, and
`merge=graphify` names the driver registered in step 7.

**Check**: after the first commit, `git diff HEAD~1` prints `Bin … bytes`, not graph contents.

### 5. Make room for it in the commit checks

The graph is one long line of compact JSON, a few megabytes, with no trailing newline. Standard
hooks will fight it, and they must be dealt with **before** the first commit:

- **a large-file check** (`check-added-large-files`, 500 KB by default) rejects it outright;
- **a JSON or general formatter** (prettier, and anything else that formats `.json`) reformats one
  line into hundreds of thousands, which destroys the whole point of the file;
- **`end-of-file-fixer`** appends the newline the tool does not write, so the hook and the tool
  rewrite the file in turn, forever;
- **a spell checker** may read it and flag typos in source identifiers — check whether this
  repository's configuration lets it see `.json` at all before excluding it.

`trailing-whitespace` and `mixed-line-ending` need no exclusion: they leave a single-line file with
no trailing space byte-identical.

Exclude `graphify-out/graph.json` from each hook that would touch it, or raise the size limit.
Block: *commit-check exclusions*.

Then look for a job that runs **every** hook over **every** file — a `lint` session, a `Format` CI
job, anything calling the hook runner with `--all-files`. It will rebuild the graph and fail for
anyone whose platform differs from the one that built it. Add `graphify-update` to whatever that job
already uses to skip hooks (`SKIP=graphify-update`, or the session's own skip list) — merging it
into any `SKIP` already set rather than replacing it, so a caller's own skips survive.

**Check**: run the repository's full check suite with the graph staged; nothing modifies or rejects
it. Then check the CI job that does the same thing over all files, because that one passes locally
and fails on another platform.

### 6. Rebuild the graph on every commit

Add the hook to the repository's committed commit-check configuration (block: *rebuild hook*). It
is a `local` hook pinned to `<version>`, with `pass_filenames: false`, `always_run: true`, and
`graphify update . --force` as its command.

`always_run: true` and `--force` are both load-bearing:

- **Without `always_run`, a commit that only deletes files does not rebuild the graph.** The hook
  runner passes only files that exist, so a deletion-only commit reports "no files to check" and
  skips — and the deleted code stays in the graph. `pass_filenames: false` does not help; the file
  filter still decides whether the hook runs at all. The cost of `always_run` is one no-op rebuild
  on commits that touch no code, around 13 seconds on a 5,000-node repository, and it makes any
  `exclude:` on this hook inert.
- **Without `--force` the rebuild is incremental, and an incremental rebuild drifts from a full
  one.** On a 5,000-node repository that was 5 stale nodes and 877 in a different community — so
  the committed graph accumulates cruft and the weekly job (step 10), which necessarily does a full
  rebuild on a bare checkout, opens a pull request every week on a healthy repository. With
  `--force` the hook's output equals a fresh-clone rebuild, which is what makes the drift check in
  step 10 meaningful.

Four more notes, since this is where the runbook leaves upstream's page:

- **The hook is committed, not installed per clone.** Upstream offers `graphify hook install` and a
  hand-written `.git/hooks/pre-commit`. Both are per clone, so they are missed by exactly the
  contributor who most needs them — and `graphify hook install` rebuilds *after* the commit, which
  leaves the refreshed graph uncommitted and is wrong when the graph is tracked.
- **Upstream's "skip when only the graph is staged" guard is gone**, deliberately: `always_run`
  overrides it. A second commit after staging the graph re-runs the rebuild, finds nothing to
  change and passes.
- **`entry: env PYTHONHASHSEED=0 …` assumes `env` is on `PATH`**, so the block is not
  Windows-safe as written.
- **The hook does not stage the result.** Like a formatter, it rebuilds and fails; you
  `git add graphify-out/graph.json` and commit again. Say this in CONTRIBUTING (step 12) or every
  contributor meets it as a mystery.

**Check**: step 13 exercises this. Nothing to check yet — there is no committed graph.

### 7. Register the merge driver

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

### 8. Build the graph you will commit

Now that the scope and the hook exist, build the real graph **with the command the hook runs**:

```bash
PYTHONHASHSEED=0 graphify update . --force
```

**In a normal clone, not a git worktree** — see the reproducibility table above. Agent sessions
often run in worktrees, so this is easy to get wrong.

Use `update`, not `extract` plus `cluster-only`: the two disagree, by about 90 nodes on a
5,000-node repository (because `extract` deduplicates and `update` does not) and with a fifth of
the nodes in a different community. Commit the wrong one and the first contributor's first commit
rewrites a fifth of the graph for nothing. And don't reach for `--no-label`: it leaves communities
named literally `Community 0`, so `graphify explain "AbstractQuantity"` reports
`Community: Community 213` where the `update` path reports `Community: AbstractQuantity`.

**Check, and do not skip this one**: clone the repository fresh into another directory, check out
this branch, and run the same command there. The two `graph.json` files must be byte-identical. One
check catches a scope still coming from the untracked cache, an incremental rebuild, and a graph
built in a worktree.

### 9. Commit the wiring and the graph

```bash
git add .gitignore .gitattributes .graphifyignore <commit-check-config> graphify-out/graph.json
git commit -m "chore: commit the graphify code graph"
```

**Check**: a fresh clone of the branch has `graphify-out/graph.json` and nothing else under
`graphify-out/`. A squash merge later does not touch the blob — the object on the branch tip and on
the default branch are the same — so there is nothing to redo after merging.

### 10. Watch for drift

Add `.github/workflows/graphify.yml` (block: *drift workflow*). Weekly and on demand, it rebuilds
with the pin read out of the commit-check config and, if the graph moved, opens or updates **one**
pull request against `<default-branch>`. It must never push to the default branch: the graph is
code-derived, but a bad rebuild is still a change nobody reviewed.

**Settle the token first.** `github.token` cannot open a pull request in many repositories, either
because it is read-only or because Actions is not permitted to. Where that is so, mint a token the
way this repository already does for bot pull requests — a GitHub App token works, and is the path
the block shows.

**Check**: step 13, after the merge.

### 11. Tell the agents

Add the rules block to `<agent-guidance-file>` (block: *agent rules*). It tells an agent to query
the graph before searching or reading source, how to refresh it, to repeat that rule in every
subagent prompt that explores code, when to skip the graph, and not to review the generated file.

If the repository has no such file, create `AGENTS.md`. If it has several, put the block in the one
the repository's own tooling reads and have the others point at it; do not maintain two copies.

**Check**: the block names the graph's path, the pinned refresh command, the subagent rule and the
skip conditions — all four, or an agent will do only the part it remembers.

### 12. Tell the humans

Three places, in descending length (blocks: *contributor section*, *README line*, *docs page*):

- **`CONTRIBUTING.md`** gets the real explanation: what the graph is, that parsing is local
  tree-sitter work and nothing leaves the machine, that each edge is marked as read from the source
  or inferred, the one-time merge-driver setup from step 7, the rebuild-and-stage loop from step 6,
  and every escape from the section below.
- **`README.md`** gets **one line** pointing at CONTRIBUTING. The README's readers are installing
  the package; a section selling someone else's tool is noise to them.
- **the documentation site** gets the CONTRIBUTING text on its contributing or development page, if
  it has one. Check first whether that page already includes `CONTRIBUTING.md` (an `{include}`
  directive or similar) — then it is there for free and there is nothing to write. If it does, any
  link you added to CONTRIBUTING must be an absolute URL, because repository-relative links break
  once the file is rendered inside the docs.

**Check**: read the README as someone who only wants to install the package. One line, pointing
elsewhere.

### 13. Verify, by breaking it

**These checks are not optional.** Wiring this profile into a repository the first time produced
four blocking defects, and every one of them surfaced here or in CI. None was visible by reading.

1. **A rebuild in a fresh clone is byte-identical** (step 8's check). The cheapest of these, and the
   one that catches the most.
2. **A commit that deletes code.** Remove a module and commit. The graph must shrink in that same
   commit — if the hook reports "no files to check", `always_run: true` is missing from step 6. In
   practice the rebuild writes the smaller graph without complaint, despite the flag that exists for
   refusing to; if it ever does refuse, `GRAPHIFY_FORCE=1` is the way through.
3. **A merge of two branches that both changed code.** Branch twice from one commit, change
   different files, commit both, merge. There must be no conflict in `graph.json`. To see that the
   driver is what did it, try the same merge in a clone without it registered: that one conflicts.
4. **A fresh clone answers a question**:
   `uvx --from graphifyy==<version> graphify query "how does X work"` with no build step first.
5. **The repository-wide check job.** Run whatever CI job runs every hook over every file, or run
   it locally the way CI does. It must not rebuild the graph. This is the check that passes on your
   machine and fails in CI, so it is worth doing before the pull request rather than after.
6. **The drift workflow**, which can only be done **after** the merge: GitHub exposes
   `workflow_dispatch` only for workflows already on the default branch, so `gh workflow run`
   cannot reach it from the branch. Dispatch it once it is merged. It should finish green, and
   either open no pull request or open one that normalises a few edges to the runner's platform.

Then open the pull request. Describe the five committed artefacts, not the commits.

---

## Escapes, which must end up in the repository

Every one of these belongs in the wired repository's CONTRIBUTING and agent rules. The skill is
read once, by whoever wires the repository; the repository is read by everyone afterwards.

| Situation | Escape |
|---|---|
| Commit without rebuilding | `SKIP=graphify-update git commit ...` — the hook runner's own mechanism |
| A rebuild refuses because the graph would shrink (rare; it generally just shrinks) | `GRAPHIFY_FORCE=1 git commit ...` |
| The graph conflicts on merge anyway | Rebuild rather than hand-edit: `rm graphify-out/graph.json && graphify update . --force && git add graphify-out/graph.json` |
| An automated commit runs where graphify is not installed | Install it in that job, or set `SKIP=graphify-update` for those commits |
| The graph has fallen behind the code | `PYTHONHASHSEED=0 uvx --from graphifyy==<version> graphify update . --force`, then commit it |

Never resolve a graph conflict by picking a side: the file is generated, so the answer is always to
rebuild it from the merged code. A union merge also leaves the graph slightly fat — a few more
nodes than a clean rebuild gives — which the next commit's rebuild cleans up on its own.

## Migrating a repository that builds the graph on demand

Some repositories ignore all of `graphify-out/` and rebuild it with a named task
(`nox -s graph` or similar). Convert it, do not wire it twice:

1. Replace the `graphify-out/` ignore line with the two lines from step 3, so the graph alone is
   tracked.
2. Work through the runbook from step 1, skipping nothing. Step 5 matters more here than in a fresh
   repository: an established one is the kind that has a large-file check, a formatter and a
   repository-wide lint job waiting.
3. **Keep the explanation that repository already has.** A repository on this older arrangement
   usually documented what the graph is better than a fresh one does; move that prose into the
   CONTRIBUTING section rather than replacing it with the block's wording.
4. Retire the on-demand build task. The hook now builds the graph, the report and the HTML on every
   commit, so a second build path is one more thing to keep pinned — and the two will drift. The
   naming pass is not a reason to keep it: it has no place in a committed graph. Keep the task only
   if it does something else the hook does not, such as a wiki build, and say so in the pull
   request.
5. Drop any instruction to run the build task from the agent rules and the docs.

**Check**: search the repository for the old task name. No hits outside the changelog.

## When the repository is shaped differently

- **A different commit-check tool.** The hook block is for `prek` / `pre-commit` configuration. For
  anything else, keep the four properties: committed rather than per clone, pinned to `<version>`,
  running even when no file matches, and failing rather than staging for you. Then point the drift
  workflow's `grep` at whatever file now holds the pin — it reads the version out of the
  commit-check config by name.
- **No shared commit checks at all.** Use upstream's `.git/hooks/pre-commit` script and say in
  CONTRIBUTING that every clone must install it. Weaker, and the weekly drift job is then the only
  thing keeping the graph honest.
- **Agent guidance under another name.** Step 11 covers it: one copy, others point at it.
- **No documentation site.** Skip the docs page. CONTRIBUTING and the README line are enough.
- **Several packages in one repository.** One graph at the repository root covers all of them;
  `graphify extract .` from the root is right. Do not wire each package.
- **A repository where the graph would be enormous.** Check `graph.json`'s size after step 1. Past
  a few megabytes, narrow `.graphifyignore` further before building the one you commit, rather than
  committing a graph nobody wants to pull.
