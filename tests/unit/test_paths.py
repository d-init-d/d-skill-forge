"""Unit tests for skillforge.paths."""

from __future__ import annotations

import re
from pathlib import Path

from skillforge.paths import generate_ulid, now_iso, runs_dir, skills_dir


class TestGenerateUlid:
    """Tests for the ULID generator."""

    def test_length_is_26(self) -> None:
        """ULID strings are exactly 26 characters."""
        result = generate_ulid()
        assert len(result) == 26  # noqa: PLR2004

    def test_charset_valid(self) -> None:
        """ULID uses only Crockford Base32 characters."""
        result = generate_ulid()
        assert re.match(r"^[0-9A-Z]{26}$", result, re.IGNORECASE)

    def test_unique(self) -> None:
        """Two consecutive ULIDs are different."""
        a = generate_ulid()
        b = generate_ulid()
        assert a != b


class TestNowIso:
    """Tests for the ISO timestamp helper."""

    def test_iso_format(self) -> None:
        """now_iso returns a valid ISO-8601 string."""
        result = now_iso()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result)

    def test_contains_timezone(self) -> None:
        """now_iso includes timezone info."""
        result = now_iso()
        assert "+" in result or "Z" in result or result.endswith("+00:00")


class TestDirectoryHelpers:
    """Tests for runs_dir and skills_dir."""

    def test_runs_dir(self) -> None:
        """runs_dir appends 'runs' to the base path."""
        base = Path("/project")
        assert runs_dir(base) == Path("/project/runs")

    def test_skills_dir(self) -> None:
        """skills_dir appends 'skills' to the base path."""
        base = Path("/project")
        assert skills_dir(base) == Path("/project/skills")
