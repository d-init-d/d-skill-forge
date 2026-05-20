"""Integration tests for the `skillforge eval` CLI command."""

from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner

from skillforge.cli.main import cli

_CORPUS = """\
version: 1
name: "eval-corpus"
description: "Eval test corpus."
domain: "test"
tasks:
  - id: "t1"
    prompt: "What is 2 + 2?"
    expected:
      kind: "exact"
      value: "4"
"""


def test_eval_prints_delta_table(tmp_path: Path) -> None:
    """Eval with mock provider prints a results table and updates SKILL.md."""
    corpus_file = tmp_path / "tasks.yaml"
    corpus_file.write_text(_CORPUS)

    # Copy sample skill to tmp
    skill_src = Path(__file__).parent.parent / "fixtures" / "skill_sample.md"
    skill_file = tmp_path / "SKILL.md"
    shutil.copy(skill_src, skill_file)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "eval",
            "--skill",
            str(skill_file),
            "--corpus",
            str(corpus_file),
            "--provider",
            "mock",
            "--weak-model",
            "mock-weak",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Baseline score" in result.output or "baseline_score" in result.output
    assert "EvalReport appended" in result.output

    # Verify skill file was updated
    content = skill_file.read_text()
    assert "target_model" in content or "mock-weak" in content
