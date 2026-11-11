"""List the largest things embedded in a one-file deck, to see where its megabytes go.

    python size_report.py _output/presentation.html [N]   # the N largest (default 15)

Each line: size in the file (base64 included), kind, and the text just before it (alt text, an id).
"""
import json, re, sys

text = open(sys.argv[1], encoding="utf-8").read()
items = []
apps = re.search(r"const apps = (\{.*?\});", text)   # inline_apps.py's id -> [path, type]
apps = {k: v[0] for k, v in json.loads(apps[1]).items()} if apps else {}
for m in re.finditer(r"data:([\w/+.-]+);base64,[A-Za-z0-9+/=]{20000,}", text):
    ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 160):m.start()])
    items.append((m.end() - m.start(), m[1], ctx[-80:]))
for chunk in text.split("</script>"):
    m = re.search(r"<script([^>]*)>(.*)\Z", chunk, re.S)
    if m and len(m[2]) > 20000 and not m[2].startswith("data:"):   # a holder of one data: URI is listed above
        app = re.search(r'id="(inlined-app-\d+)"', m[1])
        items.append((len(m[2]), f"app {apps.get(app[1], app[1])} (gzip)" if app else "script",
                      "" if app else m[2][:60].replace("\n", " ")))
items.sort(reverse=True)
print(f"{len(text) / 1e6:.1f} MB in all; the largest parts:")
for n, kind, ctx in items[: int(sys.argv[2]) if len(sys.argv) > 2 else 15]:
    print(f"{n / 1e6:6.2f} MB  {kind[:40]:40s}  {ctx}")
