"""Property-based tests for skillforge data models using Hypothesis."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.skill import ExtractionStats, Skill, SkillFrontmatter
from skillforge.models.task import ExpectedOutcome, Task, TaskCorpus
from skillforge.models.trace import ContentBlock, Message, Score, TokenUsage, Trace

# --- Strategies ---

_kebab_name = st.from_regex(r"^[a-z0-9][a-z0-9-]{1,20}$", fullmatch=True)
_nonempty_text = st.text(min_size=1, max_size=100).filter(lambda s: s.strip())
_dt = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 1, 1),
    timezones=st.just(UTC),
)

_expected_outcome = st.builds(
    ExpectedOutcome,
    kind=st.sampled_from(["exact", "regex", "contains", "executes_ok"]),
    value=st.text(min_size=1, max_size=50),
)

_task = st.builds(
    Task,
    id=_nonempty_text,
    prompt=_nonempty_text,
    context=st.one_of(st.none(), _nonempty_text),
    inputs=st.dictionaries(st.text(min_size=1, max_size=10), st.text(max_size=50), max_size=3),
    expected=_expected_outcome,
    weight=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    tags=st.lists(st.text(min_size=1, max_size=20), max_size=5),
)

_token_usage = st.builds(
    TokenUsage,
    input_tokens=st.integers(min_value=0, max_value=1_000_000),
    output_tokens=st.integers(min_value=0, max_value=1_000_000),
    thinking_tokens=st.integers(min_value=0, max_value=1_000_000),
)

_content_block = st.builds(
    ContentBlock,
    type=st.sampled_from(["text", "thinking"]),
    text=st.text(min_size=1, max_size=200),
)

_message = st.builds(
    Message,
    role=st.sampled_from(["user", "assistant", "system"]),
    content=st.lists(_content_block, min_size=1, max_size=3),
)

_score = st.builds(
    Score,
    passed=st.booleans(),
    score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    rationale=st.one_of(st.none(), _nonempty_text),
    evaluator=st.text(min_size=1, max_size=30),
)

_trace = st.builds(
    Trace,
    run_id=_nonempty_text,
    task_id=_nonempty_text,
    provider=st.sampled_from(["mock", "anthropic", "openai"]),
    model=st.text(min_size=1, max_size=30),
    started_at=_dt,
    finished_at=_dt,
    latency_ms=st.integers(min_value=0, max_value=60_000),
    cost_usd=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False)),
    messages=st.lists(_message, min_size=1, max_size=5),
    final_output=st.text(min_size=1, max_size=500),
    usage=_token_usage,
    score=st.one_of(st.none(), _score),
    error=st.one_of(st.none(), st.text(max_size=100)),
)

_extraction_stats = st.builds(
    ExtractionStats,
    total_traces=st.integers(min_value=1, max_value=1000),
    passed_traces=st.integers(min_value=0, max_value=1000),
    failed_traces=st.integers(min_value=0, max_value=1000),
    extractor=st.text(min_size=1, max_size=30),
    extracted_at=_dt,
)

_skill_frontmatter = st.builds(
    SkillFrontmatter,
    name=_kebab_name,
    description=_nonempty_text,
    version=st.just("0.1.0"),
    source_model=st.text(min_size=1, max_size=30),
    extracted_from=_extraction_stats,
    triggers=st.lists(st.text(min_size=1, max_size=20), max_size=5),
    domains=st.lists(st.text(min_size=1, max_size=20), max_size=3),
    license=st.just("Apache-2.0"),
)

_skill = st.builds(
    Skill,
    frontmatter=_skill_frontmatter,
    body=st.text(min_size=1, max_size=500),
)

_task_result = st.builds(
    TaskResult,
    task_id=_nonempty_text,
    trace_path=st.builds(Path, st.just("traces/t1.jsonl")),
    passed=st.booleans(),
    score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)

_run_manifest = st.builds(
    RunManifest,
    run_id=_nonempty_text,
    started_at=_dt,
    finished_at=st.one_of(st.none(), _dt),
    provider=st.sampled_from(["mock", "anthropic", "openai"]),
    model=st.text(min_size=1, max_size=30),
    corpus_path=st.builds(Path, st.just("tasks.yaml")),
    config_path=st.builds(Path, st.just("skillforge.toml")),
    skill_loaded=st.one_of(st.none(), st.builds(Path, st.just("skills/x/SKILL.md"))),
    task_results=st.lists(_task_result, max_size=5),
    total_cost_usd=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False),
    total_latency_ms=st.integers(min_value=0, max_value=600_000),
)


# --- Property tests ---


@given(task=_task)
@settings(max_examples=100)
def test_task_roundtrip(task: Task) -> None:
    """Task model survives JSON round-trip."""
    restored = Task.model_validate(task.model_dump(mode="json"))
    assert restored == task


@given(trace=_trace)
@settings(max_examples=100)
def test_trace_roundtrip(trace: Trace) -> None:
    """Trace model survives JSON round-trip."""
    restored = Trace.model_validate(trace.model_dump(mode="json"))
    assert restored == trace


@given(skill=_skill)
@settings(max_examples=100)
def test_skill_roundtrip(skill: Skill) -> None:
    """Skill model survives JSON round-trip."""
    restored = Skill.model_validate(skill.model_dump(mode="json"))
    assert restored == skill


@given(manifest=_run_manifest)
@settings(max_examples=100)
def test_run_manifest_roundtrip(manifest: RunManifest) -> None:
    """RunManifest model survives JSON round-trip."""
    restored = RunManifest.model_validate(manifest.model_dump(mode="json"))
    assert restored == manifest


@given(
    corpus=st.builds(
        TaskCorpus,
        name=_nonempty_text,
        description=_nonempty_text,
        domain=_nonempty_text,
        tasks=st.lists(_task, min_size=1, max_size=5),
    )
)
@settings(max_examples=100)
def test_task_corpus_roundtrip(corpus: TaskCorpus) -> None:
    """TaskCorpus model survives JSON round-trip."""
    restored = TaskCorpus.model_validate(corpus.model_dump(mode="json"))
    assert restored == corpus
