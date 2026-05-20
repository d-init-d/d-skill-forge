---
inclusion: always
---

# Product: d-skill-forge

## What we are building

`d-skill-forge` is a professional Python CLI tool that distills *procedural skills* from frontier model traces (Claude Opus, GPT-5, etc.) into reusable `SKILL.md` artifacts that can guide weaker models at inference time.

The mental model is **reflective knowledge distillation at the prompt layer**: the strong model executes a task corpus, captures full traces (thinking, tool calls, decisions), reflects on its own behaviour, and emits a structured SKILL.md. That SKILL.md is then loaded into the context of a weaker model, which produces measurably better outputs on the same domain.

## Core flow

```
Task corpus  →  STRONG MODEL  →  Traces  →  REFLECTIVE DISTILL  →  SKILL.md  →  WEAK MODEL  →  Eval delta
   (yaml)      (Opus / GPT-5)   (jsonl)      (same strong model)    (markdown)    (Haiku / 4o-mini)
```

## CLI surface

Four user-facing commands:

| Command | Purpose |
|---|---|
| `skillforge init <dir>` | Scaffold a project (skillforge.toml + tasks.yaml). |
| `skillforge run --corpus tasks.yaml --provider anthropic --model claude-opus-4` | Execute a corpus, record traces. |
| `skillforge extract --run <run_dir>` | Distill traces into SKILL.md via reflective extraction. |
| `skillforge eval --skill <path> --weak-model <name>` | Compare weak model with vs. without the skill. |

Plus a utility: `skillforge lint <SKILL.md>` to validate format.

## Audience

- Technical users: AI engineers, researchers, applied ML.
- No end-user GUI. No SaaS. Library + CLI only.
- Self-hostable. No telemetry. Apache-2.0 license.

## Non-goals (do NOT build)

- No web UI of any kind.
- No model finetuning. We do NOT touch weights.
- No real vector store. Local filesystem only.
- No authentication, no multi-tenant.
- No streaming dashboards.
- No provider plugins beyond Anthropic, OpenAI, and Mock in MVP.
- No alternative extractor strategies beyond `reflective` in MVP.

## MVP definition of done

The product is shipped when a fresh checkout supports this flow with **no API key required**:

```bash
pip install -e .
skillforge init demo
cd demo
skillforge run     --provider mock --corpus tasks.yaml --concurrency 4
skillforge extract --run runs/<id> --provider mock --out skills/demo/SKILL.md
skillforge eval    --skill skills/demo/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak
skillforge lint    skills/demo/SKILL.md
```

And, with `ANTHROPIC_API_KEY` set, the same flow works with `--provider anthropic` and `--model claude-opus-4` without code changes.
