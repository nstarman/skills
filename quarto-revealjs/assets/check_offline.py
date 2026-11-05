"""Open rendered reveal.js decks with the network blocked and report what would break offline.

    python check_offline.py _output/*.html
    python check_offline.py --webkit _output/*.html     # Safari's engine

Needs `pip install playwright`, and Google Chrome or `python -m playwright install chromium webkit`.
Runs headless (no window). For each deck it prints requests that tried to
leave the machine, local files that are missing (e.g. a background video not shipped beside the
deck), page errors, and math left as raw TeX. Exits 1 if any deck has a problem.
"""
import pathlib, sys
from urllib.parse import urlparse, unquote
from urllib.request import url2pathname
from playwright.sync_api import sync_playwright


def launch(p, webkit=False):
    """Headless only: never a visible window. Google Chrome if installed, else Playwright's Chromium."""
    if webkit:
        return p.webkit.launch(headless=True)
    try:
        return p.chromium.launch(headless=True, channel="chrome")
    except Exception:
        return p.chromium.launch(headless=True)   # `python -m playwright install chromium`

LOCAL = ("file:", "data:", "blob:", "about:")   # about:blank is the math plugin's disabled URL
webkit = "--webkit" in sys.argv
decks = [a for a in sys.argv[1:] if a != "--webkit"]
bad = False
with sync_playwright() as p:
    browser = launch(p, webkit)
    for arg in decks:
        ctx = browser.new_context(offline=True)
        blocked, missing, errors = [], [], []
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(LOCAL)
                  else (blocked.append(r.request.url), r.abort()))
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e).splitlines()[0]))
        # A failed file: request is a problem only if the file is really absent (media requests are
        # also cancelled, harmlessly, when a slide's video unloads).
        page.on("requestfailed", lambda r: r.url.startswith("file:")
                and not pathlib.Path(url2pathname(unquote(urlparse(r.url).path))).exists()
                and missing.append(r.url))
        page.goto(pathlib.Path(arg).resolve().as_uri())
        try:
            page.wait_for_function("typeof Reveal !== 'undefined' && Reveal.isReady()", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)   # MathJax typesets after load
        state = page.evaluate(r"""() => {
          const text = document.querySelector('.reveal .slides')?.innerText || '';
          return {
            ready: typeof Reveal !== 'undefined' && Reveal.isReady(),
            slides: typeof Reveal !== 'undefined' ? Reveal.getTotalSlides() : 0,
            math: document.querySelectorAll('mjx-container').length,
            rawTeX: /\\\(|\\\[|\$\$/.test(text),
          };
        }""")
        # Background media and iframes load only near their slide: visit every slide.
        if state["ready"]:
            for i in range(state["slides"]):
                page.evaluate(f"Reveal.slide(...Object.values(Reveal.getIndices(Reveal.getSlides()[{i}])).slice(0, 2))")
                page.wait_for_timeout(150)
            page.wait_for_timeout(1000)
        ok = state["ready"] and not (blocked or missing or errors or state["rawTeX"])
        bad |= not ok
        print(f"{'OK  ' if ok else 'FAIL'} {arg}: {state['slides']} slides, {state['math']} equations rendered"
              f"{', raw TeX on the page' if state['rawTeX'] else ''}{'' if state['ready'] else ', reveal.js did not start'}")
        for u in blocked:
            print(f"     network request: {u[:110]}")
        for u in missing:
            print(f"     missing local file: {unquote(u)[-110:]}")
        for e in errors:
            print(f"     page error: {e[:110]}")
        ctx.close()
sys.exit(1 if bad else 0)
