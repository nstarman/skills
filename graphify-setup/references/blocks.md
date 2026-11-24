# Paste-in blocks

One section per block, in the order [SKILL.md](../SKILL.md) calls for them. Copy-paste material
only: the reasoning is in SKILL.md, and if the two disagree, SKILL.md is wrong.

Replace `<version>`, `<default-branch>` and `<agent-guidance-file>` everywhere. Nothing here may
carry another repository's name into the one being wired.

## gitignore

```gitignore
# graphify: track the graph itself; everything else here is rebuilt locally
graphify-out/*
!graphify-out/graph.json
```

## gitattributes

```gitattributes
graphify-out/graph.json merge=graphify linguist-generated=true -diff
```

## commit-check exclusions

For `prek` / `pre-commit`, add the exclusion to each hook that would touch the graph. The names
below are the common ones; check the repository's own config for others that match `.json`.

```yaml
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: <existing rev>
    hooks:
      - id: check-added-large-files
        exclude: ^graphify-out/graph\.json$
      - id: end-of-file-fixer
        exclude: ^graphify-out/graph\.json$
      - id: trailing-whitespace
        exclude: ^graphify-out/graph\.json$

  - repo: https://github.com/rbubley/mirrors-prettier
    rev: <existing rev>
    hooks:
      - id: prettier
        exclude: ^graphify-out/graph\.json$
```

`check-added-large-files` can take `args: ["--maxkb=8192"]` instead, if the repository would rather
keep the check on the graph than exclude it. The formatter exclusions are not optional: a formatter
that reformats the graph, or appends the newline the tool does not write, makes the file churn or
fight the hook on every commit.

## rebuild hook

```yaml
  # Keeps the committed code graph (graphify-out/graph.json) in step with the code.
  # Like a formatter: if the graph changed, stage it and commit again.
  # Skip once with `SKIP=graphify-update git commit ...`.
  # If a rebuild is refused because the graph would shrink: `GRAPHIFY_FORCE=1 git commit ...`.
  - repo: local
    hooks:
      - id: graphify-update
        name: graphify update
        language: python
        additional_dependencies: ["graphifyy==<version>"]
        entry: env PYTHONHASHSEED=0 graphify update .
        pass_filenames: false
        exclude: ^graphify-out/
```

`exclude: ^graphify-out/` means the hook does not run when the graph is the only staged change.
`additional_dependencies` pins the release in an isolated environment, and this line is the pin's
only home: the workflow below reads the version back out of this file.

## drift workflow

`.github/workflows/graphify.yml`. Pin the two actions the way this repository's other workflows pin
theirs — copy the `uses:` lines from a sibling workflow rather than taking the tags below.

```yaml
name: Refresh code graph

# Rebuilds graphify-out/graph.json and opens a pull request if it drifted, e.g. because someone
# committed with the hook skipped.

on:
  workflow_dispatch:
  schedule:
    - cron: "0 7 * * 1" # Mondays, 07:00 UTC

concurrency:
  group: ${{ github.workflow }}
  cancel-in-progress: false

permissions:
  contents: write
  pull-requests: write

jobs:
  refresh:
    name: Rebuild graph
    runs-on: ubuntu-latest
    env:
      BRANCH: chore/refresh-graphify
      GH_TOKEN: ${{ github.token }}
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v6

      - name: Rebuild graph
        # The version is pinned once, in the commit-check config.
        run: |
          pin=$(grep -o 'graphifyy==[0-9.]*' .pre-commit-config.yaml)
          PYTHONHASHSEED=0 uvx --from "$pin" graphify update .

      - name: Open a pull request if the graph changed
        run: |
          git diff --quiet -- graphify-out/graph.json && exit 0
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git switch -C "$BRANCH"
          git add graphify-out/graph.json
          git commit -m "chore: refresh the graphify code graph"
          git push --force origin "$BRANCH"
          if [ -z "$(gh pr list --head "$BRANCH" --state open --json number --jq '.[].number')" ]; then
            gh pr create --head "$BRANCH" --base "${{ github.event.repository.default_branch }}" \
              --title "chore: refresh the graphify code graph" \
              --body "Weekly rebuild of \`graphify-out/graph.json\`. The graph had drifted from the code."
          fi
```

## agent rules

Into `<agent-guidance-file>`, as its own section.

```markdown
## Code graph

This repository has a committed graphify knowledge graph at `graphify-out/graph.json`: every
symbol, the links between them, the architectural hubs, and which subsystem each symbol belongs
to. It is built from the source by tree-sitter, so it is as current as the last commit.

Querying it is cheaper and more accurate than grepping. The rules:

- For any question about this codebase, query the graph **before** your first grep, glob or
  source-file read:
  - `graphify query "<question>"` — a scoped subgraph for a plain-language question
  - `graphify explain "<symbol>"` — one symbol and its neighbours
  - `graphify path "<A>" "<B>"` — how two things connect
  - `graphify-out/GRAPH_REPORT.md` — hubs and subsystems, for broad architecture review only
  Read source files for the lines a query has already located, not to find them.
- Put this rule in every subagent prompt you write that explores the code. A subagent that greps
  from scratch undoes the point of the graph.
- After changing code, refresh it: `PYTHONHASHSEED=0 graphify update .` — tree-sitter only, no
  model call, no network. If it refuses because the graph would shrink, use `--force`.
- Use the pinned release, the one in the commit-check config, so your rebuild clusters the same way
  the hook does: `uvx --from graphifyy==<version> graphify ...`.
- `graphify-out/graph.json` is generated. Do not read it directly, do not review it in a diff, and
  do not hand-resolve a conflict in it: rebuild it instead.
- Skip the graph only when the task is about the graph tooling itself being stale or wrong, or when
  asked to. An uncommitted or just-rebuilt graph file is normal and is not a reason to skip it.
```

## contributor section

Into `CONTRIBUTING.md`, near the development-setup steps.

````markdown
### The code graph

`graphify-out/graph.json` is a [graphify](https://github.com/Graphify-Labs/graphify) map of this
repository: its symbols and the relationships between them. AI assistants query it instead of
grepping, and you can too. Extraction is local tree-sitter parsing — no model call, and nothing
leaves your machine — and every edge is marked `EXTRACTED` (explicit in the source) or `INFERRED`
(resolved by graphify), so you can tell what was read from what was deduced.

The graph is committed, and the commit checks rebuild it. Install the pinned release and register
the merge driver once per clone, so two branches that both changed the graph merge cleanly:

```bash
uv tool install "graphifyy==<version>"
PY="$(sed -n '1s/^#!//p' "$(command -v graphify)")"
git config merge.graphify.name "graphify graph.json union merge"
git config merge.graphify.driver "\"$PY\" -m graphify merge-driver %O %A %B"
```

Then query it:

```bash
graphify query "how are <things> converted"   # a scoped subgraph for a question
graphify explain "<SomeClass>"                # one symbol and its neighbours
graphify path "<A>" "<B>"                     # how two things connect
open graphify-out/graph.html                  # the clickable graph
```

Day to day:

- The rebuild runs with your other commit checks. Like a formatter, it rebuilds and stops the
  commit; `git add graphify-out/graph.json` and commit again.
- Commit without rebuilding: `SKIP=graphify-update git commit ...`.
- If the rebuild is refused because the graph would shrink — you deleted code —
  `GRAPHIFY_FORCE=1 git commit ...`.
- If the graph ever conflicts in a merge, rebuild rather than edit it:
  `rm graphify-out/graph.json && graphify update . && git add graphify-out/graph.json`.
- A changed `graph.json` in a pull request is generated output. It is one line, collapsed by
  GitHub, and is not reviewed.
````

## README line

Into the contributing or development pointer near the end of `README.md`. One line.

```markdown
Contributors and AI assistants: this repository ships a queryable code graph — see
[CONTRIBUTING.md](CONTRIBUTING.md#the-code-graph).
```

## docs page

Into the documentation site's contributing or development page: the same text as the *contributor
section* block above, adjusted for the site's markup, with the heading at the page's own level. If
the site has no such page, skip it rather than making one for this.
