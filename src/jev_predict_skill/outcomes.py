"""Extract a closed decision-outcome set from skill text (host code, not Jev)."""

from __future__ import annotations

import re

from jev_predict_skill.constants import (
    FLOW_NEXT_FLOW_ALIASES,
    FLOW_NEXT_FLOW_OUTCOMES,
    OUTCOME_SECTION_TITLES,
    TABLE_OUTCOME_HEADERS,
)

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_YAML_LIST_RE = re.compile(
    r"(?ms)^outcomes:\s*\n((?:^[ \t]*-[ \t].+\n?)+)"
)
_BULLET_RE = re.compile(r"^[ \t]*[-*+]\s+(.+)$")


def _frontmatter_name(body: str) -> str | None:
    match = _FRONTMATTER_RE.match(body)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return None


def is_flow_next_flow(name: str, argument: str = "", body: str = "") -> bool:
    candidates = {name.strip(), argument.strip(), (_frontmatter_name(body) or "")}
    normalized = set()
    for item in candidates:
        if not item:
            continue
        normalized.add(item)
        normalized.add(item.lstrip("/"))
        normalized.add(item.lstrip("/").replace(":", "-"))
    return bool(normalized & FLOW_NEXT_FLOW_ALIASES)


def _clean_label(raw: str) -> str:
    text = raw.strip().strip("`")
    text = re.sub(r"^\[(.+?)\]\(.+?\)$", r"\1", text)
    text = text.strip().strip("*_").strip()
    if text.startswith("/") and " " not in text:
        text = text.lstrip("/")
        text = text.replace("flow-next:", "")
        text = text.replace("flow-next-", "")
    return text


def _frontmatter_outcomes(body: str) -> list[str]:
    match = _YAML_LIST_RE.search(body)
    if not match:
        return []
    labels: list[str] = []
    for line in match.group(1).splitlines():
        bullet = _BULLET_RE.match(line)
        if not bullet:
            continue
        label = _clean_label(bullet.group(1))
        if label:
            labels.append(label)
    return labels


def _section_outcomes(body: str) -> list[str]:
    headings = list(_HEADING_RE.finditer(body))
    for index, heading in enumerate(headings):
        title = heading.group(2).strip().lower()
        if title not in OUTCOME_SECTION_TITLES:
            continue
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        block = body[start:end]
        labels: list[str] = []
        for line in block.splitlines():
            bullet = _BULLET_RE.match(line)
            if not bullet:
                continue
            label = _clean_label(bullet.group(1))
            if label:
                labels.append(label)
        if labels:
            return labels
    return []


def _table_outcomes(body: str) -> list[str]:
    lines = body.splitlines()
    labels: list[str] = []
    for index, line in enumerate(lines):
        if "|" not in line:
            continue
        cells = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        if not any(cell in TABLE_OUTCOME_HEADERS for cell in cells):
            continue
        if index + 1 >= len(lines) or not re.search(r"\|\s*-+", lines[index + 1]):
            continue
        header_index = next(
            i for i, cell in enumerate(cells) if cell in TABLE_OUTCOME_HEADERS
        )
        for row in lines[index + 2 :]:
            if "|" not in row:
                break
            if re.search(r"^\s*\|?\s*-+", row):
                continue
            row_cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if header_index >= len(row_cells):
                continue
            label = _clean_label(row_cells[header_index])
            if label and label.lower() not in TABLE_OUTCOME_HEADERS:
                labels.append(label)
        if labels:
            return labels
    return []


def extract_outcomes(body: str, *, name: str = "", argument: str = "") -> tuple[str, ...] | None:
    if is_flow_next_flow(name, argument, body):
        return FLOW_NEXT_FLOW_OUTCOMES

    for extracted in (
        _frontmatter_outcomes(body),
        _section_outcomes(body),
        _table_outcomes(body),
    ):
        unique: list[str] = []
        seen: set[str] = set()
        for label in extracted:
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(label)
        if unique:
            return tuple(unique)
    return None
