# Data model

- **Citation** (shortcode `paper`): `url` (required), `who` ("Name", "A & B", "Name et al."), `year`,
  `title` (hover text), `corner` ("true": icon only, top-right of the slide).
- **Zotero item → citation**: `who` from the first author's last name (one, two, or "et al."),
  `year` from `date` (else "n.d."), `url` = `https://doi.org/<DOI>` unless the DOI is an arXiv
  DOI (`10.48550/…`) and a `url` exists; items sharing `who`+`year` get suffixes `a`, `b`, … in
  title order. Attachments and notes are skipped.
- **App reference** (rendered deck): `data-background-iframe="<path>"`, `<iframe src|data-src="<path>">`
  with a relative path to an existing file → blob; `<object data="<path>">` → `data:` URI. Missing
  files are reported and left alone.
