"""Unit tests for skillforge.models (Task, Trace, Skill, Run)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.skill import EvalReport, ExtractionStats, Skill, SkillFrontmatter
from skillforge.models.task import ExpectedOutcome, Task, TaskCorpus
from skillforge.models.trace import ContentBlock, Message, Score, TokenUsage, Trace


class TestExpectedOutcome:
    """Tests for the ExpectedOutcome model."""

    def test_valid_exact_outcome(self) -> None:
        """An exact outcome with a value is valid."""
        outcome = ExpectedOutcome(kind="exact", value="hello")
        assert outcome.kind == "exact"
        assert outcome.value == "hello"
        assert outcome.judge_rubric is None

    def test_llm_judge_without_rubric_rejected(self) -> None:
        """llm_judge kind requires judge_rubric to be set."""
        with pytest.raises(ValidationError, match="judge_rubric"):
            ExpectedOutcome(kind="llm_judge")

    def test_llm_judge_with_rubric_valid(self) -> None:
        """llm_judge kind with rubric is accepted."""
        outcome = ExpectedOutcome(kind="llm_judge", judge_rubric="Check correctness")
        assert outcome.kind == "llm_judge"
        assert outcome.judge_rubric == "Check correctness"

    def test_executes_ok_no_value_needed(self) -> None:
        """executes_ok kind does not require value or rubric."""
        outcome = ExpectedOutcome(kind="executes_ok")
        assert outcome.kind == "executes_ok"
        assert outcome.value is None


class TestTask:
    """Tests for the Task model."""

    def test_valid_task(self) -> None:
        """A fully specified task is accepted."""
        task = Task(
            id="task-1",
            prompt="Explain recursion",
            expected=ExpectedOutcome(kind="contains", value="base case"),
        )
        assert task.id == "task-1"
        assert task.prompt == "Explain recursion"
        assert task.weight == 1.0
        assert task.tags == []
        assert task.inputs == {}
        assert task.context is None

    def test_missing_prompt_rejected(self) -> None:
        """A task without a prompt field is rejected."""
        with pytest.raises(ValidationError, match="prompt"):
            Task(
                id="task-1",
                expected=ExpectedOutcome(kind="exact", value="x"),
            )  # type: ignore[call-arg]

    def test_empty_id_rejected(self) -> None:
        """A task with an empty id is rejected."""
        with pytest.raises(ValidationError, match="string_too_short"):
            Task(
                id="",
                prompt="Do something",
                expected=ExpectedOutcome(kind="exact", value="y"),
            )

    def test_weight_default_is_one(self) -> None:
        """Weight defaults to 1.0 when not specified."""
        task = Task(
            id="t",
            prompt="p",
            expected=ExpectedOutcome(kind="executes_ok"),
        )
        assert task.weight == 1.0

    def test_custom_weight(self) -> None:
        """A custom weight value is preserved."""
        task = Task(
            id="t",
            prompt="p",
            expected=ExpectedOutcome(kind="executes_ok"),
            weight=2.5,
        )
        assert task.weight == 2.5  # noqa: PLR2004


class TestTaskCorpus:
    """Tests for the TaskCorpus model."""

    def test_valid_corpus(self) -> None:
        """A corpus with one task is valid."""
        corpus = TaskCorpus(
            name="demo",
            description="A demo corpus",
            domain="testing",
            tasks=[
                Task(
                    id="t1",
                    prompt="Hello",
                    expected=ExpectedOutcome(kind="exact", value="Hi"),
                )
            ],
        )
        assert corpus.version == 1
        assert corpus.name == "demo"
        assert len(corpus.tasks) == 1

    def test_version_defaults_to_one(self) -> None:
        """Version defaults to 1."""
        corpus = TaskCorpus(
            name="c",
            description="d",
            domain="x",
            tasks=[],
        )
        assert corpus.version == 1


class TestContentBlock:
    """Tests for the ContentBlock model."""

    def test_text_block(self) -> None:
        """A text content block is valid with just type and text."""
        block = ContentBlock(type="text", text="Hello world")
        assert block.type == "text"
        assert block.text == "Hello world"
        assert block.name is None
        assert block.input is None
        assert block.output is None

    def test_tool_use_block(self) -> None:
        """A tool_use block carries name and input."""
        block = ContentBlock(
            type="tool_use",
            name="read_file",
            input={"path": "/tmp/test.py"},
        )
        assert block.type == "tool_use"
        assert block.name == "read_file"
        assert block.input == {"path": "/tmp/test.py"}

    def test_tool_result_block(self) -> None:
        """A tool_result block carries output."""
        block = ContentBlock(type="tool_result", output="file contents here")
        assert block.type == "tool_result"
        assert block.output == "file contents here"

    def test_thinking_block(self) -> None:
        """A thinking block carries text."""
        block = ContentBlock(type="thinking", text="Let me think...")
        assert block.type == "thinking"
        assert block.text == "Let me think..."


class TestMessage:
    """Tests for the Message model."""

    def test_valid_message(self) -> None:
        """A message with role and content blocks is valid."""
        msg = Message(
            role="assistant",
            content=[ContentBlock(type="text", text="Hi")],
        )
        assert msg.role == "assistant"
        assert len(msg.content) == 1

    def test_invalid_role_rejected(self) -> None:
        """An invalid role is rejected."""
        with pytest.raises(ValidationError):
            Message(
                role="invalid",  # type: ignore[arg-type]
                content=[ContentBlock(type="text", text="x")],
            )


class TestTokenUsage:
    """Tests for the TokenUsage model."""

    def test_defaults_to_zero(self) -> None:
        """All token counts default to zero."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.thinking_tokens == 0

    def test_custom_values(self) -> None:
        """Custom token values are preserved."""
        usage = TokenUsage(input_tokens=100, output_tokens=50, thinking_tokens=25)
        assert usage.input_tokens == 100  # noqa: PLR2004
        assert usage.output_tokens == 50  # noqa: PLR2004
        assert usage.thinking_tokens == 25  # noqa: PLR2004


class TestScore:
    """Tests for the Score model."""

    def test_valid_score(self) -> None:
        """A fully specified score is valid."""
        score = Score(passed=True, score=0.95, evaluator="exact_match")
        assert score.passed is True
        assert score.score == 0.95  # noqa: PLR2004
        assert score.rationale is None
        assert score.evaluator == "exact_match"

    def test_score_with_rationale(self) -> None:
        """A score with rationale is valid."""
        score = Score(
            passed=False,
            score=0.3,
            rationale="Output did not match expected",
            evaluator="llm_judge:gpt-4o-mini",
        )
        assert score.rationale == "Output did not match expected"


class TestTraceRoundTrip:
    """Tests for the Trace model including JSON round-trip serialization."""

    def _make_trace(self) -> Trace:
        """Build a sample Trace with mixed content blocks."""
        return Trace(
            run_id="run-abc123",
            task_id="task-1",
            provider="anthropic",
            model="claude-opus-4",
            started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            finished_at=datetime(2024, 1, 15, 10, 0, 5, tzinfo=UTC),
            latency_ms=5000,
            cost_usd=0.05,
            messages=[
                Message(
                    role="system",
                    content=[ContentBlock(type="text", text="You are helpful.")],
                ),
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="Explain recursion")],
                ),
                Message(
                    role="assistant",
                    content=[
                        ContentBlock(type="thinking", text="Let me think about this..."),
                        ContentBlock(type="text", text="Recursion is..."),
                        ContentBlock(
                            type="tool_use",
                            name="search",
                            input={"query": "recursion examples"},
                        ),
                    ],
                ),
                Message(
                    role="tool",
                    content=[
                        ContentBlock(type="tool_result", output="Found 3 results"),
                    ],
                ),
            ],
            final_output="Recursion is a technique where a function calls itself.",
            usage=TokenUsage(input_tokens=150, output_tokens=80, thinking_tokens=30),
            score=Score(passed=True, score=1.0, evaluator="exact_match"),
        )

    def test_round_trip_json(self) -> None:
        """Build a Trace, dump to JSON, load back, assert equality."""
        original = self._make_trace()
        json_str = original.model_dump_json()
        restored = Trace.model_validate_json(json_str)
        assert restored == original

    def test_schema_version_defaults_to_one(self) -> None:
        """schema_version defaults to 1."""
        trace = self._make_trace()
        assert trace.schema_version == 1

    def test_schema_version_literal_enforced(self) -> None:
        """Setting schema_version to a value other than 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            Trace(
                schema_version=2,  # type: ignore[arg-type]
                run_id="run-x",
                task_id="task-x",
                provider="mock",
                model="mock-model",
                started_at=datetime(2024, 1, 1, tzinfo=UTC),
                finished_at=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
                latency_ms=1000,
                messages=[
                    Message(role="user", content=[ContentBlock(type="text", text="hi")]),
                ],
                final_output="hello",
            )

    def test_usage_defaults_to_empty(self) -> None:
        """Usage defaults to zero-valued TokenUsage when not specified."""
        trace = Trace(
            run_id="run-x",
            task_id="task-x",
            provider="mock",
            model="mock-model",
            started_at=datetime(2024, 1, 1, tzinfo=UTC),
            finished_at=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
            latency_ms=1000,
            messages=[
                Message(role="user", content=[ContentBlock(type="text", text="hi")]),
            ],
            final_output="hello",
        )
        assert trace.usage.input_tokens == 0
        assert trace.usage.output_tokens == 0
        assert trace.usage.thinking_tokens == 0

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields (cost_usd, score, error) default to None."""
        trace = Trace(
            run_id="run-x",
            task_id="task-x",
            provider="mock",
            model="mock-model",
            started_at=datetime(2024, 1, 1, tzinfo=UTC),
            finished_at=datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC),
            latency_ms=1000,
            messages=[
                Message(role="user", content=[ContentBlock(type="text", text="hi")]),
            ],
            final_output="hello",
        )
        assert trace.cost_usd is None
        assert trace.score is None
        assert trace.error is None


class TestSkillFrontmatter:
    """Tests for the SkillFrontmatter model."""

    def _make_frontmatter(self, **kwargs: object) -> SkillFrontmatter:
        """Build a valid SkillFrontmatter with overrides."""
        defaults: dict[str, object] = {
            "name": "python-debug",
            "description": "Debug Python errors",
            "version": "0.1.0",
            "source_model": "claude-opus-4",
            "extracted_from": ExtractionStats(
                total_traces=10,
                passed_traces=8,
                failed_traces=2,
                extractor="reflective@0.1",
                extracted_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            ),
        }
        defaults.update(kwargs)
        return SkillFrontmatter(**defaults)  # type: ignore[arg-type]

    def test_valid_frontmatter(self) -> None:
        """A fully specified frontmatter is valid."""
        fm = self._make_frontmatter()
        assert fm.name == "python-debug"
        assert fm.license == "Apache-2.0"
        assert fm.eval == []
        assert fm.triggers == []
        assert fm.domains == []

    def test_kebab_case_enforced(self) -> None:
        """Name must be kebab-case."""
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            self._make_frontmatter(name="PythonDebug")

    def test_name_cannot_start_with_hyphen(self) -> None:
        """Name must start with alphanumeric."""
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            self._make_frontmatter(name="-invalid")

    def test_name_min_length(self) -> None:
        """Name must be at least 2 chars (pattern requires 2+ after first)."""
        with pytest.raises(ValidationError, match="string_pattern_mismatch"):
            self._make_frontmatter(name="a")


class TestSkill:
    """Tests for the Skill model."""

    def test_round_trip(self) -> None:
        """A Skill round-trips through JSON serialization."""
        skill = Skill(
            frontmatter=SkillFrontmatter(
                name="python-debug",
                description="Debug Python errors",
                source_model="claude-opus-4",
                extracted_from=ExtractionStats(
                    total_traces=10,
                    passed_traces=8,
                    failed_traces=2,
                    extractor="reflective@0.1",
                    extracted_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
                ),
                eval=[
                    EvalReport(
                        target_model="mock-weak",
                        baseline_score=0.4,
                        with_skill_score=0.8,
                        delta=0.4,
                        tasks_evaluated=5,
                        timestamp=datetime(2024, 1, 16, tzinfo=UTC),
                    )
                ],
            ),
            body="## When to use\nPython debugging\n",
        )
        json_str = skill.model_dump_json()
        restored = Skill.model_validate_json(json_str)
        assert restored == skill

    def test_eval_list_default_empty(self) -> None:
        """Eval list defaults to empty."""
        skill = Skill(
            frontmatter=SkillFrontmatter(
                name="test-skill",
                description="Test",
                source_model="mock",
                extracted_from=ExtractionStats(
                    total_traces=1,
                    passed_traces=1,
                    failed_traces=0,
                    extractor="reflective@0.1",
                    extracted_at=datetime(2024, 1, 1, tzinfo=UTC),
                ),
            ),
            body="body",
        )
        assert skill.frontmatter.eval == []


class TestRunManifest:
    """Tests for the RunManifest model."""

    def test_empty_manifest(self) -> None:
        """A manifest with no task results is valid."""
        manifest = RunManifest(
            run_id="01HQXYZ",
            started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            provider="mock",
            model="mock-strong",
            corpus_path=Path("tasks.yaml"),
            config_path=Path("skillforge.toml"),
        )
        assert manifest.task_results == []
        assert manifest.total_cost_usd == 0.0
        assert manifest.total_latency_ms == 0
        assert manifest.finished_at is None
        assert manifest.skill_loaded is None

    def test_manifest_with_results(self) -> None:
        """A manifest with three task results serializes correctly."""
        manifest = RunManifest(
            run_id="01HQXYZ",
            started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            finished_at=datetime(2024, 1, 15, 10, 5, 0, tzinfo=UTC),
            provider="mock",
            model="mock-strong",
            corpus_path=Path("tasks.yaml"),
            config_path=Path("skillforge.toml"),
            task_results=[
                TaskResult(
                    task_id="t1", trace_path=Path("traces/t1.jsonl"), passed=True, score=1.0
                ),
                TaskResult(
                    task_id="t2", trace_path=Path("traces/t2.jsonl"), passed=False, score=0.3
                ),
                TaskResult(
                    task_id="t3", trace_path=Path("traces/t3.jsonl"), passed=True, score=0.9
                ),
            ],
            total_cost_usd=0.15,
            total_latency_ms=15000,
        )
        assert len(manifest.task_results) == 3  # noqa: PLR2004
        assert manifest.total_cost_usd == 0.15  # noqa: PLR2004

    def test_path_serializes_as_string(self) -> None:
        """Path fields serialize to strings in JSON."""
        manifest = RunManifest(
            run_id="01HQXYZ",
            started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            provider="mock",
            model="mock-strong",
            corpus_path=Path("tasks.yaml"),
            config_path=Path("skillforge.toml"),
        )
        json_str = manifest.model_dump_json()
        assert "tasks.yaml" in json_str
        # Round-trip
        restored = RunManifest.model_validate_json(json_str)
        assert restored == manifest
