# Regex Puzzles Example

A 10-task corpus for distilling regular expression construction skills.

## Overview

This example covers common regex challenges: IPv4 matching, email validation, phone extraction, password lookaheads, non-greedy quantifiers, named groups, backreferences, negated character classes, anchors, and Unicode properties.

## Running the example

```bash
cd examples/regex-puzzles

# Full pipeline with mock (no API key)
skillforge run --corpus tasks.yaml --provider mock --model mock-strong
skillforge extract --run runs/<id> --provider mock --out skills/regex-puzzles/SKILL.md
skillforge eval --skill skills/regex-puzzles/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak
skillforge lint skills/regex-puzzles/SKILL.md
```

## Expected output

The `expected_skill/SKILL.md` shows what a high-quality extracted skill looks like for this domain. It includes pattern recipes for each regex challenge, concrete examples, and anti-patterns to avoid.

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4
```
