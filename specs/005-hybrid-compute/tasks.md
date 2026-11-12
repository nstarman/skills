---

description: "Task list for 005-hybrid-compute"
---

# Tasks: One hybrid-compute skill with per-cluster profiles

**Input**: Design documents from `specs/005-hybrid-compute/`

**Prerequisites**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md),
[quickstart.md](./quickstart.md)

**Tests**: Included. Not TDD-by-preference — FR-017 requires the repository's existing automated
checks to cover the single skill and keep passing, so retargeting `tests/test_hybrid_compute.py` is
required work, not an optional extra.

**Organization**: Tasks are grouped by user story. The content stories (US1, US2) are the
restructure; US3 makes a single cluster usable end to end; US4 and US5 are the two new
cluster-independent sections.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story the task serves (US1–US5)
- Exact file paths are given in every task

## Path Conventions

Repository root is the skills registry. Skill content under `hybrid-compute/`, tests under `tests/`,
generated outputs at the root. Paths below are repository-relative.

## ⚠️ Ordering constraint that overrides convenience

**The two retired folders are deleted last** (T030), after the fact-by-fact comparison in T028.
`engaging-hybrid-compute/` and `submit-hybrid-compute/` are the only copy of the site-specific facts
and of the scripts; deleting them before the comparison turns a missed fact into a silent loss. Every
earlier task copies out of them, never moves.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The folder skeleton the rest of the work writes into.

- [X] T001 Create the skill folder skeleton `hybrid-compute/`, `hybrid-compute/clusters/`, `hybrid-compute/scripts/` and `hybrid-compute/scripts/engaging/` per the Source Code tree in [plan.md](./plan.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The skill's identity. `scripts/build_index.py` and `claude plugin validate .` read these
two, so nothing else can be checked until they exist.

**⚠️ CRITICAL**: No user story work can be verified until this phase is complete.

- [X] T002 Write `hybrid-compute/card.json` with exactly the keys `name` (`hybrid-compute`) and `description` (one or two plain present-tense sentences for people browsing, in the style of the other cards)
- [X] T003 Write the frontmatter of `hybrid-compute/SKILL.md`: `name: hybrid-compute`, and a `description` under 1024 characters that satisfies FR-009 — it names both clusters (Engaging/ORCD, subMIT) and the cluster-generic triggers (Slurm, sbatch/squeue over ssh, login node, moving runs to a cluster, syncing results back), so either cluster's name or a cluster-free description of the workflow reaches it

**Checkpoint**: `python scripts/build_index.py --check` reports the new skill's frontmatter and card
as valid.

---

## Phase 3: User Story 1 - One edit improves every cluster (Priority: P1) 🎯 MVP

**Goal**: The cluster-independent workflow exists exactly once, so a workflow improvement is one
edit.

**Independent Test**: Change one sentence of workflow guidance; confirm no other file in the
repository states the same thing. The duplicate-paragraph scan in
[quickstart.md](./quickstart.md) section 1 reports zero.

- [X] T004 [US1] Write the body of `hybrid-compute/SKILL.md`: the two-working-copies diagram, the four standing rules (code flows one way, small results come back through git, big things by rsync, heavy compute only in jobs), and the daily loop (edit → commit → push → pull and verify the code arrived → submit → watch → collect → review before pulling), merged from both retired `SKILL.md` files with no cluster-specific values
- [X] T005 [US1] Write the "Submitting jobs well" section of `hybrid-compute/SKILL.md`, merging both retired versions and keeping every item either carried: the `--export` comma split, switches in output filenames, printing configuration on the first log lines, pilot-first sizing with `seff`, splitting checkpointed runs into an array without rewriting argv, memory from history, cache-provenance checks before comparing a rerun, `--dependency=afterok` plus the exit-non-zero-when-unusable rule, jobs reading code at start not at submit, the log path pattern, thread pinning to `$SLURM_CPUS_PER_TASK`, and `~/.local/bin` missing from the batch `PATH`
- [X] T006 [US1] Write the "Fair share" section of `hybrid-compute/SKILL.md` as cluster-independent guidance: how multifactor priority and usage decay work, treating CPU-hours as a budget, screen-then-expand, dropping decided arms, gating chains on usefulness, cancelling uninformative jobs, packing small runs, right-sizing `-c`/`-t`/`--mem`, and holding jobs when priority is low — with the live-value commands (`scontrol show config`, `sshare -l -u $USER`, `sprio -j`) and a pointer to the profile for site weights and caps
- [X] T007 [US1] Write the "Monitoring" section of `hybrid-compute/SKILL.md`: match by job name not by ID list, treat an ssh failure as a failure, sleep 5–20 minutes, print result lines when jobs disappear, and the useful `squeue`/`sacct` checks
- [X] T008 [US1] Write the "Bookkeeping" section of `hybrid-compute/SKILL.md`: the running notes file, the cluster notes file, one folder per experiment so results can be globbed, and the end-of-phase cleanup (revoke the deploy key, clean up large data)
- [X] T009 [P] [US1] Write `hybrid-compute/scripts/run_modes.sh` as one copy, merged from both retired versions: the `#SBATCH` partition and resource lines as clearly marked placeholders (sbatch directives cannot take shell variables), `REPO_DIR=` as a marked placeholder, the uv cache exports present but commented with a pointer to the cluster profile, and the task line printing script, mode, host, commit and CPU count
- [X] T010 [P] [US1] Write `hybrid-compute/scripts/push_results.sh` as one copy with `cd` to a marked placeholder clone path and a commit trailer that names the cluster generically rather than one site
- [X] T011 [P] [US1] Write `hybrid-compute/scripts/watch_jobs.sh` as one copy, with host and repo as **required** arguments (no Engaging defaults), keeping the name-regex matching, the ssh-failure-is-a-failure behaviour and the argument validation that rejects values able to break out of the remote command
- [X] T012 [P] [US1] Copy `engaging-hybrid-compute/scripts/engaging-connect` and `engaging-hybrid-compute/scripts/duo-askpass` to `hybrid-compute/scripts/engaging/`, unchanged except for any path or comment referring to the old skill folder, preserving their executable bits and their installed file names (`engaging-connect` invokes `duo-askpass` by name)
- [X] T013 [US1] Rework `tests/test_hybrid_compute.py` for the single skill: drop the `SKILLS` tuple, the `ClusterScripts` mixin and the `for _skill in SKILLS` class-generation loop in favour of one `TestCase`; keep the `retargeted()` helper and the PATH stubs; point the `engaging-connect` and `duo-askpass` tests at `hybrid-compute/scripts/engaging/`; update the module docstring

**Checkpoint**: `python -m unittest discover tests` passes against the new scripts, and the
duplicate-paragraph scan over `hybrid-compute/` reports zero.

---

## Phase 4: User Story 2 - Adding a cluster is one file (Priority: P1)

**Goal**: Each cluster's specifics live in one file with a fixed shape, so the next cluster is one
new file.

**Independent Test**: Draft a profile for a third, hypothetical cluster and confirm nothing outside
that file, the trigger description and the generated outputs needs to change.

- [X] T014 [P] [US2] Write `hybrid-compute/clusters/engaging.md` under the four fixed headings (Connecting, Storage, Partitions and caps, Site-specific breakage), carrying every Engaging fact listed in [quickstart.md](./quickstart.md) section 1 from `engaging-hybrid-compute/SKILL.md` and `setup.md`, including the account creation and OnDemand login, the key-does-not-skip-Duo rule with ControlMaster and `ControlPersist`, `ssh -O check` and `BatchMode=yes`, never `ssh -O exit`, one reconnect attempt and the lockout risk, the gated helper called only by bare name, the storage table, the free partition table with per-user caps, the free-tier-only rule with what to do when a job only fits a paid tier, the site priority weights with their live-value commands, and the maintenance-window and pending-reason table
- [X] T015 [P] [US2] Write `hybrid-compute/clusters/submit.md` under the same four headings, carrying every subMIT fact listed in [quickstart.md](./quickstart.md) section 1 from `submit-hybrid-compute/SKILL.md` and `setup.md`, including the portal key upload and access email, key-only login with no Duo, the two key-refusal messages and their different causes, round-robin login nodes and why no background process survives them, login-node load and the ~15-minute line, the storage table with the 10 GB home and the `/ceph` no-many-small-files rule, `UV_CACHE_DIR` and `UV_PYTHON_INSTALL_DIR` under `/work`, the partition table, `tier3` lacking AVX2 and killing JAX including never `--partition=submit,tier3`, always passing `--time`, the partition-often-full reality with `sinfo` and `squeue --me --start`, `seff`, and 1Password auto-lock killing an overnight watcher
- [X] T016 [US2] Add to each profile the pointers it owns: which `#SBATCH` values to put in `hybrid-compute/scripts/run_modes.sh`, which uv cache exports apply, and (for Engaging) that `scripts/engaging/engaging-connect` and `scripts/engaging/duo-askpass` are installed to `~/.local/bin` with an ask rule
- [X] T017 [US2] Verify each profile against FR-003 and the plan's design decision 3 by reading it: four headings present, nothing but site-specific material, and no restatement of shared workflow guidance

**Checkpoint**: Both profiles read as a filled-in form; a third could be written from their shape
alone.

---

## Phase 5: User Story 3 - Working on one cluster loads only that cluster (Priority: P2)

**Goal**: A reader on one cluster reaches everything they need and nothing from the other.

**Independent Test**: Follow the skill for one cluster end to end; every step is reachable and no
other cluster's profile is required reading.

- [X] T018 [US3] Add the cluster pointer to the top of `hybrid-compute/SKILL.md`: first instruction is to read `clusters/<name>.md` for the cluster in use, the known profiles listed by name, and one line on what to do when the cluster has no profile yet (work from the nearest profile and write a new one)
- [X] T019 [US3] Replace every hard-coded site value left in `hybrid-compute/SKILL.md` with a reference to the profile, so that `grep -nE "mit_quicktest|mit_normal|/work/submit|orcd-|tier3|submit\.mit\.edu" hybrid-compute/SKILL.md` is empty
- [X] T020 [US3] Write `hybrid-compute/setup.md` with the cluster-independent one-time setup only: the local SSH key and agent, the private repo with a write-scoped deploy key, the branch ruleset blocking force pushes and deletions, the gating of cluster commands via an ask rule, the repo layout, the `.gitignore`, the project `CLAUDE.md` block, and the end-of-phase cleanup — each step pointing at the profile for the site's own account, storage and connection steps
- [X] T021 [US3] Verify `hybrid-compute/setup.md` carries no site values with the same grep as T019, and that the account/storage/partition steps it drops are present in both profiles

**Checkpoint**: Reading `SKILL.md` plus one profile is sufficient for that cluster; neither names the
other's specifics.

---

## Phase 6: User Story 4 - Deciding between git and rsync (Priority: P2)

**Goal**: The reader can tell which transport any output belongs in, and run the transfer safely.

**Independent Test**: Apply the rule to the six example outputs in
[quickstart.md](./quickstart.md) section 3 and confirm each is assigned without guessing.

- [X] T022 [US4] Write the transport section of `hybrid-compute/SKILL.md`, placed next to the daily loop: the reviewability rule (git for what is worth seeing in a diff before trusting it — code, figures, small arrays, result tables, notes; rsync for what would only ever be looked at whole — raw snapshots, caches, checkpoints, Slurm logs), with examples on both sides, and the explicit statement that the review-before-pull check on cluster commits is why small results go through git at all
- [X] T023 [US4] Add to the same section how to run a large transfer safely: the exclusions to pass, and the warning never to point a `--delete` sync at the cluster-only `slurm/` folder or it is wiped

**Checkpoint**: Each of the six example outputs lands on one side of the rule, with the reason
stated.

---

## Phase 7: User Story 5 - Squashing accumulated result commits (Priority: P3)

**Goal**: The accumulated `results:` commits can be compacted at a phase boundary without breaking
either working copy, with the branch-protection conflict named.

**Independent Test**: Walk the procedure on a scratch repository with a protected branch (the
rehearsal in [quickstart.md](./quickstart.md) section 3) and confirm every step is stated in a
workable order.

- [X] T024 [US5] Write the squash procedure in the Bookkeeping section of `hybrid-compute/SKILL.md`, next to the end-of-phase cleanup: name the conflict with the branch ruleset that `setup.md` deliberately adds, then the steps in order — relax the ruleset, soft-reset to the phase base and commit once, push with `--force-with-lease`, restore the ruleset, `git gc --prune=now` locally, `git reset --hard origin/main` in the cluster clone
- [X] T025 [US5] Add the procedure's precondition and triggers: squash only when nothing is in flight (no queued or running jobs, no unpushed commits in the cluster clone), at a phase boundary, with an earlier size trigger when the repository has grown heavy before a phase closes
- [X] T026 [US5] Mark the ruleset changes and the force push in that procedure as steps the author performs, not the agent, in the same **(you)** style `setup.md` uses, and state that the cluster-clone reset is destructive so the precondition is checked first

**Checkpoint**: The procedure can be followed start to finish from the skill alone, with every
irreversible step attributed to the author.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Retire the old skills, refresh the generated outputs, and run the full verification.
T028 gates T030.

- [X] T027 Check `hybrid-compute/SKILL.md` against the 500-line soft limit `skillreg.SKILL_MD_LINES` warns at, and the plan's budget (shared workflow under about 200 lines, each profile under about 80); move detail into a profile or trim rather than crossing it
- [X] T028 Compare both retired skills fact by fact against the new tree per [quickstart.md](./quickstart.md) section 1, walking `engaging-hybrid-compute/SKILL.md`, `engaging-hybrid-compute/setup.md`, `submit-hybrid-compute/SKILL.md` and `submit-hybrid-compute/setup.md`, and record any fact that has no home yet — then give it one. **This task gates T030.**
- [X] T029 Run the duplicate-paragraph scan from [quickstart.md](./quickstart.md) section 1 over `hybrid-compute/` and resolve anything it reports
- [X] T030 Delete `engaging-hybrid-compute/` and `submit-hybrid-compute/` entirely, only after T028 is complete
- [X] T031 Run `python scripts/build_index.py` and commit the regenerated `index.json`, `.claude-plugin/marketplace.json` and README sections, confirming they list `hybrid-compute` and neither retired name
- [X] T032 Confirm no stale references remain: `grep -rn "engaging-hybrid-compute\|submit-hybrid-compute" . --exclude-dir=.git --exclude-dir=.claude --exclude-dir=specs` is empty (matches under `specs/` are history and stay)
- [X] T033 Run the mechanical checks from [quickstart.md](./quickstart.md) section 4: `python -m unittest discover tests`, `python scripts/build_index.py --check --remote`, `claude plugin validate .`, `python scripts/personal_check.py`
- [X] T034 Run the install check from [quickstart.md](./quickstart.md) section 5: build the zips and confirm `hybrid-compute.zip` contains `SKILL.md`, `setup.md`, both `clusters/*.md` and all five scripts, and does not contain `card.json`
- [X] T035 Walk [quickstart.md](./quickstart.md) sections 2 and 3 as a final read-through of the delivered skill

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: needs T001. Blocks verification of every story, because the index and
  plugin checks read `SKILL.md`'s frontmatter and `card.json`.
- **US1 (Phase 3)**: needs Phase 2. It writes the body of `SKILL.md`, so it precedes the other
  `SKILL.md` sections.
- **US2 (Phase 4)**: needs Phase 2 only. Independent of US1 — different files — so it can run
  alongside Phase 3.
- **US3 (Phase 5)**: needs US1 (T019 edits what T004–T008 wrote) and US2 (T021 checks the profiles
  carry what `setup.md` drops).
- **US4 (Phase 6)**: needs US1's daily loop (T004), which its section sits next to.
- **US5 (Phase 7)**: needs US1's Bookkeeping section (T008), which its procedure joins.
- **Polish (Phase 8)**: needs every story. Within it, T028 gates T030, and T030 gates T031/T032.

### Within Phase 3

T004–T008 all edit `hybrid-compute/SKILL.md` and are therefore sequential. T009–T012 are separate
script files and are parallel with each other and with the prose. T013 needs T009–T012.

### Parallel Opportunities

- T009, T010, T011, T012 — four separate script files.
- T014, T015 — the two profiles, separate files.
- Phase 3 and Phase 4 as whole phases: `SKILL.md`/`scripts/` versus `clusters/`, no shared file.
- Phase 6 and Phase 7 both edit `SKILL.md` and must not run at the same time.

## Parallel Example: Phase 3 scripts

```bash
Task: "Write hybrid-compute/scripts/run_modes.sh as one parameterised copy"
Task: "Write hybrid-compute/scripts/push_results.sh as one parameterised copy"
Task: "Write hybrid-compute/scripts/watch_jobs.sh with host and repo required"
Task: "Copy the two Engaging helpers to hybrid-compute/scripts/engaging/"
```

## Implementation Strategy

### MVP (US1)

Phases 1–3. At that point the shared workflow exists once and the scripts are one copy each, with
the tests passing. The old skills are still present and still work, so nothing is lost if the work
stops here — but the skill is not yet usable on a specific cluster, which is why US2 is also P1.

### Incremental delivery

1. Phases 1–2 → the skill exists and validates.
2. Phase 3 → shared workflow stated once; tests pass. **Checkpoint.**
3. Phase 4 → both clusters covered; the skill is usable. **Checkpoint.**
4. Phase 5 → one cluster at a time, setup split. **Checkpoint.**
5. Phases 6–7 → the two new sections, which are the first proof the shape pays off.
6. Phase 8 → retire the old skills, regenerate, verify.

### Notes

- Everything through Phase 7 is additive: the retired folders stay in place and keep working until
  T030. The change is only irreversible from T030 onward, which is why the fact comparison is T028.
- Commit after each task or logical group; squash on merge per the constitution.
- No personal details anywhere: placeholders such as `<kerb>` only, verified by T033.
