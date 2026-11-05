"""List elements that stick out of the slide box, slide by slide, in slide coordinates.

    python check_overflow.py _output/*.html
    python check_overflow.py --webkit _output/*.html     # Safari's engine

Needs `pip install playwright`, and Google Chrome or `python -m playwright install chromium webkit`.
Runs headless (no window), offline. Each slide is measured with all its fragments shown. Not
counted (they gave false alarms): speaker notes, anything inside an <svg> or a MathJax container
(hidden struts, assistive MathML; the container itself is measured), anything inside a clipping
container (the container is measured), and invisible or zero-size elements. Exits 1 if any.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

TOL = 2   # px of slack, in slide coordinates

MEASURE = r"""(tol) => {
  const box = document.querySelector('.reveal .slides').getBoundingClientRect();
  const s = Reveal.getScale(), W = Reveal.getConfig().width, H = Reveal.getConfig().height;
  const slide = Reveal.getCurrentSlide(), out = [];
  const skip = (e) => e.closest('aside.notes, .notes, svg *, mjx-container *');
  const clipped = (e) => {
    for (let a = e.parentElement; a && a !== slide; a = a.parentElement) {
      const o = getComputedStyle(a);
      if (o.overflowX !== 'visible' || o.overflowY !== 'visible') return true;
    }
    return false;
  };
  for (const e of slide.querySelectorAll('*')) {
    if (e.tagName === 'SECTION' || skip(e)) continue;
    const st = getComputedStyle(e);
    if (st.display === 'none' || st.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const x = (r.left - box.left) / s, y = (r.top - box.top) / s, w = r.width / s, h = r.height / s;
    if (x < -tol || y < -tol || x + w > W + tol || y + h > H + tol) {
      if (clipped(e)) continue;
      const name = e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') +
        (typeof e.className === 'string' && e.className.trim() ? '.' + e.className.trim().split(/\s+/).join('.') : '');
      const text = (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40);
      out.push(`${name} at ${Math.round(x)},${Math.round(y)} size ${Math.round(w)}x${Math.round(h)}` +
               ` (slide ${W}x${H})${text ? ' "' + text + '"' : ''}`);
    }
  }
  return out;
}"""


def launch(p, webkit=False):
    """Headless only: never a visible window. Google Chrome if installed, else Playwright's Chromium."""
    if webkit:
        return p.webkit.launch(headless=True)
    try:
        return p.chromium.launch(headless=True, channel="chrome")
    except Exception:
        return p.chromium.launch(headless=True)   # `python -m playwright install chromium`


webkit = "--webkit" in sys.argv
decks = [a for a in sys.argv[1:] if a != "--webkit"]
bad = False
with sync_playwright() as p:
    browser = launch(p, webkit)
    for arg in decks:
        ctx = browser.new_context(offline=True, viewport={"width": 1600, "height": 900})
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:", "about:"))
                  else r.abort())
        page = ctx.new_page()
        page.goto(pathlib.Path(arg).resolve().as_uri())
        page.wait_for_function("typeof Reveal !== 'undefined' && Reveal.isReady()", timeout=15000)
        page.wait_for_timeout(2000)   # MathJax typesets after load
        page.evaluate("Reveal.configure({transition: 'none', backgroundTransition: 'none'})")
        problems = []
        for i in range(page.evaluate("Reveal.getTotalSlides()")):
            # all fragments shown: the slide at its fullest
            where = page.evaluate(f"""() => {{ const s = Reveal.getSlides()[{i}], ix = Reveal.getIndices(s);
                Reveal.slide(ix.h, ix.v, 1e6); return (s.id ? '#' + s.id + ' ' : '') + ix.h + '.' + (ix.v || 0); }}""")
            page.wait_for_timeout(100)
            problems += [f"slide {where}: {m}" for m in page.evaluate(MEASURE, TOL)]
        bad |= bool(problems)
        print(f"{'FAIL' if problems else 'OK  '} {arg}: {len(problems)} element(s) outside the slide")
        for m in problems:
            print(f"     {m}")
        ctx.close()
sys.exit(1 if bad else 0)
