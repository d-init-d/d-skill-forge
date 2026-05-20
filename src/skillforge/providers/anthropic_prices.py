"""Pricing data for Anthropic models (USD per token)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Per-token pricing for a model."""

    input_per_token: float
    output_per_token: float


# Prices as of 2024-Q4 (USD per token).
ANTHROPIC_PRICES: dict[str, ModelPricing] = {
    "claude-opus-4": ModelPricing(
        input_per_token=15.0 / 1_000_000, output_per_token=75.0 / 1_000_000
    ),
    "claude-sonnet-4": ModelPricing(
        input_per_token=3.0 / 1_000_000, output_per_token=15.0 / 1_000_000
    ),
    "claude-haiku-4": ModelPricing(
        input_per_token=0.25 / 1_000_000, output_per_token=1.25 / 1_000_000
    ),
}
