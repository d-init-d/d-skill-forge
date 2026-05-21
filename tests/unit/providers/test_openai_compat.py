"""Tests for the OpenAI-compatible provider."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.base import CompletionRequest
from skillforge.providers.openai_compat import OpenAICompatibleProvider


@pytest.fixture
def provider() -> OpenAICompatibleProvider:
    """Create a test provider instance."""
    return OpenAICompatibleProvider(
        base_url="https://api.test.com/v1",
        api_key="test-key",
        provider_name="TestProvider",
    )


@pytest.fixture
def sample_request() -> CompletionRequest:
    """Create a sample completion request."""
    return CompletionRequest(
        model="test-model",
        messages=[Message(role="user", content=[ContentBlock(type="text", text="hello")])],
        max_tokens=10,
    )


@respx.mock
@pytest.mark.asyncio
async def test_complete_success(provider: OpenAICompatibleProvider, sample_request: CompletionRequest) -> None:
    """Test successful completion."""
    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=Response(200, json={
            "choices": [{"message": {"content": "Hi there!"}, "finish_reason": "stop"}],
            "model": "test-model",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        })
    )

    resp = await provider.complete(sample_request)
    assert resp.content[0].text == "Hi there!"
    assert resp.model == "test-model"
    assert resp.usage.input_tokens == 5
    assert resp.usage.output_tokens == 3


@respx.mock
@pytest.mark.asyncio
async def test_complete_auth_error(provider: OpenAICompatibleProvider, sample_request: CompletionRequest) -> None:
    """Test 401 raises AuthError."""
    from skillforge.errors import AuthError

    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=Response(401, json={"error": "unauthorized"})
    )

    with pytest.raises(AuthError):
        await provider.complete(sample_request)


@respx.mock
@pytest.mark.asyncio
async def test_complete_api_error(provider: OpenAICompatibleProvider, sample_request: CompletionRequest) -> None:
    """Test 500 raises ProviderError."""
    from skillforge.errors import ProviderError

    respx.post("https://api.test.com/v1/chat/completions").mock(
        return_value=Response(500, text="Internal Server Error")
    )

    with pytest.raises(ProviderError):
        await provider.complete(sample_request)


def test_supports_any_model(provider: OpenAICompatibleProvider) -> None:
    """OpenAI-compatible provider supports any model string."""
    assert provider.supports("anything")
    assert provider.supports("llama-3.3-70b")


def test_estimate_cost_zero(provider: OpenAICompatibleProvider) -> None:
    """Cost estimation returns 0 for generic provider."""
    from skillforge.models.trace import TokenUsage
    from skillforge.providers.base import CompletionResponse

    resp = CompletionResponse(
        content=[ContentBlock(type="text", text="hi")],
        model="test",
        usage=TokenUsage(input_tokens=100, output_tokens=50),
    )
    assert provider.estimate_cost(resp) == 0.0
