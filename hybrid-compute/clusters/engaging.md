# MIT Engaging (ORCD)

Read with `SKILL.md`, which has the workflow. This file is only what Engaging does differently.

Placeholders: `<kerb>` your Kerberos username · `<alias>` the SSH host alias (`orcd-login` below) ·
`<project>` a short project name · `<cluster-repo>` the clone, e.g. `~/orcd/pool/<project>`.
Steps marked **(you)** need a password, Duo or a browser; Claude can't do them.

## Connecting

Engaging needs **two** things: an SSH key *and* Duo. A key replaces the password but **does not skip
Duo**. The way round it is a ControlMaster socket: the user opens one connection (one Duo push), and
every later `ssh`, `scp` or `rsync` reuses it for the `ControlPersist` window (8 h below).

1. Check: `ssh -O check orcd-login`.
2. If "Master running": run everything as `ssh -o BatchMode=yes orcd-login '<cmd>'`.
3. If not, the user has to reconnect — either `ssh orcd-login` in their own terminal with a Duo
   approval, or the gated helper below. Call it only as `engaging-connect`, never by path or through
   a wrapper, so its permission rule fires.
   - Tell the user first that a permission prompt and a Duo push are coming, with a push
     notification if your harness has one, so they can approve from their phone when away from the
     machine.
   - **At most one reconnect attempt per need. Never loop.** Repeated failed attempts can trigger a
     Duo lockout.

Never run `ssh -O exit orcd-login` — it kills the user's shared socket. Never run plain
`ssh orcd-login` without `BatchMode=yes`, which hangs on the Duo menu.

**Failure messages:**

- Key refused instantly, with a message about logging in to the web portal: key auth needs a recent
  OnDemand login (about a day). **(you)** Log in at <https://orcd-ood.mit.edu> in a browser first.
  Ask the user; don't retry.
- `sign_and_send_pubkey: signing failed ... communication with agent failed`, then
  `Permission denied (publickey)`: the local SSH agent (1Password) is locked or asleep. Ask the user
  to unlock it.

### `~/.ssh/config` (local machine)

```
Host orcd-login
  HostName orcd-login.mit.edu
  User <kerb>
  IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"   # macOS; Linux: ~/.1password/agent.sock
  IdentityFile ~/.ssh/engaging.pub      # the .pub selects the key in the agent
  IdentitiesOnly yes
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h:%p
  ControlPersist 8h
```

**(you)** Install the public key once: `ssh-copy-id -i ~/.ssh/engaging.pub orcd-login` (password +
Duo). Each working day, `ssh orcd-login` in a terminal and approve Duo; for the next 8 h every
`BatchMode` call works without prompts, for the user and for Claude.

For VS Code Remote-SSH, set `remote.SSH.connectTimeout: 60`,
`remote.SSH.maxReconnectionAttempts: 1`, `remote.SSH.showLoginTerminal: true`. Otherwise a
reconnection storm becomes a storm of Duo prompts.

### The gated reconnect helper

`scripts/engaging/engaging-connect` and `scripts/engaging/duo-askpass` let Claude reopen the socket
with **one** Duo push that the user approves on their phone. The user's permission is still required
before every run.

- Put both in `~/.local/bin`, `chmod +x`, and set `HOST=` in `engaging-connect` to the alias.
- Add an **ask** rule in `~/.claude/settings.json` so Claude Code prompts every time:
  ```json
  { "permissions": { "ask": ["Bash(engaging-connect)", "Bash(engaging-connect *)",
                             "Bash(~/.local/bin/engaging-connect)", "Bash(~/.local/bin/engaging-connect *)"] } }
  ```
  The rule matches the command as typed, so a wrapper (`bash -c …`) slips past it. That is why
  `SKILL.md` and this file say to call the helper only by its bare name.
- Needs `timeout`, which macOS doesn't ship: `brew install coreutils`. Without it the helper exits
  (code 3) before any attempt.
- The helper refuses to retry for 10 minutes after a failure, and the askpass answers only the Duo
  menu, never a password prompt.
- `duo-askpass` matches the Duo menu prompt text, and that text may change; check
  `~/.ssh/engaging-connect.log` if the push never arrives.

## Account and storage

**(you)** Log in once to OnDemand, <https://orcd-ood.mit.edu>. That creates the account; allow up to
about an hour before the first job.

| Path | Typical quota | Backed up | Use |
|---|---|---|---|
| `/home/<kerb>` | 200 GB | yes | code, environments |
| `~/orcd/pool` | 1 TB | no | the project clone, data, results |
| `~/orcd/scratch` | 1 TB | no | temporary; wiped after months of inactivity |

Check current quotas in the ORCD docs; they change.

Clone the repo into pool storage: `git clone github-<project>:<owner>/<repo>.git ~/orcd/pool/<project>`,
then `~/.local/bin/uv sync --frozen && mkdir -p slurm/logs`.

Install uv pinned to the local version (`uv --version`), so the installer can't change underneath:

```bash
ssh -o BatchMode=yes orcd-login 'curl -LsSf https://astral.sh/uv/<version>/install.sh | sh'
```

Home is large enough here, so uv's cache needs no redirection. Job scripts still call
`~/.local/bin/uv` by full path, because `~/.local/bin` isn't on the batch `PATH`.

## Partitions and caps

Free tier (per-user caps on running jobs; check `sinfo` and `sacctmgr show qos`):

| Partition | Max wall | Per-user cap | Use |
|---|---|---|---|
| `mit_quicktest` | 15 min | 48 CPU | smoke tests — the short-test partition `SKILL.md` refers to |
| `mit_normal` | 12 h | 96 CPU, 386 GB | CPU work |
| `mit_normal_gpu` | 6 h | 2 GPU, 32 CPU | GPU work |
| `mit_preemptable` | 2 days | large | can be killed: checkpointed jobs only, `--requeue` |

**Free tier only** unless the user explicitly asks otherwise: no paid QOS, reservations or rentals.
The free tier has no CPU-hour bill — heavy use only lowers fair-share priority. If a job only fits a
paid tier, don't submit: say which limit it exceeds and what the paid option would cost (current
prices in the ORCD docs), and offer the free alternatives from `SKILL.md`.

For `scripts/run_modes.sh`, the `#SBATCH -p` placeholder takes one of these, and `-c`/`--mem` must
stay inside that partition's per-user cap. Memory isn't billed here, but it still limits how many of
your jobs run at once: big-memory jobs run a few at a time.

**Fair share** (check the live values; sites retune them): at the time of writing
`PriorityDecayHalfLife` is 7 days, and within one partition the partition term is the same for
everyone, so fair share is the main factor that differs between users — job size and age add only a
little. Billing is per allocated CPU × elapsed time (`scontrol show partition <p> | grep TRES`).

## Site-specific breakage

**Pending reasons:**

- `ReqNodeNotAvail, Reserved for maintenance` — a reservation (e.g. monthly maintenance) is coming
  and the job's time limit would overlap it. If the job really needs less time, lower its limit so
  it fits before the window: `scontrol update JobId=<id>_0 TimeLimit=03:00:00` (users can lower, not
  raise, limits). `scontrol show res | grep -E "ReservationName|StartTime"` shows the windows.
- `QOSMaxCpuPerUserLimit` — at the per-user cap; jobs start in waves. To free slots, cancel your own
  jobs that have become uninformative. Ask before cancelling anything the user started.
- `Priority` and `Dependency` are as in `SKILL.md`.

**Other:** node speed varies between nodes, and between clusters — one JAX orbit-integration step
that took 5.8 s on an Engaging node took 9.4–10.4 s on subMIT. Size `--time` from a pilot on *this*
cluster.

## End of the project phase

Revoke the deploy key in the repo settings. Archive or delete large `~/orcd/pool` data you no longer
need; `~/orcd/scratch` is wiped for you after months of inactivity.
