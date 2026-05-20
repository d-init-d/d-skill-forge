# SQL Debug Example

A 10-task corpus covering common SQL query errors.

## Quick Start

```bash
cd examples/sql-debug

# Run the corpus with mock provider (no API key needed)
skillforge run --corpus tasks.yaml --provider mock --model mock-strong

# Extract a skill from the run
skillforge extract --run runs/<run_id> --provider mock --model mock-strong --out skills/sql-debug/SKILL.md

# Evaluate the skill
skillforge eval --skill skills/sql-debug/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak

# Lint the generated skill
skillforge lint skills/sql-debug/SKILL.md
```

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4
```

## Task coverage

| Bug Type | Task ID |
|---|---|
| Missing JOIN | fix-missing-join |
| NULL comparison with = | fix-null-comparison |
| GROUP BY without aggregate | fix-group-by-no-aggregate |
| Ambiguous column | fix-ambiguous-column |
| Integer division | fix-integer-division |
| ORDER BY before LIMIT | fix-order-by-limit |
| Missing WHERE | fix-missing-where |
| INSERT without column list | fix-insert-no-columns |
| COUNT(*) vs COUNT(col) | fix-count-star-vs-col |
| Subquery correlation | fix-subquery-correlation |
