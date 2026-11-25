# Deciding what the graph covers

Read this at step 1 of [SKILL.md](../SKILL.md), which builds a survey graph, and at step 2, which
turns the survey into `.graphifyignore`. The scope decision sets the committed file's size and
whether queries return code or noise, and it is the one judgement the runbook cannot make for you.

## What is in the survey graph

`extract` does not write `GRAPH_REPORT.md`, so read the graph. Nodes per file, worst first:

```bash
python3 -c "
import json, collections
g = json.load(open('graphify-out/graph.json'))
c = collections.Counter(n.get('source_file', '(external)') for n in g['nodes'])
for path, n in c.most_common(40): print(f'{n:6d}  {path}')
print(len(g['nodes']), 'nodes total')"
```

The key is `source_file`, not `file_path`. Edges live under `links`, not `edges` — any script you
write against the graph needs that.

## Pricing a candidate scope without rebuilding

Rebuilding to measure costs minutes on a large repository, and you must `rm -rf graphify-out`
between candidates because a scope change does not invalidate the AST cache. Simulating from the
survey is instant and accurate to within clustering: drop the nodes whose `source_file` matches the
candidate, drop the links touching them, and measure the serialised size.

```bash
python3 -c "
import json, re, sys
g = json.load(open('graphify-out/graph.json'))
for label, pat in [
    ('as surveyed',        r'$^'),
    ('yml/yaml/md/svg/png', r'\.(ya?ml|md|svg|png)$'),
    ('  + tests/',          r'\.(ya?ml|md|svg|png)$|(^|/)tests?/'),
    ('  + docs/',           r'\.(ya?ml|md|svg|png)$|(^|/)(tests?|docs)/'),
]:
    rx = re.compile(pat)
    keep = {n['id'] for n in g['nodes'] if not rx.search(n.get('source_file') or '')}
    nodes = [n for n in g['nodes'] if n['id'] in keep]
    links = [l for l in g['links'] if l['source'] in keep and l['target'] in keep]
    size = len(json.dumps({**g, 'nodes': nodes, 'links': links}, separators=(',', ':')))
    print(f'{label:24s} {len(nodes):6d} nodes {len(links):6d} links {size/1e6:6.2f} MB')"
```

A prediction within a few per cent of the built result is close enough to decide on. Measured on one
repository: 11.60 MB as surveyed, 11.29 MB with the extension globs, 5.37 MB once `tests/` went too —
and 5.31 MB with `benchmarks/`, `scripts/` and `docs/` excluded as well, which is why that repository
keeps them. Saving 0.07 MB by dropping real coverage is a bad trade, and only numbers show that.

## Directory patterns, and the test suite

`.graphifyignore` takes gitignore syntax, not just extension globs: a bare `tests/` prunes that
directory **at any depth**, which on a monorepo catches every package's tests in one line. It also
takes `#` comments and blank lines, so the file can explain itself.

On a library of any size the extension cut is the small one and a **directory** decides the file
size. Measured on one monorepo: the extension globs removed 570 of 8,791 nodes; `tests/` removed
3,910 nodes and 11,353 edges — 44% of the survey graph and about half its bytes.

**So decide the test suite deliberately, and say which way in the pull request.** It is usually the
largest single block of nodes, and both answers are defensible: tests out, because the graph is for
navigating the library and test fixtures crowd out its hubs; or tests in, because "what covers this
function" is a question worth asking the graph. What is not defensible is deciding it silently and
differently in every repository. Keep them unless the graph's hubs come out as test fixtures.

## Repository-specific exclusions worth checking for

- `*.ipynb` — notebooks extract a node per cell and swamp a repository that keeps examples.
- `*.tex`, `*.bib`, `*.pdf` — a paper repository's manuscript, which is not code.
- generated API stubs, vendored trees, data directories, job scripts.
- `graphify-out/` itself needs **no** entry: its own files do not perturb the walk, which is what
  makes the profile coherent at all.
