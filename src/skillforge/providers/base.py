"""Abstract base class and data contracts for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, Field

from skillforge.models.trace import (  # noqa: TC001 - required at runtime by Pydantic
    ContentBlock,
    Message,
    TokenUsage,
)


class CompletionRequest(BaseModel):
    """Request payload sent to an LLM provider.

    Attributes:
        model: Model identifier (e.g. "claude-opus-4").
        messages: Conversation messages.
        system: Optional system prompt.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        thinking_budget_tokens: Optional extended thinking budget.
        tools: Provider-specific tool schemas.
    """

    model: str
    messages: list[Message]
    system: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    thinking_budget_tokens: int | None = None
    tools: list[dict[str, object]] = Field(default_factory=lambda: [])


class CompletionResponse(BaseModel):
    """Response payload returned from an LLM provider.

    Attributes:
        content: List of content blocks in the response.
        model: Model identifier that produced the response.
        usage: Token usage metrics.
        stop_reason: Why generation stopped (e.g. "end_turn").
    """

    content: list[ContentBlock]
    model: str
    usage: TokenUsage
    stop_reason: str | None = None


class Provider(ABC):
    """Abstract base class for LLM provider adapters.

    Subclasses must implement complete(), supports(), and estimate_cost().
    """

    name: ClassVar[str]

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request and return the response.

        Args:
            request: The completion request payload.

        Returns:
            The provider's completion response.

        Raises:
            ProviderError: If the provider call fails.
        """

    @abstractmethod
    def supports(self, model: str) -> bool:
        """Check whether this provider supports the given model.

        Args:
            model: Model identifier to check.

        Returns:
            True if the model is supported.
        """

    @abstractmethod
    def estimate_cost(self, response: CompletionResponse) -> float:
        """Estimate the cost in USD for a completion response.

        Args:
            response: The completion response to price.

        Returns:
            Estimated cost in USD.
        """
