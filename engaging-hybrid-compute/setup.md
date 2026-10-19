# One-time setup

Placeholders: `<kerb>` your Kerberos username · `<alias>` the SSH host alias (e.g. `orcd-login`) · `<owner>/<repo>` the private GitHub repo · `<project>` a short project name · `<cluster-repo>` the clone on the cluster, e.g. `~/orcd/pool/<project>`.

Steps marked **(you)** need your password, Duo or a browser. Claude can't do them.

## 1. Cluster account and storage

1. **(you)** Log in once to OnDemand, https://orcd-ood.mit.edu. That creates the account; allow up to ~1 h before the first job.
2. Storage (check current quotas in the ORCD docs):

   | Path | Typical quota | Backed up | Use |
   |---|---|---|---|
   | `/home/<kerb>` | 200 GB | yes | code, environments |
   | `~/orcd/pool` | 1 TB | no | the project clone, data, results |
   | `~/orcd/scratch` | 1 TB | no | temporary; wiped after months of inactivity |

3. Free partitions (per-user caps on running jobs; check `sinfo` and `sacctmgr show qos`):

   | Partition | Max wall | Per-user cap | Use |
   |---|---|---|---|
   | `mit_quicktest` | 15 min | 48 CPU | smoke tests |
   | `mit_normal` | 12 h | 96 CPU, 386 GB | CPU work |
   | `mit_normal_gpu` | 6 h | 2 GPU, 32 CPU | GPU work |
   | `mit_preemptable` | 2 days | large | can be killed: checkpointed jobs only, `--requeue` |

   Heavy use only lowers your fair-share priority; the free tier has no CPU-hour bill.

## 2. SSH key and ControlMaster (local machine)

1. Make a dedicated Ed25519 key in 1Password (New Item → SSH Key) and enable its SSH agent (Settings → Developer), so the private key never sits on disk. Save the public key as `~/.ssh/engaging.pub`. Without 1Password, use `ssh-keygen -t ed25519 -f ~/.ssh/engaging` then drop the `IdentityAgent` line below and point `IdentityFile` at `~/.ssh/engaging` (the private key).
2. `~/.ssh/config`:
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
3. **(you)** Unlock 1Password whenever you connect or commit. Install the public key: `ssh-copy-id -i ~/.ssh/engaging.pub orcd-login` (password + Duo).
4. **(you)** Each working day: `ssh orcd-login` in a terminal, then approve Duo. For the next 8 h, `ssh -o BatchMode=yes orcd-login '...'` works without prompts, for you and for Claude. Check with `ssh -O check orcd-login`.
5. Optional, for VS Code Remote-SSH: `remote.SSH.connectTimeout: 60`, `remote.SSH.maxReconnectionAttempts: 1`, `remote.SSH.showLoginTerminal: true` (avoids a storm of Duo prompts).

### Optional: a gated reconnect helper

`scripts/engaging-connect` and `scripts/duo-askpass` let Claude reopen the socket with **one** Duo push that you approve on your phone. Your permission is still required before every run.
- Put both in `~/.local/bin`, `chmod +x`, and set `HOST=` in `engaging-connect` to your alias.
- In `~/.claude/settings.json`, add an **ask** rule so Claude Code prompts you every time:
  ```json
  { "permissions": { "ask": ["Bash(engaging-connect)", "Bash(engaging-connect *)"] } }
  ```
- The helper refuses to retry for 10 minutes after a failure, and the askpass answers only the Duo menu, never a password prompt.
- `duo-askpass` matches the Duo menu prompt text, and that text may change; check the log if the push never arrives.
- If the key is refused instantly with a message about the web portal, log in to OnDemand first.

## 3. Python environment on the cluster

```bash
ssh -o BatchMode=yes orcd-login 'curl -LsSf https://astral.sh/uv/install.sh | sh'   # installs ~/.local/bin/uv
```
- Pin the Python version in the repo (`.python-version`) and commit `uv.lock`, so the cluster resolves exactly what you have locally.
- Pin git dependencies to exact commits.
- Job scripts call `~/.local/bin/uv run --frozen python ...`, because `~/.local/bin` isn't on the batch `PATH`.

## 4. Private repo with a deploy key (cluster side)

A **deploy key** is scoped to one repo, so the cluster never holds your personal GitHub credentials.

```bash
# on the cluster (login node)
ssh-keygen -t ed25519 -f ~/.ssh/<project>_deploy -N "" -C "engaging <project>"
cat ~/.ssh/<project>_deploy.pub
```
1. **(you)** GitHub → repo → Settings → Deploy keys → Add. Paste the key, **tick "Allow write access"** (needed for `push_results.sh`).
2. On the cluster, in `~/.ssh/config`:
   ```
   Host github-<project>
     HostName github.com
     User git
     IdentityFile ~/.ssh/<project>_deploy
     IdentitiesOnly yes
   ```
3. Verify GitHub's host key fingerprint against the one GitHub publishes before accepting it into `known_hosts`.
4. Clone into pool storage:
   ```bash
   git clone github-<project>:<owner>/<repo>.git ~/orcd/pool/<project>
   cd ~/orcd/pool/<project> && ~/.local/bin/uv sync --frozen && mkdir -p slurm/logs
   ```
5. Set the commit identity in the cluster clone (`git config user.name/user.email`), so result commits are attributable.

## 5. Repo layout and `.gitignore`

```
NN_experiment/          one folder per experiment, with a runnable script and its small outputs
slurm/run_modes.sh      generic array runner (scripts/run_modes.sh)
slurm/push_results.sh   results committer (scripts/push_results.sh)
slurm/logs/             git-ignored
NOTES.md                running log of decisions and findings
```
`.gitignore`: `.venv/`, `slurm/logs/`, `__pycache__/`, and large caches or snapshots.

## 6. Smoke test

Submit a `mit_quicktest` job that imports everything and runs one small case. Compare its output with a local run. That catches environment differences before a long job does.

## 7. Tell Claude about the project

Add to the project's `CLAUDE.md`:
```
- Heavy compute runs only on Engaging (Slurm, CPU partitions); local is for editing, plots and quick checks.
- Cluster clone: <cluster-repo>. Before submitting: git pull --rebase (autostash), uv sync --frozen if uv.lock changed, verify the new code is present.
- After jobs: slurm/push_results.sh "<message>" on the login node; locally git pull --rebase.
- Not in git: .venv, slurm/logs, large caches (rsync only when needed).
```

## 8. End of the project phase

Revoke the deploy key in the repo settings. Archive or delete large pool data you no longer need.
