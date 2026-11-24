# Quickstart: verifying the graphify-setup skill

Two things need verifying: the skill as a registry entry, and the wiring its runbook produces. The
second is the one that matters, and it cannot be checked by reading.

## 1. The skill as a registry entry

```bash
python scripts/build_index.py                 # regenerate index.json, marketplace.json, README sections
python scripts/build_index.py --check --remote # what CI runs: formats, unique names, limits, freshness
python -m unittest discover tests
claude plugin validate .
python scripts/personal_check.py              # no private details in published content
```

Expected: `build_index.py --check` clean, with no over-500-lines warning for `graphify-setup/SKILL.md`;
`index.json` gains one entry with `schema` still `1`; the README's skill table gains one row.

## 2. The wiring, in a throwaway repository

Do this once, in a scratch clone of any small Python repository, following the runbook as written rather
than from memory. Each step below is a claim in the spec, and each fails visibly.

**Set-up (SC-001)**: run the runbook end to end. It should need no page of graphify's own documentation
open alongside it. Note anything you had to look up — that is a gap in the runbook, not in your memory.

**A fresh clone is useful (SC-002)**: clone the result into a new directory, install the pinned tool, and
ask the graph a question:

```bash
uvx --from graphifyy==<version> graphify query "how does <something> work"
```

Expected: an answer, with no build step first. If it says the graph is missing, the `.gitignore`
negation is wrong.

**A code commit carries a refreshed graph (US1 scenario 2)**: change a function, commit. Expected: the
hook rebuilds, the commit is refused or amended per the repository's normal flow, and the graph lands in
the same commit as the code. Then `git log -1 --stat` shows one line changed in `graphify-out/graph.json`
and `git diff HEAD~1` does not print the graph's contents.

**A commit that shrinks the graph (US4 scenario 1, FR-008)**: delete a module, commit. Expected: the
rebuild refuses, and the repository's own contributor section tells you the override. Apply it, commit.
If you had to search upstream's documentation, the wiring is incomplete.

**Two branches that both changed code (SC-004, FR-009)**: branch twice from the same commit, change
different files on each, commit both, merge one into the other. Expected: no conflict in the graph. Then
confirm the driver was the reason — `git config merge.graphify.driver` is set — and that the documented
recovery is a rebuild, not a hand edit.

**Skipping the hook (US4 scenario 3)**: commit with the documented skip switch set. Expected: it
commits, and the graph is now behind the code.

**Drift is noticed (FR-010)**: with the graph deliberately behind, run the scheduled job by hand.
Expected: it opens a pull request against the default branch rather than pushing to it, and running it
again updates that same pull request instead of opening a second one.

**An agent finds the graph (SC-003)**: in the wired clone, start a fresh agent session with no
instructions beyond the repository and ask a question about the code. Expected: its first move is a
graph query, not a search over files. Then ask it to dispatch a subagent to explore something, and check
the subagent's instructions repeat the rule.

**A human finds the graph (US2 scenario 3)**: read the README as someone who wants to install the
package. Expected: one line about the code graph, pointing elsewhere, and no section selling the tool.

## 3. The migration path

Repeat section 2 against a repository whose graph directory is ignored and built by a named task.
Expected afterwards: the graph tracked, the rest of the directory still ignored, exactly one documented
way to build the graph, the earlier explanation of what the graph is carried over rather than rewritten,
and the large-file check already adjusted in the same change.

## 4. What is not verified here

The runbook's variation section (a different commit-check tool, agent guidance under another name, no
documentation site, several packages in one repository) is checked by reading, not by running: each is a
rule rather than a worked example, and exercising all four would mean four scratch repositories.
