# ruff: noqa: D101, D102, D107, PLR2004
"""Tests for LLMJudgeEvaluator."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from skillforge.errors import EvaluationError
from skillforge.evaluator.llm_judge import LLMJudgeEvaluator
from skillforge.models.task import ExpectedOutcome, Task
from skillforge.models.trace import ContentBlock, Message, TokenUsage, Trace
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider


def _make_task() -> Task:
    return Task(
        id="t1",
        prompt="Write a haiku",
        expected=ExpectedOutcome(
            kind="llm_judge",
            judge_rubric="Must be a valid haiku with 5-7-5 syllables.",
        ),
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
        messages=[Message(role="user", content=[ContentBlock(type="text", text="q")])],
        final_output="Code flows like water\nFunctions call themselves again\nStack overflows deep",
    )


class FakeJudgeProvider(Provider):
    """Fake provider that returns a configurable judge response."""

    name = "fake-judge"

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            content=[ContentBlock(type="text", text=self._response_text)],
            model="judge-model",
            usage=TokenUsage(input_tokens=10, output_tokens=5),
            stop_reason="end_turn",
        )

    def supports(self, model: str) -> bool:
        return True

    def estimate_cost(self, response: CompletionResponse) -> float:
        return 0.0


class TestLLMJudge:
    @pytest.mark.asyncio
    async def test_judge_pass(self) -> None:
        response = json.dumps({"passed": True, "score": 0.9, "rationale": "Good haiku"})
        provider = FakeJudgeProvider(response)
        ev = LLMJudgeEvaluator(provider=provider, model="judge-model")
        score = await ev.score(_make_task(), _make_trace())
        assert score.passed is True
        assert score.score == 0.9
        assert score.evaluator == "llm_judge:judge-model"

    @pytest.mark.asyncio
    async def test_judge_fail(self) -> None:
        response = json.dumps({"passed": False, "score": 0.2, "rationale": "Not a haiku"})
        provider = FakeJudgeProvider(response)
        ev = LLMJudgeEvaluator(provider=provider, model="judge-model")
        score = await ev.score(_make_task(), _make_trace())
        assert score.passed is False
        assert score.score == 0.2

    @pytest.mark.asyncio
    async def test_judge_invalid_json(self) -> None:
        provider = FakeJudgeProvider("not json at all")
        ev = LLMJudgeEvaluator(provider=provider, model="judge-model")
        with pytest.raises(EvaluationError, match="Failed to parse judge response"):
            await ev.score(_make_task(), _make_trace())

    @pytest.mark.asyncio
    async def test_judge_clamps_score(self) -> None:
        response = json.dumps({"passed": True, "score": 1.5, "rationale": "Over"})
        provider = FakeJudgeProvider(response)
        ev = LLMJudgeEvaluator(provider=provider, model="judge-model")
        score = await ev.score(_make_task(), _make_trace())
        assert score.score == 1.0
