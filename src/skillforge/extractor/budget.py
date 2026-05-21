"""Context budget allocation for extraction passes."""

from __future__ import annotations

from skillforge.models.trace import Trace


def compute_trace_weight(trace: Trace) -> float:
    """Compute importance weight for a trace based on content richness.

    Args:
        trace: Trace to evaluate.

    Returns:
        Weight multiplier (1.0 to 3.0).
    """
    has_thinking = any(
        b.type == "thinking" for m in trace.messages for b in m.content
    )
    has_tools = any(
        b.type == "tool_use" for m in trace.messages for b in m.content
    )
    passed = trace.score and trace.score.passed

    if passed and has_thinking:
        return 3.0
    if not passed and has_thinking:
        return 2.5
    if passed and has_tools:
        return 2.0
    if passed:
        return 1.5
    return 1.0


def allocate_budgets(
    traces: list[Trace],
    total_budget: int = 80_000,
) -> list[int]:
    """Allocate character budget per trace proportional to weight.

    Args:
        traces: Traces to allocate budget for.
        total_budget: Total character budget across all traces.

    Returns:
        List of per-trace character budgets (same order as input).
    """
    if not traces:
        return []

    weights = [compute_trace_weight(t) for t in traces]
    total_weight = sum(weights)

    return [int((w / total_weight) * total_budget) for w in weights]
