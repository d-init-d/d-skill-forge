# ruff: noqa: D101, D102
"""Tests for the skillforge logging module."""

from __future__ import annotations

import logging

from rich.console import Console

from skillforge.logging import get_console, get_logger


class TestGetLogger:
    def test_returns_logger_instance(self) -> None:
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_logger_has_handler(self) -> None:
        logger = get_logger("test.handler_check")
        assert len(logger.handlers) >= 1


class TestGetConsole:
    def test_returns_console_instance(self) -> None:
        console = get_console()
        assert isinstance(console, Console)

    def test_returns_same_instance(self) -> None:
        c1 = get_console()
        c2 = get_console()
        assert c1 is c2
