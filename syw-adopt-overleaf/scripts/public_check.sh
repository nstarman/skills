#!/usr/bin/env bash
# Before a migrated paper's repository is made public: nothing from the old history, no
# token-like strings, no Overleaf-only private files (class 4 marked private), anywhere in its
# history.
#
# Usage:
#     public_check.sh <new repo> <repo.bundle (old repository)> <inventory.tsv>
#
# Read-only on the new repository: the bundle is cloned into a temporary folder, never fetched.
# Identical file contents are not checked (an unchanged .cls file is not a leak); commits are.
# A token match prints commit and path, never the match. Exit 0 = all ok, 1 = a check failed.
set -euo pipefail
NEW="${1:?usage: public_check.sh <new repo> <repo.bundle> <inventory.tsv>}"
BUNDLE="${2:?usage: public_check.sh <new repo> <repo.bundle> <inventory.tsv>}"
INVENTORY="${3:?usage: public_check.sh <new repo> <repo.bundle> <inventory.tsv>}"
TOKENS='olp_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|access_token=[^[:space:]&]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY'

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
status=0

git clone -q --bare "$BUNDLE" "$tmp/old.git"
git -C "$tmp/old.git" rev-list --all | sort >"$tmp/old"
git -C "$NEW" rev-list --all | sort >"$tmp/new"
shared=$(comm -12 "$tmp/old" "$tmp/new" | wc -l | tr -d ' ')
if [ "$shared" = 0 ]; then
    echo "ok shared commits"
else
    echo "FAIL shared commits: $shared commit(s) of the old repository are in the new one"
    status=1
fi

# File contents in every commit (no commits: nothing to grep, and a bare `git grep` would search
# only the working tree), then commit messages.
hits=""
[ -s "$tmp/new" ] && hits=$(xargs git -C "$NEW" grep -I -l -E "$TOKENS" <"$tmp/new" 2>/dev/null || true)
msgs=$(git -C "$NEW" log --all --format='%H %B' | grep -E "$TOKENS" | cut -c1-40 || true)
[ -n "$msgs" ] && hits="${hits:+$hits
}$(echo "$msgs" | sed 's/$/ (commit message)/')"
if [ -z "$hits" ]; then
    echo "ok tokens"
else
    echo "$hits" | sed 's/^/FAIL tokens: /'
    status=1
fi

git -C "$NEW" -c core.quotePath=false log --all --name-only --format= | sort -u >"$tmp/paths"
# Only class-4 rows whose note starts with "private": code, data and lockfiles are class 4 in
# Overleaf too, but legitimately move into the repository.
private=$(awk -F'\t' 'NR==FNR { if ($1 == "4" && $3 ~ /^private/) p[$2] = 1; next }
    { for (k in p) if ($0 == k || substr($0, length($0) - length(k)) == "/" k) print $0 }' \
    "$INVENTORY" "$tmp/paths")
if [ -z "$private" ]; then
    echo "ok private files"
else
    echo "$private" | sed 's/^/FAIL private files: /'
    status=1
fi
exit "$status"
