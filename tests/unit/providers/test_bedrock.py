# ruff: noqa: D101, D102, PLR2004
"""Tests for BedrockProvider with mocked boto3."""

from __future__ import annotations

import io
import json

import pytest

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, Message
from skillforge.providers.base import CompletionRequest, CompletionResponse
from skillforge.providers.bedrock import BedrockProvider


def _make_request(model: str = "anthropic.claude-3-sonnet") -> CompletionRequest:
    return CompletionRequest(
        model=model,
        messages=[Message(role="user", content=[ContentBlock(type="text", text="Hello")])],
    )


class TestBedrockBoto3NotInstalled:
    def test_raises_provider_error(self, mocker) -> None:
        provider = BedrockProvider()
        provider._client = None
        mocker.patch.dict(
            "sys.modules", {"boto3": None, "botocore": None, "botocore.exceptions": None}
        )
        # Force reimport failure by patching builtins.__import__
        original_import = (
            __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
        )

        def mock_import(name, *args, **kwargs):
            if name in ("boto3", "botocore", "botocore.exceptions"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=mock_import)

        with pytest.raises(ProviderError, match="boto3 is required"):
            provider._get_client()


class TestBedrockNoCredentials:
    def test_raises_auth_error(self, mocker) -> None:
        provider = BedrockProvider()
        provider._client = None

        mock_boto3 = mocker.MagicMock()
        mock_botocore_exc = mocker.MagicMock()

        # Create a real exception class for NoCredentialsError
        class FakeNoCredentialsError(Exception):
            pass

        mock_botocore_exc.NoCredentialsError = FakeNoCredentialsError
        mock_boto3.client.side_effect = FakeNoCredentialsError("No creds")

        mocker.patch.dict(
            "sys.modules",
            {
                "boto3": mock_boto3,
                "botocore": mocker.MagicMock(),
                "botocore.exceptions": mock_botocore_exc,
            },
        )

        with pytest.raises(AuthError, match="AWS credentials"):
            provider._get_client()


class TestBedrockSuccessfulInvoke:
    @pytest.mark.asyncio
    async def test_returns_completion_response(self, mocker) -> None:
        provider = BedrockProvider()

        mock_response_body = {
            "content": [{"type": "text", "text": "Hello there!"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn",
        }
        mock_body = io.BytesIO(json.dumps(mock_response_body).encode())
        mock_body.read = mock_body.read

        mock_client = mocker.MagicMock()
        mock_client.invoke_model.return_value = {"body": mock_body}
        provider._client = mock_client

        resp = await provider.complete(_make_request())
        assert isinstance(resp, CompletionResponse)
        assert resp.content[0].text == "Hello there!"
        assert resp.usage.input_tokens == 10
        assert resp.usage.output_tokens == 5


class TestBedrockSupports:
    def test_supports_anthropic_claude(self) -> None:
        provider = BedrockProvider()
        assert provider.supports("anthropic.claude-3-sonnet") is True

    def test_rejects_gpt4(self) -> None:
        provider = BedrockProvider()
        assert provider.supports("gpt-4") is False
