# One-time setup

The cluster-independent half. The site-specific half — account creation, the `~/.ssh/config` block,
storage paths, which partitions exist, how to install the Python environment — is in
`clusters/<name>.md`. Do the steps here, and take each cluster-specific value from the profile.

Placeholders: `<alias>` the SSH host alias from the profile · `<owner>/<repo>` the private GitHub
repo · `<project>` a short project name · `<cluster-repo>` the clone path from the profile.

Steps marked **(you)** need a password, a second factor, a browser or an email. Claude can't do them.

## 1. An SSH key for the cluster (local machine)

Make a **dedicated** Ed25519 key, ideally in 1Password (New Item → SSH Key) with its SSH agent
enabled (Settings → Developer), so the private key never sits on disk. Save the public key as
`~/.ssh/<project>.pub` — the `.pub` is what selects the key in the agent.

Without 1Password: `ssh-keygen -t ed25519 -f ~/.ssh/<project>`, then drop the `IdentityAgent` line
from the profile's config block and point `IdentityFile` at the private key.

**(you)** Install or upload the key as the profile says — some clusters take `ssh-copy-id`, some want
it uploaded to a portal. Then take the rest of the connection recipe from the profile: that is where
clusters differ most.

**(you)** Unlock 1Password whenever you connect or commit. A locked agent shows up as an SSH failure
*and* as a commit-signing failure, which look unrelated until you know.

## 2. Gate cluster commands

Once the connection works, anything running as your local user — Claude included — gets a shell on
the cluster with no further prompt. The rules in `SKILL.md` are only instructions. To be asked before
each one, add to `~/.claude/settings.json`:

```json
{ "permissions": { "ask": ["Bash(ssh <alias> *)", "Bash(ssh -o BatchMode=yes <alias> *)",
                           "Bash(scp *)", "Bash(rsync *)"] } }
```

Commands run *inside* a script (e.g. `watch_jobs.sh`) are not matched: approving the script approves
everything it runs. A profile may add its own ask rules for site-specific helpers.

## 3. Python environment

The profile has the install command and says where the cache must live. What is the same everywhere:

- Pin the Python version in the repo (`.python-version`) and commit `uv.lock`, so the cluster
  resolves exactly what you have locally. Sync with `uv sync --frozen` (or `--locked`).
- Pin git dependencies to exact commits.
- Pin the uv version you install to the one you run locally (`uv --version`), so the installer can't
  change under you.
- Job scripts call `uv` **by full path** (`~/.local/bin/uv run --frozen python ...`), because
  `~/.local/bin` isn't on the non-interactive `PATH`.

## 4. Private repo with a deploy key (cluster side)

A **deploy key** is scoped to one repo, so the cluster never holds your personal GitHub credentials.

```bash
# on the cluster's login node
ssh-keygen -t ed25519 -f ~/.ssh/<project>_deploy -N "" -C "<project> on <alias>"
cat ~/.ssh/<project>_deploy.pub
```

1. **(you)** GitHub → repo → Settings → Deploy keys → Add. Paste the key and **tick "Allow write
   access"** — `push_results.sh` needs it.

   The key has no passphrase (jobs push unattended) and sits on a shared cluster, so anyone who gets
   into your cluster account can push to the repo. Limit the damage:
   - **(you)** Settings → Rules → Rulesets → new branch ruleset on `main`: **block force pushes and
     deletions**, so history can't be rewritten. This is also what the squash procedure in `SKILL.md`
     has to work around — deliberately, which is the point.
   - Review what the cluster pushed before pulling it, every time (step 6 of the daily loop). That
     review is the reason small results travel through git at all.
2. On the cluster, in `~/.ssh/config`:
   ```
   Host github-<project>
     HostName github.com
     User git
     IdentityFile ~/.ssh/<project>_deploy
     IdentitiesOnly yes
   ```
3. Verify GitHub's host key fingerprint against the one GitHub publishes before accepting it into
   `known_hosts`.
4. Clone into the filesystem the profile names, then sync the environment and
   `mkdir -p slurm/logs`.
5. Set the commit identity in the cluster clone (`git config user.name` / `user.email`), so result
   commits are attributable.

## 5. Repo layout and `.gitignore`

```text
NN_experiment/          one folder per experiment, with a runnable script and its small outputs
slurm/run_modes.sh      generic array runner (scripts/run_modes.sh)
slurm/push_results.sh   results committer (scripts/push_results.sh)
slurm/logs/             git-ignored
NOTES.md                running log of decisions and findings
```

`.gitignore`: `.venv/`, `slurm/logs/`, `__pycache__/`, and large caches, snapshots or checkpoints —
everything on the rsync side of the division in `SKILL.md`.

Copy the scripts from `scripts/` into `slurm/` and edit their marked placeholders: the `#SBATCH`
partition and resource lines, and the clone path. The profile says what to put in each.

## 6. Pilot

Submit a few-minute job on the real code (`-t 00:08:00`) on the partition the profile names for short
work: imports, one small case, and the configuration printed on the first lines. Compare its output
with a local run, and read `seff <jobid>` for CPU efficiency and peak memory. Size the real jobs from
that, not from the partition maximum. Run it at two CPU counts if threading matters; a profile may
have a worked example of why doubling CPUs often buys nothing.

## 7. Tell Claude about the project

Add to the project's `CLAUDE.md`:

```text
- Heavy compute runs only on <cluster> (Slurm); local is for editing, plots and quick checks.
- Cluster clone: <cluster-repo>. Before submitting: git pull --rebase (autostash), uv sync --frozen
  if uv.lock changed, verify the new code is present.
- After jobs: slurm/push_results.sh "<message>" on the login node; locally git pull --rebase.
- Not in git: .venv, slurm/logs, large caches and snapshots (rsync only when needed).
- <anything from the cluster profile that bites in this project, e.g. a partition to avoid.>
```

## 8. End of the project phase

Revoke the deploy key in the repo settings, squash the result commits (see `SKILL.md`), and clean up
cluster storage as the profile describes.
