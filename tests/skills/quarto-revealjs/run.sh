#!/usr/bin/env bash
# End-to-end test of the quarto-revealjs skill: set up a deck folder the way SKILL.md says, render
# the fixture decks, and check them offline, in PDF, and feature by feature against the guide.
#
#   tests/skills/quarto-revealjs/run.sh [work-dir]
#
# Needs on PATH: quarto, python3 with plotly + jupyter + playwright (and Google Chrome), ffmpeg, curl.
# MATHJAX_JS=<path to tex-svg-full.js> skips the download. Exits 1 if any step fails; all steps run.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill=$(cd "$here/../../../quarto-revealjs" && pwd)
work=${1:-$(mktemp -d)}
status=0
step() { echo; echo "== $1"; }
fail() { echo "::error::$1"; status=1; }

step "versions"
python3 "$here/versions_check.py" "$skill/versions.json" || status=1

step "set up the deck folder from the skill's assets"
mkdir -p "$work"
cp -R "$skill/assets/." "$work/"
cp -R "$here/fixture/." "$work/"
cd "$work" || exit 1
mkdir -p _vendor/mathjax _vendor/plotly media
mathjax=$(python3 -c "import json; print(json.load(open('$skill/versions.json'))['mathjax'])")
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
QUARTO_PYTHON=${QUARTO_PYTHON:-$(command -v python3)} quarto render || fail "quarto render"

step "offline check (no network requests, no page errors, no raw TeX)"
python3 check_offline.py _output/demo.html _output/reveal-features.html || fail "offline check"

step "PDF"
python3 make_pdf.py _output/demo.html || fail "make_pdf"
# title, equation, equation with its fragment, notes page, plotly, app still = 6 pages
pages=$(python3 -c "import re; print(len(re.findall(rb'/Type\s*/Page[^s]', open('_output/demo.pdf','rb').read())))" 2>/dev/null || echo 0)
echo "demo.pdf: $pages pages"
[ "$pages" -ge 6 ] || fail "demo.pdf has $pages pages, expected at least 6"

step "feature table (reveal-features.qmd against the guide)"
python3 "$here/feature_check.py" _output/reveal-features.html "$work" || fail "feature check differs from the guide"

echo
[ $status -eq 0 ] && echo "quarto-revealjs: all checks passed" || echo "quarto-revealjs: FAILED (see ::error:: lines)"
exit $status
