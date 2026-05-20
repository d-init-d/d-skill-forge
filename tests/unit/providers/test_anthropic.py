# ruff: noqa: D102, PLR2004
"""Tests for the Anthropic provider."""

from __future__ import annotations

import httpx
import pytest
import respx

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.anthropic import AnthropicProvider
from skillforge.providers.anthropic_prices import ANTHROPIC_PRICES
from skillforge.providers.base import CompletionRequest, CompletionResponse


@pytest.fixture
def provider() -> AnthropicProvider:
    """Create an AnthropicProvider instance."""
    return AnthropicProvider()


def _make_request(model: str = "claude-sonnet-4") -> CompletionRequest:
    """Helper to build a simple CompletionRequest."""
    return CompletionRequest(
        model=model,
        messages=[
            Message(role="user", content=[ContentBlock(type="text", text="Hello")]),
        ],
        system="You are helpful.",
    )


class TestAnthropicProviderSupports:
    """Tests for AnthropicProvider.supports()."""

    def test_supports_opus(self, provider: AnthropicProvider) -> None:
        assert provider.supports("claude-opus-4") is True

    def test_supports_sonnet(self, provider: AnthropicProvider) -> None:
        assert provider.supports("claude-sonnet-4") is True

    def test_supports_haiku(self, provider: AnthropicProvider) -> None:
        assert provider.supports("claude-haiku-4") is True

    def test_rejects_unknown(self, provider: AnthropicProvider) -> None:
        assert provider.supports("gpt-4o") is False


class TestAnthropicProviderCost:
    """Tests for AnthropicProvider.estimate_cost()."""

    def test_cost_calculation(self, provider: AnthropicProvider) -> None:
        resp = CompletionResponse(
            content=[ContentBlock(type="text", text="hi")],
            model="claude-sonnet-4",
            usage={"input_tokens": 1000, "output_tokens": 500},
        )
        pricing = ANTHROPIC_PRICES["claude-sonnet-4"]
        expected = 1000 * pricing.input_per_token + 500 * pricing.output_per_token
        assert provider.estimate_cost(resp) == pytest.approx(expected)

    def test_cost_unknown_model(self, provider: AnthropicProvider) -> None:
        resp = CompletionResponse(
            content=[ContentBlock(type="text", text="hi")],
            model="unknown-model",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
        assert provider.estimate_cost(resp) == 0.0


class TestAnthropicProviderComplete:
    """Tests for AnthropicProvider.complete()."""

    @pytest.mark.asyncio
    async def test_raises_auth_error_without_key(
        self, provider: AnthropicProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(AuthError):
            await provider.complete(_make_request())

    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_completion(
        self, provider: AnthropicProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")

        mock_response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "model": "claude-sonnet-4",
            "content": [{"type": "text", "text": "Hello there!"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 25, "output_tokens": 10},
        }

        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        resp = await provider.complete(_make_request())
        assert resp.model == "claude-sonnet-4"
        assert len(resp.content) == 1
        assert resp.content[0].type == "text"
        assert resp.content[0].text == "Hello there!"
        assert resp.usage.input_tokens == 25
        assert resp.usage.output_tokens == 10

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error_raises_provider_error(
        self, provider: AnthropicProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")

        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                500,
                json={
                    "type": "error",
                    "error": {"type": "api_error", "message": "Internal error"},
                },
            )
        )

        with pytest.raises(ProviderError):
            await provider.complete(_make_request())

    @pytest.mark.asyncio
    @respx.mock
    async def test_auth_error_from_api(
        self, provider: AnthropicProvider, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "invalid-key")

        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                401,
                json={
                    "type": "error",
                    "error": {"type": "authentication_error", "message": "Invalid API key"},
                },
            )
        )

        with pytest.raises(AuthError):
            await provider.complete(_make_request())
