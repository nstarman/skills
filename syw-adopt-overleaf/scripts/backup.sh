#!/usr/bin/env bash
# Phase 1 of a migration: back up everything before anything changes, and verify it.
#
# Usage:
#     backup.sh --repo <old repo clone> --mirror <Dropbox mirror folder> --overleaf-id <id>
#               --op-ref <op://... Overleaf token> --baseline <baseline.pdf>
#               [--github <owner/name>] [--dest <backups root>]
#
# --github defaults to the repository's `origin`; give it when the old repository has no remote
# (e.g. it lives inside the Dropbox mirror) or when GitHub holds a different history.
#
# Writes <dest>/<name>-<YYYY-MM-DD>/ (must not exist; never under Dropbox or iCloud):
#   repo.bundle  github.bundle (only if it is not the same history)  mirror.tar.gz  overleaf/
#   baseline.pdf  secrets.txt  MIGRATION.md (template)
# Reads the repository, the mirror and Overleaf only. The Overleaf token is read by a one-shot
# git credential helper (`op read`), so it is never in argv, a remote URL, a file or the output.
# Prints "ok <part>" per verified part; on the first failure "FAILED <part>: <reason>", exit 1.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
DEST="$HOME/Documents Local/backups"
REPO="" MIRROR="" OVERLEAF_ID="" OP_REF="" BASELINE="" GH=""
while [ $# -gt 0 ]; do
    case "$1" in
        --repo) REPO="$2" ;;
        --mirror) MIRROR="$2" ;;
        --overleaf-id) OVERLEAF_ID="$2" ;;
        --op-ref) OP_REF="$2" ;;
        --baseline) BASELINE="$2" ;;
        --dest) DEST="$2" ;;
        --github) GH="$2" ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift 2 || { echo "missing value for $1" >&2; exit 2; }
done
for v in REPO MIRROR OVERLEAF_ID OP_REF BASELINE; do
    [ -n "${!v}" ] || { sed -n '4,7p' "$0" >&2; exit 2; }
done
[ -n "$GH" ] || GH=$(git -C "$REPO" remote get-url origin 2>/dev/null | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')
[ -n "$GH" ] || { echo "no origin in $REPO: pass --github <owner/name>" >&2; exit 2; }

fail() { echo "FAILED $1: $2"; exit 1; }

# Destination: outside Dropbox and iCloud (checked before and after resolving links), and new.
synced() {
    case "$1" in
        "$HOME/Library/CloudStorage"* | "$HOME/Library/Mobile Documents"* | *Dropbox*) return 0 ;;
    esac
    return 1
}
synced "$DEST" && fail destination "$DEST is synced (Dropbox/iCloud); choose a local folder"
mkdir -p "$DEST" || fail destination "cannot create $DEST"
dest_real=$(cd "$DEST" && pwd -P)
synced "$dest_real" && fail destination "$dest_real is synced (Dropbox/iCloud); choose a local folder"
name=$(basename "$GH")
OUT="$dest_real/$name-$(date +%F)"
[ -e "$OUT" ] && fail destination "$OUT already exists; not overwriting a backup"
mkdir "$OUT"
echo "backup folder: $OUT"

# 1. The old repository: all branches and tags.
git -C "$REPO" bundle create "$OUT/repo.bundle" --all 2>/dev/null || fail repo.bundle "git bundle create failed"
git -C "$REPO" bundle verify "$OUT/repo.bundle" >/dev/null 2>&1 || fail repo.bundle "git bundle verify failed"
echo "ok repo.bundle ($(git bundle list-heads "$OUT/repo.bundle" | wc -l | tr -d ' ') refs)"

# 1b. GitHub's copy, when it is a different history (no commit of it in the local repository).
gh repo clone "$GH" "$OUT/.github.git" -- --mirror -q >/dev/null 2>&1 || fail github.bundle "cannot clone $GH"
unknown=$(git -C "$OUT/.github.git" rev-list --all | git -C "$REPO" cat-file --batch-check | grep -c missing)
if [ "$unknown" -gt 0 ]; then  # not `| grep -q`: with pipefail its early exit reads as "none"
    git -C "$OUT/.github.git" bundle create "$OUT/github.bundle" --all 2>/dev/null &&
        git -C "$OUT/.github.git" bundle verify "$OUT/github.bundle" >/dev/null 2>&1 ||
        fail github.bundle "bundle of $GH failed"
    echo "ok github.bundle ($(git bundle list-heads "$OUT/github.bundle" | wc -l | tr -d ' ') refs; a separate history)"
else
    echo "ok github.bundle not needed (every GitHub commit is in repo.bundle)"
fi
rm -rf "$OUT/.github.git"

# 2. The Dropbox mirror (reading online-only files makes Dropbox download them first).
[ -d "$MIRROR" ] || fail mirror.tar.gz "no folder $MIRROR"
tar -czf "$OUT/mirror.tar.gz" -C "$(dirname "$MIRROR")" "$(basename "$MIRROR")" 2>/dev/null ||
    fail mirror.tar.gz "tar failed (unreadable or online-only files?)"
n_src=$(find "$MIRROR" ! -type d | wc -l | tr -d ' ')  # files and symlinks, as tar lists them
n_tar=$(tar -tzf "$OUT/mirror.tar.gz" | grep -vc '/$')
[ "$n_src" = "$n_tar" ] || fail mirror.tar.gz "$n_tar files in archive, $n_src in the mirror"
echo "ok mirror.tar.gz ($n_tar files)"

# 3. The Overleaf project with its own history. `credential.helper=` first clears other helpers,
#    so the macOS keychain never stores the token.
export OP_REF
git -c credential.helper= \
    -c 'credential.helper=!f() { test "$1" = get || return 0; echo username=git; printf "password=%s\n" "$(op read "$OP_REF")"; }; f' \
    clone -q "https://git@git.overleaf.com/$OVERLEAF_ID" "$OUT/overleaf" 2>/dev/null ||
    fail overleaf "clone failed (1Password locked, wrong --op-ref, or wrong --overleaf-id?)"
git -C "$OUT/overleaf" fsck --no-progress >/dev/null 2>&1 || fail overleaf "git fsck failed"
grep -Eq 'olp_|://[^@/]*:[^@/]*@' "$OUT/overleaf/.git/config" && fail overleaf "a secret is in overleaf/.git/config"
echo "ok overleaf ($(git -C "$OUT/overleaf" rev-list --count HEAD) commits, HEAD $(git -C "$OUT/overleaf" rev-parse --short HEAD))"

# 4. The paper as compiled before the migration.
cp "$BASELINE" "$OUT/baseline.pdf" 2>/dev/null || fail baseline.pdf "cannot copy $BASELINE"
pages=$(pdfinfo "$OUT/baseline.pdf" 2>/dev/null | awk '/^Pages:/ {print $2}')
[ -n "$pages" ] || fail baseline.pdf "pdfinfo cannot read it"
echo "ok baseline.pdf ($pages pages)"

# 5. The old repository's secret names (gh never prints values).
gh secret list -R "$GH" >"$OUT/secrets.txt" 2>/dev/null || fail secrets.txt "gh secret list -R $GH failed"
echo "ok secrets.txt ($(wc -l <"$OUT/secrets.txt" | tr -d ' ') names)"

[ -f "$here/../references/migration-template.md" ] && cp "$here/../references/migration-template.md" "$OUT/MIGRATION.md"
echo "done: $OUT"
