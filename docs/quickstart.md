# Quickstart

Get a full skill distillation pipeline running in under 2 minutes.

## Install

```bash
pip install d-skill-forge
```

Or with uv:

```bash
uv add d-skill-forge
```

## Run the pipeline (no API key required)

```bash
# 1. Scaffold a project
skillforge init demo
cd demo

# 2. Execute the task corpus
skillforge run --provider mock --corpus tasks.yaml

# 3. Extract a skill from the traces
skillforge extract --run runs/<run_id> --provider mock --out skills/demo/SKILL.md

# 4. Evaluate the skill
skillforge eval --skill skills/demo/SKILL.md --corpus tasks.yaml --provider mock --weak-model mock-weak

# 5. Lint the result
skillforge lint skills/demo/SKILL.md
```

## With a real provider

Set your API key and swap `--provider`:

```bash
export ANTHROPIC_API_KEY=sk-ant-...

skillforge run --provider anthropic --model claude-opus-4 --corpus tasks.yaml
skillforge extract --run runs/<id> --provider anthropic --model claude-opus-4
skillforge eval --skill skills/demo/SKILL.md --corpus tasks.yaml --provider anthropic --weak-model claude-haiku-4
```

## Next steps

- Read [Concepts](concepts.md) to understand traces, extraction, and evaluation
- Try the [Python Debug Example](examples/python-debug.md) for a real-world corpus
- See the [CLI Reference](reference/cli.md) for all options
