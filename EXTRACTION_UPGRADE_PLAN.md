# Extraction Engine Upgrade Plan — Comprehensive Knowledge Distillation

> **Goal:** Trích xuất TẤT CẢ tri thức từ model traces: reasoning chains, decision heuristics, tool usage patterns, error recovery strategies, implicit knowledge.
> **Date:** 2026-05-21

---

## Problem Statement

### Hiện tại: Chỉ trích xuất ~5% tri thức

```python
# _format_traces() hiện tại:
parts.append(f"Output: {trace.final_output[:500]}")
```

**Bỏ qua hoàn toàn:**
- `thinking` blocks — chain-of-thought, reasoning process
- `tool_use` blocks — tool selection, input construction
- `tool_result` blocks — how model interprets results
- Full `text` across messages — multi-step reasoning
- Error recovery patterns — how model handles failures

### Sau upgrade: Trích xuất ~90% tri thức

```
Trace.messages
  ├── thinking  → Reasoning patterns, mental models
  ├── text      → Procedures, explanations, decisions
  ├── tool_use  → Tool strategies, sequencing, input construction
  └── tool_result + next response → Adaptation, interpretation
```

---

## Design

### Multi-Pass Extraction Architecture

```
Pass 1: Deep Format     traces → full message rendering (thinking, tools, text)
Pass 2: Decompose       per-trace → knowledge units (reasoning, decision, tool, error)
Pass 3: Pattern Find    cross-trace → recurring patterns ranked by frequency × success
Pass 4: Synthesize      patterns → structured SKILL.md with 6+ sections
```

### New `_format_trace_deep()` — replaces 500-char truncation

```python
def _format_trace_deep(self, trace: Trace, budget: int = 4000) -> str:
    parts = [f"## Task: {trace.task_id} [{'PASS' if trace.score and trace.score.passed else 'FAIL'}]"]
    for msg in trace.messages:
        parts.append(f"\n### {msg.role.upper()}")
        for block in msg.content:
            match block.type:
                case "thinking":
                    parts.append(f"<thinking>\n{block.text}\n</thinking>")
                case "text":
                    parts.append(block.text or "")
                case "tool_use":
                    parts.append(f"<tool name=\"{block.name}\">\n{json.dumps(block.input, indent=2)}\n</tool>")
                case "tool_result":
                    parts.append(f"<result>\n{block.output}\n</result>")
    if trace.error:
        parts.append(f"\n<error>{trace.error}</error>")
    full = "\n".join(parts)
    return self._smart_truncate(full, budget) if len(full) > budget else full
```

### Multi-Pass Prompts

**Pass 1 — Reasoning & Procedure:**
```
Analyze these FULL traces (including thinking and tool calls).
Extract: reasoning patterns, step-by-step procedures, decision gates.
```

**Pass 2 — Tool Strategies & Heuristics:**
```
From these tool usage patterns, extract: tool selection rules,
input construction patterns, chaining strategies, validation approaches.
```

**Pass 3 — Error Recovery & Anti-Patterns:**
```
From these FAILED traces, extract: recovery strategies, fallback logic,
common mistakes, assumptions that lead to failure.
```

**Pass 4 — Synthesis:**
```
Combine into SKILL.md with sections:
- Mental Model, Procedure, Tool Strategies, Error Recovery, Anti-Patterns, Examples
```

### Context Budget Allocation

| Trace Type | Weight | Rationale |
|------------|--------|-----------|
| Passed + thinking | 3x | Richest reasoning |
| Passed + tool_use | 2x | Tool strategy data |
| Failed + thinking | 2.5x | Error recovery reasoning |
| Failed + no thinking | 1x | Less insight |

---

## Implementation Tasks

| # | Task | File | Effort |
|---|------|------|--------|
| 1 | `_format_trace_deep()` with smart truncation | `extractor/reflective.py` | 2h |
| 2 | Multi-pass prompt templates (4 passes) | `extractor/_prompts.py` | 2h |
| 3 | Context budget allocator | `extractor/budget.py` | 1h |
| 4 | `DeepExtractor` (multi-pass orchestrator) | `extractor/deep.py` | 4h |
| 5 | Upgrade `ReflectiveExtractor` to use deep format | `extractor/reflective.py` | 1h |
| 6 | CLI `--strategy deep` flag | `cli/extract.py` | 1h |
| 7 | Tests | `tests/unit/extractor/test_deep.py` | 2h |
| **Total** | | | **~13h** |

### Execution Order

```
Wave 1 (parallel): Task 1, 2, 3
Wave 2: Task 4 (depends on 1,2,3)
Wave 3 (parallel): Task 5, 6
Wave 4: Task 7
```

---

## Output Quality: Before vs After

### Before
```markdown
## Procedure
1. Read the error
2. Fix the code
```

### After
```markdown
## Mental Model
Think of errors as 3 layers: surface (error type), causal (violated assumption), fix (minimal change preserving intent).

## Procedure
1. Read traceback bottom-to-top
   - Decision: your code or library? If library → check your inputs
2. Identify violated assumption (TypeError→type boundary, KeyError→missing key)
3. Trace bad value backwards to source
4. Apply minimal fix (prefer guard clause over try/except)

## Tool Strategies
- Read file FIRST, then grep for the variable
- Make ONE change, then run tests
- Add assert at suspected line before fixing

## Error Recovery
- First fix fails → revert, re-read traceback
- Error moves line → you fixed symptom not cause

## Anti-Patterns
- Don't wrap in try/except without understanding cause
- Don't add `if x is not None` everywhere (fix source of None)
```

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Trace data used | ~5% | >80% |
| SKILL.md sections | 2-3 | 6+ |
| Actionable heuristics | 2-3 | 10-15 |
| Eval delta (weak model improvement) | +10-20% | +30-50% |
