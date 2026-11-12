# make        _output/presentation.html (one offline file, checked) and _output/presentation.pdf
# make notes  _output/presentation-notes.pdf, each slide followed by its speaker notes
# make refs   rewrite the References slide's list from the Zotero collection (Zotero running)
# Needs quarto and quartz-deck's `qd` (github.com/nstarman/quartz-deck). `qd export` replaces
# _output/ as a whole, so it prints the PDF in the same run.
HTML = _output/presentation.html
ZOTERO = XXXXXXXX   # the talk's Zotero collection key (8 characters)

.PHONY: all notes refs
all:
	qd export --pdf --out _output

notes: | $(HTML)
	qd pdf --html $(HTML) --notes

refs:
	qd bib --zotero $(ZOTERO)

$(HTML):
	qd export --pdf --out _output
