"""Google Gemini provider via REST API."""

from __future__ import annotations

import os
from typing import ClassVar

import httpx

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, TokenUsage
from skillforge.providers import register
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider

_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


@register("gemini")
class GeminiProvider(Provider):
    """Provider for Google Gemini models via REST API.

    Authentication via GEMINI_API_KEY environment variable.
    Note: Gemini does not support extended thinking tokens in the same way
    as Anthropic. The thinking_tokens field will always be 0.
    """

    name: ClassVar[str] = "gemini"

    def __init__(self) -> None:
        """Initialize the Gemini provider."""
        self._api_key: str | None = None

    def _get_api_key(self) -> str:
        """Get the Gemini API key from environment.

        Returns:
            The API key string.

        Raises:
            AuthError: If GEMINI_API_KEY is not set.
        """
        if self._api_key:
            return self._api_key
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            msg = "GEMINI_API_KEY environment variable is not set."
            raise AuthError(msg)
        self._api_key = key
        return key

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request to Gemini API.

        Args:
            request: The completion request.

        Returns:
            A completion response.

        Raises:
            AuthError: If API key is missing.
            ProviderError: If the Gemini API call fails.
        """
        api_key = self._get_api_key()

        # Build Gemini-format messages
        contents: list[dict[str, object]] = []
        for msg in request.messages:
            parts: list[dict[str, str]] = []
            for block in msg.content:
                if block.type == "text" and block.text:
                    parts.append({"text": block.text})
            if parts:
                role = "user" if msg.role in ("user", "system") else "model"
                contents.append({"role": role, "parts": parts})

        body: dict[str, object] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        if request.system:
            body["systemInstruction"] = {"parts": [{"text": request.system}]}

        url = f"{_GEMINI_API_BASE}/{request.model}:generateContent?key={api_key}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, json=body)
            except httpx.HTTPError as e:
                msg = f"Gemini API request failed: {e}"
                raise ProviderError(msg) from e

        if resp.status_code == 401:  # noqa: PLR2004
            msg = "Gemini API authentication failed. Check your GEMINI_API_KEY."
            raise AuthError(msg)

        if resp.status_code != 200:  # noqa: PLR2004
            msg = f"Gemini API error ({resp.status_code}): {resp.text[:500]}"
            raise ProviderError(msg)

        data = resp.json()

        # Parse response
        content_blocks: list[ContentBlock] = []
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    content_blocks.append(ContentBlock(type="text", text=part["text"]))

        # Parse usage metadata
        usage_meta = data.get("usageMetadata", {})
        usage = TokenUsage(
            input_tokens=usage_meta.get("promptTokenCount", 0),
            output_tokens=usage_meta.get("candidatesTokenCount", 0),
            thinking_tokens=0,
        )

        stop_reason = None
        if candidates:
            stop_reason = candidates[0].get("finishReason", "STOP")

        return CompletionResponse(
            content=content_blocks,
            model=request.model,
            usage=usage,
            stop_reason=stop_reason,
        )

    def supports(self, model: str) -> bool:
        """Check if model is a Gemini model.

        Args:
            model: Model identifier.

        Returns:
            True if model contains 'gemini'.
        """
        return "gemini" in model.lower()

    def estimate_cost(self, response: CompletionResponse) -> float:
        """Estimate cost for Gemini usage.

        Args:
            response: The completion response.

        Returns:
            Estimated cost in USD (approximate Gemini Pro pricing).
        """
        input_cost = response.usage.input_tokens * 0.00025 / 1000
        output_cost = response.usage.output_tokens * 0.0005 / 1000
        return input_cost + output_cost
