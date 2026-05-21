"""Pre-configured provider presets for popular OpenAI-compatible services."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderPreset:
    """A pre-configured provider definition.

    Attributes:
        id: Unique preset identifier used in config/CLI.
        name: Human-readable display name.
        base_url: API base URL.
        api_key_env: Environment variable name for the API key.
        default_model: Recommended default model.
        requires_key: Whether an API key is required (False for local).
    """

    id: str
    name: str
    base_url: str
    api_key_env: str
    default_model: str
    requires_key: bool = True


PRESETS: dict[str, ProviderPreset] = {
    p.id: p
    for p in [
        ProviderPreset(
            id="groq",
            name="Groq",
            base_url="https://api.groq.com/openai/v1",
            api_key_env="GROQ_API_KEY",
            default_model="llama-3.3-70b-versatile",
        ),
        ProviderPreset(
            id="deepseek",
            name="DeepSeek",
            base_url="https://api.deepseek.com/v1",
            api_key_env="DEEPSEEK_API_KEY",
            default_model="deepseek-chat",
        ),
        ProviderPreset(
            id="together",
            name="Together AI",
            base_url="https://api.together.xyz/v1",
            api_key_env="TOGETHER_API_KEY",
            default_model="meta-llama/Llama-3-70b-chat-hf",
        ),
        ProviderPreset(
            id="fireworks",
            name="Fireworks AI",
            base_url="https://api.fireworks.ai/inference/v1",
            api_key_env="FIREWORKS_API_KEY",
            default_model="accounts/fireworks/models/llama-v3p1-70b-instruct",
        ),
        ProviderPreset(
            id="openrouter",
            name="OpenRouter",
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            default_model="anthropic/claude-sonnet-4",
        ),
        ProviderPreset(
            id="xai",
            name="xAI (Grok)",
            base_url="https://api.x.ai/v1",
            api_key_env="XAI_API_KEY",
            default_model="grok-3",
        ),
        ProviderPreset(
            id="ollama",
            name="Ollama (local)",
            base_url="http://localhost:11434/v1",
            api_key_env="",
            default_model="llama3.2",
            requires_key=False,
        ),
        ProviderPreset(
            id="lmstudio",
            name="LM Studio (local)",
            base_url="http://localhost:1234/v1",
            api_key_env="",
            default_model="local-model",
            requires_key=False,
        ),
        ProviderPreset(
            id="nvidia",
            name="NVIDIA",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key_env="NVIDIA_API_KEY",
            default_model="nvidia/llama-3.1-nemotron-70b-instruct",
        ),
        ProviderPreset(
            id="cerebras",
            name="Cerebras",
            base_url="https://api.cerebras.ai/v1",
            api_key_env="CEREBRAS_API_KEY",
            default_model="llama3.3-70b",
        ),
    ]
}


def get_all_provider_ids() -> list[str]:
    """Return all available provider IDs (built-in + presets).

    Returns:
        Sorted list of provider identifiers.
    """
    builtin = ["anthropic", "openai", "bedrock", "gemini", "mock"]
    return sorted(set(builtin + list(PRESETS.keys())))
