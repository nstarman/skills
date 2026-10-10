# Documentation restructure — summary

<!-- Keep this under a page. The migration map holds the detail; this is what someone reads
     before deciding whether to merge. Two sections are mandatory and are the reason this
     template exists: "Facts I invented or inferred" and "Gaps found and not filled". -->

## What changed

Two or three sentences: the shape it was in, the single biggest problem, and what the reader
gets now that they did not have before.

- Pages before: N · after: M (X moved, Y split, Z written new, W deleted)
- Sections: tutorials N · how-to N · reference N · explanation N · about N

## Key decisions

Only the ones a reviewer might disagree with, one line each with the reason.

- `getting-started.md` was an installation how-to, not a tutorial — demoted to `how-to/install.md`,
  and a real tutorial written from scratch.
- The `advanced/` section was dissolved; difficulty is not a mode, and its three pages belonged
  to three different ones.

## Facts I invented or inferred

**Mandatory. Write "none" only if it is true.**

Everything asserted in the new docs that is not traceable to the source material — invented
config keys, guessed defaults, reconstructed error strings, plausible-looking version matrices.
These are indistinguishable from real facts to every future reader, so they must be listed
somewhere a human will check them. Each is also marked `TODO(verify)` in place.

| Claim | Where | Basis | How to check |
|---|---|---|---|
| `store.connection` is the Snowflake key name | `reference/configuration.md` | Inferred from prose in the old `usage.md` | Grep the source for the config schema |
| Error strings in `reference/errors.md` | that page | Reconstructed from how-to troubleshooting sections | Grep the source for the message literals |

## Things I claimed to verify, and how

Say what you actually ran, with the command. If you did not run something, say that instead — an
unverified claim of verification is worse than no claim. **These claims live here and nowhere
else**: never in a `conf.py`/`zensical.toml` comment or in page prose, because a shipped
"verified against 0.0.56" note is false the moment anything changes and nobody deletes it.

- `python <skill-dir>/scripts/check_links.py docs/` — clean, N files.
- `python <skill-dir>/scripts/check_repo_refs.py . --old-docs ../pristine/docs --new-docs docs/`
  — clean; N references outside docs/ updated (list the files).
- The project's own gate, exactly as CI runs it: `nox -s tests` / `pytest docs/` / `sphinx-build`
  — N examples before, M after, and why if M < N.
- `python <skill-dir>/scripts/docs_inventory.py docs/` over the finished tree — no duplicated
  facts reported.
- `sphinx-build -W -n -b dirhtml` — clean.
- Tutorial `tutorials/first-pipeline.md` — executed end to end on a clean checkout; every
  "expected output" block is real output from that run.
- **Not verified:** the timings quoted in step 7 are illustrative; replace with real numbers.

## Gaps found and not filled

**Mandatory.** Everything you saw and did not fix, including every page you created but did not
write. Each also appears under "Not yet written" on its section landing page.

- **No second tutorial.** One lesson covers the basic pipeline; nothing teaches the streaming API.
- `reference/api/` is generated and thin — several public functions have no docstring.
- Three how-tos are outlines only: `deploy-on-kubernetes.md`, `custom-sources.md`, `upgrade-0.7.md`.

## Contradictions found in the source

Places where the old docs disagreed with themselves and a human has to decide. Do not silently
pick one.

- `api.md` lists `jsonl` as a supported format; `faq.md` does not.

## Links

- Redirect mechanism: _(rediraffe / host 301s / generated stubs)_ — N old URLs mapped, M with
  anchor-level targets.
- Enforcement: _(what fails CI if a page moves without a redirect)_
