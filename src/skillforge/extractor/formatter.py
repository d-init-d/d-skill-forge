"""Deep trace formatter — renders full message content for extraction."""

from __future__ import annotations

import json

from skillforge.models.trace import Trace


def format_trace_deep(trace: Trace, budget: int = 4000) -> str:
    """Format a trace with FULL message content including thinking/tool blocks.

    Args:
        trace: Trace to format.
        budget: Maximum character budget.

    Returns:
        Formatted trace text.
    """
    parts: list[str] = []
    status = "PASS" if (trace.score and trace.score.passed) else "FAIL"
    parts.append(f"## Task: {trace.task_id} [{status}]")

    for msg in trace.messages:
        parts.append(f"\n### {msg.role.upper()}")
        for block in msg.content:
            match block.type:
                case "thinking":
                    parts.append(f"<thinking>\n{block.text}\n</thinking>")
                case "text":
                    parts.append(block.text or "")
                case "tool_use":
                    input_str = json.dumps(block.input, indent=2) if block.input else "{}"
                    parts.append(f'<tool name="{block.name}">\n{input_str}\n</tool>')
                case "tool_result":
                    parts.append(f"<result>\n{block.output}\n</result>")

    if trace.error:
        parts.append(f"\n<error>{trace.error}</error>")

    full = "\n".join(parts)
    if len(full) > budget:
        return smart_truncate(full, budget)
    return full


def smart_truncate(text: str, budget: int) -> str:
    """Truncate preserving thinking blocks and start/end of content.

    Strategy: Keep first 40% and last 40% of text, cut middle.
    Prioritize <thinking> blocks — never truncate them.

    Args:
        text: Full text to truncate.
        budget: Target character count.

    Returns:
        Truncated text within budget.
    """
    if len(text) <= budget:
        return text

    # Extract thinking blocks (highest value)
    thinking_blocks: list[str] = []
    remaining = text
    while "<thinking>" in remaining:
        start = remaining.index("<thinking>")
        end = remaining.index("</thinking>") + len("</thinking>") if "</thinking>" in remaining else len(remaining)
        thinking_blocks.append(remaining[start:end])
        remaining = remaining[:start] + remaining[end:]

    thinking_text = "\n".join(thinking_blocks)

    # If thinking alone exceeds budget, truncate thinking
    if len(thinking_text) >= budget:
        return thinking_text[:budget - 20] + "\n[...truncated]"

    # Remaining budget for non-thinking content
    remaining_budget = budget - len(thinking_text) - 50
    head_budget = remaining_budget * 2 // 5
    tail_budget = remaining_budget * 2 // 5

    head = remaining[:head_budget]
    tail = remaining[-tail_budget:] if tail_budget > 0 else ""

    return f"{head}\n\n[...{len(remaining) - head_budget - tail_budget} chars truncated...]\n\n{tail}\n\n{thinking_text}"
