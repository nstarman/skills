"""Compare the installed Quarto (and the reveal.js it bundles) and plotly with the versions the
quarto-revealjs skill was verified against (quarto-revealjs/versions.json).

    python3 versions_check.py <path to versions.json>

A different bundled reveal.js fails: the guide's feature table must be re-verified (UPDATING.md).
A different Quarto or plotly only warns, since the full tests that follow still run; if they
pass, bump versions.json. In GitHub Actions, `drift=true` is written to $GITHUB_OUTPUT whenever
anything differs, so the workflow can open a reminder even when the tests pass.
"""
import json, os, re, subprocess, sys
from importlib import metadata
from pathlib import Path

want = json.loads(Path(sys.argv[1]).read_text())
run = lambda *a: subprocess.run(["quarto", *a], capture_output=True, text=True, check=True).stdout
quarto = run("--version").strip()
share = Path(run("--paths").splitlines()[-1].strip())   # second line: the share directory
reveal_js = share / "formats/revealjs/reveal/dist/reveal.js"
m = re.search(r"reveal\.js (\d+\.\d+\.\d+)", reveal_js.read_text()[:400])
if not m:
    sys.exit(f"::error::cannot read the reveal.js version from the header of {reveal_js}")
revealjs = m.group(1)
try:
    plotly = metadata.version("plotly")
except metadata.PackageNotFoundError:
    plotly = "not installed"

print(f"quarto {quarto} (verified {want['quarto']}), bundled reveal.js {revealjs} (verified {want['revealjs']}), "
      f"plotly {plotly} (verified {want['plotly']})")
drift = False
for name, have in [("quarto", quarto), ("plotly", plotly), ("revealjs", revealjs)]:
    if have != want[name]:
        drift = True
        if name != "revealjs":
            print(f"::warning::{name} is {have}, the skill was verified with {want[name]}; "
                  f"if the tests pass, update quarto-revealjs/versions.json")
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"drift={'true' if drift else 'false'}\n")
if revealjs != want["revealjs"]:
    print(f"::error::Quarto now bundles reveal.js {revealjs} (was {want['revealjs']}): re-verify the guide's "
          f"feature table and update the skill, see quarto-revealjs/UPDATING.md")
    sys.exit(1)
