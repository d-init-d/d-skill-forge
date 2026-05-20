"""Trace models capturing full model interaction records for evaluation runs."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - required at runtime by Pydantic
from typing import Literal

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """A single content block within a message.

    Represents text, thinking, tool usage, or tool results in a conversation.
    """

    type: Literal["text", "thinking", "tool_use", "tool_result"]
    text: str | None = None
    name: str | None = None  # tool name when type == "tool_use"
    input: dict | None = None  # type: ignore[type-arg]  # raw tool input payload
    output: str | None = None


class Message(BaseModel):
    """A single message in a conversation trace."""

    role: Literal["system", "user", "assistant", "tool"]
    content: list[ContentBlock]


class TokenUsage(BaseModel):
    """Token consumption metrics for a single trace."""

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0


class Score(BaseModel):
    """Evaluation score for a trace output."""

    passed: bool
    score: float  # 0.0 .. 1.0
    rationale: str | None = None
    evaluator: str  # e.g. "exact_match" | "llm_judge:gpt-4o-mini"


class Trace(BaseModel):
    """Complete trace of a single task execution against a model provider."""

    schema_version: Literal[1] = 1
    run_id: str
    task_id: str
    provider: str
    model: str
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    cost_usd: float | None = None
    messages: list[Message]
    final_output: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    score: Score | None = None
    error: str | None = None
