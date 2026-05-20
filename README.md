# d-skill-forge

[![CI](https://github.com/d-init-d/d-skill-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/d-init-d/d-skill-forge/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

Distill procedural skills from frontier model traces into reusable **SKILL.md** artifacts that make weaker models measurably better.

## What it does

d-skill-forge captures how strong models (Claude Opus, GPT-5) solve tasks, reflects on the execution traces, and produces a structured markdown skill file. When loaded into a weaker model's context, the skill improves its performance on the same domain — no fine-tuning required.

## Install

```bash
pip install d-skill-forge
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add d-skill-forge
```

## Quickstart

```bash
# Scaffold a project
skillforge init demo && cd demo

# Run tasks against a model (mock = no API key needed)
skillforge run --provider mock --corpus tasks.yaml

# Extract a skill from the traces
skillforge extract --run runs/<id> --provider mock --out skills/demo/SKILL.md

# Evaluate: does the skill help a weaker model?
skillforge eval --skill skills/demo/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak

# Validate the skill format
skillforge lint skills/demo/SKILL.md

# Check provider configuration
skillforge doctor
```

## Contrastive Extraction

Compare strong vs weak model traces to extract targeted skills:

```bash
# Run both models on the same corpus
skillforge run --provider anthropic --model claude-opus-4 --corpus tasks.yaml
skillforge run --provider anthropic --model claude-haiku-3 --corpus tasks.yaml

# Extract what the strong model does differently
skillforge extract --strategy contrastive \
  --strong-run runs/<strong-id> \
  --weak-run runs/<weak-id> \
  --provider anthropic --model claude-opus-4 \
  --out skills/SKILL.md
```

## Eval with Bootstrap CI

Measure skill impact with statistical confidence:

```bash
skillforge eval --skill skills/SKILL.md --corpus tasks.yaml \
  --provider mock --weak-model mock-weak --bootstrap 1000
```

Example output:

```
┌─────────────────┬────────┐
│ Metric          │ Value  │
├─────────────────┼────────┤
│ Baseline score  │ 0.400  │
│ With skill      │ 0.800  │
│ Delta           │ +0.400 │
│ Tasks evaluated │ 5      │
└─────────────────┴────────┘

Bootstrap (1000 resamples, 95% CI):
  delta = +0.4000  95% CI [+0.2000, +0.6000]
  Wins: 4 | Losses: 0 | Ties: 1
  Verdict: SIGNIFICANT
```

## Provider Matrix

| Provider | Install | Env Var |
|----------|---------|---------|
| anthropic | included | `ANTHROPIC_API_KEY` |
| openai | included | `OPENAI_API_KEY` |
| bedrock | `pip install d-skill-forge[bedrock]` | AWS credentials |
| gemini | `pip install d-skill-forge[gemini]` | `GOOGLE_API_KEY` |
| mock | included | (none) |

## With a real provider

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --provider anthropic --model claude-opus-4 --corpus tasks.yaml
```

## Documentation

- [Quickstart](docs/quickstart.md)
- [Concepts](docs/concepts.md)
- [Architecture](docs/architecture.md)
- [Extractors](docs/extractors.md)
- [Providers](docs/providers.md)
- [CLI Reference](docs/reference/cli.md)

## Example

See [`examples/python-debug/`](examples/python-debug/) for a complete 15-task corpus covering common Python runtime errors.

## License

[Apache-2.0](LICENSE)
