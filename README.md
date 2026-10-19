# skills

Agent skills I use — instructions, references and scripts that an AI coding
agent loads when a task calls for them. Each folder is one skill, with its
`SKILL.md` at the top.

| Skill | For |
| --- | --- |
| [`diataxis`](diataxis/) | Auditing and restructuring documentation into the [Diátaxis](https://diataxis.fr) modes — tutorials, how-to guides, reference and explanation — without breaking links. Covers Sphinx/MyST and Zensical. |
| [`engaging-hybrid-compute`](engaging-hybrid-compute/) | Splitting a research project between a local machine and MIT's Engaging (ORCD) Slurm cluster, synced through a private git repo: SSH/Duo ControlMaster, job submission and monitoring, pushing results back. |

## Using one

**Claude Code** — copy the skill's folder into your skills directory:

```bash
git clone https://github.com/nstarman/skills
cp -R skills/diataxis ~/.claude/skills/
```

For one project only, copy it into that project's `.claude/skills/` instead.

**claude.ai** — zip the skill's folder and upload it under Settings → Capabilities → Skills.

The bundled scripts are standard-library Python 3 or Bash.

## Credits

The `diataxis` skill follows [Diátaxis](https://diataxis.fr) by Daniele Procida,
and quotes it briefly; Diátaxis is licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
