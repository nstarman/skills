---
name: syw-zenodo-cache
description: Use when a showyourwork (SYW) paper caches expensive rules on Zenodo (`cache: True`, `zenodo.yml`) and CI fails with FileNotFoundOnZenodo, a Dependabot, ImgBot or other bot pull request breaks the article build, a force-push or an edit to a cached rule's input invalidates the cache, a cached output must be re-uploaded without recomputing it, the Sandbox cache is published to Zenodo at submission, or a published cache version shows "showyourwork" as its only creator.
---

# Keeping a showyourwork Zenodo cache usable

A cached rule (`cache: True`) is looked up on Zenodo under a **cache key**: Snakemake's provenance
hash of the rule's code and the *content* of every input file, comments included. CI usually
cannot recompute such a rule (hours long, or it needs software CI lacks) and with
`run_cache_rules_on_ci: false` it does not try: any change to any input means
`FileNotFoundOnZenodo` until someone uploads the output under the new key.

## Which `zenodo.yml` entry a build uses

SYW names the branch with `git rev-parse --abbrev-ref HEAD` and reads `cache: <branch>:`.

| Build | Branch name SYW sees | Needs in `zenodo.yml` |
|---|---|---|
| Push to `main` | `main` | `main:` |
| Pull request (detached merge commit) | `HEAD` | `HEAD:` with the same DOIs as `main:` |
| Local build on a feature branch | that branch | nothing, but it then **uploads nothing and restores nothing** |

A build with no entry for its branch does not treat cached rules as cached: on CI it tries to run
them (hours, or a failure on missing software). So a PR build without `HEAD:` never reads the cache.

CI never uploads. Uploads come from local builds on `main` (or a branch that has an entry).

## Keep keys stable

- List as inputs of a cached rule only files that can change its output (its script and modules,
  a parameters file, the conda environment it runs in). A lock file
  (`uv.lock`, `pyproject.toml`) in a shared settings list puts every dependency bump on the
  cache: give cached rules their own, shorter list, and rebuild them by hand after a bump that
  could change the numbers (numpy, jax, ...).
- Bots rewrite inputs: an image optimizer (ImgBot) touching an SVG or PNG that a cached rule
  reads breaks the cache for a few KB. Close such PRs or exclude those paths.
- Comment-only edits and force-pushes that touch an input file change the key too.

## Re-upload after a key change

The build below runs each cached rule, unless SYW's local cache (`.showyourwork/cache/`) already
has its output under the new key (then it prints `Restoring from local cache`). So the rule must
be cheap to rerun locally, for example from checkpoints; an output that truly needs hours is
recomputed once, locally, never on CI.

1. Commit the change and bring it onto a **local `main`** (do not push yet), with a clean tree
   apart from step 2. Tokens: `SANDBOX_TOKEN` (and `ZENODO_TOKEN` for publishing), read inline
   per command and checked non-empty: a timed-out password-manager read returns `""`.
2. If the Snakefile copies a committed copy of a cached output instead of running the rule (a
   "local cache" switch), turn it off for this build: otherwise the rule never runs and nothing
   uploads. Restore the switch afterwards.
3. Name the cached rules' **output paths** as targets:
   `showyourwork build <out-1> <out-2>`. Positional arguments are Snakemake targets.
   `--forcerun <rule>` does not get through SYW (it fails with "No rule to produce <rule>"),
   and deleting outputs is not enough: while `ms.pdf` is newer than everything, Snakemake
   reports "Nothing to be done". Expect `Syncing file with Zenodo Sandbox cache: <out>`.
4. Check the outputs are byte-identical to the previous ones (`diff -r`; a directory output
   gains a `.snakemake_timestamp`, which is fine). A Zenodo `Request error 400` during the sync
   is usually transient: retry once.
5. Run a plain `showyourwork build` so `ms.pdf` and Overleaf get the figures back (a targets
   build does not compile or push).
6. `showyourwork cache publish --branch main` if the paper's cache is public on Zenodo (it
   copies the Sandbox draft to a new production version). Then:
   - `git diff zenodo.yml`: SYW rewrites it (drops comments, may rename `main:` to `HEAD:`).
     Revert with `git checkout zenodo.yml`.
   - Restore the new version's metadata (next section).
7. Push the same commit as a branch (`git switch -c <branch> && git push -u origin <branch>`)
   and open a pull request; its content equals what you uploaded, so the keys match. CI should
   restore from the cache. Squash-merge, reset local `main` to `origin/main`, then rebase the PR
   that failed (`@dependabot rebase`).

## Publishing and metadata

`cache publish` uses the current Sandbox draft of the branch's `sandbox:` entry and makes a new
version under the `zenodo:` concept DOI. It sets the new version's metadata to SYW's defaults: creator "showyourwork", a
generic title. Fix it **after** publishing, on the new version (published versions can be edited). List the
versions with `https://zenodo.org/api/records?q=conceptrecid:<concept id>&all_versions=1`, then,
with `Authorization: Bearer $ZENODO_TOKEN`: `POST
https://zenodo.org/api/deposit/depositions/<id>/actions/edit`, `PUT` the title, creators, description, keywords
and related identifiers copied from the previous version, **keeping the new version's `notes`**
(SYW stores the rule-to-key map there), then `POST .../actions/publish`. Every later
`cache publish` resets it again. Pull requests from bots get no Actions secrets, so they can
read only a published cache, not a Sandbox draft (or add `SANDBOX_TOKEN` as a Dependabot secret).

## Common mistakes

| Mistake | What happens |
|---|---|
| Build on a feature branch to re-upload | Exits 0, uploads nothing |
| Delete outputs instead of naming targets | "Nothing to be done" |
| `--forcerun rule-a rule-b` | "No rule to produce rule-b" |
| Fix metadata before `cache publish` | Publish overwrites it |
| Commit SYW's rewritten `zenodo.yml` | PR builds lose their `HEAD:` entry, or `main:` disappears |
| `run_cache_rules_on_ci: true` to "fix" CI | CI runs the hours-long rule, or fails on missing software |
