---
name: quarto-revealjs
description: Use whenever someone asks to make a talk, presentation, slide deck or slides (even without naming Quarto), and when making, editing or checking a Quarto reveal.js presentation (`format: revealjs`, `.qmd` slides) that must work offline or be archived as one self-contained HTML file plus a PDF; when a deck shows raw TeX, loads MathJax, KaTeX or plotly.js from a CDN, or breaks without internet; when adding speaker notes, fragments (including inside equations), auto-animate, backgrounds, video, Plotly figures from Python cells, or an interactive single-file HTML app (iframe) to slides; when printing a deck to PDF; or when asked which reveal.js features Quarto supports and how to write them.
---

# Offline, archivable reveal.js decks with Quarto

The goal: a deck that opens in any browser for decades with no network. One `.qmd` source renders to
one self-contained HTML file (`embed-resources: true`), and a PDF printed from that same HTML is the
backup. A default Quarto deck does **not** meet this, even with `embed-resources`; the setup below does.

All reveal.js features and their Quarto syntax, with what was tested: `references/quarto-revealjs-guide.md`.
The author's talk conventions (words, notes, citations, backup slides): `references/style.md`;
read it before writing slides when the deck is the author's (Nathaniel Starkman's) own talk. Template files: `assets/`.

**Never open a visible browser window.** Every script here runs headless (Playwright); to look at a
deck use an embedded browser pane or a headless script, never a Chrome window or `open`.

## Set up a deck folder (once)

0. `git init` the folder on day one (the template's `.gitignore` keeps out `_output/`, `_share/`,
   `.venv/`; add any cloned data repository to it). Commit as you go; delete figures no slide uses
   any more (one talk's folder grew to 319 MB).
1. Copy everything in `assets/` into the folder: `_quarto.yml`, `_quarto-share.yml`, `.gitignore`,
   `_deck/`, `_extensions/` and the scripts.
2. Add the libraries the header loads (they are inlined into every deck at render time):
   - `_vendor/mathjax/tex-svg-full.js`: MathJax **3.2.2**, file `es5/tex-svg-full.js` from the
     `mathjax` npm package or the MathJax GitHub repository at tag `3.2.2`. The full build includes
     every TeX extension, so nothing is fetched later. (MathJax 4's SVG output loads font data at
     runtime; avoid it here.)
   - `_vendor/plotly/plotly.min.js`: copy it from the Python plotly package,
     `<site-packages>/plotly/package_data/plotly.min.js`, so the deck matches the Python version.

   ```bash
   mkdir -p _vendor/mathjax _vendor/plotly
   curl -fsSL -o _vendor/mathjax/tex-svg-full.js https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg-full.js
   cp "$(python -c 'import plotly, pathlib; print(pathlib.Path(plotly.__file__).parent / "package_data/plotly.min.js")')" _vendor/plotly/
   ```

   The header puts plotly.js (about 4.6 MB) into **every** deck. If no deck in the folder has
   Plotly figures, delete its `plotly.min.js` line from `_deck/header.html` and skip the copy.
3. Put the decks at the top of the folder: the header's `_vendor/` paths are relative to the deck.
   Each deck's front matter needs only its own settings, and must not set `embed-resources` or
   output options: front matter overrides `_quarto.yml`, profiles and `quarto render -M`, so a
   build could no longer change them. Put `jupyter: python3` here, not in
   `_quarto.yml`: there it was observed to be ignored, and Quarto picked another installed kernel.
   ````markdown
   ---
   title: "My talk"
   jupyter: python3
   ---

   {{< include _deck/setup.qmd >}}
   ````
   Include `_deck/setup.qmd` only in decks with Python Plotly cells.
4. `quarto render` renders every deck in the folder to `_output/`. The rendered decks are
   self-contained; `_vendor/` and `_deck/` are needed only to render.

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
| Cite a paper | `{{< paper url="https://doi.org/…" who="Name et al." year="2021" title="…" >}}`; top right of a result slide: add `corner="true"` |
| Bibliography slide | `python bibliography.py <collection-key>` → `_bibliography.qmd`; `## References {.bibliography visibility="uncounted"}` then `{{< include _bibliography.qmd >}}` |
| Skip a build-up | press **]** (last step of the slide; again: next slide), from `_deck/skip-steps.html` |

The table escapes `|` as `\|`; in a deck write `code-line-numbers="|1|2-3"`.

Fragments must not change any heights: reserve the space and fade in; slides that build up one
figure keep an identical base-figure box and only add layers (guide, "Animations that do not jump").
`bibliography.py` reads the Zotero app's local API (enable it in Zotero's Advanced settings).

Everything else (themes, auto-slide, scroll view, keyboard, events, postMessage, plugins,
chalkboard, multiplex): `references/quarto-revealjs-guide.md`.

## Embed an interactive app (single-file HTML, e.g. a figpress-apps build)

Copy the app's single-file HTML into `apps/`. Inline on a slide (inlined into the deck by
`inline_apps.py`, so still one file):

```markdown
## The explorer

![](apps/explorer.png){.print-only .r-stretch}

::: {.r-stretch .print-hide style="position:relative; overflow:hidden;"}
<iframe data-app="apps/explorer.html" title="explorer" style="position:absolute; top:0; left:0; width:200%; height:200%;
  max-width:none; max-height:none; border:0; transform:scale(0.5); transform-origin:0 0;"></iframe>
:::
```

- `data-app`, not `src`. Pandoc inlines `src` and `data-src` as `data:` URLs, and Chrome loads no
  `data:` URL over 2 MB: a 3 MB and a 9 MB figpress-apps build showed a blank slide
  (`about:blank#blocked`). Pandoc leaves `data-app` alone; `python inline_apps.py _output/talk.html`
  puts the app in the deck and gives the iframe a `blob:` URL as its `data-src`, so reveal.js loads
  the app when its slide is shown and unloads it when you leave (it starts fresh on each visit).
  Loading it only when shown also stopped an app from throwing a page error while its slide was
  hidden at zero size. Until `inline_apps.py` runs, the slide is empty.
- 2× size scaled by 0.5 gives the app room for its wide layout; `max-width/max-height: none`
  undoes reveal.js's 95% cap on iframes.
- Full slide instead: `## {background-iframe="apps/explorer.html" background-interactive="true"}`.
  Quarto leaves a background iframe as a path; `inline_apps.py` (from the deck folder, or
  `--root <folder>`) puts that app inside the deck too and serves it from a `blob:` URL at load. A
  `data:` URL is not enough: in the talk this came from, a real app stayed blank there (opaque origin;
  observed, not reproduced by the test, whose stand-in app runs either way). The same step swaps
  `<object data="file">`, which pandoc never inlines, for a `data:` URI.
- Match the deck's theme: an app that follows system dark mode must be pinned in its copy, e.g.
  `<html lang="en" data-theme="light">`. The deck cannot script into an inlined iframe (`data:`, or
  from a file a `blob:` one in Chrome), and Chrome does not pass an iframe's CSS `color-scheme` into
  the page.
- A live app does not make it into the PDF: reveal's print view never loads a `data-app` iframe,
  and a background iframe printed blank (observed by hand with `make_pdf.py`). Give each app a
  `.print-only` still (a screenshot of it).
- A click into the app takes the keyboard; the header script gives it back so arrow keys still
  change slides.

## Check offline, then print

The scripts need `pip install playwright` and Google Chrome or Playwright's own browsers
(`python -m playwright install chromium webkit`). They run headless and block the network.

```bash
python inline_apps.py _output/my-talk.html    # data-app and background-iframe apps, <object> files inside
python check_offline.py _output/*.html        # network requests, missing files, errors, raw TeX
python check_overflow.py _output/*.html       # anything past the slide edge, in slide coordinates
python check_offline.py --webkit _output/*.html && python check_overflow.py --webkit _output/*.html
python make_pdf.py _output/my-talk.html       # -> _output/my-talk.pdf, notes on their own pages
```

`check_overflow.py` measures each slide with all fragments shown and names each element outside
the slide box with its position; it ignores notes, SVG internals, MathJax internals (struts,
assistive MathML) and content inside a clipping container. `--webkit` is Safari's engine; CSS path
animation and file-loaded CSS masks failed in Safari during a talk (guide, "Safari and WebKit").

A deck passes when it makes **no** network requests, misses no local file (a background video or
background-iframe app not shipped beside it), has no page errors and no raw TeX. "It rendered" is
not evidence: on a machine with internet a broken deck looks fine. `check_offline.py` allows the
math plugin's `about:blank` request, which loads nothing by design.
Then step through the deck once in the browser (S for notes, the app slides, fragments), and look at
the PDF: fragment steps are separate pages, live content shows its still.

`make_pdf.py` is reveal.js's own PDF route (`?print-pdf`) automated; Chrome's
`--headless --print-to-pdf` gives a blank page. Do not set `show-notes` in YAML: it shows the notes to
the audience. The script turns them on only for the PDF.

## A shareable copy

```bash
quarto render my-talk.qmd --profile share                    # _quarto-share.yml: output in _share/
python inline_apps.py --strip-notes _share/my-talk.html      # one file, no speaker notes
```

The archive build in `_output/` keeps the notes; the shared copy drops every `<aside class="notes">`.
The profile works only while the deck's front matter leaves `embed-resources` and output options
alone (front matter wins over profiles and `-M`).

## Gotchas

- Quarto 1.11.9 bundles reveal.js **5.1.0**: reveal's own lightbox (5.2+) and 6.x features are absent.
  Check `share/formats/revealjs/reveal/dist/reveal.js` in the Quarto install for the version.
- Preview links (`preview-link="true"`) only work for `http`/`www` URLs; a local file navigates away.
  Use `onclick="Reveal.showPreview(this.href); return false;"`.
- `.navigate-next` and friends: put them on a `<button>`; `<a href="#">` jumps to the title slide.
- YAML `keyboard:` takes only `true`/`false`: custom keys via `Reveal.addKeyBinding()`. postMessage
  replies need `Reveal.configure({postMessageEvents: true})`; no YAML option.
- Chalkboard refuses `embed-resources` (render that deck as a folder); multiplex needs a hosted server.
- Background video and parallax images stay relative paths: ship them. Background iframes too,
  until `inline_apps.py` runs.
- An inline app over 2 MB in `<iframe src>` is blank in Chrome (`data:` URL limit); use `data-app`.
- A fragment `.grow` on a full-width block scales off the left edge; put it on a span.
- Re-rendering while the deck is open over HTTP: reload without cache (Shift-Cmd-R) to see changes
  in background iframes.
