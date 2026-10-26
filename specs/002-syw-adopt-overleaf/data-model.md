# Data model: syw-adopt-overleaf

## Backup folder

`~/Documents Local/backups/<old-repo>-<YYYY-MM-DD>/` (outside Dropbox and iCloud; `backup.sh`
refuses a path under either):

| File | Content | Verified by |
|---|---|---|
| `repo.bundle` | `git bundle create --all` of the old repository | `git bundle verify` |
| `mirror.tar.gz` | the Dropbox mirror folder | `tar -tzf` lists every file (count matches) |
| `overleaf/` | clone of the Overleaf git remote, no secret in its config (research R3) | `git fsck`, no `olp_`/token in `.git/config` |
| `baseline.pdf` | the paper compiled before the migration (R7) | `pdfinfo` reads it |
| `secrets.txt` | `gh secret list` of the old repository: names and dates only | exists (may list none) |
| `MIGRATION.md` | the migration record (below) | — |

The folder must not exist beforehand (no overwriting a previous backup).

## Inventory

A tab-separated file `inventory.tsv` in the backup folder, one line per Overleaf file, `#`
comments allowed:

```text
<class>\t<path relative to the Overleaf root>\t<destination or note>
1	ms.tex	src/tex/ms.tex (renamed from main.tex)
2	figures/GD1/track.pdf	built by src/scripts/plot_gd1.py
3	aastex701.cls	src/tex/aastex701.cls
4	uv.lock	moves to the repository root
4	notes/referee.md	private: stays out of git; pruned in phase 7
```

- Class: `1` authored text, `2` build output, `3` static support, `4` not needed (design.md
  "Mapping").
- A class-4 note starting with `private` marks a file that must never be committed (notes,
  referee replies); `public_check.sh` checks those. Other class-4 files (code, data, lockfiles)
  may move into the repository.
- Every file in the Overleaf clone appears exactly once (the runbook checks with
  `git -C overleaf ls-files` against the inventory). Paths are the **post-rename** names; the
  rename is noted in column 3.

## `MIGRATION.md`

Sections, filled as the migration goes (template in `references/migration-template.md`):

1. **Sources** — old repository, mirror path, Overleaf project id, slug, new repository.
2. **Findings** — survey notes (submodules, custom `\variable`, build system, data locations).
3. **Inventory** — counts per class; points to `inventory.tsv`.
4. **Gates** — one line per ⛔: phase, what was shown, the author's answer, date.
5. **Freeze** — Overleaf commit at the freeze; at the first sync (must match, or reconcile).
6. **PDF differences** — each `pdf_diff.py` run: what differed, the author's decision.
7. **Push / pull lists** — the drafted `overleaf:` block and the `check_lists.py` result.
8. **Prune list** — the approved class-4 deletions.

## Phase state

Phases 0–8 run in order; a phase starts only when the previous phase's gate (if any) has a
recorded yes in `MIGRATION.md`. The old repository's state changes only in phase 8 (archived).
The Overleaf project changes only in phases 6 (rename, first push) and 7 (prune).
