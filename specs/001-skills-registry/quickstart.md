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
