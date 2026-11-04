#!/usr/bin/env bash
# End-to-end test of the quarto-revealjs skill: set up a deck folder the way SKILL.md says, render
# the fixture decks, and check them offline, in PDF, and feature by feature against the guide;
# then check the gotchas the guide documents (KaTeX not embedded, chalkboard refuses one file).
#
#   tests/skills/quarto-revealjs/run.sh [work-dir]
#
# Needs on PATH: quarto, python3 with plotly + jupyter + playwright (and Google Chrome), ffmpeg, curl.
# MATHJAX_JS=<path to tex-svg-full.js> skips the download. Exits 1 if any step fails; all steps run.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill=$(cd "$here/../../../quarto-revealjs" && pwd)
work=${1:-$(mktemp -d)}
mkdir -p "$work" && work=$(cd "$work" && pwd)   # absolute: later steps cd into it
status=0
step() { echo; echo "== $1"; }
fail() { echo "::error::$1"; status=1; }

step "versions"
python3 "$here/versions_check.py" "$skill/versions.json" || status=1

step "set up the deck folder from the skill's assets"
cp -R "$skill/assets/." "$work/"
cp -R "$here/fixture/." "$work/"
rm -rf "$work/gotchas"                            # rendered on their own below, not in the project
cd "$work" || exit 1
mkdir -p _vendor/mathjax _vendor/plotly media
mathjax=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['mathjax'])" "$skill/versions.json")
if [ -n "${MATHJAX_JS:-}" ]; then
  cp "$MATHJAX_JS" _vendor/mathjax/tex-svg-full.js
else
  curl -fsSL -o _vendor/mathjax/tex-svg-full.js \
    "https://cdn.jsdelivr.net/npm/mathjax@${mathjax}/es5/tex-svg-full.js" || fail "MathJax download"
fi
cp "$(python3 -c 'import plotly, pathlib; print(pathlib.Path(plotly.__file__).parent / "package_data/plotly.min.js")')" \
  _vendor/plotly/plotly.min.js
# Test media and images, generated so nothing binary is committed.
ffmpeg -loglevel error -y -f lavfi -i "testsrc2=size=640x360:rate=24:duration=3" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart media/clip.mp4
ffmpeg -loglevel error -y -f lavfi -i "sine=frequency=440:duration=2" media/tone.mp3
ffmpeg -loglevel error -y -f lavfi -i "testsrc2=size=1280x720" -frames:v 1 apps/explorer.png
ffmpeg -loglevel error -y -f lavfi -i "smptebars=size=1280x720" -frames:v 1 apps/explorer-full.png

step "render"
export QUARTO_PYTHON=${QUARTO_PYTHON:-$(command -v python3)}
quarto render || fail "quarto render"

step "offline check (no network requests, no missing files, no page errors, no raw TeX)"
python3 check_offline.py _output/demo.html _output/reveal-features.html || fail "offline check"

step "PDF"
python3 make_pdf.py _output/demo.html || fail "make_pdf"
# title, equation, equation with its fragment, notes page, plotly, app still = 6 pages; the still
# is the PDF's only raster image (math and Plotly print as vectors).
read -r pages images < <(python3 -c "
import re, sys; d = open(sys.argv[1], 'rb').read()
print(len(re.findall(rb'/Type\s*/Page[^s]', d)), len(re.findall(rb'/Subtype\s*/Image', d)))" _output/demo.pdf 2>/dev/null || echo "0 0")
echo "demo.pdf: $pages pages, $images raster images"
[ "$pages" -eq 6 ] || fail "demo.pdf has $pages pages, expected 6"
[ "$images" -ge 1 ] || fail "demo.pdf has no raster image: the app's print still is missing"

step "feature table (reveal-features.qmd against the guide)"
python3 "$here/feature_check.py" _output/reveal-features.html "$work/_output" _output/demo.html \
  || fail "feature check differs from the guide"

step "documented gotchas still hold (if one stops holding, update the guide)"
g="$work-gotchas"; rm -rf "$g"; mkdir -p "$g"; cp "$here"/fixture/gotchas/*.qmd "$g/"
( cd "$g" && quarto render katex.qmd >/dev/null 2>&1 ) || fail "katex.qmd did not render"
if python3 "$work/check_offline.py" "$g/katex.html" >/dev/null 2>&1; then
  fail "KaTeX deck now works offline: the guide says KaTeX is not embedded"
else
  echo "KaTeX deck still fails offline, as the guide says"
fi
if ( cd "$g" && quarto render chalkboard.qmd >/dev/null 2>&1 ); then
  fail "chalkboard now renders with embed-resources: the guide says Quarto refuses it"
else
  echo "chalkboard with embed-resources still refused, as the guide says"
fi

echo
[ $status -eq 0 ] && echo "quarto-revealjs: all checks passed" || echo "quarto-revealjs: FAILED (see ::error:: lines)"
exit $status
