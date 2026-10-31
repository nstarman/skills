#!/bin/bash
# Generic array runner: one mode per array task.
#   sbatch --array=0-2 -J fit_seeds --export=ALL,SEED=0 slurm/run_modes.sh path/to/script.py modeA modeB modeC
# Settings go in env vars via --export (it splits on commas: never put a comma inside a value).
# Edit REPO_DIR, the resources (from a pilot) and the env exports for your project.
#SBATCH -J run_modes
#SBATCH -p submit
#SBATCH -c 4
#SBATCH --mem=8G
#SBATCH -t 04:00:00
#SBATCH -o slurm/logs/%x-%A_%a.out
REPO_DIR=/work/submit/$USER/PROJECT      # <-- your cluster clone
export PYTHONUNBUFFERED=1
export UV_CACHE_DIR=/work/submit/$USER/.cache/uv UV_PYTHON_INSTALL_DIR=/work/submit/$USER/.local/share/uv/python
# export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK   # if threads oversubscribe the allocation
cd "$REPO_DIR" || exit 1
SCRIPT=$1; shift; MODES=("$@"); MODE=${MODES[$SLURM_ARRAY_TASK_ID]}
echo "task $SLURM_ARRAY_TASK_ID: $SCRIPT $MODE on $(hostname) at $(git rev-parse --short HEAD), $SLURM_CPUS_PER_TASK CPUs"
for v in SEED MOCK MODE CONFIG; do echo "$v=${!v-}"; done   # <-- list exactly the switches your code reads (never secrets)
~/.local/bin/uv run --frozen python "$SCRIPT" "$MODE"
