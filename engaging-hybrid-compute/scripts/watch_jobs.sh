#!/bin/bash
# Run LOCALLY (e.g. as a background task): wait until no job whose name matches REGEX is queued,
# then print the last lines of their logs. Matches by name, because `squeue -j a,b,c` prints
# nothing if any ID is invalid, which looks like "done". Stops loudly if ssh fails.
#   scripts/watch_jobs.sh '^(fit_|lap_)' orcd-login ~/orcd/pool/PROJECT 600
set -u
REGEX=${1:?name regex}; HOST=${2:-orcd-login}; REPO=${3:-'~/orcd/pool/PROJECT'}; EVERY=${4:-600}
while :; do
  n=$(ssh -o BatchMode=yes "$HOST" "squeue --me -h -o %j | grep -cE '$REGEX'" 2>/dev/null); rc=$?
  [ $rc -gt 1 ] && { echo "ssh failed (rc=$rc); stopping watcher"; exit 1; }   # grep -c exits 1 on 0 matches
  [ "$n" = "0" ] && break
  sleep "$EVERY"
done
ssh -o BatchMode=yes "$HOST" "cd $REPO/slurm/logs && for f in \$(ls -t | head -40); do \
  j=\${f%%-*}; echo \"\$j\" | grep -qE '$REGEX' && { echo \"== \$f\"; tail -n 3 \"\$f\"; }; done"
