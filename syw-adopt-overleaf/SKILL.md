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
    --op-ref 'op://<vault>/<item>/credential' --baseline baseline.pdf
```

Writes `~/Documents Local/backups/<old-repo>-<YYYY-MM-DD>/` (refuses Dropbox/iCloud and an
existing folder) with `repo.bundle`, `mirror.tar.gz`, `overleaf/` (clone with Overleaf's
history), `baseline.pdf`, `secrets.txt` (names only) and a `MIGRATION.md` from
`references/migration-template.md`; every part verified. Move `inventory.tsv` there.
⛔ Show the `ok` lines; the author confirms before anything changes.

### 2. Freeze Overleaf

Draft a short message asking co-authors not to edit until the migration is done (expected
duration, who to contact). The author sends it. Record Overleaf's HEAD (from the backup clone) in
`MIGRATION.md` → Freeze.

### 3. Build the SYW layout locally

In a new folder `<parent>/paper-<slug>/` (a new repository; nothing from the old one's `.git`):

1. `showyourwork setup` (no `--overleaf`) with the agreed SYW version → commit 1,
   `[showyourwork] first commit`.
2. Place files per the inventory (`references/mapping.md`): text from **the backup's Overleaf
   clone** under its new names `src/tex/ms.tex`, `src/tex/bib.bib` (and `\bibliography{bib}`);
   class-3 files into `src/tex/`; code to `src/scripts/`, data to `src/data/`; Snakefile rules for
   every figure and cited number. Commit 2, `[showyourwork] migrate paper sources`.
3. `showyourwork.yml` has **no `overleaf:` section yet**. Draft the push/pull lists in
   `MIGRATION.md` and run `scripts/check_lists.py <draft> inventory.tsv` until `ok`.

### 4. Build and compare ⛔

Build locally (Zenodo token inline if the paper caches on Zenodo). Then:

```sh
scripts/pdf_diff.py baseline.pdf ms.pdf --out pdf-diff/
```

Show every section that differs (`numbers` first, then `images` with the PNGs, then `text`,
`pages`). For each difference: find the cause (code, data, a hand-edited figure, a font), fix
what is a migration error, and leave what the author accepts. Repeat 3–4. ⛔ The author accepts
the remaining differences, one by one; record them in `MIGRATION.md` → PDF differences.

### 5. Create the new repository ⛔

⛔ Then `gh repo create <owner>/paper-<slug> --private --source . --push`. The author sets the
secrets (`OVERLEAF_TOKEN`, and `SANDBOX_TOKEN`/`ZENODO_TOKEN` if used) in the GitHub UI or with
`op read … | gh secret set NAME -R <owner>/paper-<slug>` run themselves. The old repository is
not touched.

### 6. Rename, then first sync

Still frozen; compare Overleaf's HEAD with the one recorded at the freeze, and stop to reconcile
if a co-author edited.

1. In the mirror: rename `main.tex`→`ms.tex`, `main.bib`→`bib.bib`; change
   `\bibliography{main}`→`\bibliography{bib}` with an exact-match edit (as
   `syw-overleaf-dropbox`'s `mirror_edit.py`). Wait for Dropbox to sync.
2. ⛔ The author sets Overleaf **Menu → Main document** to `ms.tex`.
3. The author recompiles in Overleaf and downloads the PDF; `pdf_diff.py baseline.pdf <it>`
   shows no differences (the text did not change).
4. **Dry run.** SYW pulls and pushes only on branch `main`, and has no dry-run flag. So, on a
   branch `overleaf-sync` (not `main`): add the `overleaf:` section (`id`,
   `gh_actions_sync: true`, the checked lists) and commit it, **unpushed**. Then show the author:
   - every file the push would write: each `push` entry expanded to the files under it in
     `src/tex/` after the build;
   - a fresh Overleaf clone (credential helper as in `backup.sh`, into a temporary folder):
     `cmp` its `ms.tex`/`bib.bib` with the mirror and with `src/tex/` — byte-identical;
   - `check_lists.py showyourwork.yml inventory.tsv` → `ok`.
   ⛔ The author approves.
5. Merge to `main`, run the full SYW build (pull, build, push; tokens inline). Overleaf
   compiles; its PDF passes `pdf_diff.py` against the accepted local `ms.pdf`. Push to GitHub.

### 7. Prune ⛔

List the Overleaf files that are class 4 (code, data, lockfiles, notes now kept elsewhere).
⛔ The author approves the list; delete them in the mirror; Overleaf compiles again. The author
tells co-authors the freeze is over.

### 8. Hand off ⛔

1. `sh <syw-overleaf-dropbox>/scripts/check_build.sh "<mirror>" build.log` in the new repository:
   push found, no missing variables, every figure (subfolders too) same as the mirror.
2. ⛔ Archive the old repository: `gh repo archive <owner>/<old> --yes`. Deleting it is the
   author's call, not part of this runbook.
3. Point the author to `syw-overleaf-dropbox` for daily work and `syw-site init` for a paper site.
4. New gotchas go into `references/lessons.md`.

## Before the repository is ever made public

The author decides when (typically at arXiv). First run:

```sh
scripts/public_check.sh <new repo> <backup>/repo.bundle <backup>/inventory.tsv
```

It fails on any commit shared with the old repository, a token-like string anywhere in history,
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
