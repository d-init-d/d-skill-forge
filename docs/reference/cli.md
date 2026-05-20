# CLI Reference

::: mkdocs-click
    :module: skillforge.cli.main
    :command: cli
    :prog_name: skillforge
    :depth: 1

## Commands

### `skillforge init <directory>`

Scaffold a new project with `skillforge.toml`, `tasks.yaml`, and `skills/` directory.

**Exit codes:** 0 success, 2 if directory is non-empty.

### `skillforge run`

Execute a task corpus against a provider and record traces.

| Option | Description |
|---|---|
| `--corpus PATH` | Path to tasks.yaml (required) |
| `--provider TEXT` | Provider name (default: from config) |
| `--model TEXT` | Model identifier (default: from config) |
| `--concurrency INT` | Max parallel tasks (default: 8) |
| `--skill PATH` | Optional SKILL.md to load into system prompt |

### `skillforge extract`

Distill recorded traces into a SKILL.md artifact.

| Option | Description |
|---|---|
| `--run PATH` | Path to run directory (required) |
| `--provider TEXT` | Provider for extraction (default: mock) |
| `--model TEXT` | Model for extraction (default: mock-strong) |
| `--out PATH` | Output path for SKILL.md |

### `skillforge eval`

Compare weak model performance with and without a skill.

| Option | Description |
|---|---|
| `--skill PATH` | Path to SKILL.md (required) |
| `--corpus PATH` | Path to tasks.yaml (required) |
| `--provider TEXT` | Provider name (default: mock) |
| `--weak-model TEXT` | Weak model identifier (default: mock-weak) |
| `--baseline-run PATH` | Skip baseline run, use existing |

### `skillforge lint <path>`

Validate a SKILL.md file for structural and content issues.

**Exit codes:** 0 clean, 1 errors found, 2 file unreadable.
