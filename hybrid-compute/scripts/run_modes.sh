#!/bin/bash
# Generic array runner: one mode per array task.
#   sbatch --array=0-2 -J fit_seeds --export=ALL,SEED=0 slurm/run_modes.sh path/to/script.py modeA modeB modeC
# Settings go in env vars via --export (it splits on commas: never put a comma inside a value).
# Edit the #SBATCH values, REPO_DIR and the env exports for your project and cluster.
# Your cluster profile (clusters/<name>.md) names the partition, the caps and where the clone lives.
#SBATCH -J run_modes
#SBATCH -p PARTITION                    # <-- from your cluster profile
#SBATCH -c 4                            # <-- from a pilot, not from the partition maximum
#SBATCH --mem=8G                        # <-- from MaxRSS history plus a cushion
#SBATCH -t 04:00:00                     # <-- always set one; short accurate limits backfill
#SBATCH -o slurm/logs/%x-%A_%a.out
REPO_DIR=/path/to/cluster/clone/PROJECT  # <-- your cluster clone
export PYTHONUNBUFFERED=1
# export UV_CACHE_DIR=... UV_PYTHON_INSTALL_DIR=...   # <-- if your profile says home is too small
# export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK         # if threads oversubscribe the allocation
cd "$REPO_DIR" || exit 1
SCRIPT=$1; shift; MODES=("$@"); MODE=${MODES[$SLURM_ARRAY_TASK_ID]}
echo "task $SLURM_ARRAY_TASK_ID: $SCRIPT $MODE on $(hostname) at $(git rev-parse --short HEAD), $SLURM_CPUS_PER_TASK CPUs"
for v in SEED MOCK MODE CONFIG; do echo "$v=${!v-}"; done   # <-- list exactly the switches your code reads (never secrets)
~/.local/bin/uv run --frozen python "$SCRIPT" "$MODE"
