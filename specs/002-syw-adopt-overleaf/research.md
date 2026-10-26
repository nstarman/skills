# Phase 0 Research: syw-adopt-overleaf

Read on 2026-10-26 from the showyourwork development install used for CP2
(`showyourwork-main` env, 0.4.4.dev431+g44d15103f), CP2's repository (read-only) and the
`syw-overleaf-dropbox` skill.

## R1. When SYW touches Overleaf, and the "dry run"

- **Facts** (`workflow/prep.smk`, `workflow/build.smk`, `overleaf.py`):
  - Pull runs in the preprocess step, push in `onsuccess` of a build — **both only when the
    current git branch is `main`** and `overleaf.id` is set.
  - `push` and `pull` entries are literal paths under `src/tex/` (files or folders), no globs. A
    folder is copied whole (`copytree` after `rmtree` on the Overleaf side).
  - Pull refuses to overwrite a file whose last commit is not a `[showyourwork]` commit or that
    has uncommitted changes; it only logs an error unless configured otherwise.
  - Config validation rejects an exact path in both lists, but explicitly not a folder in one and
    a file inside it in the other.
  - There is **no dry-run option**.
- **Decision**: the phase-6 dry run is done without SYW contacting Overleaf:
  1. commit the `overleaf:` section on a branch **other than `main`** (so no build can sync);
  2. list what the push would write: every push entry expanded to the files under it in
     `src/tex/` after the local build;
  3. clone the Overleaf project into the scratch area (credential helper, R3) and `cmp` its
     `ms.tex`/`bib.bib` with the renamed mirror files and with `src/tex/`;
  4. `check_lists.py` (R4) on the final lists.
  After approval, merge to `main` and run the full build.
- **Alternatives**: patching SYW for a dry-run flag (out of scope; dev version is shared); a build
  on `main` with a bogus id (still runs pull code paths, confusing errors).

## R2. `showyourwork setup --overleaf` is not used

- **Fact**: `setup --overleaf=<id>` calls `setup_remote`, made for an *empty* Overleaf project; it
  refuses a non-empty one, and the module also has `wipe_remote`, which empties a project.
- **Decision**: the new repository is created with `showyourwork setup` **without** `--overleaf`;
  the `overleaf:` section is added by hand in phase 6. The runbook states this as a hard rule.

## R3. Overleaf git access without exposing the token

- **Decision**: clone with a one-shot credential helper that reads the token itself:
  `git -c credential.helper= -c 'credential.helper=!f() { echo username=git; echo "password=$(op read "$OP_REF")"; }; f' clone https://git@git.overleaf.com/<id>`.
  The token never appears in argv, the remote URL, `.git/config`, or output; afterwards the clone's
  remote URL is `https://git@git.overleaf.com/<id>` with no secret.
- **Rejected**: `https://git:<token>@…` URLs (SYW's own approach): the token is stored in the
  clone's `.git/config` and visible in `ps`.

## R4. `check_lists.py` input and rules

- **Input**: the `overleaf:` block as YAML text (the same snippet later pasted into
  `showyourwork.yml`, or `showyourwork.yml` itself), parsed with a minimal reader for its `push:`
  and `pull:` item lists (no YAML library, constitution VI); and the inventory (data-model.md).
- **Rules** (fail, naming each path):
  1. a path in both lists, **including** a folder in one covering a path in the other (closes the
     gap SYW leaves, R1);
  2. a push entry equal to or covering a class-1 (authored) path;
  3. any entry covering a class-4 path (keeps notes and referee replies out of git and out of the
     push).
- Coverage = equal, or the entry is a folder prefix of the path. Paths are compared relative to
  `src/tex/`.

## R5. `pdf_diff.py` method

- **Text**: `pdftotext -layout` per page; words compared over the whole document (reflow moves
  words between pages) with `difflib.SequenceMatcher`; replaced/inserted/deleted runs printed with
  page numbers.
- **Numbers**: number tokens (`-?\d+(\.\d+)?([eE][-+]?\d+)?`, also with `,` thousands) extracted
  in order and diffed on their own, each change printed `old → new` with its page.
- **Images**: `pdftoppm -r 100` to PPM (P6), parsed with the standard library; a page is flagged if
  more than 0.1 % of its pixels differ by more than 16 levels in any channel (absorbs
  antialiasing, catches a moved marker or a changed tick label). Flagged pages are rendered again
  as PNG for both PDFs into `--out` (poppler writes the PNGs; no image library).
- **Pages**: `pdfinfo` page counts; common pages compared, extra pages reported.
- **Exit**: 0 = no differences; 1 = differences; 2 = usage or tool error.

## R6. `public_check.sh`: what "from the old history" means

- **Decision**: fail on any **commit** of the new repository that is also in `repo.bundle`
  (bundle cloned into a temporary folder; the new repository never fetches it). Shared *blobs*
  are expected and not a leak (e.g. `aastex701.cls`, or `ms.tex` identical to an old version), so
  they are not checked.
- Also fail on: token-like strings in any commit's content (`olp_`, `ghp_`, `gho_`,
  `github_pat_`, `access_token=`, `-----BEGIN … PRIVATE KEY`), via `git grep` over `rev-list --all`;
  and any class-4 inventory path present in any commit (`git log --all --name-only`).

## R7. Baseline PDF must not be compiled in the mirror

- **Fact**: the mirror is synced to Overleaf; aux files written there would appear in the
  co-authors' project.
- **Decision**: phase 0 compiles a temporary copy of the mirror (latexmk, or Overleaf's own
  download of the compiled PDF if the local toolchain cannot build it); the copy is deleted, the
  PDF goes to the backup folder.

## R8. Tests need poppler

- **Decision**: tests generate tiny PDFs with a stdlib writer (one page of Helvetica text, or a
  filled rectangle) and skip with a message when `pdftotext` is missing; `check.yml` installs
  `poppler-utils` with apt so they run in CI. No new secrets.

## R9. CP2 as the reference layout

- CP2's history: `[showyourwork] first commit`, then `[showyourwork] migrate paper sources and
  generation DAG`; push list = `src/tex/figures`, `src/tex/output`, class/bst files and the four
  `preamble/*.sty`; pull list = `ms.tex`, `bib.bib`; `.gitignore` ignores `src/tex/figures/*`. CP1
  follows the same shape. CP2's later fixes (FontAwesome collisions, stylesheet dependency,
  `local_cache` for hours-long rules, Zenodo Sandbox inputs) go into `references/lessons.md`.
