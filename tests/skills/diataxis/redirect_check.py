"""Check that redirect pages resolve inside a built site: every target they name (the
meta-refresh URL, and each entry of a per-anchor map) is a page of the site, and its #fragment
is an id on that page. Works for make_redirect_stubs.py's stubs and for the pages rediraffe,
sphinx-reredirects and Zensical's redirects plugin write.

    python3 redirect_check.py <site root> <redirect page>...   (paths relative to the root)

Exits 1 if a redirect page is missing or any target does not resolve.
"""
import html, json, re, sys
from pathlib import Path

REFRESH = re.compile(r"""http-equiv=["']refresh["']\s+content=["']\d+;\s*url=([^"']+)["']""", re.I)
ANCHOR_MAP = re.compile(r"(?:ANCHORS|redirects)\s*=\s*(\{.*?\})", re.S)


def resolve(root: Path, page: Path, url: str) -> str | None:
    """None if url resolves, else what is wrong."""
    path, _, frag = url.partition("#")
    target = (root / path.lstrip("/") if path.startswith("/") else page.parent / path).resolve()
    if path.endswith("/") or not target.suffix:
        target = target / "index.html"
    if not target.is_file():
        return f"{url}: no page {target.relative_to(root) if target.is_relative_to(root) else target}"
    if frag and not re.search(rf"""\bid=["']{re.escape(frag)}["']""", target.read_text(errors="replace")):
        return f"{url}: no id {frag!r} on {target.relative_to(root)}"
    return None


root, bad = Path(sys.argv[1]).resolve(), 0
for rel in sys.argv[2:]:
    page = root / rel
    if not page.is_file():
        print(f"  {rel}: redirect page not written"); bad += 1; continue
    text = html.unescape(page.read_text(errors="replace"))
    urls = REFRESH.findall(text)
    for m in ANCHOR_MAP.findall(text):
        urls += json.loads(m).values()
    if not urls:
        print(f"  {rel}: no redirect target found"); bad += 1
    for url in dict.fromkeys(urls):
        err = resolve(root, page, url)
        print(f"  {rel} -> {url}: {'ok' if err is None else 'BROKEN, ' + err}")
        bad += err is not None
sys.exit(1 if bad else 0)
