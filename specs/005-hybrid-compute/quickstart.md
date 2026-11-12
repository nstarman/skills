# Verifying the change

Run from the repository root on branch `005-hybrid-compute`. The content checks come first, because
they are the ones that can fail silently; the mechanical checks catch the rest.

## Prerequisites

- Python 3 (standard library only).
- `claude` CLI for plugin validation, as CI uses it.
- Optional: `~/.config/skills/personal-strings.txt`, or the personal-details check skips itself.

## 1. Content: every site-specific fact survived

Do this **before deleting** `engaging-hybrid-compute/` and `submit-hybrid-compute/`, while both
versions are side by side.

For each retired skill, walk its `SKILL.md` and `setup.md` and confirm each site-specific fact is
present in the matching `clusters/*.md`. The facts that must appear, at minimum:

**Engaging** — Duo is not skipped by a key; the ControlMaster socket and `ControlPersist`; `ssh -O
check` before acting and `BatchMode=yes` for every call; never `ssh -O exit`; the one-reconnect rule
and the lockout risk; the OnDemand login requirement for key auth; the gated `engaging-connect`
helper called only by bare name; home/pool/scratch paths and quotas; the four free partitions with
their wall limits and per-user caps; the free-tier-only rule and what to do when a job only fits a
paid tier; `scontrol show config`, `sshare`, `sprio` and the decay half-life; the maintenance-window
and pending-reason table.

**subMIT** — key-only login via the portal, no Duo; the round-robin login nodes and what that means
for background processes; the two key-refusal messages and their different causes; login-node load
and the ~15-minute line; the 10 GB home, `/work` at 100 GB, `/ceph` at 1 TB and its no-many-small-
files rule; `UV_CACHE_DIR` and `UV_PYTHON_INSTALL_DIR` under `/work`; the partitions and their
limits; `tier3` lacking AVX2 and killing JAX, including never using `--partition=submit,tier3`;
always pass `--time`; the partition-full reality and `sinfo` / `squeue --me --start`; `seff`; the
1Password auto-lock killing an overnight watcher.

Then confirm the converse: nothing in a profile restates shared workflow guidance.

```bash
# No workflow paragraph should appear in two files.
python - <<'PY'
import pathlib, re, collections
files = list(pathlib.Path("hybrid-compute").rglob("*.md"))
seen = collections.defaultdict(list)
for f in files:
    for para in re.split(r"\n\s*\n", f.read_text()):
        key = " ".join(para.split())
        if len(key) > 120:
            seen[key].append(f.as_posix())
dupes = {k: v for k, v in seen.items() if len(v) > 1}
print(f"{len(dupes)} duplicated paragraphs")
for k, v in dupes.items():
    print(" ", v, k[:90])
PY
```

Expected: `0 duplicated paragraphs`.

## 2. Content: the structure holds

```bash
ls hybrid-compute hybrid-compute/clusters hybrid-compute/scripts hybrid-compute/scripts/engaging
grep -n "clusters/" hybrid-compute/SKILL.md | head
awk 'END{print NR" lines"}' hybrid-compute/SKILL.md
python -c "import json;d=json.load(open('hybrid-compute/card.json'));print(sorted(d),d['name'])"
```

Expected: `SKILL.md`, `setup.md`, `card.json`, `clusters/`, `scripts/`; `engaging.md` and
`submit.md`; the three shared scripts plus `scripts/engaging/` with the two helpers; `SKILL.md`
pointing at `clusters/<name>.md` within its first few lines and listing both profiles by name; fewer
than 500 lines; a card with exactly `description` and `name`, named `hybrid-compute`.

Read each profile and check it has the four headings — Connecting, Storage, Partitions and caps,
Site-specific breakage — and that no shared value is hard-coded in `SKILL.md`:

```bash
# Skip the frontmatter: its description must name the clusters (FR-009), and the pointer
# table must list the profiles by name (FR-005). The body prose must not.
sed '1,/^---$/d;1,/^---$/d' hybrid-compute/SKILL.md |
  grep -nE "mit_quicktest|mit_normal|/work/submit|/ceph/submit|orcd|tier3|submit\.mit\.edu|Engaging|subMIT" |
  grep -v 'clusters/'
grep -nE "mit_quicktest|mit_normal|/work/submit|/ceph/submit|orcd|tier3|submit\.mit\.edu|Engaging|subMIT" hybrid-compute/setup.md
```

Expected: no output from either. Those values belong in the profiles.

## 3. Content: the two new sections answer their questions

Read the transport section and confirm it assigns each of these without the reader guessing: a
40 KB figure, a 3 MB `.npz` of fit parameters, a one-page summary table, a 200 MB simulation
snapshot, a checkpoint directory, Slurm logs. Confirm it states that the review-before-pull check is
why small results go through git, names the exclusions for a large transfer, and warns against
pointing a `--delete` sync at the cluster-only `slurm/` folder.

Read the squash section and confirm it names the branch-ruleset conflict, marks the ruleset changes
and the force push as the author's, states the nothing-in-flight precondition (no queued or running
jobs, no unpushed commits in the cluster clone), gives a size trigger for squashing before a phase
ends, and covers both `git gc --prune=now` locally and `git reset --hard origin/main` in the cluster
clone.

Optionally rehearse it on a scratch repository to confirm the steps are in a workable order:

```bash
cd "$(mktemp -d)" && git init -q --bare origin.git && git clone -q origin.git work && cd work
for i in 1 2 3; do echo "$i" > "fig$i.png"; git add -A; git commit -qm "results: run $i"; done
git push -q -u origin HEAD:main
git reset --soft HEAD~3 && git commit -qm "results: phase 1" && git push --force-with-lease
git log --oneline      # one results commit
```

## 4. Mechanical checks

```bash
python -m unittest discover tests
```

```bash
python scripts/build_index.py
```

```bash
git diff --stat index.json .claude-plugin/marketplace.json README.md
```

```bash
python scripts/build_index.py --check --remote
```

```bash
claude plugin validate .
```

```bash
python scripts/personal_check.py
```

Expected: tests pass; the regenerated outputs list `hybrid-compute` and neither retired name;
`--check --remote` is clean; plugin validation passes; no personal details.

```bash
grep -rn "engaging-hybrid-compute\|submit-hybrid-compute" . --exclude-dir=.git --exclude-dir=.claude --exclude-dir=specs
```

Expected: no output. References inside `specs/` are history and stay.

## 5. Install checks

```bash
python scripts/release_zips.py "$(mktemp -d)/zips" && unzip -l "$_"/hybrid-compute.zip
```

Expected: one zip per skill; `hybrid-compute.zip` contains `hybrid-compute/SKILL.md`,
`hybrid-compute/setup.md`, both `clusters/*.md` and all five scripts, and does **not** contain
`card.json`.

## Done when

- Every fact in section 1's two lists is in the matching profile, and no paragraph is duplicated.
- Sections 2 and 3 read as described.
- Section 4 and 5 commands all succeed.
