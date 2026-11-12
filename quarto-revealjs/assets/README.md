# Title of the talk — venue, date

Quarto reveal.js deck (`presentation.qmd`), set up with the `quarto-revealjs` skill and built with
quartz-deck's `qd` (github.com/nstarman/quartz-deck). Title and abstract: `abstract.md`.

## Layout

```
presentation.qmd   the talk
abstract.md        its title and abstract
Makefile           make, make notes, make refs (all through qd)
_quarto.yml        project options (Quarto reads it only here)
_extensions/       the {{< paper >}} shortcode (Quarto looks for extensions only here)
_talk/             everything else; Quarto skips folders starting with _
  style/           presentation.css, fonts/ (subset woff2)
  html/            skip-steps, notes panel, and {{< include >}} slide pieces
  vendor/          third-party scripts the deck loads itself
  figures/ apps/   figures (WebP, about 2× their size on the slide) and single-file apps
  src/             scripts that made figures and apps
_output/           written by `make`: presentation.html and presentation.pdf
```

## Build

```bash
make        # _output/presentation.html (one offline file, checked) and presentation.pdf
make notes  # _output/presentation-notes.pdf, with the speaker notes
make refs   # rewrite the References list from Zotero (Zotero running; key in the Makefile)
```

`qd export` owns `_output/` and replaces the whole folder. Its JSON reports any problem (network
requests, missing files, raw TeX, anything past the slide edge) and the largest parts of the deck
(`size`). A copy to share without speaker notes: `qd export --strip-notes --out share`.

Open `_output/presentation.html`; press S for the speaker view. While building, add `?preview` to the
address to see the current slide's notes below it (N toggles it).
