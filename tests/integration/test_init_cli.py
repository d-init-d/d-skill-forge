"""Integration tests for the `skillforge init` CLI command."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - needed at runtime for tmp_path

from click.testing import CliRunner

from skillforge.cli.main import cli
from skillforge.tasks import load_corpus


def test_init_creates_project(tmp_path: Path) -> None:
    """Init creates skillforge.toml, tasks.yaml, and skills/ dir."""
    runner = CliRunner()
    target = tmp_path / "myproject"
    result = runner.invoke(cli, ["init", str(target)])

    assert result.exit_code == 0
    assert (target / "skillforge.toml").exists()
    assert (target / "tasks.yaml").exists()
    assert (target / "skills").is_dir()


def test_init_nonempty_dir_exits_2(tmp_path: Path) -> None:
    """Init exits with code 2 if directory is non-empty."""
    target = tmp_path / "existing"
    target.mkdir()
    (target / "file.txt").write_text("content")

    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(target)])

    assert result.exit_code != 0
    assert "non-empty" in result.output


def test_init_tasks_yaml_is_valid(tmp_path: Path) -> None:
    """Generated tasks.yaml validates against TaskCorpus model."""
    runner = CliRunner()
    target = tmp_path / "proj"
    runner.invoke(cli, ["init", str(target)])

    corpus = load_corpus(target / "tasks.yaml")
    assert len(corpus.tasks) >= 1
