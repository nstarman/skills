# Phase 0 Research: skills registry

Experiments run on 2026-10-22 with Claude Code 2.1.259, in a throwaway marketplace and an
isolated `CLAUDE_CONFIG_DIR` (the user's own settings were not touched).

## R1. One skill folder as one plugin

- **Decision**: every plugin entry's source is the skill folder itself, with `"skills": ["./"]`:
  a relative path `./<skill>` for local skills, a `git-subdir` source (`url` = repo, `path` = the
  skill folder, `ref`) for external ones. No `plugin.json` anywhere: the entry is the manifest.
- **Evidence**: four entry forms all passed `claude plugin validate` and installed with exactly one
  skill in their component inventory: (A) local folder as root + `skills: ["./"]`; (B) repo root +
  `skills: ["./diataxis"]`; (C) external `git-subdir` to the `skills/` parent + `skills: ["./quax"]`;
  (D) external `git-subdir` to the skill folder at tag `v0.2.0` + `skills: ["./"]`.
- **Why A/D**: they copy only the skill's folder into the plugin cache; B copies the whole repo, C
  the whole `skills/` folder. One form for both kinds keeps the generator simple.

## R2. claude.ai limits and zip shape

- **Decision**: frontmatter `name` matches `^[a-z0-9-]{1,64}$` and equals the folder name;
  `description` non-empty and at most 1024 characters. Zip = one top-level folder `<name>/` with the
  skill's files.
- **Source**: claude.com/docs/skills/how-to (fetched 2026-10-22): name "Lowercase letters, numbers,
  and hyphens only, up to 64 characters. Must match the skill's directory name"; description "Up to
  1,024 characters, the limit in the Agent Skills specification"; the ZIP "must contain the skill
  directory itself as its top level". An older/third-party claim of a 200-character description
  limit for claude.ai is not what the current official page says.
- **Also**: the page recommends `SKILL.md` under 500 lines — a warning, not a failure.

## R3. Reading `SKILL.md` frontmatter without a YAML library

- **Decision**: a small parser for the frontmatter subset skills use: `key: value`, single- and
  double-quoted values, and block scalars `>` / `|` with optional chomping (`-`, `+`), folded or
  literal by YAML's rules. Anything else in `name`/`description` is an error naming the file.
- **Why**: Principle VI (stdlib only); unxt's description uses `>`.

## R4. Fetching external skills

- **Validation** (CI, every PR): GitHub contents API via `urllib`, raw media type, with the
  workflow's `GITHUB_TOKEN` (`/repos/<repo>/contents/<path>/SKILL.md?ref=<ref>`). One request per
  entry.
- **Zips** (release workflow): `git clone --depth 1 --branch <ref> --filter=blob:none --sparse`
  then `git sparse-checkout set <path>` — works for branches and tags and fetches only the folder.

## R5. Deterministic zips and change detection

- **Decision**: zips are written with sorted entries, fixed timestamps (1980-01-01) and fixed
  permissions, so equal content gives equal bytes. Each release also carries `hashes.json`
  (`{name: sha256 of the zip}`); the workflow compares with the latest release's `hashes.json` and
  publishes only when any differs or a skill was added/removed.
- **Tags**: `vYYYY.MM.DD`, then `vYYYY.MM.DD.2`, … if a release already exists that day.

## R6. Keeping tag pins current

- **Decision**: an entry is "tag-pinned" when its `ref` is a tag of its repository
  (`git ls-remote --tags`); for those, the latest release's `tag_name` (`/repos/<repo>/releases/latest`)
  is the candidate. The weekly job updates refs, regenerates, **runs the full validation itself**,
  and opens one pull request (or updates the open one) with `gh`.
- **Caveat**: pull requests opened with `GITHUB_TOKEN` do not trigger other workflows, so CI does
  not run on them automatically; the job's own validation stands in, and the PR body says to re-run
  checks before merging (Principle VI forbids adding a token secret).

## R7. `claude plugin validate` in CI

- **Decision**: install the Claude Code CLI in CI with npm (`npm i -g @anthropic-ai/claude-code`,
  pinned version) and run `claude plugin validate .`. It is a local check and needs no login.

## R8. Tests

- **Decision**: `python -m unittest` (stdlib) for the generator, parser, validator and zipper, with
  fixtures built in temporary directories; network checks are separate (`--remote`) and not run by
  the unit tests.
