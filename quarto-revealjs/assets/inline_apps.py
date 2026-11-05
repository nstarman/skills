"""Make a rendered deck truly one file: put its background-iframe apps and <object> files inside it.

    python inline_apps.py _output/talk.html                       # in place
    python inline_apps.py --strip-notes _share/talk.html          # shared copy: no speaker notes
    python inline_apps.py _output/talk.html -o talk-single.html

Run from the deck folder: relative paths are looked up there. `embed-resources` leaves
`data-background-iframe="apps/x.html"` as a path, and pandoc never inlines `<object data=…>`.
Each app goes into the deck as base64 in a `<script type="text/plain">`; a small script turns it
into a `blob:` URL before reveal.js starts and points the slide (and any iframe `src`/`data-src`
with that path) at it. A `data:` URL would be simpler but leaves many apps blank: a `data:` page
has an opaque origin. `<object>` files become `data:` URIs. Exits 1 if a referenced file is missing.
"""
import argparse, base64, html, json, mimetypes, pathlib, re, sys
from urllib.parse import unquote

BG = re.compile(r'data-background-iframe="([^"]+)"')
IFRAME = re.compile(r'<iframe\b[^>]*?\b(?:data-src|src)="([^"]+)"')
OBJ = re.compile(r'''(<object\b[^>]*?\bdata=")([^"]+)(")''')
LOCALPATH = re.compile(r"^(?![a-z][a-z0-9+.-]*:|//|#)")   # no scheme, not protocol-relative, not #
NOTES = re.compile(r"""<aside\b[^>]*\bclass="(?:[^"]*\s)?notes(?:\s[^"]*)?"[^>]*>.*?</aside>""", re.S)
DONE = 'id="inlined-app-'   # a deck this script already inlined


def file_for(root, path):
    """The file a relative URL points at: without ?query/#hash, %-decoded."""
    return root / unquote(re.split(r"[?#]", path, maxsplit=1)[0])


def inline(text, root=pathlib.Path("."), strip_notes=False):
    """Return (new_html, missing_paths)."""
    missing = []
    if strip_notes:
        text = NOTES.sub("", text)

    def obj(m):
        path = html.unescape(m[2])
        if not LOCALPATH.match(path):
            return m[0]
        f = file_for(root, path)
        if not f.is_file():
            missing.append(path); return m[0]
        mime = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        return f"{m[1]}data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}{m[3]}"
    text = OBJ.sub(obj, text)

    if DONE in text:   # already inlined: running again would embed every app a second time
        return text, missing
    markup = re.sub(r"<script\b.*?</script>", "", text, flags=re.S)   # inlined libraries hold `<iframe src="${…}">`
    found = BG.findall(markup) + IFRAME.findall(markup)
    apps = list(dict.fromkeys(p for p in map(html.unescape, found) if LOCALPATH.match(p)))
    blobs = []
    for i, path in enumerate(apps):
        f = file_for(root, path)
        if not f.is_file():
            missing.append(path); continue
        blobs.append((i, path, base64.b64encode(f.read_bytes()).decode()))
    if blobs:
        data = "".join(f'<script type="text/plain" id="inlined-app-{i}">{b}</script>\n' for i, _, b in blobs)
        paths = {f"inlined-app-{i}": p for i, p, _ in blobs}
        loader = data + "<script>(() => {\n" + f"  const apps = {json.dumps(paths)};\n" + r"""
  for (const [id, path] of Object.entries(apps)) {
    const b = atob(document.getElementById(id).textContent);
    const url = URL.createObjectURL(new Blob([Uint8Array.from(b, (c) => c.charCodeAt(0))], { type: "text/html" }));
    document.querySelectorAll("[data-background-iframe]").forEach((e) => {
      if (e.getAttribute("data-background-iframe") === path) e.setAttribute("data-background-iframe", url);
    });
    document.querySelectorAll("iframe").forEach((f) => {
      if (f.getAttribute("data-src") === path) f.setAttribute("data-src", url);
      if (f.getAttribute("src") === path) f.setAttribute("src", url);
    });
  }
})();</script>
"""
        # Before reveal.js starts (it creates background iframes at init), i.e. before the script
        # that calls Reveal.initialize; the last one, as inlined libraries may mention it too.
        k = text.rfind("Reveal.initialize(")
        k = text.rfind("<script", 0, k) if k >= 0 else -1
        if k < 0:
            k = text.rfind("</body>")
        text = text[:k] + loader + text[k:]
    return text, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deck")
    ap.add_argument("-o", "--output", help="write here instead of in place")
    ap.add_argument("--strip-notes", action="store_true", help="remove speaker notes (shared copy)")
    a = ap.parse_args(argv)
    src = pathlib.Path(a.deck)
    text, missing = inline(src.read_text(encoding="utf-8"), strip_notes=a.strip_notes)
    out = pathlib.Path(a.output or src)
    out.write_text(text, encoding="utf-8")
    for m in missing:
        print(f"missing file (left as a path): {m}", file=sys.stderr)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
