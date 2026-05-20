"""Prompt templates for reflective skill extraction."""

from __future__ import annotations

REFLECTIVE_EXTRACTION_PROMPT_V1 = """\
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
