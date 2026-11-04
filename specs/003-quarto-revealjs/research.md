# Research: quarto-revealjs

Decisions behind the skill, each with the evidence that settled it. All observations: Quarto
1.11.9 (reveal.js 5.1.0), plotly 7.1.0, Google Chrome, network blocked, 2026-11-03/04.

## R1. Authoring pipeline: Quarto → reveal.js, PDF from the same HTML

- **Decision**: author in Quarto (`format: revealjs`, `embed-resources: true`); print the PDF with
  reveal.js's own print view (`?print-pdf`).
- **Rationale**: reveal.js is the long-lived, widely used HTML slide format; Quarto adds Markdown,
  executed Python cells and visual editors. Printing the HTML gives a PDF identical to the talk.
- **Alternatives**: Slidev and Spectacle (built sites need a server; Node toolchain to re-edit),
  Marp (weak for interactive content), Typst slides via a Quarto extension (a second, separately
  laid-out deck; Plotly needs static images; dropped by the author).

## R2. A default deck is not offline-safe

- **Findings**:
  - reveal.js's math plugin always appends a MathJax `<script>` (CDN by default), even without math.
  - `html-math-method: katex` is not embedded (raw TeX offline).
  - plotly.py's output adds a CDN MathJax `<script>`, inlined by Quarto at render time, which
    typesets the whole page: math looked fine only on decks that also had a Plotly figure.
  - In connected mode plotly.py also `import`s plotly.js from its CDN.
- **Decision**: point the plugin's URL at `about:blank`; load MathJax 3.2.2 `tex-svg-full.js` and
  plotly.js once from `_vendor/` in an `include-in-header` file (inlined by `embed-resources`);
  replace plotly.py's renderer with one that emits bare divs.
- **Alternatives**: MathML (no setup, offline, but visibly worse typesetting); MathJax 4 (its SVG
  output loads font data at runtime).

## R3. Fragments inside equations

- **Finding**: `\class{fragment}` needs MathJax's `html` extension (not in plotly's reduced build),
  and MathJax typesets after reveal.js collected fragments; MathJax's hidden assistive copy adds a
  phantom step.
- **Decision**: full build with `html` enabled; after typesetting, strip `fragment` from the
  assistive copy, reset indices on those slides and call `Reveal.sync()`. Steps follow page order
  on such slides (documented).

## R4. Speaker notes and the PDF

- **Finding**: `show-notes` in YAML shows notes to the audience. Chrome's
  `--headless --print-to-pdf` prints a blank page.
- **Decision**: notes only when printing (`?showNotes=separate-page`); a Playwright helper prints
  with reveal.js's own page size (`prefer_css_page_size`).

## R5. Embedding single-file apps

- **Findings**: an inline `<iframe src>` is inlined as a `data:` URL; `background-iframe`,
  `background-video` and parallax images stay relative paths. reveal.js caps iframes at 95%.
  A click into an iframe takes the keyboard. Apps follow system dark mode; the deck cannot script
  into a `data:` iframe, and Chrome does not pass an iframe's CSS `color-scheme` into the page.
  WebGL/canvas prints blank.
- **Decision**: 2× layout scaled 0.5 with `max-width/height: none`; focus hand-back in the header;
  pin `data-theme` in the app copy; `.print-only` stills.

## R6. Feature support (the guide)

- **Method**: one test deck exercising every revealjs.com feature page, driven by Playwright.
- **Notable results**: reveal.js 5.1 has no native lightbox (5.2+; Quarto's GLightbox works);
  preview links only for `http`/`www` URLs (`Reveal.showPreview()` works for local files);
  `[..](#/id)` is rewritten to `#//id` (use `#id`); `<a href="#" class="navigate-next">` jumps to
  the title (use a button); `keyboard:` is boolean-only in YAML (use `Reveal.addKeyBinding`);
  postMessage replies need `postMessageEvents` (no YAML option); zoom is Ctrl+click on Linux;
  chalkboard refuses `embed-resources`; multiplex needs a hosted server.

## R7. Where the skill lives

- **Decision**: a local skill in nstarman/skills.
- **Rationale**: the knowledge is general Quarto/reveal.js knowledge; the candidate editor repository
  is private and proprietary, and a registry entry must point at a public repository.

## R8. Testing a moving target

- **Decision**: an end-to-end test that builds a deck folder from the skill's assets as `SKILL.md`
  says; weekly against the latest Quarto release; feature results compared with the guide in both
  directions (a limitation that disappears also fails); expected failures must return False, not
  crash; documented gotchas re-checked; a reveal.js version change fails, a Quarto/plotly change
  warns and opens a reminder issue.
- **Audit**: an independent review (two agents, tests and content) found vacuous checks, missing
  assertions, a missing-file blind spot, over-broad workflow permissions and stale text; all fixed
  before merge.
