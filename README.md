<p align="center">
  <h1 align="center">🔥 d-skill-forge</h1>
  <p align="center">
    <strong>Distill procedural skills from frontier model traces into reusable SKILL.md artifacts</strong>
  </p>
  <p align="center">
    <a href="https://github.com/d-init-d/d-skill-forge/actions/workflows/ci.yml"><img src="https://github.com/d-init-d/d-skill-forge/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
    <a href="https://github.com/d-init-d/d-skill-forge/releases"><img src="https://img.shields.io/github/v/release/d-init-d/d-skill-forge?color=blue" alt="Release"></a>
    <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/license-Apache--2.0-green.svg" alt="License">
  </p>
</p>

---

## What is d-skill-forge?

d-skill-forge captures how strong models (Claude Opus, GPT-5) solve tasks, reflects on the execution traces, and produces a structured **SKILL.md** file. When loaded into a weaker model's context, the skill improves its performance on the same domain — **no fine-tuning required**.

```
Task corpus  →  STRONG MODEL  →  Traces  →  REFLECTIVE DISTILL  →  SKILL.md  →  WEAK MODEL  →  +40% score
```

---

## Install

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/d-init-d/d-skill-forge/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/d-init-d/d-skill-forge/main/install.ps1 | iex
```

### From source (with pip)

```bash
pip install d-skill-forge[tui]
```

---

## Usage

```bash
dskillforge
```

That's it. The TUI launches automatically.

### TUI Features

| Key | Action |
|-----|--------|
| `c` | Connect a provider |
| `m` | Select model |
| `1` | Run corpus |
| `2` | Extract skill |
| `3` | Evaluate |
| `4` | Lint |
| `Tab` | Next step |
| `q` | Quit |

### CLI Mode

```bash
# Run without TUI
dskillforge run --provider groq --model llama-3.3-70b-versatile --corpus tasks.yaml
dskillforge extract --run runs/<id> --provider groq --out skills/SKILL.md
dskillforge eval --skill skills/SKILL.md --corpus tasks.yaml --provider mock
dskillforge lint skills/SKILL.md
```

---

## Providers (15+)

| Provider | Type | Auth |
|----------|------|------|
| Anthropic | Built-in | `ANTHROPIC_API_KEY` |
| OpenAI | Built-in | `OPENAI_API_KEY` |
| Groq | Preset | `GROQ_API_KEY` |
| DeepSeek | Preset | `DEEPSEEK_API_KEY` |
| Together AI | Preset | `TOGETHER_API_KEY` |
| Fireworks AI | Preset | `FIREWORKS_API_KEY` |
| OpenRouter | Preset | `OPENROUTER_API_KEY` |
| xAI (Grok) | Preset | `XAI_API_KEY` |
| NVIDIA | Preset | `NVIDIA_API_KEY` |
| Cerebras | Preset | `CEREBRAS_API_KEY` |
| Amazon Bedrock | Built-in | AWS credentials |
| Google Gemini | Built-in | `GOOGLE_API_KEY` |
| Ollama | Local | (none) |
| LM Studio | Local | (none) |
| Any OpenAI-compatible | Custom | configurable |

Connect in TUI: press `c` → select provider → paste key → done.

---

## How It Works

```bash
# 1. Init a project
dskillforge init demo && cd demo

# 2. Run tasks against a strong model
dskillforge run --provider anthropic --model claude-opus-4 --corpus tasks.yaml

# 3. Extract a skill from the traces
dskillforge extract --run runs/<id> --provider anthropic --out skills/SKILL.md

# 4. Evaluate: does the skill help a weaker model?
dskillforge eval --skill skills/SKILL.md --corpus tasks.yaml --provider anthropic --weak-model claude-haiku-4

# 5. Validate
dskillforge lint skills/SKILL.md
```

### Output: SKILL.md

```markdown
---
name: python-debug
description: Fix common Python runtime errors
version: 1.0.0
source_model: claude-opus-4
triggers: [TypeError, AttributeError, KeyError]
domains: [python, debugging]
---

## Strategy
When encountering a Python error...

## Examples
...
```

---

## Quick Demo (no API key needed)

```bash
dskillforge init demo && cd demo
dskillforge run --provider mock --corpus tasks.yaml
dskillforge extract --run runs/<id> --provider mock --out skills/demo/SKILL.md
dskillforge eval --skill skills/demo/SKILL.md --corpus tasks.yaml --provider mock
```

---

## Documentation

- [TUI Guide](docs/tui.md)
- [Providers](docs/providers.md)
- [Authentication](docs/auth.md)
- [Concepts](docs/concepts.md)
- [Architecture](docs/architecture.md)
- [CLI Reference](docs/reference/cli.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache-2.0](LICENSE)
