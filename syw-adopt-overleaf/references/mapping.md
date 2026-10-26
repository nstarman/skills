# Mapping an Overleaf project onto the SYW layout

SYW's `src/tex/` mirrors the Overleaf project root: `src/tex/figures/GD1/a.pdf` is
`figures/GD1/a.pdf` in Overleaf. Every Overleaf file goes in exactly one class.

| Class | What | Repository | `showyourwork.yml` |
|---|---|---|---|
| 1. Text | authored in Overleaf: `ms.tex`, `bib.bib` (after the rename), any `\input` sections | `src/tex/`, committed | `pull` |
| 2. Build output | made by code: `figures/**/*.pdf`, `output/**.tex` | `src/tex/figures`, `src/tex/output`, gitignored, regenerated | `push` |
| 3. Static support | needed to compile, not generated: `.cls`, `.bst`, logos, `preamble/*.sty` | `src/tex/`, committed | `push` (the repository is the source of truth) |
| 4. Not needed in Overleaf | code, data, lockfiles, notes, referee replies | code → `src/scripts`, data → `src/data`; private notes stay out of git | neither; pruned in phase 7 |

## Rules

- A path is never in both `pull` and `push`, also not as a folder in one covering a file in the
  other (SYW itself only rejects exact duplicates). No `push` entry covers a class-1 file.
  No entry covers a class-4 file. `scripts/check_lists.py` checks all three.
- `push`/`pull` entries are literal paths under `src/tex/` (files or folders), not globs. A pushed
  folder replaces the Overleaf folder of that name.
- A paper-local `\variable` macro is removed in favour of `showyourwork.sty`'s; the
  `\variable{output/…}` paths stay, so the text does not change.
- `make variables` / `variables.yml` become Snakefile rules per output group; only cited
  variables are generated (`syw-overleaf-dropbox/references/variables.md`).
- Figures follow `syw-overleaf-dropbox`: `calc_*` (heavy, cached) and `plot_*` (light).
- Submodules (a shared preamble) are vendored as plain class-3 files; no submodules in the new
  repository unless the author asks.
- Additional `\input` text files authored in Overleaf are class 1 and go into `pull`.

## Inventory format

`inventory.tsv` in the backup folder, tab-separated, `#` comments allowed:

```text
<class>	<path relative to the Overleaf root, post-rename>	<destination or note>
```

A class-4 note starting with `private` marks a file that must never be committed (notes, referee
replies); `public_check.sh` checks those. Other class-4 files (code, data, lockfiles) may move
into the repository.

## Worked example: CP1

CP1 ("Stellar Stream Straights and Convexities Constrain Dark Matter Nature and Geometry") keeps
code, data and a Python project inside the Overleaf project. Expected shape (confirm in the
survey; the real inventory is the one in the backup folder):

```text
1	ms.tex	src/tex/ms.tex (renamed from main.tex)
1	bib.bib	src/tex/bib.bib (renamed from main.bib)
2	figures/GD1/<figure>.pdf	built by a plot_* rule
2	output/<group>/<name>.tex	built by a variables rule
3	aastex701.cls	src/tex/
3	aasjournalv7.bst	src/tex/
3	orcid-ID.png	src/tex/
3	preamble/preamble-starkman.sty	src/tex/preamble/ (vendored if a submodule)
4	src/<package>/...	src/scripts/ (or a package the scripts import)
4	pyproject.toml	repository root
4	uv.lock	repository root
4	figures/<script>.py	src/scripts/
4	notes/<file>	private: stays out of git
```

Its push/pull lists then look like CP2's: push `src/tex/figures`, `src/tex/output`, the class,
bst, logo and preamble files; pull `src/tex/ms.tex`, `src/tex/bib.bib`.
