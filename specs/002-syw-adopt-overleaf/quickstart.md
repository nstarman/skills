# Quickstart: validating syw-adopt-overleaf

Prerequisites: Python ≥ 3.11, git, poppler (`pdftotext`, `pdftoppm`, `pdfinfo`).

1. **Unit tests** (pdf_diff, check_lists, check_build):

   ```bash
   python -m unittest discover tests
   ```

   Expected: all pass; the PDF tests are skipped only if poppler is missing (never in CI).

2. **Registry**: `python scripts/build_index.py --check` passes and lists `syw-adopt-overleaf` in
   `index.json`, the marketplace and the README table.

3. **pdf_diff by hand**: `pdf_diff.py a.pdf a.pdf` exits 0; on a copy with one changed number it
   exits 1 and prints that number under `numbers`.

4. **backup.sh on scratch data**: a throwaway repository, a throwaway folder as mirror, a fake
   `--baseline`; with no Overleaf access the script stops at `FAILED overleaf` and nothing outside
   the new backup folder changed. (The full run, with Overleaf, is part of the CP1 migration.)

5. **public_check.sh**: on a repository cloned from a bundle it fails `shared commits`; on a fresh
   `git init` repository with one commit it passes.

6. **End to end**: migrating CP1 with the skill (separate session) — success criteria SC-001 to
   SC-005 of spec.md.
