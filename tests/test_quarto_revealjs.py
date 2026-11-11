"""quarto-revealjs/assets: inline_apps.py (apps and <object> into the deck) and bibliography.py."""

import base64
import gzip
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ASSETS = Path(__file__).resolve().parents[1] / "quarto-revealjs" / "assets"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ASSETS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inline_apps = load("inline_apps")
bibliography = load("bibliography")

DECK = """<html><body><div class="reveal"><div class="slides">
<section id="t"><h2>T</h2><aside class="notes"><p>say this</p></aside></section>
<section data-background-iframe="apps/full.html" data-background-interactive="true"></section>
<section><iframe data-src="apps/inline.html"></iframe><iframe src="data:text/html;base64,AA=="></iframe></section>
<section><object data="media/header.svg" type="image/svg+xml"></object><object data="https://x.org/a.svg"></object></section>
<section data-background-iframe="https://example.org/"></section>
</div></div>
<script>/* lib */ "Reveal.initialize(" + `<iframe src="${e}">` </script>
<script>Reveal.initialize({});</script>
</body></html>"""


class InlineAppsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "apps").mkdir()
        (self.root / "media").mkdir()
        (self.root / "apps/full.html").write_text("<p>full</p>")
        (self.root / "apps/inline.html").write_text("<p>inline</p>")
        (self.root / "media/header.svg").write_text("<svg/>")

    def tearDown(self):
        self.tmp.cleanup()

    def test_apps_become_blobs_before_reveal_starts(self):
        out, missing = inline_apps.inline(DECK, self.root)
        self.assertEqual(missing, [])
        b64 = re.search(r'<script type="text/plain" id="inlined-app-0">([^<]+)</script>', out)[1]
        self.assertEqual(gzip.decompress(base64.b64decode(b64)), b"<p>full</p>")   # gzipped, unzipped in the browser
        self.assertIn('new DecompressionStream("gzip")', out)
        self.assertIn('"inlined-app-1": ["apps/inline.html", "text/html"]', out)
        self.assertIn("URL.createObjectURL", out)
        # loader sits right before the script that calls Reveal.initialize (the last one)
        self.assertLess(out.index("createObjectURL"), out.index("<script>Reveal.initialize"))
        self.assertGreater(out.index("createObjectURL"), out.index("/* lib */"))
        # remote URLs and data: iframes are left alone; notes kept by default
        self.assertIn('data-background-iframe="https://example.org/"', out)
        self.assertNotIn("inlined-app-2", out)
        self.assertIn('src="data:text/html;base64,AA=="', out)
        self.assertIn('<aside class="notes">', out)

    def test_data_app_becomes_lazy_data_src(self):
        # pandoc leaves data-app alone (src/data-src become data: URLs, which Chrome caps at 2 MB)
        deck = DECK.replace('<iframe data-src="apps/inline.html">', '<iframe data-app="apps/inline.html">')
        out, missing = inline_apps.inline(deck, self.root)
        self.assertEqual(missing, [])
        self.assertIn('"inlined-app-1": ["apps/inline.html", "text/html"]', out)
        self.assertIn('[f.getAttribute("data-app"), f.getAttribute("data-src"), f.getAttribute("src")].includes(path)', out)
        self.assertIn('f.setAttribute("data-src", url);', out)
        (self.root / "apps/inline.html").unlink()
        self.assertEqual(inline_apps.inline(deck, self.root)[1], ["apps/inline.html"])

    def test_non_html_app_keeps_its_type(self):
        (self.root / "apps/fig.svg").write_text("<svg/>")
        out, _ = inline_apps.inline(DECK.replace("apps/full.html", "apps/fig.svg"), self.root)
        self.assertIn('["apps/fig.svg", "image/svg+xml"]', out)

    def test_root_option(self):
        deck = self.root / "out.html"
        deck.write_text(DECK)
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(inline_apps.main([str(deck), "--root", str(self.root)]), 0)
        self.assertIn("inlined-app-0", deck.read_text())

    def test_object_becomes_data_uri(self):
        out, _ = inline_apps.inline(DECK, self.root)
        svg = base64.b64encode(b"<svg/>").decode()
        self.assertIn(f'<object data="data:image/svg+xml;base64,{svg}"', out)
        self.assertIn('<object data="https://x.org/a.svg">', out)

    def test_strip_notes(self):
        out, _ = inline_apps.inline(DECK, self.root, strip_notes=True)
        self.assertNotIn("<aside", out)
        self.assertNotIn("say this", out)

    def test_second_run_changes_nothing(self):
        once, _ = inline_apps.inline(DECK, self.root)
        twice, missing = inline_apps.inline(once, self.root)
        self.assertEqual((twice, missing), (once, []))
        self.assertEqual(twice.count('id="inlined-app-0"'), 1)

    def test_strip_notes_with_more_classes(self):
        out, _ = inline_apps.inline('<aside class="notes x">a</aside><aside class="x notes">b</aside>'
                                    '<aside class="notesy">keep</aside>', self.root, strip_notes=True)
        self.assertEqual(out, '<aside class="notesy">keep</aside>')

    def test_encoded_paths_and_query(self):
        (self.root / "apps/my app.html").write_text("<p>sp</p>")
        deck = DECK.replace('data-src="apps/inline.html"', 'data-src="apps/my%20app.html"') \
                   .replace('data-background-iframe="apps/full.html"', 'data-background-iframe="apps/full.html?v=1#x"')
        out, missing = inline_apps.inline(deck, self.root)
        self.assertEqual(missing, [])
        self.assertIn('"apps/my%20app.html"', out)
        self.assertIn('"apps/full.html?v=1#x"', out)

    def test_missing_file_is_reported_and_left(self):
        (self.root / "apps/full.html").unlink()
        out, missing = inline_apps.inline(DECK, self.root)
        self.assertEqual(missing, ["apps/full.html"])
        self.assertIn('data-background-iframe="apps/full.html"', out)

    def test_iframes_inside_scripts_are_not_apps(self):
        # any case, and an end tag with junk before ">" (browsers accept it): an app path inside a script is not an app
        deck = DECK.replace("<script>/* lib */", '<SCRIPT>/* lib */ `<iframe src="apps/gone.html">`</script\t\n bar>\n<script>')
        self.assertEqual(inline_apps.inline(deck, self.root)[1], [])

    def test_no_apps_no_loader(self):
        out, missing = inline_apps.inline("<html><body><p>x</p></body></html>", self.root)
        self.assertEqual((out, missing), ("<html><body><p>x</p></body></html>", []))

    def test_cli_exit_code(self):
        deck = self.root / "deck.html"
        deck.write_text(DECK.replace("apps/full.html", "apps/gone.html"))
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(inline_apps.main(["deck.html", "-o", "out.html"]), 1)
                deck.write_text(DECK)
                self.assertEqual(inline_apps.main(["deck.html", "--strip-notes"]), 0)
        finally:
            os.chdir(cwd)
        self.assertIn("inlined-app-0", deck.read_text())
        self.assertNotIn("<aside", deck.read_text())

    def test_repeated_data_uri_is_kept_once(self):
        # pandoc embeds a file once per use: an image on three slides is in the deck three times
        big = "data:image/png;base64," + "A" * 5000
        small = "data:image/png;base64,BB=="
        deck = DECK.replace("<section id=\"t\">",
            f'<section><img src="{big}"><img src="{small}"><svg><image xlink:href="{big}"/></svg></section>'
            f'<section><img src="{big}"><img src="{small}"><script src="data:text/javascript;base64,{"C" * 5000}"></script>'
            f'<script src="data:text/javascript;base64,{"C" * 5000}"></script></section><section id="t">')
        out, _ = inline_apps.inline(deck, self.root)
        self.assertEqual(out.count(big), 1)
        self.assertEqual(out.count('data-dup-src="dup-0"'), 2)
        self.assertIn('<image data-dup-href="dup-0"/>', out)       # xlink:href comes back as href
        self.assertEqual(out.count(small), 2)                      # small ones are not worth it
        self.assertEqual(out.count("C" * 5000), 2)                 # scripts stay where they run
        # restored before reveal.js starts, and a second run changes nothing
        self.assertLess(out.index('id="dup-0"'), out.index("<script>Reveal.initialize"))
        self.assertGreater(out.index('id="dup-0"'), out.index("/* lib */"))
        self.assertEqual(inline_apps.inline(out, self.root)[0], out)


class SizeReportTest(unittest.TestCase):
    def test_lists_largest_parts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "apps").mkdir()
            (root / "apps/full.html").write_text(base64.b64encode(os.urandom(30000)).decode())   # gzip can't shrink it
            (root / "apps/inline.html").write_text("<p>inline</p>")
            (root / "media").mkdir()
            (root / "media/header.svg").write_text("<svg/>")
            deck = DECK.replace("<section id=\"t\">",
                                '<section><img alt="a photo" src="data:image/webp;base64,' + "D" * 30000 + '"></section><section id="t">')
            out, _ = inline_apps.inline(deck, root)
            (root / "deck.html").write_text(out)
            r = subprocess.run([sys.executable, str(ASSETS / "size_report.py"), str(root / "deck.html"), "5"],
                               capture_output=True, text=True, check=True)
        lines = r.stdout.splitlines()
        self.assertRegex(lines[0], r"^0\.\d MB in all; the largest parts:$")
        self.assertIn("app apps/full.html (gzip)", lines[1])         # ~41 kB of base64, listed first
        self.assertIn("image/webp", lines[2])
        self.assertIn('alt="a photo"', lines[2])
        self.assertEqual(len(lines), 3)


def item(last, year, title, doi="", url="", kind="journalArticle", n=1):
    creators = [{"creatorType": "author", "lastName": last}] + \
               [{"creatorType": "author", "lastName": f"Co{i}"} for i in range(n - 1)]
    return {"data": {"itemType": kind, "creators": creators, "date": f"{year}-01-01", "title": title,
                     "DOI": doi, "url": url}}


class BibliographyTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(bibliography.label(item("Rubin", 1970, "t")["data"]), ("Rubin", "1970"))
        self.assertEqual(bibliography.label(item("Rubin", 1970, "t", n=2)["data"]), ("Rubin & Co0", "1970"))
        self.assertEqual(bibliography.label(item("Rubin", 1970, "t", n=3)["data"]), ("Rubin et al.", "1970"))
        self.assertEqual(bibliography.label({"title": "Untitled thing", "date": ""}), ("Untitled thing", "n.d."))

    def test_links_prefer_doi_but_not_arxiv_doi(self):
        self.assertEqual(bibliography.link({"DOI": "10.1/x", "url": "u"}), "https://doi.org/10.1/x")
        self.assertEqual(bibliography.link({"DOI": "10.48550/arXiv.1", "url": "https://arxiv.org/abs/1"}),
                         "https://arxiv.org/abs/1")
        self.assertEqual(bibliography.link({"DOI": "10.48550/arXiv.1"}), "https://doi.org/10.48550/arXiv.1")

    def test_lines_sorted_with_suffixes_and_quotes(self):
        rows = bibliography.lines([
            item("Zed", 2020, "Z", doi="10.1/z")["data"],
            item("Bho", 2021, 'B "two"', doi="10.1/b2", n=3)["data"],
            item("Bho", 2021, "A one", doi="10.1/b1", n=3)["data"],
        ])
        self.assertEqual(rows[0], '- {{< paper url="https://doi.org/10.1/b1" who="Bho et al." year="2021a" title="A one" >}}')
        self.assertIn('year="2021b" title="B \'two\'"', rows[1])
        self.assertIn('who="Zed" year="2020"', rows[2])

    def test_warns_when_an_item_links_nowhere(self):
        with mock.patch("sys.stderr", io.StringIO()) as err:
            bibliography.lines([item("Nolink", 1999, "t")["data"]])
        self.assertIn("Nolink (1999) has no DOI or URL", err.getvalue())

    def test_fetch_pages_and_skips_attachments(self):
        pages = [[item(f"A{i}", 2000, "t") for i in range(99)] + [item("X", 1, "", kind="attachment")],
                 [item("B", 2001, "t"), item("N", 1, "", kind="note")]]
        urls = []

        def fake(url):
            urls.append(url)
            return io.BytesIO(json.dumps(pages[len(urls) - 1]).encode())
        with mock.patch.object(bibliography.urllib.request, "urlopen", fake):
            got = bibliography.fetch("ABCD1234")
        self.assertEqual(len(got), 100)
        self.assertIn("/collections/ABCD1234/items/top", urls[0])
        self.assertTrue(urls[1].endswith("start=100"))

    def test_main_reports_unreachable_zotero(self):
        def down(url):
            raise OSError("connection refused")
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(bibliography.urllib.request, "urlopen", down), \
                mock.patch("sys.stderr", io.StringIO()) as err:
            self.assertEqual(bibliography.main(["K", "-o", str(Path(d) / "b.qmd")]), 1)
        self.assertIn("not reachable", err.getvalue())


if __name__ == "__main__":
    unittest.main()
