"""Integration tests for the `skillforge run` CLI command."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - used at runtime in test bodies

from click.testing import CliRunner

from skillforge.cli.main import cli

_CORPUS = """\
version: 1
name: "test-corpus"
description: "Test corpus."
domain: "test"
tasks:
  - id: "t1"
    prompt: "What is 2 + 2?"
    expected:
      kind: "exact"
      value: "4"
"""


def test_run_creates_traces(tmp_path: Path) -> None:
    """Run with mock provider creates a run directory with traces."""
    corpus_file = tmp_path / "tasks.yaml"
    corpus_file.write_text(_CORPUS)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            ["run", "--corpus", str(corpus_file), "--provider", "mock", "--model", "mock-strong"],
        )

    assert result.exit_code == 0, result.output
    assert "Run complete" in result.output
    assert "Path:" in result.output


def test_run_missing_corpus_fails() -> None:
    """Run with non-existent corpus file fails."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["run", "--corpus", "/nonexistent/nope.yaml", "--provider", "mock"],
    )

    assert result.exit_code != 0
