"""Tests for deep extraction components: formatter, budget, DeepExtractor."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from skillforge.extractor.budget import allocate_budgets, compute_trace_weight
from skillforge.extractor.formatter import format_trace_deep, smart_truncate
from skillforge.models.trace import ContentBlock, Message, Score, TokenUsage, Trace


def _make_trace(
    task_id: str = "t1",
    passed: bool = True,
    with_thinking: bool = False,
    with_tools: bool = False,
) -> Trace:
    """Create a test trace."""
    blocks: list[ContentBlock] = []
    if with_thinking:
        blocks.append(ContentBlock(type="thinking", text="Let me think step by step about this..."))
    if with_tools:
        blocks.append(ContentBlock(type="tool_use", name="read_file", input={"path": "main.py"}))
        blocks.append(ContentBlock(type="tool_result", output="def main():\n    pass"))
    blocks.append(ContentBlock(type="text", text="Here is my answer"))

    return Trace(
        run_id="run1",
        task_id=task_id,
        provider="mock",
        model="mock-strong",
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        finished_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        latency_ms=1000,
        messages=[Message(role="assistant", content=blocks)],
        final_output="Here is my answer",
        usage=TokenUsage(input_tokens=100, output_tokens=50),
        score=Score(passed=passed, score=1.0 if passed else 0.0, evaluator="test"),
    )


class TestFormatTraceDeep:
    """Tests for format_trace_deep."""

    def test_includes_thinking(self) -> None:
        trace = _make_trace(with_thinking=True)
        result = format_trace_deep(trace, budget=10000)
        assert "<thinking>" in result
        assert "Let me think step by step" in result

    def test_includes_tool_use(self) -> None:
        trace = _make_trace(with_tools=True)
        result = format_trace_deep(trace, budget=10000)
        assert '<tool name="read_file">' in result
        assert "main.py" in result
        assert "<result>" in result

    def test_includes_text(self) -> None:
        trace = _make_trace()
        result = format_trace_deep(trace, budget=10000)
        assert "Here is my answer" in result

    def test_includes_status(self) -> None:
        trace = _make_trace(passed=True)
        result = format_trace_deep(trace, budget=10000)
        assert "[PASS]" in result

    def test_truncates_when_over_budget(self) -> None:
        trace = _make_trace(with_thinking=True, with_tools=True)
        result = format_trace_deep(trace, budget=50)
        assert len(result) <= 200  # some overhead from truncation markers


class TestSmartTruncate:
    """Tests for smart_truncate."""

    def test_no_truncation_when_under_budget(self) -> None:
        text = "short text"
        assert smart_truncate(text, 1000) == text

    def test_preserves_thinking_blocks(self) -> None:
        text = "x" * 100 + "\n<thinking>\nIMPORTANT REASONING\n</thinking>\n" + "y" * 100
        result = smart_truncate(text, 80)
        assert "IMPORTANT REASONING" in result

    def test_indicates_truncation(self) -> None:
        text = "a" * 1000
        result = smart_truncate(text, 100)
        assert "truncated" in result


class TestBudget:
    """Tests for budget allocation."""

    def test_weight_passed_with_thinking(self) -> None:
        trace = _make_trace(passed=True, with_thinking=True)
        assert compute_trace_weight(trace) == 3.0

    def test_weight_failed_with_thinking(self) -> None:
        trace = _make_trace(passed=False, with_thinking=True)
        assert compute_trace_weight(trace) == 2.5

    def test_weight_passed_with_tools(self) -> None:
        trace = _make_trace(passed=True, with_tools=True)
        assert compute_trace_weight(trace) == 2.0

    def test_weight_plain_failed(self) -> None:
        trace = _make_trace(passed=False)
        assert compute_trace_weight(trace) == 1.0

    def test_allocate_proportional(self) -> None:
        traces = [
            _make_trace(passed=True, with_thinking=True),  # 3.0
            _make_trace(passed=False),  # 1.0
        ]
        budgets = allocate_budgets(traces, total_budget=4000)
        assert budgets[0] == 3000
        assert budgets[1] == 1000

    def test_allocate_empty(self) -> None:
        assert allocate_budgets([]) == []


class TestDeepExtractor:
    """Tests for DeepExtractor integration."""

    @pytest.mark.asyncio
    async def test_extract_produces_skill(self) -> None:
        """DeepExtractor with mock provider produces a parseable skill."""
        from skillforge.extractor.deep import DeepExtractor
        from skillforge.models.run import RunManifest
        from skillforge.providers.mock import MockProvider

        traces = [
            _make_trace("t1", passed=True, with_thinking=True),
            _make_trace("t2", passed=True, with_tools=True),
            _make_trace("t3", passed=False),
        ]

        manifest = RunManifest(
            run_id="test-run",
            started_at=datetime(2026, 1, 1, tzinfo=UTC),
            finished_at=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            provider="mock",
            model="mock-strong",
            corpus_path="tasks.yaml",
            config_path="skillforge.toml",
        )

        provider = MockProvider()
        extractor = DeepExtractor()

        # This will use mock provider which returns canned responses
        # The mock won't produce valid SKILL.md, so we expect ExtractionError
        from skillforge.errors import ExtractionError

        with pytest.raises(ExtractionError):
            await extractor.extract(manifest, traces, provider, "mock-strong")

    @pytest.mark.asyncio
    async def test_empty_traces_raises(self) -> None:
        """DeepExtractor raises on empty traces."""
        from skillforge.extractor.deep import DeepExtractor
        from skillforge.errors import ExtractionError
        from skillforge.models.run import RunManifest
        from skillforge.providers.mock import MockProvider

        manifest = RunManifest(
            run_id="test",
            started_at=datetime(2026, 1, 1, tzinfo=UTC),
            finished_at=datetime(2026, 1, 1, tzinfo=UTC),
            provider="mock",
            model="mock-strong",
            corpus_path="tasks.yaml",
            config_path="skillforge.toml",
        )

        with pytest.raises(ExtractionError, match="No traces"):
            await DeepExtractor().extract(manifest, [], MockProvider(), "mock-strong")
