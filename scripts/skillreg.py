"""Shared code for the skills registry: read local skills and registry entries, validate them.

Standard library only. Used by build_index.py, release_zips.py and bump_refs.py.
See specs/001-skills-registry/ (data-model.md, contracts/) for the formats.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = "nstarman/skills"
MARKETPLACE = "nstarman-skills"
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DESCRIPTION_MAX = 1024  # claude.ai and the Agent Skills specification
SKILL_MD_LINES = 500  # recommended maximum (a warning)
NOT_SKILLS = {".claude", ".specify", ".github", ".git", "registry", "scripts", "specs", "tests"}


class SkillError(Exception):
    """A skill, card or registry entry is malformed or cannot be read."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    origin: str  # "local" | "external"
    repo: str
    path: str
    ref: str

    @property
    def href(self) -> str:
        return f"https://github.com/{self.repo}/tree/{self.ref}/{self.path}"

    @property
    def install(self) -> str:
        return f"{self.name}@{MARKETPLACE}"

    @property
    def zip(self) -> str:
        return f"https://github.com/{REPO}/releases/latest/download/{self.name}.zip"


# ── frontmatter ──────────────────────────────────────────────────────────────

_KEY = re.compile(r"^([A-Za-z0-9_-]+):(?:\s+(.*))?$")
_BLOCK = re.compile(r"^([>|])([+-]?)\d?$")


def _block(lines: list[str], style: str, chomp: str) -> str:
    """A YAML block scalar's value from its (indented) lines."""
    content = list(lines)
    indent = min((len(ln) - len(ln.lstrip(" ")) for ln in content if ln.strip()), default=0)
    content = [ln[indent:] if ln.strip() else "" for ln in content]
    body_end = len(content)
    while body_end and not content[body_end - 1]:
        body_end -= 1
    body, tail = content[:body_end], content[body_end:]
    if style == "|":
        text = "\n".join(body)
    else:  # folded: lines joined by spaces, blank lines become newlines
        out, para = [], []
        for ln in body:
            if ln:
                para.append(ln)
            else:
                out.append(" ".join(para))
                para = []
        out.append(" ".join(para))
        text = "\n".join(out)
    if chomp == "-":
        return text
    if chomp == "+":
        return text + "\n" + "\n" * len(tail) if body else "\n" * len(tail)
    return text + "\n" if body else ""


def _scalar(raw: str, cont: list[str], key: str, source: str) -> str:
    raw = raw.strip()
    if raw.startswith('"'):
        m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', raw)
        if not m or cont:
            raise SkillError(f"{source}: {key}: unsupported or unterminated double-quoted value")
        return re.sub(r'\\(.)', lambda c: {"n": "\n", "t": "\t"}.get(c.group(1), c.group(1)), m.group(1))
    if raw.startswith("'"):
        m = re.fullmatch(r"'((?:[^']|'')*)'", raw)
        if not m or cont:
            raise SkillError(f"{source}: {key}: unsupported or unterminated single-quoted value")
        return m.group(1).replace("''", "'")
    if raw[:1] in "[{&*!|>%@`":
        raise SkillError(f"{source}: {key}: unsupported YAML value {raw[:20]!r}")
    return " ".join([raw, *(c.strip() for c in cont if c.strip())]).strip()


def parse_frontmatter(text: str, source: str = "SKILL.md") -> dict[str, str]:
    """`name` and `description` (and other plain top-level keys) from a SKILL.md's frontmatter."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise SkillError(f"{source}: no frontmatter (the file must start with ---)")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise SkillError(f"{source}: frontmatter is not closed with ---") from None
    body = lines[1:end]
    out: dict[str, str] = {}
    i = 0
    while i < len(body):
        line = body[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = _KEY.match(line)
        if not m:
            raise SkillError(f"{source}: cannot read frontmatter line {line!r}")
        key, raw = m.group(1), (m.group(2) or "")
        j = i + 1
        while j < len(body) and (not body[j].strip() or body[j][:1] in " \t"):
            j += 1
        cont = body[i + 1:j]
        i = j
        important = key in ("name", "description")
        block = _BLOCK.match(raw.strip())
        try:
            if block:
                out[key] = _block(cont, block.group(1), block.group(2))
            elif raw.strip() == "" and cont:
                if important:
                    raise SkillError(f"{source}: {key}: nested values are not supported")
                continue  # a list or mapping under another key: not needed
            else:
                out[key] = _scalar(raw, cont, key, source)
        except SkillError:
            if important:
                raise
    return out


# ── reading skills ───────────────────────────────────────────────────────────

def _read_json(path: Path, label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SkillError(f"{label}: not valid JSON ({e})") from None


def discover_local(root: Path) -> list[Skill]:
    """Top-level folders containing SKILL.md (sorted); description from card.json when readable."""
    skills = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in NOT_SKILLS):
        if not (d / "SKILL.md").is_file():
            continue
        description = ""
        try:
            card = json.loads((d / "card.json").read_text(encoding="utf-8"))
            if isinstance(card, dict) and isinstance(card.get("description"), str):
                description = card["description"]
        except (OSError, ValueError):
            pass
        skills.append(Skill(d.name, description, "local", REPO, d.name, "main"))
    return skills


def load_registry(root: Path) -> list[tuple[Path, object]]:
    """(path, parsed JSON or SkillError) for every registry/*.json, sorted by file name."""
    out = []
    for p in sorted((root / "registry").glob("*.json")):
        try:
            out.append((p, _read_json(p, f"registry/{p.name}")))
        except SkillError as e:
            out.append((p, e))
    return out


def check_skill_md(text: str, name: str, label: str) -> tuple[list[str], list[str]]:
    """Errors and warnings for one SKILL.md's frontmatter against the skill's name."""
    errors, warnings = [], []
    try:
        fm = parse_frontmatter(text, source=label)
    except SkillError as e:
        return [str(e)], []
    got = fm.get("name")
    if got != name:
        errors.append(f"{label}: name {got!r} must equal {name!r} (the folder/entry name)")
    desc = (fm.get("description") or "").strip()
    if not desc:
        errors.append(f"{label}: description is missing or empty")
    elif len(desc) > DESCRIPTION_MAX:
        errors.append(f"{label}: description is {len(desc)} characters; at most {DESCRIPTION_MAX} "
                      f"(claude.ai / Agent Skills limit)")
    if text.count("\n") > SKILL_MD_LINES:
        warnings.append(f"{label}: over {SKILL_MD_LINES} lines; consider moving detail to references/")
    return errors, warnings


def validate_offline(root: Path) -> tuple[list[str], list[str], list[Skill]]:
    """Validate local skills and registry entries without the network. Returns (errors, warnings, skills)."""
    errors: list[str] = []
    warnings: list[str] = []
    skills: list[Skill] = []

    for s in discover_local(root):
        d = root / s.name
        if not NAME_RE.match(s.name):
            errors.append(f"{s.name}: name must match [a-z0-9-] and be 1–64 characters")
        card_path = d / "card.json"
        if not card_path.exists():
            errors.append(f"{s.name}: no card.json")
        else:
            try:
                card = _read_json(card_path, f"{s.name}/card.json")
                if not isinstance(card, dict) or set(card) != {"name", "description"}:
                    errors.append(f"{s.name}/card.json: must be an object with exactly the keys name, description")
                elif not all(isinstance(v, str) and v.strip() for v in card.values()):
                    errors.append(f"{s.name}/card.json: name and description must be non-empty strings")
                elif card["name"] != s.name:
                    errors.append(f"{s.name}/card.json: name {card['name']!r} must equal the folder name")
            except SkillError as e:
                errors.append(str(e))
        e2, w2 = check_skill_md((d / "SKILL.md").read_text(encoding="utf-8"), s.name, f"{s.name}/SKILL.md")
        e2 = [e.replace("(the folder/entry name)", "(the folder name)") for e in e2]
        errors += e2
        warnings += w2
        skills.append(s)

    for p, entry in load_registry(root):
        label = f"registry/{p.name}"
        if isinstance(entry, SkillError):
            errors.append(str(entry))
            continue
        if not isinstance(entry, dict) or set(entry) != {"name", "description", "source"}:
            errors.append(f"{label}: must be an object with exactly the keys name, description, source")
            continue
        name, desc, src = entry["name"], entry["description"], entry["source"]
        if not isinstance(name, str) or not NAME_RE.match(name):
            errors.append(f"{label}: name must match [a-z0-9-] and be 1–64 characters")
            continue
        if name != p.stem:
            errors.append(f"{label}: name {name!r} must equal the file name")
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f"{label}: description must be a non-empty string")
        if not isinstance(src, dict) or set(src) != {"repo", "path", "ref"}:
            errors.append(f"{label}: source must have exactly the keys repo, path, ref")
            continue
        if not isinstance(src["repo"], str) or not REPO_RE.match(src["repo"]):
            errors.append(f"{label}: source.repo must be owner/repo")
        path = src["path"]
        if not isinstance(path, str) or not path.strip() or path.startswith("/") or ".." in path.split("/"):
            errors.append(f"{label}: source.path must be a relative folder without .. or a leading /")
        if not isinstance(src["ref"], str) or not src["ref"].strip():
            errors.append(f"{label}: source.ref must be a non-empty tag or branch")
        skills.append(Skill(name, desc if isinstance(desc, str) else "", "external",
                            str(src["repo"]), str(path), str(src["ref"])))

    seen: dict[str, str] = {}
    for s in skills:
        if s.name in seen:
            kinds = {seen[s.name], s.origin}
            what = ("both a local skill and a registry entry" if kinds == {"local", "external"}
                    else "registered twice")
            errors.append(f"{s.name}: is {what}; skill names must be unique")
        seen[s.name] = s.origin
    return errors, warnings, sorted(skills, key=lambda s: s.name)


# ── GitHub ───────────────────────────────────────────────────────────────────

def github(path: str, accept: str = "application/vnd.github+json", token: str | None = None) -> bytes:
    """GET https://api.github.com/<path> (with GITHUB_TOKEN when available)."""
    token = token if token is not None else os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={
        "Accept": accept, "User-Agent": "nstarman-skills", "X-GitHub-Api-Version": "2022-11-28",
        **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_skill_md(skill: Skill, token: str | None = None) -> str:
    """The SKILL.md of an external skill at its ref."""
    q = urllib.parse.quote
    try:
        return github(f"repos/{skill.repo}/contents/{q(skill.path)}/SKILL.md?ref={q(skill.ref, safe='')}",
                      accept="application/vnd.github.raw+json", token=token).decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise SkillError(f"{skill.name}: {skill.repo}/{skill.path}/SKILL.md not found at {skill.ref}") from None
        raise SkillError(f"{skill.name}: GitHub returned {e.code} for {skill.repo}@{skill.ref}") from None
    except urllib.error.URLError as e:
        raise SkillError(f"{skill.name}: cannot reach GitHub ({e.reason})") from None
