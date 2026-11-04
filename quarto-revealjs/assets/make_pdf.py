"""Print a self-contained reveal.js deck to PDF, with the network blocked.

    python make_pdf.py talk.html            # -> talk.pdf

Needs `pip install playwright` and Google Chrome. Blocking the network doubles
as a check: if a slide needs the internet, the PDF shows it.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

html = pathlib.Path(sys.argv[1]).resolve()
with sync_playwright() as p:
    ctx = p.chromium.launch(channel="chrome").new_context(offline=True)
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else r.abort())
    page = ctx.new_page()
    page.goto(html.as_uri() + "?print-pdf&showNotes=separate-page")  # notes in the PDF only
    page.wait_for_function("typeof Reveal !== 'undefined' && Reveal.isReady()", timeout=30000)
    page.wait_for_timeout(3000)  # MathJax and Plotly finish after reveal.js is ready
    # reveal.js's print view declares the page size (@page: slide size plus margin); use it as is.
    page.pdf(path=html.with_suffix(".pdf"), prefer_css_page_size=True, print_background=True)
print("wrote", html.with_suffix(".pdf"))
