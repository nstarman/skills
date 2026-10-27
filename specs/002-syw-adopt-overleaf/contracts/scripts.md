# Contract: the skill's scripts

All in `syw-adopt-overleaf/scripts/`; standard-library Python 3.11+ or POSIX sh/Bash, plus `git`,
`gh`, `op`, poppler where noted. Exit codes: 0 ok, 1 check failed / differences found, 2 usage or
tool error. Nothing prints a token.

## `backup.sh`

```text
backup.sh --repo <old repo clone> --mirror <Dropbox mirror folder> --overleaf-id <id>
          --op-ref <op://… Overleaf token> --baseline <baseline.pdf> [--dest <backups root>]
```

- `--dest` defaults to `~/Documents Local/backups`; the folder `<old-repo>-<YYYY-MM-DD>` is
  created and must not exist. Refuses a destination under Dropbox or iCloud
  (`~/Library/CloudStorage`, `~/Library/Mobile Documents`).
- Writes and verifies the five parts (data-model.md), printing one `ok <part>` line each; on the
  first failure prints `FAILED <part>: <reason>` and exits 1, leaving what was written for
  inspection.
- Reads the repository, the mirror and Overleaf only; writes only inside the new folder.

## `pdf_diff.py`

```text
pdf_diff.py <baseline.pdf> <new.pdf> [--out DIR]
```

- Prints sections `pages`, `numbers`, `text`, `images` (research R5); each says `same` or lists
  differences with page numbers. Numbers as `p<N>: <old> → <new>`.
- With `--out`, writes `p<N>-baseline.png` and `p<N>-new.png` for each flagged page.
- Exit 0 only when every section is `same`.

## `check_lists.py`

```text
check_lists.py <overleaf block or showyourwork.yml> <inventory.tsv>
```

- Applies research R4's three rules; prints `ok` or one `FAIL <rule>: <path>` line per problem.

## `public_check.sh`

```text
public_check.sh <new repo> <repo.bundle> <inventory.tsv>
```

- Research R6: shared commits, token-like strings in history, private class-4 paths in history. Prints
  `ok <check>` or `FAIL <check>: <detail>` (a token match prints commit and path, never the match).
- Read-only on the new repository.

## `syw-overleaf-dropbox/scripts/check_build.sh` (changed)

- Same usage and output lines; figures are found with `find src/tex/figures -name '*.pdf'`, and
  each is compared with the mirror file at the same relative path
  (`src/tex/figures/GD1/a.pdf` ↔ `<mirror>/figures/GD1/a.pdf`). Output names the relative path
  (`figure GD1/a.pdf: …`).
