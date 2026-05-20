"""Integration tests for the `skillforge lint` CLI command."""

from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner

from skillforge.cli.main import cli


def test_lint_valid_skill_prints_ok(tmp_path: Path) -> None:
    """Lint a valid SKILL.md prints OK and exits 0."""
    skill_src = Path(__file__).parent.parent / "fixtures" / "skill_sample.md"
    skill_file = tmp_path / "SKILL.md"
    shutil.copy(skill_src, skill_file)

    runner = CliRunner()
    result = runner.invoke(cli, ["lint", str(skill_file)])

    assert result.exit_code == 0
    assert "OK" in result.output


def test_lint_missing_file_exits_2(tmp_path: Path) -> None:
    """Lint a non-existent file exits with non-zero code."""
    runner = CliRunner()
    result = runner.invoke(cli, ["lint", str(tmp_path / "nope.md")])

    assert result.exit_code != 0


def test_lint_invalid_skill_exits_nonzero(tmp_path: Path) -> None:
    """Lint an unparseable file exits with non-zero code."""
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("not a valid skill file")

    runner = CliRunner()
    result = runner.invoke(cli, ["lint", str(bad_file)])

    assert result.exit_code != 0


def test_lint_skill_with_errors_exits_1(tmp_path: Path) -> None:
    """Lint a skill with missing sections exits with code 1."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("""\
---
name: test-skill
description: A test skill
version: 0.1.0
source_model: mock
extracted_from:
  total_traces: 1
  passed_traces: 1
  failed_traces: 0
  extractor: reflective@0.1
  extracted_at: '2024-01-01T00:00:00+00:00'
---

No required sections here.
""")

    runner = CliRunner()
    result = runner.invoke(cli, ["lint", str(skill_file)])

    assert result.exit_code == 1
    assert "ERROR" in result.output
