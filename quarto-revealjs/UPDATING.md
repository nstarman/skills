# Keeping quarto-revealjs current

**Updating a deck folder made with an older version of the skill**: copy `_deck/` together with
`_quarto.yml`. Since the talk-lessons update, `_quarto.yml` includes `_deck/skip-steps.html`, and a
render without that file fails. New assets (`inline_apps.py`, `check_overflow.py`,
`bibliography.py`, `_extensions/paper/`, `_quarto-share.yml`) are optional; copy the ones you use.
Since the inline-apps-over-2-MB update, `inline_apps.py` understands `<iframe data-app="apps/x.html">`:
copy it again and change each inline app's `src` to `data-app` (an app over 2 MB in `src` is blank in
Chrome).
Since the keep-it-small update, `inline_apps.py` gzips the apps and keeps an image used on several slides once, and
`size_report.py` lists what makes a deck large: copy both again and add the new lines of "Check
offline, then print" in `SKILL.md` to the deck's build.

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
   tests/skills/quarto-revealjs/run.sh /tmp/qr-test     # needs quarto, ffmpeg, python3 with
                                                          # plotly jupyter playwright, and
                                                          # playwright's chromium + webkit
   ```
   The steps: version check, set up a deck folder from `assets/` exactly as `SKILL.md` says, render
   the fixture decks, offline check in Chromium and WebKit (network, missing files, errors, raw TeX),
   `inline_apps.py` (the inlined `lessons.html` alone in an empty folder still runs its background
   app, and its 3 MB `data-app` app once that slide is shown; `lessons_check.py` also checks the "]" skip key and the `paper` shortcode), the share build
   (no notes), `check_overflow.py` (only `#too-long` flagged in `lessons.html`, in both engines), PDF (6 pages including
   the app's still), the feature table (`feature_check.py`, which also checks the demo deck's Plotly
   figure and equation fragment), and the documented gotchas (`fixture/gotchas/`: KaTeX not
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
   - Offline check fails: something now loads from the network. Usually a new CDN default in
     Quarto's templates (`share/formats/revealjs/`) or in plotly.py's notebook renderer; adjust
     `assets/` (`_quarto.yml`, `_deck/header.html`, `_deck/setup.qmd`) so it is loaded once, locally.
   - A gotcha step fails: the documented gotcha no longer holds (KaTeX now embedded, chalkboard
     now allowed). Update the guide, SKILL.md and the fixture.
   - Render fails: an option was renamed or removed; check Quarto's schema in
     `share/schema/document-reveal-*.yml` (the guide's option list comes from there).
3. **New reveal.js version bundled** (the version step errors): read the reveal.js changelog from the
   old version to the new one. For each new or changed feature: add a slide to
   `tests/skills/quarto-revealjs/fixture/reveal-features.qmd`, a check to `feature_check.py`, and a
   row to the guide. Re-check the guide's "Gotchas" and the `SKILL.md` gotchas one by one; several
   (preview links only for http, `#/id` rewriting, the 95% iframe cap) are version-specific.
4. **Re-check the workarounds** in `assets/_deck/header.html` still need to exist: the `about:blank`
   math URL, the `Reveal.sync()` after MathJax, the iframe focus hand-back. Remove any that the new
   versions make unnecessary, and say so in the guide.
5. **Record the versions**: update `versions.json` (`verified` date, `quarto`, `revealjs`, `mathjax`,
   `plotly`), and the version numbers quoted in the guide's first paragraph and `SKILL.md`.
6. Run the repository checks (`python -m unittest discover tests`,
   `python scripts/build_index.py --check`) and open a pull request; the workflow runs on it.

## MathJax

The skill pins MathJax 3.2.2's `tex-svg-full.js` (`versions.json` → `mathjax`; the test downloads that
version). Move to a newer MathJax only after checking that its SVG build is still one file with every
TeX extension and no runtime font or component loading (MathJax 4's is not), and that
`\class{fragment}` still works.
