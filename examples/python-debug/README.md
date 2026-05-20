# Python Debug Example

A 15-task corpus covering common Python runtime errors.

## Quick Start

```bash
cd examples/python-debug

# Run the corpus with mock provider (no API key needed)
skillforge run --corpus tasks.yaml --provider mock --model mock-strong

# Extract a skill from the run
skillforge extract --run runs/<run_id> --provider mock --model mock-strong --out skills/python-debug/SKILL.md

# Evaluate the skill
skillforge eval --skill skills/python-debug/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak

# Lint the generated skill
skillforge lint skills/python-debug/SKILL.md
```

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4
```

## Task coverage

| Error Type | Tasks |
|---|---|
| TypeError | 2 |
| AttributeError | 2 |
| KeyError | 2 |
| IndexError | 2 |
| ImportError | 1 |
| ValueError | 2 |
| Mutable default | 1 |
| Async misuse | 1 |
| Off-by-one | 1 |
| RecursionError | 1 |
