# Python Debug Example

A 15-task corpus for distilling Python debugging skills.

## Overview

This example covers common runtime errors: TypeError, AttributeError, KeyError, IndexError, ImportError, ValueError, async misuse, off-by-one errors, mutable defaults, and RecursionError.

## Running the example

```bash
cd examples/python-debug

# Full pipeline with mock (no API key)
skillforge run --corpus tasks.yaml --provider mock --model mock-strong
skillforge extract --run runs/<id> --provider mock --out skills/python-debug/SKILL.md
skillforge eval --skill skills/python-debug/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak
skillforge lint skills/python-debug/SKILL.md
```

## Expected output

The `expected_skill/SKILL.md` shows what a high-quality extracted skill looks like for this domain. It includes fix patterns for each error type, concrete examples, and anti-patterns to avoid.

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4
```
