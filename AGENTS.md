# AGENTS.md

nstarman/skills is the registry and clearinghouse for the agent skills Nathaniel Starkman
publishes: every skill is registered here, wherever its files live, and listed, validated and
installed from here. Read `.specify/memory/constitution.md` first; it overrides this file.

## Layout

```
<skill>/                         a local skill: SKILL.md, card.json, references/, assets/, scripts/
registry/<name>.json             a skill that lives in another repository (pointer, not a copy)
index.json                       generated: every skill — the contract the website reads
.claude-plugin/marketplace.json  generated: the Claude Code marketplace `nstarman-skills`
README.md                        the skill table and install section are generated (between markers)
scripts/                         skillreg.py (shared), build_index.py, release_zips.py, bump_refs.py
tests/                           python -m unittest discover tests
.specify/, specs/                Spec Kit (v1.1.3); features go specify → plan → tasks → implement
```

A top-level folder with a `SKILL.md` is a local skill; nothing else is (`.claude/`, `.specify/`,
`.github/`, `registry/`, `scripts/`, `specs/`, `tests/` never are).

## Adding a local skill

1. Add `<skill>/SKILL.md` (frontmatter `name` = folder name, `[a-z0-9-]`, ≤ 64 characters;
   `description` ≤ 1024 characters) and `<skill>/card.json`:
   ```json
   { "name": "<skill>", "description": "One or two plain sentences, present tense, for people browsing." }
   ```
2. `python scripts/build_index.py` and commit the regenerated files.
3. Open a pull request (squash merge).

## Registering a skill from another repository

1. Add `registry/<name>.json` — no change is needed in the other repository:
   ```json
   {
     "name": "<name>",
     "description": "One or two plain sentences for people browsing.",
     "source": { "repo": "owner/repo", "path": "skills/<name>", "ref": "main" }
   }
   ```
   `ref` is a branch (the skill tracks it) or a tag (a versioned skill; the weekly bump job keeps it
   current). Register only skills meant for others, not a repository's internal tooling.
2. `python scripts/build_index.py --remote` (checks the skill's `SKILL.md` at `repo`/`path`/`ref`),
   commit, open a pull request.

## Generated files and checks

Never edit `index.json`, `.claude-plugin/marketplace.json` or the README's generated sections by
hand: change the skill or the registry entry and run `python scripts/build_index.py`.
`check.yml` runs on every pull request and push: unit tests, `build_index.py --check --remote`
(formats, unique names, every `SKILL.md` at its real location, claude.ai limits, freshness) and
`claude plugin validate .`.

## Releases and zips

Versions are dates, as in figpress-apps and syw-site: a release is `vYYYY.MM.DD`; a second release on the
same day is `vYYYY.MM.DD.2`, and so on. Every release is a complete snapshot of all skills, so
nothing is backported here.

`release.yml` builds one zip per skill (the skill's folder, without `card.json`; external skills at
their ref) on every push to `main`, weekly and by hand, and publishes a release tagged
`vYYYY.MM.DD` only when a zip changed. `https://github.com/nstarman/skills/releases/latest/download/<name>.zip`
is the stable link (it 404s until the first release exists).

`bump-refs.yml` runs weekly: for tag-pinned entries it opens (or updates) one pull request moving
them to their repository's latest release (date tags sort after older semver tags, e.g. figpress-apps'
`v2026.10.30` after `v0.2.0`). Pull requests opened by `GITHUB_TOKEN` do not trigger
CI; the job validates and puts the output in the pull request — re-run checks before merging.

## How it reaches the website

[nstarman/nstarman.github.io](https://github.com/nstarman/nstarman.github.io) reads
`index.json`; nothing here pushes to it. Its weekly `refresh-skills.yml` (or a manual run) runs
`scripts/collect-skills.mjs`, which writes `config/skills.json` for the Agent Skills section of
`/tools/` and opens a pull request on the site when it changed.

`index.json` (schema 1) is a contract: adding an optional field keeps `schema: 1`; removing or
renaming a field, or changing its meaning, makes it `schema: 2` and must be coordinated with the
collector, which refuses an unknown schema rather than showing a broken section.
