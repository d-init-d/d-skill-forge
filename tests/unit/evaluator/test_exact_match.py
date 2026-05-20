# ruff: noqa: D101, D102
"""Tests for ExactMatchEvaluator."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from skillforge.evaluator.exact_match import ExactMatchEvaluator
from skillforge.models.task import ExpectedOutcome, Task
from skillforge.models.trace import ContentBlock, Message, Trace


def _make_trace(output: str) -> Trace:
    return Trace(
        run_id="r1",
        task_id="t1",
        provider="mock",
        model="mock-strong",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        latency_ms=10,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="q")])],
        final_output=output,
    )


class TestExactKind:
    @pytest.mark.asyncio
    async def test_exact_pass(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="exact", value="hello"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("hello"))
        assert score.passed is True
        assert score.score == 1.0

    @pytest.mark.asyncio
    async def test_exact_strips_whitespace(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="exact", value="hello"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("  hello  "))
        assert score.passed is True

    @pytest.mark.asyncio
    async def test_exact_fail(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="exact", value="hello"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("world"))
        assert score.passed is False
        assert score.score == 0.0


class TestContainsKind:
    @pytest.mark.asyncio
    async def test_contains_pass(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="contains", value="world"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("hello world!"))
        assert score.passed is True

    @pytest.mark.asyncio
    async def test_contains_fail(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="contains", value="xyz"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("hello world"))
        assert score.passed is False


class TestRegexKind:
    @pytest.mark.asyncio
    async def test_regex_pass(self) -> None:
        task = Task(
            id="t1", prompt="q", expected=ExpectedOutcome(kind="regex", value=r"\d{3}-\d{4}")
        )
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("Call 555-1234"))
        assert score.passed is True

    @pytest.mark.asyncio
    async def test_regex_fail(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="regex", value=r"^\d+$"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("not a number"))
        assert score.passed is False


class TestExecutesOk:
    @pytest.mark.asyncio
    async def test_executes_ok_pass(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="executes_ok"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("print('hello')"))
        assert score.passed is True

    @pytest.mark.asyncio
    async def test_executes_ok_fail(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="executes_ok"))
        ev = ExactMatchEvaluator()
        score = await ev.score(task, _make_trace("raise ValueError('boom')"))
        assert score.passed is False

    @pytest.mark.asyncio
    async def test_executes_ok_timeout(self) -> None:
        task = Task(id="t1", prompt="q", expected=ExpectedOutcome(kind="executes_ok"))
        ev = ExactMatchEvaluator()
        code = "import time; time.sleep(10)"
        score = await ev.score(task, _make_trace(code))
        assert score.passed is False
        assert "timed out" in (score.rationale or "").lower()
