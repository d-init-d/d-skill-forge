"""Custom Textual messages for pipeline events."""

from __future__ import annotations

from typing import Any

from textual.message import Message


class PipelineEvent(Message):
    """Base pipeline event message."""

    def __init__(self, event_type: str, data: dict[str, Any]) -> None:
        super().__init__()
        self.event_type = event_type
        self.data = data


class TaskStarted(Message):
    """Emitted when a task begins execution."""

    def __init__(self, task_id: str) -> None:
        super().__init__()
        self.task_id = task_id


class TaskCompleted(Message):
    """Emitted when a task finishes."""

    def __init__(self, task_id: str, passed: bool, score: float, latency_ms: int) -> None:
        super().__init__()
        self.task_id = task_id
        self.passed = passed
        self.score = score
        self.latency_ms = latency_ms


class TaskFailed(Message):
    """Emitted when a task errors."""

    def __init__(self, task_id: str, error: str) -> None:
        super().__init__()
        self.task_id = task_id
        self.error = error


class RunCompleted(Message):
    """Emitted when the full corpus run finishes."""

    def __init__(self, run_id: str, passed: int, total: int, cost: float) -> None:
        super().__init__()
        self.run_id = run_id
        self.passed = passed
        self.total = total
        self.cost = cost


class ExtractionCompleted(Message):
    """Emitted when skill extraction finishes."""

    def __init__(self, skill_path: str) -> None:
        super().__init__()
        self.skill_path = skill_path


class EvalCompleted(Message):
    """Emitted when evaluation finishes."""

    def __init__(self, baseline: float, with_skill: float, delta: float) -> None:
        super().__init__()
        self.baseline = baseline
        self.with_skill = with_skill
        self.delta = delta
