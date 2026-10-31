---
name: submit-hybrid-compute
description: Split a research project between a local machine and MIT's subMIT cluster (submit.mit.edu, the physics department's login pool and Slurm cluster), with code and results kept in sync through a private git repo. Light work (editing, plotting, quick checks) stays local; heavy compute runs as Slurm jobs on the submit partition. Use when the user mentions subMIT, submit.mit.edu, the submit or tier3 partitions, /work/submit or /ceph/submit, sbatch/squeue on subMIT, moving runs there from a laptop or from Engaging, syncing results back, or a project that already has this setup (a clone under /work/submit, a deploy key, slurm/ scripts).
---

# Local ↔ subMIT hybrid compute, synced through a private git repo

One repo, two working copies:

```
local machine                          GitHub (private repo)                 subMIT (clone in /work/submit/<kerb>)
edit, commit, push   ───────────────▶  origin  ◀───── pull --rebase (deploy key) ─────  login node: git pull, uv sync, sbatch
pull --rebase, plot  ◀───────────────          ◀──── push_results.sh (figures, small arrays) ── after jobs finish
```

- **Code** is written locally, committed and pushed. The cluster only pulls.
- **Results** that are small and cheap to regenerate (figures, small `.npz`/`.json`, result tables) are committed *on the cluster* by `push_results.sh` and pulled locally.
- **Big things** (raw outputs, caches, `.venv`, Slurm logs) never go in git. Move them with `rsync` only when needed.
- **Heavy compute only in Slurm jobs.** Locally: editing, plotting, reading results, checks that take seconds.

For a one-off run of an existing project (no deploy key yet), `rsync` the working tree to `/work/submit/<kerb>/<project>` instead of cloning; the rest of this file still applies.

Read `setup.md` (next to this file) for the one-time setup. The rest of this file is the daily workflow and the rules.

## Connecting (SSH key only, no Duo)

subMIT logs in with an SSH key that the user uploaded to the submit portal (https://submit-portal.mit.edu, behind Touchstone). There is no Duo prompt, so no ControlMaster or reconnect helper is needed: every call is a fresh connection.

- Run everything as `ssh -o BatchMode=yes <alias> '<cmd>'` (`<alias>` is the `~/.ssh/config` host, e.g. `submit`). `BatchMode` makes a refused key fail fast instead of prompting.
- `submit.mit.edu` is a **round-robin of login nodes** (submit01…submit08 and so on). Two calls can land on different machines. `/home`, `/work` and `/ceph` are shared, so files are the same everywhere, but processes are not: a `nohup` or `screen` you started on one call may not be on the next login node. Use Slurm for anything long-running, never a background process on a login node.
- If the key is refused, stop and ask the user. Don't retry in a loop. Read the error first:
  - `sign_and_send_pubkey: signing failed ... communication with agent failed` then `Permission denied (publickey)`: the local SSH agent (1Password) is locked or asleep. Ask the user to unlock it.
  - A plain `Permission denied (publickey)` with no agent error: the key isn't on the portal (anymore). The user re-uploads it.

The key opens a full shell on the user's account. Treat every command as if the user typed it, and keep to the rules below even when nothing prompts.

Never touch `~/.ssh/authorized_keys` on the cluster: the portal manages keys.

## Rules

- **Login nodes are shared and busy** (load ~50 is normal). Allowed there: `git`, `uv sync` (installs), `rsync`, `sbatch`/`squeue`/`sacct`/`scancel`, reading logs, short tests (seconds to a couple of minutes). Anything longer goes in a Slurm job. subMIT's guide sets ~15 minutes as the line; stay well under it.
- **Storage:** home is only **10 GB**. Put the clone, `.venv` and the uv cache in `/work/submit/<kerb>` (100 GB). Large data goes in `/ceph/submit/data/user/<k>/<kerb>` (1 TB, large files only: no 100k+ small files). See `setup.md`.
- **Partitions:** `submit` for CPU work (6 days max). `tier3` has old CPUs **without AVX2** (mostly without AVX): JAX, standard TensorFlow and many optimized wheels die there with `Illegal instruction`. Never send such jobs to `tier3` or to `--partition=submit,tier3`. GPUs: `submit-gpu` (2 days), `submit-gpu-express` (1 h).
- **Always pass `--time`.** Without it a job gets the 12 h default, which both kills long runs and hides short ones from backfill.
- **Ask the user before:**
  - jobs beyond the project's agreed size, for example > 1 day, more than ~20 array tasks or > 32 CPUs per task (agree the thresholds per project);
  - GPU jobs, unless agreed;
  - deleting anything on the cluster;
  - emailing submit-help@mit.edu or asking for more quota (the user does that);
  - changing pinned dependencies.
- **Keep the repo private.** Never commit secrets, keys or tokens. `push_results.sh` commits every `.json` in an experiment folder, so no credentials go in those folders, and job logs print only named switches, never the whole environment.
- **Commit signing:** if a commit fails because the signing agent is locked (1Password's SSH agent), ask the user to unlock 1Password. Never bypass signing.
- **If something breaks, stop and report.** Don't quietly fall back to running locally or to a different dependency source.

## The daily loop

1. **Local:** edit → commit → push.
2. **Cluster:** update the clone, then **verify the code arrived** before submitting:
   ```bash
   ssh -o BatchMode=yes <alias> 'cd <cluster-repo> && git pull -q --rebase --autostash && git log --oneline -1 && grep -c "<a symbol you just added>" <file>'
   ```
   Run `uv sync --frozen` only if the lockfile changed.
   *Why verify:* if the local commit silently failed (e.g. signing), the cluster runs the old code and you only find out hours later.
3. **Submit** with `sbatch`, usually the generic array script `scripts/run_modes.sh` (one mode per task). Give jobs **descriptive names**: they're how you watch them.
4. **Watch** by job name, not by a list of IDs (see Monitoring).
5. **Collect:** on the login node, `scripts/push_results.sh "<what these results are>"` commits figures and small arrays and pushes.
6. **Local:** check what the cluster pushed, then pull:
   ```bash
   git fetch -q && git log --stat HEAD..@{u}
   ```
   Cluster commits should touch only result files in experiment folders. If one changes code, scripts or config, stop and tell the user before pulling: the deploy key may be misused. Then `git pull --rebase`, plot, analyse and write notes.

## Submitting jobs well

- **Pilot first, with a short limit.** A few-minute job on the real code (`-t 00:08:00`) gives the per-step time and memory; size the real jobs from it. Run it at two CPU counts in parallel and compare the step times: they often land on the same node, which makes the comparison clean. `seff <jobid>` gives CPU efficiency and peak memory even for a pilot killed at its time limit.
  - Example (a JAX orbit integration): 4 CPUs → 10.4 s/step at 57% CPU efficiency; 8 CPUs → 9.4 s/step at 40%. Doubling the CPUs bought 10% for twice the billing, so 4 it is. JAX's CPU backend often uses only 2–3 cores.
  - Node speed varies between nodes (and between clusters: the same step took 5.8 s on an Engaging node). Set `--time` from the slowest pilot plus a wide margin; the 6-day partition limit leaves room.
- **Split long checkpointed runs into an array.** If a script already loops over independent chunks and checkpoints each one, run one chunk per array task through a small runner that narrows the loop (and skips the final assembly), then one dependent job that runs the unmodified script and reuses every checkpoint. The pipeline's own script stays untouched.
- **Settings via environment, passed with `--export=ALL,KEY=val,...`.** `--export` **splits on commas**, so never put a comma inside a value: `KAPPAS=8,4,2,1` arrives as `KAPPAS=8`. Use another separator (`8:4:2:1`).
- **Every switch that changes results must appear in the output filename.** Two jobs that differ only in an env var otherwise overwrite each other's output.
- **Print the full configuration on the first lines of each job log**, and check the first lines of one task before trusting a whole batch.
- **Memory is a consumable resource on subMIT**, like CPUs: a job holding a node's memory blocks that node even if its CPUs sit idle. Request from history (`seff <jobid>` or `sacct -o MaxRSS`) plus a cushion. Most nodes have 64–128 GB.
- **Before comparing a rerun with a cached result, check that the cache came from the same code and inputs** (grid sizes, shapes, file dates against the git log). A cache that build tools copy without hashing inputs can outlive the code that made it. Compare on matching keys (e.g. parameter pairs), not on array positions.
- **Chain dependent steps:** `sbatch --dependency=afterok:<jobid> ...`. Have the upstream step exit non-zero if its result is unusable; `afterok` only sees the exit code.
- **Jobs read the code when they *start*, not when you submit.** Pulling new code on the cluster changes what *queued* jobs will run. Pull only when the change is backward compatible for queued jobs, or wait until they've started.
- **Logs:** `#SBATCH -o slurm/logs/%x-%j.out` (arrays: `%x-%A_%a.out`). The directory must exist before `sbatch`.
- **Thread counts:** inside a job, `os.cpu_count()` reports the whole node. Pin threads (`OMP_NUM_THREADS`, `XLA_FLAGS`, etc.) to `$SLURM_CPUS_PER_TASK` if oversubscription shows up.
- **Tools in `~/.local/bin` (e.g. `uv`) aren't on the batch `PATH`.** Call them by full path in job scripts, and export `UV_CACHE_DIR` to `/work` (see `setup.md`).

## Fair share

subMIT uses multifactor priority with fair share as the largest weight (check `scontrol show config | grep ^Priority`; at the time of writing FairShare 10000, JobSize 2000, Partition 1000, Age 500, with a 7-day decay half-life). Billing is CPUs × elapsed time. The cluster is shared by the whole department, so the same discipline as on any fair-share cluster applies:

- **Ask what question the batch answers**, and run the smallest set of jobs that answers it. Screen with one seed or a pilot, then expand only the informative variants. Skip outputs that already exist.
- **Right-size:** `-c` only what the code uses (compare `sacct -o Elapsed,TotalCPU,AllocCPUS` or `seff`), `-t` from past runs plus a margin, `--mem` from MaxRSS plus a cushion. Short accurate limits backfill into idle gaps.
- **The partition is often full.** Even with top fair share, array tasks can wait as `(Resources)`: one evening, 28 of 29 `submit` nodes were allocated and over 1000 jobs were pending, so 2 of 8 tasks started at once and the rest queued. Plan for wall time beyond the run time, and check with `sinfo -p submit -o "%D %T"` and `squeue --me --start`.
- `sshare -l -u $USER` shows `LevelFS = share / usage` (below 1: over your share); `sprio -j <id>` breaks down one pending job.
- **Cancel jobs as soon as they stop being informative.** Ask first if the user started them.
- **Pack small runs that share setup into one job**, so imports and JIT compilation are paid once.

## Monitoring

Use `scripts/watch_jobs.sh <name-regex>` (or the same loop inline) as a background task:
- **Match jobs by name with `squeue --me -h -o %j | grep -cE '<regex>'`.** `squeue -j id1,id2,...` prints nothing when one ID is invalid or finished, which looks like "all done".
- **Treat an ssh failure as a failure, not as "0 jobs left".**
- **An overnight watcher dies when 1Password auto-locks** (each check is a fresh connection, and a locked agent refuses to sign). The jobs keep running; only the watcher stops. Tell the user before a long watch, so they can lengthen 1Password's auto-lock or accept checking in by hand after unlocking.
- Sleep 5–20 minutes between checks. When the jobs disappear, print the result lines from the logs.

Useful checks:
```bash
squeue --me -o "%i %j %T %M %l %R"      # state, elapsed, limit, reason or node
sacct -X -n -S <date> -o JobID%14,JobName%22,State%12,Elapsed
seff <jobid>                            # CPU and memory efficiency of a finished job
srun --jobid=<jobid> --overlap --pty bash   # a shell on a running job's node (user only; interactive)
```

## Bookkeeping

- Keep a running notes file in the repo (decisions, findings, job IDs, what each result means) and commit it often in small logical commits.
- Keep a cluster notes file for setup facts and gotchas, and append new ones.
- Each experiment gets its own folder (`NN_short_name/`) with a runnable script, so `push_results.sh` can glob results by folder.
- At the end of the project phase, revoke the deploy key and clean up `/work` and `/ceph`: storage there is yours to keep tidy.
