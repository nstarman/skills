#!/bin/bash
# Run LOCALLY, from inside the local clone: move one big data folder between it and the cluster
# clone by rsync. For snapshots, caches, checkpoints; anything you would read a diff of goes by git.
#   scripts/sync_data.sh pull <alias> <cluster-repo> <dir>            # cluster -> here
#   scripts/sync_data.sh push <alias> <cluster-repo> <dir>            # here -> cluster
#   scripts/sync_data.sh pull <alias> <cluster-repo> <dir> --delete   # also remove what the source lacks
# <dir> is one folder inside the repo, never the root or slurm/: slurm/ exists only on the cluster
# and is git-ignored, so a deleting sync of the root would wipe the logs.
# --delete prints a dry run and stops; rerun with CONFIRM_DELETE=1 once the user has read it.
# Uses only options the macOS rsync (openrsync) also has: no --info=progress2.
set -euo pipefail
MODE=${1:?pull or push}; HOST=${2:?ssh alias for the cluster}
REPO=${3:?cluster repo path}; DIR=${4:?one folder inside the repo}; DEL=${5-}
DIR=${DIR%/}
# These values reach a shell on the cluster: refuse anything that could break out.
safe_host='^[A-Za-z0-9][A-Za-z0-9._-]*$'; safe_path='^[~A-Za-z0-9_./-]+$'
[[ $MODE == pull || $MODE == push ]] || { echo "first argument is pull or push"; exit 2; }
[[ $HOST =~ $safe_host && $REPO =~ $safe_path && $DIR =~ $safe_path ]] || { echo "bad host, repo path or folder"; exit 2; }
[[ $DEL == "" || $DEL == --delete ]] || { echo "the only option is --delete"; exit 2; }
case /$DIR/ in
  //|/./|/~*|*/../*|//*) echo "folder must be a path inside the repo, not the root: $DIR"; exit 2 ;;
  /slurm/*) echo "slurm/ stays on the cluster; read logs over ssh"; exit 2 ;;
esac
cd "$(git rev-parse --show-toplevel)"   # <dir> is relative to the repo root on both sides

args=(-azh --partial --stats -e "ssh -o BatchMode=yes"
  --exclude .git/ --exclude .venv/ --exclude __pycache__/ --exclude slurm/)
here="./$DIR/"; there="$HOST:$REPO/$DIR/"
if [ "$MODE" = pull ]; then
  mkdir -p "$here"; src=$there; dst=$here
else
  [ -d "$here" ] || { echo "no local folder $DIR"; exit 2; }
  args+=(--rsync-path "mkdir -p $REPO/$DIR && rsync"); src=$here; dst=$there
fi

if [ -n "$DEL" ]; then
  args+=(--delete)
  if [ "${CONFIRM_DELETE-}" != 1 ]; then
    echo "dry run: what --delete would change in $([ "$MODE" = pull ] && echo "local" || echo "cluster") $DIR/"
    rsync "${args[@]}" --dry-run --itemize-changes "$src" "$dst"
    echo "nothing changed; rerun with CONFIRM_DELETE=1 to apply"
    exit 3
  fi
fi
rsync "${args[@]}" "$src" "$dst"
