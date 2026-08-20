#!/usr/bin/env python3
"""Validate the essential structure of a Codex skill without third-party packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9-]{1,63}$")
FIELD_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.+?)\s*$")


def parse_frontmatter(text: str) -> dict[str, str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        header, _body = normalized[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("YAML frontmatter is not closed") from exc

    fields: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip():
            continue
        match = FIELD_RE.match(line)
        if not match:
            raise ValueError(f"unsupported frontmatter line: {line}")
        key, value = match.groups()
        fields[key] = value.strip("'\"")
    return fields


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["SKILL.md not found"]

    try:
        text = skill_file.read_text(encoding="utf-8")
        fields = parse_frontmatter(text)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]

    name = fields.get("name", "")
    description = fields.get("description", "")

    if not NAME_RE.fullmatch(name):
        errors.append("name must use lowercase letters, digits, and hyphens (max 63)")
    if name and skill_dir.name != name:
        errors.append(f"folder name '{skill_dir.name}' must match skill name '{name}'")
    if not description:
        errors.append("description is required")
    if "TODO" in text:
        errors.append("unfinished TODO marker found")
    if not (skill_dir / "agents" / "openai.yaml").is_file():
        errors.append("agents/openai.yaml not found")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_skill.py PATH_TO_SKILL", file=sys.stderr)
        return 2

    skill_dir = Path(sys.argv[1]).resolve()
    errors = validate(skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Valid skill: {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
