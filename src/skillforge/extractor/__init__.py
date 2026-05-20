"""Skill extraction from recorded traces via reflective distillation."""

from __future__ import annotations

from .base import Extractor
from .reflective import ReflectiveExtractor

__all__ = ["Extractor", "ReflectiveExtractor"]
