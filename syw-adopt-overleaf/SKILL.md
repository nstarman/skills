---
name: syw-adopt-overleaf
description: Runbook for moving an existing paper (a live Overleaf project, often with co-authors, plus a private git repository) into a fresh showyourwork (SYW) repository without losing or silently changing anything. Backs up first, rebuilds figures and numbers from code and compares the new PDF with the old one, keeps the old git history private, and stops for the author's yes before every irreversible step. Use this whenever the user wants to "adopt", "migrate", "convert" or "move" a paper to showyourwork, put an existing Overleaf paper under SYW, or make an older paper reproducible, even if they only say "set up showyourwork for this paper". Afterwards the paper is ready for syw-overleaf-dropbox (daily work) and syw-site init (paper site).
---

# Moving an existing Overleaf paper into showyourwork

The paper is real, often submitted, and other people edit it. Nothing may be lost, no number
may change silently, and the old repository's history must never become public. So the
migration is a runbook with checkpoints: the agent prepares, the author decides.

**The result:** a new private repository `paper-<slug>` whose history starts at
`[showyourwork] first commit`; the *same* Overleaf project (same co-authors, links and history)
with the text renamed to SYW's defaults `ms.tex` / `bib.bib`; figures and numbers built by code;
the old repository archived, untouched otherwise.

## Hard rules

- **⛔ gates.** Every step marked ⛔ below waits for the author's explicit yes in chat. Record
  each answer in `MIGRATION.md` (one line: phase, what was shown, answer, date).
- **The author acts, the agent prepares**: sending the co-author freeze message, setting
  Overleaf's main document, setting repository secrets, changing repository visibility.
- **Never `showyourwork setup --overleaf=<id>`** on an existing project: that code path is for an
  empty project and SYW also ships a function that wipes one. Set up without `--overleaf`; the
  `overleaf:` section is added by hand in phase 6.
- **The new repository never fetches from the old one** (no `git remote add old`, no
  `git fetch <bundle>`). Text comes from the Overleaf clone, code is copied as files.
- **Tokens** are read inline (`op read`) on the one command that needs them, never printed,
  written, logged or put in a URL. Redact `access_token=` when reading SYW logs.
- **Signing:** never bypass commit signing. If signing fails, ask the author to unlock 1Password.
- **Private until arXiv:** the repository is created private; any docs site stays local.
- **Never compile in the Dropbox mirror:** aux files there sync into the co-authors' project.
  Compile a temporary copy.
- Touch nothing else of the author's: other repositories, branches, worktrees, uncommitted work.

## Before starting

Find, and write into `MIGRATION.md` → Sources: the old repository (local clone and
`owner/name`), the Dropbox mirror (`~/Library/CloudStorage/Dropbox/Apps/Overleaf/<Project>/`),
the Overleaf project id (Overleaf → Menu → Git, or the project URL), the 1Password reference of
the Overleaf git token, and the SYW version to use (ask; e.g. a development install). Propose a
slug from the title (short, lowercase, hyphens) and get the author's confirmation of
`paper-<slug>`.

## Phases

### 0. Survey (read-only)

1. Read the paper's build: main file, bibliography, class/bst files, preamble packages,
   submodules, any `\variable`-like macro, `make variables` / `variables.yml`, figure scripts,
   data locations, lockfiles.
2. Compile the current Overleaf text **in a temporary copy of the mirror** (latexmk) — or, if the
   local toolchain cannot build it, ask the author to download Overleaf's compiled PDF. That PDF
   is `baseline.pdf`.
3. Inventory every Overleaf file into `inventory.tsv` (class 1–4, see `references/mapping.md`),
   using the post-rename names. Check that every file in the Overleaf project appears exactly
   once.

### 1. Backup ⛔

```sh
scripts/backup.sh --repo <old clone> --mirror "<mirror>" --overleaf-id <id> \
    --op-ref 'op://<vault>/<item>/credential' --baseline baseline.pdf [--github <owner/name>]
```

`--github` is needed when the old repository has no `origin` (for example when it *is* the
Dropbox mirror folder); if GitHub holds a different history (Overleaf's own GitHub sync), it is
bundled too, as `github.bundle`.

Writes `~/Documents Local/backups/<old-repo>-<YYYY-MM-DD>/` (refuses Dropbox/iCloud and an
existing folder) with `repo.bundle`, `mirror.tar.gz`, `overleaf/` (clone with Overleaf's
history), `baseline.pdf`, `secrets.txt` (names only) and a `MIGRATION.md` from
`references/migration-template.md`; every part verified. Move `inventory.tsv` there.
⛔ Show the `ok` lines; the author confirms before anything changes.

### 2. Freeze Overleaf

Draft a short message asking co-authors not to edit until the migration is done (expected
duration, who to contact). The author sends it. If the Overleaf project is linked to a GitHub
repository through Overleaf's own GitHub integration (Menu → GitHub), note it: Overleaf cannot
unlink a single project, so from now on nobody uses that menu, and phase 8 retires the repository.
Record Overleaf's HEAD (from the backup clone) in `MIGRATION.md` → Freeze.

### 3. Build the SYW layout locally

In a new folder `<parent>/paper-<slug>/` (a new repository; nothing from the old one's `.git`):

1. `showyourwork setup` (no `--overleaf`) with the agreed SYW version → commit 1,
   `[showyourwork] first commit`.
2. Place files per the inventory (`references/mapping.md`): text from **the backup's Overleaf
   clone** under its new names `src/tex/ms.tex`, `src/tex/bib.bib` (and `\bibliography{bib}`);
   class-3 files into `src/tex/`; code to `src/scripts/`, data to `src/data/`; Snakefile rules for
   every figure and cited number. Keep every `ms.tex` change in an exact-match edit script in the
   backup folder (`ms_edits.py`): phase 6 replays it on Overleaf so the first pull is
   byte-identical. The usual edits, and the other first-build failures, are in
   `references/lessons.md` (CP1).
2. Run the old tests. Point pytest's `testpaths` at the package, never at `src/scripts`:
   importing a figure script runs it. Commit 2, `[showyourwork] migrate paper sources`. The
   prefix matters: SYW's pull refuses to overwrite a file whose last commit is not a
   `[showyourwork]` commit.
3. `showyourwork.yml` has **no `overleaf:` section yet**. Draft the push/pull lists in
   `MIGRATION.md` and run `scripts/check_lists.py <draft> inventory.tsv` until `ok`. Its
   `deleted:` lines are the class-4 files the first push removes from Overleaf (a pushed folder
   replaces the whole Overleaf folder); they are approved at the dry run.

### 4. Build and compare ⛔

Build locally (Zenodo token inline if the paper caches on Zenodo). Then:

```sh
scripts/pdf_diff.py baseline.pdf ms.pdf --out pdf-diff/
```

Show every section that differs (`numbers` first, then `images` with the PNGs, then `text`,
`pages`). For each difference: find the cause (code, data, a hand-edited figure, a font), fix
what is a migration error, and leave what the author accepts. Repeat 3–4. ⛔ The author accepts
the remaining differences, one by one; record them in `MIGRATION.md` → PDF differences.

SYW compiles with tectonic and Overleaf with pdflatex, so `ms.pdf` differs from the baseline
everywhere (hyphenation, line numbers, the SYW stamp) and that diff hides real changes. Compare
the parts instead: each regenerated figure against the old one (`pdf_diff.py`), every generated
number file byte for byte, and the migrated `src/tex/` compiled with pdflatex in a temporary
copy against the baseline (expect only `\today`). Then show the author the two PDFs side by side,
page by page: a figure moving to another page is layout work they will want to know about.

### 5. Create the new repository ⛔

**If any rule is `cache: True`, seed the Zenodo cache before `main` reaches GitHub.** With no
Sandbox DOI in `zenodo.yml`, CI does not treat those rules as cached and runs them (CP1's 21-hour
rule ran on a runner until cancelled). ⛔ With the author's yes, `showyourwork cache create`
(token inline) makes a private Sandbox draft and writes its DOI. To upload existing results
instead of recomputing:

1. Read the rule's cache key without letting any script run: build once with
   `UV_CONFIG_FILE=/nonexistent` (every `uv run` then exits at once; the key is not affected) and
   take the hash from `Searching for file \`<rule>\` with hash \`<key>\`` in
   `.showyourwork/logs/showyourwork.log`.
2. Copy the results to `.showyourwork/cache/<key>` (a folder for a directory output, the file
   plus its extension otherwise).
3. Build normally (with any `local_cache` entry for that rule off for this one build): SYW restores
   from the local cache and uploads to the draft. The draft's notes list each rule's key.

Then ⛔ `gh repo create <owner>/paper-<slug> --private --source . --push`. The author sets the
secrets (`OVERLEAF_TOKEN`, and `SANDBOX_TOKEN`/`ZENODO_TOKEN` if used) in the GitHub UI or with
`op read … | gh secret set NAME -R <owner>/paper-<slug>` run themselves. Watch the first CI run:
it should restore cached rules (`Restoring from Zenodo Sandbox cache`), not run them. The old
repository is not touched.

### 6. Rename, then first sync

Still frozen; compare Overleaf's HEAD with the one recorded at the freeze, and stop to reconcile
if a co-author edited.

1. ⛔ In a fresh Overleaf clone (credential helper as in `backup.sh`, in a temporary folder):
   `git mv main.tex ms.tex`, `git mv main.bib bib.bib`, run `ms_edits.py ms.tex`, add
   `showyourwork.sty` (the edited `ms.tex` loads it, so Overleaf cannot compile without it).
   `cmp` `ms.tex`/`bib.bib` with `src/tex/`: byte-identical. Show the diff, commit, push.
2. ⛔ The author sets Overleaf **Menu → Main document** to `ms.tex`.
3. The author recompiles in Overleaf and downloads the PDF; `pdf_diff.py baseline.pdf <it>`
   shows only `\today` (and, if Overleaf's pdfTeX differs from the local one, sub-pixel
   anti-aliasing in figures; zoom in to confirm).
4. **Dry run.** SYW pulls and pushes only on branch `main`, and has no dry-run flag. So, on a
   branch `overleaf-sync` (not `main`): add the `overleaf:` section (`id`,
   `gh_actions_sync: true`, the checked lists) and commit it, **unpushed**. Simulate the push on
   a copy of a fresh Overleaf clone: for each `push` entry, delete the Overleaf folder and copy
   `src/tex/<entry>` in its place (files: copy over); `git add -A; git status --short`. Show the
   author:
   - every write and **every deletion**, with where each deleted file lives afterwards (the
     repository by content hash, regenerated by a rule, or the backup only). Files only in the
     backup are the author's call: keep them in the repository (gitignored if private) or not;
   - `ms.tex`/`bib.bib` in the clone byte-identical to `src/tex/`;
   - `check_lists.py showyourwork.yml inventory.tsv` → `ok`, its `deleted:` count matching.
   ⛔ The author approves.
5. Merge to `main`. Read each token into a variable and check it is non-empty first (a timed-out
   `op read` gives an empty string and SYW then skips the sync quietly). Run the full SYW build
   (pull, build, push). SYW pushes from an `onsuccess` handler that Snakemake skips when there is
   nothing to do: if the log has no `Pushing changes to Overleaf`, delete `ms.pdf` and build
   again. Compare Overleaf's new commit with the dry run (same files, same change types; pushed
   figures identical to the old ones). Push to GitHub.
6. The first CI run on `main` syncs Overleaf with **CI's** build. Compare every figure it pushed
   with the local one: `pdfinfo` page size, then `pdf_diff.py`. CP1 hit two CI-only failures
   here (cached outputs in `src/tex/` crashing the cache restore; a figure whose size depended on
   the matplotlib backend); both are in `references/lessons.md`.

### 7. Prune ⛔

List every file in a fresh Overleaf clone that the sync lists do not cover, with its class and
its identical copy in the repository, if any. ⛔ The author approves the list (keeping a file is
an answer). Delete them in the clone, compile that exact tree with pdflatex in a temporary copy
(it must still build), then commit and push. Overleaf's git access does not export hidden
folders (`.vscode/`, `.figure-baseline/`): the author deletes those in Overleaf's file tree.
The author recompiles in Overleaf and tells co-authors the freeze is over.

The Dropbox mirror may still hold the old checkout (`.git`, `.venv`, notes) next to Overleaf's
files. ⛔ With the author's choice for it, delete only files whose content is in
`mirror.tar.gz`; afterwards the mirror's file set must equal Overleaf's exactly.

### 8. Hand off ⛔

1. `sh <syw-overleaf-dropbox>/scripts/check_build.sh "<mirror>" build.log` in the new repository:
   push found, no missing variables, every figure (subfolders too) same as the mirror. With
   `gh_actions_sync`, a figure CI rebuilt differs in bytes from the local one; compare content.
2. Check the old GitHub repository against the backup before retiring it: a fresh
   `git clone --mirror` has the same refs as the bundle; list what lives only on GitHub (issues,
   PRs and comments, releases, wiki, secrets, Actions artifacts); and look up every blob in its
   history (`git rev-list --objects --all`) in the new repository, `repo.bundle`, the Overleaf
   backup, `mirror.tar.gz` and any submodule's repository. Report the blobs found only on GitHub.
   ⛔ Then archive (`gh repo archive <owner>/<old> --yes`) or, if the author asks, delete
   (`gh repo delete`; needs `gh auth refresh -h github.com -s delete_repo`, run by the author).
   Overleaf's GitHub link cannot be removed per project; an archived or deleted repository makes
   any accidental push from Overleaf's GitHub menu fail.
3. Point the author to `syw-overleaf-dropbox` for daily work and `syw-site init` for a paper site.
4. New gotchas go into `references/lessons.md`.

## Before the repository is ever made public

The author decides when (typically at arXiv). First run:

```sh
scripts/public_check.sh <new repo> <backup>/repo.bundle <backup>/inventory.tsv
```

Run it once per bundle (`repo.bundle`, and `github.bundle` if there is one). It fails on any
commit shared with the old repository, a token-like string anywhere in history,
or a class-4 file marked `private` ever committed. Identical file contents are fine.

## If something goes wrong

Every phase has restore steps in `references/rollback.md`. In short: the old repository is
unchanged until phase 8; Overleaf can be restored from the backup clone or Overleaf's history;
the new repository and folder can be deleted until the author has used them.

## Files

- `references/mapping.md` — the four classes, rules, inventory format, CP1 example.
- `references/rollback.md` — restore commands per phase.
- `references/lessons.md` — what went wrong in earlier migrations, and why.
- `references/migration-template.md` — the `MIGRATION.md` skeleton.
- `scripts/backup.sh`, `scripts/pdf_diff.py`, `scripts/check_lists.py`, `scripts/public_check.sh`
  — run each with no arguments for usage. `pdf_diff.py` needs poppler.
