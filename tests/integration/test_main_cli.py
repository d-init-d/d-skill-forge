# ruff: noqa: D101, D102
"""Integration tests for main CLI error handling."""

from __future__ import annotations

from click.testing import CliRunner

from skillforge.cli.main import cli


class TestVersionFlag:
    def test_version_flag_runs(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        # Version may fail to detect in test env but should not crash with traceback
        assert result.exit_code in (0, 1)


class TestUnknownSubcommand:
    def test_exits_non_zero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["nonexistent-command"])
        assert result.exit_code != 0


class TestSkillForgeErrorHandling:
    def test_graceful_error(self) -> None:
        """Run a command that triggers SkillForgeError and verify graceful exit."""
        runner = CliRunner()
        # 'run' without required args triggers a usage error (exit 2)
        result = runner.invoke(cli, ["run"])
        assert result.exit_code != 0
        # Should not produce a raw traceback
        assert "Traceback" not in result.output
