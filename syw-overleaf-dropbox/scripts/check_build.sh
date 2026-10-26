#!/usr/bin/env sh
# Post-build checks for a showyourwork repo that mirrors Overleaf through Dropbox.
#
# Usage (from the repository root):
#     sh check_build.sh "<path to the Dropbox mirror folder>" [build.log]
#
# Reports: whether the log ended with a push, any cited \variable{} files that are missing,
# figures that differ between the repo and the mirror, and the PDF's page count.
set -u
MIRROR="${1:?usage: check_build.sh <mirror folder> [build.log]}"
LOG="${2:-}"

if [ -n "$LOG" ]; then
    if grep -q "Pushing changes to Overleaf" "$LOG" && grep -q "^Done!" "$LOG"; then
        echo "log: pushed to Overleaf"
    else
        echo "log: NO PUSH found (nothing ran, or it failed): check for a stale hand-made PDF"
    fi
fi

missing=0
for p in $(grep -o '\\variable{[^}]*}' src/tex/ms.tex | sed 's/\\variable{//;s/}//' | sort -u); do
    [ -f "src/tex/$p" ] || { echo "MISSING variable file: $p"; missing=1; }
done
[ "$missing" = 0 ] && echo "variables: none missing"

hash_of() {  # md5 on macOS, md5sum elsewhere; prints nothing for a missing file
    [ -f "$1" ] || return 0
    md5 -q "$1" 2>/dev/null || md5sum "$1" | cut -d' ' -f1
}

# Figures in subfolders too (figures/GD1/a.pdf), compared by path relative to figures/.
figs=$(find src/tex/figures -name '*.pdf' 2>/dev/null | sort)
[ -z "$figs" ] && echo "figures: no PDFs in src/tex/figures"
echo "$figs" | while IFS= read -r f; do
    [ -n "$f" ] || continue
    name=${f#src/tex/figures/}
    a=$(hash_of "$f")
    b=$(hash_of "$MIRROR/figures/$name")
    if [ -z "$b" ]; then
        echo "figure $name: ABSENT from mirror (Dropbox lag? wait and recheck)"
    elif [ "$a" = "$b" ]; then
        echo "figure $name: same as mirror"
    else
        echo "figure $name: DIFFERENT from mirror (Dropbox lag? wait and recheck)"
    fi
done

command -v pdfinfo >/dev/null && pdfinfo ms.pdf 2>/dev/null | grep Pages
