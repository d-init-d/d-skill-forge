# ruff: noqa: D101, D102, PLR2004, TC003
"""Tests for the corpus runner."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.evaluator.exact_match import ExactMatchEvaluator
from skillforge.models.skill import (
    ExtractionStats,
    Skill,
    SkillFrontmatter,
)
from skillforge.models.task import ExpectedOutcome, Task, TaskCorpus
from skillforge.providers.mock import MockProvider
from skillforge.recorder import Recorder, load_run
from skillforge.runner import run_corpus


def _make_corpus() -> TaskCorpus:
    return TaskCorpus(
        version=1,
        name="test",
        description="test corpus",
        domain="test",
        tasks=[
            Task(
                id="t-exact",
                prompt="What is 2 + 2?",
                expected=ExpectedOutcome(kind="exact", value="4"),
            ),
            Task(
                id="t-contains",
                prompt="Explain recursion briefly.",
                expected=ExpectedOutcome(kind="contains", value="function"),
            ),
        ],
    )


def _make_skill() -> Skill:
    return Skill(
        frontmatter=SkillFrontmatter(
            name="test-skill",
            description="A test skill",
            source_model="mock-strong",
            extracted_from=ExtractionStats(
                total_traces=5,
                passed_traces=4,
                failed_traces=1,
                extractor="reflective@0.1",
                extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
            ),
        ),
        body="## When to use\nAlways.\n\n## Procedure\n1. Do it.\n",
    )


class TestRunCorpus:
    @pytest.mark.asyncio
    async def test_basic_run(self, tmp_path: Path) -> None:
        corpus = _make_corpus()
        provider = MockProvider()
        evaluator = ExactMatchEvaluator()
        run_dir = tmp_path / "run-1"

        async with Recorder.open(run_dir) as recorder:
            manifest = await run_corpus(
                corpus=corpus,
                provider=provider,
                model="mock-strong",
                recorder=recorder,
                evaluator=evaluator,
            )

        assert manifest.run_id
        assert manifest.provider == "mock"
        assert manifest.model == "mock-strong"
        assert len(manifest.task_results) == 2
        assert manifest.finished_at is not None

    @pytest.mark.asyncio
    async def test_run_with_skill(self, tmp_path: Path) -> None:
        corpus = _make_corpus()
        provider = MockProvider()
        evaluator = ExactMatchEvaluator()
        skill = _make_skill()
        run_dir = tmp_path / "run-skill"

        async with Recorder.open(run_dir) as recorder:
            manifest = await run_corpus(
                corpus=corpus,
                provider=provider,
                model="mock-strong",
                skill=skill,
                recorder=recorder,
                evaluator=evaluator,
            )

        assert len(manifest.task_results) == 2

    @pytest.mark.asyncio
    async def test_traces_recorded(self, tmp_path: Path) -> None:
        corpus = _make_corpus()
        provider = MockProvider()
        evaluator = ExactMatchEvaluator()
        run_dir = tmp_path / "run-traces"

        async with Recorder.open(run_dir) as recorder:
            await run_corpus(
                corpus=corpus,
                provider=provider,
                model="mock-strong",
                recorder=recorder,
                evaluator=evaluator,
            )

        _, traces = load_run(run_dir)
        assert len(traces) == 2

    @pytest.mark.asyncio
    async def test_exact_match_passes(self, tmp_path: Path) -> None:
        corpus = TaskCorpus(
            version=1,
            name="exact",
            description="exact test",
            domain="math",
            tasks=[
                Task(
                    id="t-math",
                    prompt="What is 2 + 2?",
                    expected=ExpectedOutcome(kind="exact", value="4"),
                ),
            ],
        )
        provider = MockProvider()
        evaluator = ExactMatchEvaluator()
        run_dir = tmp_path / "run-exact"

        async with Recorder.open(run_dir) as recorder:
            manifest = await run_corpus(
                corpus=corpus,
                provider=provider,
                model="mock-strong",
                recorder=recorder,
                evaluator=evaluator,
            )

        assert manifest.task_results[0].passed is True
        assert manifest.task_results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_concurrency_respected(self, tmp_path: Path) -> None:
        tasks = [
            Task(
                id=f"t-{i}",
                prompt="What is 2 + 2?",
                expected=ExpectedOutcome(kind="exact", value="4"),
            )
            for i in range(10)
        ]
        corpus = TaskCorpus(
            version=1, name="conc", description="concurrency", domain="test", tasks=tasks
        )
        provider = MockProvider()
        evaluator = ExactMatchEvaluator()
        run_dir = tmp_path / "run-conc"

        async with Recorder.open(run_dir) as recorder:
            manifest = await run_corpus(
                corpus=corpus,
                provider=provider,
                model="mock-strong",
                concurrency=2,
                recorder=recorder,
                evaluator=evaluator,
            )

        assert len(manifest.task_results) == 10
