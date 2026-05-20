"""Mock provider for deterministic testing without network calls."""

from __future__ import annotations

import hashlib
from typing import ClassVar

from skillforge.models.trace import ContentBlock, TokenUsage
from skillforge.providers import register
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider

# Deterministic answers for mock-strong keyed by task prompt substring.
_STRONG_ANSWERS: dict[str, str] = {
    "What is 2 + 2?": "4",
    "recursion": (
        "Recursion is a technique where a function calls itself to solve smaller subproblems."
    ),
    "valid email": "test.user+tag@example-domain.com",
    "returns True": "def check():\n    return True",
    "haiku": "Code flows like water\nFunctions call themselves again\nStack overflows deep",
}

# Weak answers that are plausible but wrong.
_WEAK_ANSWERS: dict[str, str] = {
    "What is 2 + 2?": "5",
    "recursion": "Recursion is when a loop repeats many times until a condition is met.",
    "valid email": "not-an-email",
    "returns True": "def check():\n    return False",
    "haiku": "I like programming very much today yes",
}

_THINKING_TEXT = (
    "Step 1: Analyze the question.\nStep 2: Consider the context.\nStep 3: Formulate answer."
)


def _find_answer(prompt: str, answers: dict[str, str], fallback: str) -> str:
    """Find the best matching answer for a prompt."""
    for key, value in answers.items():
        if key.lower() in prompt.lower():
            return value
    return fallback


def _deterministic_seed(model: str, prompt: str) -> int:
    """Create a deterministic integer seed from model + prompt."""
    h = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()
    return int(h[:8], 16)


@register("mock")
class MockProvider(Provider):
    """Deterministic mock provider for testing without API calls."""

    name: ClassVar[str] = "mock"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Return deterministic responses based on model and last user message.

        Args:
            request: The completion request.

        Returns:
            A deterministic completion response.
        """
        last_user_msg = ""
        for msg in reversed(request.messages):
            if msg.role == "user":
                for block in msg.content:
                    if block.type == "text" and block.text:
                        last_user_msg = block.text
                        break
                break

        seed = _deterministic_seed(request.model, last_user_msg)
        is_strong = "strong" in request.model

        if is_strong:
            answer = _find_answer(last_user_msg, _STRONG_ANSWERS, f"Answer({seed})")
            content = [
                ContentBlock(type="thinking", text=_THINKING_TEXT),
                ContentBlock(type="text", text=answer),
            ]
        else:
            answer = _find_answer(last_user_msg, _WEAK_ANSWERS, f"Unsure({seed})")
            content = [
                ContentBlock(type="text", text=answer),
            ]

        usage = TokenUsage(
            input_tokens=seed % 100 + 50,
            output_tokens=len(answer) + 10,
            thinking_tokens=30 if is_strong else 0,
        )

        return CompletionResponse(
            content=content,
            model=request.model,
            usage=usage,
            stop_reason="end_turn",
        )

    def supports(self, model: str) -> bool:
        """Check if model starts with 'mock-'.

        Args:
            model: Model identifier.

        Returns:
            True if model starts with 'mock-'.
        """
        return model.startswith("mock-")

    def estimate_cost(self, response: CompletionResponse) -> float:
        """Return zero cost for mock provider.

        Args:
            response: The completion response.

        Returns:
            Always 0.0.
        """
        return 0.0
