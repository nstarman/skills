---
name: hybrid-compute
description: Split a research project between a local machine and a Slurm cluster, with code and results kept in sync through a private git repo. Light work (editing, plotting, quick checks) stays local; heavy compute runs as Slurm jobs. Covers the daily loop, what goes through git versus rsync, submitting and watching jobs, fair-share priority, and squashing accumulated result commits. Per-cluster profiles in `clusters/`: MIT Engaging (ORCD, orcd-login) and MIT subMIT (submit.mit.edu, the submit and tier3 partitions, /work/submit, /ceph/submit). Use when the user mentions Engaging, ORCD, subMIT, sbatch/squeue over ssh, a cluster login node, queue priority or fair share, moving runs to a cluster, syncing results back, or a project that already has this setup (a cluster clone, a deploy key, slurm/ scripts).
---

# Local ↔ cluster hybrid compute, synced through a private git repo

**First, read the profile for the cluster you are on.** It carries everything that differs by site:
how to connect, where storage lives, which partitions exist and what breaks there.

| Cluster | Profile |
|---|---|
| MIT Engaging (ORCD) | `clusters/engaging.md` |
| MIT subMIT | `clusters/submit.md` |

No profile for the cluster yet? Work from the nearest one, and write a new profile as you go: the
four headings are Connecting, Storage, Partitions and caps, Site-specific breakage. That file is the
only thing a new cluster needs.

The rest of this file is the workflow, and it is the same everywhere.

## The shape

One repo, two working copies:

```
local machine                       GitHub (private repo)            cluster (clone)
edit, commit, push  ─────────────▶  origin  ◀──── pull (deploy key) ──── login node: git pull, sync env, sbatch
pull --rebase, plot ◀────────────          ◀──── push_results.sh ─────── after jobs finish
```

- **Code** is written locally, committed and pushed. The cluster only pulls.
- **Results** that are small and cheap to regenerate are committed *on the cluster* by
  `push_results.sh` and pulled locally.
- **Big things** move by `rsync`, never through git (see Git or rsync).
- **Heavy compute only in Slurm jobs.** Locally: editing, plotting, reading results, checks that
  take seconds.

Read `setup.md` (next to this file) for the one-time setup, and the profile for the site-specific
half of it.

**Assumes 1Password** on the local machine: its SSH agent holds the cluster key and signs commits, so
a locked 1Password shows up as SSH or commit failures. Other agents work; `setup.md` is written for
1Password.

## Connecting

The profile gives the recipe, because this is where clusters differ most — some gate every login
behind a second factor, some take a key and nothing else. Two things hold everywhere:

- **Run every command as `ssh -o BatchMode=yes <alias> '<cmd>'`.** `BatchMode` makes a refused key
  fail fast instead of hanging on a prompt.
- **The session is a full shell on the user's account.** Treat every command as if the user typed it,
  and keep to the rules below even when nothing prompts.

Never touch `~/.ssh/authorized_keys` on the cluster.

If a connection fails, read the error and stop. Don't retry in a loop: on a cluster with a
second-factor gate, repeated attempts can trigger a lockout. The profile lists that cluster's
failure messages and what each one means.

## Rules

- **No compute on the login node.** Allowed there: `git`, dependency installs, `rsync`,
  `sbatch`/`squeue`/`sacct`/`scancel`, reading logs, tiny file inspection. Everything else goes in a
  job — the profile names the short-test partition for anything brief.
- **Stay inside the allocation the profile describes** unless the user explicitly asks otherwise.
  Before every `sbatch`, check the job against that cluster's caps (wall time, CPUs, GPUs, memory per
  user). If it only fits a tier the project isn't on, don't submit: say which limit it exceeds, and
  offer the alternatives — split it, checkpoint and resubmit, a job array, or a preemptable partition
  with `--requeue`.
- **Ask the user before:**
  - jobs beyond the project's agreed size, for example > 12 h, more than ~20 array tasks or > 32 CPUs
    per task (agree the thresholds per project);
  - GPU jobs, unless agreed;
  - deleting anything on the cluster;
  - changing pinned dependencies;
  - emailing the cluster's support address or asking for more quota — the user does that.
- **Keep the repo private.** Never commit secrets, keys or tokens. `push_results.sh` commits every
  `.json` in an experiment folder, so no credentials go in those folders, and job logs print only
  named switches, never the whole environment.
- **Commit signing:** if a commit fails because the signing agent is locked, ask the user to unlock
  it. Never bypass signing (`--no-gpg-sign`, changing config).
- **If something breaks, stop and report.** Don't quietly fall back to running locally or to a
  different dependency source.

## The daily loop

1. **Local:** edit → commit → push.
2. **Cluster:** update the clone, then **verify the code arrived** before submitting:
   ```bash
   ssh -o BatchMode=yes <alias> 'cd <cluster-repo> && git pull -q --rebase --autostash && git log --oneline -1 && grep -c "<a symbol you just added>" <file>'
   ```
   Sync the environment only if the lockfile changed (it's an install, so fine on the login node).
   *Why verify:* if the local commit silently failed (e.g. signing), the cluster runs the old code
   and you only find out hours later.
3. **Submit** with `sbatch`, usually the generic array script `scripts/run_modes.sh` (one mode per
   task). Give jobs **descriptive names**: they're how you watch them.
4. **Watch** by job name, not by a list of IDs (see Monitoring).
5. **Collect:** on the login node, `scripts/push_results.sh "<what these results are>"` commits
   figures and small arrays from the experiment folders and pushes.
6. **Local:** check what the cluster pushed, then pull:
   ```bash
   git fetch -q && git log --stat HEAD..@{u}
   ```
   Cluster commits should touch only result files in experiment folders. If one changes code, scripts
   or config, stop and tell the user before pulling: the deploy key may be misused. Then
   `git pull --rebase`, plot, analyse and write notes.

## Git or rsync

The division isn't by file type. It's by whether you would ever read a diff of the thing.

**Git carries what you want to see before you trust it:** code, figures, small arrays
(`.npz`/`.json`), result tables, notes. The reason isn't convenience — it's step 6 above. The cluster
pushes with a deploy key that has no passphrase and sits on a shared machine, so every cluster commit
gets read before it's pulled, and that check only works on what a diff can show you: a file list and
sizes you can sanity-check. So keep what goes through git small enough that `git log --stat` stays
readable, and cheap enough to regenerate that losing it costs a rerun rather than a week.

**rsync carries what you'd only ever look at whole:** raw simulation snapshots, caches, checkpoints,
anything big or numerous. These never go in git. A diff tells you nothing about them, and git keeps
every version forever — which is the problem the next section exists to clean up.

Slurm logs are a third case: they stay on the cluster and you read them over ssh. They're
git-ignored, and they're not worth syncing.

Worked examples: a 40 kB figure → git. A 3 MB `.npz` of fit parameters → git. A one-page summary
table → git. A 200 MB snapshot → rsync. A checkpoint directory → rsync. Job logs → neither.

**Running the transfer.** Pull the direction you need, with the repo's own machinery excluded:

```bash
rsync -az --info=progress2 \
  --exclude '.git/' --exclude '.venv/' --exclude '__pycache__/' --exclude 'slurm/logs/' \
  <alias>:<cluster-repo>/<dir>/ ./<dir>/
```

- **Never point a `--delete` sync at the cluster repo.** `slurm/` exists only there and is
  git-ignored, so a deleting push from the local tree wipes the logs and the job scripts' output
  directory. If you need `--delete`, scope it to one data directory, never the repo root, and run
  `--dry-run` first.
- `rsync` goes over ssh, so on a cluster whose profile describes a shared connection it needs that
  connection open, same as any other command.
- Big transfers are I/O on a shared login node. Move one directory at a time rather than the whole
  tree, and prefer the cluster's fast scratch filesystem as the source if the profile names one.

## Submitting jobs well

- **Pilot first, with a short limit.** A few-minute job on the real code (`-t 00:08:00`) gives the
  per-step time and memory; size the real jobs from it. Run it at two CPU counts in parallel and
  compare the step times: they often land on the same node, which makes the comparison clean. `seff
  <jobid>` gives CPU efficiency and peak memory even for a pilot killed at its time limit. Node speed
  varies between nodes and between clusters, so set `--time` from the slowest pilot plus a wide
  margin.
- **Settings via environment, passed with `--export=ALL,KEY=val,...`.** `--export` **splits on
  commas**, so never put a comma inside a value: `KAPPAS=8,4,2,1` arrives as `KAPPAS=8`. Use another
  separator (`8:4:2:1`).
- **Every switch that changes results must appear in the output filename.** Two jobs that differ only
  in an env var otherwise overwrite each other's output. Add the tag to the code that writes outputs
  *before* submitting.
- **Print the full configuration on the first lines of each job log.** Then a typo in a mode string
  shows up when you first look at the log. Check the first log lines of one task before trusting a
  whole batch.
- **Split long checkpointed runs into an array.** If a script already loops over independent chunks
  and checkpoints each one, run one chunk per array task through a small runner that narrows the loop
  (and skips the final assembly), then one dependent job that runs the unmodified script and reuses
  every checkpoint. The runner forwards the script's arguments verbatim and takes its chunk from
  `SLURM_ARRAY_TASK_ID`, never from a rewritten `argv`: in one run, a runner that reset `sys.argv`
  silently computed the default grid instead of the requested one. Printing the configuration catches
  this on the first lines.
- **Size memory from history:** `sacct -j <id> -o JobID,Elapsed,MaxRSS,ReqMem`, or `seff <jobid>`,
  plus a cushion. On some clusters memory is a consumable like CPUs, so a job holding a node's memory
  blocks that node even with idle CPUs; on others it only limits how many of your jobs pack on at
  once. Either way, request what you need, not the maximum.
- **Before comparing a rerun with a cached result, check the cache came from the same code and
  inputs** (grid sizes, shapes, file dates against the git log). A cache that build tools copy without
  hashing inputs can outlive the code that made it. Compare on matching keys (e.g. parameter pairs),
  not on array positions.
- **Chain dependent steps:** `sbatch --dependency=afterok:<jobid> ...`. `afterok` only sees the exit
  code, and a fit that converged to the wrong solution still exits 0 — so have the upstream step exit
  non-zero when its result is unusable, and the downstream jobs never start.
- **Jobs read the code when they *start*, not when you submit.** Pulling new code on the cluster
  changes what *queued* jobs will run. Pull only when the change is backward compatible for queued
  jobs (a new option with an unchanged default), or wait until they've started.
- **Logs:** `#SBATCH -o slurm/logs/%x-%j.out` (arrays: `%x-%A_%a.out`). The directory must exist
  before `sbatch`.
- **Thread counts:** inside a job, `os.cpu_count()` reports the whole node, not your allocation. Pin
  threads (`OMP_NUM_THREADS`, `XLA_FLAGS`, etc.) to `$SLURM_CPUS_PER_TASK` if oversubscription shows
  up.
- **Tools installed in `~/.local/bin` aren't on the non-interactive `PATH`.** Call them by full path
  in job scripts.

## Fair share: fewer, more targeted jobs

Queue priority on a shared cluster is mostly **fair share**: how much of your share you have used
lately. Every CPU-hour you run lowers the priority of your next job, and usage decays over a half-life
of days, so last week's runs still count. A day of broad sweeps can leave the user near the bottom of
the queue for a week. Treat CPU-hours as a budget.

Check the live values; sites retune them and the profile records what they were:

```bash
scontrol show config | grep ^Priority        # the weights, and the decay half-life
scontrol show partition <p> | grep TRES      # what is billed (usually allocated CPUs × elapsed)
sshare -l -u $USER                           # LevelFS = share / usage; below 1 is over your share
sprio -j <jobid>                             # one pending job's priority, broken down
```

`FairShare` in `sshare` is your **rank** among all users from 0 to 1, not a ratio: 0.03 means about
the bottom 3%. Requested CPUs are billed **even when idle**.

**Before submitting, ask what question the batch answers**, and run the smallest set of jobs that
answers it:

- **Screen, then expand.** One seed and one configuration first, or a short pilot. Add seeds or arms
  only for the variants that look informative. Don't launch the full grid "to have it".
- **Don't run what's already decided.** Drop arms earlier results ruled out, and skip any job whose
  output file already exists.
- **Gate dependency chains on usefulness, not only exit code** (see above).
- **Cancel jobs as soon as they stop being informative.** Ask first if the user started them.
- **Pack small runs that share setup into one job.** Looping over modes in one process pays imports,
  environment start-up and JIT compilation once instead of per task. That saves real CPU-hours, unlike
  splitting the same work differently.

**Right-size every request:**

- `-c`: only what the code actually uses. Check `sacct -j <id> -o Elapsed,TotalCPU,AllocCPUS`: if
  TotalCPU ≪ Elapsed × AllocCPUS, most of the allocated CPUs sat idle and were still billed.
- `-t`: a realistic limit from past runs plus a margin, not the partition maximum. Charging uses
  elapsed time, so this doesn't change cost. It changes *wait*: the backfill scheduler slots jobs with
  short, accurate limits into idle gaps ahead of higher-priority jobs. That's how a low-priority job
  starts while CPUs sit idle.
- `--mem`: from `MaxRSS` history plus a cushion.

**When priority is already low:** submit the most informative job first and hold the rest
(`scontrol hold <id>` / `scontrol release <id>`) instead of queueing everything, so the job that
matters runs first. Holding doesn't restore priority; only not running does. Prefer the short-test
partition for anything that fits — tiny jobs backfill easily. LevelFS reaches 1 after usage decays by
a factor of 1/LevelFS, which takes about `half-life × log2(1/LevelFS)` with no new runs; tell the user
roughly how long that is.

## Monitoring

Use `scripts/watch_jobs.sh '<name-regex>' <alias> <cluster-repo> <seconds>` (or the same loop inline)
as a background task:

- **Match jobs by name with `squeue --me -h -o %j | grep -cE '<regex>'`.** Don't use
  `squeue -j id1,id2,...`: one invalid or finished ID makes `squeue` print nothing, which looks like
  "all done".
- **Treat an ssh failure as a failure, not as "0 jobs left".** A dropped connection otherwise ends the
  watch early.
- **A long watch can outlive the local SSH agent.** If 1Password auto-locks, each new connection is
  refused and the watcher stops, though the jobs keep running. Tell the user before an overnight
  watch, so they can lengthen the auto-lock or plan to check in by hand.
- Sleep 5–20 minutes between checks. When the jobs disappear, print the result lines from the logs.

Useful checks:

```bash
squeue --me -o "%i %j %T %M %l %R"      # state, elapsed, limit, reason or node
sacct -X -n -S <date> -o JobID%14,JobName%22,State%12,Elapsed
seff <jobid>                            # CPU and memory efficiency of a finished job
scontrol show res | grep -E "ReservationName|StartTime"   # maintenance windows
```

Common pending reasons: `Priority` is normal queueing, and a long wait under it usually means low
fair share. `Dependency` is waiting on an upstream job. `Resources` means the partition is full.
Anything about a per-user cap means your jobs start in waves — to free slots, cancel your own jobs
that have become uninformative. The profile lists that cluster's own reasons, including maintenance
reservations.

## Bookkeeping

- Keep a running notes file in the repo (decisions, findings, job IDs, what each result means) and
  commit it often in small logical commits.
- Keep a cluster notes file for setup facts and gotchas, and append new ones. When a gotcha is about
  the site rather than the project, it belongs in the cluster profile.
- Each experiment gets its own folder (`NN_short_name/`) with a runnable script, so
  `push_results.sh` can glob results by folder.

### Squashing the result commits

`push_results.sh` commits on every collection, so a long project accumulates hundreds of `results:`
commits, each carrying a fresh copy of every figure that changed. Git keeps all of them forever.
Squash them when a project phase closes.

The branch ruleset `setup.md` has you add blocks force pushes on `main` **on purpose** — it is the
guard against a stolen deploy key rewriting your history. Squashing is a rewrite, so the two collide.
The way through is to lower the guard deliberately for a few minutes, not to work around it.

**First, confirm nothing is in flight.** A job that starts mid-squash reads whatever the clone has,
and an unpushed cluster commit is destroyed in step 5.

```bash
ssh -o BatchMode=yes <alias> 'squeue --me'                      # no queued or running jobs
ssh -o BatchMode=yes <alias> 'cd <cluster-repo> && git status --short && git log --oneline @{u}..'
```

Both must come back empty. Then:

1. **(you)** GitHub → repo → Settings → Rules → Rulesets → the `main` ruleset → disable it.
2. Squash the phase's result commits into one. `<base>` is the last commit you want to keep:
   ```bash
   git log --oneline <base>..HEAD      # check this really is only results: commits
   git reset --soft <base>
   git commit -m "results: <phase name>"
   ```
3. `git push --force-with-lease`. **If it's refused, stop and ask the user** — it means someone or
   something pushed after your last fetch, so something was in flight after all. Don't merge, and
   don't force without the lease.
4. **(you)** Re-enable the ruleset, before the next job runs.
5. On the cluster: `git -C <cluster-repo> fetch && git -C <cluster-repo> reset --hard origin/main`.
   This is **destructive** — it discards anything uncommitted in the clone, which is what the check
   above was for.
6. Locally: `git reflog expire --expire=now --all && git gc --prune=now`. Until this runs, the old
   blobs are still on disk. GitHub reclaims its own copy on its own schedule.

Steps 1, 3 and 4 are the user's: an agent doesn't disable branch protection or force-push over
history.

**Squash earlier than a phase boundary** if `git count-objects -vH` shows the repo past a few hundred
MB, or if `results:` commits crowd out everything else in `git log --oneline | head -50`. Wait for the
next quiet moment rather than the next phase.

## End of the project phase

Revoke the deploy key in the repo settings. Squash the result commits (above). Archive or delete large
cluster data you no longer need — the profile says which filesystems are yours to keep tidy and which
are wiped for you.
