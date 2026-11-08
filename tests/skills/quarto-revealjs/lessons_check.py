"""Check the lessons fixture in a rendered deck, offline and headless.

    python lessons_check.py DECK.html [--webkit]

The background-iframe app runs from a blob: URL (nothing beside the deck), so does the
data-app iframe over 2 MB, only once its slide is shown; the
"]" key skips to a slide's last step and then on and is listed under "?", and both citation forms render as links.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

deck = pathlib.Path(sys.argv[1]).resolve()
webkit = "--webkit" in sys.argv
fails = []
with sync_playwright() as p:
    if webkit:
        browser = p.webkit.launch(headless=True)
    else:
        try:
            browser = p.chromium.launch(headless=True, channel="chrome")
        except Exception:
            browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(offline=True, viewport={"width": 1280, "height": 800})
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:", "about:"))
              else r.abort())
    pg = ctx.new_page()
    pg.goto(deck.as_uri())
    pg.wait_for_function("typeof Reveal !== 'undefined' && Reveal.isReady()", timeout=15000)

    def go(i):
        pg.evaluate(f"Reveal.slide(...Object.values(Reveal.getIndices(document.getElementById('{i}'))).slice(0,2))")
        pg.wait_for_timeout(1200)

    go("steps")
    pg.keyboard.press("BracketRight"); pg.wait_for_timeout(300)
    f, last = pg.evaluate("[Reveal.getIndices().f, Reveal.getCurrentSlide().id]")
    if (f, last) != (2, "steps"):
        fails.append(f'"]" on #steps went to fragment {f} of #{last}, expected the last (2)')
    pg.keyboard.press("BracketRight"); pg.wait_for_timeout(1200)
    if pg.evaluate("Reveal.getCurrentSlide().id") == "steps":
        fails.append('"]" at the last step did not move on')

    pg.evaluate("Reveal.toggleHelp(true)"); pg.wait_for_timeout(300)
    if "Skip to the last step" not in pg.evaluate("document.body.innerText"):
        fails.append('"]" is not listed in the ? help overlay')
    pg.evaluate("Reveal.toggleHelp(false)")

    big = "document.querySelector('#big-app iframe')"
    src, lazy = pg.evaluate(f"[{big}.getAttribute('src'), {big}.getAttribute('data-src')]")
    if src or not (lazy or "").startswith("blob:"):
        fails.append(f"data-app iframe before its slide: src {src!r}, data-src {(lazy or '')[:30]!r} (want none, blob:)")
    go("big-app")
    ok = None
    for _ in range(20):
        try:
            ok = [f.evaluate("document.getElementById('msg').textContent") for f in pg.frames if f.url == lazy]
        except Exception as e:
            ok = str(e).splitlines()[0]
        if ok == ["big app ok"]:
            break
        pg.wait_for_timeout(250)
    else:
        fails.append(f"data-app iframe over 2 MB did not run from its blob: URL: {ok}; frames {[f.url[:30] for f in pg.frames]}")

    go("full-app")
    ok = None
    for _ in range(20):
        blobs = [f for f in pg.frames if f.url.startswith("blob:")]
        try:
            ok = blobs and blobs[0].evaluate("window.__ok === true && document.getElementById('msg').textContent")
        except Exception as e:
            ok = str(e).splitlines()[0]
        if ok == "app ok":
            break
        pg.wait_for_timeout(250)
    else:
        fails.append(f"background-iframe app did not load from a blob: URL: {ok}; frames {[f.url[:30] for f in pg.frames]}")

    links = pg.evaluate("""[...document.querySelectorAll('#cite a.paper-ref')].map(a =>
        [a.getAttribute('href'), a.classList.contains('paper-corner'), a.innerText.trim(),
         !!a.querySelector('.paper-icon'), a.getAttribute('title')])""")
    want = [["https://doi.org/10.1000/one", True, "", True, "Author et al. (2020): A paper"],
            ["https://doi.org/10.1000/two", False, "Other & Second (2021)", True, "Other & Second (2021): Another paper"]]
    if links != want:
        fails.append(f"citations: {links}")
    browser.close()

for m in fails:
    print("FAIL", m)
print(f"lessons check ({'webkit' if webkit else 'chromium'}): {'FAILED' if fails else 'OK'}")
sys.exit(1 if fails else 0)
