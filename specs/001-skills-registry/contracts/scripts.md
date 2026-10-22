# Contract: scripts (stdlib Python ≥ 3.11, run from the repository root)

Exit codes: 0 success; 1 a validation or build failure (each problem printed on its own line,
prefixed with the skill or file it concerns); 2 bad arguments.

## `python scripts/build_index.py [--check] [--remote]`

- default: validate local skills and registry entries (offline checks), then write `index.json`,
  `.claude-plugin/marketplace.json` and the README sections between
  `<!-- skills:table:start -->`/`<!-- skills:table:end -->` and
  `<!-- skills:install:start -->`/`<!-- skills:install:end -->`.
- `--check`: write nothing; exit 1 if any generated file would change (lists which).
- `--remote`: also fetch each external `SKILL.md` at its ref (GitHub API; `GITHUB_TOKEN` used if
  set) and validate its frontmatter.

## `python scripts/release_zips.py OUT_DIR [--previous HASHES_JSON]`

- Builds `OUT_DIR/<name>.zip` for every skill (local from its folder without `card.json`; external
  via a sparse clone at its ref) and `OUT_DIR/hashes.json`.
- With `--previous`, prints `changed` or `unchanged` as its last line (and the differing names
  before it); the workflow releases only on `changed`.

## `python scripts/bump_refs.py [--dry-run]`

- For each registry entry whose `ref` is a tag of its repository, finds the latest release tag;
  when newer, rewrites the entry's `ref` (unless `--dry-run`) and prints `name: old -> new`.
- Prints nothing and exits 0 when everything is current.
