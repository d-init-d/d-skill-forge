"""LLM provider adapters and registry for Anthropic, OpenAI, and mock."""

from __future__ import annotations

from typing import TYPE_CHECKING

from skillforge.errors import ProviderError
from skillforge.providers.base import (
    CompletionRequest,
    CompletionResponse,
    Provider,
)

if TYPE_CHECKING:
    from collections.abc import Callable

PROVIDERS: dict[str, type[Provider]] = {}


def register(name: str) -> Callable[[type[Provider]], type[Provider]]:
    """Register a provider class under the given name.

    Args:
        name: Unique provider name (e.g. "anthropic", "openai", "mock").

    Returns:
        A decorator that registers the provider class.
    """

    def decorator(cls: type[Provider]) -> type[Provider]:
        PROVIDERS[name] = cls
        return cls

    return decorator


def get_provider(name: str) -> type[Provider]:
    """Look up a registered provider class by name.

    Args:
        name: The provider name to look up.

    Returns:
        The provider class registered under that name.

    Raises:
        ProviderError: If no provider is registered with the given name.
    """
    if name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS.keys())) or "(none)"
        msg = f"Unknown provider '{name}'. Available: {available}"
        raise ProviderError(msg)
    return PROVIDERS[name]


__all__ = [
    "PROVIDERS",
    "CompletionRequest",
    "CompletionResponse",
    "Provider",
    "get_provider",
    "register",
]
