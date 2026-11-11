#!/usr/bin/env bash
# End-to-end test of the quarto-revealjs skill: set up a deck folder the way SKILL.md says, render
# the fixture decks, and check them offline, in PDF, and feature by feature against the guide;
# then check the gotchas the guide documents (KaTeX not embedded, chalkboard refuses one file).
#
#   tests/skills/quarto-revealjs/run.sh [work-dir]
#
# Needs on PATH: quarto, python3 with plotly + jupyter + playwright (Google Chrome or Playwright's
# Chromium, and Playwright's WebKit), ffmpeg, curl. Every browser runs headless.
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
# An inline app over Chrome's 2 MB data: URL limit (lessons.qmd, #big-app), padded so nothing big is committed.
python3 -c "import pathlib; a = pathlib.Path('apps'); pathlib.Path(a, 'big.html').write_text(
    a.joinpath('background.html').read_text().replace('app ok', 'big app ok').replace('</body>', '<!--' + 'x' * 3_000_000 + '-->\\n</body>'))"

step "render"
export QUARTO_PYTHON=${QUARTO_PYTHON:-$(command -v python3)}
quarto render || fail "quarto render"

step "offline check (no network requests, no missing files, no page errors, no raw TeX)"
python3 check_offline.py _output/demo.html _output/reveal-features.html || fail "offline check"
python3 check_offline.py --webkit _output/demo.html _output/reveal-features.html || fail "offline check (WebKit)"

step "inline_apps.py: the deck alone in an empty folder still has its apps (background iframe, data-app over 2 MB)"
solo="$work-solo"; rm -rf "$solo"; mkdir -p "$solo"
python3 inline_apps.py _output/lessons.html -o "$solo/lessons.html" || fail "inline_apps.py"
python3 check_offline.py "$solo/lessons.html" || fail "inlined deck is not self-contained"
python3 check_offline.py --webkit "$solo/lessons.html" || fail "inlined deck is not self-contained (WebKit)"
cp "$solo/lessons.html" "$solo/again.html"
python3 inline_apps.py "$solo/again.html" >/dev/null 2>&1 \
  && cmp -s "$solo/lessons.html" "$solo/again.html" || fail "inline_apps.py changed an already-inlined deck"
python3 "$here/lessons_check.py" "$solo/lessons.html" || fail "lessons check (Chromium)"
python3 "$here/lessons_check.py" "$solo/lessons.html" --webkit || fail "lessons check (WebKit)"
grep -q '<object data="data:image/svg+xml' "$solo/lessons.html" || fail "<object> not inlined"
grep -q '<aside class="notes"' "$solo/lessons.html" || fail "archive copy lost its notes"
python3 -c "import base64, sys; b = base64.b64encode(open('apps/explorer.png', 'rb').read()).decode()
sys.exit(open(sys.argv[1]).read().count(b) != 1)" "$solo/lessons.html" || fail "image on two slides embedded twice"
# the 3 MB app is padding, so gzipped it adds almost nothing (4 MB of base64 without gzip)
[ $(( $(wc -c < "$solo/lessons.html") - $(wc -c < _output/lessons.html) )) -lt 1000000 ] || fail "inlined apps are not gzipped"
python3 size_report.py "$solo/lessons.html" 3 | grep -q "MB in all; the largest parts:" || fail "size_report.py"

step "share build: quarto render --profile share, then inline_apps.py --strip-notes"
quarto render lessons.qmd --profile share >/dev/null 2>&1 || fail "share render"
python3 inline_apps.py --strip-notes _share/lessons.html || fail "inline_apps.py --strip-notes"
if grep -q '<aside class="notes' _share/lessons.html; then fail "shared copy has speaker notes"; else echo "shared copy has no notes"; fi
python3 check_offline.py _share/lessons.html || fail "shared copy is not self-contained"
python3 check_offline.py --webkit _share/lessons.html || fail "shared copy is not self-contained (WebKit)"

step "overflow check: flags only #too-long in lessons.html, nothing in demo.html"
for engine in "" --webkit; do
  out=$(python3 check_overflow.py $engine _output/lessons.html); echo "$out"
  n=$(grep -c '^     slide' <<<"$out"); others=$(grep '^     slide' <<<"$out" | grep -vc '#too-long')
  [ "$n" -ge 1 ] && [ "$others" -eq 0 ] || fail "overflow check ${engine:-chromium}: expected only #too-long"
  python3 check_overflow.py $engine _output/demo.html || fail "overflow in demo.html (${engine:-chromium})"
done

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
