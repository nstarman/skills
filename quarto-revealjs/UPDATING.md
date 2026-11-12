# Keeping quarto-revealjs current

**Updating a deck folder made with an older version of the skill**: since the qd update, decks are
built only with quartz-deck's `qd`, and the per-deck tools are gone (`inline_apps.py`, `make_pdf.py`,
`check_offline.py`, `check_overflow.py`, `size_report.py`, `bibliography.py`, `_quarto-share.yml`,
`_deck/header.html`, `_deck/setup.qmd`, `_vendor/`). To convert a folder:
1. Install `qd` at the commit in `versions.json` (SKILL.md, step 0).
2. Copy `assets/Makefile` (set `ZOTERO`) and move the sources into the layout in SKILL.md: decks at
   the root, one per folder; css, html pieces, figures, apps and scripts under `_talk/`. Fix the paths
   in the deck (`apps/x.html` → `_talk/apps/x.html`, and so on).
3. From `_quarto.yml` remove `html-math-method`, the `include-in-header` of the old header and
   `pdf-separate-fragments`; include `_talk/html/skip-steps.html` after the body (it carries the
   WebKit `MathJax.Hub` stand-in the old header had). Delete `_vendor/` and the scripts above, and
   the `{{< include _deck/setup.qmd >}}` line (qd adds its own Plotly renderer).
4. Put `<!-- bibliography:start -->` and `<!-- bibliography:end -->` on the References slide in
   place of `{{< include _bibliography.qmd >}}`, run `make refs`, and delete `_bibliography.qmd`.
5. Give a full-bleed footer band class `overflow-ok`. Run `make`; `qd export` reports what is left.

This skill documents a moving target: Quarto, the reveal.js it bundles, MathJax and plotly.py.
Every claim in `references/quarto-revealjs-guide.md` was observed in a browser against the versions in
`versions.json`. When those move, re-verify; do not edit claims from release notes alone.

## What tells you to update

- **An issue titled "quarto-revealjs: weekly test needs attention (upstream change)"**. The weekly
  run (`.github/workflows/test-quarto-revealjs.yml`, Mondays, latest Quarto release, latest plotly)
  opens it, or comments on the open one, when the test fails *or* when it passes on versions newer
  than `versions.json`. The comment says which. On a failure, the run's log says which step failed,
  and the rendered decks, the PDF and the speaker-view and scroll-view screenshots are attached as
  an artifact. On a pass with newer versions, just bump `versions.json` (step 5).
- **A new reveal.js or Quarto release** with features you want. Run the workflow by hand with a
  specific Quarto (`workflow_dispatch`, input `quarto-version`, e.g. `v1.12.0`, prereleases too).

## How to update

1. **Reproduce locally** with the new versions:
   ```bash
   tests/skills/quarto-revealjs/run.sh /tmp/qr-test     # needs quarto, qd, ffmpeg, python3 with
                                                          # plotly jupyter playwright, and
                                                          # playwright's chromium + webkit
   ```
   The steps: version check; the scaffold in `assets/` (the files SKILL.md lists, none of the removed
   tools, the Makefile targets, the bibliography markers); a new deck from the scaffold alone built
   with `make` and `make notes` (an equation, and a full-bleed `.overflow-ok` band that must not be
   flagged), `qd check`, and WebKit; `qd export` of each fixture deck; exactly one MathJax in
   `demo.html`; the exported decks in WebKit (`offline_check.py --webkit`: network, errors, raw TeX);
   `lessons.html` alone in an empty folder (`lessons_check.py`, Chromium and WebKit: the background
   app and the 3 MB `data-app` app run, the "]" skip key, the `paper` shortcode, an image on two
   slides kept once; `<object>` and SVG `<image href>` inlined, notes kept, apps gzipped, a size
   report); qd's overflow check (only `#too-long` in `lessons.html`, nothing in `demo.html`); the
   shared copy (`--strip-notes`); the PDF (5 pages including the app's still, and a longer notes
   PDF); the feature table (`feature_check.py`, which also checks the demo deck's Plotly figure and
   equation fragment); and the documented gotchas with plain Quarto (`fixture/gotchas/`: KaTeX not
   embedded, chalkboard refusing one file).
2. **Read what changed**:
   - `DIFFERS FROM THE GUIDE: '<check>'` on a check listed in `EXPECTED_FAIL` that passed: a limitation went away (e.g. reveal.js 5.2's
     native lightbox once Quarto bundles it). Update the guide's table row and section, remove the
     workaround from `SKILL.md` if there was one, and drop the name from `EXPECTED_FAIL` in
     `tests/skills/quarto-revealjs/feature_check.py`.
   - The same on an expected-to-fail check that *crashed* (its log line starts `error:`): the
     check no longer tests anything (a fixture element is gone, or the page changed); fix the check.
   - The same on any other check: a regression or a changed syntax. Find the new way in the Quarto and reveal.js
     docs and changelogs, fix the guide (and the fixture deck if the syntax changed), or, if it is
     simply broken upstream, mark it ✗ in the guide, add it to `EXPECTED_FAIL` with a comment, and
     report it upstream.
   - Offline check fails (qd's, or `offline_check.py` in WebKit): something now loads from the
     network. Usually a new CDN default in Quarto's templates (`share/formats/revealjs/`) or in
     plotly.py's notebook renderer. The offline header and Plotly renderer live in quartz-deck
     (`src/export.rs`): fix it there, then move `qd` in `versions.json` to that commit. Adjust
     `assets/_quarto.yml` only for what the deck itself sets.
   - A gotcha step fails: the documented gotcha no longer holds (KaTeX now embedded, chalkboard
     now allowed). Update the guide, SKILL.md and the fixture.
   - Render fails: an option was renamed or removed; check Quarto's schema in
     `share/schema/document-reveal-*.yml` (the guide's option list comes from there).
3. **New reveal.js version bundled** (the version step errors): read the reveal.js changelog from the
   old version to the new one. For each new or changed feature: add a slide to
   `tests/skills/quarto-revealjs/fixture/reveal-features.qmd`, a check to `feature_check.py`, and a
   row to the guide. Re-check the guide's "Gotchas" and the `SKILL.md` gotchas one by one; several
   (preview links only for http, `#/id` rewriting, the 95% iframe cap) are version-specific.
4. **Re-check the workarounds** still need to exist: in qd's header the `about:blank` math URL, the
   `Reveal.sync()` after MathJax and the iframe focus hand-back; in `assets/_talk/html/skip-steps.html`
   the WebKit `MathJax.Hub` stand-in (drop it once qd's header defines one). Remove any that the new
   versions make unnecessary, and say so in the guide.
5. **Record the versions**: update `versions.json` (`verified` date, `quarto`, `revealjs`, `mathjax`,
   `plotly`, `qd`), and the version numbers quoted in the guide's first paragraph and `SKILL.md`
   (including the `cargo install --rev`). The workflow installs `qd` at the commit in `versions.json`.
6. Run the repository checks (`python -m unittest discover tests`,
   `python scripts/build_index.py --check`) and open a pull request; the workflow runs on it.

## MathJax

The skill pins MathJax 3.2.2's `tex-svg-full.js` (`versions.json` → `mathjax`); qd pins the same file
by SHA-256 (`src/assets.rs` in quartz-deck) and downloads it once into its cache. Move to a newer MathJax only after checking that its SVG build is still one file with every
TeX extension and no runtime font or component loading (MathJax 4's is not), and that
`\class{fragment}` still works.
