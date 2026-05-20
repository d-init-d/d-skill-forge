"""Skill extraction from recorded traces via reflective distillation."""

from __future__ import annotations

from .base import Extractor
from .contrastive import ContrastiveExtractor
from .iterative import IterativeExtractor
from .reflective import ReflectiveExtractor

__all__ = ["ContrastiveExtractor", "Extractor", "IterativeExtractor", "ReflectiveExtractor"]
