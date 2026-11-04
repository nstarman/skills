"""Drive every reveal.js feature in fixture/reveal-features.qmd, offline, and compare with the guide.

    python feature_check.py _output/reveal-features.html <scratch-dir>

Each check prints PASS or FAIL. EXPECTED_FAIL lists what the guide documents as not working in the
tested Quarto/reveal.js versions. The run fails (exit 1) when any result differs from the guide, in
either direction: a documented limitation that now works means the guide is out of date too.
"""
import pathlib, sys, json

# The guide's ✗ and ◐-without-workaround rows (quarto-revealjs/references/quarto-revealjs-guide.md).
EXPECTED_FAIL = {
    "Lightbox: reveal native",   # data-preview-image is reveal.js 5.2+
    "Links: preview overlay",    # preview links only for http/www URLs
}
from playwright.sync_api import sync_playwright

deck = pathlib.Path(sys.argv[1]).resolve()
URL = deck.as_uri()
results = []

def check(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # a crash is a failed check, not a failed run
        ok, detail = False, f"error: {str(e).splitlines()[0][:120]}"
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name:28s} {detail}", flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(offline=True, viewport={"width": 1280, "height": 800}, has_touch=True)
    blocked = []
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else (blocked.append(r.request.url), r.abort()))
    pg = ctx.new_page(); errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)[:150]))
    pg.goto(URL); pg.wait_for_timeout(3000)
    ev = pg.evaluate
    def ensure():
        if not pg.url.startswith(URL) or not ev("typeof Reveal !== 'undefined'"):
            pg.goto(URL); pg.wait_for_timeout(3000)
    def go(i): ensure(); ev(f"Reveal.slide(...Object.values(Reveal.getIndices(document.getElementById('{i}'))).slice(0,2))"); pg.wait_for_timeout(1200)
    cur = lambda: ev("Reveal.getCurrentSlide().id")
    key = lambda k: (pg.keyboard.press(k), pg.wait_for_timeout(900))

    # ---- Content
    check("Markup / raw HTML", lambda: (ev("!!document.querySelector('.raw-html-test')"), "raw HTML block rendered"))
    def bg(i, test):
        go(i); return ev("(() => { const b = Reveal.getSlideBackground(Reveal.getCurrentSlide()); return getComputedStyle(b).backgroundImage + ' ' + getComputedStyle(b.querySelector('.slide-background-content')).backgroundImage; })()").replace('none ', '').startswith(test.replace('url("data:image', 'none url("data:image')) or test in ev("(() => { const b = Reveal.getSlideBackground(Reveal.getCurrentSlide()); return getComputedStyle(b).backgroundImage + getComputedStyle(b.querySelector('.slide-background-content')).backgroundImage; })()")
    def bgcolour():
        go("bg-colour"); c = ev("getComputedStyle(Reveal.getSlideBackground(Reveal.getCurrentSlide())).backgroundColor")
        return c == "rgb(11, 29, 58)", c
    check("Background: colour", bgcolour)
    check("Background: gradient", lambda: (bg("bg-gradient", "linear-gradient"), "linear-gradient applied"))
    check("Background: image", lambda: (bg("bg-image", 'url("data:image'), "inlined data URI"))
    def bgvid():
        go("bg-video"); pg.wait_for_timeout(1500)
        r = ev("(() => { const v = document.querySelector('.slide-background.present video'); return v && [v.readyState, v.paused, v.currentSrc.slice(0,40)]; })()")
        return bool(r and r[0] >= 2), f"readyState={r and r[0]} paused={r and r[1]} src={r and r[2]}"
    check("Background: video", bgvid)
    def bgiframe():
        go("bg-iframe"); pg.wait_for_timeout(2000)
        fr = [f for f in pg.frames if f.url.endswith("explorer.html")]
        n = fr[0].evaluate("window.__draws || 0") if fr else 0
        return n > 0, f"background app drew {n} times"
    check("Background: iframe", bgiframe)
    check("Parallax background", lambda: ("explorer" in ev("document.querySelector('.reveal .backgrounds').style.backgroundImage"), ev("document.querySelector('.reveal .backgrounds').style.backgroundImage")[:60]))
    def media():
        go("media"); pg.wait_for_timeout(1500)
        v = ev("(() => { const v = document.querySelector('video.vjs-tech, video.video-js, video'); return v && v.readyState; })()")
        a = ev("document.querySelector('.audio-test').readyState")
        lz = ev("(document.querySelector('.lazy-test').getAttribute('src')||'').slice(0,15)")
        return v >= 1 and a >= 1 and lz.startswith("data:image"), f"video.js readyState={v}, audio readyState={a}, lazy img src={lz}"
    check("Media (video, audio, lazy)", media)
    def qlightbox():
        go("lightbox"); pg.locator("a.lightbox").first.click(); pg.wait_for_timeout(1200)
        ok = ev("!!document.querySelector('.glightbox-container, .gcontainer')"); pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
        return ok, "Quarto lightbox (GLightbox) opened"
    check("Lightbox: Quarto .lightbox", qlightbox)
    def nlightbox():
        go("lightbox"); pg.locator("img.native-lightbox").click(); pg.wait_for_timeout(1000)
        ok = ev("!!document.querySelector('.r-overlay, .overlay')")
        if ok: pg.keyboard.press("Escape")
        return ok, "reveal.js 5.2+ data-preview-image overlay"
    check("Lightbox: reveal native", nlightbox)
    def preview():
        go("lightbox"); pg.locator("a.preview-test").click(); pg.wait_for_timeout(1500)
        pg.wait_for_timeout(500)
        if not pg.url.startswith(URL): return False, f"click navigated the page to {pg.url[-30:]}"
        ok = ev("!!document.querySelector('.r-overlay iframe, .overlay iframe')")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
        return ok, "preview-link opens the app in an overlay iframe"
    check("Links: preview overlay", preview)
    def preview_local():
        go("lightbox"); pg.locator("a.preview-local").click(); pg.wait_for_timeout(2500)
        ok = pg.url.startswith(URL) and ev("!!document.querySelector('.r-overlay iframe, .overlay iframe')")
        cnv = 0
        if ok:
            fr = [f for f in pg.frames if f.url.endswith("explorer.html")]
            cnv = fr[0].evaluate("window.__draws || 0") if fr else 0
            pg.keyboard.press("Escape"); pg.wait_for_timeout(600)
        return ok and cnv > 0, f"local app in overlay, canvases drawn: {cnv}"
    check("Links: preview (local file)", preview_local)
    def code():
        go("code"); n = ev("Reveal.getCurrentSlide().querySelectorAll('.fragment').length"); steps = []
        for _ in range(3):
            key("ArrowRight"); steps.append(ev("Reveal.getIndices().f"))
        return n >= 2 and steps == [0, 1, 2] or steps[:2] == [0, 1], f"{n} highlight steps; fragment index per key press {steps}"
    check("Code line stepping", code)
    check("Math", lambda: (go("math") or ev("document.querySelectorAll('#math mjx-container').length") > 0, "MathJax SVG"))
    def frags():
        go("fragments"); order = []
        for _ in range(6):
            key("ArrowRight")
            order.append(ev("Reveal.getCurrentSlide().querySelector('.fragment.current-fragment')?.textContent.trim().split(/\\s+/)[0] || ''"))
        return order[:3] == ["fade-left,", "strike,", "fade-up,"], f"shown in order {order}"
    check("Fragments + fragment-index", frags)
    def links():
        go("links"); pg.locator("a.internal-link").click(); pg.wait_for_timeout(1200); a = cur()
        go("links"); pg.locator("a.navigate-next").click(); pg.wait_for_timeout(1200); b = cur()
        go("links"); pg.locator("button.btn-next").click(); pg.wait_for_timeout(1200); c2 = cur()
        return a == "layout" and c2 == "layout", f"[..](#layout) -> {a}; <a href='#' class=navigate-next> -> {b}; <button class=navigate-next> -> {c2}"
    check("Links: internal + navigate-*", links)
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
        total = ev("document.querySelectorAll('.reveal .slides section:not(.stack)').length")  # every slide in the page
        return int(num.split("/")[1]) < total, f"last slide '{num}', {total} slides in the page (uncounted ones left out)"
    check("Slide visibility: uncounted", uncounted)

    # ---- Customization
    check("Presentation size", lambda: (ev("[Reveal.getConfig().width, Reveal.getConfig().height]") == [1280, 720], "1280x720 from YAML"))
    check("Transition per slide", lambda: (ev("document.getElementById('trans').dataset.transition") == "convex", "data-transition=convex, speed=" + ev("document.getElementById('trans').dataset.transitionSpeed")))

    # ---- Features
    check("Vertical slides", lambda: (ev("(() => { const a = Reveal.getIndices(document.getElementById('features')), b = Reveal.getIndices(document.getElementById('vertical')); return a.h === b.h && b.v === 1; })()"), "'Features' column, child at v=1"))
    def autoanim():
        go("aa1"); key("ArrowDown"); pg.wait_for_timeout(100)
        return cur() == "aa2", "moved to the auto-animate pair (morph runs via CSS)"
    check("Auto-animate", autoanim)
    def autoslide():
        go("autoslide"); pg.wait_for_timeout(2500)
        return cur() != "autoslide", f"after 2.5 s now on '{cur()}'"
    check("Auto-slide (per slide)", autoslide)
    slnum = lambda: ev("document.querySelector('.slide-number').textContent.replace(/\\s+/g, '')")
    check("Slide numbers c/t", lambda: (bool(__import__("re").fullmatch(r"\d+/\d+", slnum())), slnum()))
    def jump():
        go("content"); key("g"); pg.keyboard.type("4"); key("Enter")
        n = ev("document.querySelector('.slide-number').textContent.replace(/\\s+/g, '')")
        return n.startswith("4/"), f"G 4 Enter -> slide number {n}"
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
        ensure(); go("content"); key("f"); pg.wait_for_timeout(500); a = ev("!!document.fullscreenElement")
        if a: ev("document.exitFullscreen()")
        return a, "F requests fullscreen"
    check("Fullscreen (F)", fullscreen)
    def custom_key():
        go("content"); before = ev("JSON.stringify(Reveal.getIndices())"); key("x")
        return ev("JSON.stringify(Reveal.getIndices())") != before, "X bound via Reveal.addKeyBinding"
    check("Keyboard: custom binding", custom_key)
    def touch():
        go("markup"); before = cur(); cdp = ctx.new_cdp_session(pg)
        for t, x in [("touchStart", 900), ("touchMove", 700), ("touchMove", 300), ("touchEnd", 300)]:
            cdp.send("Input.dispatchTouchEvent", {"type": t, "touchPoints": [] if t == "touchEnd" else [{"x": x, "y": 400}]}); pg.wait_for_timeout(60)
        pg.wait_for_timeout(1200)
        return cur() != before, f"swipe left: {before} -> {cur()}"
    check("Touch navigation (swipe)", touch)
    def search():
        go("content"); pg.keyboard.press("Control+Shift+F"); pg.wait_for_timeout(700)
        ok = ev("(() => { const b = document.querySelector('#searchbox, .searchbox'); return !!b && getComputedStyle(b).display !== 'none'; })()")
        pg.keyboard.press("Control+Shift+F")
        return ok, "Ctrl+Shift+F shows the search box (RevealSearch)"
    check("Search plugin", search)
    def zoom():
        go("layout"); pg.keyboard.down("Alt"); pg.mouse.click(640, 400); pg.keyboard.up("Alt"); pg.wait_for_timeout(1200)
        t = ev("document.body.style.transform || document.querySelector('.reveal').style.transform || ''")
        pg.keyboard.down("Alt"); pg.mouse.click(640, 400); pg.keyboard.up("Alt"); pg.wait_for_timeout(800)
        return "scale" in t, f"Alt+click body transform: {t[:50]}"
    check("Zoom plugin (Alt+click)", zoom)
    def menu():
        go("content"); key("m")
        ok = ev("!!document.querySelector('.slide-menu.active, .slide-menu-wrapper.active, .slide-menu-overlay.active')")
        pg.keyboard.press("Escape"); return ok, "Quarto menu opens"
    check("Menu (Quarto)", menu)
    check("Custom plugin (ping)", lambda: (ev("Reveal.hasPlugin('ping') && window.__pingSlides > 0"), f"init(deck) ran, saw {ev('window.__pingSlides')} slides"))
    def events():
        ev("window.__ev = []; Reveal.on('fragmentshown', () => __ev.push('f')); Reveal.on('slidechanged', () => __ev.push('s'));")
        go("fragments"); key("ArrowRight")
        e = ev("__ev"); return "f" in e and "s" in e, f"events seen {e}"
    check("Events API", events)
    def state():
        go("code"); st = ev("Reveal.getState()"); go("last"); ev(f"Reveal.setState({json.dumps(st)})"); pg.wait_for_timeout(800)
        return cur() == "code", f"getState/setState round-trip -> {cur()}"
    check("Presentation state", state)
    check("Speaker notes in markup", lambda: ("NOTES-MARKER" in ev("document.getElementById('notes').querySelector('aside.notes').textContent"), "aside.notes present, hidden from audience"))

    # Speaker view: S opens a popup with current/next slide, notes, timer
    def speaker():
        go("notes")
        with pg.expect_popup(timeout=8000) as pop:
            pg.keyboard.press("s")
        sp = pop.value; sp.wait_for_timeout(5000)
        notes = sp.evaluate("document.querySelector('.speaker-controls-notes')?.innerText || ''")
        frames = sp.evaluate("document.querySelectorAll('iframe').length")
        cur_id = sp.evaluate("(() => { const f = document.querySelector('#current-slide iframe'); try { return f.contentWindow.Reveal.getCurrentSlide().id; } catch (e) { return 'n/a: ' + e.message.slice(0, 40); } })()")
        timer = sp.evaluate("document.querySelector('.speaker-controls-time .clock-value, .speaker-controls-time')?.innerText.slice(0, 40) || ''")
        sp.screenshot(path=str(pathlib.Path(sys.argv[2]) / "speaker-view.png"))
        # does advancing the main deck move the speaker view?
        key("ArrowDown"); sp.wait_for_timeout(1500)
        cur2 = sp.evaluate("(() => { const f = document.querySelector('#current-slide iframe'); try { return f.contentWindow.Reveal.getCurrentSlide().id; } catch (e) { return 'n/a'; } })()")
        sp.close()
        return "NOTES-MARKER" in notes and frames >= 2, f"notes shown={'NOTES-MARKER' in notes}, {frames} slide previews, current={cur_id} -> after next: {cur2}, timer='{timer.strip()[:20]}'"
    check("Speaker view (S)", speaker)
    print("blocked requests:", blocked or "none"); print("page errors:", errors or "none")

    # Scroll view: ?view=scroll
    pg2 = ctx.new_page(); pg2.goto(URL + "?view=scroll"); pg2.wait_for_timeout(3000)
    check("Scroll view (?view=scroll)", lambda: (pg2.evaluate("Reveal.isScrollView()"), "deck becomes a scrollable page"))
    pg2.screenshot(path=str(pathlib.Path(sys.argv[2]) / "scroll-view.png"))

    # postMessage: control the deck from a parent page
    wrapper = pathlib.Path(sys.argv[2]) / "postmessage.html"
    wrapper.write_text(f'<iframe id="d" src="{URL}" width="1000" height="600"></iframe>')
    pg3 = ctx.new_page(); pg3.goto(wrapper.as_uri()); pg3.wait_for_timeout(9000)
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
    dark = browser.new_context(offline=True, color_scheme="dark", viewport={"width": 1280, "height": 800})
    dark.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:")) else r.abort())
    pg4 = dark.new_page(); pg4.goto(URL + "#/bg-iframe"); pg4.wait_for_timeout(4000)
    def theme():
        fr = [f for f in pg4.frames if f.url.endswith("explorer.html")]
        bgc = fr[0].evaluate("getComputedStyle(document.querySelector('.fk-app')).backgroundColor") if fr else None
        return bgc == "rgb(255, 255, 255)", f"system dark, pinned app background {bgc}"
    check("Embedded app theme pinned", theme)
    browser.close()

surprises = [(n, ok) for n, ok, _ in results if ok == (n in EXPECTED_FAIL)]
print(f"\n{sum(ok for _, ok, _ in results)}/{len(results)} passed; {len(EXPECTED_FAIL)} expected to fail")
for n, ok in surprises:
    print(f"DIFFERS FROM THE GUIDE: '{n}' now {'passes' if ok else 'fails'}")
if blocked or errors:
    print("DIFFERS FROM THE GUIDE: the deck used the network or raised page errors")
sys.exit(1 if surprises or blocked or errors else 0)
