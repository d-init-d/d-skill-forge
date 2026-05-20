"""Typed error hierarchy for skillforge.

All user-facing errors inherit from SkillForgeError. The CLI top-level
catches SkillForgeError and prints a styled message with the appropriate
exit code.
"""

from __future__ import annotations


class SkillForgeError(Exception):
    """Base exception for all skillforge errors."""


class ConfigError(SkillForgeError):
    """Raised when configuration is invalid or missing."""


class ProviderError(SkillForgeError):
    """Raised when a provider operation fails."""


class RateLimitError(ProviderError):
    """Raised when a provider rate-limits the request."""


class AuthError(ProviderError):
    """Raised when provider authentication fails (missing or invalid key)."""


class TraceError(SkillForgeError):
    """Raised when trace recording or loading fails."""


class ExtractionError(SkillForgeError):
    """Raised when skill extraction fails."""


class EvaluationError(SkillForgeError):
    """Raised when evaluation fails."""


class SkillFormatError(SkillForgeError):
    """Raised when a SKILL.md file has invalid format."""
