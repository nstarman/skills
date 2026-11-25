# What the graph is reproducible across, and what it is not

Read this once, before step 8 of [SKILL.md](../SKILL.md). It is the background behind three of the
runbook's instructions: why the committed graph is built in a fresh clone, why no CI job may gate on
a rebuild, and why the weekly drift job opens pull requests on a healthy repository.

**graphify's output depends on the set of files on disk, not just the tracked ones.** This is the
single most important property of the tool for this profile, and the least obvious. Pin,
`PYTHONHASHSEED=0`, `.graphifyignore` and `--force` buy you a graph that is byte-identical from a
**fresh clone with nothing generated in it** — and nothing beyond that:

| built the same way | result |
|---|---|
| same OS, fresh clone, nothing generated in it | byte-identical across independent clones, warm cache or cold |
| a checkout that has installed the package, run the tests or built the docs | identical nodes, edges and community *names*, but ~45% of nodes get a different community *id* |
| different OS | a few edges differ, nothing else: 3 of 9,674 measured |

Three faults, worth keeping apart:

- **A generated, gitignored file changes the graph even when no symbol comes from it.** Measured on
  a 700-node repository: adding a 24-line `_version.py` — which graphify extracts nothing from —
  moved 310 of 699 nodes to a different community id and reclassified one edge. **`.graphifyignore`
  cannot suppress this**: the scope file filters symbol extraction, not the directory walk, so an
  ignored-but-present file still perturbs ordering. This is the first thing anyone reaches for and
  it does not work.
- **A git worktree is just one case of the above.** `.git` is a file there rather than a directory,
  so the scan sees one more entry — and on its own that changes nothing. Worktrees got the blame
  earlier because a worktree is where an agent happens to have run a build. Once two trees hold the
  same files, a worktree and a clone agree exactly.
- **Across operating systems, clustering is stable and edge extraction is not.** Identical node ids,
  community ids and community names, and three `imports_from` edges present on macOS and absent on
  Linux — nothing added, nothing reclassified. The committed graph carries the flavour of whichever
  platform last built it; the difference runs both ways.

The diagnostic, when a rebuild does not match and you need to know why:

```bash
git status --porcelain --ignored -uall | grep '^!!' | grep -E '\.pyi?$'
```

Anything under `src/` there is a reason your rebuild will not match CI's.

**What this costs, said plainly.** Every package that generates a version file — anything on
hatch-vcs or setuptools_scm, which is most of them — has this the moment someone installs it. So a
contributor with a working environment rebuilds a different graph, their hook rewrites it, and they
commit that; the weekly job then normalises it back. In such a repository the drift pull request is
**not occasional, it is most weeks**. It is one line, generated, collapsed by GitHub and union-merged,
so it costs a click — but decide knowingly, and tell the repository so in CONTRIBUTING.


## The three consequences

The runbook depends on all three:

- **Never gate CI on a rebuild.** A job that rebuilds and compares fails permanently for everyone
  not on the platform that built the committed graph.
- **A repository-wide "run every hook over every file" job must skip this hook** (step 5). That is
  the shape of gate that will bite: it passes on your machine and fails in CI.
- **The weekly job will occasionally normalise the graph to its own platform** (step 10). It is a
  real pull request that changes three edges and nothing else. Expected, not a bug — but say so in
  the pull request, or a reviewer will read it as one.
