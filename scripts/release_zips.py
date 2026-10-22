"""Build one claude.ai zip per skill, plus hashes.json, and decide whether to release.

    python scripts/release_zips.py OUT_DIR [--previous HASHES_JSON]

Each zip holds one top-level folder named after the skill, with SKILL.md and its resources and
without card.json (website metadata). External skills are fetched at their ref with a sparse git
clone. Zips are deterministic (sorted entries, fixed timestamps and permissions), so equal content
gives equal bytes. With --previous, the last line printed is "changed" or "unchanged".
A failed fetch fails the whole run, so a release never has a partial set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import skillreg
from skillreg import Skill, SkillError

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"card.json", ".DS_Store"}
EPOCH = (1980, 1, 1, 0, 0, 0)


def fetch_external(skill: Skill, dest: Path) -> None:
    """Copy an external skill's folder at its ref into `dest` (sparse, shallow clone)."""
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "repo"
        url = f"https://github.com/{skill.repo}.git"
        try:
            subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--branch", skill.ref, "--filter=blob:none",
                            "--sparse", url, str(clone)], check=True, capture_output=True, text=True)
            subprocess.run(["git", "-C", str(clone), "sparse-checkout", "set", "--no-cone", f"/{skill.path}/"],
                           check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise SkillError(f"{skill.name}: cannot fetch {skill.repo}@{skill.ref} ({e.stderr.strip()[:200]})") from None
        src = clone / skill.path
        if not (src / "SKILL.md").is_file():
            raise SkillError(f"{skill.name}: {skill.repo}/{skill.path}/SKILL.md not found at {skill.ref}")
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git"))


def write_zip(folder: Path, name: str, out: Path) -> None:
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.name not in SKIP
                   and ".git" not in p.relative_to(folder).parts)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            info = zipfile.ZipInfo(f"{name}/{p.relative_to(folder).as_posix()}", date_time=EPOCH)
            info.external_attr = (0o755 if p.stat().st_mode & 0o111 else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())


def build(root: Path, out: Path) -> dict[str, str]:
    errors, _, skills = skillreg.validate_offline(root)
    if errors:
        raise SkillError("\n".join(errors))
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    with tempfile.TemporaryDirectory() as tmp:
        for s in skills:
            if s.origin == "local":
                folder = root / s.path
            else:
                folder = Path(tmp) / s.name
                fetch_external(s, folder)
            zpath = out / f"{s.name}.zip"
            write_zip(folder, s.name, zpath)
            hashes[s.name] = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (out / "hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return hashes


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--previous", type=Path, help="hashes.json of the latest release")
    args = ap.parse_args(argv)
    try:
        hashes = build(root, args.out_dir)
    except SkillError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"built {len(hashes)} zips in {args.out_dir}")
    if args.previous is not None:
        try:
            prev = json.loads(args.previous.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            prev = {}
        diff = sorted(n for n in set(hashes) | set(prev) if hashes.get(n) != prev.get(n))
        if diff:
            print("differs: " + ", ".join(diff))
        print("changed" if diff else "unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
