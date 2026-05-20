"""Smoke test: Anthropic provider with a real API call."""

from __future__ import annotations

import pytest

from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.anthropic import AnthropicProvider
from skillforge.providers.base import CompletionRequest

pytestmark = pytest.mark.smoke


async def test_anthropic_single_request() -> None:
    """Send a minimal request to Anthropic and assert no exception."""
    provider = AnthropicProvider()
    request = CompletionRequest(
        model="claude-haiku-4",
        messages=[Message(role="user", content=[ContentBlock(type="text", text="Say hi")])],
        max_tokens=10,
    )
    response = await provider.complete(request)
    assert response.content
