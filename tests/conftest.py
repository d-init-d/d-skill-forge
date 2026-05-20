"""Shared test fixtures and configuration for the skillforge test suite."""

from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip tests marked `smoke` unless RUN_SMOKE=1 is set."""
    if os.environ.get("RUN_SMOKE") == "1":
        return
    skip_smoke = pytest.mark.skip(reason="smoke tests require RUN_SMOKE=1 and real API credentials")
    for item in items:
        if "smoke" in item.keywords:
            item.add_marker(skip_smoke)
