# SQL Debug Example

A 10-task corpus for distilling SQL debugging skills.

## Overview

This example covers common SQL query errors: missing JOINs, NULL comparisons with `=`, GROUP BY without aggregates, ambiguous columns, integer division, clause ordering, missing WHERE, INSERT without column lists, COUNT semantics, and correlated subqueries.

## Running the example

```bash
cd examples/sql-debug

# Full pipeline with mock (no API key)
skillforge run --corpus tasks.yaml --provider mock --model mock-strong
skillforge extract --run runs/<id> --provider mock --out skills/sql-debug/SKILL.md
skillforge eval --skill skills/sql-debug/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak
skillforge lint skills/sql-debug/SKILL.md
```

## Expected output

The `expected_skill/SKILL.md` shows what a high-quality extracted skill looks like for this domain. It includes fix patterns for each SQL error type, concrete examples, and anti-patterns to avoid.

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4
```
