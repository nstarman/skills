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
    page.wait_for_timeout(5000)  # fixed wait for MathJax/Plotly; poll a ready flag if decks get heavy
    w, h = page.evaluate("[Reveal.getConfig().width, Reveal.getConfig().height]")
    page.pdf(path=html.with_suffix(".pdf"), width=f"{w}px", height=f"{h}px", print_background=True)
print("wrote", html.with_suffix(".pdf"))
