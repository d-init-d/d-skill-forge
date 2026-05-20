"""Integration tests for the `skillforge doctor` CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from skillforge.cli.main import cli


def test_doctor_happy_path(tmp_path: Path) -> None:
    """Doctor exits 0 when Python >= 3.11 and disk is available."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "Python version" in result.output
        assert "skillforge version" in result.output


def test_doctor_with_workspace(tmp_path: Path) -> None:
    """Doctor shows workspace files when present."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        (Path(td) / "skillforge.toml").write_text("[project]\n")
        (Path(td) / "tasks.yaml").write_text("tasks: []\n")
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "skillforge.toml" in result.output
        assert "tasks.yaml" in result.output


def test_doctor_missing_workspace(tmp_path: Path) -> None:
    """Doctor warns when no workspace files found."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "no workspace files found" in result.output or "WARN" in result.output


def test_doctor_low_python_version(tmp_path: Path) -> None:
    """Doctor reports FAIL when Python version check fails."""
    runner = CliRunner()
    with (
        runner.isolated_filesystem(temp_dir=tmp_path),
        patch("skillforge.cli.doctor.sys") as mock_sys,
    ):
        mock_sys.version_info = (3, 9, 0, "final", 0)
        result = runner.invoke(cli, ["doctor"])
        # The command should report FAIL for Python version
        assert "Python version" in result.output
        assert result.exit_code == 1
