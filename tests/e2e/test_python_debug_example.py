"""End-to-end test: full pipeline on the python-debug example with mock provider."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from skillforge.cli.main import cli

_EXAMPLE_DIR = Path(__file__).parent.parent.parent / "examples" / "python-debug"


def test_full_pipeline_mock(tmp_path: Path) -> None:
    """Run the full pipeline: run → extract → eval → lint with mock provider."""
    runner = CliRunner()
    corpus = _EXAMPLE_DIR / "tasks.yaml"

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        work_dir = Path(td)

        # Step 1: run
        result = runner.invoke(
            cli,
            ["run", "--corpus", str(corpus), "--provider", "mock", "--model", "mock-strong"],
        )
        assert result.exit_code == 0, f"run failed: {result.output}"

        runs_path = work_dir / "runs"
        assert runs_path.exists(), "runs/ directory not created"
        run_dirs = [d for d in runs_path.iterdir() if d.is_dir()]
        assert len(run_dirs) >= 1, "No run directory found"
        run_dir = run_dirs[0]

        # Step 2: extract — MUST produce a valid SKILL.md
        skill_out = work_dir / "skills" / "python-debug" / "SKILL.md"
        result = runner.invoke(
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
        assert result.exit_code == 0, f"extract failed: {result.output}"
        assert skill_out.exists()

        # Step 3: eval — uses the EXTRACTED skill, not a hand-authored fixture
        result = runner.invoke(
            cli,
            [
                "eval",
                "--skill",
                str(skill_out),
                "--corpus",
                str(corpus),
                "--provider",
                "mock",
                "--weak-model",
                "mock-weak",
            ],
        )
        assert result.exit_code == 0, f"eval failed: {result.output}"

        # Step 4: lint
        result = runner.invoke(cli, ["lint", str(skill_out)])
        assert result.exit_code == 0, f"lint failed: {result.output}"
