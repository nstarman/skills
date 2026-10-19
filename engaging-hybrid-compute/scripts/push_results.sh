#!/bin/bash
# Run on the cluster LOGIN node after jobs finish: commit small result files and push.
#   slurm/push_results.sh "results: seeds 0-4 of the frame test (jobs 123-127)"
# Adds figures / small arrays / result tables under the numbered experiment folders only.
# Logs and caches stay git-ignored. Rebases onto local pushes first.
# Every .json in an experiment folder gets committed: keep credentials out of those folders.
set -euo pipefail
cd ~/orcd/pool/PROJECT                   # <-- your cluster clone
msg=${1:?commit message required}
git pull --rebase --autostash -q
git add -- '[0-9][0-9]_*/*.png' '[0-9][0-9]_*/*.npz' '[0-9][0-9]_*/*.json' '[0-9][0-9]_*/*results*.txt' 2>/dev/null || true
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git diff --cached --stat
git commit -q -m "results: $msg" -m "Committed on Engaging from Slurm outputs."
git push -q
git log --oneline -1
