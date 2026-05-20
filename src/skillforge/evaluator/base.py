"""Abstract base class for task evaluators."""

from __future__ import annotations

from abc import ABC, abstractmethod

from skillforge.models.task import Task  # noqa: TC001 - required at runtime
from skillforge.models.trace import Score, Trace  # noqa: TC001 - required at runtime


class Evaluator(ABC):
    """Abstract evaluator that scores a trace against a task's expected outcome."""

    @abstractmethod
    async def score(self, task: Task, trace: Trace) -> Score:
        """Score a trace against the task's expected outcome.

        Args:
            task: The task definition with expected outcome.
            trace: The execution trace to evaluate.

        Returns:
            A Score indicating pass/fail and numeric score.
        """
