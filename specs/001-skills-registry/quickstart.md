# Quickstart validation: skills registry

Runnable scenarios that prove the feature end to end. Formats: [contracts/](contracts/).

## Prerequisites

Python ≥ 3.11, `git`, `gh` (logged in), Claude Code CLI ≥ 2.1, a checkout of `nstarman/skills` on
`001-skills-registry`.

## 1. Unit tests and generation

```bash
python -m unittest discover tests
python scripts/build_index.py
python scripts/build_index.py --check
```

Expected: tests pass; `index.json` lists 7 skills (diataxis, engaging-hybrid-compute, figkit,
figkit-upgrade, quax, syw-overleaf-dropbox, unxt; 4 with origin `external`); `--check` exits 0.

## 2. Remote validation and failures (US1, SC-003)

```bash
python scripts/build_index.py --check --remote
```

Expected: exit 0. Then, one at a time in a scratch copy: change `registry/unxt.json`'s `path` to
`skills/nope`, its `ref` to `no-such-tag`, its `name` to `unxtx` (and the file name), or add an
extra key; edit `index.json` by hand; add `registry/diataxis.json`. Each makes the command exit 1
with a line naming the entry and the problem.

## 3. Marketplace (US3, SC-004)

```bash
claude plugin validate .
CLAUDE_CONFIG_DIR=$(mktemp -d) sh -c 'claude plugin marketplace add . && claude plugin install diataxis@nstarman-skills && claude plugin install unxt@nstarman-skills && claude plugin details unxt'
```

Expected: validation passes; both install; `details` shows `Skills (1) unxt`. Your own settings
are untouched (temporary config directory).

## 4. Zips (US4)

```bash
python scripts/release_zips.py /tmp/skillzips && unzip -l /tmp/skillzips/unxt.zip
python scripts/release_zips.py /tmp/skillzips2 --previous /tmp/skillzips/hashes.json
```

Expected: 7 zips, each with one top-level `<name>/` folder containing `SKILL.md` and no `card.json`;
the second run ends with `unchanged` (deterministic zips).

## 5. Bumping tags (US5)

Set `registry/figkit.json`'s `ref` to `v0.1.0`, then `python scripts/bump_refs.py --dry-run`.
Expected: `figkit: v0.1.0 -> v0.2.0` (or the newest release); quax and unxt (branches) are not
listed.

## 6. Website (US2, after merge; separate PR on nstarman.github.io)

```bash
SKILLS_REF=main node scripts/collect-skills.mjs
```

Expected: `config/skills.json` lists 7 skills; `from` is set exactly for the 4 external ones;
/tools/ shows them.

## Results (2026-10-22, macOS, Python 3.14, Claude Code 2.1.259)

- Step 1: 28 unit tests pass; `index.json` lists 7 skills, 4 external; `--check` passes.
- Step 2: `--check --remote` passes against GitHub. Each break in a scratch copy exits 1 naming
  the entry: bad path and bad ref (`unxt: …/SKILL.md not found at <ref>`), wrong name, extra key,
  hand-edited `index.json` (`stale … index.json`), registry name equal to a local folder.
- Step 3: `claude plugin validate .` passes with no warnings; from a temporary config, `diataxis`
  (local), `unxt` (branch) and `figkit` (tag v0.2.0) install with one skill each.
- Step 4: 7 zips, one top-level `<name>/` folder each, no `card.json`; figkit's zip carries its 11
  files; a second build (real sparse clones) prints `unchanged` — deterministic.
- Step 5: with `registry/figkit.json` at `v0.1.0`, `bump_refs.py --dry-run` prints
  `figkit: v0.1.0 -> v0.2.0`; at the real pin it prints nothing; quax/unxt (branches) untouched.
- After merge (2026-10-22): `release.yml` published **v2026.10.22** with 7 zips and `hashes.json`;
  `https://github.com/nstarman/skills/releases/latest/download/unxt.zip` downloads a valid zip.
  Uploading a zip to claude.ai is left to the author (needs their account).
- Step 6: nstarman/nstarman.github.io#409 (merged, deployed) — `collect-skills.mjs` reads
  `index.json`; `config/skills.json` lists 7 skills with `from` on exactly the 4 external ones;
  https://nstarkman.space/tools/ shows them, external ones "from <owner/repo>".
