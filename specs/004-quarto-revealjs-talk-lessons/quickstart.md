# Quickstart: validate

```bash
python -m unittest tests.test_quarto_revealjs
tests/skills/quarto-revealjs/run.sh "$(mktemp -d)"
```

Expected: unit tests pass; `run.sh` ends "all checks passed", including: `lessons.html` overflow
check flags exactly the slide `#too-long` (Chromium and WebKit); the inlined `lessons.html`, alone in
an empty folder, passes the offline check; the share build has no `<aside class="notes">`; the
offline check passes in WebKit.
