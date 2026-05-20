# d-skill-forge

**Distill procedural skills from frontier model traces into reusable SKILL.md artifacts.**

d-skill-forge captures how strong models (Claude Opus, GPT-5) solve tasks, then extracts that knowledge into a structured markdown file that makes weaker models measurably better at the same domain.

## How it works

```
Task corpus → STRONG MODEL → Traces → REFLECTIVE DISTILL → SKILL.md → WEAK MODEL → Eval delta
```

1. You define a **task corpus** — a YAML file with prompts and expected outcomes
2. A strong model executes the corpus, producing **traces** (full reasoning + tool calls)
3. The same strong model **reflects** on its own traces and distills a **SKILL.md**
4. You **evaluate** the skill by comparing a weak model's performance with and without it

## Quick links

- [Quickstart](quickstart.md) — get running in 2 minutes
- [Concepts](concepts.md) — understand the mental model
- [Architecture](architecture.md) — system design and data flow
- [CLI Reference](reference/cli.md) — all commands and options
- [Python Debug Example](examples/python-debug.md) — a complete worked example
