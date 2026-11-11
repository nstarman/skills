"""Make a rendered deck truly one file: put its background-iframe apps and <object> files inside it.

    python inline_apps.py _output/talk.html                       # in place
    python inline_apps.py --strip-notes _share/talk.html          # shared copy: no speaker notes
    python inline_apps.py _output/talk.html -o talk-single.html
    python inline_apps.py --root talks talks/_output/a.html        # apps relative to talks/

Relative paths are looked up in the deck (source) folder: the current folder, or `--root DIR`. `embed-resources` leaves
`data-background-iframe="apps/x.html"` as a path, and pandoc never inlines `<object data=…>`.
Each app goes into the deck gzipped, as base64 in a `<script type="text/plain">`; a small script
unzips it (DecompressionStream, a few ms) into a `blob:` URL and points the slide (and any iframe
`src`/`data-src` with that path, including one reveal.js already loaded) at it. A `data:` URL would
be simpler but leaves many apps blank: a `data:` page has an opaque origin. `<object>` files become
`data:` URIs. A `data:` URI used more than once (pandoc embeds a file once per use) is kept once and
put back by a script. Exits 1 if a referenced file is missing.

For an app on a slide, write `<iframe data-app="apps/x.html">`, not `src`: `embed-resources` turns
`src` and `data-src` into `data:` URLs, and Chrome will not load a `data:` URL over 2 MB (the iframe
shows `about:blank#blocked`). Pandoc leaves `data-app` alone; the loader gives the iframe that
app's `blob:` URL as `data-src`, which reveal.js loads when the slide is shown.
"""
import argparse, base64, collections, gzip, html, json, mimetypes, pathlib, re, sys
from urllib.parse import unquote

BG = re.compile(r'data-background-iframe="([^"]+)"')
# data-app="apps/x.html": an app pandoc must not inline (it inlines src and data-src as data: URLs, and
# Chrome won't load a data: URL over 2 MB); it becomes the iframe's data-src, which reveal lazy-loads
IFRAME = re.compile(r'<iframe\b[^>]*?\b(?:data-src|src|data-app)="([^"]+)"')
OBJ = re.compile(r'''(<object\b[^>]*?\bdata=")([^"]+)(")''')
LOCALPATH = re.compile(r"^(?![a-z][a-z0-9+.-]*:|//|#)")   # no scheme, not protocol-relative, not #
NOTES = re.compile(r"""<aside\b[^>]*\bclass="(?:[^"]*\s)?notes(?:\s[^"]*)?"[^>]*>.*?</aside>""", re.S)
DONE = 'id="inlined-app-'   # a deck this script already inlined
# a data: URI in an attribute; pandoc embeds a file once per use, so an image on three slides is in the deck three times
DATAURI = re.compile(r'(?<![\w-])(data-src|src|poster|data|xlink:href|href)="(data:(?!\w+/javascript)[^"]{4000,})"')


def before_reveal(text, snippet):
    """Insert `snippet` before the script that calls Reveal.initialize (the last one: inlined libraries
    may mention it too), so it runs once the slides exist and before reveal.js reads them."""
    k = text.rfind("Reveal.initialize(")
    k = text.rfind("<script", 0, k) if k >= 0 else -1
    if k < 0:
        k = text.rfind("</body>")
    return text[:k] + snippet + text[k:]


def dedupe(text):
    """Keep each repeated data: URI once, in a <script type="text/plain">; a small script puts it back
    into its attributes before reveal.js starts."""
    counts = collections.Counter(m[2] for m in DATAURI.finditer(text))
    ids = {u: f"dup-{i}" for i, u in enumerate(u for u, n in counts.items() if n > 1)}
    if not ids:
        return text
    # xlink:href comes back as href, which SVG 2 reads the same
    text = DATAURI.sub(lambda m: f'data-dup-{m[1].removeprefix("xlink:")}="{ids[m[2]]}"' if m[2] in ids else m[0], text)
    holders = "".join(f'<script type="text/plain" id="{i}">{u}</script>\n' for u, i in ids.items())
    restore = r"""<script>(() => {
  for (const a of ["data-src", "src", "poster", "data", "href"]) {
    const d = "data-dup-" + a;
    document.querySelectorAll("[" + d + "]").forEach((e) => {
      e.setAttribute(a, document.getElementById(e.getAttribute(d)).textContent);
      e.removeAttribute(d);
    });
  }
})();</script>
"""
    return before_reveal(text, holders + restore)


def mime(f):
    return mimetypes.guess_type(f.name)[0] or "application/octet-stream"


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
        return f"{m[1]}data:{mime(f)};base64,{base64.b64encode(f.read_bytes()).decode()}{m[3]}"
    text = OBJ.sub(obj, text)
    text = dedupe(text)

    if DONE in text:   # already inlined: running again would embed every app a second time
        return text, missing
    markup = re.sub(r"<script\b.*?</script>", "", text, flags=re.S | re.I)   # inlined libraries hold `<iframe src="${…}">`
    found = BG.findall(markup) + IFRAME.findall(markup)
    apps = list(dict.fromkeys(p for p in map(html.unescape, found) if LOCALPATH.match(p)))
    blobs = []
    for i, path in enumerate(apps):
        f = file_for(root, path)
        if not f.is_file():
            missing.append(path); continue
        blobs.append((i, (path, mime(f)), base64.b64encode(gzip.compress(f.read_bytes(), 9, mtime=0)).decode()))
    if blobs:
        data = "".join(f'<script type="text/plain" id="inlined-app-{i}">{b}</script>\n' for i, _, b in blobs)
        paths = {f"inlined-app-{i}": p for i, p, _ in blobs}
        loader = data + "<script>(() => {\n" + f"  const apps = {json.dumps(paths)};\n" + r"""
  for (const [id, [path, type]] of Object.entries(apps)) {
    const gz = Uint8Array.from(atob(document.getElementById(id).textContent), (c) => c.charCodeAt(0));
    new Response(new Blob([gz]).stream().pipeThrough(new DecompressionStream("gzip"))).blob().then((b) => {
      const url = URL.createObjectURL(new Blob([b], { type }));
      document.querySelectorAll("[data-background-iframe]").forEach((e) => {
        if (e.getAttribute("data-background-iframe") === path) e.setAttribute("data-background-iframe", url);
      });
      document.querySelectorAll("iframe").forEach((f) => {
        if (![f.getAttribute("data-app"), f.getAttribute("data-src"), f.getAttribute("src")].includes(path)) return;
        f.setAttribute("data-src", url);
        // reveal.js got there first (the deck opened on this slide): load it now
        if (f.getAttribute("src") === path || (!f.getAttribute("src") && f.closest("section.present"))) f.setAttribute("src", url);
      });
    });
  }
})();</script>
"""
        text = before_reveal(text, loader)   # before reveal.js creates the background iframes
    return text, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deck")
    ap.add_argument("-o", "--output", help="write here instead of in place")
    ap.add_argument("--root", default=".", help="folder the deck's relative paths start from (default: here)")
    ap.add_argument("--strip-notes", action="store_true", help="remove speaker notes (shared copy)")
    a = ap.parse_args(argv)
    src = pathlib.Path(a.deck)
    text, missing = inline(src.read_text(encoding="utf-8"), pathlib.Path(a.root), strip_notes=a.strip_notes)
    out = pathlib.Path(a.output or src)
    out.write_text(text, encoding="utf-8")
    for m in missing:
        print(f"missing file (left as a path): {m}", file=sys.stderr)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
