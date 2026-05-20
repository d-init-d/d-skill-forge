"""Structured logging utilities for skillforge.

Provides a shared Rich console and stdlib logger configured with RichHandler.
"""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

_console: Console | None = None


def get_console() -> Console:
    """Return the shared Rich console instance.

    Returns:
        The singleton Console used for all terminal output.
    """
    global _console  # noqa: PLW0603
    if _console is None:
        _console = Console()
    return _console


def get_logger(name: str) -> logging.Logger:
    """Return a stdlib logger configured with RichHandler.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        A configured Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(console=get_console(), show_path=False, markup=True)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
