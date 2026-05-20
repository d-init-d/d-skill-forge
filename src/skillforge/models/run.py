"""RunManifest model tracking execution metadata."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - required at runtime by Pydantic
from pathlib import Path  # noqa: TC003 - required at runtime by Pydantic

from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    """Result of a single task execution within a run.

    Attributes:
        task_id: The task identifier.
        trace_path: Path to the trace JSONL file.
        passed: Whether the task passed evaluation.
        score: Numeric score (0.0 to 1.0).
    """

    task_id: str
    trace_path: Path
    passed: bool
    score: float


class RunManifest(BaseModel):
    """Manifest tracking metadata for a complete corpus run.

    Attributes:
        run_id: Unique run identifier (ULID).
        started_at: When the run started.
        finished_at: When the run completed (None if still running).
        provider: Provider name used for the run.
        model: Model identifier used.
        corpus_path: Path to the corpus file.
        config_path: Path to the config file.
        skill_loaded: Path to the skill file if one was loaded.
        task_results: Results for each task in the run.
        total_cost_usd: Cumulative cost of the run.
        total_latency_ms: Cumulative latency of the run.
    """

    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    provider: str
    model: str
    corpus_path: Path
    config_path: Path
    skill_loaded: Path | None = None
    task_results: list[TaskResult] = Field(default_factory=list[TaskResult])
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
