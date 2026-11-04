"""Open rendered reveal.js decks with the network blocked and report what would break offline.

    python check_offline.py _output/*.html

Needs `pip install playwright` and Google Chrome. For each deck it prints the requests that tried
to leave the machine, page errors, and whether math rendered. Exits 1 if any deck has a problem.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

LOCAL = ("file:", "data:", "blob:", "about:")
bad = False
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    for arg in sys.argv[1:]:
        ctx = browser.new_context(offline=True)
        blocked, errors = [], []
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(LOCAL)
                  else (blocked.append(r.request.url), r.abort()))
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e).splitlines()[0]))
        page.goto(pathlib.Path(arg).resolve().as_uri())
        page.wait_for_timeout(4000)
        state = page.evaluate("""() => ({
          ready: typeof Reveal !== 'undefined' && Reveal.isReady(),
          slides: typeof Reveal !== 'undefined' ? Reveal.getTotalSlides() : 0,
          math: document.querySelectorAll('mjx-container').length,
          rawTeX: [...document.querySelectorAll('span.math')].filter(s => !s.querySelector('mjx-container, .katex, math')).length,
        })""")
        ok = state["ready"] and not blocked and not errors and not state["rawTeX"]
        bad |= not ok
        print(f"{'OK  ' if ok else 'FAIL'} {arg}: {state['slides']} slides, {state['math']} equations rendered,"
              f" {state['rawTeX']} left as raw TeX")
        for u in blocked:
            print(f"     network request: {u[:110]}")
        for e in errors:
            print(f"     page error: {e[:110]}")
        ctx.close()
sys.exit(1 if bad else 0)
