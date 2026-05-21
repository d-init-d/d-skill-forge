"""Tests for the AuthStore credential manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from skillforge.auth import AuthStore


@pytest.fixture
def auth_store(tmp_path: Path) -> AuthStore:
    """Create an AuthStore with a temp path."""
    return AuthStore(path=tmp_path / "auth.json")


def test_empty_store(auth_store: AuthStore) -> None:
    """New store has no providers."""
    assert auth_store.list_providers() == []
    assert auth_store.get("anthropic") is None


def test_set_and_get(auth_store: AuthStore) -> None:
    """Can store and retrieve a key."""
    auth_store.set("groq", "gsk_test123")
    assert auth_store.get("groq") == "gsk_test123"


def test_list_providers(auth_store: AuthStore) -> None:
    """List returns sorted provider names."""
    auth_store.set("openai", "sk-test")
    auth_store.set("anthropic", "sk-ant-test")
    assert auth_store.list_providers() == ["anthropic", "openai"]


def test_delete(auth_store: AuthStore) -> None:
    """Delete removes a provider."""
    auth_store.set("groq", "key")
    assert auth_store.delete("groq") is True
    assert auth_store.get("groq") is None
    assert auth_store.delete("groq") is False


def test_persistence(tmp_path: Path) -> None:
    """Data persists across instances."""
    path = tmp_path / "auth.json"
    store1 = AuthStore(path=path)
    store1.set("test", "value123")

    store2 = AuthStore(path=path)
    assert store2.get("test") == "value123"


def test_overwrite(auth_store: AuthStore) -> None:
    """Setting same provider overwrites."""
    auth_store.set("groq", "old")
    auth_store.set("groq", "new")
    assert auth_store.get("groq") == "new"
