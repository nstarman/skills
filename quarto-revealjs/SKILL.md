---
name: quarto-revealjs
description: Use whenever someone asks to make a talk, presentation, slide deck or slides (even without naming Quarto), and when making, editing or checking a Quarto reveal.js presentation (`format: revealjs`, `.qmd` slides) that must work offline or be archived as one self-contained HTML file plus a PDF; when a deck shows raw TeX, loads MathJax, KaTeX or plotly.js from a CDN, or breaks without internet; when adding speaker notes, fragments (including inside equations), auto-animate, backgrounds, video, Plotly figures from Python cells, or an interactive single-file HTML app (iframe) to slides; when printing a deck to PDF or building one with quartz-deck's `qd`; or when asked which reveal.js features Quarto supports and how to write them.
---

# Offline, archivable reveal.js decks with Quarto

The goal: a deck that opens in any browser for decades with no network. One `.qmd` source becomes
one self-contained HTML file, and a PDF printed from that same HTML is the backup. A default Quarto
deck does **not** meet this, even with `embed-resources`. Build only with quartz-deck's `qd`
(github.com/nstarman/quartz-deck): `qd export` adds the offline setup, inlines the apps, checks the
result and prints the PDF, so the deck folder carries no build scripts or libraries.

All reveal.js features and their Quarto syntax, with what was tested: `references/quarto-revealjs-guide.md`.
The author's talk conventions (words, notes, citations, backup slides): `references/style.md`;
read it before writing slides when the deck is the author's (Nathaniel Starkman's) own talk. Template files: `assets/`.

**Never open a visible browser window.** `qd` and the test scripts run headless; to look at a deck
use an embedded browser pane or a headless script, never a Chrome window or `open`.

## Set up a deck folder (once)

0. Install `qd` once, at the commit in `versions.json`:
   ```bash
   cargo install --locked --git https://github.com/nstarman/quartz-deck --rev 90fec66
   ```
   It finds Google Chrome (or downloads its own with `qd browser --install`) and downloads MathJax
   3.2.2 into its cache on first use.
1. One folder per talk; `git init` it on day one and commit as you go (the template's `.gitignore`
   keeps out `_output/`, `.quarto/`, `.venv/`; add any cloned data repository to it). Delete figures
   no slide uses any more (one talk's folder grew to 319 MB).
2. Copy everything in `assets/` into the folder (dotfiles too: `cp -R assets/. <folder>/`). The layout:
   ```
   presentation.qmd   the talk; qd picks the only .qmd in the folder
   abstract.md        title and abstract (optional; add it when there is one)
   Makefile           make, make notes, make refs
   README.md          fill in the title, venue and anything particular to this talk
   _quarto.yml        project options; Quarto reads it only at the root
   _extensions/       the {{< paper >}} shortcode; Quarto looks for extensions only at the root
   _output/           written by `make`
   _talk/             everything else; Quarto skips folders that start with _
     style/           presentation.css, fonts/ (subset woff2)
     html/            skip-steps, notes panel, chrome scripts, {{< include >}} slide pieces
     vendor/          third-party scripts the deck loads itself (not MathJax or plotly.js)
     figures/ apps/   figures, single-file interactive apps and their print stills
     src/             scripts that made figures and apps
   ```
   Make `figures/`, `apps/`, `src/`, `vendor/` and `style/fonts/` when the first file goes in.
3. Front matter holds only the deck's own settings (title, size, theme, `css:`). It must not set
   `embed-resources` or output options: `qd export` sets those. Put `jupyter: python3` here, not in
   `_quarto.yml`, and only for a deck with Python cells: in `_quarto.yml` it was observed to be ignored,
   and Quarto picked another installed kernel.
4. Do not vendor MathJax or plotly.js, and do not set `html-math-method` in `_quarto.yml`. `qd export`
   adds one local MathJax 3.2.2 (and plotly.js from the Python plotly package when a Python cell
   imports plotly) plus a Plotly renderer with no CDN scripts. A project that sets the math URL to
   `about:blank` tells qd the deck loads MathJax itself, and qd then adds no MathJax at all.

## Build

```bash
make         # qd export --pdf --out _output: _output/presentation.html (checked) and .pdf
make notes   # qd pdf --html _output/presentation.html --notes: presentation-notes.pdf
make refs    # qd bib --zotero KEY: the References list from the Zotero collection (Zotero running)
```

`qd export` owns `_output/` and replaces the whole folder on every run, which is why `make` prints
the PDF in the same run (`make notes` adds its file afterwards). It renders a copy of the deck with
the offline setup, puts apps, `<object>` files and SVG `<image href>` files inside the HTML, copies
background videos and the parallax image beside it, and checks the result in headless Chromium with
the network blocked. Its JSON result has `ok` and `check.problems`:

- errors: network requests (`P_NETWORK`), missing local files, math shown as raw TeX (`P_RAW_TEX`);
  `ok` is false and `_output/` is left as it was;
- warnings: anything outside the slide box with all fragments shown (`P_OVERFLOW`, with its position
  in slide coordinates), and speaker notes visible to the audience.

The overflow check skips notes, SVG and MathJax internals, content inside a clipping container, and
anything inside an element with class `overflow-ok`. A footer band drawn full-bleed on purpose (by a
chrome script in `_talk/html/`) needs that class, or every slide is flagged.

"It rendered" is not evidence: on a machine with internet a broken deck looks fine. After `make`,
step through the deck once in the browser (S for notes, the app slides, fragments), and look at the
PDF: fragment steps are separate pages, live content shows its still. `qd check` (no build) catches
duplicate ids, unsafe constructs and missing files while editing. qd checks in Chromium only; Safari
needs one pass by hand (guide, "Safari and WebKit").

A copy to share without speaker notes: `qd export --strip-notes --out share`.
While building, open `_output/presentation.html?preview` to see each slide's notes in a panel below
it (`_talk/html/notes-below.html`; N toggles it, it hides itself fullscreen and in the speaker view).
Present with S for the speaker view. Do not set `show-notes` in YAML: it shows the notes to the
audience; `qd pdf --notes` turns them on only for the PDF.

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
| References slide | the scaffold's `## References {#bibliography .bibliography visibility="uncounted"}`: `make refs` (`qd bib --zotero KEY`) writes the list between its `<!-- bibliography:start -->` and `<!-- bibliography:end -->` lines |
| Skip a build-up | press **]** (last step of the slide; again: next slide), from `_talk/html/skip-steps.html` |

The table escapes `|` as `\|`; in a deck write `code-line-numbers="|1|2-3"`.

Fragments must not change any heights: reserve the space and fade in; slides that build up one
figure keep an identical base-figure box and only add layers (guide, "Animations that do not jump").
`qd bib` reads the Zotero app's local API (enable it in Zotero's Advanced settings) and changes only
the lines between the markers; set the collection key in the `Makefile` (`ZOTERO = …`).

Everything else (themes, auto-slide, scroll view, keyboard, events, postMessage, plugins,
chalkboard, multiplex): `references/quarto-revealjs-guide.md`.

## Embed an interactive app (single-file HTML, e.g. a figpress-apps build)

Copy the app's single-file HTML into `_talk/apps/`. Inline on a slide (inlined into the deck by
`qd export`, so still one file):

```markdown
## The explorer

![](_talk/apps/explorer.png){.print-only .r-stretch}

::: {.r-stretch .print-hide style="position:relative; overflow:hidden;"}
<iframe data-app="_talk/apps/explorer.html" title="explorer" style="position:absolute; top:0; left:0; width:200%; height:200%;
  max-width:none; max-height:none; border:0; transform:scale(0.5); transform-origin:0 0;"></iframe>
:::
```

- `data-app`, not `src`. Pandoc inlines `src` and `data-src` as `data:` URLs, and Chrome loads no
  `data:` URL over 2 MB: a 3 MB and a 9 MB figpress-apps build showed a blank slide
  (`about:blank#blocked`). Pandoc leaves `data-app` alone; `qd export`
  puts the app in the deck and gives the iframe a `blob:` URL as its `data-src`, so reveal.js loads
  the app when its slide is shown and unloads it when you leave (it starts fresh on each visit).
  Loading it only when shown also stopped an app from throwing a page error while its slide was
  hidden at zero size. In a plain `quarto render` the slide is empty.
- 2× size scaled by 0.5 gives the app room for its wide layout; `max-width/max-height: none`
  undoes reveal.js's 95% cap on iframes.
- Full slide instead: `## {background-iframe="_talk/apps/explorer.html" background-interactive="true"}`.
  Quarto leaves a background iframe as a path; `qd export` puts that app inside the deck too and serves it from a `blob:` URL at load. A
  `data:` URL is not enough: in the talk this came from, a real app stayed blank there (opaque origin;
  observed, not reproduced by the test, whose stand-in app runs either way). The same step swaps
  `<object data="file">`, which pandoc never inlines, for a `data:` URI.
- Match the deck's theme: an app that follows system dark mode must be pinned in its copy, e.g.
  `<html lang="en" data-theme="light">`. The deck cannot script into an inlined iframe (`data:`, or
  from a file a `blob:` one in Chrome), and Chrome does not pass an iframe's CSS `color-scheme` into
  the page.
- A live app does not make it into the PDF: reveal's print view never loads a `data-app` iframe,
  and a background iframe printed blank (observed by hand). Give each app a
  `.print-only` still (a screenshot of it).
- A click into the app takes the keyboard; the header script gives it back so arrow keys still
  change slides.

## Keep it small

One talk's deck was 41.6 MB and its folder 221 MB before these steps, 34.8 MB and 157 MB after.
Do them from the first slide; shrinking a finished deck means redoing every figure.

- Size a raster figure to about twice its size on the slide (no figure shows wider than the deck's
  `width`, 1050 px unless the deck sets it), and save it as WebP:
  `cwebp -q 85 -resize W 0 in.png -o out.webp`. A 3000 px photo shown 1380 px wide was 1 MB; at
  2000 px WebP it was 200 kB.
- Self-host fonts as subset woff2 files in `_talk/style/fonts/`, made with `pyftsubset --flavor=woff2`
  (fonttools and brotli), and load them with `@font-face`. Never `@import` Google Fonts: embedding
  then pulls the full TTF, 520 kB a weight instead of 68 kB.
- Read the size report after each build: `check.size` in `qd export`'s JSON (`--human` to read it)
  lists the largest things embedded in the deck (apps, images, scripts) with the text just before
  each, so you know what to shrink.
- `qd export` gzips each app (the browser unzips it when the deck opens, in a few ms) and keeps an
  image that is on several slides once; `qd pdf` recompresses the PDF's images when ghostscript
  (`gs`) is installed.
- Every app or figure you commit stays in `.git` for good, including each rebuild (one talk's
  `.git` reached about 80 MB). Commit an app when it is final, not after each rebuild.

## Gotchas

- Quarto 1.11.9 bundles reveal.js **5.1.0**: reveal's own lightbox (5.2+) and 6.x features are absent.
  Check `share/formats/revealjs/reveal/dist/reveal.js` in the Quarto install for the version.
- Preview links (`preview-link="true"`) only work for `http`/`www` URLs; a local file navigates away.
  Use `onclick="Reveal.showPreview(this.href); return false;"`.
- `.navigate-next` and friends: put them on a `<button>`; `<a href="#">` jumps to the title slide.
- YAML `keyboard:` takes only `true`/`false`: custom keys via `Reveal.addKeyBinding()`. postMessage
  replies need `Reveal.configure({postMessageEvents: true})`; no YAML option.
- Chalkboard refuses `embed-resources` (render that deck as a folder); multiplex needs a hosted server.
- Background video and parallax images stay relative paths; `qd export` copies them beside the deck.
  Background iframes too, until `qd export` inlines them.
- An inline app over 2 MB in `<iframe src>` is blank in Chrome (`data:` URL limit); use `data-app`.
- A fragment `.grow` on a full-width block scales off the left edge; put it on a span.
- Re-rendering while the deck is open over HTTP: reload without cache (Shift-Cmd-R) to see changes
  in background iframes.
