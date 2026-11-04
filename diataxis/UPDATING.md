# Keeping diataxis current

The Diátaxis advice in this skill does not age, but `references/sphinx-myst.md` and
`references/zensical.md` document moving targets: Sphinx, MyST-Parser, sphinx-design,
sphinxext-rediraffe, sphinx-reredirects, pydata-sphinx-theme and Zensical (alpha, released about
weekly). `versions.json` records the releases the end-to-end test last passed on. When those
move, re-verify against the tools; do not edit claims from release notes alone.

## What tells you to update

An issue titled **"diataxis: weekly test needs attention (upstream change)"**. The weekly run
(`.github/workflows/test-diataxis.yml`, latest releases from PyPI) opens it, or comments on the
open one, when the test fails. Versions newer than `versions.json` that pass are only a warning
in the run's log (Zensical releases about weekly); bump `versions.json` (step 4) when convenient.

## How to update

1. **Reproduce locally**, in a virtual environment:
   ```bash
   pip install sphinx 'myst-parser[linkify]' sphinx-design sphinxext-rediraffe \
       sphinx-reredirects pydata-sphinx-theme zensical
   tests/skills/diataxis/run.sh /tmp/diataxis-test
   ```
   It lays out `tests/skills/diataxis/fixture/docs/` with the skill's landing-page and
   contributing assets, runs the skill's scripts on it, then builds it with Sphinx (`-W -n`, the
   reference's starter `conf.py`, rediraffe and sphinx-reredirects) and with Zensical
   (`--strict`, the reference's `zensical.toml`, the `redirects` plugin and generated stubs).
2. **Read the failing step** (`::error::` lines):
   - A build fails under `-W` or `--strict`: an option, extension or theme option was renamed or
     removed. Find the new spelling in the tool's changelog, then fix the reference *and* the
     fixture config (`fixture/sphinx/conf.py`, `fixture/zensical/*.toml`), which copy it.
   - A documented behaviour no longer holds (the step names the reference section): page titles,
     redirects, `rediraffecheckdiff`, the Zensical CLI. Update that section, and `SKILL.md` if it
     repeats the claim, then the check.
   - A `scripts/` step fails: the skill's own scripts, not upstream; fix the script.
3. **New features worth documenting** (Zensical especially): read the changelogs since the
   version in `versions.json`; the Zensical "Feature gaps" table goes stale fastest. Add a check
   to `run.sh` for any new claim you make.
4. **Record the versions** in `versions.json` (`verified` date and each package).
5. Run the repository checks (`python -m unittest discover tests`,
   `python scripts/build_index.py --check`) and open a pull request; the workflow runs on it.
