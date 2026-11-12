# Phase 0: Research

Three decisions were taken with the author before the spec was written, and are recorded here with
the alternatives that were rejected. The rest is what the repository's existing tooling already
supports, established by reading it rather than by changing it.

## Decision 1: one skill with per-cluster profiles

**Decision**: Publish one skill, `hybrid-compute`, holding the cluster-independent workflow once,
with one profile file per cluster.

**Rationale**: The author expects to work on many clusters over the years and wants one edit to
improve all of them. The duplication today is about 70% of each entry point, and the per-cluster
remainder — connecting, storage, partitions, site breakage — really is about a page. Adding a cluster
becomes one new file. A reader also loads only the cluster they are on, which is less context than
today's two skills, not more.

**Alternatives considered**:

- *Thin per-cluster skills deferring to a shared one.* Rejected: skills install individually and
  nothing in `index.json` or `.claude-plugin/marketplace.json` expresses a dependency, so a reader
  who installed only `engaging-hybrid-compute` would silently be missing the shared half.
- *A generator that stitches the shared workflow and one profile into standalone per-cluster skill
  folders, with CI failing on drift.* This works, and mirrors how `index.json` is already handled.
  Rejected for now: it adds a stitcher to `scripts/` and a generated skill folder per cluster
  without improving the content. It stays the fallback if separate marketplace cards per cluster
  ever become necessary.
- *Two standalone skills with a shared reference file duplicated into both, plus a check that the
  copies are identical.* Rejected: it still ships N copies and does not scale past a handful.
- *Status quo plus the new sections written twice.* Rejected: it is the problem, doubled.

## Decision 2: squash result commits at phase boundaries on `main`

**Decision**: Keep results on `main`. Squash the accumulated `results:` commits as a deliberate
project-phase-close step: relax the branch ruleset, squash, push with `--force-with-lease`, restore
the ruleset, `git gc --prune=now` locally, and `git reset --hard origin/main` in the cluster clone.
The ruleset changes and the force push are the author's to perform.

**Rationale**: Both retired `setup.md` files tell the author to add a branch ruleset on `main` that
blocks force pushes and deletions, precisely so a stolen cluster deploy key cannot rewrite history.
Squashing is a history rewrite, so the two collide and the collision has to be named rather than
worked around silently. Doing it at a phase boundary costs a handful of manual steps a few times per
project instead of taxing the daily loop, and it happens at the one moment when nothing is in flight
— no queued jobs, no unpushed cluster commits — which is when a force push is safe. Both skills
already have an "End of the project phase" section for it to join.

**Alternatives considered**:

- *Results on their own branch.* `main` stays protected forever and the results branch can be reset
  freely, with no settings change. Rejected: plotting wants code and results in one working tree, so
  the local side would need a second worktree or `git checkout results -- <paths>`, and the
  review-before-pull habit becomes a two-branch one. It makes the daily case worse to make the rare
  case easier.
- *No squashing; keep figures out of git entirely and rsync them.* Rejected: the review-before-pull
  check on cluster commits is the reason small results go through git, and it is the main guard
  against a misused deploy key.
- *Interactive rebase over the whole history.* Rejected as the mechanism; hundreds of commits make
  it error-prone. A soft reset to the phase base plus one commit is the same result in one step.

## Decision 3: retire the old names without stubs

**Decision**: Delete the `engaging-hybrid-compute` and `submit-hybrid-compute` folders. Their
marketplace install commands and release zip URLs stop working.

**Rationale**: The author is the only user. A stub skill per cluster would reintroduce exactly the
per-cluster duplication this change removes, and a registry entry pointing at a folder that no longer
exists fails CI under constitution principle III, as it should.

**Alternatives considered**: a deprecation period with stub skills that only say "install
`hybrid-compute`". Rejected: two more skills to maintain and two more cards for no benefit.

## Finding: no repository tooling has to change

Read from the scripts rather than assumed:

- `skillreg.discover_local` treats any top-level directory outside `NOT_SKILLS` that contains
  `SKILL.md` as a skill, and reads its description from `card.json`. A `clusters/` subfolder is
  invisible to it, so the new layout needs no change.
- `skillreg.validate_offline` checks the name pattern, that `card.json` has exactly `name` and
  `description`, that `SKILL.md`'s frontmatter `name` equals the folder name, and that the
  description is at most `DESCRIPTION_MAX` (1024) characters. It warns above `SKILL_MD_LINES` (500)
  lines, which is the only budget this change has to watch.
- `release_zips.write_zip` collects files with `folder.rglob("*")`, skipping `card.json` and
  `.DS_Store`. Nested `clusters/` and `scripts/engaging/` files are therefore included in the
  claude.ai zip at their relative paths, with the executable bit preserved for the two helpers.
- `build_index.py` regenerates `index.json`, `.claude-plugin/marketplace.json` and the README
  sections between the `skills:table` and `skills:install` markers, so no generated file is edited by
  hand and the README needs no manual change.
- `personal_check.py` walks the whole tree except `.git` and `.claude`, so the new files are covered
  without being registered anywhere.
- `index.json` keeps `schema: 1`: one entry replaces two, and no field changes. Per constitution
  principle V this needs no version bump and no coordination with the website collector.

## Finding: what the existing test file assumes

`tests/test_hybrid_compute.py` parameterises over `SKILLS = ("engaging-hybrid-compute",
"submit-hybrid-compute")`, generating one `TestCase` subclass per skill from a `ClusterScripts`
mixin, and uses a `retargeted()` helper that copies a script with the hard-coded cluster path line
replaced (matching on `REPO_DIR=` or `cd `). The `EngagingConnect` and `DuoAskpass` tests reference
`engaging-hybrid-compute/scripts/` directly.

Consequences for this change:

- The generation loop and the mixin collapse into a single `TestCase` once there is one skill.
- `retargeted()` stays useful, because the shared scripts still carry placeholder lines.
- The two helper tests' paths move to `hybrid-compute/scripts/engaging/`.
- `test_watch_jobs_*` already passes host and repo explicitly, so making those arguments required
  rather than Engaging-defaulted breaks nothing.
