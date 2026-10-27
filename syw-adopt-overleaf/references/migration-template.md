# Migration record: <paper title>

Private: this file lives in the backup folder, never in a repository.

## 1. Sources

- Old repository: `<owner>/<name>` (local clone: `<path>`)
- Dropbox mirror: `<path>`
- Overleaf project id: `<id>`
- Overleaf token: `op://<vault>/<item>/credential` (reference only)
- SYW version: `<version / commit>`
- New repository: `<owner>/paper-<slug>` (local: `<path>`)

## 2. Findings

- Main file / bibliography / class:
- Submodules:
- Custom `\variable` or number macros:
- Figure scripts and data:
- Build system (make, variables.yml, …):
- Anything unusual:

## 3. Inventory

`inventory.tsv` in this folder. Counts: class 1 = , 2 = , 3 = , 4 = (private: ).

## 4. Gates

| Phase | Shown | Answer | Date |
|---|---|---|---|
| 1 backup | | | |
| 4 PDF differences | | | |
| 5 create repository | | | |
| 6.2 main document | | | |
| 6.4 dry run | | | |
| 7 prune list | | | |
| 8 archive or delete | | | |

## 5. Freeze

- Freeze message sent by the author on: 
- Overleaf HEAD at freeze: 
- Overleaf HEAD before first sync (must match): 
- Unfrozen on: 

## 6. PDF differences

| Run | Section | Difference | Cause | Decision |
|---|---|---|---|---|

## 7. Push / pull lists

```yaml
overleaf:
  id:
  gh_actions_sync: true
  push:
  pull:
```

`check_lists.py` result:

## 8. Prune list

Approved deletions from Overleaf (class 4):
