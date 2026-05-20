"""Unit tests for skillforge.errors."""

from __future__ import annotations

from skillforge.errors import (
    AuthError,
    ConfigError,
    EvaluationError,
    ExtractionError,
    ProviderError,
    RateLimitError,
    SkillForgeError,
    SkillFormatError,
    TraceError,
)


class TestErrorHierarchy:
    """Tests for the error class hierarchy."""

    def test_all_inherit_from_skillforge_error(self) -> None:
        """Every custom error is a SkillForgeError."""
        assert issubclass(ConfigError, SkillForgeError)
        assert issubclass(ProviderError, SkillForgeError)
        assert issubclass(RateLimitError, SkillForgeError)
        assert issubclass(AuthError, SkillForgeError)
        assert issubclass(TraceError, SkillForgeError)
        assert issubclass(ExtractionError, SkillForgeError)
        assert issubclass(EvaluationError, SkillForgeError)
        assert issubclass(SkillFormatError, SkillForgeError)

    def test_auth_error_is_provider_error(self) -> None:
        """AuthError is a subclass of ProviderError."""
        assert issubclass(AuthError, ProviderError)

    def test_rate_limit_error_is_provider_error(self) -> None:
        """RateLimitError is a subclass of ProviderError."""
        assert issubclass(RateLimitError, ProviderError)

    def test_skillforge_error_is_exception(self) -> None:
        """SkillForgeError is a standard Exception."""
        assert issubclass(SkillForgeError, Exception)

    def test_error_message_preserved(self) -> None:
        """Error messages are preserved when raised."""
        err = AuthError("Missing API key")
        assert str(err) == "Missing API key"

    def test_catching_provider_error_catches_auth(self) -> None:
        """Catching ProviderError also catches AuthError."""
        try:
            raise AuthError("no key")
        except ProviderError as e:
            assert str(e) == "no key"
