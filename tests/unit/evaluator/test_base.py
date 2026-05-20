# ruff: noqa: D101, D102
"""Tests for evaluator base class."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from skillforge.evaluator.base import Evaluator
from skillforge.models.task import ExpectedOutcome, Task
from skillforge.models.trace import ContentBlock, Message, Score, Trace


def _make_task() -> Task:
    return Task(
        id="t1",
        prompt="test",
        expected=ExpectedOutcome(kind="exact", value="hello"),
    )


def _make_trace() -> Trace:
    return Trace(
        run_id="r1",
        task_id="t1",
        provider="mock",
        model="mock-strong",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        latency_ms=10,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="test")])],
        final_output="hello",
    )


class ConcreteEvaluator(Evaluator):
    async def score(self, task: Task, trace: Trace) -> Score:
        return Score(passed=True, score=1.0, evaluator="test")


class TestEvaluatorBase:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            Evaluator()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_implementation(self) -> None:
        ev = ConcreteEvaluator()
        score = await ev.score(_make_task(), _make_trace())
        assert score.passed is True
        assert score.score == 1.0
