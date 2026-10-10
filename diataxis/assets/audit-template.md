# Migration map — <project>

<!--
Template for the deliverable produced in Phase 2. Fill in from the scanner output plus a
read of each page. Keep it in the repo (docs/audit/migration-map.md) — it doubles as the
review artifact and, later, as the record of why the structure is what it is.
-->

## Summary

- Pages audited: N
- Clean (correct mode, correct place): N
- Need moves only: N
- Need splitting or extraction: N
- Not practitioner documentation: N
- New pages required: N
- **Gaps found and not filled:** _(list — missing tutorials above all)_

Structural verdict in two or three sentences: what shape the doc set is in now, the single
biggest problem, and what the restructure will change for readers.

## Proposed structure

```
docs/
  index.md
  tutorials/
    index.md
    ...
  how-to/
  reference/
  explanation/
  about/            # non-practitioner material
```

Note anything unusual: a second dimension (product/role/platform), sections that stay flat,
generated reference placement.

## Per-page map

| # | Current path | Words | Dominant mode | Contaminants | Moves | Destination | Redirect | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | `getting-started.md` | 1840 | how-to | explanation §2; reference table §5 | DEMOTE, EXTRACT, DRAIN, RETITLE | `how-to/install.md` | ✅ | §2 → `explanation/architecture.md`; §5 → `reference/configuration.md`. Real tutorial still missing. |
| 2 | `api.md` | 620 | reference | instruction in intro | MOVE, EXTRACT | `reference/api/index.md` | ✅ | Intro paragraph → `how-to/first-request.md` |
| 3 | `faq.md` | 950 | — | mixed | SPLIT | dissolved | ✅ → `explanation/index.md` | 4 entries → how-to, 3 → explanation, 2 → reference |

**Moves vocabulary:** SPLIT · EXTRACT · DRAIN · MOVE · RETITLE · DEMOTE · PROMOTE · LINK ·
MERGE · STUB · DELETE (see SKILL.md).

**Contaminants** column: name the section or heading, not just the mode, so the extraction is
actionable without re-reading.

## New pages required

| Path | Mode | Why it is needed | Source material | Effort |
|---|---|---|---|---|
| `tutorials/first-pipeline.md` | tutorial | No lesson exists anywhere; every entry path assumes competence | Partly extractable from `getting-started.md`; needs new narrative | High — write and user-test |
| `reference/errors.md` | reference | Error strings only appear inline in how-tos | Grep the source for message strings | Medium |

Tutorials are almost always the expensive item. Say so here rather than letting it surface late.

## Redirect map

| Old URL | New URL |
|---|---|
| `/getting-started/` | `/how-to/install/` |
| `/api/` | `/reference/api/` |
| `/faq/` | `/explanation/` |

This table is read directly by `scripts/make_redirect_stubs.py` — keep the `Old URL` and
`New URL` headers so it stays machine-readable, and add a row per moved *anchor* where a split
page sends different anchors to different destinations (`/usage/#pipeline-methods` →
`/reference/api/#pipeline-methods`). Generate the artifacts rather than hand-writing them:

```bash
python <skill-dir>/scripts/make_redirect_stubs.py --map audit/migration-map.md --emit netlify
```

Mechanism: _(rediraffe / sphinx-reredirects / host rules / generated stubs)_
Enforcement: _(what fails CI if a page moves without a redirect)_

For a stack with no redirect support (Zensical), state the chosen mitigation here explicitly.

## Execution order

Increments, each independently publishable:

1. …
2. …
3. …

Order by leverage: entry points first, then the most mixed pages, then missing tutorials, then
the rest. Note which increments are destructive and need sign-off before they run.

## Open questions

Decisions that need the maintainers, not you — audience assumptions, whether a section is worth
keeping, what the product actually recommends where the docs contradict themselves.
