"""Read and write SKILL.md files with YAML frontmatter.

Provides parse/dump/read/write operations for Skill artifacts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from skillforge.errors import SkillFormatError
from skillforge.models.skill import Skill, SkillFrontmatter

if TYPE_CHECKING:
    from pathlib import Path


def parse(text: str) -> Skill:
    """Parse a SKILL.md text into a Skill instance.

    The text must have YAML frontmatter delimited by --- fences,
    followed by a markdown body.

    Args:
        text: Raw SKILL.md content.

    Returns:
        A validated Skill instance.

    Raises:
        SkillFormatError: If frontmatter is missing or invalid.
    """
    text = text.strip()
    if not text.startswith("---"):
        msg = "SKILL.md must start with YAML frontmatter (---)"
        raise SkillFormatError(msg)

    # Find the closing ---
    end_idx = text.find("---", 3)
    if end_idx == -1:
        msg = "SKILL.md frontmatter is not closed (missing closing ---)"
        raise SkillFormatError(msg)

    frontmatter_text = text[3:end_idx].strip()
    body = text[end_idx + 3 :].lstrip("\n").rstrip()

    if not frontmatter_text:
        msg = "SKILL.md frontmatter is empty"
        raise SkillFormatError(msg)

    try:
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        msg = f"Invalid YAML in frontmatter: {e}"
        raise SkillFormatError(msg) from e

    if not isinstance(data, dict):
        msg = "Frontmatter must be a YAML mapping"
        raise SkillFormatError(msg)

    try:
        frontmatter = SkillFrontmatter.model_validate(data)
    except Exception as e:
        msg = f"Invalid frontmatter fields: {e}"
        raise SkillFormatError(msg) from e

    return Skill(frontmatter=frontmatter, body=body)


def dump(skill: Skill) -> str:
    """Serialize a Skill to SKILL.md text format.

    Produces deterministic output with sorted YAML keys, LF line endings,
    and a trailing newline.

    Args:
        skill: The Skill instance to serialize.

    Returns:
        SKILL.md formatted string.
    """
    frontmatter_data = skill.frontmatter.model_dump(mode="json")
    frontmatter_yaml = yaml.dump(
        frontmatter_data,
        default_flow_style=False,
        sort_keys=True,
        allow_unicode=True,
    ).strip()

    return f"---\n{frontmatter_yaml}\n---\n\n{skill.body}\n"


def read(path: Path) -> Skill:
    """Read and parse a SKILL.md file from disk.

    Args:
        path: Path to the SKILL.md file.

    Returns:
        A validated Skill instance.

    Raises:
        SkillFormatError: If the file cannot be read or parsed.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        msg = f"Cannot read skill file: {path}: {e}"
        raise SkillFormatError(msg) from e

    return parse(text)


def write(skill: Skill, path: Path) -> None:
    """Write a Skill to disk as a SKILL.md file.

    Creates parent directories if they don't exist.

    Args:
        skill: The Skill instance to write.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(skill), encoding="utf-8", newline="\n")
