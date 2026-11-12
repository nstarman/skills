#!/usr/bin/env bash
# End-to-end test of the quarto-revealjs skill: set up a deck folder from the skill's assets, build
# the fixture decks with quartz-deck's `qd export` (as the scaffold's Makefile does), and check them
# offline (Chromium and WebKit), as PDF, and feature by feature against the guide; then check the
# gotchas the guide documents (KaTeX not embedded, chalkboard refuses one file) with plain Quarto.
#
#   tests/skills/quarto-revealjs/run.sh [work-dir]
#
# Needs on PATH: quarto, qd (the version in quarto-revealjs/versions.json), python3 with plotly +
# jupyter + playwright (Google Chrome or Playwright's Chromium, and Playwright's WebKit), ffmpeg.
# Every browser runs headless. Exits 1 if any step fails; all steps run.
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill=$(cd "$here/../../../quarto-revealjs" && pwd)
work=${1:-$(mktemp -d)}
mkdir -p "$work" && work=$(cd "$work" && pwd)   # absolute: later steps cd into it
status=0
step() { echo; echo "== $1"; }
fail() { echo "::error::$1"; status=1; }
# qd's JSON result: `field <file> <python expression on d>`
field() { python3 -c "import json, sys; d = json.load(open(sys.argv[1])); print($2)" "$1"; }

step "versions"
python3 "$here/versions_check.py" "$skill/versions.json" || status=1

step "set up the deck folder from the skill's assets"
cp -R "$skill/assets/." "$work/"
for f in Makefile presentation.qmd README.md _quarto.yml .gitignore _extensions/paper/paper.lua \
         _talk/html/skip-steps.html _talk/html/notes-below.html _talk/style/presentation.css; do
  [ -f "$work/$f" ] || fail "the scaffold has no $f"
done
for f in inline_apps.py make_pdf.py check_offline.py check_overflow.py size_report.py bibliography.py \
         _quarto-share.yml _deck _vendor; do
  [ ! -e "$work/$f" ] || fail "the scaffold still ships $f (qd replaces it)"
done
grep -q 'qd export --pdf --out _output' "$work/Makefile" || fail "Makefile: make is not qd export --pdf"
grep -q -- '--notes' "$work/Makefile" && grep -q 'qd bib --zotero' "$work/Makefile" || fail "Makefile: notes or refs target"
grep -q '<!-- bibliography:start' "$work/presentation.qmd" && grep -q '<!-- bibliography:end' "$work/presentation.qmd" \
  || fail "presentation.qmd has no bibliography markers"

step "a new deck from the scaffold alone: make (qd export --pdf), make notes, qd check"
sc="$work-scaffold"; rm -rf "$sc"; mkdir -p "$sc"; cp -R "$skill/assets/." "$sc/"
# an equation with a step, and a full-bleed footer band marked .overflow-ok (qd's overflow check skips it)
python3 - "$sc/presentation.qmd" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace("Text.\n", "$$\\nabla^2 \\Phi = 4\\pi G\\rho \\class{fragment}{\\quad\\Rightarrow\\quad x}$$\n\n"
    '<div class="overflow-ok" style="position:absolute; left:-60px; right:-60px; bottom:-40px; height:30px; background:#3d4a5c"></div>\n'))
PY
(
  cd "$sc" || exit 1
  make -s > make.json || fail "make"
  [ "$(field make.json "d['ok'] and d['pdf']['pages'] > 0")" = True ] || fail "make: export not ok or no PDF"
  [ "$(field make.json "d['check']['problems']")" = "[]" ] || fail "make: qd export reports problems (the footer band?)"
  [ -f _output/presentation.html ] && [ -f _output/presentation.pdf ] || fail "make: _output/ lacks the deck or its PDF"
  make -s notes > notes.json && [ -f _output/presentation-notes.pdf ] || fail "make notes"
  qd check > check.json; [ "$(field check.json "d['ok']")" = True ] || fail "qd check on the scaffold deck"
  python3 "$here/offline_check.py" --webkit _output/presentation.html || fail "scaffold deck in WebKit"
  exit $status
) || status=1

step "the fixture decks beside it (qd export -d picks each one)"
cp -R "$here/fixture/." "$work/"
rm -rf "$work/gotchas"                            # rendered on their own below, not in the project
cd "$work" || exit 1
qd --version
# Test media and images, generated so nothing binary is committed.
ffmpeg -loglevel error -y -f lavfi -i "testsrc2=size=640x360:rate=24:duration=3" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart _talk/figures/clip.mp4
ffmpeg -loglevel error -y -f lavfi -i "sine=frequency=440:duration=2" _talk/figures/tone.mp3
ffmpeg -loglevel error -y -f lavfi -i "testsrc2=size=1280x720" -frames:v 1 _talk/apps/explorer.png
ffmpeg -loglevel error -y -f lavfi -i "smptebars=size=1280x720" -frames:v 1 _talk/apps/explorer-full.png
# An inline app over Chrome's 2 MB data: URL limit (lessons.qmd, #big-app), padded so nothing big is committed.
python3 -c "import pathlib; a = pathlib.Path('_talk/apps'); pathlib.Path(a, 'big.html').write_text(
    a.joinpath('background.html').read_text().replace('app ok', 'big app ok').replace('</body>', '<!--' + 'x' * 3_000_000 + '-->\\n</body>'))"
export QUARTO_PYTHON=${QUARTO_PYTHON:-$(command -v python3)}

step "qd export of the fixture decks (offline check, overflow check, size report in its JSON)"
for deck in demo lessons reveal-features; do
  qd export -d $deck.qmd --out "out-$deck" $([ $deck = demo ] && echo --pdf) > "$deck.json"
  [ "$(field "$deck.json" "d['ok']")" = True ] || { fail "qd export $deck"; field "$deck.json" "json.dumps(d.get('check', d), indent=1)[:3000]"; }
done

step "one MathJax, from qd's header (the scaffold vendors none), in demo.html"
mj=$(field demo.json "[a['path'] for a in d['assets'] if a['name'] == 'mathjax'][0]")
python3 - "$mj" out-demo/demo.html <<'PY' || fail "demo.html does not have exactly one MathJax"
import sys
mj, deck = (open(p, encoding="utf-8").read() for p in sys.argv[1:])
n = [deck.count(mj[int(len(mj) * f):][:300]) for f in (0.25, 0.5, 0.75)]
print("MathJax copies:", n); sys.exit(n != [1, 1, 1])
PY

step "WebKit: the exported decks make no requests, raise no errors, show no raw TeX"
python3 "$here/offline_check.py" --webkit out-demo/demo.html out-lessons/lessons.html || fail "offline check (WebKit)"

step "lessons.html alone in an empty folder: apps inlined (background iframe, data-app over 2 MB)"
solo="$work-solo"; rm -rf "$solo"; mkdir -p "$solo"; cp out-lessons/lessons.html "$solo/"
python3 "$here/lessons_check.py" "$solo/lessons.html" || fail "lessons check (Chromium)"
python3 "$here/lessons_check.py" "$solo/lessons.html" --webkit || fail "lessons check (WebKit)"
grep -q '<object data="data:image/svg+xml' "$solo/lessons.html" || fail "<object> not inlined"
grep -q '<image href="data:image/svg+xml' "$solo/lessons.html" || fail "SVG <image href> not inlined"
grep -q '<aside class="notes"' "$solo/lessons.html" || fail "archive copy lost its notes"
python3 -c "import base64, sys; b = base64.b64encode(open('_talk/apps/explorer.png', 'rb').read()).decode()
sys.exit(open(sys.argv[1]).read().count(b) != 1)" "$solo/lessons.html" || fail "image on two slides embedded twice"
# the 3 MB app is padding: gzipped it adds almost nothing (4 MB of base64 without gzip)
[ "$(wc -c < "$solo/lessons.html")" -lt 9000000 ] || fail "inlined apps are not gzipped"
[ "$(field lessons.json "len(d['check']['size']['largest']) > 0")" = True ] || fail "qd export reports no sizes"

step "overflow check: flags only #too-long in lessons.html, nothing in demo.html"
field lessons.json "'\n'.join(f\"{p['slide']}: {p['message']}\" for p in d['check']['problems'] if p['code'] == 'P_OVERFLOW')"
[ "$(field lessons.json "sorted({p['slide'] for p in d['check']['problems'] if p['code'] == 'P_OVERFLOW'})")" = "['too-long']" ] \
  || fail "overflow check: expected only #too-long"
[ "$(field demo.json "[p for p in d['check']['problems'] if p['code'] == 'P_OVERFLOW']")" = "[]" ] || fail "overflow in demo.html"

step "a copy to share: qd export --strip-notes"
qd export -d lessons.qmd --strip-notes --out out-share > share.json; [ "$(field share.json "d['ok']")" = True ] || fail "share export"
if grep -q '<aside class="notes' out-share/lessons.html; then fail "shared copy has speaker notes"; else echo "shared copy has no notes"; fi

step "PDF (qd export --pdf)"
# title, equation, equation with its fragment, plotly, app still = 5 pages; the still is the PDF's
# only raster image (math and Plotly print as vectors).
read -r pages images < <(python3 -c "
import re, sys; d = open(sys.argv[1], 'rb').read()
print(len(re.findall(rb'/Type\s*/Page[^s]', d)), len(re.findall(rb'/Subtype\s*/Image', d)))" out-demo/demo.pdf 2>/dev/null || echo "0 0")
echo "demo.pdf: $pages pages, $images raster images"
[ "$pages" -eq 5 ] || fail "demo.pdf has $pages pages, expected 5"
[ "$images" -ge 1 ] || fail "demo.pdf has no raster image: the app's print still is missing"
qd pdf --html out-demo/demo.html --notes > pdf-notes.json || fail "qd pdf --notes"
[ "$(field pdf-notes.json "d['pages']")" -gt "$pages" ] || fail "notes PDF has no notes pages"

step "feature table (reveal-features.qmd against the guide)"
cp -R _talk out-reveal-features/   # local preview links open files beside the deck
python3 "$here/feature_check.py" out-reveal-features/reveal-features.html "$work/out-features-shots" out-demo/demo.html \
  || fail "feature check differs from the guide"

step "documented gotchas still hold (plain Quarto; if one stops holding, update the guide)"
g="$work-gotchas"; rm -rf "$g"; mkdir -p "$g"; cp "$here"/fixture/gotchas/*.qmd "$g/"
( cd "$g" && quarto render katex.qmd >/dev/null 2>&1 ) || fail "katex.qmd did not render"
if python3 "$here/offline_check.py" "$g/katex.html" >/dev/null 2>&1; then
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
