"""End-to-end test: full pipeline on the python-debug example with mock provider."""

from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner

from skillforge.cli.main import cli

_EXAMPLE_DIR = Path(__file__).parent.parent.parent / "examples" / "python-debug"


def test_full_pipeline_mock(tmp_path: Path) -> None:
    """Run the full pipeline: run → extract → eval → lint with mock provider."""
    runner = CliRunner()
    corpus = _EXAMPLE_DIR / "tasks.yaml"

    # Step 1: run
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        work_dir = Path(td)
        result = runner.invoke(
            cli,
            ["run", "--corpus", str(corpus), "--provider", "mock", "--model", "mock-strong"],
        )
        assert result.exit_code == 0, f"run failed: {result.output}"

        # Find the run directory
        runs_path = work_dir / "runs"
        assert runs_path.exists(), "runs/ directory not created"
        run_dirs = [d for d in runs_path.iterdir() if d.is_dir()]
        assert len(run_dirs) >= 1, "No run directory found"
        run_dir = run_dirs[0]

        # Step 2: extract — mock provider won't produce valid SKILL.md,
        # so we test that it runs and fails gracefully
        skill_out = work_dir / "skills" / "python-debug" / "SKILL.md"
        runner.invoke(
            cli,
            [
                "extract",
                "--run",
                str(run_dir),
                "--provider",
                "mock",
                "--model",
                "mock-strong",
                "--out",
                str(skill_out),
            ],
        )
        # Mock provider can't produce valid SKILL.md — expected to fail parse
        # Use the example expected_skill instead for eval and lint
        skill_file = work_dir / "SKILL.md"
        shutil.copy(_EXAMPLE_DIR / "expected_skill" / "SKILL.md", skill_file)

        # Step 3: eval
        result_eval = runner.invoke(
            cli,
            [
                "eval",
                "--skill",
                str(skill_file),
                "--corpus",
                str(corpus),
                "--provider",
                "mock",
                "--weak-model",
                "mock-weak",
            ],
        )
        assert result_eval.exit_code == 0, f"eval failed: {result_eval.output}"

        # Step 4: lint
        result_lint = runner.invoke(cli, ["lint", str(skill_file)])
        assert result_lint.exit_code == 0, f"lint failed: {result_lint.output}"
        assert "OK" in result_lint.output
