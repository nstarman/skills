"""Print a self-contained reveal.js deck to PDF, with the network blocked.

    python make_pdf.py talk.html            # -> talk.pdf

Needs `pip install playwright`, and Google Chrome or `python -m playwright install chromium`
(Chromium only: WebKit cannot print to PDF). Runs headless (no window). Blocking the network doubles
as a check: if a slide needs the internet, the PDF shows it.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright


def launch(p):
    """Headless only: never a visible window. Google Chrome if installed, else Playwright's Chromium."""
    try:
        return p.chromium.launch(headless=True, channel="chrome")
    except Exception:
        return p.chromium.launch(headless=True)   # `python -m playwright install chromium`

html = pathlib.Path(sys.argv[1]).resolve()
with sync_playwright() as p:
    ctx = launch(p).new_context(offline=True)
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else r.abort())
    page = ctx.new_page()
    page.goto(html.as_uri() + "?print-pdf&showNotes=separate-page")  # notes in the PDF only
    page.wait_for_function("typeof Reveal !== 'undefined' && Reveal.isReady()", timeout=30000)
    page.wait_for_timeout(3000)  # MathJax and Plotly finish after reveal.js is ready
    # reveal.js's print view declares the page size (@page: slide size plus margin); use it as is.
    page.pdf(path=html.with_suffix(".pdf"), prefer_css_page_size=True, print_background=True)
print("wrote", html.with_suffix(".pdf"))
