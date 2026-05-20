"""Filesystem path conventions and helpers.

Provides ULID generation, ISO timestamp formatting, and standard directory
resolution for runs and skills.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import ulid

if TYPE_CHECKING:
    from pathlib import Path


def generate_ulid() -> str:
    """Generate a new ULID string.

    Returns:
        A 26-character ULID string.
    """
    return str(ulid.new())


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        ISO-8601 formatted UTC timestamp.
    """
    return datetime.now(tz=UTC).isoformat()


def runs_dir(base: Path) -> Path:
    """Return the runs directory under the given base path.

    Args:
        base: Project base directory.

    Returns:
        Path to the runs directory.
    """
    return base / "runs"


def skills_dir(base: Path) -> Path:
    """Return the skills directory under the given base path.

    Args:
        base: Project base directory.

    Returns:
        Path to the skills directory.
    """
    return base / "skills"
