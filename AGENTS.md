# AGENTS.md

How this repo is laid out, and how a skill gets onto the website.

## Layout

One folder per skill, at the top level:

```
<skill>/
  SKILL.md      the skill itself: YAML frontmatter (name, description) and instructions
  card.json     the card on https://nstarkman.space/tools/ (below)
  references/   optional: longer docs SKILL.md points to
  assets/       optional: templates
  scripts/      optional: helpers (standard-library Python 3 or Bash)
```

The folder name is the skill's `name` in `SKILL.md`. A folder with a
`SKILL.md` is a skill; nothing else at the top level is.

## `card.json`

Every skill has one. It is what the website shows, so it is written for people
browsing, not for an agent deciding whether to load the skill (that is
`SKILL.md`'s `description`):

```json
{
  "name": "engaging-hybrid-compute",
  "description": "One or two sentences on what the skill does, in the present tense."
}
```

- `name`: the folder name.
- `description`: one or two sentences, plain text, no Markdown.
- Exactly these two keys, both non-empty strings.

## How it reaches the website

[nstarman/nstarman.github.io](https://github.com/nstarman/nstarman.github.io)
reads this repo; nothing here pushes to it.

1. `.github/workflows/refresh-skills.yml` there runs weekly (and by hand from
   the Actions tab).
2. `scripts/collect-skills.mjs` reads every `<skill>/card.json` on `main` and
   writes `config/skills.json`, linking each card to `<skill>/` on `main`.
3. If that file changed, the workflow opens a pull request on the site. Merging
   it updates the Agent Skills section of `/tools/`.

The collector stops, and no PR opens, if a folder with a `SKILL.md` has no
`card.json` or the card is malformed. A skill's card appears only after it is
merged here, so the link never points at a missing folder.

## Adding a skill

1. Add `<skill>/SKILL.md` and `<skill>/card.json`.
2. Add a row to the table in `README.md`.
3. Open a PR. After it merges, the next site refresh proposes the card; run
   `refresh-skills` on the site by hand to get it sooner.
