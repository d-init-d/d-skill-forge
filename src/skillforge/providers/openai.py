"""OpenAI provider adapter wrapping the official SDK."""

from __future__ import annotations

import os
from typing import ClassVar

import openai

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, TokenUsage
from skillforge.providers import register
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider
from skillforge.providers.openai_prices import OPENAI_PRICES


def _build_messages(request: CompletionRequest) -> list[dict[str, object]]:
    """Convert our Message models to OpenAI chat format."""
    result: list[dict[str, object]] = []
    if request.system:
        result.append({"role": "system", "content": request.system})
    for msg in request.messages:
        if msg.role == "system":
            continue
        text_parts = [b.text for b in msg.content if b.type == "text" and b.text]
        content = "\n".join(text_parts) if text_parts else ""
        result.append({"role": msg.role, "content": content})
    return result


@register("openai")
class OpenAIProvider(Provider):
    """Provider adapter for OpenAI's chat completion models."""

    name: ClassVar[str] = "openai"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request to OpenAI.

        Args:
            request: The completion request payload.

        Returns:
            The mapped completion response.

        Raises:
            AuthError: If OPENAI_API_KEY is not set.
            ProviderError: If the API call fails.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            msg = "OPENAI_API_KEY environment variable is not set."
            raise AuthError(msg)

        client = openai.AsyncOpenAI(api_key=api_key)
        messages = _build_messages(request)

        try:
            response = await client.chat.completions.create(
                model=request.model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        except openai.AuthenticationError as exc:
            msg = f"OpenAI authentication failed: {exc}"
            raise AuthError(msg) from exc
        except openai.APIError as exc:
            msg = f"OpenAI API error: {exc}"
            raise ProviderError(msg) from exc

        choice = response.choices[0]
        text = choice.message.content or ""
        content = [ContentBlock(type="text", text=text)]

        usage_data = response.usage
        usage = TokenUsage(
            input_tokens=usage_data.prompt_tokens if usage_data else 0,
            output_tokens=usage_data.completion_tokens if usage_data else 0,
        )

        return CompletionResponse(
            content=content,
            model=response.model,
            usage=usage,
            stop_reason=choice.finish_reason,
        )

    def supports(self, model: str) -> bool:
        """Check if model is a known OpenAI model.

        Args:
            model: Model identifier.

        Returns:
            True if model is in the pricing table.
        """
        return model in OPENAI_PRICES

    def estimate_cost(self, response: CompletionResponse) -> float:
        """Estimate cost based on token usage and model pricing.

        Args:
            response: The completion response.

        Returns:
            Estimated cost in USD, or 0.0 if model not in pricing table.
        """
        pricing = OPENAI_PRICES.get(response.model)
        if not pricing:
            return 0.0
        return (
            response.usage.input_tokens * pricing.input_per_token
            + response.usage.output_tokens * pricing.output_per_token
        )
