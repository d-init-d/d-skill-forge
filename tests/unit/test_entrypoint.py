# ruff: noqa: D101, D102
"""Tests for __main__.py entrypoint."""

from __future__ import annotations

import subprocess
import sys


class TestEntrypoint:
    def test_python_m_skillforge_help_exits_0(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skillforge", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert "skillforge" in result.stdout.lower() or "Usage" in result.stdout
