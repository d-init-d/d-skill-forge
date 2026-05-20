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
