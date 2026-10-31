# One-time setup

Placeholders: `<kerb>` your Kerberos username · `<k>` its first letter · `<alias>` the SSH host alias (e.g. `submit`) · `<owner>/<repo>` the private GitHub repo · `<project>` a short project name · `<cluster-repo>` the clone on the cluster, `/work/submit/<kerb>/<project>`.

Steps marked **(you)** need Touchstone, an email or a browser. Claude can't do them.

## 1. Account

1. **(you)** With an MIT Kerberos account, upload your SSH public key at https://submit-portal.mit.edu (Touchstone login). Without one, a faculty sponsor requests an MIT guest account first.
2. **(you)** Email submit-help@mit.edu for final access, naming the group you work with (for group storage).

subMIT is free to use; there are no paid tiers to avoid. Its user guide is at https://submit.mit.edu/submit-users-guide/ (source: https://github.com/mit-submit/submit-users-guide).

## 2. SSH key (local machine)

1. Make a dedicated Ed25519 key, ideally in 1Password (New Item → SSH Key, with its SSH agent enabled), and upload its public key at the portal. Save the public key as `~/.ssh/submit.pub`.
2. `~/.ssh/config`:
   ```
   Host submit
     HostName submit.mit.edu
     User <kerb>
     IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"   # macOS; Linux: ~/.1password/agent.sock
     IdentityFile ~/.ssh/submit.pub        # the .pub selects the key in the agent
     IdentitiesOnly yes
   ```
   Without 1Password: `ssh-keygen -t ed25519 -f ~/.ssh/submit`, drop the `IdentityAgent` line and point `IdentityFile` at the private key.
3. Check: `ssh -o BatchMode=yes submit hostname` prints a login node (e.g. `submit08.mit.edu`). No Duo is involved.
4. **Gate cluster commands.** Anything running as your local user, Claude included, can open a shell on subMIT with no prompt. The rules in `SKILL.md` are only instructions. To be asked before each one, add to `~/.claude/settings.json`:
   ```json
   { "permissions": { "ask": ["Bash(ssh submit *)", "Bash(ssh -o BatchMode=yes submit *)",
                              "Bash(scp *)", "Bash(rsync *)"] } }
   ```

## 3. Storage

| Path | Quota | Backed up | Use |
|---|---|---|---|
| `/home/submit/<kerb>` | 10 GB | yes | dotfiles, small notes. **Too small for environments.** |
| `/work/submit/<kerb>` | 100 GB | no | the project clone, `.venv`, the uv cache |
| `/ceph/submit/data/user/<k>/<kerb>` | 1 TB | no | large outputs; large files only (no 100k+ small files) |
| `/scratch/submit/...` | — | no | fast I/O, short-term |

All are mounted on the login nodes and on every Slurm node. Check usage with `quota -s`.

## 4. Python environment

```bash
ssh -o BatchMode=yes submit 'curl -LsSf https://astral.sh/uv/<version>/install.sh | env UV_NO_MODIFY_PATH=1 sh'   # ~/.local/bin/uv
```
- `<version>` is the uv you use locally (`uv --version`), so the installer can't change under you. `UV_NO_MODIFY_PATH=1` keeps it out of your shell rc files.
- Keep uv's cache and Python installs in `/work`, or a single JAX environment fills the 10 GB home. Export these in every login command and job script (or in `~/.bashrc`):
  ```bash
  export UV_CACHE_DIR=/work/submit/<kerb>/.cache/uv
  export UV_PYTHON_INSTALL_DIR=/work/submit/<kerb>/.local/share/uv/python
  ```
  With the cache and the project on the same filesystem, uv hardlinks packages, so the `.venv` itself stays small.
- Pin the Python version in the repo (`.python-version`) and commit `uv.lock`; sync with `uv sync --frozen` (or `--locked`).
- A JAX env imports fine on a login node, so a quick import check needs no job. Real runs still go to Slurm.

## 5. Private repo with a deploy key (cluster side)

A **deploy key** is scoped to one repo, so the cluster never holds your personal GitHub credentials.

```bash
# on a login node
ssh-keygen -t ed25519 -f ~/.ssh/<project>_deploy -N "" -C "submit <project>"
cat ~/.ssh/<project>_deploy.pub
```
1. **(you)** GitHub → repo → Settings → Deploy keys → Add. Paste the key, **tick "Allow write access"** (needed for `push_results.sh`). The key has no passphrase and sits on a shared cluster, so:
   - **(you)** Settings → Rules → Rulesets → branch ruleset on `main`: block force pushes and deletions.
   - Review what the cluster pushed before running it locally (see the daily loop in `SKILL.md`).
2. On the cluster, in `~/.ssh/config`:
   ```
   Host github-<project>
     HostName github.com
     User git
     IdentityFile ~/.ssh/<project>_deploy
     IdentitiesOnly yes
   ```
3. Verify GitHub's host key fingerprint against the one GitHub publishes before accepting it into `known_hosts`.
4. Clone into `/work`:
   ```bash
   git clone github-<project>:<owner>/<repo>.git /work/submit/<kerb>/<project>
   cd /work/submit/<kerb>/<project> && ~/.local/bin/uv sync --frozen && mkdir -p slurm/logs
   ```
5. Set the commit identity in the cluster clone (`git config user.name/user.email`).

For a one-off run without a deploy key, `rsync -az -e ssh` the working tree to `/work/submit/<kerb>/<project>` (excluding `.venv`, data and build outputs), and later `rsync` results back. Exclude the cluster-only `slurm/` folder from any `--delete` sync, or it is wiped.

## 6. Repo layout and `.gitignore`

```
NN_experiment/          one folder per experiment, with a runnable script and its small outputs
slurm/run_modes.sh      generic array runner (scripts/run_modes.sh)
slurm/push_results.sh   results committer (scripts/push_results.sh)
slurm/logs/             git-ignored
NOTES.md                running log of decisions and findings
```
`.gitignore`: `.venv/`, `slurm/logs/`, `__pycache__/`, and large caches or outputs.

## 7. Pilot

Submit a few-minute job on the `submit` partition that runs the real code (`-t 00:08:00`), at two CPU counts if threading matters. Read the per-step time and `seff <jobid>`, compare with a local run, and size the real jobs from that.

## 8. Tell Claude about the project

Add to the project's `CLAUDE.md`:
```
- Heavy compute runs only on subMIT (Slurm, partition submit; never tier3 for JAX); local is for editing, plots and quick checks.
- Cluster clone: <cluster-repo>. Before submitting: git pull --rebase (autostash), uv sync --frozen if uv.lock changed, verify the new code is present.
- uv on subMIT: ~/.local/bin/uv, with UV_CACHE_DIR and UV_PYTHON_INSTALL_DIR under /work/submit/<kerb>.
- After jobs: slurm/push_results.sh "<message>" on a login node; locally git pull --rebase.
- Not in git: .venv, slurm/logs, large outputs (rsync only when needed).
```

## 9. End of the project phase

Revoke the deploy key in the repo settings. Delete what you no longer need in `/work` and `/ceph`.
