# ruff: noqa: D101, D102, PLR2004
"""Tests for evaluator runner utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.evaluator.exact_match import ExactMatchEvaluator
from skillforge.evaluator.runner import EvalDelta, compare_runs, evaluate_run
from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.task import ExpectedOutcome, Task, TaskCorpus
from skillforge.models.trace import ContentBlock, Message, Score, Trace


def _make_trace(task_id: str, output: str, passed: bool) -> Trace:
    return Trace(
        run_id="r1",
        task_id=task_id,
        provider="mock",
        model="mock-strong",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        latency_ms=10,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="q")])],
        final_output=output,
        score=Score(passed=passed, score=1.0 if passed else 0.0, evaluator="test"),
    )


def _make_manifest(results: list[TaskResult]) -> RunManifest:
    return RunManifest(
        run_id="r1",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        provider="mock",
        model="mock-strong",
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
        task_results=results,
    )


class TestEvaluateRun:
    @pytest.mark.asyncio
    async def test_evaluate_updates_manifest(self) -> None:
        corpus = TaskCorpus(
            version=1,
            name="test",
            description="test",
            domain="test",
            tasks=[
                Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="exact", value="4")),
            ],
        )
        traces = [_make_trace("t1", "4", passed=True)]
        manifest = _make_manifest([])
        evaluator = ExactMatchEvaluator()

        result = await evaluate_run(manifest, traces, corpus, evaluator)
        assert len(result.task_results) == 1
        assert result.task_results[0].passed is True

    @pytest.mark.asyncio
    async def test_evaluate_skips_unknown_tasks(self) -> None:
        corpus = TaskCorpus(
            version=1,
            name="test",
            description="test",
            domain="test",
            tasks=[
                Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="exact", value="4")),
            ],
        )
        traces = [_make_trace("unknown-task", "4", passed=True)]
        manifest = _make_manifest([])
        evaluator = ExactMatchEvaluator()

        result = await evaluate_run(manifest, traces, corpus, evaluator)
        assert len(result.task_results) == 0


class TestCompareRuns:
    def test_compare_basic(self) -> None:
        baseline = _make_manifest(
            [
                TaskResult(task_id="t1", trace_path=Path("x"), passed=False, score=0.3),
                TaskResult(task_id="t2", trace_path=Path("x"), passed=True, score=0.8),
            ]
        )
        with_skill = _make_manifest(
            [
                TaskResult(task_id="t1", trace_path=Path("x"), passed=True, score=0.9),
                TaskResult(task_id="t2", trace_path=Path("x"), passed=True, score=1.0),
            ]
        )

        delta = compare_runs(baseline, with_skill)
        assert delta.tasks_evaluated == 2
        assert delta.baseline_score == pytest.approx(0.55)
        assert delta.with_skill_score == pytest.approx(0.95)
        assert delta.delta == pytest.approx(0.4)

    def test_compare_no_common_tasks(self) -> None:
        baseline = _make_manifest(
            [
                TaskResult(task_id="t1", trace_path=Path("x"), passed=True, score=1.0),
            ]
        )
        with_skill = _make_manifest(
            [
                TaskResult(task_id="t2", trace_path=Path("x"), passed=True, score=1.0),
            ]
        )

        delta = compare_runs(baseline, with_skill)
        assert delta.tasks_evaluated == 0
        assert delta.delta == 0.0

    def test_eval_delta_model(self) -> None:
        d = EvalDelta(baseline_score=0.5, with_skill_score=0.8, delta=0.3, tasks_evaluated=5)
        assert d.delta == 0.3
