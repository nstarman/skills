---
name: syw-overleaf-dropbox
description: Workflow for writing a scientific paper with showyourwork (SYW, the Snakemake-based reproducible-paper tool) and Overleaf, using the Dropbox copy of the Overleaf project as the local text mirror. Use this whenever the user is working in a showyourwork repository (showyourwork.yml, Snakefile, src/tex/ms.tex, src/scripts), edits ms.tex or bib.bib, uses \variable{output/...} macros, rebuilds the paper, syncs with Overleaf, hits a "figure not found" or stale-number problem in Overleaf, or mentions Zenodo caches, 1Password tokens for builds, or SYW stalls and hangs. Make sure to use it before editing any paper text or running a build in such a repo, even if the user only says "update the figure", "fix this sentence", "rebuild", or "push to Overleaf".
---

# Writing a showyourwork paper with Overleaf and a Dropbox mirror

A showyourwork (SYW) paper lives in three places that must not drift apart. Most
mistakes come from editing the right thing in the wrong place, so learn the map first.

| What | Where you edit it | Why |
|---|---|---|
| Paper **text** (`ms.tex`, `bib.bib`) | The **Dropbox copy of the Overleaf project** (the "mirror") | SYW *pulls* these two files from Overleaf at the start of every build and overwrites the repo's copy. An edit made in `src/tex/` is silently lost, or collides with the pull. |
| **Code, data, figures, numbers** | The repo (`src/scripts/`, `variables.yml`, `Snakefile`, ...) | SYW builds them and *pushes* the results to Overleaf. |
| **Figure PDFs, `\variable{}` values, class and preamble files** | Nobody: they are build outputs | A build pushes them to Overleaf (`overleaf.push` in `showyourwork.yml`). Overleaf has no figures or numbers until a build has pushed. |

The Dropbox mirror is an ordinary folder that Dropbox keeps in sync with the Overleaf
project, so Claude can read and edit the text with normal file tools while the user (or
co-authors) edit in Overleaf. On macOS it is
`~/Library/CloudStorage/Dropbox/Apps/Overleaf/<Project Name>/`. Find it before the first
edit; if you cannot find it, ask the user rather than editing `src/tex/ms.tex`.

## The loop

1. **Text change:** read the relevant part of the mirror's `ms.tex`, then edit it *there*
   (see "Editing text" below). Do not touch `src/tex/ms.tex`.
2. **Code or figure change:** edit in the repo.
3. **Rebuild** (see `references/build.md` for the exact command and environment). The build
   pulls `ms.tex` and `bib.bib` from Overleaf, regenerates anything whose inputs changed,
   compiles `ms.pdf`, and pushes figures and numbers to Overleaf.
4. **Verify**, then show the user the PDF (`scripts/check_build.sh` automates the checks).
5. Commit and push to GitHub only when the user asks.

Run a build after *any* change that Overleaf needs to see, because Overleaf only receives
figures and `\variable{}` values at the end of a build. That is the usual reason for
"File `figures/...pdf` not found" or "`output/...tex` not found" in Overleaf: the
text arrived first and the build has not pushed yet.

## Editing text

- Apply edits with exact-match replacement that fails loudly if the old text is not found
  exactly once (`scripts/mirror_edit.py` does this). The mirror may have changed since you
  last read it, because Overleaf collaborators edit it too.
- Numbers in the text should be `\variable{output/<group>/<name>.tex}` macros, not typed
  digits, so they follow the code. `references/variables.md` explains the plumbing.
- A rename or restructure of a figure needs the `\includegraphics` line in the mirror
  changed too. Otherwise a clean checkout (CI) fails.

## Figures and numbers in the repo

- Split each figure into a `calc_*.py` (heavy; writes an `.npz`/values JSON) and a `plot_*.py`
  (light; only draws). Restyling a plot then never invalidates a cached calculation.
- Every number the text quotes comes from a `calc_*` script via `write_values`, is rendered
  by a `make_variables.py`-style exporter, and is cited as `\variable{...}`. Only variables
  that the text cites are generated, so adding a citation requires a build before Overleaf
  can compile it.
- Preview a figure by running its `plot_*.py` and converting the PDF to a PNG (`pdftoppm`)
  to look at it. Iterate on the picture, not on guesses about it.
- **After editing a figure script, do not leave a hand-generated PDF in `src/tex/figures`.**
  Snakemake then sees the output as newer than the script, runs no jobs, and the build
  exits 0 *without pushing to Overleaf*. Delete the PDF (or just rebuild first) so the build
  regenerates and pushes it.
- Figures for a project web page, talks, or anything that is not in the paper belong in a
  separate folder (for example `docs/`) with their own script and no SYW rule.

## What SYW builds is decided by what `ms.tex` references

SYW starts from the manuscript: it builds the figures that `\includegraphics` names and the
numbers that `\variable{...}` cites, plus whatever those depend on. So:

- A number must be cited with `\variable{output/<group>/<name>.tex}` to be generated. A home-made
  `\newcommand` that `\input`s a file does not count, because SYW never sees a citation.
- A figure that no `\includegraphics` in `ms.tex` names is not built. When `ms.tex` does name
  it, a rule in the `Snakefile` must produce exactly that path (or the file must already
  exist). The `\script{...}` tag in a caption is how SYW's automatic figure rules find the
  script; with an explicit `Snakefile` rule it is not needed. Check your SYW version's docs
  before adding or removing it.
- When a figure does not appear in Overleaf, first look at the build log (did it run the rule, did
  it end with a push?), then at these references. A stale hand-made PDF explains an exit 0
  with no push far more often than a missing tag does.

## Credentials

Builds need an Overleaf git token and, for Zenodo-cached rules, a Zenodo token. Read them
from a password manager's CLI at the moment of the build and pass them as environment
variables on that one command, so they never reach a file or the transcript:

```sh
SANDBOX_TOKEN="$(op read 'op://<vault>/<item>/credential')" \
OVERLEAF_TOKEN="$(op read 'op://<vault>/<item>/credential')" \
showyourwork build ...
```

Never print, log or write a token. SYW's own error output *can* include a Zenodo access
token inside a failed request URL, so redact `access_token=...` when you read build logs.

## After a build, check

1. The log ends with `Pushing changes to Overleaf: ...` then `Done!`. A build that exits 0
   without that line did nothing (see the stale-PDF note above).
2. No cited `\variable{...}` file is missing (`scripts/check_build.sh`).
3. Figures in the repo and in the mirror have identical checksums. Dropbox can lag the push
   by seconds to a minute, so wait and recheck before suspecting a failure.
4. Show the user `ms.pdf` (and any changed figure) after every rebuild.

## Where things go wrong

The long list of stalls, flags and platform quirks is in `references/gotchas.md`. Read it
when a build hangs, fails, or silently does nothing. The most common ones:

- Build idle for minutes after "Syncing file with Zenodo ... cache": a Zenodo token is
  missing.
- Looks hung at "Updating checkpoint dependencies": SYW's unmemoized dependency walk.
- "No module named <your package>" on macOS: hidden `.pth` file; use `PYTHONPATH=src`.
- Overleaf compile error "figure not found": the build has not pushed yet.
- `MissingInputException` in CI for a derived values file: no rule produces it.
