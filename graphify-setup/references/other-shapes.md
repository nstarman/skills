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
- **No shared commit checks at all.** Use upstream's `.git/hooks/pre-commit` script and say in
  CONTRIBUTING that every clone must install it. Weaker, and the weekly drift job is then the only
  thing keeping the graph honest.
- **Agent guidance under another name.** Step 11 covers it: one copy, others point at it.
- **No documentation site.** Skip the docs page. CONTRIBUTING and the README line are enough.
- **Several packages in one repository.** One graph at the repository root covers all of them;
  `graphify extract .` from the root is right. Do not wire each package.
- **A repository where the graph would be enormous.** Check `graph.json`'s size after step 1. Past
  a few megabytes, narrow `.graphifyignore` further before building the one you commit, rather than
  committing a graph nobody wants to pull.
