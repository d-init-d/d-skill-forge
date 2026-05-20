# Regex Puzzles Example

A 10-task corpus covering common regular expression challenges.

## Quick Start

```bash
cd examples/regex-puzzles

# Run the corpus with mock provider (no API key needed)
skillforge run --corpus tasks.yaml --provider mock --model mock-strong

# Extract a skill from the run
skillforge extract --run runs/<run_id> --provider mock --model mock-strong --out skills/regex-puzzles/SKILL.md

# Evaluate the skill
skillforge eval --skill skills/regex-puzzles/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak

# Lint the generated skill
skillforge lint skills/regex-puzzles/SKILL.md
```

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4
```

## Task coverage

| Pattern | Task ID |
|---|---|
| IPv4 matching | match-ipv4-address |
| Email validation | validate-email-format |
| Phone extraction | extract-phone-number |
| Password lookahead | password-lookahead |
| Non-greedy | non-greedy-match |
| Named groups | named-groups-date |
| Backreferences | backreference-repeated-word |
| Character class negation | negated-character-class |
| Anchors | anchors-full-line |
| Unicode | unicode-letter-match |
