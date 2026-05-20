"""Unit tests for skillforge.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from skillforge.config import Config, ProviderConfig, load_config
from skillforge.errors import AuthError, ConfigError

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadConfig:
    """Tests for load_config."""

    def test_load_valid_toml(self) -> None:
        """Loading a valid TOML config succeeds."""
        config = load_config(FIXTURES / "skillforge_minimal.toml")
        assert config.default_provider == "mock"
        assert config.concurrency == 4  # noqa: PLR2004
        assert "anthropic" in config.providers
        assert config.providers["anthropic"].api_key_env == "ANTHROPIC_API_KEY"

    def test_missing_file_raises_config_error(self) -> None:
        """A missing config file raises ConfigError."""
        with pytest.raises(ConfigError, match="not found"):
            load_config(Path("/nonexistent/skillforge.toml"))

    def test_invalid_toml_raises_config_error(self, tmp_path: Path) -> None:
        """Invalid TOML syntax raises ConfigError."""
        bad_file = tmp_path / "bad.toml"
        bad_file.write_text("[[invalid toml", encoding="utf-8")
        with pytest.raises(ConfigError, match="Invalid TOML"):
            load_config(bad_file)

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Loading a valid YAML config succeeds."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(
            "default_provider: mock\nconcurrency: 2\n",
            encoding="utf-8",
        )
        config = load_config(yaml_file)
        assert config.default_provider == "mock"
        assert config.concurrency == 2  # noqa: PLR2004

    def test_unsupported_format_raises_config_error(self, tmp_path: Path) -> None:
        """An unsupported file extension raises ConfigError."""
        bad_file = tmp_path / "config.ini"
        bad_file.write_text("[section]\nkey=val", encoding="utf-8")
        with pytest.raises(ConfigError, match="Unsupported config format"):
            load_config(bad_file)


class TestProviderConfig:
    """Tests for ProviderConfig.resolve_api_key."""

    def test_resolve_api_key_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """resolve_api_key returns the env var value when set."""
        monkeypatch.setenv("TEST_KEY", "sk-test-123")
        pc = ProviderConfig(api_key_env="TEST_KEY")
        assert pc.resolve_api_key() == "sk-test-123"

    def test_resolve_api_key_missing_raises_auth_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """resolve_api_key raises AuthError when env var is not set."""
        monkeypatch.delenv("MISSING_KEY", raising=False)
        pc = ProviderConfig(api_key_env="MISSING_KEY")
        with pytest.raises(AuthError, match="MISSING_KEY"):
            pc.resolve_api_key()

    def test_resolve_api_key_no_env_configured(self) -> None:
        """resolve_api_key raises AuthError when no api_key_env is set."""
        pc = ProviderConfig()
        with pytest.raises(AuthError, match="No api_key_env"):
            pc.resolve_api_key()


class TestConfigDefaults:
    """Tests for Config default values."""

    def test_defaults(self) -> None:
        """Config has sensible defaults."""
        config = Config()
        assert config.default_provider == "mock"
        assert config.default_model == "mock-strong"
        assert config.concurrency == 8  # noqa: PLR2004
        assert config.providers == {}
        assert config.extractor.max_traces_per_pass == 20  # noqa: PLR2004
