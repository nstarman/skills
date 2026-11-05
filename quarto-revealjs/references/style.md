# Talk conventions of this skill's author

These are the house rules of the person who maintains this skill (Nathaniel Starkman), learned from
their talks. Apply them only when the person you are working for says the deck is their own talk or
asks for these conventions. For anyone else, use what is generally useful (checking citations,
notes after a divider, a backup section) and leave the rest.

## Words on slides

- In slide **body text** write "DM", not "dark matter". **Titles** keep the words as the author
  wrote them.
- A constraint or result slide names its source with the paper icon at the **top right**
  (`{{< paper … corner="true" >}}`), not with the paper's name in the title.
- Slides on a field outside the author's expertise get a **light grey background**
  (`{background-color="#efefef"}`) and their notes start with "I'm not an expert here; this is my
  reading of the literature."
- Backup material goes in a **section at the end** (`# Backup` and `{visibility="uncounted"}` slides),
  after the closing slide, never interleaved.

## Speaker notes

- The notes are the author talking: plain first-person spoken sentences, short, pointing at what is
  on screen ("the orange line", "on the left").
- Not: "X isn't Y. It's Z." reveals, slogan one-liners, stacked fragments, a bolded label opening
  every line.
- Extra detail (numbers, caveats, where a figure came from) goes after a `- - -` divider line, below
  what is said aloud.

```markdown
::: {.notes}
Here's every bound on one plane. The grey region on the left is ruled out by microlensing.

- - -

Plane regenerated from the review's public code (scripts/planes.py). Microlensing bound: survey paper, their Fig. 3.
:::
```

## Citations

- Every paper cited in the talk is in the talk's **Zotero collection**; the bibliography slide is
  generated from it (`bibliography.py`), never typed by hand. Add a paper to the collection when you
  cite it.
- Cite on a slide with the `paper` shortcode: "[icon] Name et al. (year)", linking to the DOI.
- **Check before showing**: every citation, arXiv ID, DOI, figure number or label and physical claim is
  checked against its source (open the paper or its arXiv page) before the slide is shown to the
  author. A plausible-looking arXiv ID is not evidence.

## Deck folder

- `git init` the deck folder on day one and commit as you go.
- Keep `.venv/`, cloned data or code repositories and render output out of it (`.gitignore` in the
  template); record how to recreate them in the deck's README instead.
- Delete unused figures as soon as a slide stops using them; regenerate figures from scripts in the
  folder rather than keeping every version. (One talk's folder reached 319 MB this way.)
