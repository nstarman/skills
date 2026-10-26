# Rollback, per phase

`$B` is the backup folder, `$ID` the Overleaf project id, `$REF` the 1Password reference of the
Overleaf token. Every command that talks to Overleaf uses the credential helper, never a token
in a URL:

```sh
export OP_REF="$REF"
ol() { git -c credential.helper= \
    -c 'credential.helper=!f() { test "$1" = get || return 0; echo username=git; printf "password=%s\n" "$(op read "$OP_REF")"; }; f' "$@"; }
```

Restoring Overleaf is itself an outward-facing step: ⛔ ask the author first.

| Phase | What changed | Undo |
|---|---|---|
| 0–1 | nothing outside the backup folder | delete `$B` if unwanted |
| 2 | co-authors asked to pause | the author tells them to continue |
| 3–4 | new local folder `paper-<slug>/` | delete the folder |
| 5 | new private GitHub repository | `gh repo delete <owner>/paper-<slug> --yes` (needs the `delete_repo` scope; the author's call) |
| 6.1 | mirror renamed | rename back in the mirror (`ms.tex`→`main.tex`, `bib.bib`→`main.bib`, `\bibliography{main}`); the author resets the main document |
| 6.5 | Overleaf received SYW's push | restore Overleaf to the frozen state (below) |
| 7 | class-4 files deleted in Overleaf | restore them from Overleaf's history (Menu → History) or from `$B/mirror.tar.gz` into the mirror |
| 8 | old repository archived | `gh repo unarchive <owner>/<old> --yes` |

## Restore Overleaf to the frozen state

Overleaf's history keeps everything, so first try Overleaf → History → restore a version (the
author, in the UI). From the backup instead — a new commit that makes the project equal to the
frozen one, keeping later history:

```sh
tmp=$(mktemp -d)
ol clone -q "https://git@git.overleaf.com/$ID" "$tmp/now"
cd "$tmp/now"
git rm -rq . && git clean -fdq
git -C "$B/overleaf" archive HEAD | tar -x -C .   # read-only on the backup
git add -A && git commit -qm "restore pre-migration state"
ol push origin HEAD
```

## Restore the old repository

It is not modified before phase 8. If a local clone was lost: `git clone $B/repo.bundle <dir>`
(all branches and tags). The secrets' names are in `$B/secrets.txt`; their values are in
1Password.
