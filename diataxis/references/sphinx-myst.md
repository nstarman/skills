# Sphinx + MyST: implementing a Diátaxis restructure

Exact syntax and configuration for building the structure described in `architecture.md` on
Sphinx with MyST-Parser. Verified against the Sphinx, MyST-Parser, sphinx-design,
sphinx-autoapi, sphinx-autodoc2, sphinx-reredirects and sphinxext-rediraffe documentation.

**Contents**

- [Layout](#layout)
- [toctree](#toctree)
- [Section landing pages](#section-landing-pages)
- [MyST setup](#myst-setup)
- [Cross-referencing](#cross-referencing)
- [Code and includes](#code-and-includes)
- [API reference placement](#api-reference-placement)
- [Redirects](#redirects)
- [rst and md together](#rst-and-md-together)
- [Starter conf.py](#starter-confpy)
- [CI](#ci)

---

## Layout

```
docs/
  conf.py
  index.md                     # root: hidden toctree of the four section indexes
  tutorials/index.md           # + hidden toctree
  how-to/index.md
  reference/
    index.md
    cli.md
    configuration.md
    api/                       # generated output lands here
  explanation/index.md
  _static/
```

Directory layout is convention — Sphinx specifies only the toctree mechanics below. But with
pydata-sphinx-theme, top-level toctree entries become the navbar, so four top-level entries
give you exactly four navbar items. That alignment is the main reason to use folder-per-mode.

---

## toctree

MyST spelling, with options as `:key: value` lines directly under the opening fence:

````markdown
```{toctree}
:maxdepth: 2
:caption: Tutorials
:titlesonly:

installation
first-pipeline
```
````

| Option | Effect |
| --- | --- |
| `:maxdepth: N` | Depth of the tree; default is all levels |
| `:caption: text` | Sidebar section header in most themes |
| `:hidden:` | "Defines the document hierarchy… will not insert links into the document" |
| `:titlesonly:` | "Only list document titles, not other headings of the same level" |
| `:glob:` | Glob wildcards; matches inserted **alphabetically** |
| `:numbered:` | Section numbering — put it only on the top-level toctree |
| `:reversed:` | Reverse entry order (useful with `:glob:`) |
| `:name:` | Implicit target, referenceable with `{ref}` |

Entry forms: `docname`, `Title <docname>` (overrides the target's own title), a bare URL, and
`self` (the document containing the toctree).

**Every document must appear in some toctree** or Sphinx warns. Escape hatches:
`exclude_patterns` in `conf.py`, or `orphan: true` in a page's front matter.

`:glob:` sorts alphabetically, which suits nothing except accident. Tutorials are ordered —
list them explicitly, or prefix `01-`, `02-`.

---

## Section landing pages

The idiom is a visible hand-written page plus a `:hidden:` toctree that registers the children
for the machine. Without `:hidden:` you get a duplicated bullet list under your carefully
written cards.

`docs/tutorials/index.md`:

````markdown
# Tutorials

Learning-oriented lessons. Start here if you have not used the toolkit before.

If you already know what you want to accomplish, the [how-to guides](../how-to/index.md)
will get you there faster.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Install and first run
:link: installation
:link-type: doc

Get a working environment and run your first query in ten minutes.
:::

:::{grid-item-card} Build your first pipeline
:link: first-pipeline
:link-type: doc

Fetch, transform and publish a dataset end to end.
:::
::::

```{toctree}
:hidden:
:maxdepth: 1

installation
first-pipeline
```
````

Root `docs/index.md` chains the four:

````markdown
```{toctree}
:hidden:
:maxdepth: 2

tutorials/index
how-to/index
reference/index
explanation/index
```
````

Drop the sidebar on the landing page only:

```python
html_sidebars = {"index": []}
```

`:link-type:` accepts `url` (default), `ref`, `doc`, `any`. Use `doc` with a docname, or `ref`
with an explicit `(label)=` target.

Other sphinx-design pieces worth having: `tab-set` with `:sync-group:` for how-tos that differ
by platform (the reader picks once and it applies site-wide), and `dropdown` for advanced
options so the happy path stays short.

````markdown
::::{tab-set}
:sync-group: platform

:::{tab-item} macOS
:sync: macos

```console
brew install toolkit
```
:::

:::{tab-item} Linux
:sync: linux

```console
sudo apt install toolkit
```
:::
::::
````

---

## MyST setup

```python
extensions = ["myst_parser", "sphinx_design"]

myst_enable_extensions = [
    "colon_fence",   # ::: fences — required by all sphinx-design examples
    "deflist",       # definition lists — reference pages live on these
    "substitution",  # {{ version }} — stops version strings drifting between modes
    "fieldlist",     # needed if sphinx-style docstrings pass through MyST
    "attrs_block",   # {#id .class} block attributes
    "linkify",       # bare URLs become links
]
myst_heading_anchors = 3
```

`colon_fence` is worth enabling regardless of sphinx-design: `:::{note}` renders acceptably in
GitHub and editor previews, where backtick-brace directives do not.

Admonitions: `note`, `tip`, `warning`, `caution`, `important`, `attention`, `danger`, `error`,
`hint`, `seealso`, plus `versionadded`, `versionchanged`, `deprecated`.

`{seealso}` is the cross-mode workhorse — the standard place to put the links that let a mode
stay lean:

```markdown
:::{seealso}
- {doc}`/explanation/architecture` — why the scheduler is single-threaded
- {ref}`cli-run-flags` — every flag accepted by `run`
:::
```

Nesting requires the outer fence to have more backticks (or use `:::` inside ` ``` `).

---

## Cross-referencing

Diátaxis depends on links replacing duplication, so this is the load-bearing configuration.

**Explicit targets** — three forms:

```markdown
(cli-run-flags)=
### Flags

{#config-precedence}
This paragraph explains precedence.        <!-- needs attrs_block -->
```

```markdown
:::{note}
:name: caching-caveat
:::
```

**Roles:**

```markdown
{ref}`cli-run-flags`
{ref}`Explicit text <cli-run-flags>`
{doc}`/reference/cli`
{doc}`the CLI reference </reference/cli>`
{term}`idempotent`
{py:func}`toolkit.search`
{numref}`fig-pipeline`
```

A label placed immediately before a section title generates its own link text from the heading
and "works across files and persists even when section titles change."

**Use absolute `{doc}` paths** (leading `/`, relative to the source root) for cross-mode links.
Relative paths break the moment a page moves between sections — which is the entire activity
here.

**Markdown-native forms** also work and preview correctly on GitHub:

```markdown
[the CLI reference](../reference/cli.md)
[precedence](#config-precedence)
<project:/reference/cli.md#flags>
<inv:python:py:class#zipfile.ZipFile>
```

**`myst_heading_anchors = 3`** auto-generates GitHub-style anchors for every heading. Convenient,
but derived from heading *text* — renaming a heading silently breaks inbound links. For links
that must survive a restructure, write explicit `(label)=` targets.

**Intersphinx:**

```python
extensions += ["sphinx.ext.intersphinx"]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}
```

`intersphinx_disabled_reftypes` defaults to `['std:doc']`, so bare `{doc}` refs will not
silently resolve into another project.

**Glossary** — define once in reference, `{term}`-link from everywhere. This is the cheapest
way to stop concept definitions duplicating across modes:

````markdown
```{glossary}
idempotent
  An operation that produces the same result whether applied once or many times.
```
````

---

## Code and includes

A `{code-block}` with a caption and emphasis:

````markdown
```{code-block} python
:caption: pipeline.py
:emphasize-lines: 2,3
:name: pipeline-config

client = Client()
client.configure(retries=3)
client.run()
```
````

**Include from real files, with sentinels — not line numbers:**

````markdown
```{literalinclude} ../examples/pipeline.py
:language: python
:caption: examples/pipeline.py
:start-after: # start: configure
:end-before: # end: configure
:dedent: 4
```
````

`:lines: 12-30` rots silently whenever the example file is edited. `:start-after:`/`:end-before:`
survives edits and is the single highest-value habit for keeping examples true.

**Shared snippets between modes** — MyST `include`:

````markdown
```{include} /_snippets/auth-prerequisite.md
:heading-offset: 1
:relative-docs: ..
:relative-images:
```
````

`relative-docs` matters: without it, links inside the included file resolve relative to the
snippet's location, not the including page. Use includes sparingly — a link is usually the
right answer, and a shared snippet is a duplication you have merely centralized.

---

## API reference placement

The goal from `architecture.md`: generated API docs live *inside* `reference/`, not beside it.
Every generator defaults to injecting its own top-level nav entry, which produces a fifth
section outside the four modes. Turn that off.

| Tool | Imports your code? | Emits | Turn off its own toctree with |
| --- | --- | --- | --- |
| `sphinx.ext.autodoc` | yes | inline (you write the pages) | n/a |
| `sphinx.ext.autosummary` | yes | `.rst` stubs | you control `:toctree:` dir |
| `sphinx-autoapi` | no (static analysis) | `.rst` | `autoapi_add_toctree_entry = False` |
| `sphinx-autodoc2` | no (static analysis) | `.rst` **or `.md`** | manual mode / place index yourself |

**autoapi** — safe for packages with import side effects or heavy deps:

```python
extensions = ["autoapi.extension"]
autoapi_dirs = ["../src/toolkit"]
autoapi_root = "reference/api"
autoapi_add_toctree_entry = False       # essential — otherwise you get a 5th nav section
autoapi_options = ["members", "undoc-members", "show-inheritance"]
autoapi_member_order = "bysource"
```

**autodoc2** — the only one that emits MyST Markdown, so generated pages match hand-written
ones in a Markdown-first project:

```python
extensions = ["autodoc2"]
autodoc2_packages = ["../src/toolkit"]
autodoc2_render_plugin = "myst"
autodoc2_output_dir = "reference/api"
```

Add `"fieldlist"` to `myst_enable_extensions` if docstrings are sphinx-style.

**autodoc inside MyST** requires `eval-rst`:

````markdown
```{eval-rst}
.. automodule:: toolkit.core
   :members:
   :member-order: bysource
```
````

Note that autodoc and autosummary **import** the modules they document: "If any modules have
side effects on import, these will be executed by autodoc when sphinx-build is run."

Do not mix two generators — both claim `py:` domain targets and produce duplicate-object
warnings.

Then in `reference/index.md`, list `api/index` in the hidden toctree alongside the hand-written
reference pages, so generated and hand-written reference appear as one section.

---

## Redirects

Every URL changes in a restructure. Both extensions below emit meta-refresh HTML, which is a
workaround for static hosts; if you control the server (or use Netlify `_redirects`, Cloudflare
rules, or Read the Docs' redirect dashboard), do server-side 301s and treat the extension as a
belt-and-braces fallback.

### sphinxext-rediraffe — for in-project restructures, CI-enforceable

This is the right default here, because it can **fail the build when you move a file without
adding a redirect**.

```python
extensions += ["sphinxext.rediraffe"]
rediraffe_branch = "main"
rediraffe_redirects = "redirects.txt"
```

`docs/redirects.txt` — source filenames *with* extensions on both sides:

```
# comments start with '#'
getting-started.md          tutorials/installation.md
guides/authentication.md    how-to/authenticate.md
'design notes.md'           explanation/architecture.md
```

Builders:

```bash
sphinx-build -b rediraffecheckdiff docs docs/_build   # CI: fails if a moved file has no redirect
sphinx-build -b rediraffewritediff docs docs/_build   # adds renames automatically
```

`rediraffewritediff` only works with configuration files and cannot detect deleted files.
Rediraffe chains transitively (A→B, B→C implies A→C), which matters across successive
restructure increments.

### sphinx-reredirects — for wildcards and cross-domain moves

Source is a **docname** (no suffix); target is a URL matching the builder's output naming.

```python
extensions += ["sphinx_reredirects"]
redirects = {
    "getting-started":       "tutorials/installation.html",
    "guides/authentication": "../how-to/authenticate.html",
    "faq/*":                 "explanation/faq/$source.html",
    "*":                     "https://newdocs.example.com/$source.html",
}
```

Wildcards are `fnmatch` only (`*`, `?`, `[seq]`, `[!seq]`) — `**` has no special meaning. `$source`
is the matched docname and has no suffix, so append `.html` or `/`. With the `dirhtml` builder,
targets must be folders (`"install/"`). A source that already exists gets **overwritten** with
the redirect; wildcards only expand against existing documents, so explicitly list pages you
have `git mv`d away.

Its default template preserves the URL fragment via JavaScript, which matters a lot — deep links
into old pages carry anchors. Override with `redirect_html_template_file`.

### Canonical URLs

```python
html_baseurl = "https://docs.example.com/en/stable/"
```

Emits `<link rel="canonical">` on every page. Set it before the restructure ships, and update it
if the site itself moves.

---

## rst and md together

A mixed tree is normal during migration and fully supported.

```python
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
```

Cross-references resolve across the boundary — targets live in Sphinx's domain registries, not
in the parser — so `{ref}` from a `.md` page finds a label in a `.rst` page. That is what makes
incremental conversion safe.

Markdown inside rST:

```rst
.. include:: include.md
   :parser: myst_parser.sphinx_
```

Inside roles, use rST-style `` {role}`Text <target>` ``, not Markdown link syntax — some roles
hard-code the rST pattern.

**Move first, convert second, in separate commits.** A combined diff is unreviewable and
rediraffe's rename detection works on similarity. If the rST side uses
`sphinx.ext.autosectionlabel`, expect duplicate-label warnings during the mixed period, since
its slugs differ from `myst_heading_anchors`.

---

## Starter conf.py

```python
extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx.ext.intersphinx",
    "sphinxext.rediraffe",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "**.ipynb_checkpoints"]

myst_enable_extensions = [
    "colon_fence", "deflist", "substitution", "fieldlist", "attrs_block", "linkify",
]
myst_heading_anchors = 3

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

html_theme = "pydata_sphinx_theme"
html_baseurl = "https://docs.example.com/en/stable/"
html_theme_options = {
    "navbar_center": ["navbar-nav"],   # top-level toctree entries -> navbar
    "show_nav_level": 1,
    "navigation_depth": 3,
}
html_sidebars = {"index": []}

rediraffe_branch = "main"
rediraffe_redirects = "redirects.txt"

nitpicky = True          # unresolved cross-references become warnings
```

Theme option names differ between pydata-sphinx-theme and sphinx-book-theme and have been
renamed across minor releases — pin versions and check the changelog rather than copying option
names between themes.

---

## CI

```bash
python <skill-dir>/scripts/check_links.py docs/           # fast, pre-build, checks fragments too
sphinx-build -W --keep-going -b html docs docs/_build/html
sphinx-build -b rediraffecheckdiff docs docs/_build/redirects
sphinx-build -b linkcheck docs docs/_build/linkcheck
```

Run `check_links.py` first while editing: it works on a tree that does not build yet, and it
verifies `#fragment` targets against heading slugs and explicit anchors, which is where a
restructure breaks links most quietly. `redirects.txt` for rediraffe can be generated from the
migration map with `scripts/make_redirect_stubs.py --emit rediraffe`.

`-W` turns warnings into errors, which with `nitpicky = True` means a broken cross-mode
reference fails CI. That is what makes "link instead of duplicating" a discipline the project
can actually keep. `rediraffecheckdiff` is the guard that stops a moved page from losing its
inbound links. Note that linkcheck does not currently verify redirects to other pages within
the same documentation.
