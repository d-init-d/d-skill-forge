# ruff: noqa: D102, PLR2004
"""Tests for the OpenAI provider."""

from __future__ import annotations

import httpx
import pytest
import respx

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.base import CompletionRequest, CompletionResponse
from skillforge.providers.openai import OpenAIProvider
from skillforge.providers.openai_prices import OPENAI_PRICES


@pytest.fixture
def provider() -> OpenAIProvider:
    """Create an OpenAIProvider instance."""
    return OpenAIProvider()


def _make_request(model: str = "gpt-4o") -> CompletionRequest:
    """Helper to build a simple CompletionRequest."""
    return CompletionRequest(
        model=model,
        messages=[
            Message(role="user", content=[ContentBlock(type="text", text="Hello")]),
        ],
        system="You are helpful.",
    )


class TestOpenAIProviderSupports:
    """Tests for OpenAIProvider.supports()."""

    def test_supports_gpt5(self, provider: OpenAIProvider) -> None:
        assert provider.supports("gpt-5") is True

    def test_supports_gpt5_mini(self, provider: OpenAIProvider) -> None:
        assert provider.supports("gpt-5-mini") is True

    def test_supports_gpt4o(self, provider: OpenAIProvider) -> None:
        assert provider.supports("gpt-4o") is True

    def test_supports_gpt4o_mini(self, provider: OpenAIProvider) -> None:
        assert provider.supports("gpt-4o-mini") is True

    def test_rejects_unknown(self, provider: OpenAIProvider) -> None:
        assert provider.supports("claude-opus-4") is False


class TestOpenAIProviderCost:
    """Tests for OpenAIProvider.estimate_cost()."""

    def test_cost_calculation(self, provider: OpenAIProvider) -> None:
        resp = CompletionResponse(
            content=[ContentBlock(type="text", text="hi")],
            model="gpt-4o",
            usage={"input_tokens": 1000, "output_tokens": 500},
        )
        pricing = OPENAI_PRICES["gpt-4o"]
        expected = 1000 * pricing.input_per_token + 500 * pricing.output_per_token
        assert provider.estimate_cost(resp) == pytest.approx(expected)

    def test_cost_unknown_model(self, provider: OpenAIProvider) -> None:
        resp = CompletionResponse(
            content=[ContentBlock(type="text", text="hi")],
            model="unknown-model",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
        assert provider.estimate_cost(resp) == 0.0


class TestOpenAIProviderComplete:
    """Tests for OpenAIProvider.complete()."""

    @pytest.mark.asyncio
    async def test_raises_auth_error_without_key(
        self, provider: OpenAIProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(AuthError):
            await provider.complete(_make_request())

    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_completion(
        self, provider: OpenAIProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

        mock_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello there!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 8, "total_tokens": 28},
        }

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        resp = await provider.complete(_make_request())
        assert resp.model == "gpt-4o"
        assert len(resp.content) == 1
        assert resp.content[0].type == "text"
        assert resp.content[0].text == "Hello there!"
        assert resp.usage.input_tokens == 20
        assert resp.usage.output_tokens == 8

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error_raises_provider_error(
        self, provider: OpenAIProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                500,
                json={"error": {"message": "Internal error", "type": "server_error"}},
            )
        )

        with pytest.raises(ProviderError):
            await provider.complete(_make_request())

    @pytest.mark.asyncio
    @respx.mock
    async def test_auth_error_from_api(
        self, provider: OpenAIProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "invalid-key")

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"message": "Invalid API key", "type": "invalid_api_key"}},
            )
        )

        with pytest.raises(AuthError):
            await provider.complete(_make_request())
