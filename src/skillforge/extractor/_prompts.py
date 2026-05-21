"""Prompt templates for reflective skill extraction."""

from __future__ import annotations

REFLECTIVE_EXTRACTION_MARKER = "<<SKILLFORGE_REFLECTIVE_EXTRACTION_V1>>"

REFLECTIVE_EXTRACTION_PROMPT_V1 = """\
{marker}
You are a skill extraction engine. Analyze the following execution traces and \
distill a reusable procedural skill in SKILL.md format.

## Source Information
- Run ID: {run_id}
- Model: {model}
- Domain: {domain}
- Total traces: {total_traces}
- Passed: {passed_count}
- Failed: {failed_count}

## Traces

{traces_text}

## Instructions

Reflect on the patterns in successful traces and anti-patterns in failed traces.
Produce a SKILL.md with YAML frontmatter and these sections:
- ## When to use
- ## Procedure
- ## Examples
- ## Anti-patterns

The frontmatter must include:
- name: (kebab-case, derived from the domain)
- description: (one sentence)
- version: "0.1.0"
- source_model: "{model}"
- extracted_from:
    total_traces: {total_traces}
    passed_traces: {passed_count}
    failed_traces: {failed_count}
    extractor: "reflective@0.1"
    extracted_at: "{extracted_at}"
- triggers: (list of keywords)
- domains: ["{domain}"]
- license: "Apache-2.0"

Output ONLY the complete SKILL.md content starting with ---.
"""

CONTRASTIVE_EXTRACTION_MARKER = "<<SKILLFORGE_CONTRASTIVE_EXTRACTION_V1>>"

CONTRASTIVE_EXTRACTION_PROMPT_V1 = """\
{marker}
You are a skill extraction engine performing contrastive analysis. You will see \
pairs of (strong trace, weak trace) for the same task. The strong run passed; the \
weak run failed or scored lower. Distill the decisive differences into a SKILL.md.

## Source Information
- Strong run: {strong_run_id} (model: {strong_model})
- Weak run: {weak_run_id} (model: {weak_model})
- Domain: {domain}
- Total pairs: {total_pairs}
- Strong passed: {strong_passed}
- Weak passed: {weak_passed}

## Trace Pairs

{pairs_text}

## Instructions

For each pair, identify what the strong model did differently that led to success.
Produce a SKILL.md with YAML frontmatter and these sections:
- ## When to use
- ## Decisive differences
- ## Procedure
- ## Anti-patterns (from weak model failures)

The frontmatter must include:
- name: (kebab-case, derived from the domain)
- description: (one sentence)
- version: "0.1.0"
- source_model: "{strong_model}"
- extracted_from:
    total_traces: {total_pairs}
    passed_traces: {strong_passed}
    failed_traces: {weak_passed}
    extractor: "contrastive@0.1"
    extracted_at: "{extracted_at}"
- triggers: (list of keywords)
- domains: ["{domain}"]
- license: "Apache-2.0"

Output ONLY the complete SKILL.md content starting with ---.
"""

ITERATIVE_EXTRACTION_MARKER = "<<SKILLFORGE_ITERATIVE_EXTRACTION_V1>>"

ITERATIVE_REFINEMENT_PROMPT_V1 = """\
{marker}
You are refining an existing SKILL.md. Review the current draft and improve it.

## Current Draft
{current_skill}

## Source Traces (for reference)
{traces_text}

## Instructions
Review the current skill draft. Identify:
- Missing patterns from the traces
- Overly vague rules that could be more specific
- Anti-patterns not yet captured

Output the COMPLETE revised SKILL.md starting with ---.
If the skill is already optimal, output it unchanged.
"""


# =============================================================================
# DEEP EXTRACTION — Multi-Pass Prompts
# =============================================================================

DEEP_PASS1_REASONING = """\
You are a knowledge extraction engine. Analyze these FULL execution traces \
(including thinking blocks, tool calls, and results).

## Traces

{traces_text}

## Task

Extract REASONING PATTERNS and PROCEDURES:

1. **Reasoning patterns**: How does the model think through problems?
   - What questions does it ask itself?
   - What decomposition strategies does it use?
   - What mental models does it apply?

2. **Step-by-step procedures**: What sequence leads to success?
   - What's the typical order of operations?
   - What are decision gates between steps?
   - When does it deviate from the standard path?

Output as structured text. Be specific — cite exact reasoning from the traces.
"""

DEEP_PASS2_TOOLS = """\
You are a knowledge extraction engine. Analyze tool usage patterns from these traces.

## Traces

{traces_text}

## Task

Extract DECISION HEURISTICS and TOOL STRATEGIES:

1. **Decision heuristics**: What rules guide approach selection?
   - When does it choose tool A vs tool B?
   - What signals trigger a strategy change?
   - What thresholds or conditions matter?

2. **Tool strategies**: How does it use tools effectively?
   - What patterns in input construction lead to success?
   - How does it chain sequential tool calls?
   - How does it validate and interpret tool outputs?

Output as structured text. Be specific — reference actual tool names and patterns.
"""

DEEP_PASS3_ERRORS = """\
You are a knowledge extraction engine. Analyze these FAILED traces and error recovery patterns.

## Failed Traces

{traces_text}

## Successful Traces (for contrast)

{success_traces}

## Task

Extract ERROR RECOVERY and ANTI-PATTERNS:

1. **Error recovery**: How does the model recover from failures?
   - What retry strategies does it use?
   - How does it adapt after a failed attempt?
   - What fallback paths does it take?

2. **Anti-patterns**: What approaches consistently fail?
   - What common mistakes appear in failed traces?
   - What assumptions lead to failure?
   - What should always be avoided?

Output as structured text. Be specific.
"""

DEEP_PASS4_SYNTHESIS = """\
You are synthesizing extracted knowledge into a SKILL.md file.

## Extracted Knowledge

### Reasoning & Procedures
{pass1_output}

### Tool Strategies & Heuristics
{pass2_output}

### Error Recovery & Anti-Patterns
{pass3_output}

## Source Info
- Model: {model}
- Domain: {domain}
- Total traces: {total_traces} (passed: {passed_count}, failed: {failed_count})

## Task

Produce a complete SKILL.md with YAML frontmatter and these sections:
- ## Mental Model (how to think about problems in this domain)
- ## Procedure (step-by-step with decision gates)
- ## Tool Strategies (when/how to use tools effectively)
- ## Error Recovery (what to do when things fail)
- ## Anti-Patterns (what to avoid and why)
- ## Examples (concrete before/after from the traces)

Frontmatter must include:
- name: (kebab-case)
- description: (one sentence)
- version: "0.1.0"
- source_model: "{model}"
- extracted_from:
    total_traces: {total_traces}
    passed_traces: {passed_count}
    failed_traces: {failed_count}
    extractor: "deep@1.0"
    extracted_at: "{extracted_at}"
- triggers: (list of keywords)
- domains: ["{domain}"]
- license: "Apache-2.0"

Output ONLY the complete SKILL.md starting with ---.
"""
