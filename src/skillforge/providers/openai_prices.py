"""Pricing data for OpenAI models (USD per token)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Per-token pricing for a model."""

    input_per_token: float
    output_per_token: float


# Prices as of 2024-Q4 (USD per token).
OPENAI_PRICES: dict[str, ModelPricing] = {
    "gpt-5": ModelPricing(input_per_token=30.0 / 1_000_000, output_per_token=60.0 / 1_000_000),
    "gpt-5-mini": ModelPricing(input_per_token=5.0 / 1_000_000, output_per_token=15.0 / 1_000_000),
    "gpt-4o": ModelPricing(input_per_token=2.5 / 1_000_000, output_per_token=10.0 / 1_000_000),
    "gpt-4o-mini": ModelPricing(input_per_token=0.15 / 1_000_000, output_per_token=0.6 / 1_000_000),
}
