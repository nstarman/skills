---
name: quarto-revealjs
description: Use when making, editing or checking a Quarto reveal.js presentation (`format: revealjs`, `.qmd` slides) that must work offline or be archived as one self-contained HTML file plus a PDF; when a deck shows raw TeX, loads MathJax, KaTeX or plotly.js from a CDN, or breaks without internet; when adding speaker notes, fragments (including inside equations), auto-animate, backgrounds, video, Plotly figures from Python cells, or an interactive single-file HTML app (iframe) to slides; when printing a deck to PDF; or when asked which reveal.js features Quarto supports and how to write them.
---

# Offline, archivable reveal.js decks with Quarto

The goal: a deck that opens in any browser for decades with no network. One `.qmd` source renders to
one self-contained HTML file (`embed-resources: true`), and a PDF printed from that same HTML is the
backup. A default Quarto deck does **not** meet this, even with `embed-resources`; the setup below does.

All reveal.js features and their Quarto syntax, with what was tested: `references/quarto-revealjs-guide.md`.
Template files: `assets/`.

## Set up a deck folder (once)

1. Copy `assets/_quarto.yml`, `assets/_deck/` and the two scripts in `assets/` into the folder.
2. Add the libraries the header loads (they are inlined into every deck at render time):
   - `_vendor/mathjax/tex-svg-full.js`: MathJax **3.2.2**, file `es5/tex-svg-full.js` from the
     `mathjax` npm package or the MathJax GitHub repository at tag `3.2.2`. The full build includes
     every TeX extension, so nothing is fetched later. (MathJax 4's SVG output loads font data at
     runtime; avoid it here.)
   - `_vendor/plotly/plotly.min.js`: copy it from the Python plotly package,
     `<site-packages>/plotly/package_data/plotly.min.js`, so the deck matches the Python version.
3. Each deck's front matter needs only its own settings; `jupyter: python3` must be here, not in
   `_quarto.yml` (Quarto ignores it there and picks some other installed kernel):
   ````markdown
   ---
   title: "My talk"
   jupyter: python3
   ---

   {{< include _deck/setup.qmd >}}
   ````
   Include `_deck/setup.qmd` only in decks with Python Plotly cells.
4. `quarto render` renders every deck in the folder to `_output/`. Keep `_vendor/` out of the output
   folder: next to a deck, reveal.js's math plugin finds it and loads MathJax twice.

Why each piece exists (all observed, not theoretical):

- reveal.js's math plugin always appends a MathJax `<script>`; by default from a CDN, even on decks
  without math. `_quarto.yml` points it at `about:blank`, and the header loads MathJax itself.
- `html-math-method: katex` is never embedded: offline the math is raw TeX.
- Every Plotly figure from plotly.py carries its own CDN MathJax `<script>` (a reduced build that
  cannot load extensions) and, in connected mode, an `import` of plotly.js from its CDN. Quarto inlines
  the first at render time, so a deck *with* a Plotly figure shows math that a deck *without* one
  does not. `_deck/setup.qmd` replaces the renderer with one that emits bare divs.

## Write slides

| Want | Write |
|---|---|
| Slide / section | `## Title {#id}` / `# Section` (with `navigation-mode: vertical`, sections become columns) |
| Speaker notes | `::: {.notes}` … `:::`; press **S** for the speaker view (works offline) |
| Step-by-step | `::: {.fragment .fade-up}`, `[word]{.fragment .highlight-red}`, `fragment-index=2`, `::: {.incremental}` |
| Step inside an equation | `\class{fragment}{…}` in TeX (needs the header script) |
| Code walk-through | ```` ```{.python code-line-numbers="\|1\|2-3"} ```` |
| Morph between slides | `{auto-animate="true"}` on both slides; same `data-id` on the element |
| Transition | YAML `transition: slide`; per slide `{transition="zoom"}` |
| Background | `{background-color=…}`, `background-gradient`, `background-image`, `background-video`, `background-iframe` |
| Layout | `.r-stack`, `.r-fit-text`, `.r-stretch`, `::: {.absolute top=… left=…}`, `:::: {.columns}` |
| Video / image zoom | `{{< video clip.mp4 >}}`; YAML `lightbox: true` + `![](img.png){.lightbox}` |
| Link to a slide | `[text](#id)`, **not** `#/id` (Quarto rewrites it to `#//id`) |
| Backup slides | `{visibility="uncounted"}`; drafts `{visibility="hidden"}` |
| JavaScript | a ```` ```{=html} ```` block with `<script>`; use `Reveal` after `window` `load` |

Everything else (themes, auto-slide, scroll view, keyboard, events, postMessage, plugins,
chalkboard, multiplex): `references/quarto-revealjs-guide.md`.

## Embed an interactive app (single-file HTML, e.g. a figpress-apps build)

Copy the app's single-file HTML into `apps/`. Inline on a slide (inlined into the deck, so still one
file):

```markdown
## The explorer

![](apps/explorer.png){.print-only .r-stretch}

::: {.r-stretch .print-hide style="position:relative; overflow:hidden;"}
<iframe src="apps/explorer.html" style="position:absolute; top:0; left:0; width:200%; height:200%;
  max-width:none; max-height:none; border:0; transform:scale(0.5); transform-origin:0 0;"></iframe>
:::
```

- 2× size scaled by 0.5 gives the app room for its wide layout; `max-width/max-height: none`
  undoes reveal.js's 95% cap on iframes.
- Full slide instead: `## {background-iframe="apps/explorer.html" background-interactive="true"}`.
  Background iframes are **not** inlined: list `apps/` under `resources:` and ship it beside the deck.
- Match the deck's theme: an app that follows system dark mode must be pinned in its copy, e.g.
  `<html lang="en" data-theme="light">`. The deck cannot script into an inlined (`data:`) iframe, and
  Chrome does not pass an iframe's CSS `color-scheme` into the page.
- WebGL and canvas content prints blank: give each app a `.print-only` still (a screenshot of it).
- A click into the app takes the keyboard; the header script gives it back so arrow keys still
  change slides.

## Check offline, then print

Both scripts need `pip install playwright` and Google Chrome, and block the network while they run.

```bash
python check_offline.py _output/*.html    # lists any request that tried to leave the machine
python make_pdf.py _output/my-talk.html   # -> _output/my-talk.pdf, notes on their own pages
```

A deck passes when it makes **no** network requests, has no page errors and no raw TeX. "It
rendered" is not evidence: on a machine with internet a broken deck looks fine.
`check_offline.py` ignores one expected console message (the math plugin's `about:blank` load).
Then step through the deck once in the browser (S for notes, the app slides, fragments), and look at
the PDF: fragment steps are separate pages, live content shows its still.

`make_pdf.py` is reveal.js's own PDF route (`?print-pdf`) automated; Chrome's
`--headless --print-to-pdf` gives a blank page. Do not set `show-notes` in YAML: it shows the notes to
the audience. The script turns them on only for the PDF.

## Gotchas

- Quarto 1.11.9 bundles reveal.js **5.1.0**: reveal's own lightbox (5.2+) and 6.x features are absent.
  Check `share/formats/revealjs/reveal/dist/reveal.js` in the Quarto install for the version.
- Preview links (`preview-link="true"`) only work for `http`/`www` URLs; a local file navigates away.
  Use `onclick="Reveal.showPreview(this.href); return false;"`.
- `.navigate-next` and friends: put them on a `<button>`; `<a href="#">` jumps to the title slide.
- YAML `keyboard:` takes only `true`/`false`: custom keys via `Reveal.addKeyBinding()`. postMessage
  replies need `Reveal.configure({postMessageEvents: true})`; no YAML option.
- Chalkboard refuses `embed-resources` (render that deck as a folder); multiplex needs a hosted server.
- Background video, background iframe and parallax images stay relative paths: ship them.
- A fragment `.grow` on a full-width block scales off the left edge; put it on a span.
- Re-rendering while the deck is open over HTTP: reload without cache (Shift-Cmd-R) to see changes
  in background iframes.
