---
name: engaging-hybrid-compute
description: Split a research project between a local machine and MIT's Engaging (ORCD) cluster, with code and results kept in sync through a private git repo. Light work (editing, plotting, quick checks) stays local; heavy compute runs as Slurm jobs. Use when the user mentions Engaging, ORCD, orcd-login, sbatch/squeue on the MIT cluster, moving runs to the cluster, syncing results back, or a project that already has this setup (a cluster clone, a deploy key, slurm/ scripts).
---

# Local ↔ Engaging hybrid compute, synced through a private git repo

One repo, two working copies:

```
local machine                          GitHub (private repo)                 Engaging (cluster clone)
edit, commit, push   ───────────────▶  origin  ◀───── pull --rebase (deploy key) ─────  login node: git pull, uv sync, sbatch
pull --rebase, plot  ◀───────────────          ◀──── push_results.sh (figures, small arrays) ── after jobs finish
```

- **Code** is written locally, committed and pushed. The cluster only pulls.
- **Results** that are cheap to regenerate and small (figures, small `.npz`/`.json`, result tables) are committed *on the cluster* by `push_results.sh` and pulled locally.
- **Big things** (raw simulation snapshots, caches, `.venv`, Slurm logs) never go in git. Move them with `rsync` only when needed.
- **Heavy compute only on the cluster.** Locally: editing, plotting, reading results, checks that take seconds.

**Assumes 1Password** on the local machine: its SSH agent holds the cluster key and signs commits, so a locked 1Password shows up as SSH or commit failures. Other agents work, but `setup.md` is written for 1Password.

Read `setup.md` (next to this file) for the one-time setup. The rest of this file is the daily workflow and the rules.

## Connecting (SSH key + Duo + ControlMaster)

An SSH key replaces the password but **does not skip Duo**. The way around it is a ControlMaster socket: the user opens one connection (one Duo push), and every later `ssh`, `scp` or `rsync` reuses it for the `ControlPersist` window (e.g. 8 h).

1. Check: `ssh -O check <alias>`, where `<alias>` is the `~/.ssh/config` host, e.g. `orcd-login`.
2. If "Master running": run everything as `ssh -o BatchMode=yes <alias> '<cmd>'`. `BatchMode` makes it fail fast instead of hanging on a Duo prompt.
3. If not, the user has to reconnect. Either they run `ssh <alias>` in their own terminal and approve Duo, or they have the gated helper from `setup.md`. Call it only as `engaging-connect`, never by path or through a wrapper, so its permission rule fires.
   - **At most one reconnect attempt per need. Never loop.** Repeated failed attempts can trigger a Duo lockout.
   - If key auth is refused instantly with a message about logging in to the web portal, the user must first log in to OnDemand (https://orcd-ood.mit.edu) in a browser. Key auth appears to need a recent OnDemand login (about a day). Ask them; don't retry.

The open socket is a full shell on the user's account. Treat every command as if the user typed it, and keep to the rules below even when nothing prompts.

Never:
- run `ssh -O exit <alias>`, which kills the user's shared socket;
- run plain `ssh <alias>` without `BatchMode=yes`, which hangs on the Duo menu;
- touch `~/.ssh/authorized_keys` on the cluster.

## Rules

- **No compute on the login node.** Allowed there: `git`, `uv sync` (installs), `rsync`, `sbatch`/`squeue`/`sacct`/`scancel`, reading logs, tiny file inspection. Everything else goes in a Slurm job (`mit_quicktest` for anything short).
- **Free tier only** unless the user explicitly asks otherwise: partitions `mit_quicktest`, `mit_normal`, `mit_normal_gpu`, `mit_preemptable`; no paid QOS, reservations or rentals. If a job only fits a paid tier, say so instead of submitting.
- **Ask the user before:**
  - jobs beyond the project's agreed size, for example > 12 h, more than ~20 array tasks or > 32 CPUs per task (agree the thresholds per project);
  - GPU jobs, unless agreed;
  - deleting anything on the cluster;
  - changing pinned dependencies.
- **Keep the repo private.** Never commit secrets, keys or tokens. `push_results.sh` commits every `.json` in an experiment folder, so no credentials go in those folders, and job logs print only named switches, never the whole environment.
- **Commit signing:** if a commit fails because the signing agent is locked (1Password's SSH agent), ask the user to unlock 1Password. Never bypass signing (`--no-gpg-sign`, changing config).
- **If something breaks, stop and report.** Don't quietly fall back to running locally or to a different dependency source.

## The daily loop

1. **Local:** edit → commit → push.
2. **Cluster:** update the clone, then **verify the code arrived** before submitting:
   ```bash
   ssh -o BatchMode=yes <alias> 'cd <cluster-repo> && git pull -q --rebase --autostash && git log --oneline -1 && grep -c "<a symbol you just added>" <file>'
   ```
   Run `uv sync --frozen` only if the lockfile changed (it's an install, so fine on the login node).
   *Why verify:* if the local commit silently failed (e.g. signing), the cluster runs the old code and you only find out hours later.
3. **Submit** with `sbatch`, usually the generic array script `scripts/run_modes.sh` (one mode per task). Give jobs **descriptive names**: they're how you watch them.
4. **Watch** by job name, not by a list of IDs (see Monitoring).
5. **Collect:** on the login node, `scripts/push_results.sh "<what these results are>"` commits figures and small arrays from the experiment folders and pushes.
6. **Local:** check what the cluster pushed, then pull:
   ```bash
   git fetch -q && git log --stat HEAD..@{u}
   ```
   Cluster commits should touch only result files in experiment folders. If one changes code, scripts or config, stop and tell the user before pulling: the deploy key may be misused. Then `git pull --rebase`, plot, analyse and write notes.

## Submitting jobs well

- **Settings via environment, passed with `--export=ALL,KEY=val,...`.** `--export` **splits on commas**, so never put a comma inside a value: `KAPPAS=8,4,2,1` arrives as `KAPPAS=8`. Use another separator (`8:4:2:1`).
- **Every switch that changes results must appear in the output filename.** Two jobs that differ only in an env var otherwise overwrite each other's output. Add the tag to the code that writes outputs *before* submitting.
- **Print the full configuration on the first lines of each job log.** Then a typo in a mode string shows up when you first look at the log. Check the first log lines of one task before trusting a whole batch.
- **Smoke test on `mit_quicktest`** (15 min) after any environment change: imports, one small run, compare with a local result.
- **Size memory from history:** `sacct -j <id> -o JobID,Elapsed,MaxRSS,ReqMem`. Per-user caps (e.g. 96 CPUs and 386 GB on `mit_normal`) mean big-memory jobs run a few at a time; request what you need, not the maximum.
- **Chain dependent steps:** `sbatch --dependency=afterok:<jobid> ...`. Check that the upstream result is actually usable before relying on the chain; e.g. a fit that converged to the wrong solution still exits 0.
- **Jobs read the code when they *start*, not when you submit.** Pulling new code on the cluster changes what *queued* jobs will run. Pull only when the change is backward compatible for queued jobs (new option with an unchanged default), or wait until they've started.
- **Logs:** `#SBATCH -o slurm/logs/%x-%j.out` (arrays: `%x-%A_%a.out`). The directory must exist before `sbatch`.
- **Thread counts:** inside a job, `os.cpu_count()` reports the whole node, not your allocation. Pin threads (`OMP_NUM_THREADS`, `XLA_FLAGS`, etc.) to `$SLURM_CPUS_PER_TASK` if oversubscription shows up.
- **Tools installed in `~/.local/bin` (e.g. `uv`) aren't on the non-interactive `PATH`.** Call them by full path in job scripts.

## Monitoring

Use `scripts/watch_jobs.sh <name-regex>` (or the same loop inline) as a background task:
- **Match jobs by name with `squeue --me -h -o %j | grep -cE '<regex>'`.** Don't use `squeue -j id1,id2,...`: one invalid or finished ID makes `squeue` print nothing, which looks like "all done".
- **Treat an ssh failure as a failure, not as "0 jobs left".** A dropped socket otherwise ends the watch early.
- Sleep 5–20 minutes between checks. When the jobs disappear, print the result lines from the logs.

Useful checks:
```bash
squeue --me -o "%i %j %T %M %l %r"      # state, elapsed, limit, pending reason
sacct -X -n -S <date> -o JobID%14,JobName%22,State%12,Elapsed
scontrol show res | grep -E "ReservationName|StartTime"   # maintenance windows
```

## Maintenance windows and pending reasons

- `ReqNodeNotAvail, Reserved for maintenance`: a reservation (e.g. monthly maintenance) is coming and your job's time limit would overlap it. If the job really needs less time, lower its limit so it fits before the window:
  `scontrol update JobId=<id>_0 TimeLimit=03:00:00` (users can lower, not raise, limits).
- `QOSMaxCpuPerUserLimit`: you're at your per-user cap; jobs start in waves. To free slots, cancel your own jobs that have become uninformative. Ask before cancelling anything the user started.
- `Priority`: normal queueing.
- `Dependency`: waiting on an upstream job.

## Bookkeeping

- Keep a running notes file in the repo (decisions, findings, job IDs, what each result means) and commit it often in small logical commits.
- Keep a cluster notes file for setup facts and gotchas, and append new ones.
- Each experiment gets its own folder (`NN_short_name/`) with a runnable script, so `push_results.sh` can glob results by folder.
- At the end of the project phase, revoke the deploy key in the repo settings.
