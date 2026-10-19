# Quoting numbers: the `\variable{}` plumbing

The text never contains a typed result. A result goes through four steps:

1. A `calc_*.py` script computes it and writes it with `write_values(__file__, {...})` into a
   JSON file under `src/data/derived/`.
2. An exporter script (`make_variables.py`) reads those JSON files and `variables.yml` and
   renders each number as a one-line `.tex` file (`src/tex/output/<group>/<name>.tex`),
   choosing the format (significant figures, percent, a range) in one place.
3. `ms.tex` cites it as `\variable{output/<group>/<name>.tex}`.
4. SYW generates only the variables `ms.tex` cites, and pushes them to Overleaf at the end of
   a build.

Consequences:

- A new number needs: the value in a `calc_*` script, a line in the exporter, the citation in
  the text, and a build. Until the build has pushed, Overleaf cannot compile the citation.
- To change how a number looks, change the exporter, not the text.
- Constants that define a model or a test (a halo shape, a radius range) belong in
  `variables.yml` and are cited from there, so the paper and the code cannot disagree.
- Describe what a number is in the text, and let the variable carry its value. If you must
  quote a computed number in chat, quote it from the generated file, not from memory.
