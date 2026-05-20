"""Anthropic provider adapter wrapping the official SDK."""

from __future__ import annotations

import os
from typing import Any, ClassVar

import anthropic

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, TokenUsage
from skillforge.providers import register
from skillforge.providers.anthropic_prices import ANTHROPIC_PRICES
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider


def _map_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert our Message models to Anthropic API format."""
    result: list[dict[str, Any]] = []
    for msg in messages:
        role: str = msg["role"]
        content: list[dict[str, Any]] = msg["content"]
        blocks: list[dict[str, Any]] = []
        for block in content:
            if block["type"] == "text":
                blocks.append({"type": "text", "text": block.get("text", "")})
            elif block["type"] == "tool_use":
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": "toolu_" + (block.get("name") or "unknown"),
                        "name": block.get("name", ""),
                        "input": block.get("input") or {},
                    }
                )
            elif block["type"] == "tool_result":
                blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_" + (block.get("name") or "unknown"),
                        "content": block.get("output", ""),
                    }
                )
        result.append({"role": role, "content": blocks})
    return result


def _map_response_blocks(
    content: Any,
) -> list[ContentBlock]:
    """Map Anthropic response content blocks to our ContentBlock model."""
    blocks: list[ContentBlock] = []
    for block in content:
        block_type: str = getattr(block, "type", "text")
        if block_type == "thinking":
            blocks.append(ContentBlock(type="thinking", text=getattr(block, "thinking", "")))
        elif block_type == "tool_use":
            blocks.append(
                ContentBlock(
                    type="tool_use",
                    name=getattr(block, "name", None),
                    input=getattr(block, "input", None),
                )
            )
        else:
            blocks.append(ContentBlock(type="text", text=getattr(block, "text", "")))
    return blocks


@register("anthropic")
class AnthropicProvider(Provider):
    """Provider adapter for Anthropic's Claude models."""

    name: ClassVar[str] = "anthropic"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request to Anthropic.

        Args:
            request: The completion request payload.

        Returns:
            The mapped completion response.

        Raises:
            AuthError: If ANTHROPIC_API_KEY is not set.
            ProviderError: If the API call fails.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            msg = "ANTHROPIC_API_KEY environment variable is not set."
            raise AuthError(msg)

        client = anthropic.AsyncAnthropic(api_key=api_key)

        messages_raw = [m.model_dump() for m in request.messages if m.role != "system"]
        api_messages = _map_messages(messages_raw)

        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": api_messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.system:
            kwargs["system"] = request.system

        try:
            response = await client.messages.create(**kwargs)  # type: ignore[arg-type]  # SDK kwargs
        except anthropic.AuthenticationError as exc:
            msg = f"Anthropic authentication failed: {exc}"
            raise AuthError(msg) from exc
        except anthropic.APIError as exc:
            msg = f"Anthropic API error: {exc}"
            raise ProviderError(msg) from exc

        # SDK response types are dynamic; cast at boundary
        resp_content: list[Any] = response.content  # type: ignore[assignment]  # SDK boundary
        content = _map_response_blocks(resp_content)
        usage = TokenUsage(
            input_tokens=int(response.usage.input_tokens),  # type: ignore[union-attr]  # SDK
            output_tokens=int(response.usage.output_tokens),  # type: ignore[union-attr]  # SDK
        )

        return CompletionResponse(
            content=content,
            model=str(response.model),  # type: ignore[arg-type]  # SDK enum to str
            usage=usage,
            stop_reason=str(response.stop_reason) if response.stop_reason else None,  # type: ignore[arg-type]  # SDK
        )

    def supports(self, model: str) -> bool:
        """Check if model is a known Anthropic model.

        Args:
            model: Model identifier.

        Returns:
            True if model is in the pricing table.
        """
        return model in ANTHROPIC_PRICES

    def estimate_cost(self, response: CompletionResponse) -> float:
        """Estimate cost based on token usage and model pricing.

        Args:
            response: The completion response.

        Returns:
            Estimated cost in USD, or 0.0 if model not in pricing table.
        """
        pricing = ANTHROPIC_PRICES.get(response.model)
        if not pricing:
            return 0.0
        return (
            response.usage.input_tokens * pricing.input_per_token
            + response.usage.output_tokens * pricing.output_per_token
        )
