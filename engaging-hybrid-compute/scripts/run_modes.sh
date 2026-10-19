#!/bin/bash
# Generic array runner: one mode per array task.
#   sbatch --array=0-2 -J fit_seeds --export=ALL,SEED=0 slurm/run_modes.sh path/to/script.py modeA modeB modeC
# Settings go in env vars via --export (it splits on commas: never put a comma inside a value).
# Edit REPO_DIR and the env exports for your project.
#SBATCH -J run_modes
#SBATCH -p mit_normal
#SBATCH -c 16
#SBATCH --mem=48G
#SBATCH -t 12:00:00
#SBATCH -o slurm/logs/%x-%A_%a.out
REPO_DIR=~/orcd/pool/PROJECT            # <-- your cluster clone
export PYTHONUNBUFFERED=1
# export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK   # if threads oversubscribe the allocation
cd "$REPO_DIR" || exit 1
SCRIPT=$1; shift; MODES=("$@"); MODE=${MODES[$SLURM_ARRAY_TASK_ID]}
echo "task $SLURM_ARRAY_TASK_ID: $SCRIPT $MODE on $(hostname) at $(git rev-parse --short HEAD)"
for v in SEED MOCK MODE CONFIG; do echo "$v=${!v-}"; done   # <-- list exactly the switches your code reads (never secrets)
~/.local/bin/uv run --frozen python "$SCRIPT" "$MODE"
