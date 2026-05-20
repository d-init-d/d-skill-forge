"""Lint SKILL.md files for structural and content issues."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from skillforge.models.skill import Skill  # noqa: TC001 - required at runtime

_REQUIRED_SECTIONS = ["## When to use", "## Procedure", "## Examples", "## Anti-patterns"]

_SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

_TASK_ID_PATTERN = re.compile(r"\b\w+[-_]\w+\b")

_MAX_SECTION_LINES = 400


class LintIssue(BaseModel):
    """A single lint issue found in a SKILL.md file.

    Attributes:
        severity: Whether this is an error or warning.
        message: Human-readable description of the issue.
        location: Optional location hint (section name, line range).
    """

    severity: Literal["error", "warning"]
    message: str
    location: str | None = None


def lint_skill(skill: Skill) -> list[LintIssue]:
    """Lint a Skill artifact for structural and content issues.

    Args:
        skill: The parsed Skill to lint.

    Returns:
        List of lint issues found (empty if clean).
    """
    issues: list[LintIssue] = []

    fm = skill.frontmatter
    if not fm.name:
        issues.append(LintIssue(severity="error", message="Frontmatter 'name' is empty"))
    if not fm.description:
        issues.append(LintIssue(severity="error", message="Frontmatter 'description' is empty"))
    if not fm.source_model:
        issues.append(LintIssue(severity="error", message="Frontmatter 'source_model' is empty"))

    body = skill.body
    for section in _REQUIRED_SECTIONS:
        if section not in body:
            issues.append(
                LintIssue(
                    severity="error",
                    message=f"Missing required section: {section}",
                    location="body",
                )
            )

    _check_section_lengths(body, issues)
    _check_secrets(body, issues)
    _check_examples_references(body, issues)

    return issues


def _check_section_lengths(body: str, issues: list[LintIssue]) -> None:
    """Check that no section exceeds the maximum line count."""
    lines = body.split("\n")
    section_start: int | None = None
    section_name: str | None = None

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if section_start is not None and section_name is not None:
                length = i - section_start
                if length > _MAX_SECTION_LINES:
                    issues.append(
                        LintIssue(
                            severity="warning",
                            message=f"Section '{section_name}' exceeds 400 lines ({length})",
                            location=section_name,
                        )
                    )
            section_start = i
            section_name = line.strip()

    if section_start is not None and section_name is not None:
        length = len(lines) - section_start
        if length > _MAX_SECTION_LINES:
            issues.append(
                LintIssue(
                    severity="warning",
                    message=f"Section '{section_name}' exceeds 400 lines ({length})",
                    location=section_name,
                )
            )


def _check_secrets(body: str, issues: list[LintIssue]) -> None:
    """Check for secret patterns in the body."""
    for pattern in _SECRET_PATTERNS:
        matches = pattern.findall(body)
        for match in matches:
            issues.append(
                LintIssue(
                    severity="error",
                    message=f"Potential secret detected: {match[:10]}...",
                    location="body",
                )
            )


def _check_examples_references(body: str, issues: list[LintIssue]) -> None:
    """Check that ## Examples contains at least one task_id reference."""
    examples_idx = body.find("## Examples")
    if examples_idx == -1:
        return

    next_section = body.find("\n## ", examples_idx + len("## Examples"))
    examples_text = body[examples_idx:] if next_section == -1 else body[examples_idx:next_section]

    if not _TASK_ID_PATTERN.search(examples_text):
        issues.append(
            LintIssue(
                severity="warning",
                message="No task_id reference found in ## Examples section",
                location="## Examples",
            )
        )
