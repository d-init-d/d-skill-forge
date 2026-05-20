---
name: skill-forge-driver
description: Teaches agents how to use the skillforge CLI to distill procedural skills from model traces.
version: "0.1.0"
source_model: claude-opus-4
extracted_from:
  total_traces: 1
  passed_traces: 1
  failed_traces: 0
  extractor: "manual@0.1"
  extracted_at: "2026-05-20T00:00:00Z"
triggers:
  - distill skill
  - extract skill
  - skill from traces
  - skillforge
  - SKILL.md
domains:
  - ai-engineering
  - prompt-engineering
license: Apache-2.0
---

## When to use

Use this skill when you need to:
- Distill a reusable procedural skill from model execution traces
- Compare how a strong model vs weak model solves the same tasks
- Evaluate whether a skill actually improves a weaker model's performance
- Create SKILL.md artifacts for prompt-layer knowledge transfer

## Prerequisites

- Python 3.11+ with `d-skill-forge` installed (`pip install d-skill-forge`)
- A task corpus in YAML format (see `skillforge init` for scaffolding)
- For real extraction: an API key for the provider (Anthropic, OpenAI, Bedrock, or Gemini)
- For testing/development: the `mock` provider requires no credentials

## Procedure

### Step 1: Initialize a project

```bash
skillforge init my-project
cd my-project
```

This creates `skillforge.toml` and a sample `tasks.yaml`.

### Step 2: Define your task corpus

Edit `tasks.yaml` with domain-specific tasks. Each task needs:
- `id`: unique identifier
- `prompt`: the question/instruction
- `expected`: how to evaluate (exact, regex, contains, llm_judge, executes_ok)

### Step 3: Run the strong model

```bash
skillforge run --provider anthropic --model claude-opus-4 --corpus tasks.yaml
```

This produces traces in `runs/<run_id>/`.

### Step 4: Extract a skill (reflective mode)

```bash
skillforge extract --run runs/<run_id> --provider anthropic --model claude-opus-4 --out skills/my-skill/SKILL.md
```

### Step 4b: Extract a skill (contrastive mode)

For contrastive extraction, run both strong and weak models first:

```bash
skillforge run --provider mock --model mock-strong --corpus tasks.yaml
skillforge run --provider mock --model mock-weak --corpus tasks.yaml
skillforge extract --strategy contrastive --strong-run runs/<strong_id> --weak-run runs/<weak_id> --provider mock --out skills/contrastive/SKILL.md
```

### Step 5: Validate the skill

```bash
skillforge lint skills/my-skill/SKILL.md
```

### Step 6: Evaluate the skill

```bash
skillforge eval --skill skills/my-skill/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak --bootstrap 1000
```

This produces:
- Terminal output with delta, CI, and significance verdict
- `delta_report.json` with full statistical breakdown

### Step 7: Iterate

If the delta is not significant or negative:
1. Review the SKILL.md for vague or incorrect rules
2. Add more tasks to the corpus covering failure modes
3. Re-run extraction with more traces

## Anti-patterns

- **Don't skip evaluation.** A skill that doesn't measurably help is noise.
- **Don't extract from too few traces.** Minimum 10 tasks for meaningful patterns.
- **Don't use the same model for extraction and evaluation.** The point is transfer to a weaker model.
- **Don't hardcode provider-specific patterns.** Skills should be model-agnostic.
- **Don't trust a single run.** Use `--bootstrap` to get confidence intervals.

## Examples

### Quick mock pipeline (no API key needed)

```bash
skillforge init demo && cd demo
skillforge run --provider mock --corpus tasks.yaml
RUN=$(ls runs/)
skillforge extract --run runs/$RUN --provider mock --out skills/demo/SKILL.md
skillforge eval --skill skills/demo/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak --bootstrap 1000
skillforge lint skills/demo/SKILL.md
```

## Environment check

Run `skillforge doctor` to verify your setup before starting.
