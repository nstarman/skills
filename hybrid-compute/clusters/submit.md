# MIT subMIT

Read with `SKILL.md`, which has the workflow. This file is only what subMIT does differently.

Placeholders: `<kerb>` your Kerberos username · `<k>` its first letter · `<alias>` the SSH host alias
(`submit` below) · `<project>` a short project name · `<cluster-repo>` the clone,
`/work/submit/<kerb>/<project>`. Steps marked **(you)** need Touchstone, an email or a browser;
Claude can't do them.

subMIT is the physics department's login pool and Slurm cluster. It is free to use, with no paid
tiers to avoid. User guide: <https://submit.mit.edu/submit-users-guide/>
(source: <https://github.com/mit-submit/submit-users-guide>).

## Connecting

Key only, **no Duo**, so there is no ControlMaster socket and no reconnect helper: every call is a
fresh connection.

- Run everything as `ssh -o BatchMode=yes submit '<cmd>'`.
- `submit.mit.edu` is a **round-robin of login nodes** (submit01…submit08 and so on). Two calls can
  land on different machines. `/home`, `/work` and `/ceph` are shared, so files are the same
  everywhere, but **processes are not**: a `nohup` or `screen` started on one call may not exist on
  the next. Use Slurm for anything long-running, never a background process on a login node.

**Failure messages** — read the error before doing anything, and don't retry in a loop:

- `sign_and_send_pubkey: signing failed ... communication with agent failed`, then
  `Permission denied (publickey)`: the local SSH agent (1Password) is locked or asleep. Ask the user
  to unlock it.
- A plain `Permission denied (publickey)` with no agent error: the key isn't on the portal (any
  more). The user re-uploads it.

Never touch `~/.ssh/authorized_keys` here: the portal manages keys.

### Account and `~/.ssh/config`

1. **(you)** With an MIT Kerberos account, upload the SSH public key at
   <https://submit-portal.mit.edu> (Touchstone login). Without one, a faculty sponsor requests an MIT
   guest account first.
2. **(you)** Email submit-help@mit.edu for final access, naming the group you work with (for group
   storage). Asking for more quota is also the user's job, not Claude's.

```
Host submit
  HostName submit.mit.edu
  User <kerb>
  IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"   # macOS; Linux: ~/.1password/agent.sock
  IdentityFile ~/.ssh/submit.pub        # the .pub selects the key in the agent
  IdentitiesOnly yes
```

Check with `ssh -o BatchMode=yes submit hostname`: it prints a login node, e.g. `submit08.mit.edu`.

## Storage

**Home is only 10 GB** — too small for environments. Everything of size goes in `/work`.

| Path | Quota | Backed up | Use |
|---|---|---|---|
| `/home/submit/<kerb>` | 10 GB | yes | dotfiles, small notes |
| `/work/submit/<kerb>` | 100 GB | no | the project clone, `.venv`, the uv cache |
| `/ceph/submit/data/user/<k>/<kerb>` | 1 TB | no | large outputs; **large files only** (no 100k+ small files) |
| `/scratch/submit/...` | — | no | fast I/O, short-term — the rsync source `SKILL.md` mentions |

All are mounted on the login nodes and on every Slurm node. Check usage with `quota -s`.

Clone into `/work`: `git clone github-<project>:<owner>/<repo>.git /work/submit/<kerb>/<project>`,
then `~/.local/bin/uv sync --frozen && mkdir -p slurm/logs`.

Install uv pinned to the local version (`uv --version`), keeping it out of the shell rc files:

```bash
ssh -o BatchMode=yes submit 'curl -LsSf https://astral.sh/uv/<version>/install.sh | env UV_NO_MODIFY_PATH=1 sh'
```

**Keep uv's cache and Python installs in `/work`**, or a single JAX environment fills the 10 GB home.
Export these in every login command and job script (or in `~/.bashrc`) — they are the
`run_modes.sh` exports that this profile turns on:

```bash
export UV_CACHE_DIR=/work/submit/<kerb>/.cache/uv
export UV_PYTHON_INSTALL_DIR=/work/submit/<kerb>/.local/share/uv/python
```

With the cache and the project on the same filesystem, uv hardlinks packages, so the `.venv` itself
stays small.

A JAX environment imports fine on a login node, so a quick import check needs no job. Real runs
still go to Slurm.

For a **one-off run of an existing project** with no deploy key yet, `rsync -az -e ssh` the working
tree to `/work/submit/<kerb>/<project>` instead of cloning (excluding `.venv`, data and build
outputs), and `rsync` results back. Exclude the cluster-only `slurm/` folder from any `--delete`
sync, or it is wiped. Everything else in `SKILL.md` still applies.

## Partitions and caps

| Partition | Max wall | Use |
|---|---|---|
| `submit` | 6 days | CPU work |
| `submit-gpu` | 2 days | GPU work |
| `submit-gpu-express` | 1 h | short GPU work — the short-test partition `SKILL.md` refers to |
| `tier3` | — | **old CPUs; see below** |

- **Always pass `--time`.** Without it a job gets the 12 h default, which both kills long runs and
  hides short ones from backfill. In `scripts/run_modes.sh` the `#SBATCH -t` line is not optional
  here.
- **Login nodes are shared and busy** (load ~50 is normal). The subMIT guide sets ~15 minutes as the
  line for work on a login node; stay well under it.
- **Memory is a consumable resource**, like CPUs: a job holding a node's memory blocks that node even
  if its CPUs sit idle. Request from history (`seff <jobid>` or `sacct -o MaxRSS`) plus a cushion.
  Most nodes have 64–128 GB.
- **The partition is often full.** Even with top fair share, array tasks can wait as `(Resources)`:
  one evening, 28 of 29 `submit` nodes were allocated and over 1000 jobs were pending, so 2 of 8
  tasks started at once and the rest queued. Plan for wall time well beyond the run time, and check
  with `sinfo -p submit -o "%D %T"` and `squeue --me --start`.

**Fair share** (check the live values): multifactor priority with fair share as the largest weight —
at the time of writing FairShare 10000, JobSize 2000, Partition 1000, Age 500, with a 7-day decay
half-life. Billing is CPUs × elapsed time. The cluster is shared by the whole department.

## Site-specific breakage

- **`tier3` CPUs lack AVX2** (mostly even AVX). JAX, standard TensorFlow and many optimized wheels
  die there with `Illegal instruction`. **Never send such jobs to `tier3`, and never to
  `--partition=submit,tier3`** — the comma means Slurm may pick either.
- **An overnight watcher dies when 1Password auto-locks.** Each check is a fresh connection, and a
  locked agent refuses to sign. The jobs keep running; only the watcher stops. Tell the user before a
  long watch so they can lengthen the auto-lock or plan to check in by hand.
- **Node speed varies**, here and between clusters. A JAX orbit-integration step: 4 CPUs → 10.4 s/step
  at 57% CPU efficiency; 8 CPUs → 9.4 s/step at 40%. Doubling the CPUs bought 10% for twice the
  billing, so 4 was right — JAX's CPU backend often uses only 2–3 cores. The same step took 5.8 s on
  an Engaging node, so size `--time` from a pilot on *this* cluster; the 6-day limit leaves room.
- `srun --jobid=<jobid> --overlap --pty bash` gets a shell on a running job's node (the user only;
  it's interactive).

## End of the project phase

Revoke the deploy key in the repo settings. Delete what you no longer need in `/work` and `/ceph`:
storage there is yours to keep tidy, and nothing wipes it for you.
