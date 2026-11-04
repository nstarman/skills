"""Compare the installed Quarto (and the reveal.js it bundles) and plotly with the versions the
quarto-revealjs skill was verified against (quarto-revealjs/versions.json).

    python3 versions_check.py <path to versions.json>

A different bundled reveal.js fails: the guide's feature table must be re-verified (UPDATING.md).
A different Quarto or plotly version only warns, since the full tests that follow still run;
if they pass, bump versions.json.
"""
import json, re, subprocess, sys
from importlib import metadata
from pathlib import Path

want = json.loads(Path(sys.argv[1]).read_text())
quarto = subprocess.run(["quarto", "--version"], capture_output=True, text=True, check=True).stdout.strip()
share = Path(subprocess.run(["quarto", "--paths"], capture_output=True, text=True, check=True).stdout.split()[-1])
head = (share / "formats/revealjs/reveal/dist/reveal.js").read_text()[:400]
revealjs = re.search(r"reveal\.js (\d+\.\d+\.\d+)", head).group(1)
try:
    plotly = metadata.version("plotly")
except metadata.PackageNotFoundError:
    plotly = "not installed"

print(f"quarto {quarto} (verified {want['quarto']}), bundled reveal.js {revealjs} (verified {want['revealjs']}), "
      f"plotly {plotly} (verified {want['plotly']})")
for name, have in [("quarto", quarto), ("plotly", plotly)]:
    if have != want[name]:
        print(f"::warning::{name} is {have}, the skill was verified with {want[name]}; "
              f"if the tests pass, update quarto-revealjs/versions.json")
if revealjs != want["revealjs"]:
    print(f"::error::Quarto now bundles reveal.js {revealjs} (was {want['revealjs']}): re-verify the guide's "
          f"feature table and update the skill, see quarto-revealjs/UPDATING.md")
    sys.exit(1)
