#!/usr/bin/env bash
# End-to-end test of the diataxis skill: lay out a small docs tree the Diátaxis way, as SKILL.md
# and references/architecture.md say (four mode folders, landing pages from assets/), run the
# skill's scripts on it, then build it on each stack its references document, with their config
# snippets: Sphinx + MyST (references/sphinx-myst.md) and Zensical (references/zensical.md).
# Checks that pages land where the references say, that redirects (every documented mechanism)
# resolve, and that documented behaviours still hold in both directions.
#
#   tests/skills/diataxis/run.sh [work-dir]
#
# Needs on PATH: python3 with sphinx, myst-parser, linkify-it-py, sphinx-design,
# sphinxext-rediraffe, sphinx-reredirects, pydata-sphinx-theme and zensical; git.
# Exits 1 if any step fails; all steps run.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill=$(cd "$here/../../../diataxis" && pwd)
scripts=$skill/scripts
fx=$here/fixture
work=${1:-$(mktemp -d)}
rm -rf "$work" && mkdir -p "$work" && work=$(cd "$work" && pwd)   # absolute: later steps cd
status=0
step() { echo; echo "== $1"; }
fail() { echo "::error::$1"; status=1; }
ok() { echo "ok: $1"; }
# A page each stack must build, by the URL style it uses (Sphinx html: x.html; Zensical: x/).
pages="index tutorials/index tutorials/installation tutorials/first-pipeline how-to/index
  how-to/schedule-runs reference/index reference/cli explanation/index explanation/architecture
  about/contributing"
git() { command git -c user.name=test -c user.email=test@example.com -c init.defaultBranch=main "$@"; }

step "versions"
python3 "$here/versions_check.py" "$skill/versions.json" || status=1

step "lay out the docs tree (fixture pages + the skill's landing-page and contributing assets)"
src=$work/docs
cp -R "$fx/docs" "$src"
cp "$skill/assets/landing-page-template.md" "$src/how-to/index.md"   # as shipped, comments and all
# contributing-diataxis.md is a drop-in section (starts at ##) for docs/about/contributing.md.
{ echo "# Contributing"; echo; cat "$skill/assets/contributing-diataxis.md"; } > "$src/about/contributing.md"
find "$src" -name '*.md' | sed "s|^$work/||" | sort

step "scripts/check_links.py: clean tree passes, a broken anchor fails"
python3 "$scripts/check_links.py" "$src" --quiet && ok "no unresolved links" || fail "check_links.py reports problems on the fixture tree"
cp -R "$src" "$work/broken"
echo "See [flags](../reference/cli.md#no-such-anchor)." >> "$work/broken/tutorials/index.md"
if python3 "$scripts/check_links.py" "$work/broken" --quiet >/dev/null; then
  fail "check_links.py missed a broken #fragment"
else ok "broken #fragment caught"; fi

step "scripts/docs_inventory.py: each page reads as its folder's mode, about/ is not practitioner docs"
python3 "$scripts/docs_inventory.py" "$src" --format json --out "$work/inventory.json" || fail "docs_inventory.py failed"
python3 "$scripts/docs_inventory.py" "$src" --out "$work/inventory.md" || fail "docs_inventory.py (md) failed"
python3 - "$work/inventory.json" "$work/inventory.md" <<'EOF' || fail "docs_inventory.py results differ from the tree's modes"
import json, sys
mode = {"tutorials": "tutorial", "how-to": "howto", "reference": "reference", "explanation": "explanation"}
bad = 0
for p in json.load(open(sys.argv[1])):
    top = p["path"].split("/")[0]
    want = mode.get(top)
    if top == "about" and not p["non_practitioner"]:
        print(f"  {p['path']}: not flagged as non-practitioner"); bad += 1
    if want and p["guess"] != want:
        print(f"  {p['path']}: reads as {p['guess']}, expected {want}"); bad += 1
md = open(sys.argv[2]).read()
for section in ("## Facts asserted on more than one page", "## Duplicate titles", "## Pages nothing links to"):
    if section in md:
        print(f"  inventory.md has '{section}': the fixture has none"); bad += 1
print("ok: modes, non-practitioner flag, no duplicates, no orphans" if not bad else "")
sys.exit(bad > 0)
EOF

step "scripts/check_repo_refs.py: a README naming a moved page is caught, then clean once fixed"
repo=$work/repo; mkdir -p "$repo"; cp "$fx/repo/README.md" "$repo/"; cp -R "$src" "$repo/docs"
if out=$(python3 "$scripts/check_repo_refs.py" "$repo" --old-docs "$fx/repo/old-docs" --new-docs "$repo/docs"); then
  fail "check_repo_refs.py missed README.md's link to a moved page"
else
  echo "$out" | grep -q "README.md" && ok "stale README.md reference caught" || fail "check_repo_refs.py failed without naming README.md: $out"
fi
sed -i.bak 's|docs/getting-started.md|docs/tutorials/installation.md|' "$repo/README.md" && rm "$repo/README.md.bak"
python3 "$scripts/check_repo_refs.py" "$repo" --old-docs "$fx/repo/old-docs" --new-docs "$repo/docs" \
  && ok "clean once README.md is fixed" || fail "check_repo_refs.py still reports after the fix"

# ---------------------------------------------------------------------------------------------
step "Sphinx + MyST: build with the reference's starter conf.py, -W -n (warnings fail)"
sp=$work/sphinx; mkdir -p "$sp"; cp -R "$src" "$sp/docs"; cp -R "$fx/sphinx/." "$sp/docs/"
# Section landing pages = hand-written page + hidden toctree (sphinx-myst.md, "Section landing
# pages"); tutorials/index.md comes from the fixture's copy of the reference's card-grid example.
toctree() { f=$1; shift; { printf '\n```{toctree}\n:hidden:\n:maxdepth: 2\n\n'; printf '%s\n' "$@"; printf '```\n'; } >> "$sp/docs/$f"; }
toctree index.md tutorials/index how-to/index reference/index explanation/index about/changelog about/contributing
toctree how-to/index.md read-from-private-s3 write-partitioned-parquet schedule-runs deploy-on-kubernetes
toctree reference/index.md cli configuration glossary
toctree explanation/index.md architecture
python3 "$scripts/check_links.py" "$sp/docs" --quiet && ok "check_links.py resolves the MyST roles and targets" \
  || fail "check_links.py reports problems on the Sphinx tree (MyST roles)"
# redirects.txt for rediraffe, generated as sphinx-myst.md ("CI") says, from a filename map.
python3 "$scripts/make_redirect_stubs.py" --map "$fx/rediraffe-map.txt" --emit rediraffe --out "$sp/docs/redirects.txt" \
  || fail "make_redirect_stubs.py --emit rediraffe"
cd "$sp" || exit 1
sphinx-build --version
sphinx-build -W --keep-going -n -q -b html docs docs/_build/html && ok "sphinx-build -W -n" || fail "sphinx-build -W -n failed (see warnings above)"
h=docs/_build/html
for p in $pages reference/glossary; do [ -f "$h/$p.html" ] || fail "Sphinx: $p.html not built"; done
grep -q '<link rel="canonical" href="https://docs.example.com/en/stable/tutorials/index.html"' "$h/tutorials/index.html" \
  && ok "html_baseurl emits rel=canonical" || fail "Sphinx: html_baseurl did not emit rel=canonical"
python3 - "$h/index.html" <<'EOF' || fail "Sphinx: navbar is not the root toctree's top-level entries"
# sphinx-myst.md: with pydata-sphinx-theme, top-level toctree entries become the navbar.
import re, sys
t = open(sys.argv[1]).read()
nav = t[t.find("navbar-nav"):]; nav = nav[:nav.find("</ul>")]
got = re.findall(r'href="([^"#]+)"', nav)
want = ["tutorials/index.html", "how-to/index.html", "reference/index.html", "explanation/index.html",
        "about/changelog.html", "about/contributing.html"]
print("navbar:", got)
sys.exit(got[:len(want)] != want)
EOF
grep -q 'sd-card' "$h/tutorials/index.html" && grep -q 'href="installation.html"' "$h/tutorials/index.html" \
  && ok "grid-item-card :link-type: doc renders linked cards" || fail "Sphinx: tutorials landing page has no linked cards"

step "Sphinx: rediraffe writes redirect pages that resolve"
python3 "$here/redirect_check.py" "$h" getting-started.html usage.html || fail "rediraffe redirects do not resolve"

step "Sphinx: rediraffecheckdiff fails on a move without a redirect, passes with one"
# Commit the old layout on branch main (rediraffe_branch), then move the pages as a restructure would.
mv docs/tutorials/installation.md docs/getting-started.md; mv docs/how-to/schedule-runs.md docs/usage.md
rm -rf docs/_build; git init -q && git add -A && git commit -qm "old layout"
git mv docs/getting-started.md docs/tutorials/installation.md; git mv docs/usage.md docs/how-to/schedule-runs.md
sphinx-build -q -b rediraffecheckdiff docs docs/_build/check >/dev/null 2>&1 && ok "passes with redirects.txt" \
  || fail "rediraffecheckdiff fails although every move has a redirect"
cp docs/redirects.txt redirects.full; : > docs/redirects.txt
if sphinx-build -q -b rediraffecheckdiff docs docs/_build/check-empty >/dev/null 2>&1; then
  fail "rediraffecheckdiff passes with no redirects: sphinx-myst.md says it fails the build"
else ok "fails when a moved file has no redirect"; fi
mv redirects.full docs/redirects.txt

step "Sphinx: sphinx-reredirects (docname -> .html) writes redirect pages that resolve"
REDIRECTS=reredirects sphinx-build -W -n -q -b html docs docs/_build/reredirects && ok "sphinx-build with sphinx-reredirects" \
  || fail "sphinx-build with sphinx-reredirects failed"
python3 "$here/redirect_check.py" docs/_build/reredirects getting-started.html usage.html || fail "sphinx-reredirects redirects do not resolve"
grep -q 'window.location.hash' docs/_build/reredirects/getting-started.html && ok "reredirects keeps the #fragment" \
  || fail "sphinx-reredirects' default template no longer keeps the fragment"

# ---------------------------------------------------------------------------------------------
step "Zensical: build with the reference's zensical.toml, --strict"
zn=$work/zensical; mkdir -p "$zn"; cp -R "$src" "$zn/docs"; cp "$fx/zensical/zensical.toml" "$zn/"
cp "$fx/zensical/errors.md" "$zn/docs/reference/errors.md"   # nav title, no H1 (see below)
cd "$zn" || exit 1
zensical --version
zensical build --strict --clean && ok "zensical build --strict" || fail "zensical build --strict failed"
for p in $pages reference/errors; do
  d=${p%index}; d=${d%/}                                    # directory URLs: x.md -> x/index.html
  f=site/${d:+$d/}index.html; [ "${p##*/}" = index ] || f=site/$p/index.html
  [ -f "$f" ] || fail "Zensical: $f not built"
done
# zensical.md, "Page titles": a page with a nav title and no H1 gets the nav title as its <h1>.
grep -q '<h1[^>]*>Error messages' site/reference/errors/index.html && ok "page without H1 takes its nav title" \
  || fail "Zensical: page without H1 does not show its nav title; zensical.md 'Page titles' needs updating"

step "Zensical: --strict fails on a broken link and on a broken anchor"
for bad in "[x](nope.md)" "[x](../reference/cli.md#no-such-anchor)"; do
  cp docs/tutorials/index.md index.md.keep; echo "$bad" >> docs/tutorials/index.md
  if zensical build --strict >/dev/null 2>&1; then fail "zensical build --strict passed with $bad"; else ok "caught $bad"; fi
  mv index.md.keep docs/tutorials/index.md
done

step "Zensical: generated stub pages (make_redirect_stubs.py, dirhtml) copied into site/ resolve"
zensical build --strict --clean >/dev/null 2>&1 || fail "rebuild"
python3 "$scripts/make_redirect_stubs.py" --map "$fx/migration-map.md" --emit stubs --out site/ --url-style dirhtml \
  || fail "make_redirect_stubs.py --emit stubs"
python3 "$here/redirect_check.py" site getting-started/index.html usage/index.html || fail "stub redirects do not resolve"

step "Zensical: the redirects plugin (redirect_maps), as zensical.md documents it"
{ cat zensical.toml; cat "$fx/zensical/redirects.toml"; } > redirects.toml
zensical build --strict --clean -f redirects.toml && ok "build with redirect_maps" || fail "zensical build with redirect_maps failed"
python3 "$here/redirect_check.py" site getting-started/index.html usage/index.html || fail "Zensical redirects do not resolve"

step "Zensical: the CLI is still new, build, serve (zensical.md: no migrate command)"
cmds=$(zensical --help | awk '/^Commands:/{f=1;next} f&&NF{print $1}' | sort | tr '\n' ' ')
[ "$cmds" = "build new serve " ] && ok "commands: $cmds" || fail "zensical commands are now: $cmds; update zensical.md 'CLI and CI' and 'Migrating from MkDocs'"

echo
[ $status -eq 0 ] && echo "diataxis: all checks passed" || echo "diataxis: FAILED (see ::error:: lines)"
exit $status
