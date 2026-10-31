#!/bin/bash
# Run LOCALLY (e.g. as a background task): wait until no job whose name matches REGEX is queued,
# then print the last lines of their logs. Matches by name, because `squeue -j a,b,c` prints
# nothing if any ID is invalid, which looks like "done". Stops loudly if ssh fails.
#   scripts/watch_jobs.sh '^(fit_|lap_)' submit /work/submit/<kerb>/PROJECT 600
set -u
REGEX=${1:?name regex}; HOST=${2:-submit}; REPO=${3:?cluster repo, e.g. /work/submit/<kerb>/PROJECT}; EVERY=${4:-600}
# These values are pasted into commands run on the cluster: refuse anything that could break out.
case $REGEX in *\'*) echo "regex must not contain a single quote"; exit 2 ;; esac
safe_host='^[A-Za-z0-9][A-Za-z0-9._-]*$'; safe_path='^[~A-Za-z0-9_./-]+$'
[[ $HOST =~ $safe_host && $REPO =~ $safe_path && $EVERY =~ ^[0-9]+$ ]] || { echo "bad host, repo path or interval"; exit 2; }
while :; do
  n=$(ssh -o BatchMode=yes "$HOST" "squeue --me -h -o %j | grep -cE '$REGEX'" 2>/dev/null); rc=$?
  [ $rc -gt 1 ] && { echo "ssh failed (rc=$rc); stopping watcher"; exit 1; }   # grep -c exits 1 on 0 matches
  [ "$n" = "0" ] && break
  sleep "$EVERY"
done
ssh -o BatchMode=yes "$HOST" "cd $REPO/slurm/logs && for f in \$(ls -t | head -40); do \
  j=\${f%%-*}; echo \"\$j\" | grep -qE '$REGEX' && { echo \"== \$f\"; tail -n 3 \"\$f\"; }; done"
