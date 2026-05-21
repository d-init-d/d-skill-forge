"""OpenAI-compatible provider for any endpoint implementing /v1/chat/completions."""

from __future__ import annotations

from typing import Any, ClassVar

import httpx

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, TokenUsage
from skillforge.providers import register
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider


def _build_messages(request: CompletionRequest) -> list[dict[str, str]]:
    """Convert internal Message models to OpenAI chat format."""
    result: list[dict[str, str]] = []
    if request.system:
        result.append({"role": "system", "content": request.system})
    for msg in request.messages:
        text_parts = [b.text for b in msg.content if b.type == "text" and b.text]
        content = "\n".join(text_parts) if text_parts else ""
        result.append({"role": msg.role, "content": content})
    return result


@register("openai-compatible")
class OpenAICompatibleProvider(Provider):
    """Generic provider for any OpenAI-compatible API endpoint.

    Args:
        base_url: The API base URL (e.g. https://api.groq.com/openai/v1).
        api_key: API key for authentication.
        provider_name: Display name for this provider instance.
    """

    name: ClassVar[str] = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        provider_name: str = "openai-compatible",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._provider_name = provider_name

    @property
    def display_name(self) -> str:
        """Human-readable provider name."""
        return self._provider_name

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request to the OpenAI-compatible endpoint.

        Args:
            request: The completion request payload.

        Returns:
            The mapped completion response.

        Raises:
            AuthError: If authentication fails.
            ProviderError: If the API call fails.
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {
            "model": request.model,
            "messages": _build_messages(request),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        url = f"{self._base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                msg = f"HTTP error calling {self._provider_name}: {exc}"
                raise ProviderError(msg) from exc

        if resp.status_code == 401:  # noqa: PLR2004
            msg = f"Authentication failed for {self._provider_name}"
            raise AuthError(msg)
        if resp.status_code >= 400:  # noqa: PLR2004
            msg = f"{self._provider_name} API error {resp.status_code}: {resp.text[:200]}"
            raise ProviderError(msg)

        data = resp.json()
        choice = data["choices"][0]
        text = choice.get("message", {}).get("content", "")
        content = [ContentBlock(type="text", text=text)]

        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
        )

        return CompletionResponse(
            content=content,
            model=data.get("model", request.model),
            usage=usage,
            stop_reason=choice.get("finish_reason"),
        )

    def supports(self, model: str) -> bool:
        """OpenAI-compatible providers support any model string.

        Args:
            model: Model identifier.

        Returns:
            Always True (model validation is server-side).
        """
        return True

    def estimate_cost(self, response: CompletionResponse) -> float:
        """Estimate cost — returns 0.0 as pricing varies by provider.

        Args:
            response: The completion response.

        Returns:
            0.0 (no generic pricing available).
        """
        return 0.0
