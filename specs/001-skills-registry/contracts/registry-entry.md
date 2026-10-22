# Contract: registry entry and card

## `registry/<name>.json` — a skill held in another repository

```json
{
  "name": "unxt",
  "description": "One or two plain sentences on what the skill does, in the present tense.",
  "source": {
    "repo": "GalacticDynamics/unxt",
    "path": "skills/unxt",
    "ref": "main"
  }
}
```

| Key | Rule |
|---|---|
| `name` | `^[a-z0-9-]{1,64}$`; equals the file stem; equals `name:` in the `SKILL.md` at `repo`/`path`/`ref`; unique across the registry and local folders |
| `description` | non-empty plain text (no Markdown) for people browsing the website; one or two sentences |
| `source.repo` | GitHub `owner/repo`; public |
| `source.path` | folder holding `SKILL.md`, relative to the repository root, no leading `/`, no `..` |
| `source.ref` | a tag (versioned skills; kept current by the weekly bump job) or a branch (tracks it) |

No other keys at either level. Files are UTF-8, 2-space indented, with a trailing newline.

## `<skill>/card.json` — a local skill (unchanged)

```json
{ "name": "diataxis", "description": "…" }
```

Exactly `name` (= folder name) and `description` (non-empty plain text). Registry entries share
these two fields so every skill is described the same way.
