# Zensical: implementing a Diátaxis restructure

Zensical is the static site generator from the Material for MkDocs team. Details below were
verified against zensical.org, the `zensical/zensical` repository and PyPI in August 2026.
Zensical is young — PyPI classifier `Development Status :: 3 - Alpha`, versioned `0.0.x`,
released roughly weekly — so check anything surprising against the current docs.

**Contents**

- [Read this first: no redirects](#read-this-first-no-redirects)
- [Project shape](#project-shape)
- [Configuration](#configuration)
- [Navigation](#navigation)
- [Section landing pages](#section-landing-pages)
- [Page titles](#page-titles)
- [Front matter](#front-matter)
- [Markdown and content features](#markdown-and-content-features)
- [Link validation](#link-validation)
- [Cross-linking and glossaries](#cross-linking-and-glossaries)
- [API reference](#api-reference)
- [Feature gaps that affect architecture](#feature-gaps-that-affect-architecture)
- [Migrating from MkDocs](#migrating-from-mkdocs)
- [CLI and CI](#cli-and-ci)

---

## Read this first: no redirects

**Zensical has no redirect or alias mechanism.** `mkdocs-redirects` is not supported and there
is no built-in equivalent (tracked as backlog #23). A Diátaxis restructure changes every URL,
so raise this before any files move. The options:

1. **Host-level redirects** — Netlify `_redirects`, Cloudflare rules, nginx/Apache config,
   CloudFront functions. Best outcome: real 301s. Requires control of hosting.
2. **Generated meta-refresh stub pages** at the old paths. Works anywhere, including GitHub
   Pages. Generate them from the migration map — do not hand-write them:

   ```bash
   python <skill-dir>/scripts/make_redirect_stubs.py \
       --map audit/migration-map.md --emit stubs --out redirects/ --url-style dirhtml
   ```

   The stubs preserve the URL fragment and route split-page anchors to different destinations,
   which is the part that goes wrong by hand. Copy the output into `site/` after each build.
3. **Keep URLs stable** — reorganize nav and rewrite content without moving files. This
   preserves links completely and still delivers most of the benefit, since the mode separation
   and the rewrites are where the value is. Consider it seriously for a public doc set with
   significant inbound traffic.

Whichever you choose, say so explicitly in the plan. Silently shipping a restructure on Zensical
means silently breaking every inbound link.

---

## Project shape

```
.
├─ docs/
│  ├─ index.md
│  ├─ tutorials/index.md
│  ├─ how-to/index.md
│  ├─ reference/index.md
│  └─ explanation/index.md
├─ overrides/            # optional theme custom_dir
└─ zensical.toml
```

`docs_dir` defaults to `docs`, `site_dir` to `site`. `docs_dir` cannot be `"."` (a stated
temporary limitation). `zensical new <dir>` scaffolds a project and refuses to overwrite
existing files.

Install with `pip install zensical` or `uv add --dev zensical` (Python ≥3.10). uv symlink mode
is unsupported.

---

## Configuration

`zensical.toml` (preferred) or `mkdocs.yml` / `mkdocs.yaml`. Resolution order is
`zensical.toml` → `mkdocs.yml` → `mkdocs.yaml`. All settings currently live under `[project]`
and sub-scopes; the docs warn that scopes will move as the schema matures, with automatic
refactorings promised.

```toml
[project]
site_name = "Toolkit"
site_url = "https://docs.example.com/"
site_description = "Documentation for Toolkit"
repo_url = "https://github.com/example/toolkit"
edit_uri = "edit/main/docs/"

nav = [
  { "Home" = "index.md" },
  { "Tutorials" = [
    "tutorials/index.md",
    { "Install and first run" = "tutorials/installation.md" },
    { "Your first pipeline" = "tutorials/first-pipeline.md" },
  ] },
  { "How-to guides" = [
    "how-to/index.md",
    { "How to authenticate" = "how-to/authenticate.md" },
  ] },
  { "Reference" = [
    "reference/index.md",
    { "CLI" = "reference/cli.md" },
    { "Configuration" = "reference/configuration.md" },
  ] },
  { "Explanation" = [
    "explanation/index.md",
    { "About the architecture" = "explanation/architecture.md" },
  ] },
]

[project.theme]
language = "en"
features = [
  "navigation.indexes",     # required for section landing pages
  "navigation.sections",
  "navigation.tabs",        # four modes as top-level tabs
  "navigation.path",        # breadcrumbs — helps readers know which mode they are in
  "navigation.top",
  "navigation.footer",
  "content.tabs.link",      # tab choice persists site-wide
  "content.code.copy",
  "content.code.annotate",
  "search.highlight",
]

[project.markdown_extensions]
admonition = {}
attr_list = {}
def_list = {}
md_in_html = {}
toc.permalink = true
pymdownx.details = {}
pymdownx.superfences = {}
pymdownx.tabbed.alternate_style = true
pymdownx.snippets = {}
```

TOML idioms to know: extension options use dotted keys (`pymdownx.highlight.anchor_linenums =
true`), an extension with no options is `name = {}`, and YAML `!!python/name:` tags become plain
strings.

`mkdocs.yml` settings **not** supported: `remote_branch`, `remote_name`, `exclude_docs`,
`draft_docs`, `not_in_nav`, `hooks`.

---

## Navigation

Navigation is generated from the folder structure by default; an explicit `nav` overrides it.
Paths are relative to `docs_dir`. Use an explicit `nav` for a Diátaxis site — mode order is
deliberate (tutorials first, explanation last) and alphabetical folder order will not give it
to you.

```toml
nav = [ "index.md", "about.md" ]                              # titles inferred from content
nav = [ { "Home" = "index.md" } ]                             # explicit title
nav = [ { "About" = [ "about/index.md", "about/team.md" ] } ] # nested section
nav = [ { "GitHub" = "https://github.com/example/toolkit" } ] # unresolvable string = URL
```

Useful theme features for a four-mode site: `navigation.tabs` puts the modes in a top bar,
`navigation.sections` renders them as sidebar groups, `navigation.path` adds breadcrumbs so a
reader arriving from search can see which mode they landed in, and `navigation.prune` helps on
large sites.

`navigation.instant` and instant previews require `site_url`, since they rely on the generated
`sitemap.xml`.

Behaviour for Markdown files present in `docs_dir` but absent from an explicit `nav` is not
documented, and `not_in_nav` is unsupported — verify against your version rather than assuming
MkDocs' build-and-warn behaviour.

---

## Section landing pages

Enable `navigation.indexes` and put the section's `index.md` **first** in its nav array:

```toml
nav = [
  { "How-to guides" = [
    "how-to/index.md",
    { "How to authenticate" = "how-to/authenticate.md" },
    { "How to deploy to Kubernetes" = "how-to/deploy-to-kubernetes.md" },
  ] },
]
```

`README.md` also counts as an index page, but if both `README.md` and `index.md` exist in a
directory the behaviour is currently undefined — pick one.

`navigation.indexes` is **not compatible with `toc.integrate`**.

For the landing page content itself, grids of linked cards work well (Material's card grid
syntax carries over). What matters more than layout is the orienting sentence and the pointer
elsewhere — see `architecture.md`.

---

## Page titles

Precedence, highest first:

1. Title given in `nav`
2. Front matter `title`
3. First `# H1` in the page
4. Base filename

**A known deviation from MkDocs matters during a restructure:** if you set `nav` titles but a
page has no `# H1`, MkDocs uses the nav title as the heading while Zensical uses the *base
filename*. So a file named `authenticate.md` with a nav title of "How to authenticate" and no
H1 renders an `<h1>` of "authenticate". Give every page an explicit `# H1` — which you want
anyway, because the H1 is where the mode signal lives ("How to…"). This area is being
redesigned under ZAP 001.

---

## Front matter

```markdown
---
title: How to authenticate against a private registry
description: Configure credentials for a private package registry.
icon: lucide/key
status: new
tags:
  - authentication
  - registries
---

# How to authenticate against a private registry
```

Recognised keys: `title`, `description`, `icon`, `status` (keyed to `[project.extra.status]`;
built-ins `new` and `deprecated`), `template`, `tags`, `hide` (`navigation`, `toc`, `path`,
`tags`), and `search: {exclude: true}`. Arbitrary keys are available to templates as
`page.meta.*`.

`description` is worth filling in on every page — it becomes the meta description and therefore
the search-result snippet, which is where most readers first judge whether a page is the mode
they need.

---

## Markdown and content features

Python Markdown plus PyMdown Extensions — the same dialect as Material for MkDocs. CommonMark
is explored but not present.

One trap: **Zensical's default extension set differs from MkDocs'** (MkDocs activates only
`meta`, `toc`, `tables`, `fenced_code`). Defaults apply only when you define no
`markdown_extensions` at all — there is no add/remove preset mechanism yet, so the moment you
declare one extension you are declaring all of them. If a migrated project renders oddly, this
is the first thing to check.

Features that carry real weight in a Diátaxis site:

- **Admonitions** for `!!! note` / `!!! tip`, and `pymdownx.details` for collapsible
  `??? note` — good for keeping advanced options out of a how-to's happy path.
- **Content tabs** (`pymdownx.tabbed`) with `content.tabs.link` so a platform choice persists
  site-wide. This is what lets one how-to serve macOS/Linux/Windows instead of three drifting
  copies.
- **Snippets** (`pymdownx.snippets`) to include shared fragments from real files rather than
  transcribing them — the Zensical equivalent of `literalinclude` with sentinels. Use section
  markers, not line ranges.
- **Code annotations** (`content.code.annotate`) — numbered markers inside a code block that
  expand to prose. Excellent in tutorials, where they let you narrate a snippet without breaking
  it up; avoid in reference, where they read as instruction.
- **Definition lists** (`def_list`) for reference entries.
- **Tables**, **footnotes**, **abbreviations** (`abbr`, with a shared glossary file included via
  snippets — a good substitute for Sphinx's `{term}` role).

---

## Link validation

Zensical validates links at build time, on by default, resolving inline and reference-style
links **and anchors**. This is the main safety net for a restructure and it is better than
MkDocs' — use it.

```toml
[project.validation]
invalid_links = "error"
invalid_link_anchors = "error"
```

```bash
zensical build --strict     # exits 1 on validation failure
```

Always link to `.md` files, not built HTML paths — Zensical rewrites them according to
`use_directory_urls`. Linking to `.html` bypasses validation and breaks when that setting changes.

Some `[project.validation]` keys (`unresolved_references`, `unresolved_footnotes`,
`unused_definitions`, `unused_footnotes`, `shadowed_definitions`, `shadowed_footnotes`) are
deprecated in their current form; `invalid_links` and `invalid_link_anchors` are the active ones.
`validation = false` disables everything.

---

## Cross-linking and glossaries

There is no `{term}`/`{ref}` role system. The equivalents:

- **Relative `.md` links** for cross-mode references — validated at build time, so they are safe.
- **Heading anchors** via `toc.permalink = true`; anchors are slugified from heading text, so
  renaming a heading breaks inbound links. Where a link must survive, add an explicit anchor
  (`## Flags {#cli-run-flags}` with `attr_list` enabled).
- **A glossary** via the `abbr` extension plus a snippets-included abbreviations file, so a term
  defined once gets tooltips everywhere. This substitutes for Sphinx's glossary role and solves
  the same duplication problem.

---

## API reference

Zensical supports **mkdocstrings** and **autorefs**, so Python API reference can be generated
into `reference/api/` pages and listed in the nav alongside hand-written reference. `gen-files`
and `literate-nav` are **not** supported, so the common mkdocstrings pattern of generating one
page per module at build time does not work — write the API pages explicitly, one per module or
package, each containing the mkdocstrings directive.

That is more manual than the Sphinx equivalent, but it has an upside worth noting to the user:
explicit pages let you curate what appears in reference and give each a proper title, rather
than dumping the module tree into the nav.

---

## Feature gaps that affect architecture

| Need | Status |
| --- | --- |
| Redirects / aliases | **Not supported** — see the top of this file |
| Tag index/listing pages | Not supported. Tagging pages works (rendered at page bottom, filterable in search) but there are no tag landing pages yet |
| Blog | Not supported |
| Social cards | Not supported |
| `awesome-nav` / `literate-nav` / `.pages` files | Not supported |
| `gen-files` | Not supported |
| `hooks` | Not supported |
| Search UI localisation | English-only at present |
| Versioning | Supported via `mike`, with version warning banner and aliases |
| Offline builds | Supported (`use_directory_urls` forced false) |
| mkdocstrings / autorefs / macros / glightbox | Supported |

If the plan depends on tag-based navigation across modes (e.g. "all pages about
authentication"), note that only search-based filtering is available today.

---

## Migrating from MkDocs

`mkdocs.yml` is read natively and will stay supported as a transition mechanism, so a Diátaxis
restructure and a Zensical migration do not have to happen together — and generally should not.
Do them as separate changes so that when something renders oddly you know which change caused it.

There is **no `zensical migrate` command**; the CLI has only `new`, `build`, `serve`. Converting
`mkdocs.yml` to `zensical.toml` is manual.

Generated HTML is deliberately identical to Material for MkDocs, so existing overrides, CSS and
JS carry over. Two theme variants: `modern` (default) and `classic` (pixel-matches Material).

---

## CLI and CI

```bash
zensical new <dir>
zensical serve --open --dev-addr localhost:8000
zensical build --strict --clean
```

`build` options: `--config-file/-f`, `--clean/-c`, `--strict/-s`. `serve` options:
`--config-file/-f`, `--open/-o`, `--dev-addr/-a`. (`serve --strict` exists but is marked
unsupported.)

CI for a restructure:

```bash
zensical build --strict          # fails on broken internal links and anchors
```

Zensical's own validation covers internal links but not inbound URLs, so also run:

```bash
python <skill-dir>/scripts/check_links.py docs/            # works before the site builds
python <skill-dir>/scripts/make_redirect_stubs.py --map audit/migration-map.md \
    --emit stubs --out site/ --url-style dirhtml            # after zensical build
```
