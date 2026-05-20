# Concepts

## Task Corpus

A YAML file defining prompts and expected outcomes. Each task has:

- **id** — unique identifier
- **prompt** — what the model is asked to do
- **expected** — how to judge success (`exact`, `contains`, `regex`, `executes_ok`, `llm_judge`)
- **context** — optional system-level context
- **inputs** — template variables for `{{ var }}` interpolation

```yaml
tasks:
  - id: "fix-type-error"
    prompt: "Fix: result = 'count: ' + 42"
    expected:
      kind: "executes_ok"
```

## Trace

A complete record of one model execution: the messages exchanged, thinking blocks, tool calls, token usage, latency, cost, and the evaluator's score. Traces are stored as JSONL files under `runs/<id>/traces/`.

## Run

A single execution of a corpus against a provider/model. Produces a `manifest.json` (metadata, results summary) and one trace file per task.

## Reflective Extraction

The core innovation. After collecting traces, the same strong model is asked to **reflect** on its own behavior across all tasks and distill the patterns into a structured skill document. The extractor:

1. Stratified-samples traces (biased toward passed, includes some failed)
2. Formats them into a reflection prompt
3. Asks the model to produce a SKILL.md with procedures, examples, and anti-patterns

## SKILL.md

The output artifact. A markdown file with YAML frontmatter containing:

- **Frontmatter**: name, description, source model, extraction stats, triggers, domains
- **Body sections**: When to use, Procedure, Examples, Anti-patterns

Skills are loaded into a weak model's system prompt at inference time to improve its performance on the target domain.

## Eval Delta

The measurable improvement. Evaluation runs the corpus twice with a weak model:

1. **Baseline** — weak model alone
2. **With skill** — weak model + SKILL.md in system prompt

The delta (score difference) quantifies the skill's value. A positive delta means the skill helps.

## Providers

Adapters for LLM APIs. Built-in: `anthropic`, `openai`, `mock`. The mock provider enables the full pipeline without API keys or network access.
