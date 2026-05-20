# ruff: noqa: D101, D102, PLR2004
"""Tests for GeminiProvider with respx HTTP mocking."""

from __future__ import annotations

import httpx
import pytest
import respx

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.base import CompletionRequest, CompletionResponse
from skillforge.providers.gemini import _GEMINI_API_BASE, GeminiProvider


def _make_request(model: str = "gemini-pro") -> CompletionRequest:
    return CompletionRequest(
        model=model,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="Hello")])],
    )


class TestGeminiMissingApiKey:
    @pytest.mark.asyncio
    async def test_raises_auth_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        provider = GeminiProvider()
        with pytest.raises(AuthError, match="GEMINI_API_KEY"):
            await provider.complete(_make_request())


class TestGemini401Response:
    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_auth_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
        provider = GeminiProvider()

        respx.post(f"{_GEMINI_API_BASE}/gemini-pro:generateContent").mock(
            return_value=httpx.Response(401, json={"error": {"message": "Invalid key"}})
        )

        with pytest.raises(AuthError, match="authentication failed"):
            await provider.complete(_make_request())


class TestGemini500Response:
    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_provider_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
        provider = GeminiProvider()

        respx.post(f"{_GEMINI_API_BASE}/gemini-pro:generateContent").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        with pytest.raises(ProviderError, match="500"):
            await provider.complete(_make_request())


class TestGeminiSuccessfulResponse:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_completion_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
        provider = GeminiProvider()

        mock_response = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hello there!"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 15,
                "candidatesTokenCount": 8,
            },
        }

        respx.post(f"{_GEMINI_API_BASE}/gemini-pro:generateContent").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        resp = await provider.complete(_make_request())
        assert isinstance(resp, CompletionResponse)
        assert resp.content[0].text == "Hello there!"
        assert resp.model == "gemini-pro"


class TestGeminiUsageMetadata:
    @pytest.mark.asyncio
    @respx.mock
    async def test_usage_extracted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
        provider = GeminiProvider()

        mock_response = {
            "candidates": [
                {
                    "content": {"parts": [{"text": "Hi"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 42,
                "candidatesTokenCount": 7,
            },
        }

        respx.post(f"{_GEMINI_API_BASE}/gemini-pro:generateContent").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        resp = await provider.complete(_make_request())
        assert resp.usage.input_tokens == 42
        assert resp.usage.output_tokens == 7
        assert resp.usage.thinking_tokens == 0


class TestGeminiSupports:
    def test_supports_gemini_pro(self) -> None:
        provider = GeminiProvider()
        assert provider.supports("gemini-pro") is True

    def test_rejects_non_gemini(self) -> None:
        provider = GeminiProvider()
        assert provider.supports("claude-opus-4") is False
