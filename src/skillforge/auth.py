"""Credential store for provider API keys.

Stores credentials in ~/.config/skillforge/auth.json with restricted
file permissions. Supports get/set/delete/list operations.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any


def _default_auth_path() -> Path:
    """Return the default auth.json path respecting XDG on Linux."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "skillforge" / "auth.json"


class AuthStore:
    """Manages provider credentials persisted in auth.json.

    Args:
        path: Override path to auth.json. Defaults to platform-appropriate location.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _default_auth_path()
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load auth.json from disk."""
        if not self._path.exists():
            return {"version": 1, "credentials": {}}
        try:
            content = self._path.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return {"version": 1, "credentials": {}}

    def _save(self) -> None:
        """Persist auth.json to disk with restricted permissions."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2) + "\n",
            encoding="utf-8",
        )
        # Restrict to owner-only on Unix
        if os.name != "nt":
            self._path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    @property
    def credentials(self) -> dict[str, dict[str, str]]:
        """Access the credentials dict."""
        return self._data.setdefault("credentials", {})

    def get(self, provider: str) -> str | None:
        """Get API key for a provider.

        Args:
            provider: Provider identifier (e.g. "anthropic", "groq").

        Returns:
            The API key string, or None if not stored.
        """
        entry = self.credentials.get(provider)
        if entry and isinstance(entry, dict):
            return entry.get("api_key")
        return None

    def set(self, provider: str, api_key: str) -> None:
        """Store API key for a provider.

        Args:
            provider: Provider identifier.
            api_key: The API key to store.
        """
        self.credentials[provider] = {"api_key": api_key}
        self._save()

    def delete(self, provider: str) -> bool:
        """Remove credentials for a provider.

        Args:
            provider: Provider identifier.

        Returns:
            True if the provider was found and removed.
        """
        if provider in self.credentials:
            del self.credentials[provider]
            self._save()
            return True
        return False

    def list_providers(self) -> list[str]:
        """List all providers with stored credentials.

        Returns:
            Sorted list of provider names.
        """
        return sorted(self.credentials.keys())
