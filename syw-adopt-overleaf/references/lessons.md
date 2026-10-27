# Lessons from earlier migrations

Add one entry per surprise: what happened, why, what to do instead.

## CP2 (spatial correlations of stream convexities), 2026

Migrated by hand before this skill existed; its history shows what a migration needs after the
first two commits.

- **Package conflicts in the preamble.** AASTeX, the personal preamble and `showyourwork.sty`
  each loaded FontAwesome variants; the build failed on an icon name collision, then on package
  option clashes. Load an icon package once, in the preamble, and check the log for
  "Option clash" before blaming SYW.
- **Undeclared TeX dependencies.** A stylesheet the manuscript `\input`s was not a Snakemake
  dependency, so changing it did not rebuild the PDF. List such files under `dependencies:
  src/tex/ms.tex:` in `showyourwork.yml`.
- **Hours-long rules.** Three simulations took hours each. SYW's `local_cache` copies their
  committed results from `src/static/` instead of recomputing; document in the README how to
  refresh them. Decide this in phase 3, not after a CI run times out.
- **Inputs from another paper.** Data from Paper I came from a Zenodo Sandbox record
  (`datasets:` in `showyourwork.yml`), with checksums in `src/data/.../README.md`. Do the same
  for any input not produced by this repository's code.
- **Cheap cached rules on CI.** `run_cache_rules_on_ci: true` lets CI recompute the minutes-long
  rules when the Zenodo cache misses (for example after a lockfile change), instead of failing.
- **Tests.** The old repository's tests were restored after the migration; copy them in phase 3.
