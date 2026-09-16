"""Resolve a skill argument to readable skill text."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_NAME_LINE_RE = re.compile(r"(?m)^name:\s*['\"]?([^\n'\"]+)")


@dataclass(frozen=True)
class ResolvedSkill:
    name: str
    source: str
    body: str
    argument: str


@dataclass(frozen=True)
class ResolveError:
    kind: str
    message: str


def default_search_roots(home: Path | None = None, cwd: Path | None = None) -> tuple[Path, ...]:
    home = home or Path.home()
    cwd = cwd or Path.cwd()
    extra = os.environ.get("JEV_PREDICT_SKILL_PATH", "")
    roots = [
        cwd / ".cursor" / "skills",
        cwd / "skills",
        home / ".cursor" / "skills",
        home / ".claude" / "skills",
        home / ".codex" / "skills",
        home / ".grok" / "skills",
    ]
    for part in extra.split(os.pathsep):
        if part.strip():
            roots.append(Path(part).expanduser())
    return tuple(roots)


def lookup_names(argument: str) -> tuple[str, ...]:
    no_slash = argument.strip().lstrip("/")
    names = {no_slash, no_slash.replace(":", "-")}
    lowered = no_slash.lower()
    if lowered in {"flow", "flow-next:flow", "flow-next-flow"}:
        names.update({"flow-next-flow", "flow-next:flow", "flow"})
    return tuple(name for name in names if name and not name.startswith("/"))


def _frontmatter_name(body: str) -> str | None:
    match = _FRONTMATTER_RE.match(body)
    if not match:
        return None
    name_match = _NAME_LINE_RE.search(match.group(1))
    if not name_match:
        return None
    return name_match.group(1).strip()


def looks_like_skill(body: str, *, source_name: str = "") -> bool:
    if _frontmatter_name(body):
        return True
    if source_name == "SKILL.md" and body.strip():
        return True
    return False


def _read_skill_file(path: Path) -> ResolvedSkill | None:
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not looks_like_skill(body, source_name=path.name):
        return None
    name = _frontmatter_name(body) or path.parent.name or path.stem
    return ResolvedSkill(name=name, source=str(path.resolve()), body=body, argument="")


def _plugin_skill_paths(name: str, home: Path) -> list[Path]:
    patterns = (
        home / ".cursor" / "plugins" / "local" / "*" / "skills" / name / "SKILL.md",
        home / ".cursor" / "plugins" / "cache" / "*" / "*" / "skills" / name / "SKILL.md",
        home / ".claude" / "plugins" / "cache" / "*" / "*" / "skills" / name / "SKILL.md",
        home / ".codex" / "skills" / name / "SKILL.md",
    )
    found: list[Path] = []
    for pattern in patterns:
        found.extend(sorted(home.glob(str(pattern.relative_to(home)))))
    return found


def _candidate_files(name: str, roots: tuple[Path, ...], home: Path) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        files.append(root / name / "SKILL.md")
        files.append(root / f"{name}.md")
        files.append(root / name)
    files.extend(_plugin_skill_paths(name, home))
    return files


def _existing_skill_path(path: Path) -> Path | None:
    if path.is_file():
        return path
    if path.is_dir():
        skill_md = path / "SKILL.md"
        if skill_md.is_file():
            return skill_md
    return None


def resolve_skill(
    argument: str | None,
    *,
    search_roots: tuple[Path, ...] | None = None,
    cwd: Path | None = None,
    home: Path | None = None,
) -> ResolvedSkill | ResolveError:
    if argument is None or not str(argument).strip():
        return ResolveError(
            kind="missing_argument",
            message="No skill was given.",
        )

    raw = str(argument).strip()
    cwd = cwd or Path.cwd()
    home = home or Path.home()
    roots = search_roots if search_roots is not None else default_search_roots(home=home, cwd=cwd)

    as_path = Path(raw).expanduser()
    if not as_path.is_absolute():
        as_path = (cwd / as_path)
    existing = _existing_skill_path(as_path)
    if existing is not None:
        resolved = _read_skill_file(existing)
        if resolved is not None:
            return ResolvedSkill(
                name=resolved.name,
                source=resolved.source,
                body=resolved.body,
                argument=raw,
            )
        return ResolveError(
            kind="unreadable_skill",
            message="Argument cannot be read as a skill.",
        )

    for name in lookup_names(raw):
        for candidate in _candidate_files(name, roots, home):
            existing = _existing_skill_path(candidate)
            if existing is None:
                continue
            resolved = _read_skill_file(existing)
            if resolved is not None:
                return ResolvedSkill(
                    name=resolved.name,
                    source=resolved.source,
                    body=resolved.body,
                    argument=raw,
                )

    if looks_like_skill(raw):
        name = _frontmatter_name(raw) or "pasted-skill"
        return ResolvedSkill(name=name, source="pasted", body=raw, argument=raw)

    return ResolveError(
        kind="unreadable_skill",
        message="Argument cannot be read as a skill.",
    )
