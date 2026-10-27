# Lessons from earlier migrations

Add one entry per surprise: what happened, why, what to do instead.

## CP1 (stream straights and convexities), 2026

- **The Dropbox mirror was the working repository.** Its `.git` (196 commits, no remote), a
  20,000-file `.venv` and a `preamble` submodule lived inside the Overleaf folder; the GitHub
  repository held only Overleaf's own GitHub-sync snapshots (2 commits). So "the old repository"
  was two histories. Check `git -C <mirror> remote -v` and compare commits with GitHub in the
  survey; back up both (`backup.sh --github`), and run `public_check.sh` against both bundles.
- **Overleaf's GitHub integration** was linked to the old repository. Overleaf has no per-project
  unlink ("it is not possible to change the repository associated with a given project"), so the
  link stays; retiring the repository (archived or deleted) makes the menu harmless.
- **`\today`** in the paper shows up as a one-number difference in every `pdf_diff.py` run; expect
  it.
- **`ms.tex` edits the first SYW build needed**, each replayed on Overleaf with `ms_edits.py`:
  - the preamble's modules `\RequirePackage` each other by bare name, found before through
    latexmk's `TEXINPUTS`: add `\makeatletter\providecommand\input@path{}`
    `\g@addto@macro\input@path{{preamble/}}\makeatother` (`\providecommand`: tectonic does not
    define `\input@path`);
  - remove the paper's own `\variable`/`\script` shims: `showyourwork.sty` defines them;
  - `\leavevmode` before an `\includegraphics` followed by `\\`: SYW's preprocess pass redefines
    `\includegraphics` so it starts no line, and `\\` then has "no line here to end";
  - add `.pdf` to extension-less `\includegraphics` paths: SYW resolves them literally.
- **A fix to `ms.tex` that did not take effect.** SYW's preprocess stage copies `src/tex` only
  when its inputs change; delete `.showyourwork/preprocess` before rebuilding.
- **FontAwesome `\faRepeat` undefined.** The template's `showyourwork.sty` was older; CP2's fixed
  copy worked.
- **The engine difference swamped `pdf_diff.py`** (841 numbers, 1632 text lines): SYW builds with
  tectonic, the baseline and Overleaf with pdflatex. Comparing figures, number files and a
  pdflatex compile of the migrated sources separately found no difference at all; the
  side-by-side showed every float on its old page.
- **Pytest hung for 9 hours.** `testpaths = ["tests", "src"]` with `--doctest-modules` now
  reached `src/scripts/`, and importing the step_1 script started its 21-hour run (it wrote two
  checkpoints). Point doctests at the package only.
- **A reduced-grid check script still wrote to the real data folder** after paths moved to a
  shared `paths` module; patch output paths in the staged copies too.
- **The first CI build ran the 21-hour cached rule.** `zenodo.yml` had no Sandbox DOI yet, so SYW
  did not treat the rule as cached and `run_cache_rules_on_ci: false` never applied. Seed the
  draft before pushing `main` (phase 5).
- **The first sync pushed nothing.** The preceding failed attempt (empty token: `op read` had
  timed out) had already built everything, and Snakemake skips `onsuccess`, where SYW pushes,
  when there is nothing to do. Deleting `ms.pdf` forced a job.
- **CI crashed in `showyourwork cache restore`** (`FileNotFoundError` on
  `src/tex/figures/graphic/graphic.pdf`). A cached rule's output is a symlink into
  `.showyourwork/cache`; the Actions article cache saves `src/tex/figures` without the target,
  and `os.utime` follows the dangling link. Cached rules write under `src/data/`; a plain `cp`
  rule puts the real file in `src/tex/figures/`; bump `article-cache-number` to drop the bad
  cache. Upstream SYW has the same code.
- **CI pushed two figures 3.7% wider to Overleaf.** The script measured text in pixels while
  laying out; on a Retina Mac matplotlib's `macosx` backend draws at 200 dpi, CI's Agg at 100,
  and the tight bounding box followed. `matplotlib.use("agg")` plus `dpi=200` on the figure
  reproduced the original on every backend.
- **Two files existed only in Overleaf's `figures/`** (a notebook, an older data array): the
  dry run's deletion list caught them; the notebook went into the repository, the array into
  `.local_cache/`.
- **Pre-migration files only on GitHub.** Overleaf's import snapshot held 9 files deleted the next
  day, before the local history recorded them; the blob lookup in phase 8 found them in
  `github.bundle` only.

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
