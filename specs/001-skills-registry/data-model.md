# Data Model: skills registry

## Skill (the common view of both kinds)

| Field | Local skill | External skill |
|---|---|---|
| name | folder name = `card.json` name = `SKILL.md` name | registry file stem = entry name = `SKILL.md` name at ref |
| description | `card.json` description | entry description |
| origin | `local` | `external` |
| source.repo | `nstarman/skills` | entry `source.repo` |
| source.path | the folder name | entry `source.path` |
| source.ref | `main` | entry `source.ref` (tag or branch) |
| href | `https://github.com/nstarman/skills/tree/main/<name>` | `https://github.com/<repo>/tree/<ref>/<path>` |
| install | `<name>@nstarman-skills` | same |
| zip | `https://github.com/nstarman/skills/releases/latest/download/<name>.zip` | same |

Validation rules (all skills):

- `name` matches `^[a-z0-9-]{1,64}$`; unique across local folders and registry entries.
- card/entry `description`: non-empty string.
- `SKILL.md` frontmatter at the skill's source: `name` equals the skill's name; `description`
  non-empty, at most 1024 characters (claude.ai / Agent Skills limit). `SKILL.md` over 500 lines is
  a warning.

## Registry entry (`registry/<name>.json`)

Exactly the keys `name`, `description`, `source`; `source` exactly `repo` (`owner/repo`), `path`
(relative, no leading `/`, no `..`), `ref` (non-empty). See
[contracts/registry-entry.md](contracts/registry-entry.md).

## Local skill

A top-level folder with `SKILL.md` and `card.json` (exactly `name`, `description`). Folders under
`.claude/`, `.specify/`, `.github/`, `registry/`, `scripts/`, `specs/`, `tests/` are never skills;
only top-level folders containing `SKILL.md` are.

## Index (`index.json`)

`{ "$comment", "schema": 1, "marketplace": "nstarman-skills", "skills": [Skill …] }` sorted by
name. See [contracts/index-json.md](contracts/index-json.md).

## Release

Tag `vYYYY.MM.DD[.N]`; assets: one `<name>.zip` per skill and `hashes.json`
(`{name: sha256-of-zip}`). Published only when `hashes.json` would differ from the latest
release's.

State of a tag-pinned entry: `current` (ref = latest release tag) → `behind` (a newer release tag
exists) → proposed in the weekly pull request → `current` after merge. Branch-tracking entries have
no state.
