# syw-adopt-overleaf — agreed design (input to /speckit-specify and /speckit-plan)

Agreed with the author on 2026-10-26, section by section.

## Goal

A local skill, `syw-adopt-overleaf`, that migrates an existing paper — one with a live Overleaf
project and a private git repository — into a fresh showyourwork (SYW) repository, without losing
or silently changing anything. When it finishes, the paper is in the state the
`syw-overleaf-dropbox` skill expects, and `syw-site init` can follow.

First real case: Convexity Paper 1 (`nstarman/stream_convexity_rates_paper`, submitted; Overleaf
mirror `~/Library/CloudStorage/Dropbox/Apps/Overleaf/Stellar Stream Straights and Convexities
Constrain Dark Matter Nature and Geometry/`). Run in a separate session after the skill ships.

## Decisions

| Question | Decision | Why |
|---|---|---|
| Which Overleaf project? | The **existing** project, in place | Co-authors, share links and Overleaf history stay put. |
| Old git history | **Gone**: a **new repository**, history starting at `[showyourwork] first commit` | A force-push to the old repository does not remove history on GitHub (`refs/pull/*`, commits reachable by SHA); the new repository may become public, the old history must never. |
| New repository name | `paper-<slug>` (prefix convention from now on), slug proposed from the title, confirmed by the author | Author's naming convention. |
| Old repository | Stays private; archived (read-only) once the migration passes; deleting it is the author's call | Archive is reversible; the git bundle in the backup is the permanent copy. |
| File names | **Rename** `main.tex`→`ms.tex`, `main.bib`→`bib.bib` in Overleaf | Keeps every paper on SYW defaults, so `syw-overleaf-dropbox` works unchanged. |
| Figures and numbers | **Regenerate from code, then diff** against the pre-migration PDF; every difference shown and accepted by the author | Reproducible paper, no silent drift in a submitted paper. |
| Files Overleaf does not need (code, data, lockfiles) | **Prune** after the first build, from an approved list | Avoids stale copies co-authors might edit; Overleaf history and the backup keep them. |
| Form of the skill | A **runbook with checkpoints** plus small scripts for the exact parts | Mapping a paper is judgment; backup and PDF comparison must be exact. A scripted `adopt` command waits until 2–3 migrations show what repeats. |

## Phases (⛔ = stops for the author's explicit yes)

0. **Survey (read-only).** Locate the repository, the Dropbox mirror, the Overleaf project id.
   Inventory every Overleaf file into one of four classes (Section "Mapping"). Compile the current
   Overleaf paper as `baseline.pdf`. Start `MIGRATION.md` in the backup folder: findings, the
   inventory table, and every decision as it is made.
1. **Backup** (`scripts/backup.sh`), to `~/Documents Local/backups/<old-repo>-<YYYY-MM-DD>/` —
   outside Dropbox and iCloud:
   - `repo.bundle`: `git bundle create --all` of the old repository (all branches and tags);
   - `mirror.tar.gz`: the Dropbox mirror folder;
   - `overleaf/`: a fresh clone of the Overleaf git remote (carries Overleaf's own history), token
     read inline with `op read`, never written or printed;
   - `baseline.pdf`;
   - `secrets.txt`: the old repository's secret *names* only (`gh secret list`).
   The script verifies (`git bundle verify`, `tar -tzf`, the clone's `git fsck`) and fails loudly.
   ⛔ The author confirms the backup before anything changes.
2. **Freeze Overleaf.** Draft a message asking co-authors to stop editing until the migration is
   done; the author sends it. Record Overleaf's latest commit in `MIGRATION.md`.
3. **Build the SYW layout locally** in a new folder `<parent>/paper-<slug>/`, a new git repository
   that never fetches from the old one:
   - commit 1, `[showyourwork] first commit`: from the SYW template (dev version, as CP2);
   - commit 2, `migrate paper sources`: files placed per "Mapping"; Snakefile rules for figures and
     numbers. Text is taken from the Overleaf backup clone, not the old repository (Overleaf is the
     text's source of truth), already under its new names (`src/tex/ms.tex`, `src/tex/bib.bib`).
     `showyourwork.yml` has **no `overleaf:` section yet**, so neither a local build nor CI on the
     new repository can pull from or push to Overleaf before phase 6; the push/pull lists are
     drafted in `MIGRATION.md` and checked with `check_lists.py`.
4. **Build locally without Overleaf** (no `overleaf:` section, so no pull or push), with
   `SANDBOX_TOKEN` if the paper uses Zenodo caches. Run `scripts/pdf_diff.py baseline.pdf ms.pdf`.
   ⛔ The author reviews every difference; repeat 3–4 until accepted. The acceptance is recorded in
   `MIGRATION.md`.
5. **Create the new repository.** ⛔ Then: `gh repo create nstarman/paper-<slug> --private`, push,
   and the author sets `OVERLEAF_TOKEN` and `SANDBOX_TOKEN` (GitHub UI, or
   `op read … | gh secret set NAME`, never through the agent's output). The old repository is not
   touched in this phase.
6. **Rename, then first sync.** While frozen:
   1. In the mirror, rename `main.tex`→`ms.tex`, `main.bib`→`bib.bib`, and change
      `\bibliography{main}`→`\bibliography{bib}` (exact-match edit).
   2. ⛔ The author sets Overleaf **Menu → Main document** to `ms.tex` (UI only).
   3. Overleaf's compiled PDF still passes `pdf_diff.py` against the baseline.
   4. Add the `overleaf:` section (id, `gh_actions_sync: true`, the checked push/pull lists) in a
      commit that is not yet pushed to GitHub.
      Dry run: list exactly the Overleaf files the push would write, and check that the pulled
      `ms.tex`/`bib.bib` are byte-identical to the renamed mirror files. ⛔ The author approves.
   5. Full SYW build (pull, build, push). Overleaf compiles; its PDF passes `pdf_diff.py` against
      the accepted local `ms.pdf`.
7. **Prune.** ⛔ The author approves the list of Overleaf files to delete (class 4); delete them in
   the mirror; Overleaf compiles again. Unfreeze: the author tells co-authors.
8. **Hand off.** Run `syw-overleaf-dropbox`'s `scripts/check_build.sh` against the new repository
   and the mirror; it must be clean. ⛔ Archive the old repository. Point to
   `syw-overleaf-dropbox` for daily work and `syw-site init` for the paper site. New gotchas go into
   this skill's `references/`.

**Rollback**, documented with exact commands in `references/rollback.md`: Overleaf — push the
backup clone back to the Overleaf remote, or restore from Overleaf's history; the old repository is
never modified before phase 8 (archive is undone with `gh repo unarchive`); the new repository and
folder can simply be deleted before the author has used them.

**Before the new repository is ever made public** (the author's call, typically at arXiv),
`scripts/public_check.sh`: no object in the new repository is reachable from the old one's history
(compare against `repo.bundle`), no token-like strings in the tree or history, no class-4 Overleaf
files (notes, referee replies) committed.

## Mapping Overleaf to the SYW layout

SYW's `src/tex/` mirrors the Overleaf project root. Every Overleaf file goes in exactly one class:

| Class | CP1 examples | Repository | `showyourwork.yml` |
|---|---|---|---|
| 1. Text (authored in Overleaf) | `ms.tex`, `bib.bib` (after the rename) | `src/tex/` | `pull` |
| 2. Build output (made by code) | `figures/**/*.pdf`, `output/**.tex` | `src/tex/figures`, `src/tex/output` — gitignored, regenerated | `push` |
| 3. Static support (needed to compile, not generated) | `aastex701.cls`, `aasjournalv7.bst`, `orcid-ID.png`, `preamble/*.sty` | `src/tex/`, committed | `push` (repository is the source of truth) |
| 4. Overleaf-only / not needed | `src/`, `uv.lock`, `pyproject.toml`, scripts and data under `figures/`, `notes/` | code and data move to `src/scripts`, `src/data`; notes stay out of git | neither; pruned in phase 7 |

Rules:

- A path is never in both `pull` and `push`, and no `push` pattern matches a class-1 file
  (`scripts/check_lists.py` checks the lists against the inventory).
- A paper-local `\variable` macro is removed in favour of `showyourwork.sty`'s; `\variable{output/…}`
  paths stay as they are, so the text does not change.
- `make variables` / `variables.yml` become Snakefile rules per output group; only cited variables
  are generated (as `syw-overleaf-dropbox/references/variables.md` describes).
- Figures follow `syw-overleaf-dropbox`: `calc_*` (heavy, cached) and `plot_*` (light) scripts.
- Submodules (e.g. a shared preamble) are vendored as plain files in class 3; the new repository
  has no submodules unless the author asks.

## `scripts/pdf_diff.py`

`pdf_diff.py <baseline.pdf> <new.pdf> [--out DIR]` — standard-library Python plus poppler
(`pdftotext`, `pdftoppm`, `pdfinfo`), per constitution VI.

- **Text:** `pdftotext -layout` per page; a word-level `difflib` diff; numbers extracted and
  compared on their own, so `0.43 → 0.44` is listed explicitly rather than lost in reflow.
- **Images:** each page rendered with `pdftoppm -r 100` to PPM (parsed with the standard library);
  pages whose pixels differ beyond a small tolerance are flagged, and both pages are also rendered
  to PNG in `--out` for the author to view.
- **Page count** reported separately.
- Exit 0 only if nothing differs. Accepting differences is the author's decision, recorded in
  `MIGRATION.md`; the script never accepts.

## Compatibility with `syw-overleaf-dropbox`

The result uses SYW defaults (`ms.tex`, `bib.bib`, `ms.pdf`, `src/tex/figures`, `src/tex/output`),
so the existing skill applies unchanged, with one fix that ships in the same change:
`check_build.sh` compares only `src/tex/figures/*.pdf`; it must search `src/tex/figures`
recursively (CP1 keeps figures in subfolders such as `figures/GD1/`).

## Skill layout

```
syw-adopt-overleaf/
  SKILL.md                 the phased runbook; when to use; the ⛔ gates; hand-off
  card.json
  references/
    mapping.md             the four classes, rules, worked CP1 example
    rollback.md            exact restore commands per phase
    lessons.md             CP2 and later migrations: what went wrong and why
  scripts/
    backup.sh              phase 1; verifies what it wrote
    pdf_diff.py            phases 4 and 6
    check_lists.py         push/pull lists vs the inventory
    public_check.sh        before making the repository public
```

Tests in `tests/` (constitution: `python -m unittest discover tests`): `pdf_diff.py` on two small
generated PDFs (identical, a changed number, an extra page); `check_lists.py` on overlapping and
clean lists.

## Constraints

- Never bypass git commit signing (1Password); on a signing failure, ask the author to unlock it.
- Tokens only inline from `op read`; never written, printed or logged; redact `access_token=` in
  logs.
- Pre-arXiv content is never published: the new repository is created private, the docs site stays
  local (`publish: false`).
- The skill does not touch the author's other repositories, branches, worktrees or uncommitted work.
- The agent never sends the freeze message, sets the Overleaf main document, sets repository
  secrets, or changes repository visibility; it prepares, the author acts.

## Out of scope

- A scripted `adopt` command (revisit after 2–3 migrations).
- Renaming existing SYW repositories (e.g. CP2) to `paper-*`.
- The paper site itself (`syw-site`), beyond pointing to `syw-site init`.
