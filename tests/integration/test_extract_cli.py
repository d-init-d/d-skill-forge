"""Integration tests for the `skillforge extract` CLI command."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from click.testing import CliRunner

from skillforge.cli.main import cli
from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.trace import ContentBlock, Message, Score, Trace


def _create_run_dir(tmp_path: Path) -> Path:
    """Create a minimal run directory with manifest and traces."""
    run_dir = tmp_path / "runs" / "test-run"
    traces_dir = run_dir / "traces"
    traces_dir.mkdir(parents=True)

    manifest = RunManifest(
        run_id="test-run",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
        provider="mock",
        model="mock-strong",
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
        task_results=[
            TaskResult(task_id="t1", trace_path=Path("traces/t1.jsonl"), passed=True, score=1.0)
        ],
    )
    (run_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2))

    trace = Trace(
        run_id="test-run",
        task_id="t1",
        provider="mock",
        model="mock-strong",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
        latency_ms=1000,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="test")])],
        final_output="4",
        score=Score(passed=True, score=1.0, rationale="ok", evaluator="exact_match"),
    )
    (traces_dir / "t1.jsonl").write_text(trace.model_dump_json() + "\n")

    return run_dir


def test_extract_with_mock_reports_parse_error(tmp_path: Path) -> None:
    """Extract with mock provider fails gracefully when output isn't valid SKILL.md."""
    run_dir = _create_run_dir(tmp_path)
    out_path = tmp_path / "output" / "SKILL.md"

    runner = CliRunner()
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
            str(out_path),
        ],
    )

    # Mock provider doesn't produce valid SKILL.md, so extraction fails gracefully
    assert result.exit_code != 0
    assert "Extraction failed" in result.output or "Error" in result.output


def test_extract_empty_run_exits_nonzero(tmp_path: Path) -> None:
    """Extract with no traces exits with non-zero code."""
    run_dir = tmp_path / "empty-run"
    run_dir.mkdir(parents=True)

    manifest = RunManifest(
        run_id="empty",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        provider="mock",
        model="mock-strong",
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
        task_results=[],
    )
    (run_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["extract", "--run", str(run_dir), "--provider", "mock"],
    )

    assert result.exit_code != 0
