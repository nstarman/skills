"""Move tag-pinned registry entries to their repository's latest release tag.

    python scripts/bump_refs.py [--dry-run]

An entry is tag-pinned when its ref is a tag of its repository; branch-tracking entries are left
alone. Prints "name: old -> new" per bump (nothing when everything is current). A ref never moves
to an older version. Exit 1 if any entry could not be checked (the others are still bumped).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import skillreg
from skillreg import SkillError

ROOT = Path(__file__).resolve().parents[1]


def is_tag(repo: str, ref: str) -> bool:
    r = subprocess.run(["git", "ls-remote", "--tags", f"https://github.com/{repo}.git", f"refs/tags/{ref}"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SkillError(f"{repo}: git ls-remote failed ({r.stderr.strip()[:200]})")
    return bool(r.stdout.strip())


def latest_release(repo: str) -> str:
    try:
        return json.loads(skillreg.github(f"repos/{repo}/releases/latest"))["tag_name"]
    except Exception as e:  # noqa: BLE001 — any failure is reported per entry
        raise SkillError(f"cannot read the latest release of {repo} ({e})") from None


def version_key(tag: str):
    """Numeric parts of a tag (v0.10.0 > v0.2.0); None if it has none."""
    nums = re.findall(r"\d+", tag)
    return tuple(int(n) for n in nums) if nums else None


def newer(candidate: str, current: str) -> bool:
    a, b = version_key(candidate), version_key(current)
    return candidate != current and a is not None and b is not None and a > b


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print the bumps without writing")
    args = ap.parse_args(argv)
    failed = False
    for path, entry in skillreg.load_registry(root):
        if isinstance(entry, SkillError) or not isinstance(entry, dict):
            continue  # malformed entries are build_index.py's to report
        name, src = entry.get("name", path.stem), entry.get("source") or {}
        repo, ref = src.get("repo"), src.get("ref")
        try:
            if not repo or not ref or not is_tag(repo, ref):
                continue
            latest = latest_release(repo)
        except SkillError as e:
            print(f"{name}: {e}" if not str(e).startswith(f"{name}:") else e, file=sys.stderr)
            failed = True
            continue
        if newer(latest, ref):
            print(f"{name}: {ref} -> {latest}")
            if not args.dry_run:
                entry["source"]["ref"] = latest
                path.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
