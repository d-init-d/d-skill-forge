"""Unit tests for skillforge.skill_io."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.errors import SkillFormatError
from skillforge.models.skill import ExtractionStats, Skill, SkillFrontmatter
from skillforge.skill_io import dump, parse, read, write

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_skill() -> Skill:
    """Build a minimal valid Skill for testing."""
    return Skill(
        frontmatter=SkillFrontmatter(
            name="test-skill",
            description="A test skill",
            source_model="mock-strong",
            extracted_from=ExtractionStats(
                total_traces=5,
                passed_traces=4,
                failed_traces=1,
                extractor="reflective@0.1",
                extracted_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            ),
        ),
        body="## When to use\nTesting\n\n## Procedure\nSteps",
    )


class TestParse:
    """Tests for the parse function."""

    def test_round_trip(self) -> None:
        """A skill round-trips through dump and parse."""
        original = _make_skill()
        text = dump(original)
        restored = parse(text)
        assert restored.frontmatter.name == original.frontmatter.name
        assert restored.frontmatter.description == original.frontmatter.description
        assert restored.body == original.body

    def test_parse_fixture(self) -> None:
        """Parsing the fixture skill_sample.md succeeds."""
        text = (FIXTURES / "skill_sample.md").read_text(encoding="utf-8")
        skill = parse(text)
        assert skill.frontmatter.name == "python-debug"
        assert "## When to use" in skill.body

    def test_no_frontmatter_raises(self) -> None:
        """Text without frontmatter raises SkillFormatError."""
        with pytest.raises(SkillFormatError, match="must start with"):
            parse("# Just a heading\nNo frontmatter here")

    def test_unclosed_frontmatter_raises(self) -> None:
        """Unclosed frontmatter raises SkillFormatError."""
        with pytest.raises(SkillFormatError, match="not closed"):
            parse("---\nname: test\n")

    def test_malformed_yaml_raises(self) -> None:
        """Invalid YAML in frontmatter raises SkillFormatError."""
        with pytest.raises(SkillFormatError, match="Invalid YAML"):
            parse("---\n: : : invalid\n---\nbody")

    def test_empty_frontmatter_raises(self) -> None:
        """Empty frontmatter raises SkillFormatError."""
        with pytest.raises(SkillFormatError, match="empty"):
            parse("---\n\n---\nbody")


class TestDump:
    """Tests for the dump function."""

    def test_deterministic_output(self) -> None:
        """Dump produces the same output on repeated calls."""
        skill = _make_skill()
        assert dump(skill) == dump(skill)

    def test_trailing_newline(self) -> None:
        """Dump output ends with a newline."""
        skill = _make_skill()
        assert dump(skill).endswith("\n")

    def test_starts_with_frontmatter_fence(self) -> None:
        """Dump output starts with ---."""
        skill = _make_skill()
        assert dump(skill).startswith("---\n")


class TestReadWrite:
    """Tests for read and write functions."""

    def test_write_and_read(self, tmp_path: Path) -> None:
        """Writing and reading a skill produces the same data."""
        skill = _make_skill()
        path = tmp_path / "skills" / "test" / "SKILL.md"
        write(skill, path)
        assert path.exists()
        restored = read(path)
        assert restored.frontmatter.name == skill.frontmatter.name
        assert restored.body == skill.body

    def test_read_nonexistent_raises(self) -> None:
        """Reading a nonexistent file raises SkillFormatError."""
        with pytest.raises(SkillFormatError, match="Cannot read"):
            read(Path("/nonexistent/SKILL.md"))
