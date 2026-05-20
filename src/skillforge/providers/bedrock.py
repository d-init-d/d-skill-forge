"""AWS Bedrock provider for Anthropic Claude models via AWS."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, ClassVar, Protocol

from skillforge.errors import AuthError, ProviderError
from skillforge.models.trace import ContentBlock, TokenUsage
from skillforge.providers import register
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider

if TYPE_CHECKING:
    from typing import Any


class _BedrockClient(Protocol):
    """Protocol for the subset of boto3 bedrock-runtime client we use."""

    def invoke_model(
        self, *, modelId: str, body: str, contentType: str, accept: str
    ) -> dict[str, Any]: ...


@register("bedrock")
class BedrockProvider(Provider):
    """Provider for Anthropic Claude models via AWS Bedrock.

    Requires boto3 (optional dependency: `pip install d-skill-forge[bedrock]`).
    Authentication uses the standard AWS credential chain.
    """

    name: ClassVar[str] = "bedrock"

    def __init__(self) -> None:
        """Initialize the Bedrock provider with lazy boto3 import."""
        self._client: _BedrockClient | None = None

    def _get_client(self) -> _BedrockClient:
        """Lazily initialize the boto3 bedrock-runtime client.

        Returns:
            A boto3 bedrock-runtime client.

        Raises:
            ProviderError: If boto3 is not installed.
            AuthError: If AWS credentials are not configured.
        """
        if self._client is not None:
            return self._client

        try:
            import boto3  # noqa: PLC0415
            from botocore.exceptions import NoCredentialsError  # noqa: PLC0415
        except ImportError as e:
            msg = (
                "boto3 is required for the Bedrock provider. "
                "Install with: pip install d-skill-forge[bedrock]"
            )
            raise ProviderError(msg) from e

        try:
            self._client = boto3.client("bedrock-runtime")
        except NoCredentialsError as e:
            msg = (
                "AWS credentials not configured. "
                "Set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or configure ~/.aws/credentials."
            )
            raise AuthError(msg) from e

        return self._client

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Send a completion request to AWS Bedrock.

        Args:
            request: The completion request.

        Returns:
            A completion response.

        Raises:
            AuthError: If AWS credentials are missing.
            ProviderError: If the Bedrock API call fails.
        """
        client = self._get_client()

        messages = []
        for msg in request.messages:
            content_parts = []
            for block in msg.content:
                if block.type == "text" and block.text:
                    content_parts.append({"type": "text", "text": block.text})
            if content_parts:
                messages.append({"role": msg.role, "content": content_parts})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.system:
            body["system"] = request.system

        try:
            response = client.invoke_model(
                modelId=request.model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
        except Exception as e:
            error_name = type(e).__name__
            if "Credential" in error_name or "Auth" in error_name:
                msg = f"AWS authentication failed: {e}"
                raise AuthError(msg) from e
            msg = f"Bedrock API error: {e}"
            raise ProviderError(msg) from e

        result = json.loads(response["body"].read())

        content_blocks: list[ContentBlock] = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                content_blocks.append(ContentBlock(type="text", text=block["text"]))

        usage_data = result.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
        )

        return CompletionResponse(
            content=content_blocks,
            model=request.model,
            usage=usage,
            stop_reason=result.get("stop_reason", "end_turn"),
        )

    def supports(self, model: str) -> bool:
        """Check if model is a Bedrock Anthropic model.

        Args:
            model: Model identifier.

        Returns:
            True if model contains 'anthropic' or 'claude'.
        """
        return "anthropic" in model.lower() or "claude" in model.lower()

    def estimate_cost(self, response: CompletionResponse) -> float:
        """Estimate cost for Bedrock usage (approximate).

        Args:
            response: The completion response.

        Returns:
            Estimated cost in USD.
        """
        # Bedrock pricing varies by model and region; use approximate Claude pricing
        input_cost = response.usage.input_tokens * 0.003 / 1000
        output_cost = response.usage.output_tokens * 0.015 / 1000
        return input_cost + output_cost
