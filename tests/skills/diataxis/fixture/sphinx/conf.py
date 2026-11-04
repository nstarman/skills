# The "Starter conf.py" of diataxis/references/sphinx-myst.md, as written there, except:
#  - intersphinx is left out (it needs the network, and a failed fetch is a warning under -W);
#  - REDIRECTS=reredirects swaps rediraffe for sphinx-reredirects, configured as in the
#    reference's "sphinx-reredirects" section, so both documented mechanisms are built.
import os

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinxext.rediraffe",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "**.ipynb_checkpoints"]

myst_enable_extensions = [
    "colon_fence", "deflist", "substitution", "fieldlist", "attrs_block", "linkify",
]
myst_heading_anchors = 3

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

if os.environ.get("REDIRECTS") == "reredirects":
    extensions.remove("sphinxext.rediraffe")
    extensions += ["sphinx_reredirects"]
    redirects = {
        "getting-started": "tutorials/installation.html",
        "usage":           "how-to/schedule-runs.html",
    }
