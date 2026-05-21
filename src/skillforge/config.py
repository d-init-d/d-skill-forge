"""Configuration loading and validation.

Loads skillforge.toml (or YAML) and resolves provider API keys via
environment variables at access time.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from skillforge.errors import AuthError, ConfigError

_DEFAULT_CONFIG_NAME = "skillforge.toml"


class ProviderConfig(BaseModel):
    """Configuration for a single provider.

    Attributes:
        api_key_env: Name of the environment variable holding the API key.
        default_model: Default model to use for this provider.
        type: Provider type ("openai-compatible" for custom endpoints).
        base_url: Base URL for openai-compatible providers.
    """

    api_key_env: str | None = None
    default_model: str | None = None
    type: str | None = None
    base_url: str | None = None

    def resolve_api_key(self, provider_id: str | None = None) -> str:
        """Resolve the API key using auth.json → env var → config fallback.

        Args:
            provider_id: Provider identifier for auth.json lookup.

        Returns:
            The API key value.

        Raises:
            AuthError: If no key can be resolved.
        """
        # 1. Try auth.json first
        if provider_id:
            from skillforge.auth import AuthStore

            store = AuthStore()
            key = store.get(provider_id)
            if key:
                return key

        # 2. Try environment variable
        if self.api_key_env:
            value = os.environ.get(self.api_key_env)
            if value:
                return value

        # 3. Try preset env var
        if provider_id:
            from skillforge.providers.presets import PRESETS

            preset = PRESETS.get(provider_id)
            if preset and preset.api_key_env:
                value = os.environ.get(preset.api_key_env)
                if value:
                    return value
                if not preset.requires_key:
                    return ""

        msg = f"No API key found for provider '{provider_id or 'unknown'}'"
        raise AuthError(msg)


class ExtractorConfig(BaseModel):
    """Configuration for the extractor.

    Attributes:
        max_traces_per_pass: Maximum traces to include in a single extraction pass.
    """

    max_traces_per_pass: int = 20


class Config(BaseModel):
    """Top-level skillforge configuration.

    Attributes:
        project_dir: Base directory of the project.
        providers: Per-provider configuration.
        extractor: Extractor configuration.
        default_provider: Default provider name.
        default_model: Default model name.
        concurrency: Default concurrency for runs.
    """

    project_dir: Path = Field(default_factory=Path.cwd)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)
    default_provider: str = "mock"
    default_model: str = "mock-strong"
    concurrency: int = 8


def load_config(path: Path | None = None) -> Config:
    """Load configuration from a TOML or YAML file.

    Args:
        path: Path to the config file. If None, searches for skillforge.toml in CWD.

    Returns:
        A validated Config instance.

    Raises:
        ConfigError: If the file is missing, unreadable, or has invalid syntax.
    """
    if path is None:
        path = Path.cwd() / _DEFAULT_CONFIG_NAME

    if not path.exists():
        msg = f"Configuration file not found: {path}"
        raise ConfigError(msg)

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        msg = f"Cannot read configuration file: {path}: {e}"
        raise ConfigError(msg) from e

    data: dict[str, Any]
    if path.suffix == ".toml":
        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            msg = f"Invalid TOML syntax in {path}: {e}"
            raise ConfigError(msg) from e
    elif path.suffix in (".yaml", ".yml"):
        try:
            data = yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            msg = f"Invalid YAML syntax in {path}: {e}"
            raise ConfigError(msg) from e
    else:
        msg = f"Unsupported config format: {path.suffix} (use .toml or .yaml)"
        raise ConfigError(msg)

    # Set project_dir to the config file's parent
    data.setdefault("project_dir", str(path.parent))

    try:
        return Config.model_validate(data)
    except Exception as e:
        msg = f"Invalid configuration in {path}: {e}"
        raise ConfigError(msg) from e
