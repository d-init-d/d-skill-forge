"""Mock provider for deterministic testing without network calls."""

from __future__ import annotations

import hashlib
import re
from typing import ClassVar

from skillforge.extractor._prompts import (
    CONTRASTIVE_EXTRACTION_MARKER,
    ITERATIVE_EXTRACTION_MARKER,
    REFLECTIVE_EXTRACTION_MARKER,
)
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


def _build_mock_skill_md(prompt_text: str) -> str:
    """Build a deterministic valid SKILL.md from extraction prompt content."""
    # Extract task IDs from the prompt for determinism
    task_ids = re.findall(r"task:\s*([^\s\)]+)", prompt_text)
    seed_input = "|".join(sorted(task_ids)) if task_ids else prompt_text[:200]
    seed = hashlib.sha256(seed_input.encode()).hexdigest()[:12]

    return f"""---
name: mock-extracted-{seed[:8]}
description: Deterministic mock skill produced by MockProvider for testing.
version: "0.1.0"
source_model: mock-strong
extracted_from:
  total_traces: {len(task_ids) or 3}
  passed_traces: {len(task_ids) or 3}
  failed_traces: 0
  extractor: "reflective@0.1"
  extracted_at: "2024-01-01T00:00:00Z"
triggers:
  - mock
  - testing
domains:
  - general
license: Apache-2.0
---

## When to use

Use this skill for tasks similar to those in the source corpus.

## Procedure

1. Read the input carefully.
2. Identify the core problem pattern.
3. Apply the deterministic mock heuristic.
4. Return the answer in the expected format.

## Examples

- Given a math question, compute the answer step by step.
- Given a code question, produce working code.

## Anti-patterns

- Do not guess without analyzing the input.
- Do not skip validation of the output format.
"""


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
        # Check for extraction marker in messages
        full_text = ""
        for msg in request.messages:
            for block in msg.content:
                if block.type == "text" and block.text:
                    full_text += block.text

        if REFLECTIVE_EXTRACTION_MARKER in full_text:
            skill_md = _build_mock_skill_md(full_text)
            return CompletionResponse(
                content=[ContentBlock(type="text", text=skill_md)],
                model=request.model,
                usage=TokenUsage(input_tokens=200, output_tokens=300, thinking_tokens=50),
                stop_reason="end_turn",
            )

        if CONTRASTIVE_EXTRACTION_MARKER in full_text:
            skill_md = _build_mock_skill_md(full_text)
            return CompletionResponse(
                content=[ContentBlock(type="text", text=skill_md)],
                model=request.model,
                usage=TokenUsage(input_tokens=250, output_tokens=350, thinking_tokens=60),
                stop_reason="end_turn",
            )

        if ITERATIVE_EXTRACTION_MARKER in full_text:
            skill_md = _build_mock_skill_md(full_text)
            return CompletionResponse(
                content=[ContentBlock(type="text", text=skill_md)],
                model=request.model,
                usage=TokenUsage(input_tokens=250, output_tokens=350, thinking_tokens=60),
                stop_reason="end_turn",
            )

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
