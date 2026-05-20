# ruff: noqa: D102, PLR2004
"""Tests for trace recording and loading."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.errors import TraceError
from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.trace import ContentBlock, Message, Score, TokenUsage, Trace
from skillforge.recorder import Recorder, load_run


def _make_trace(task_id: str = "t1", run_id: str = "run-1") -> Trace:
    """Create a minimal trace for testing."""
    now = datetime(2024, 1, 1, tzinfo=UTC)
    return Trace(
        run_id=run_id,
        task_id=task_id,
        provider="mock",
        model="mock-model",
        started_at=now,
        finished_at=now,
        latency_ms=100,
        messages=[
            Message(role="user", content=[ContentBlock(type="text", text="hi")]),
            Message(
                role="assistant",
                content=[ContentBlock(type="text", text="hello")],
            ),
        ],
        final_output="hello",
        usage=TokenUsage(input_tokens=5, output_tokens=3),
        score=Score(passed=True, score=1.0, evaluator="exact_match"),
    )


def _make_manifest(tmp_path: Path) -> RunManifest:
    """Create a minimal manifest for testing."""
    now = datetime(2024, 1, 1, tzinfo=UTC)
    return RunManifest(
        run_id="run-1",
        started_at=now,
        finished_at=now,
        provider="mock",
        model="mock-model",
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
        task_results=[
            TaskResult(
                task_id="t1",
                trace_path=Path("traces/t1.jsonl"),
                passed=True,
                score=1.0,
            )
        ],
        total_cost_usd=0.001,
        total_latency_ms=100,
    )


class TestRecorder:
    """Tests for Recorder async context manager."""

    @pytest.mark.asyncio
    async def test_record_and_finalise(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-1"
        trace = _make_trace()
        manifest = _make_manifest(tmp_path)

        async with Recorder.open(run_dir) as recorder:
            await recorder.record_trace(trace)
            await recorder.finalise(manifest)

        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "traces" / "t1.jsonl").exists()

    @pytest.mark.asyncio
    async def test_multiple_traces_same_task(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-2"
        trace1 = _make_trace(task_id="t1")
        trace2 = _make_trace(task_id="t1")

        async with Recorder.open(run_dir) as recorder:
            await recorder.record_trace(trace1)
            await recorder.record_trace(trace2)

        lines = (run_dir / "traces" / "t1.jsonl").read_text().splitlines()
        assert len(lines) == 2

    @pytest.mark.asyncio
    async def test_multiple_tasks(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-3"

        async with Recorder.open(run_dir) as recorder:
            await recorder.record_trace(_make_trace(task_id="a"))
            await recorder.record_trace(_make_trace(task_id="b"))

        assert (run_dir / "traces" / "a.jsonl").exists()
        assert (run_dir / "traces" / "b.jsonl").exists()


class TestLoadRun:
    """Tests for load_run."""

    @pytest.mark.asyncio
    async def test_roundtrip(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-rt"
        trace = _make_trace()
        manifest = _make_manifest(tmp_path)

        async with Recorder.open(run_dir) as recorder:
            await recorder.record_trace(trace)
            await recorder.finalise(manifest)

        loaded_manifest, loaded_traces = load_run(run_dir)
        assert loaded_manifest.run_id == "run-1"
        assert len(loaded_traces) == 1
        assert loaded_traces[0].task_id == "t1"
        assert loaded_traces[0].final_output == "hello"

    def test_missing_manifest(self, tmp_path: Path) -> None:
        with pytest.raises(TraceError, match="Manifest not found"):
            load_run(tmp_path / "nonexistent")

    def test_empty_traces_dir(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "empty-run"
        run_dir.mkdir()
        manifest = _make_manifest(tmp_path)
        (run_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        loaded_manifest, loaded_traces = load_run(run_dir)
        assert loaded_manifest.run_id == "run-1"
        assert loaded_traces == []

    def test_corrupt_trace_line(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "corrupt-run"
        run_dir.mkdir()
        (run_dir / "traces").mkdir()
        manifest = _make_manifest(tmp_path)
        (run_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "traces" / "bad.jsonl").write_text("not valid json\n", encoding="utf-8")

        with pytest.raises(TraceError, match="Failed to parse trace"):
            load_run(run_dir)
