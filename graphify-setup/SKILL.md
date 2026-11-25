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

It does not teach graph queries: `graphify install` writes the vendor's own skill onto the reader's
machine, and the only usage text here is the rules block that goes into the wired repository, for
agents arriving without it.

Follow the steps in order. The order is not cosmetic — the scope and the hook must exist *before*
the committed graph is built, or you commit one the hook immediately rewrites.

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

This is the one profile, based on upstream's
[team-workflows guide](https://docs.graphify.com/guides/team-workflows); where the runbook departs
from that page, the step says why.

## Conventions

`<version>` is the pinned `graphifyy` release, `<default-branch>` the default branch, and
`<agent-guidance-file>` whatever the repository uses (`AGENTS.md`, `CLAUDE.md`, both). Replace them;
never leave a placeholder in a committed file, and never copy another repository's name into one.
Paste-in material lives in [references/blocks.md](references/blocks.md), one section per block: this
file holds the decisions and the order, that one holds the text, and if they disagree this one is
wrong.

## The pin

Every place that builds the graph uses **one** `graphifyy` release with **no optional extras**:

- the commit hook, where the version is written down (this is the pin's only home);
- the weekly workflow, which reads the version back out of that file rather than repeating it;
- any command this runbook gives a human or an agent, as
  `uvx --from graphifyy==<version> graphify ...`.

Two reasons. Without the `leiden` extra, clustering falls back to networkx Louvain, and switching
between the two "reshuffles every community", so one contributor who installed `graphifyy[leiden]`
rewrites the whole graph on every commit. And community numbering depends on hash ordering, so every
build also needs `PYTHONHASHSEED=0`. Pin the release current when you wire the repository (0.9.119
at the time of writing) rather than carrying an old pin in: the graph records what built it.

## What the graph is reproducible across, and what it is not

**graphify's output depends on the set of files on disk, not just the tracked ones.** A graph is
byte-identical only when rebuilt from a **fresh clone with nothing generated in it**, on the same
platform, with the same pin. A checkout that has installed the package, run the tests or built the
docs is not a canonical tree: on a 700-node repository a 24-line generated `_version.py`, which
contributes no nodes at all, moved 310 of 699 nodes to a different community id. `.graphifyignore`
cannot suppress it, a git worktree is just one case of it, and across operating systems a few edges
differ as well.

Read [references/reproducibility.md](references/reproducibility.md) before step 8: the measurements,
the diagnostic for when a rebuild does not match, and what this costs a repository whose package
generates a version file — in which the weekly drift pull request is most weeks, not occasional.

Three things follow, and the runbook depends on all three:

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

**Check**: `extract` does not write `GRAPH_REPORT.md` — only `cluster-only` and `update` do — so
read the graph itself. Count nodes per file:

```bash
python3 -c "
import json, collections
g = json.load(open('graphify-out/graph.json'))
c = collections.Counter(n.get('source_file', '(external)') for n in g['nodes'])
for path, n in c.most_common(40): print(f'{n:6d}  {path}')
print(len(g['nodes']), 'nodes total')"
```

Two questions. Is anything indexed that should not be — names, paths, anything the graph should not
carry? And what is in there that is not code? On one repository a third of the survey graph was
YAML mapping keys, on another a quarter was CI workflows. Both answers go into step 2. The key is
`source_file`, not `file_path`.

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
*.yml
*.yaml
*.md
*.svg
*.png
```

`*.yml` / `*.yaml` first, because for a Python library YAML is usually the biggest single source of
noise and it is pure mapping keys, not structure: on one repository that was 258 nodes from
`.github/workflows`, 58 from `mkdocs.yml` and 20 from the commit-check config. The glob beats a
`.github/` entry, which misses the root-level files. `*.svg` matters more than `*.png` — a favicon
is likelier than an image — and `--code-only` skips SVGs at step 1 while `update` indexes them
later, so their absence from the survey means nothing. Add `*.tex`, `*.bib`, `*.pdf` only in a
repository that has prose or a paper in it.

**After editing `.graphifyignore`, delete `graphify-out/` before rebuilding.** A scope change does
not invalidate the AST cache, so `update --force` will report "No code-graph topology changes
detected" and leave the old scope's graph in place — measuring nothing.

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

Two more hooks to look for, both common in a cookiecutter repository:

- **`check-useless-excludes`** (pre-commit's own `meta` repo) fails when an `exclude:` matches no
  file — so the exclusions you just added fail until `graph.json` is committed. Step 9 handles it;
  nothing to do here but expect it.
- **a repository-local grep hook** (`disallow-caps` and friends). It will read the graph and report
  a source identifier's spelling from inside a generated file, which is a confusing place to be told
  about it. Exclude it if it has hits.

Then find every gate that runs **all** hooks over **all** files. There are usually two, and only one
of them looks like a CI job:

- **pre-commit.ci**, configured by a `ci:` key in the very file you are editing — no workflow file,
  nothing in `.github/`, invisible to a search for `--all-files`. It is often a *required* check and
  it **autofixes by pushing a commit**, so without a skip it either fails every pull request or
  pushes a reshuffled graph into every branch. One line, in that same `ci:` block:

  ```yaml
  ci:
    skip: [graphify-update]
  ```

- **a `lint` session or `Format` job** calling the hook runner with `--all-files`. Add
  `graphify-update` to whatever it already skips, merging into any caller `SKIP` rather than
  replacing it. Grep for `SKIP` first: a repository that runs hooks over everything almost always
  skips something already (`no-commit-to-branch`, typically), and that line is both the gate and the
  shape of the fix.

**Check**: run the repository's full check suite with the graph staged; nothing modifies or rejects
it. Then check the CI job that does the same thing over all files, because that one passes locally
and fails on another platform.

### 6. Rebuild the graph on every commit

Add the hook to the repository's committed commit-check configuration (block: *rebuild hook*). It
is a `local` hook pinned to `<version>`, with `pass_filenames: false`, `always_run: true`, and
`graphify update . --force` as its command.

Check `default_stages` in that file first. Where it includes `pre-push`, this hook inherits it and
runs a second full rebuild on every push — one that can only report what the commit hook already
enforced, and that fails the push with nothing to fix in place. Pin it with `stages: [pre-commit]`,
which is probably what the repository already does for `no-commit-to-branch`.

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

**From a fresh clone with nothing generated in it** — see the reproducibility section above. Your
own checkout almost certainly does not qualify: installing the package writes `_version.py`, and
that alone moves nearly half the nodes to different community ids. So:

```bash
git clone --no-hardlinks <repo> /tmp/graph-build
cd /tmp/graph-build && git checkout <branch>
PYTHONHASHSEED=0 graphify update . --force
cp graphify-out/graph.json <your working tree>/graphify-out/graph.json
```

`--no-hardlinks` because cloning a local path shares the object store by default. **Commit the
fresh-clone flavour**, not your checkout's: a plain checkout is what CI and the drift job reproduce,
and committing the built-tree flavour makes the drift job fire on literally every run.

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

The wiring and the graph have to land in **one** commit, and there is a chicken-and-egg problem
getting there: the clone of step 8 has to see `.graphifyignore` before it can build the right graph,
but a wiring-only commit fails `check-useless-excludes`, whose patterns match nothing until
`graph.json` exists. Two phases, one commit:

```bash
# 1. the wiring, so the clone can see .graphifyignore
SKIP=graphify-update,check-useless-excludes git commit -m "chore: commit the graphify code graph" \
  .gitignore .gitattributes .graphifyignore <commit-check-config>
# 2. build in the clone (step 8), copy graph.json in, fold it into that same commit
git add graphify-out/graph.json && git commit --amend --no-edit
```

The amend runs the full hook set with the graph in the index, so the exclusions now match and the
rebuild hook gets its first real test — does the hook agree with the clone-built graph? Use
`SKIP=graphify-update` on the amend only if your checkout is built, and so cannot reproduce it.
`--no-verify` is not the answer: it skips the rebuild hook too, which is the one you want to run.

**Check**: a fresh clone of the branch has `graphify-out/graph.json` and nothing else under
`graphify-out/`. A squash merge later does not touch the blob — the object on the branch tip and on
the default branch are the same — so there is nothing to redo after merging.

### 10. Watch for drift

Add `.github/workflows/graphify.yml` (block: *drift workflow*). Weekly and on demand, it rebuilds
with the pin read out of the commit-check config and, if the graph moved, opens or updates **one**
pull request against `<default-branch>`. It must never push to the default branch: the graph is
code-derived, but a bad rebuild is still a change nobody reviewed.

**This job has two dependencies on the repository's shape, and the block as written satisfies
neither in a protected repository. Both are invisible until its first real run — which, per step 13,
cannot happen until after your pull request merges. Settle them now, by reading the rules rather
than waiting to be surprised.**

1. **A token that may open a pull request.** Read it, don't guess:
   `gh api repos/<owner>/<repo>/actions/permissions/workflow` and
   `gh api repos/<owner>/<repo>/actions/secrets --jq '.secrets[].name'`. Three cases, and the third
   is the common one in a library repository: `github.token` can do it (drop the app-token step);
   the repository already has an App or PAT for bot pull requests (use it); or it does **no** bot
   pull requests at all and there is nothing to copy. In that last case decide deliberately rather
   than inventing something — wiring a whole fleet of repositories, create **one** organization-level
   App or secret before the first one and have every workflow read it. Committing the app-token step
   against secrets that do not exist yet is defensible (the weekly run fails loudly at that step,
   which is the signal it is unconfigured), but choose it, and say so in a comment.
2. **Commits that satisfy the default branch's rules.** Read the ruleset, which takes two calls —
   the listing does not include the rules: `gh api repos/<owner>/<repo>/rulesets` then
   `gh api repos/<owner>/<repo>/rulesets/<id>`. Under a `required_signatures` ruleset the
   action pushes with plain git, so its commit is unsigned and the pull request it opens can only
   ever be merged with an administrator override — with every required check green and an approval
   recorded. `sign-commits: true` is the fix: it commits through the GitHub API, so GitHub signs it,
   and it attributes the commit to the app, which also clears a
   `require_extra_approval_for_unattributed_changes` rule. Confirm the input exists at the SHA you
   pin, not just in the major version:
   `gh api "repos/peter-evans/create-pull-request/contents/action.yml?ref=<sha>" --jq .content | base64 -d | grep -n sign-commits`
   (quote the `?ref=`, or zsh eats it). Check the ruleset for anything else a bot commit would trip.

Then **match the repository's commit-message convention** in the block's `commit-message` and
`title`. A `commitizen` hook or a `.czrc` means the message is validated: under
`cz-conventional-gitmoji`, `chore(graph): …` is rejected and `🧹 chore(graph): …` is required. The
action's own commit goes through the API and escapes local hooks, but the pull-request title becomes
the squash subject, so get it right.

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

Find the file first — `ls CONTRIBUTING.md .github/CONTRIBUTING.md docs/` — because `.github/` is a
common home and GitHub treats it identically. If it lives there, the README line's link needs the
`.github/` path (keep the link *text* as `CONTRIBUTING.md`, so the README still reads naturally), and
so does the agent-rules block's pointer. Match the file's own heading level, too: a CONTRIBUTING that
uses `#` for every section will nest the block's `###` wrongly.

- **`CONTRIBUTING.md`** gets the real explanation: what the graph is, that parsing is local
  tree-sitter work and nothing leaves the machine, that each edge is marked as read from the source
  or inferred, the one-time merge-driver setup from step 7, the rebuild-and-stage loop from step 6,
  and every escape from the section below. Add the line that stops the churn from reading as a bug:
  a rebuild that rewrites the graph in your checkout is expected if you have built the package —
  stage it and commit.
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

### 14. Keep the graph current if the branch moves

If the default branch moves while you are working, the rebase leaves the committed graph stale, and
the drift job would catch it a week later. Not optional even when the incoming commits look like
dependency bumps: five of them moved one graph from 697 nodes to 699, because `pyproject.toml` is
indexed.

```bash
git rebase origin/main
# rebuild in a fresh clone of the rebased branch (step 8) and copy graph.json in
git add graphify-out/graph.json && git commit --amend --no-edit
git push --force-with-lease
```

---

## Escapes, which must end up in the repository

Every one of these belongs in the wired repository's CONTRIBUTING and agent rules: this skill is
read once, by whoever wires the repository, and the repository is read by everyone after.

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

## When the repository is not the assumed shape

[references/other-shapes.md](references/other-shapes.md) covers two cases: **migrating** a
repository that ignores `graphify-out/` and rebuilds it with a named task, and the **variations** —
a different commit-check tool, no shared commit checks at all, agent guidance under another name, no
documentation site, several packages in one repository, a graph that would be enormous. Check it
before step 5 if this repository is not a `prek` / `pre-commit` one.
