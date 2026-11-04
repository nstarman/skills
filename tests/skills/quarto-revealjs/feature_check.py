"""Drive every reveal.js feature in fixture/reveal-features.qmd, offline, and compare with the guide.

    python feature_check.py _output/reveal-features.html <out-dir> [_output/demo.html]

Each check prints PASS or FAIL. EXPECTED_FAIL lists what the guide documents as not working in the
tested Quarto/reveal.js versions; such a check must *return* False. The run fails (exit 1) when any
result differs from the guide, in either direction (a documented limitation that now works means
the guide is out of date), when an expected-to-fail check crashes instead (it no longer tests
anything), or when any page used the network or raised an error. Screenshots go to <out-dir>.
"""
import json, pathlib, re, sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# The guide's ✗ and ◐-without-workaround rows (quarto-revealjs/references/quarto-revealjs-guide.md).
EXPECTED_FAIL = {
    "Lightbox: reveal native",   # data-preview-image is reveal.js 5.2+
    "Links: preview overlay",    # preview links only for http/www URLs
}
LOCAL = ("file:", "data:", "blob:", "about:")

deck = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
demo = pathlib.Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None
URL = deck.as_uri()
results, blocked, errors = [], [], []   # results: (name, ok, crashed, detail)


def check(name, fn):
    try:
        ok, detail = fn(); crashed = False
    except Exception as e:
        ok, crashed, detail = False, True, f"error: {str(e).splitlines()[0][:120]}"
    results.append((name, bool(ok), crashed, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name:30s} {detail}", flush=True)


def until(page, js, timeout=8000):
    """Wait until the JS expression is truthy; False on timeout."""
    try:
        page.wait_for_function(js, timeout=timeout); return True
    except PWTimeout:
        return False


def frame(page, suffix, js, timeout=8000):
    """The value of js in the first frame whose URL ends with suffix, once it is truthy."""
    for _ in range(timeout // 250):
        for f in page.frames:
            if f.url.endswith(suffix):
                try:
                    v = f.evaluate(js)
                    if v: return v
                except Exception:
                    pass
        page.wait_for_timeout(250)
    return None


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")

    def new_ctx(**kw):
        c = browser.new_context(offline=True, viewport={"width": 1280, "height": 800}, **kw)
        c.route("**/*", lambda r: r.continue_() if r.request.url.startswith(LOCAL)
                else (blocked.append(r.request.url), r.abort()))
        c.on("page", lambda pg_: pg_.on("pageerror", lambda e: errors.append(f"{pg_.url[-30:]}: {str(e)[:150]}")))
        return c

    ctx = new_ctx(has_touch=True)
    pg = ctx.new_page(); pg.goto(URL); until(pg, "typeof Reveal !== 'undefined' && Reveal.isReady()", 15000)
    ev = pg.evaluate

    def ensure():
        if not pg.url.startswith(URL) or not ev("typeof Reveal !== 'undefined'"):
            pg.goto(URL); until(pg, "typeof Reveal !== 'undefined' && Reveal.isReady()", 15000)

    def go(i):
        ensure()
        ev(f"Reveal.slide(...Object.values(Reveal.getIndices(document.getElementById('{i}'))).slice(0,2))")
        until(pg, f"Reveal.getCurrentSlide().id === '{i}'", 4000); pg.wait_for_timeout(700)  # + transition

    cur = lambda: ev("Reveal.getCurrentSlide().id")
    key = lambda k: (pg.keyboard.press(k), pg.wait_for_timeout(900))
    bgimg = ("(() => { const b = Reveal.getSlideBackground(Reveal.getCurrentSlide());"
             " return getComputedStyle(b).backgroundImage + ' ' + getComputedStyle(b.querySelector('.slide-background-content')).backgroundImage; })()")

    # ---- Content
    check("Markup / raw HTML", lambda: (ev("!!document.querySelector('.raw-html-test')"), "raw HTML block rendered"))
    def bgcolour():
        go("bg-colour"); c = ev("getComputedStyle(Reveal.getSlideBackground(Reveal.getCurrentSlide())).backgroundColor")
        return c == "rgb(11, 29, 58)", c
    check("Background: colour", bgcolour)
    def bgiframe():
        go("bg-iframe"); n = frame(pg, "explorer.html", "window.__draws || 0")
        return bool(n), f"background app drew {n} times"
    check("Background: iframe", bgiframe)
    def bggrad():
        go("bg-gradient"); s = ev(bgimg); return "linear-gradient" in s, s[:50]
    check("Background: gradient", bggrad)
    def bgimage():
        go("bg-image"); s = ev(bgimg); return 'url("data:image' in s, "inlined data URI" if 'data:image' in s else s[:60]
    check("Background: image", bgimage)
    def bgvid():
        go("bg-video")
        ok = until(pg, "(() => { const v = document.querySelector('.slide-background.present video'); return v && v.readyState >= 2 && !v.paused; })()")
        return ok, "video loaded and playing" if ok else "video did not play"
    check("Background: video", bgvid)
    check("Parallax background", lambda: ("explorer" in ev("document.querySelector('.reveal .backgrounds').style.backgroundImage"),
                                         ev("document.querySelector('.reveal .backgrounds').style.backgroundImage")[:60]))
    def media():
        go("media")
        ok = until(pg, "(() => { const v = document.querySelector('video'), a = document.querySelector('.audio-test');"
                       " return v && v.readyState >= 1 && a.readyState >= 1; })()")
        lz = ev("(document.querySelector('.lazy-test').getAttribute('src')||'').slice(0,15)")
        return ok and lz.startswith("data:image"), f"video/audio loaded={ok}, lazy img src={lz}"
    check("Media (video, audio, lazy)", media)
    def qlightbox():
        go("lightbox"); pg.locator("a.lightbox").first.click()
        ok = until(pg, "!!document.querySelector('.glightbox-container, .gcontainer')", 5000)
        pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
        return ok, "Quarto lightbox (GLightbox) opened"
    check("Lightbox: Quarto .lightbox", qlightbox)
    def nlightbox():
        go("lightbox"); pg.locator("img.native-lightbox").click(timeout=5000)
        ok = until(pg, "!!document.querySelector('.r-overlay, .overlay')", 2000)
        if ok: pg.keyboard.press("Escape")
        return ok, "reveal.js 5.2+ data-preview-image overlay"
    check("Lightbox: reveal native", nlightbox)
    def preview():
        go("lightbox"); pg.locator("a.preview-test").click(timeout=5000); pg.wait_for_timeout(1500)
        if not pg.url.startswith(URL): return False, f"click navigated the page to {pg.url[-30:]}"
        ok = ev("!!document.querySelector('.r-overlay iframe, .overlay iframe')")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
        return ok, "preview-link opens the app in an overlay iframe"
    check("Links: preview overlay", preview)
    def preview_local():
        go("lightbox"); pg.locator("a.preview-local").click()
        n = frame(pg, "explorer.html", "window.__draws || 0") if pg.url.startswith(URL) else None
        if n: pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
        return bool(n), f"local app in overlay, drew {n} times"
    check("Links: preview (local file)", preview_local)
    def code():
        go("code"); n = ev("Reveal.getCurrentSlide().querySelectorAll('.fragment').length"); steps = []
        for _ in range(3):
            key("ArrowRight"); steps.append(ev("Reveal.getIndices().f"))
        return (n >= 2 and steps[:2] == [0, 1]), f"{n} highlight steps; fragment index per key press {steps}"
    check("Code line stepping", code)
    check("Math", lambda: (go("math") or ev("document.querySelectorAll('#math mjx-container').length") > 0, "MathJax SVG"))
    def frags():
        go("fragments"); order = []
        for _ in range(6):
            key("ArrowRight")
            order.append(ev("Reveal.getCurrentSlide().querySelector('.fragment.current-fragment')?.textContent.trim().split(/\\s+/)[0] || ''"))
        return order[:3] == ["fade-left,", "strike,", "fade-up,"] and order[-1] == "nested", f"shown in order {order}"
    check("Fragments + fragment-index", frags)
    def links():
        go("links"); pg.locator("a.internal-link").click(); pg.wait_for_timeout(1200); a = cur()
        go("links"); pg.locator("a.navigate-next").click(); pg.wait_for_timeout(1200); b = cur()
        go("links"); pg.locator("button.btn-next").click(); pg.wait_for_timeout(1200); c2 = cur()
        ok = a == "layout" and b == "title-slide" and c2 == "layout"   # the guide: <a href="#"> jumps to the title
        return ok, f"[..](#layout) -> {a}; <a href='#' class=navigate-next> -> {b}; <button class=navigate-next> -> {c2}"
    check("Links: internal + navigate-*", links)
    def hashlink():
        h = ev("document.querySelector('a.hash-link').getAttribute('href')")
        return h == "#//layout", f"[..](#/layout) is written as href={h!r} (the guide's gotcha)"
    check("Links: #/id rewritten (gotcha)", hashlink)
    def layout():
        go("layout")
        fs = ev("parseFloat(getComputedStyle(document.querySelector('.r-fit-text')).fontSize)")
        stack = ev("getComputedStyle(document.querySelector('.r-stack')).display")
        ab = ev("(() => { const e = document.querySelector('.abs-test'); return [e.style.top, e.style.left]; })()")
        return fs > 100 and stack == "grid" and ab == ["600px", "1000px"], f"r-fit-text {fs:.0f}px, r-stack display={stack}, absolute={ab}"
    check("Layout (r-stack, r-fit-text, .absolute)", layout)
    check("Slide visibility: hidden", lambda: (ev("!document.getElementById('hidden')"), "hidden slide removed"))
    def uncounted():
        go("last"); num = ev("document.querySelector('.slide-number').textContent.replace(/\\s+/g, '')")
        total = ev("document.querySelectorAll('.reveal .slides section:not(.stack)').length")
        return int(num.split("/")[1]) < total, f"last slide '{num}', {total} slides in the page (uncounted ones left out)"
    check("Slide visibility: uncounted", uncounted)

    # ---- Customization
    check("Presentation size", lambda: (ev("[Reveal.getConfig().width, Reveal.getConfig().height]") == [1280, 720], "1280x720 from YAML"))
    check("Transition per slide", lambda: (ev("document.getElementById('trans').dataset.transition") == "convex",
                                          "data-transition=convex, speed=" + ev("document.getElementById('trans').dataset.transitionSpeed")))

    # ---- Features
    check("Vertical slides", lambda: (ev("(() => { const a = Reveal.getIndices(document.getElementById('features')), "
                                         "b = Reveal.getIndices(document.getElementById('vertical')); return a.h === b.h && b.v === 1; })()"),
                                      "'Features' column, child at v=1"))
    def autoanim():
        go("aa1"); key("ArrowDown")
        return cur() == "aa2", "moved to the auto-animate pair (morph runs via CSS)"
    check("Auto-animate", autoanim)
    def autoslide():
        go("autoslide"); ok = until(pg, "Reveal.getCurrentSlide().id !== 'autoslide'", 6000)
        return ok, f"now on '{cur()}'"
    check("Auto-slide (per slide)", autoslide)
    slnum = lambda: ev("document.querySelector('.slide-number').textContent.replace(/\\s+/g, '')")
    check("Slide numbers c/t", lambda: (bool(re.fullmatch(r"\d+/\d+", slnum())), slnum()))
    def jump():
        go("content"); key("g"); pg.keyboard.type("4"); key("Enter")
        n = slnum(); return n.startswith("4/"), f"G 4 Enter -> slide number {n}"
    check("Jump to slide (G)", jump)
    def overview():
        key("o"); a = ev("Reveal.isOverview()"); key("o")
        return a and not ev("Reveal.isOverview()"), "O toggles overview"
    check("Overview mode (O/Esc)", overview)
    def pause():
        key("b"); a = ev("Reveal.isPaused()"); key("b")
        return a, "B pauses (black screen)"
    check("Pause / blackout (B)", pause)
    def fullscreen():
        go("content"); key("f"); a = until(pg, "!!document.fullscreenElement", 3000)
        if a: ev("document.exitFullscreen()")
        return a, "F requests fullscreen"
    check("Fullscreen (F)", fullscreen)
    def custom_key():
        go("content"); before = ev("JSON.stringify(Reveal.getIndices())"); key("x")
        return ev("JSON.stringify(Reveal.getIndices())") != before, "X bound via Reveal.addKeyBinding"
    check("Keyboard: custom binding", custom_key)
    def iframe_focus():
        go("bg-iframe"); frame(pg, "explorer.html", "window.__draws || 0")
        pg.mouse.click(640, 400); pg.wait_for_timeout(500)          # into the interactive background app
        key("ArrowRight")
        return cur() != "bg-iframe", f"after clicking into the app, ArrowRight -> {cur()}"
    check("Keyboard after clicking an app", iframe_focus)
    def touch():
        go("markup"); before = cur(); cdp = ctx.new_cdp_session(pg)
        for t, x in [("touchStart", 900), ("touchMove", 700), ("touchMove", 300), ("touchEnd", 300)]:
            cdp.send("Input.dispatchTouchEvent", {"type": t, "touchPoints": [] if t == "touchEnd" else [{"x": x, "y": 400}]}); pg.wait_for_timeout(60)
        ok = until(pg, f"Reveal.getCurrentSlide().id !== '{before}'", 3000)
        return ok, f"swipe left: {before} -> {cur()}"
    check("Touch navigation (swipe)", touch)
    def search():
        go("content"); pg.keyboard.press("Control+Shift+F")
        ok = until(pg, "(() => { const b = document.querySelector('#searchbox, .searchbox'); return !!b && getComputedStyle(b).display !== 'none'; })()", 3000)
        pg.keyboard.press("Control+Shift+F")
        return ok, "Ctrl+Shift+F shows the search box (RevealSearch)"
    check("Search plugin", search)
    def zoom():
        # The zoom plugin's key is Ctrl on Linux, Alt elsewhere (config zoomKey overrides).
        mod = "Control" if "Linux" in ev("navigator.platform") else "Alt"
        go("layout"); pg.keyboard.down(mod); pg.mouse.click(640, 400); pg.keyboard.up(mod)
        ok = until(pg, "(document.body.style.transform || '').includes('scale')", 3000)
        t = ev("document.body.style.transform || ''")
        pg.keyboard.down(mod); pg.mouse.click(640, 400); pg.keyboard.up(mod); pg.wait_for_timeout(800)
        return ok, f"{mod}+click body transform: {t[:50]}"
    check("Zoom plugin (Alt/Ctrl+click)", zoom)
    def menu():
        go("content"); key("m")
        ok = ev("!!document.querySelector('.slide-menu.active, .slide-menu-wrapper.active, .slide-menu-overlay.active')")
        pg.keyboard.press("Escape"); return ok, "M opens Quarto's slide menu"
    check("Menu (Quarto)", menu)
    check("Custom plugin (ping)", lambda: (ev("Reveal.hasPlugin('ping') && window.__pingSlides > 0"), f"init(deck) ran, saw {ev('window.__pingSlides')} slides"))
    def events():
        ev("window.__ev = []; Reveal.on('fragmentshown', () => __ev.push('f')); Reveal.on('slidechanged', () => __ev.push('s'));")
        go("fragments"); key("ArrowRight")
        e = ev("__ev"); return "f" in e and "s" in e, f"events seen {e}"
    check("Events API", events)
    def state():
        go("code"); st = ev("Reveal.getState()"); go("last"); ev(f"Reveal.setState({json.dumps(st)})")
        ok = until(pg, "Reveal.getCurrentSlide().id === 'code'", 3000)
        return ok, f"getState/setState round-trip -> {cur()}"
    check("Presentation state", state)
    check("Speaker notes in markup", lambda: ("NOTES-MARKER" in ev("document.getElementById('notes').querySelector('aside.notes').textContent"),
                                             "aside.notes present, hidden from audience"))
    def speaker():
        go("notes")
        with pg.expect_popup(timeout=8000) as pop:
            pg.keyboard.press("s")
        sp = pop.value
        until(sp, "(document.querySelector('.speaker-controls-notes')?.innerText || '').includes('NOTES-MARKER')", 10000)
        notes = sp.evaluate("document.querySelector('.speaker-controls-notes')?.innerText || ''")
        previews = sp.evaluate("document.querySelectorAll('iframe').length")
        sp.wait_for_timeout(1500)
        before = sp.locator("#current-slide").screenshot()
        sp.screenshot(path=str(out / "speaker-view.png"))
        key("ArrowDown"); sp.wait_for_timeout(2000)
        follows = sp.locator("#current-slide").screenshot() != before
        sp.close()
        return "NOTES-MARKER" in notes and previews >= 2 and follows, f"notes shown={'NOTES-MARKER' in notes}, {previews} slide previews, follows the deck={follows}"
    check("Speaker view (S)", speaker)

    # Scroll view
    pg2 = ctx.new_page(); pg2.goto(URL + "?view=scroll"); until(pg2, "typeof Reveal !== 'undefined' && Reveal.isReady()", 15000)
    def scroll():
        a = pg2.evaluate("Reveal.getIndices().h"); pg2.mouse.wheel(0, 2500); pg2.wait_for_timeout(1500)
        b = pg2.evaluate("Reveal.getIndices().h")
        return pg2.evaluate("Reveal.isScrollView()") and b != a, f"scroll view; scrolling moved from column {a} to {b}"
    check("Scroll view (?view=scroll)", scroll)
    pg2.screenshot(path=str(out / "scroll-view.png"))

    # postMessage: drive the deck from a parent page
    wrapper = out / "postmessage.html"
    wrapper.write_text(f'<iframe id="d" src="{URL}" width="1000" height="600"></iframe>')
    pg3 = ctx.new_page(); pg3.goto(wrapper.as_uri())
    frame(pg3, deck.name, "typeof Reveal !== 'undefined' && Reveal.isReady()", 15000)
    def pm():
        got = pg3.evaluate("""() => new Promise(res => {
          window.addEventListener('message', e => { try { const d = JSON.parse(e.data); if (d.method === 'getIndices') res(d.result); } catch (_) {} });
          const w = document.getElementById('d').contentWindow;
          w.postMessage(JSON.stringify({method: 'slide', args: [1, 3]}), '*');
          setTimeout(() => w.postMessage(JSON.stringify({method: 'getIndices'}), '*'), 800);
          setTimeout(() => res(null), 4000); })""")
        return got == {"h": 1, "v": 3}, f"parent sent slide(1, 3); deck replied getIndices = {got}"
    check("postMessage API", pm)

    # Theme: an app whose copy pins data-theme="light" stays light when the system is dark
    dark = new_ctx(color_scheme="dark")
    pg4 = dark.new_page(); pg4.goto(URL + "#/bg-iframe")
    def theme():
        bgc = frame(pg4, "explorer.html", "getComputedStyle(document.querySelector('.fk-app')).backgroundColor", 15000)
        return bgc == "rgb(255, 255, 255)", f"system dark, pinned app background {bgc}"
    check("Embedded app theme pinned", theme)

    # The demo deck: the setup's Plotly renderer drew, and a fragment inside an equation steps
    if demo:
        pg5 = ctx.new_page(); pg5.goto(demo.as_uri()); until(pg5, "typeof Reveal !== 'undefined' && Reveal.isReady()", 15000)
        def plotly():
            ok = until(pg5, "document.querySelectorAll('.js-plotly-plot .main-svg').length > 0", 8000)
            return ok, "Plotly figure drew from plotly.js loaded once in the header"
        check("Demo: Plotly figure drew", plotly)
        def eqfrag():
            pg5.evaluate("Reveal.slide(1, 0, -1)"); pg5.wait_for_timeout(800)
            op = lambda: pg5.evaluate("[...document.querySelectorAll('mjx-container .fragment')].map(e => getComputedStyle(e).opacity).join(',')")
            a = op(); pg5.keyboard.press("ArrowRight"); pg5.wait_for_timeout(900); b = op()
            return a == "0" and b == "1", f"equation fragment opacity {a!r} -> {b!r} after one step"
        check("Demo: fragment in an equation", eqfrag)
    browser.close()

surprises = [n for n, ok, crashed, _ in results if (n in EXPECTED_FAIL) != (not ok) or (n in EXPECTED_FAIL and crashed)]
print(f"\n{sum(ok for _, ok, _, _ in results)}/{len(results)} passed; {len(EXPECTED_FAIL)} expected to fail")
print("blocked network requests:", blocked or "none")
print("page errors:", errors or "none")
for n in surprises:
    print(f"DIFFERS FROM THE GUIDE: '{n}'")
sys.exit(1 if surprises or blocked or errors else 0)
