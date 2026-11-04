"""Compare the installed Sphinx, MyST-Parser, Sphinx extensions and Zensical with the versions
the diataxis skill's stack references were verified against (diataxis/versions.json).

    python3 versions_check.py <path to versions.json>

A different version only warns, since the full tests that follow still run; if they pass, bump
versions.json. A missing package fails. In GitHub Actions, `drift=true` is written to
$GITHUB_OUTPUT whenever anything differs, so the workflow can open a reminder even when the
tests pass.
"""
import json, os, sys
from importlib import metadata
from pathlib import Path

want = {k: v for k, v in json.loads(Path(sys.argv[1]).read_text()).items() if not k.startswith(("$", "verified"))}
drift = missing = False
for name, verified in want.items():
    try:
        have = metadata.version(name)
    except metadata.PackageNotFoundError:
        print(f"::error::{name} is not installed")
        missing = True
        continue
    print(f"{name} {have} (verified {verified})")
    if have != verified:
        drift = True
        print(f"::warning::{name} is {have}, the skill was verified with {verified}; "
              f"if the tests pass, update diataxis/versions.json")
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"drift={'true' if drift else 'false'}\n")
sys.exit(1 if missing else 0)
