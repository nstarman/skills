"""quarto-revealjs/assets: inline_apps.py (apps and <object> into the deck) and bibliography.py."""

import base64
import importlib.util
import io
import json
import os
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
        b64 = base64.b64encode(b"<p>full</p>").decode()
        self.assertIn(f'<script type="text/plain" id="inlined-app-0">{b64}</script>', out)
        self.assertIn('"inlined-app-1": "apps/inline.html"', out)
        self.assertIn("URL.createObjectURL", out)
        # loader sits right before the script that calls Reveal.initialize (the last one)
        self.assertLess(out.index("createObjectURL"), out.index("<script>Reveal.initialize"))
        self.assertGreater(out.index("createObjectURL"), out.index("/* lib */"))
        # remote URLs and data: iframes are left alone; notes kept by default
        self.assertIn('data-background-iframe="https://example.org/"', out)
        self.assertNotIn("inlined-app-2", out)
        self.assertIn('src="data:text/html;base64,AA=="', out)
        self.assertIn('<aside class="notes">', out)

    def test_object_becomes_data_uri(self):
        out, _ = inline_apps.inline(DECK, self.root)
        svg = base64.b64encode(b"<svg/>").decode()
        self.assertIn(f'<object data="data:image/svg+xml;base64,{svg}"', out)
        self.assertIn('<object data="https://x.org/a.svg">', out)

    def test_strip_notes(self):
        out, _ = inline_apps.inline(DECK, self.root, strip_notes=True)
        self.assertNotIn("<aside", out)
        self.assertNotIn("say this", out)

    def test_missing_file_is_reported_and_left(self):
        (self.root / "apps/full.html").unlink()
        out, missing = inline_apps.inline(DECK, self.root)
        self.assertEqual(missing, ["apps/full.html"])
        self.assertIn('data-background-iframe="apps/full.html"', out)

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
