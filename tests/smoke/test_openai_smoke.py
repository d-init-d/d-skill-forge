"""Smoke test: OpenAI provider with a real API call."""

from __future__ import annotations

import pytest

from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.base import CompletionRequest
from skillforge.providers.openai import OpenAIProvider

pytestmark = pytest.mark.smoke


async def test_openai_single_request() -> None:
    """Send a minimal request to OpenAI and assert no exception."""
    provider = OpenAIProvider()
    request = CompletionRequest(
        model="gpt-4o-mini",
        messages=[Message(role="user", content=[ContentBlock(type="text", text="Say hi")])],
        max_tokens=10,
    )
    response = await provider.complete(request)
    assert response.content
