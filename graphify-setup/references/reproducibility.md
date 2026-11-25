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

- **The hazard is a generated file *inside the indexed source tree*** — not a built checkout in
  general. A `.venv/`, a results file and a JAX cache added to one repository changed the graph not
  at all; a generated `src/<pkg>/_version.py` is what moves it. So the question to answer per
  repository is narrow: **does this package generate a version file?** `hatch-vcs` or
  `setuptools_scm` means yes; a static `version = "..."` in `pyproject.toml` means no, and then a
  working checkout and a fresh clone agree and the weekly drift pull request is rare rather than
  near-weekly. That difference is big enough to change whether the profile is worth wiring.
  Measured on a 700-node repository, adding a 24-line `_version.py` — which that repository
  extracted no nodes from, though another extracted one —
  moved 310 of 699 nodes (44%) to a different community id and reclassified one edge. But the
  magnitude does not generalise: on a 591-node repository the same file moved **no** communities and
  changed exactly one edge, and on a paper repository, one edge and nothing else. Read the mechanism
  as the rule and the number as unknown — a one-edge diff is not a sign your repository is exempt,
  and 44% is not what to expect. **`.graphifyignore`
  cannot suppress this**: the scope file filters symbol extraction, not the directory walk, so an
  ignored-but-present file still perturbs ordering. This is the first thing anyone reaches for and
  it does not work.
- **A git worktree is not a cause at all.** `.git` is a file there rather than a directory, so the
  scan sees one more entry, and that changes nothing: the cleanest measurement found a worktree
  build and a clone build differing in exactly one field, `built_at_commit` — zero nodes, edges or
  communities. Worktrees got the blame earlier because a worktree is where an agent happens to have
  run a build. One consequence for step 8: `cmp` between a worktree build and a clone build fails on
  that single field and looks like a scope or cache fault, so compare **clone against clone**.
- **Across operating systems, clustering is stable and edge extraction is not.** Identical node ids,
  community ids and community names, and three `imports_from` edges present on macOS and absent on
  Linux — nothing added, nothing reclassified. The committed graph carries the flavour of whichever
  platform last built it; the difference runs both ways.

The diagnostic, when a rebuild does not match and you need to know why:

```bash
git status --porcelain --ignored -uall | grep '^!!' \
  | grep -Ev '^!! \.(venv|nox)/|^!! graphify-out/' | grep -E '\.pyi?$'
```

Those exclusions are not optional: without them a `uv` project prints thousands of lines from
`.venv/` and the handful of files that matter are nowhere near the top. What is left — typically
`src/**/_version.py`, one per distribution on a monorepo, plus generated `.pyi` stubs — is the reason
your rebuild will not match CI's.

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

## Making the byte-identity check mean something

With `graph.json` already present and nothing changed, `update --force` does not rewrite the file at
all — no `Rebuilt: N nodes, M edges` line, just "Code graph updated". Byte-identity is then trivially
true, so step 8's check can be ticked without having tested anything. Either watch for that
`Rebuilt:` line, or perturb the graph first and confirm the rebuild restores it:

```bash
python3 -c "
import json; p='graphify-out/graph.json'
g=json.load(open(p)); g['nodes']=g['nodes'][:-50]
json.dump(g, open(p,'w'), separators=(',',':'))"
PYTHONHASHSEED=0 graphify update . --force      # must print 'Rebuilt:'
git diff --quiet -- graphify-out/graph.json && echo PASS
```

That is what proved one 3,865-node graph reproducible: the same nodes, edges and bytes restored from
a perturbation, with a cold AST cache.
