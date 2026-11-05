# reveal.js features in Quarto: reference

Tested with **Quarto 1.11.9**, which bundles **reveal.js 5.1.0** (the current reveal.js is
6.0.1, so features added after 5.1 are missing). Every row was exercised in Google Chrome with the
network blocked, from decks rendered with `embed-resources: true` (one self-contained HTML file) unless
noted.

Legend: ✓ works as documented · ◐ works with a caveat or a workaround · ✗ not available · — not relevant to Quarto.

## Summary table

| reveal.js feature (revealjs.com page) | How to write it in Quarto | Status | Offline single file? |
|---|---|---|---|
| Markup | Markdown headings (`##` = slide); raw HTML in `` ```{=html} `` blocks | ✓ | yes |
| Markdown plugin (`data-markdown`, external `.md`) | Not used: Quarto is Pandoc Markdown. Pull in other files with `{{< include file.qmd >}}` | — | yes |
| Background colour | `## Title {background-color="#0b1d3a"}` | ✓ | yes |
| Background gradient | `{background-gradient="linear-gradient(to bottom, #283b95, #17b2c3)"}` | ✓ | yes |
| Background image | `{background-image="img.png" background-size="contain" background-opacity="0.4"}` | ✓ | yes (inlined) |
| Background video | `{background-video="clip.mp4" background-video-loop="true" background-video-muted="true"}` | ✓ | **no**: stays a relative path; ship the file beside the deck |
| Background iframe | `{background-iframe="app.html" background-interactive="true"}` | ✓ | after `inline_apps.py` (as a `blob:` URL); Quarto alone leaves a path |
| Parallax background | YAML `parallax-background-image:`, `parallax-background-size:` | ✓ | **no**: relative path |
| Media: video | `{{< video clip.mp4 width="480" height="270" >}}` (Quarto uses video.js) | ✓ | yes (inlined) |
| Media: audio | raw `<audio controls src="tone.mp3">` | ✓ | yes (inlined) |
| Media: lazy loading | `<img data-src="…">`, `<iframe data-src="…">` | ✓ | yes (inlined) |
| Media: inline iframe | `<iframe src="app.html">` | ✓ | yes (inlined as a `data:` URL) |
| Lightbox (reveal.js 5.2+ `data-preview-image`) | — | ✗ (not in 5.1) | — |
| Lightbox, Quarto's own (GLightbox) | YAML `lightbox: true`; image `![](img.png){.lightbox}` | ✓ | yes |
| Preview links (overlay iframe) | `[text](https://…){preview-link="true"}` or YAML `preview-links: true` | ◐ only `http`/`www` URLs; local files navigate away. Workaround below | n/a (needs the web) |
| Code highlighting | Pandoc highlighting (reveal's highlight plugin is not used) | ✓ | yes |
| Code line stepping | ```` ```{.python code-line-numbers="\|1\|2-3"} ```` | ✓ | yes |
| Math | MathJax; needs the offline setup below | ◐ | yes, with setup |
| Fragments (all styles) | `::: {.fragment .fade-up}` … `:::`, or inline `[text]{.fragment .highlight-red}` | ✓ | yes |
| Fragment order | `fragment-index=3` attribute | ✓ | yes |
| Nested fragments | a fragment span inside a fragment div | ✓ | yes |
| Fragments inside equations | `\class{fragment}{…}` in TeX, plus the header script below | ◐ | yes, with setup |
| Links to a slide | `[text](#slide-id)` — **not** `#/slide-id` (Quarto turns that into `#//slide-id`) | ✓ | yes |
| Navigation links (`.navigate-next` etc.) | Put the class on a `<button>`; an `<a href="#">` jumps to the title slide | ◐ | yes |
| Layout helpers | `::: {.r-stack}`, `::: {.r-fit-text}`, `.r-stretch`, `.r-hstack`/`.r-vstack` | ✓ | yes |
| Absolute positioning (Quarto) | `::: {.absolute top="600" left="1000" width="300"}` | ✓ | yes |
| Columns (Quarto) | `:::: {.columns}` / `::: {.column width="50%"}` | ✓ | yes |
| Slide visibility | `## Title {visibility="hidden"}` / `{visibility="uncounted"}` | ✓ | yes |
| Themes | YAML `theme: [moon, custom.scss]`; SCSS variables under `/*-- scss:defaults --*/` | ✓ | yes |
| Transitions | YAML `transition:`, `transition-speed:`, `background-transition:`; per slide `{transition="convex" transition-speed="slow"}` | ✓ | yes |
| Config options | About 80 exposed as kebab-case YAML (list below); the rest via `Reveal.configure()` in a script | ◐ | yes |
| Presentation size | YAML `width:`, `height:`, `margin:`, `min-scale:`, `max-scale:`, `center:` | ✓ | yes |
| Vertical slides | YAML `navigation-mode: vertical`; each `#` heading starts a new column | ✓ | yes |
| Auto-animate | `## Title {auto-animate="true"}` on consecutive slides; match elements with `data-id` | ✓ | yes |
| Auto-slide | YAML `auto-slide: 5000`; per slide `{autoslide="1500"}` | ✓ | yes |
| Speaker notes | `::: {.notes}` … `:::` | ✓ | yes |
| Speaker view | press **S** (current + next slide, notes, timer, clock) | ✓ | yes |
| Scroll view | YAML `scroll-view:` or open the deck with `?view=scroll` | ✓ | yes |
| Slide numbers | YAML `slide-number: c/t` (or `true`, `h.v`, `c`), `show-slide-number: all\|print\|speaker` | ✓ | yes |
| Jump to slide | press **G**, type a number, Enter (numbers count across vertical stacks) | ✓ | yes |
| Touch navigation | on by default (`touch: true`) | ✓ | yes |
| PDF export | open `deck.html?print-pdf` in Chrome, or the `make_pdf.py` script below | ✓ | yes |
| Overview mode | **O** or **Esc** | ✓ | yes |
| Fullscreen | **F** | ✓ | yes |
| Pause / blackout | **B** or **.** | ✓ | yes |
| Keyboard: custom bindings | YAML only takes `keyboard: true/false`; use `Reveal.addKeyBinding()` in a script | ◐ | yes |
| API methods | `Reveal.*` from any `` ```{=html} `` `<script>` block | ✓ | yes |
| Events | `Reveal.on("slidechanged", …)`, `fragmentshown`, `ready`, … | ✓ | yes |
| Presentation state | `Reveal.getState()` / `Reveal.setState()` | ✓ | yes |
| postMessage | commands from a parent page work by default; replies need `Reveal.configure({postMessageEvents: true})` | ◐ | yes |
| Built-in plugins | Notes, Search (**Ctrl+Shift+F**), Zoom (**Alt+click**; **Ctrl+click** on Linux, or set `zoomKey`) are loaded; Highlight and Math are replaced by Quarto | ✓ | yes |
| Creating a plugin | a Quarto extension that contributes `revealjs-plugins`; list it in YAML `revealjs-plugins:` | ✓ | yes |
| Multiplex | YAML `multiplex: true` (also writes `deck-speaker.html`) | ◐ needs a hosted socket.io server | **no** |
| Menu (Quarto) | on by default; **M** or the ☰ button | ✓ | yes |
| Chalkboard (Quarto) | YAML `chalkboard: true`; **C** draws on the slide | ◐ | **no**: refuses `embed-resources`; works as a folder |
| Footer, logo, `.smaller`, `.scrollable` (Quarto) | YAML `footer:`, `logo:`; slide classes `{.smaller}`, `{.scrollable}` | ✓ | yes |
| Initialization, Installation, Upgrading, React | Quarto writes `Reveal.initialize()` for you | — | — |

---

## 1. The offline setup (do this once per folder of decks)

The files below are in this skill's `assets/`.

A default Quarto reveal.js deck is **not** offline-safe, even with `embed-resources: true`:

- It loads MathJax 2 from a CDN through reveal.js's math plugin, even on decks with no math.
- `html-math-method: katex` is not embedded at all: offline, the math shows as raw TeX.
- Each Plotly figure from a Python cell carries its own `<script>` for MathJax 3 from a CDN, which
  Quarto inlines at render time. On a deck with a Plotly figure that MathJax then typesets the whole
  page, which hides the problem above. It is a reduced build that cannot load extensions (so
  `\class{fragment}` breaks all math), and it conflicts with any other MathJax on the page.
- Plotly figures also add an `import` of plotly.js from its CDN unless `plotly-connected: false`.

The fix is to load each library exactly once, from a local copy, and stop the plugins from loading their
own. Folder layout:

```
<deck-folder>/
  _quarto.yml            shared settings for every deck in the folder
  _deck/header.html      loads MathJax + plotly.js once; small fixes (below)
  _deck/setup.qmd        Plotly renderer for decks (Python)
  _vendor/mathjax/tex-svg-full.js   MathJax 3.2.2, full build (from the MathJax repo or npm)
  _vendor/plotly/plotly.min.js      from your Python plotly package: plotly/package_data/plotly.min.js
  apps/                  single-file interactive apps + their print stills
  media/                 video and audio
  make_pdf.py            prints a deck to PDF with the network blocked
  my-talk.qmd
  _output/               rendered decks land here
```

### `_quarto.yml`

See `assets/_quarto.yml` (copy it into the deck folder).

Two things that do **not** work in `_quarto.yml`:

- `jupyter: python3` at project level is ignored; Quarto then picks *some* Python kernel installed on
  the machine. Put `jupyter: python3` in each deck's own header.
- `show-notes: separate-page` puts the notes **on screen during the talk**, not only in the PDF. Turn
  notes on only when printing (`?showNotes=separate-page`, as `make_pdf.py` does).

### `_deck/header.html`

See `assets/_deck/header.html` (copy it into the deck folder). It:

- loads MathJax 3 (full SVG build, with the `html` extension for `\class{fragment}`) and plotly.js
  once, from `_vendor/`; `embed-resources` inlines both;
- defines `.print-only` / `.print-hide` for PDF stills of live content;
- after MathJax finishes, lets reveal.js find fragments inside equations (section 2, Math);
- hands keyboard focus back to the deck after a click into an embedded app.

`_quarto.yml` points `html-math-method`'s `url` at `about:blank`: reveal.js's math plugin always
appends a MathJax `<script>` with that URL, so this stops it loading a second (CDN) copy.

### `_deck/setup.qmd` (for decks with Python Plotly cells)

See `assets/_deck/setup.qmd`. It switches Plotly to a renderer that outputs bare divs: no per-figure plotly.js, no CDN MathJax tag.

### A deck

````markdown
---
title: "My talk"
jupyter: python3
resources:
  - media/         # only for background-video / parallax files (apps: inline_apps.py)
---

{{< include _deck/setup.qmd >}}

## First slide
````

Render and print:

```bash
quarto render                              # every deck in the folder -> _output/
python make_pdf.py _output/my-talk.html    # -> _output/my-talk.pdf
```

### `make_pdf.py`

See `assets/make_pdf.py` (copy it into the deck folder).

Chrome's own `--headless --print-to-pdf` gives a blank page: it does not wait for reveal.js's print
layout. The PDF route is reveal.js's native one (`?print-pdf`); the script only automates the print
dialog's settings (page size, no margins, backgrounds).

---

## 2. Content

### Markup and raw HTML

`##` headings start slides (`#` headings start sections; with `navigation-mode: vertical` they start
columns). Anything Markdown cannot say goes in a raw block, which passes through untouched:

````markdown
```{=html}
<p class="note" style="color:#b03a2e">Raw HTML.</p>
<script>/* runs in the deck; Reveal is available after load */</script>
```
````

Inline raw HTML (`<audio …>`, `<button …>`) also works in normal paragraphs.

### Backgrounds

Slide attributes become reveal.js `data-background-*` attributes:

```markdown
## Dark slide {background-color="#0b1d3a"}
## Gradient {background-gradient="linear-gradient(to bottom, #283b95, #17b2c3)"}
## Image {background-image="img.png" background-size="contain" background-opacity="0.4"}
## Video {background-video="media/clip.mp4" background-video-loop="true" background-video-muted="true"}
## {background-iframe="apps/app.html" background-interactive="true"}
```

Parallax is deck-wide: `parallax-background-image:` and `parallax-background-size: "2560px 1440px"`.

Packaging: background **images** are inlined into the HTML. Background **videos** and the
**parallax** image are left as relative paths: list their folders under `resources:` and ship them
next to the deck, or use `{{< video >}}` (inlined). Background **iframes** are also left as paths by
Quarto, but `inline_apps.py` puts them inside the deck afterwards (section 6). It does the same for
`<object data="…">`, which pandoc never inlines.

### Media

```markdown
{{< video media/clip.mp4 width="480" height="270" >}}

<audio controls src="media/tone.mp3"></audio>

<img data-src="big.png">   <!-- loaded only when the slide is near -->
```

The video shortcode gives a video.js player. All three were inlined as `data:` URLs.

### Lightbox and preview links

- reveal.js's own lightbox (`data-preview-image`, `data-preview-video`) arrived in 5.2; Quarto bundles
  5.1, so it does nothing. Use **Quarto's** lightbox: YAML `lightbox: true` and
  `![caption](img.png){.lightbox}` (GLightbox, inlined, works offline).
- `preview-link="true"` (or YAML `preview-links: true`) opens a link in an overlay iframe, but **both
  reveal.js 5.1 and Quarto only do this for links starting with `http` or `www`**. A link to a local
  file navigates the whole page away from the deck. To preview a local file (e.g. a single-file app):

  ```html
  <a href="apps/app.html" onclick="Reveal.showPreview(this.href); return false;">Open the app</a>
  ```

### Code

Quarto uses Pandoc's highlighter, not reveal's highlight plugin. Stepped highlighting:

````markdown
```{.python code-line-numbers="|1|2-3"}
import numpy as np
t = np.linspace(0, 1, 10)
print(t.sum())
```
````

The leading `|` means "first show all lines". For executed cells the Quarto docs give the cell option
`#| code-line-numbers: "|1|2-3"` and `output-location: fragment|slide|column` for cell output (not
tested here).

### Math

With the setup in section 1, `$…$` and `$$…$$` render as MathJax SVG with no network. Do not use
`html-math-method: katex` for offline decks. `mathml` works offline with no setup but looks worse.

Fragments inside an equation:

```markdown
$$
\nabla^2 \Phi = 4 \pi G \rho
\class{fragment}{\quad\Rightarrow\quad \Phi(\mathbf{x}) = -G \int \frac{\rho(\mathbf{x}')}{|\mathbf{x}-\mathbf{x}'|}\, d^3x'}
$$
```

This needs the header script: MathJax typesets after reveal.js has collected the fragments, so reveal.js
must re-scan (`Reveal.sync()`), and MathJax's hidden screen-reader copy of the equation must lose its
`fragment` class or it becomes an extra invisible step. On such slides, steps follow page order.

### Fragments

```markdown
::: {.fragment .fade-up fragment-index=3}
shown third
:::

::: {.fragment .fade-left fragment-index=1}
shown first
:::

[inline]{.fragment .highlight-red}

::: {.fragment}
outer [nested]{.fragment .highlight-blue}
:::

::: {.incremental}
- bullets one at a time
:::
```

All reveal.js fragment styles work (`fade-out`, `fade-up/down/left/right`, `fade-in-then-out`,
`fade-in-then-semi-out`, `semi-fade-out`, `current-visible`, `grow`, `shrink`, `strike`,
`highlight-red/green/blue`, `highlight-current-*`). Put `grow` on an inline span: on a full-width block
it scales off the left edge.

#### Animations that do not jump

- A fragment must not change any height. Reserve its space from the start and fade it in: `fade-in`,
  `fade-up` and friends keep the box; `display`-toggling tricks (`.r-stack` swaps of unequal size,
  content added by script, `fade-in-then-out` on blocks of different heights) push the rest around.
- Appearing text must not reflow its neighbours: give the container a fixed size or use
  `.absolute` placement; put an inline highlight on a span, not a block that changes width.
- A sequence of slides that builds up one figure keeps an **identical base-figure box** (same image
  size, same position, same aspect ratio: export every stage on the same canvas) and only adds
  layers; with `auto-animate` give the base the same `data-id` so it stays put.
- A long build-up gets a skip key: the template's `_deck/skip-steps.html` binds **]** to "last
  step of this slide" (pressed again: next slide). It is listed in the **?** help overlay.
- Check with `check_overflow.py`, which measures every slide with all fragments shown.

### Links

- To a slide: `[text](#slide-id)`. Give the slide an id with `## Title {#slide-id}`. Writing reveal's
  `#/slide-id` form breaks (Quarto rewrites it to `#//slide-id`).
- Relative navigation: `<button class="navigate-next">Next</button>` (also `navigate-prev`,
  `navigate-left/right/up/down`). Do not use `<a href="#" class="navigate-next">`: the `#` href wins
  and jumps to the title slide.

### Layout

```markdown
::: {.r-stack}
![](a.png){.fragment width="400"}

![](b.png){.fragment width="400"}
:::

::: {.r-fit-text}
BIG
:::

::: {.absolute top="600" left="1000" width="200"}
placed exactly
:::

:::: {.columns}
::: {.column width="50%"}
left
:::
::: {.column width="50%"}
right
:::
::::
```

`.r-stretch` fills the remaining height of the slide. Note that reveal.js caps images, videos and
iframes at `max-width: 95%; max-height: 95%`; override with `max-width:none; max-height:none` when you
deliberately size something larger (see section 6).

### Slide visibility

`## Draft {visibility="hidden"}` removes the slide; `{visibility="uncounted"}` keeps it but leaves it out
of the slide count (for backup slides at the end).

---

## 3. Customization

### Themes

```yaml
format:
  revealjs:
    theme: [moon, custom.scss]
```

Built-in: `default`, `simple`, `dark`, `beige`, `blood`, `league`, `moon`, `night`, `serif`, `sky`,
`solarized`. `custom.scss`:

```scss
/*-- scss:defaults --*/
$body-bg: #102030;
$link-color: #ffb000;

/*-- scss:rules --*/
.reveal h2 { letter-spacing: -0.02em; }
```

### Transitions

Deck: `transition: none|fade|slide|convex|concave|zoom`, `transition-speed: default|fast|slow`,
`background-transition:`. Per slide: `{transition="zoom"}`, or separate in/out
`{transition="fade-in slide-out"}`.

### Config options and presentation size

Quarto exposes these reveal.js options as kebab-case YAML (Quarto 1.11.9 schema):

- Layout: `width`, `height`, `margin`, `min-scale`, `max-scale`, `center`, `disable-layout`,
  `auto-stretch`, `code-block-height`
- Navigation: `controls`, `controls-layout`, `controls-tutorial`, `controls-back-arrows`, `progress`,
  `history`, `navigation-mode`, `touch`, `keyboard`, `mouse-wheel`, `loop`, `shuffle`, `hash`,
  `hash-type`, `hash-one-based-index`, `respond-to-hash-changes`, `fragment-in-url`, `jump-to-slide`,
  `auto-slide`, `auto-slide-stoppable`, `auto-slide-method`, `default-timing`, `pause`, `help`,
  `hide-inactive-cursor`, `hide-cursor-time`, `slide-tone`
- Transitions/animation: `transition`, `transition-speed`, `background-transition`, `fragments`,
  `auto-animate`, `auto-animate-easing`, `auto-animate-duration`, `auto-animate-unmatched`,
  `auto-animate-styles`
- Media: `preview-links`, `auto-play-media`, `preload-iframes`, `view-distance`,
  `mobile-view-distance`, `parallax-background-*`
- Print: `pdf-max-pages-per-slide`, `pdf-separate-fragments`, `pdf-page-height-offset`
- Content/tools: `logo`, `footer`, `scrollable`, `smaller`, `output-location`, `overview`, `menu`,
  `chalkboard`, `multiplex`, `scroll-view`

Anything else (e.g. `postMessageEvents`, custom keyboard maps) is set from a script:

````markdown
```{=html}
<script>
  window.addEventListener("load", () => Reveal.configure({ postMessageEvents: true }));
</script>
```
````

Also, any reveal.js option can be overridden from the URL: `deck.html?showNotes=true&controls=false`.

---

## 4. Features

### Vertical slides

```yaml
navigation-mode: vertical
```

Each `# Section` heading starts a column; the `##` slides after it stack below it. With vertical
navigation, `Reveal.slide(h, v)` uses column and row; slide numbers and "jump to slide" count all slides.

### Auto-animate

```markdown
## Step {auto-animate="true"}
::: {data-id="box" style="background:#0072B2; width:100px; height:100px;"}
:::

## Step {auto-animate="true"}
::: {data-id="box" style="background:#E69F00; width:300px; height:150px; border-radius:75px;"}
:::
```

Elements with the same `data-id` (or identical text, like a repeated equation) morph between the two
slides: position, size, colour, radius.

### Auto-slide

`auto-slide: 5000` (ms) for the deck, or `{autoslide="1500"}` on one slide. `auto-slide-stoppable:
true` lets a keypress stop it.

### Speaker notes and the speaker view

```markdown
## Results

::: {.notes}
Say the key number; skip the derivation if short on time.
:::
```

Press **S**: a second window shows the current slide, the next slide, an elapsed timer (click to reset),
the clock and the notes. It works from a single offline HTML file. Notes in the PDF: print with
`?print-pdf&showNotes=separate-page` (notes on their own page after each slide) or `showNotes=true`
(overlay). Don't set `show-notes` in YAML: it shows notes to the audience.

### Scroll view

Open `deck.html?view=scroll` (or YAML `scroll-view: true`) to read the deck as a scrolling page, good
for sharing after the talk. (Tested: the deck switches to scroll view and scrolling moves through the slides.)

### Slide numbers, jump, overview, fullscreen, pause, touch

`slide-number: c/t`; **G** + number + Enter jumps; **O**/**Esc** overview; **F** fullscreen;
**B** or **.** blackout; swipes work on touch screens; **?** lists all shortcuts.

### PDF export

reveal.js's native route: `deck.html?print-pdf` in Chrome, print to PDF, landscape, no margins,
background graphics on. `make_pdf.py` does exactly that with the right page size and the network
blocked. Live content prints blank (WebGL apps in iframes, `<canvas>` animations), so:

```markdown
![](apps/app.png){.print-only .r-stretch}

::: {.print-hide}
<iframe src="apps/app.html" …></iframe>
:::
```

with the `.print-only`/`.print-hide` CSS from the header. For a canvas animation, draw its final state
when `location.search` contains `print-pdf`.

---

## 5. API, events, plugins

### API and events

Any `` ```{=html} `` `<script>` can use the global `Reveal` after the page's `load` event:

```html
<script>
window.addEventListener("load", () => {
  Reveal.on("slidechanged", (e) => { /* e.currentSlide, e.indexh, e.indexv */ });
  Reveal.on("fragmentshown", (e) => { /* e.fragment */ });
});
</script>
```

Pattern for an animation that runs only while its slide is showing:

```js
const sync = () => { running = Reveal.getCurrentSlide().contains(canvas); if (running) step(); };
Reveal.on("slidechanged", sync); Reveal.on("ready", sync);
```

State: `const s = Reveal.getState(); … Reveal.setState(s);`.

### Keyboard

YAML `keyboard:` only accepts `true`/`false`. Custom keys:

```js
Reveal.addKeyBinding({ keyCode: 88, key: "X", description: "Next slide" }, () => Reveal.next());
```

### postMessage

A page that embeds the deck in an `<iframe>` can drive it:

```js
deck.contentWindow.postMessage(JSON.stringify({ method: "slide", args: [1, 3] }), "*");
```

Commands work by default. To get return values (`getIndices`, `isOverview`, …) back as
`{"namespace":"reveal","eventName":"callback","method":…,"result":…}` messages, the deck must run
`Reveal.configure({ postMessageEvents: true })` (no YAML option).

### Plugins

Loaded by Quarto: Notes, Search (**Ctrl+Shift+F**), Zoom (**Alt+click**; **Ctrl+click** on Linux, or set `zoomKey`), plus Quarto's menu (**M**),
line highlight, PDF export and support plugins. reveal.js's Highlight, Markdown and Math plugins are
replaced by Quarto's own handling.

Your own plugin, as a Quarto extension:

```
_extensions/ping/_extension.yml
_extensions/ping/ping.js
```

```yaml
# _extension.yml
title: ping
version: 0.0.1
contributes:
  revealjs-plugins:
    - name: RevealPing     # the global variable ping.js defines
      script: ping.js
```

```js
// ping.js
window.RevealPing = { id: "ping", init: (deck) => { /* deck is the Reveal instance */ } };
```

```yaml
# deck front matter
format:
  revealjs:
    revealjs-plugins: [ping]
```

Third-party plugins are distributed the same way (`quarto add owner/repo`).

### Multiplex and chalkboard

- `multiplex: true` writes `deck.html` (audience) and `deck-speaker.html` (presenter) that sync through a
  hosted socket.io server (`multiplex.up.railway.app` in Quarto 1.11.9). Needs the internet both ends.
- `chalkboard: true`: **C** draws on the slide (tested); the plugin also has a separate blackboard
  (toolbar button).
  Quarto refuses it with `embed-resources: true`; render that deck as a folder (`embed-resources: false`)
  and it works offline.

---

## 6. Embedding interactive apps (single-file HTML builds, e.g. figpress-apps)

Copy the app's single-file HTML into `apps/` and pick one of two embeddings:

**Inline on a slide (inlined into the deck, single file):**

```markdown
## The explorer

![](apps/explorer.png){.print-only .r-stretch}

::: {.r-stretch .print-hide style="position:relative; overflow:hidden;"}
<iframe src="apps/explorer.html" style="position:absolute; top:0; left:0; width:200%; height:200%;
  max-width:none; max-height:none; border:0; transform:scale(0.5); transform-origin:0 0;"></iframe>
:::
```

Laying the iframe out at 2× and scaling it by 0.5 gives the app enough room for its wide layout;
`max-width/max-height: none` undoes reveal.js's 95% cap on iframes.

**Full-slide background:**

```markdown
## {background-iframe="apps/explorer-full.html" background-interactive="true"}

![](apps/explorer-full.png){.print-only .r-stretch}
```

Quarto leaves the background iframe as a path. To make the deck one file again, run
`python inline_apps.py _output/talk.html` from the deck folder after rendering: each app goes into the
deck as base64 in a `<script type="text/plain">`, and a small script, run before reveal.js starts,
turns it into a `blob:` URL and points `data-background-iframe` (and any iframe `src`/`data-src`
with that path) at it. Pointing the background at a `data:` URL instead was tried: the app stayed
blank (a `data:` page gets an opaque origin, which many single-file apps cannot run in). The
end-to-end test checks that the inlined deck, alone in an empty folder, shows its app.

Things to know:

- **Theme**: the apps follow the system's dark mode unless `<html data-theme="light|dark">` is set.
  The deck cannot script into an inlined (`data:` URL) iframe (nor, opened from a file, into a `blob:` one in Chrome), and Chrome does not pass an iframe's CSS
  `color-scheme` into the page, so pin the theme in the copy:
  `perl -pi -e 's|<html lang="en">|<html lang="en" data-theme="light">|' apps/app.html` (works on macOS and Linux).
- **Keyboard**: clicking into an app gives it the keyboard; the header script hands focus back so the
  arrow keys keep changing slides. Dragging is unaffected.
- **Print**: WebGL apps print blank; give each a `.print-only` still (a screenshot of the app).
- **Browser cache**: when re-rendering while the deck is open over HTTP, reload with Shift-Cmd-R.

## 6b. Safari and WebKit

Present on a Mac and you may be in Safari. What broke there, and how the check scripts cover it:

- **CSS path animation**: Safari cannot animate an SVG path's shape from CSS (`d: path(…)` in a
  transition or keyframes); the path just jumps. Keep the CSS for other browsers and add an SVG SMIL
  fallback where it is missing:
  ```js
  if (!CSS.supports("d", 'path("M 0 0")')) {          // Safari
    const a = document.createElementNS("http://www.w3.org/2000/svg", "animate");
    a.setAttribute("attributeName", "d"); a.setAttribute("from", oldD); a.setAttribute("to", newD);
    a.setAttribute("dur", "1.8s"); a.setAttribute("fill", "freeze");
    path.appendChild(a); path.setAttribute("d", newD); a.beginElement();
  }
  ```
  Run it from `Reveal.on("fragmentshown" / "fragmenthidden" / "slidechanged")`.
- **CSS masks** (icons coloured with `background: currentColor` through a mask): Safari did not load a
  mask image from a separate file in a deck opened as a local file. Embed the mask as a `data:` URI in
  the CSS and set both `-webkit-mask` and `mask` (the `paper` shortcode's CSS does this).
- **MathJax**: WebKit fires `load` for the math plugin's `about:blank` script, and the plugin then calls
  MathJax 2's API: a page error. `_deck/header.html` defines a no-op `MathJax.Hub` for it.
- **Checks**: `check_offline.py --webkit` and `check_overflow.py --webkit` run Playwright's WebKit
  (`python -m playwright install webkit`), close to Safari but not Safari: step through the deck in
  Safari once too. The PDF route is Chromium only.

---

## 7. Gotchas, in one list

1. Quarto 1.11.9 ships reveal.js 5.1.0; features from 5.2+ (native lightbox) and 6.0 are missing.
2. A default deck loads MathJax from a CDN even without math; KaTeX is never embedded; Plotly output
   carries its own CDN MathJax. Use the section 1 setup.
3. `show-notes` in YAML shows notes on screen; set it only when printing.
4. `jupyter:` in `_quarto.yml` is ignored; set it per deck.
5. Put decks at the top of the deck folder: the header's `_vendor/` paths are relative to the deck.
6. Slide links: `#id`, not `#/id`. Navigation classes on `<button>`, not `<a href="#">`.
7. Preview links only for `http`/`www`; use `Reveal.showPreview()` for local files.
8. `keyboard:` and `postMessageEvents` need JavaScript, not YAML.
9. Chalkboard and multiplex cannot be single-file / offline.
10. Background video and parallax images are not inlined; list them under `resources:`. Background
    iframes and `<object>` files neither, until `inline_apps.py` runs.
11. reveal.js caps iframes at 95%; MathJax fragments need `Reveal.sync()`.
12. Embedded apps follow system dark mode unless their `<html>` pins `data-theme`.
13. Deck front matter overrides `_quarto.yml`, profiles and `quarto render -M`: keep options a build
    changes (`embed-resources`, output) out of it.
14. Safari: no CSS path animation; CSS masks from files; MathJax 2 call on `about:blank` (section 6b).
15. Fragments that change heights make the slide jump; reserve the space (section 2, Fragments).
