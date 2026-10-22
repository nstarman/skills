# Contract: `.claude-plugin/marketplace.json` (generated)

```json
{
  "name": "nstarman-skills",
  "description": "Agent skills by Nathaniel Starkman — one plugin per skill.",
  "owner": { "name": "Nathaniel Starkman", "url": "https://nstarkman.space" },
  "plugins": [
    {
      "name": "diataxis",
      "description": "<the skill's description>",
      "source": "./diataxis",
      "skills": ["./"],
      "homepage": "https://github.com/nstarman/skills/tree/main/diataxis"
    },
    {
      "name": "figkit",
      "description": "<the skill's description>",
      "source": { "source": "git-subdir", "url": "nstarman/figkit", "path": "skills/figkit", "ref": "v0.2.0" },
      "skills": ["./"],
      "homepage": "https://github.com/nstarman/figkit/tree/v0.2.0/skills/figkit"
    }
  ]
}
```

- One plugin per skill; plugin `name` = skill name, so installs are `<name>@nstarman-skills` and
  the skill runs as `/<name>:<name>`.
- Source = the skill folder itself, with `"skills": ["./"]` (research R1). No `plugin.json`.
- Must pass `claude plugin validate .` with no errors or warnings.
- Users: `/plugin marketplace add nstarman/skills`, then `/plugin install <name>@nstarman-skills`.
