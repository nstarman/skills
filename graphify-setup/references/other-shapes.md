# When the repository is not the assumed shape

Read this from step 1 of [SKILL.md](../SKILL.md) if the repository already has a graph built on
demand, and before step 5 if it does not use `prek` / `pre-commit`.

## Migrating a repository that builds the graph on demand

Some repositories ignore all of `graphify-out/` and rebuild it with a named task
(`nox -s graph` or similar). Convert it, do not wire it twice:

1. Replace the `graphify-out/` ignore line with the two lines from step 3, so the graph alone is
   tracked.
2. Work through the runbook from step 1, skipping nothing. Step 5 matters more here than in a fresh
   repository: an established one is the kind that has a large-file check, a formatter and a
   repository-wide lint job waiting.
3. **Keep the explanation that repository already has.** A repository on this older arrangement
   usually documented what the graph is better than a fresh one does; move that prose into the
   CONTRIBUTING section rather than replacing it with the block's wording.
4. Retire the on-demand build task. The hook now builds the graph, the report and the HTML on every
   commit, so a second build path is one more thing to keep pinned — and the two will drift. The
   naming pass is not a reason to keep it: it has no place in a committed graph. Keep the task only
   if it does something else the hook does not, such as a wiki build, and say so in the pull
   request.
5. Drop any instruction to run the build task from the agent rules and the docs.

**Check**: search the repository for the old task name. No hits outside the changelog.

## When the repository is shaped differently

- **A different commit-check tool.** The hook block is for `prek` / `pre-commit` configuration. For
  anything else, keep the four properties: committed rather than per clone, pinned to `<version>`,
  running even when no file matches, and failing rather than staging for you. Then point the drift
  workflow's `grep` at whatever file now holds the pin — it reads the version out of the
  commit-check config by name.
- **No shared commit checks at all.** Do **not** use `.git/hooks/pre-commit`: it is untracked, so
  the hook body is unreviewed and unversioned, and — the part that breaks the rest of the runbook —
  **the pin has nowhere to live**, while step 10's workflow greps the commit-check config for
  `graphifyy==`. Commit the hook as `.githooks/pre-commit` instead and enable it per clone with
  `git config core.hooksPath .githooks`, which goes beside the merge-driver `git config` lines
  CONTRIBUTING already asks every clone to run. The hook body is then tracked, the pin lives in it,
  and the workflow greps that file.

  Four substitutions follow in the blocks: `SKIP=graphify-update` becomes `git commit --no-verify`
  (there are no other hooks to skip); `additional_dependencies` becomes a `uvx --from
  graphifyy==<version>` call in the script; "runs with your other commit checks" becomes "runs if
  you enabled the hook"; and the agent rules' "the pin in the commit-check config" becomes the hook
  path. Two things come free: a raw git hook has no file filter, so `always_run` is moot and a
  deletion-only commit rebuilds; and there is no `SKIP` machinery to explain.

  Introducing a minimal `.pre-commit-config.yaml` just for this hook is the obvious alternative and
  usually the wrong one: `pre-commit install` is per clone too, so a committed config buys nothing
  over a tracked hook script while adding a tool to the dev loop. Which also qualifies step 6's
  "committed, not installed per clone" — that is only true where the repository's setup already runs
  `pre-commit install`.
- **Agent guidance under another name.** Step 11 covers it: one copy, others point at it.
- **No documentation site.** Skip the docs page. CONTRIBUTING and the README line are enough.
- **Several packages in one repository.** One graph at the repository root covers all of them;
  `graphify extract .` from the root is right. Do not wire each package.
- **A repository where the graph would be enormous.** Check `graph.json`'s size after step 1. Past
  a few megabytes, narrow `.graphifyignore` further before building the one you commit, rather than
  committing a graph nobody wants to pull.
