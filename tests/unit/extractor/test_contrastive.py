# ruff: noqa: D101, D102
"""Tests for ContrastiveExtractor."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.errors import ExtractionError
from skillforge.extractor._prompts import CONTRASTIVE_EXTRACTION_MARKER
from skillforge.extractor.contrastive import ContrastiveExtractor
from skillforge.models.run import RunManifest
from skillforge.models.trace import ContentBlock, Message, Score, Trace
from skillforge.providers.mock import MockProvider


def _make_manifest(run_id: str = "r1", model: str = "mock-strong") -> RunManifest:
    return RunManifest(
        run_id=run_id,
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        provider="mock",
        model=model,
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
    )


def _make_trace(task_id: str, model: str, passed: bool) -> Trace:
    return Trace(
        run_id="r1",
        task_id=task_id,
        provider="mock",
        model=model,
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        finished_at=datetime(2024, 1, 1, tzinfo=UTC),
        latency_ms=10,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="q")])],
        final_output=f"output-{task_id}-{model}",
        score=Score(passed=passed, score=1.0 if passed else 0.0, evaluator="test"),
    )


class TestContrastiveExtractorHappyPath:
    @pytest.mark.asyncio
    async def test_three_pairs_produces_valid_skill(self) -> None:
        provider = MockProvider()
        ext = ContrastiveExtractor()
        strong_traces = [_make_trace(f"t{i}", "mock-strong", passed=True) for i in range(3)]
        weak_traces = [_make_trace(f"t{i}", "mock-weak", passed=False) for i in range(3)]

        skill = await ext.extract(
            _make_manifest("r1", "mock-strong"),
            strong_traces,
            provider,
            "mock-strong",
            weak_manifest=_make_manifest("r2", "mock-weak"),
            weak_traces=weak_traces,
        )
        assert skill.frontmatter.name.startswith("mock-extracted-")
        assert "## When to use" in skill.body


class TestBuildPairs:
    def test_partial_overlap(self) -> None:
        ext = ContrastiveExtractor()
        strong = [_make_trace("t1", "mock-strong", True), _make_trace("t2", "mock-strong", True)]
        weak = [_make_trace("t2", "mock-weak", False), _make_trace("t3", "mock-weak", False)]

        pairs = ext._build_pairs(strong, weak)
        assert len(pairs) == 1
        assert pairs[0][0].task_id == "t2"
        assert pairs[0][1].task_id == "t2"

    def test_no_overlap_returns_empty(self) -> None:
        ext = ContrastiveExtractor()
        strong = [_make_trace("t1", "mock-strong", True)]
        weak = [_make_trace("t99", "mock-weak", False)]

        pairs = ext._build_pairs(strong, weak)
        assert pairs == []


class TestContrastiveExtractorErrors:
    @pytest.mark.asyncio
    async def test_missing_weak_traces_raises(self) -> None:
        provider = MockProvider()
        ext = ContrastiveExtractor()
        strong_traces = [_make_trace("t1", "mock-strong", True)]

        with pytest.raises(ExtractionError, match="requires --weak-run"):
            await ext.extract(
                _make_manifest(),
                strong_traces,
                provider,
                "mock-strong",
            )

    @pytest.mark.asyncio
    async def test_no_matching_pairs_raises(self) -> None:
        provider = MockProvider()
        ext = ContrastiveExtractor()
        strong_traces = [_make_trace("t1", "mock-strong", True)]
        weak_traces = [_make_trace("t99", "mock-weak", False)]

        with pytest.raises(ExtractionError, match="No matching task pairs"):
            await ext.extract(
                _make_manifest("r1", "mock-strong"),
                strong_traces,
                provider,
                "mock-strong",
                weak_manifest=_make_manifest("r2", "mock-weak"),
                weak_traces=weak_traces,
            )


class TestContrastivePromptMarker:
    @pytest.mark.asyncio
    async def test_prompt_contains_marker(self) -> None:
        """Verify the extraction prompt includes the contrastive marker."""
        # The MockProvider checks for CONTRASTIVE_EXTRACTION_MARKER and returns
        # a valid skill. If the marker weren't in the prompt, MockProvider would
        # return a generic answer that wouldn't parse as a skill.
        provider = MockProvider()
        ext = ContrastiveExtractor()
        strong_traces = [_make_trace("t1", "mock-strong", True)]
        weak_traces = [_make_trace("t1", "mock-weak", False)]

        skill = await ext.extract(
            _make_manifest("r1", "mock-strong"),
            strong_traces,
            provider,
            "mock-strong",
            weak_manifest=_make_manifest("r2", "mock-weak"),
            weak_traces=weak_traces,
        )
        # If we got here without ExtractionError, the marker was present
        assert skill.frontmatter.name is not None
        # Also verify the marker constant itself
        assert "CONTRASTIVE" in CONTRASTIVE_EXTRACTION_MARKER
