# ruff: noqa: D102
"""Tests for the mock provider."""

from __future__ import annotations

import re

import pytest

from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.base import CompletionRequest, CompletionResponse
from skillforge.providers.mock import MockProvider


@pytest.fixture
def provider() -> MockProvider:
    """Create a MockProvider instance."""
    return MockProvider()


def _make_request(model: str, prompt: str) -> CompletionRequest:
    """Helper to build a CompletionRequest with a single user message."""
    return CompletionRequest(
        model=model,
        messages=[
            Message(role="user", content=[ContentBlock(type="text", text=prompt)]),
        ],
    )


class TestMockProviderSupports:
    """Tests for MockProvider.supports()."""

    def test_supports_mock_strong(self, provider: MockProvider) -> None:
        assert provider.supports("mock-strong") is True

    def test_supports_mock_weak(self, provider: MockProvider) -> None:
        assert provider.supports("mock-weak") is True

    def test_supports_mock_custom(self, provider: MockProvider) -> None:
        assert provider.supports("mock-anything") is True

    def test_rejects_non_mock(self, provider: MockProvider) -> None:
        assert provider.supports("claude-opus-4") is False

    def test_rejects_partial_prefix(self, provider: MockProvider) -> None:
        assert provider.supports("moc-strong") is False


class TestMockProviderCost:
    """Tests for MockProvider.estimate_cost()."""

    def test_always_zero(self, provider: MockProvider) -> None:
        resp = CompletionResponse(
            content=[ContentBlock(type="text", text="hi")],
            model="mock-strong",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
        assert provider.estimate_cost(resp) == 0.0


class TestMockProviderComplete:
    """Tests for MockProvider.complete()."""

    @pytest.mark.asyncio
    async def test_strong_exact_match(self, provider: MockProvider) -> None:
        req = _make_request("mock-strong", "What is 2 + 2?")
        resp = await provider.complete(req)
        text_blocks = [b for b in resp.content if b.type == "text"]
        assert text_blocks[-1].text == "4"

    @pytest.mark.asyncio
    async def test_strong_contains_function(self, provider: MockProvider) -> None:
        req = _make_request("mock-strong", "Explain recursion briefly.")
        resp = await provider.complete(req)
        text_blocks = [b for b in resp.content if b.type == "text"]
        assert "function" in text_blocks[-1].text.lower()

    @pytest.mark.asyncio
    async def test_strong_regex_email(self, provider: MockProvider) -> None:
        req = _make_request("mock-strong", "Generate a valid email address.")
        resp = await provider.complete(req)
        text_blocks = [b for b in resp.content if b.type == "text"]
        pattern = r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$"
        assert re.match(pattern, text_blocks[-1].text)

    @pytest.mark.asyncio
    async def test_strong_executes_ok(self, provider: MockProvider) -> None:
        req = _make_request("mock-strong", "Write a Python function that returns True.")
        resp = await provider.complete(req)
        text_blocks = [b for b in resp.content if b.type == "text"]
        code = text_blocks[-1].text
        local_ns: dict[str, object] = {}
        exec(code, {}, local_ns)
        assert local_ns["check"]() is True  # type: ignore[operator]

    @pytest.mark.asyncio
    async def test_strong_has_thinking(self, provider: MockProvider) -> None:
        req = _make_request("mock-strong", "What is 2 + 2?")
        resp = await provider.complete(req)
        thinking_blocks = [b for b in resp.content if b.type == "thinking"]
        assert len(thinking_blocks) == 1

    @pytest.mark.asyncio
    async def test_weak_exact_fails(self, provider: MockProvider) -> None:
        req = _make_request("mock-weak", "What is 2 + 2?")
        resp = await provider.complete(req)
        text_blocks = [b for b in resp.content if b.type == "text"]
        assert text_blocks[-1].text != "4"

    @pytest.mark.asyncio
    async def test_weak_no_thinking(self, provider: MockProvider) -> None:
        req = _make_request("mock-weak", "What is 2 + 2?")
        resp = await provider.complete(req)
        thinking_blocks = [b for b in resp.content if b.type == "thinking"]
        assert len(thinking_blocks) == 0

    @pytest.mark.asyncio
    async def test_deterministic(self, provider: MockProvider) -> None:
        req = _make_request("mock-strong", "What is 2 + 2?")
        resp1 = await provider.complete(req)
        resp2 = await provider.complete(req)
        assert resp1 == resp2

    @pytest.mark.asyncio
    async def test_different_prompts_different_results(self, provider: MockProvider) -> None:
        req1 = _make_request("mock-strong", "What is 2 + 2?")
        req2 = _make_request("mock-strong", "Explain recursion briefly.")
        resp1 = await provider.complete(req1)
        resp2 = await provider.complete(req2)
        assert resp1 != resp2
