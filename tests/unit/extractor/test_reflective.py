# ruff: noqa: D101, D102, D107, PLR2004
"""Tests for ReflectiveExtractor."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import pytest

from skillforge.errors import ExtractionError
from skillforge.extractor.reflective import ReflectiveExtractor
from skillforge.models.run import RunManifest
from skillforge.models.trace import ContentBlock, Message, Score, TokenUsage, Trace
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider

_VALID_SKILL_MD = """\
---
name: test-skill
description: A test skill for debugging
version: 0.1.0
source_model: mock-strong
extracted_from:
  total_traces: 5
  passed_traces: 4
  failed_traces: 1
  extractor: reflective@0.1
  extracted_at: '2024-01-01T00:00:00+00:00'
triggers:
  - error
domains:
  - python
license: Apache-2.0
---

## When to use

When debugging Python errors.

## Procedure

1. Read the traceback
2. Fix the issue

## Examples

### task_id: fix-type-error

Fix type errors by casting.

## Anti-patterns

- Do not use bare except
"""


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
        final_output="output",
        score=Score(passed=passed, score=1.0 if passed else 0.0, evaluator="test"),
    )


class FakeExtractionProvider(Provider):
    """Provider that returns a valid SKILL.md."""

    name: ClassVar[str] = "fake-extract"

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            content=[ContentBlock(type="text", text=self._response_text)],
            model="mock-strong",
            usage=TokenUsage(input_tokens=100, output_tokens=200),
            stop_reason="end_turn",
        )

    def supports(self, model: str) -> bool:
        return True

    def estimate_cost(self, response: CompletionResponse) -> float:
        return 0.0


class TestReflectiveExtractor:
    @pytest.mark.asyncio
    async def test_extract_success(self) -> None:
        provider = FakeExtractionProvider(_VALID_SKILL_MD)
        ext = ReflectiveExtractor()
        traces = [_make_trace(f"t{i}", passed=i < 4) for i in range(5)]

        skill = await ext.extract(_make_manifest(), traces, provider, "mock-strong")
        assert skill.frontmatter.name == "test-skill"
        assert "## When to use" in skill.body

    @pytest.mark.asyncio
    async def test_extract_parse_failure(self) -> None:
        provider = FakeExtractionProvider("not a valid skill.md")
        ext = ReflectiveExtractor()
        traces = [_make_trace("t1", passed=True)]

        with pytest.raises(ExtractionError, match="Failed to parse"):
            await ext.extract(_make_manifest(), traces, provider, "mock-strong")

    @pytest.mark.asyncio
    async def test_extract_empty_response(self) -> None:
        provider = FakeExtractionProvider("")
        ext = ReflectiveExtractor()
        traces = [_make_trace("t1", passed=True)]

        with pytest.raises(ExtractionError, match="empty response"):
            await ext.extract(_make_manifest(), traces, provider, "mock-strong")

    @pytest.mark.asyncio
    async def test_stratified_sampling(self) -> None:
        provider = FakeExtractionProvider(_VALID_SKILL_MD)
        ext = ReflectiveExtractor()
        traces = [_make_trace(f"t{i}", passed=i < 20) for i in range(30)]

        skill = await ext.extract(
            _make_manifest(), traces, provider, "mock-strong", max_traces_per_pass=10
        )
        assert skill.frontmatter.name == "test-skill"

    def test_stratified_sample_method(self) -> None:
        ext = ReflectiveExtractor()
        traces = [_make_trace(f"t{i}", passed=i < 16) for i in range(20)]
        sampled = ext._stratified_sample(traces, 10)
        assert len(sampled) == 10
        failed = [t for t in sampled if not (t.score and t.score.passed)]
        assert len(failed) >= 2

    def test_stratified_sample_all_when_small(self) -> None:
        ext = ReflectiveExtractor()
        traces = [_make_trace(f"t{i}", passed=True) for i in range(5)]
        sampled = ext._stratified_sample(traces, 20)
        assert len(sampled) == 5
