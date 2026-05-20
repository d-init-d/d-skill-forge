# ruff: noqa: D102, PLR2004
"""Tests for provider base class and registry."""

from __future__ import annotations

from typing import ClassVar

import pytest

from skillforge.errors import ProviderError
from skillforge.models.trace import ContentBlock, Message, TokenUsage
from skillforge.providers import (
    PROVIDERS,
    CompletionRequest,
    CompletionResponse,
    Provider,
    get_provider,
    register,
)


class TestCompletionRequest:
    """Tests for CompletionRequest model."""

    def test_defaults(self) -> None:
        msg = Message(role="user", content=[ContentBlock(type="text", text="hi")])
        req = CompletionRequest(model="test-model", messages=[msg])
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.thinking_budget_tokens is None
        assert req.tools == []
        assert req.system is None

    def test_full_construction(self) -> None:
        msg = Message(role="user", content=[ContentBlock(type="text", text="hi")])
        req = CompletionRequest(
            model="claude-opus-4",
            messages=[msg],
            system="You are helpful.",
            temperature=0.3,
            max_tokens=1024,
            thinking_budget_tokens=500,
            tools=[{"name": "search"}],
        )
        assert req.model == "claude-opus-4"
        assert req.system == "You are helpful."
        assert req.thinking_budget_tokens == 500


class TestCompletionResponse:
    """Tests for CompletionResponse model."""

    def test_construction(self) -> None:
        resp = CompletionResponse(
            content=[ContentBlock(type="text", text="hello")],
            model="test",
            usage=TokenUsage(input_tokens=10, output_tokens=5),
            stop_reason="end_turn",
        )
        assert resp.model == "test"
        assert resp.usage.input_tokens == 10
        assert resp.stop_reason == "end_turn"


class TestRegistry:
    """Tests for provider registry."""

    def setup_method(self) -> None:
        """Save registry state."""
        self._original = dict(PROVIDERS)

    def teardown_method(self) -> None:
        """Restore registry state."""
        PROVIDERS.clear()
        PROVIDERS.update(self._original)

    def test_register_and_get(self) -> None:
        @register("test-provider")
        class TestProvider(Provider):
            name: ClassVar[str] = "test-provider"

            async def complete(self, request: CompletionRequest) -> CompletionResponse:
                return CompletionResponse(content=[], model="t", usage=TokenUsage())

            def supports(self, model: str) -> bool:
                return model == "test"

            def estimate_cost(self, response: CompletionResponse) -> float:
                return 0.0

        assert get_provider("test-provider") is TestProvider

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(ProviderError, match="Unknown provider"):
            get_provider("nonexistent-provider-xyz")

    def test_register_overwrites(self) -> None:
        @register("dup")
        class First(Provider):
            name: ClassVar[str] = "dup"

            async def complete(self, request: CompletionRequest) -> CompletionResponse:
                return CompletionResponse(content=[], model="f", usage=TokenUsage())

            def supports(self, model: str) -> bool:
                return False

            def estimate_cost(self, response: CompletionResponse) -> float:
                return 0.0

        @register("dup")
        class Second(Provider):
            name: ClassVar[str] = "dup"

            async def complete(self, request: CompletionRequest) -> CompletionResponse:
                return CompletionResponse(content=[], model="s", usage=TokenUsage())

            def supports(self, model: str) -> bool:
                return True

            def estimate_cost(self, response: CompletionResponse) -> float:
                return 1.0

        assert get_provider("dup") is Second
