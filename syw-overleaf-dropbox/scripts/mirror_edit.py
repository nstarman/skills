#!/usr/bin/env python3
"""Apply exact-match text edits to a file in the Overleaf Dropbox mirror, failing loudly.

Usage:  mirror_edit.py <path-to-mirror-file> <edits.json>

``edits.json`` is a list of {"old": "...", "new": "..."} objects.  Every ``old`` must occur
exactly once in the file, otherwise nothing is written.  It never touches the repo's own
src/tex copy.
"""

import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit("usage: mirror_edit.py <path-to-mirror-file> <edits.json>")
path, edits_file = Path(sys.argv[1]), Path(sys.argv[2])
if "src/tex" in str(path):
    sys.exit("refusing to edit src/tex/: edit the Dropbox mirror (SYW pulls from Overleaf)")
text = path.read_text(encoding="utf-8")
for i, edit in enumerate(json.loads(edits_file.read_text(encoding="utf-8"))):
    n = text.count(edit["old"])
    if n != 1:
        sys.exit(f"edit {i}: 'old' text occurs {n} times, expected exactly 1; nothing written")
    text = text.replace(edit["old"], edit["new"], 1)
path.write_text(text, encoding="utf-8")
print(f"applied edits to {path}")
