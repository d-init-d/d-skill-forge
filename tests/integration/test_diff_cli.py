"""Integration tests for the `skillforge diff` CLI command."""

from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner

from skillforge.cli.main import cli

_FIXTURE = Path(__file__).parent.parent / "fixtures" / "skill_sample.md"


def test_diff_identical_skills_exits_0(tmp_path: Path) -> None:
    """Two identical skills produce exit 0."""
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    shutil.copy(_FIXTURE, a)
    shutil.copy(_FIXTURE, b)

    runner = CliRunner()
    result = runner.invoke(cli, ["diff", str(a), str(b)])

    assert result.exit_code == 0
    assert "identical" in result.output.lower()


def test_diff_different_body_exits_1(tmp_path: Path) -> None:
    """Skills with different body produce exit 1 and diff markers."""
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    shutil.copy(_FIXTURE, a)
    shutil.copy(_FIXTURE, b)

    # Modify body of b
    text = b.read_text(encoding="utf-8")
    b.write_text(text.replace("## Anti-patterns", "## Changed section"), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["diff", str(a), str(b)])

    assert result.exit_code == 1
    assert "---" in result.output or "+++" in result.output


def test_diff_different_frontmatter_exits_1(tmp_path: Path) -> None:
    """Skills with different frontmatter produce exit 1."""
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    shutil.copy(_FIXTURE, a)
    shutil.copy(_FIXTURE, b)

    # Modify frontmatter of b
    text = b.read_text(encoding="utf-8")
    b.write_text(text.replace("version: 0.1.0", "version: 0.2.0"), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["diff", str(a), str(b)])

    assert result.exit_code == 1
    assert "version" in result.output
