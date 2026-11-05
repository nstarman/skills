# Script contracts (run from the deck folder)

| Command | Does | Exit |
|---|---|---|
| `python inline_apps.py [--strip-notes] DECK.html [-o OUT.html]` | inline apps and `<object>` files (paths relative to the current folder); with `--strip-notes` remove speaker notes; in place unless `-o` | 1 if a referenced file is missing |
| `python check_overflow.py [--webkit] DECK.html…` | list `slide h.v: <tag.class> x,y w×h` for elements outside the slide box | 1 if any |
| `python check_offline.py [--webkit] DECK.html…` | as before | 1 if any problem |
| `python make_pdf.py DECK.html` | as before; Chromium only | |
| `python bibliography.py COLLECTION_KEY [-o _bibliography.qmd]` | one `- {{< paper … >}}` line per item | 1 if Zotero is not reachable |
| `{{< paper url="…" who="…" year="…" title="…" [corner="true"] >}}` | link "[icon] who (year)" or corner icon | |

All browser scripts launch headless, prefer Google Chrome, else Playwright's bundled Chromium.
