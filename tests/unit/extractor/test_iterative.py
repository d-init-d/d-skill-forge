# ruff: noqa: D101, PLR2004
"""Tests for IterativeExtractor."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import pytest

from skillforge.errors import ExtractionError
from skillforge.extractor._prompts import ITERATIVE_EXTRACTION_MARKER
from skillforge.extractor.iterative import IterativeExtractor
from skillforge.models.run import RunManifest
from skillforge.models.trace import ContentBlock, Message, Score, Trace
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider
from skillforge.providers.mock import MockProvider


def _make_manifest() -> RunManifest:
    return RunManifest(
        run_id="r1",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        provider="mock",
        model="mock-strong",
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
    )


def _make_trace(task_id: str, passed: bool) -> Trace:
    return Trace(
        run_id="r1",
        task_id=task_id,
        provider="mock",
        model="mock-strong",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        latency_ms=10,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="q")])],
        final_output=f"output-{task_id}",
        score=Score(passed=passed, score=1.0 if passed else 0.0, evaluator="test"),
    )


class TestIterativeExtractorSingleRound:
    @pytest.mark.asyncio
    async def test_max_rounds_1_same_as_reflective(self) -> None:
        """max_rounds=1 produces a single reflective pass."""
        provider = MockProvider()
        ext = IterativeExtractor(max_rounds=1)
        traces = [_make_trace(f"t{i}", passed=True) for i in range(3)]

        skill = await ext.extract(_make_manifest(), traces, provider, "mock-strong")
        assert skill.frontmatter.name.startswith("mock-extracted-")
        assert "## When to use" in skill.body


class TestIterativeExtractorConvergence:
    @pytest.mark.asyncio
    async def test_max_rounds_3_converges_with_mock(self) -> None:
        """Mock returns same skill each round, so iterative converges."""
        provider = MockProvider()
        ext = IterativeExtractor(max_rounds=3)
        traces = [_make_trace(f"t{i}", passed=True) for i in range(3)]

        skill = await ext.extract(_make_manifest(), traces, provider, "mock-strong")
        assert skill.frontmatter.name.startswith("mock-extracted-")


class TestIterativeExtractorErrors:
    @pytest.mark.asyncio
    async def test_missing_traces_raises(self) -> None:
        """Empty traces list raises ExtractionError."""
        provider = MockProvider()
        ext = IterativeExtractor(max_rounds=3)

        with pytest.raises(ExtractionError, match="requires at least one trace"):
            await ext.extract(_make_manifest(), [], provider, "mock-strong")


class TestIterativePromptMarker:
    @pytest.mark.asyncio
    async def test_prompt_contains_marker_on_round_2(self) -> None:
        """Verify refinement prompt includes ITERATIVE_EXTRACTION_MARKER."""
        captured_prompts: list[str] = []

        class CapturingProvider(Provider):
            name: ClassVar[str] = "capturing"

            def __init__(self) -> None:
                self._call_count = 0
                self._mock = MockProvider()

            async def complete(self, request: CompletionRequest) -> CompletionResponse:
                self._call_count += 1
                for msg in request.messages:
                    for block in msg.content:
                        if block.type == "text" and block.text:
                            captured_prompts.append(block.text)
                return await self._mock.complete(request)

            def supports(self, model: str) -> bool:
                return True

            def estimate_cost(self, response: CompletionResponse) -> float:
                return 0.0

        provider = CapturingProvider()
        ext = IterativeExtractor(max_rounds=2)
        traces = [_make_trace(f"t{i}", passed=True) for i in range(3)]

        await ext.extract(_make_manifest(), traces, provider, "mock-strong")

        # Round 1 uses reflective marker, round 2 uses iterative marker
        assert len(captured_prompts) >= 2
        assert ITERATIVE_EXTRACTION_MARKER in captured_prompts[1]


class TestIterativeEarlyStop:
    @pytest.mark.asyncio
    async def test_early_stop_when_identical(self) -> None:
        """Stops early when refinement output is identical to previous."""
        call_count = 0

        class CountingProvider(Provider):
            name: ClassVar[str] = "counting"

            def __init__(self) -> None:
                self._mock = MockProvider()

            async def complete(self, request: CompletionRequest) -> CompletionResponse:
                nonlocal call_count
                call_count += 1
                return await self._mock.complete(request)

            def supports(self, model: str) -> bool:
                return True

            def estimate_cost(self, response: CompletionResponse) -> float:
                return 0.0

        provider = CountingProvider()
        ext = IterativeExtractor(max_rounds=5)
        traces = [_make_trace(f"t{i}", passed=True) for i in range(3)]

        await ext.extract(_make_manifest(), traces, provider, "mock-strong")

        # Mock returns deterministic output, so it should stop early
        # Round 1 (reflective) + at most 1 refinement round before convergence
        assert call_count < 5
