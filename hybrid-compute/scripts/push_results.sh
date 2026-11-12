#!/bin/bash
# Run on the cluster login node after jobs finish: commit small result files and push.
#   slurm/push_results.sh "seeds 0-4 of the frame test (jobs 123-127)"
# Adds figures / small arrays / result tables under the numbered experiment folders only.
# Logs and caches stay git-ignored; big things move by rsync, never through git.
# Every .json in an experiment folder gets committed: keep credentials out of those folders.
set -euo pipefail
cd /path/to/cluster/clone/PROJECT      # <-- your cluster clone
msg=${1:?commit message required}
git pull --rebase --autostash -q
# one pattern at a time: git add aborts the whole call if any single pattern matches nothing
for g in '[0-9][0-9]_*/*.png' '[0-9][0-9]_*/*.npz' '[0-9][0-9]_*/*.json' '[0-9][0-9]_*/*results*.txt'; do
  git add -- "$g" 2>/dev/null || true
done
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git diff --cached --stat
git commit -q -m "results: $msg" -m "Committed on the cluster from Slurm outputs."
git push -q
git log --oneline -1
