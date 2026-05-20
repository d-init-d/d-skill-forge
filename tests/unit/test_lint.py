# ruff: noqa: D101, D102, PLR2004
"""Tests for SKILL.md linter."""

from __future__ import annotations

from datetime import UTC, datetime

from skillforge.lint import LintIssue, lint_skill
from skillforge.models.skill import ExtractionStats, Skill, SkillFrontmatter


def _make_skill(body: str, name: str = "test-skill") -> Skill:
    return Skill(
        frontmatter=SkillFrontmatter(
            name=name,
            description="A test skill",
            source_model="mock-strong",
            extracted_from=ExtractionStats(
                total_traces=10,
                passed_traces=8,
                failed_traces=2,
                extractor="reflective@0.1",
                extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
            ),
        ),
        body=body,
    )


_VALID_BODY = """\
## When to use

Apply when debugging.

## Procedure

1. Read traceback
2. Fix issue

## Examples

### task_id: fix-error

Example fix.

## Anti-patterns

- Do not use bare except
"""


class TestLintSkill:
    def test_valid_skill_no_issues(self) -> None:
        skill = _make_skill(_VALID_BODY)
        issues = lint_skill(skill)
        assert issues == []

    def test_missing_section(self) -> None:
        body = "## When to use\nTest\n\n## Procedure\n1. Do it\n\n## Examples\n\ntask-ref\n"
        skill = _make_skill(body)
        issues = lint_skill(skill)
        errors = [i for i in issues if i.severity == "error"]
        assert any("## Anti-patterns" in i.message for i in errors)

    def test_missing_multiple_sections(self) -> None:
        body = "## When to use\nTest\n"
        skill = _make_skill(body)
        issues = lint_skill(skill)
        missing = [i for i in issues if "Missing required section" in i.message]
        assert len(missing) == 3

    def test_secret_detection_anthropic(self) -> None:
        body = _VALID_BODY + "\nsk-ant-abcdefghijklmnopqrstuvwxyz\n"
        skill = _make_skill(body)
        issues = lint_skill(skill)
        assert any("secret" in i.message.lower() for i in issues)

    def test_secret_detection_openai(self) -> None:
        body = _VALID_BODY + "\nsk-abcdefghijklmnopqrstuvwxyz\n"
        skill = _make_skill(body)
        issues = lint_skill(skill)
        assert any("secret" in i.message.lower() for i in issues)

    def test_secret_detection_aws(self) -> None:
        body = _VALID_BODY + "\nAKIA1234567890ABCDEF\n"
        skill = _make_skill(body)
        issues = lint_skill(skill)
        assert any("secret" in i.message.lower() for i in issues)

    def test_no_task_id_in_examples(self) -> None:
        body = (
            "## When to use\nTest\n\n## Procedure\n1. Do\n\n"
            "## Examples\n\nJust some text no references\n\n## Anti-patterns\n\n- None\n"
        )
        skill = _make_skill(body)
        issues = lint_skill(skill)
        warnings = [i for i in issues if i.severity == "warning"]
        assert any("task_id" in i.message for i in warnings)

    def test_section_too_long(self) -> None:
        long_section = "\n".join([f"Line {i}" for i in range(450)])
        body = (
            f"## When to use\n{long_section}\n\n## Procedure\n1. Do\n\n"
            "## Examples\n\ntask-ref\n\n## Anti-patterns\n\n- None\n"
        )
        skill = _make_skill(body)
        issues = lint_skill(skill)
        assert any("exceeds 400 lines" in i.message for i in issues)

    def test_lint_issue_model(self) -> None:
        issue = LintIssue(severity="error", message="test", location="body")
        assert issue.severity == "error"
        assert issue.location == "body"
