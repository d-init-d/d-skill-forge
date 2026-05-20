# ruff: noqa: D101, D102, TC001
"""Tests for extractor base class."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.extractor.base import Extractor
from skillforge.models.run import RunManifest
from skillforge.models.skill import ExtractionStats, Skill, SkillFrontmatter
from skillforge.models.trace import Trace
from skillforge.providers.base import Provider
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


class ConcreteExtractor(Extractor):
    async def extract(
        self,
        manifest: RunManifest,
        traces: list[Trace],
        provider: Provider,
        model: str,
    ) -> Skill:
        return Skill(
            frontmatter=SkillFrontmatter(
                name="test-skill",
                description="test",
                source_model=model,
                extracted_from=ExtractionStats(
                    total_traces=len(traces),
                    passed_traces=0,
                    failed_traces=0,
                    extractor="test",
                    extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
                ),
            ),
            body="## When to use\nTest",
        )


class TestExtractorBase:
    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            Extractor()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_implementation(self) -> None:
        ext = ConcreteExtractor()
        skill = await ext.extract(_make_manifest(), [], MockProvider(), "mock-strong")
        assert skill.frontmatter.name == "test-skill"
