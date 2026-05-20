"""Pydantic v2 models for task definitions and task corpora.

A TaskCorpus is a collection of Tasks that define evaluation prompts,
expected outcomes, and metadata used to drive model runs and scoring.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ExpectedOutcome(BaseModel):
    """Expected outcome specification for a single task.

    Attributes:
        kind: The evaluation strategy to use.
        value: The expected value (used by exact, regex, contains).
        judge_rubric: Rubric text required when kind is "llm_judge".
    """

    kind: Literal["exact", "regex", "contains", "llm_judge", "executes_ok"]
    value: str | None = None
    judge_rubric: str | None = None

    @model_validator(mode="after")
    def _require_rubric_for_llm_judge(self) -> ExpectedOutcome:
        """Ensure judge_rubric is provided when kind is 'llm_judge'."""
        if self.kind == "llm_judge" and not self.judge_rubric:
            msg = "judge_rubric is required when kind is 'llm_judge'"
            raise ValueError(msg)
        return self


class Task(BaseModel):
    """A single evaluation task within a corpus.

    Attributes:
        id: Unique task identifier (non-empty).
        prompt: The prompt text sent to the model.
        context: Optional additional context for the model.
        inputs: Key-value pairs injected into the prompt template.
        expected: The expected outcome specification.
        weight: Relative weight for scoring (default 1.0).
        tags: Freeform tags for filtering and grouping.
    """

    id: str = Field(min_length=1)
    prompt: str
    context: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)
    expected: ExpectedOutcome
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)


class TaskCorpus(BaseModel):
    """A versioned collection of tasks for evaluation.

    Attributes:
        version: Schema version (always 1 for MVP).
        name: Human-readable corpus name.
        description: Brief description of the corpus purpose.
        domain: The knowledge domain this corpus targets.
        tasks: Ordered list of tasks in the corpus.
    """

    version: Literal[1] = 1
    name: str
    description: str
    domain: str
    tasks: list[Task]
