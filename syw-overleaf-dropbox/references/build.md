# Building a showyourwork paper locally

## Environment

- Run `showyourwork build` from a shell where the conda environment that contains
  `snakemake` and `showyourwork` is on `PATH`, for example
  `export PATH="$HOME/miniconda3/envs/showyourwork-main/bin:$PATH"`.
- Analysis code usually runs through `uv run --locked python ...` inside Snakemake rules.
  If the repo has no `.venv` yet (a fresh clone or a moved folder), the first rule creates it
  and needs network access.
- Pin the Python version the lockfile supports with a `.python-version` file (for example
  `3.12`). A new machine's `uv` may pick the newest CPython, for which scientific wheels
  (jaxlib, ...) do not exist yet, and the environment fails to install.

## The command

```sh
export PYTHONPATH=src            # see gotchas: macOS hides .pth files
showyourwork build \
  --cores 2 \
  --rerun-incomplete \
  --conda-not-block-search-path-envvars
```

Add `--scheduler greedy` on Apple Silicon without Rosetta: Snakemake's default
(MILP) scheduler runs an x86 solver binary and dies with `Bad CPU type in executable`.

Tokens are passed inline on the same command (see SKILL.md, "Credentials").

## What a build does, in order

1. Fetches the Overleaf project and **pulls** the files listed under `overleaf.pull`
   (normally `ms.tex` and `bib.bib`) into the repo as a `[showyourwork]` commit. It refuses
   to overwrite a pulled file whose last commit is not a `[showyourwork]` commit.
2. Restores or recomputes cached rules (Zenodo-backed `cache: True` rules), then runs the
   calc, plot and variable-export rules whose inputs changed.
3. Compiles `ms.pdf`.
4. **Pushes** the files listed under `overleaf.push` (figures, generated numbers, class and
   preamble files) to Overleaf, then prints `Done!`.

If nothing needed running, steps 2-4 are skipped and nothing is pushed.

## Running a long build

Run it in the background, redirect output to a log file, and watch the log for the final
`Pushing changes to Overleaf` / `Done!` or for `Error` / `Traceback`. Expect minutes for a
warm cache and much longer when a cached rule must be recomputed. Do not start a second
build or a second Overleaf push while one is running: both use the same git clone under
`.showyourwork/overleaf` and can collide.

## What invalidates caches

Cached rules are keyed on their inputs, including any settings file (for example
`variables.yml`) that is listed as an input. Editing that file, even a comment, can force
an expensive recompute and a round trip to Zenodo. For hours-long computations, keep a
committed backup of the result and a `local_cache:` switch in `showyourwork.yml` that copies
the backup instead of recomputing, with a fingerprint test that fails when the backup no
longer matches its sources. Re-record fingerprints only when a change cannot affect the
physics (for example, adding an unrelated section to the settings file).
