# skills

Agent skills I publish — instructions, references and scripts that an AI coding
agent loads when a task calls for them. This repository is their registry: skills
kept here are folders with a `SKILL.md` at the top, and skills that live with the
code they describe (quax, unxt, figkit) are registered in `registry/` and listed
alongside them, linked to their home repository.

<!-- skills:table:start -->
| Skill | For | From |
| --- | --- | --- |
| [`diataxis`](diataxis/) | Audits and restructures documentation into the Diátaxis modes — tutorials, how-to guides, reference and explanation — without breaking links. |  |
| [`engaging-hybrid-compute`](engaging-hybrid-compute/) | Splits a research project between a laptop and MIT's Engaging cluster: edit locally, run Slurm jobs on the cluster, and sync code and results through a private git repo. |  |
| [`figkit`](https://github.com/nstarman/figkit/tree/v0.2.0/skills/figkit) | Builds an interactive webapp for a scientific paper with figkit: exports the paper's arrays, ports the per-interaction science to tested JavaScript, composes linked views, and publishes a static site plus a single archivable HTML file that also runs in notebooks. | [nstarman/figkit](https://github.com/nstarman/figkit) |
| [`figkit-upgrade`](https://github.com/nstarman/figkit/tree/v0.2.0/skills/figkit-upgrade) | Moves a figkit webapp to a newer figkit version by applying the changelog's migration notes in order, then rebuilds and re-checks that the app still reproduces the paper's numbers. | [nstarman/figkit](https://github.com/nstarman/figkit) |
| [`quax`](https://github.com/nstarman/quax/tree/main/skills/quax) | Writes, reviews and debugs JAX code that uses quax: custom array-like types such as physical units, sparse and low-rank arrays, quaxify, and the dispatch rules that make them work. | [nstarman/quax](https://github.com/nstarman/quax) |
| [`syw-adopt-overleaf`](syw-adopt-overleaf/) | Moves an existing paper, with a live Overleaf project and a private git repository, into a fresh showyourwork repository: backup first, regenerated figures and numbers compared against the old PDF, every irreversible step approved by the author, and the old history kept private. |  |
| [`syw-overleaf-dropbox`](syw-overleaf-dropbox/) | Guides writing a paper with showyourwork and Overleaf, using the Dropbox copy of the Overleaf project as the local text mirror: where to edit text versus code, how a build pushes figures and numbers, and the stalls and silent non-builds to expect. |  |
| [`syw-site`](https://github.com/nstarman/syw-site/tree/v2026.10.28/skills/syw-site) | Adds a docs site to a showyourwork paper: its numbers, figures and interactive figkit webapps, built by the paper's own pipeline and published at nstarkman.space with the website's layout, kept private until arXiv. | [nstarman/syw-site](https://github.com/nstarman/syw-site) |
| [`syw-site-upgrade`](https://github.com/nstarman/syw-site/tree/v2026.10.28/skills/syw-site-upgrade) | Moves a paper's docs site to a newer syw-site release by applying the changelog's migration notes in order, refreshing the scaffold, rebuilding and checking that the site still shows the paper's numbers. | [nstarman/syw-site](https://github.com/nstarman/syw-site) |
| [`unxt`](https://github.com/GalacticDynamics/unxt/tree/main/skills/unxt) | Writes, reviews and debugs code that uses unxt quantities in JAX: units, dimensions and unit systems, conversions, and passing quantities through JAX and quax transformations. | [GalacticDynamics/unxt](https://github.com/GalacticDynamics/unxt) |
<!-- skills:table:end -->

## Installing

<!-- skills:install:start -->
**Claude Code** — add this repository as a plugin marketplace once, then install any skill by name
(skills in other repositories install from there, at the version listed):

```text
/plugin marketplace add nstarman/skills
/plugin install <name>@nstarman-skills
```

**claude.ai** — download `<name>.zip` from the
[latest release](https://github.com/nstarman/skills/releases/latest) and upload it under Customize → Skills.

**By hand** — copy the skill's folder (its link in the table above) into `~/.claude/skills/`, or into
a project's `.claude/skills/` for that project only.
<!-- skills:install:end -->

The skills' bundled scripts are standard-library Python 3 or Bash. To add or register a
skill, see [AGENTS.md](AGENTS.md).

## Credits

The `diataxis` skill follows [Diátaxis](https://diataxis.fr) by Daniele Procida,
and quotes it briefly; Diátaxis is licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
