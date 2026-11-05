# Research: quarto-revealjs — lessons from a real talk

Evidence is the talk folder (kept private; its scripts are the working reference) and the
end-to-end test.

## R1. Inlining background-iframe apps

- **Decision**: after rendering, embed each referenced local app as base64 in a
  `<script type="text/plain">`, and a small script, placed before `Reveal.initialize`, builds a
  `blob:` URL and rewrites `data-background-iframe` and iframe `src`/`data-src` to it.
- **Rationale**: Quarto's `embed-resources` leaves `data-background-iframe` as a path. A `data:` URL
  in its place loaded but stayed blank for a real app (opaque origin); `blob:` URLs keep the
  page's origin. Running before reveal.js initialises means no request for the path is ever made.
- **Alternatives**: `data:` URL (blank for apps needing an origin); shipping `apps/` beside the deck
  (not one file); inline `<iframe>` (fine for simple apps, but also a `data:` URL).

## R2. `<object data=…>`

- **Decision**: the same step swaps a local `<object data="file">` for a `data:` URI.
- **Rationale**: pandoc does not inline `<object>` (the talk's title-slide header SVG).

## R3. Share build

- **Decision**: a Quarto profile `share` (`_quarto-share.yml`, output `_share/`), then
  `inline_apps.py --strip-notes`.
- **Rationale**: observed: deck front matter overrides `_quarto.yml`, profiles and `quarto render -M`,
  so the talk had to copy and edit its `.qmd` to change `embed-resources`. Keeping such options out
  of front matter lets a profile change them. Quarto has no option to drop notes, so the step
  removes every `<aside class="notes">`.

## R4. Overflow check

- **Decision**: per slide, all fragments shown, compare each element's box with the `.slides` box,
  dividing by `Reveal.getScale()`; skip notes, everything inside `svg`, `mjx-container` (MathJax
  struts and assistive MathML) and inside clipping containers (only the container is measured);
  skip zero-size and invisible elements.
- **Rationale**: these were the false positives in the talk's first attempts.

## R5. Safari / WebKit

- **Decision**: document CSS `d: path()` animation (unsupported; SMIL `<animate>` fallback behind
  `CSS.supports('d', 'path("M 0 0")')`) and CSS masks (a mask from a separate file did not load from
  a local deck: embed as a `data:` URI and set both `-webkit-mask` and `mask`). The offline and
  overflow checks accept `--webkit`; the PDF stays Chromium (`page.pdf` is Chromium-only).

## R6. Browser launch

- **Decision**: `headless=True` explicitly; try `channel="chrome"`, fall back to Playwright's bundled
  Chromium when Chrome is missing.
- **Rationale**: the author's rule: never a visible browser window; CI and fresh machines may lack
  Chrome.

## R7. Citations

- **Decision**: a shortcode extension `paper` (`url`, `who`, `year`, `title`, `corner`) emitting one
  link "[icon] who (year)", or the icon alone placed top-right; icon as a `data:` CSS mask in the
  extension's CSS, inlined by `embed-resources`. `bibliography.py` writes the same shortcodes from a
  Zotero collection through Zotero's local API, with `a`/`b` suffixes for equal labels and DOI links
  (arXiv DOIs fall back to the item URL).
- **Alternatives**: raw `[[]{.icon}](url){.paper-ref}` Markdown as in the talk (verbose, easy to
  get wrong); Quarto citations with CSL (no icon, no corner form, needs a `.bib` export).
