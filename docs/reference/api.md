# API Reference

Public Python API for programmatic use.

## Models

### `skillforge.models.task`

- `Task` — single task definition with prompt and expected outcome
- `TaskCorpus` — collection of tasks with metadata
- `ExpectedOutcome` — evaluation criteria (exact, regex, contains, executes_ok, llm_judge)

### `skillforge.models.trace`

- `Trace` — complete execution record (messages, usage, score, timing)
- `Message` — single message in a conversation
- `ContentBlock` — text, thinking, tool_use, or tool_result block
- `Score` — evaluation result (passed, score, rationale)

### `skillforge.models.skill`

- `Skill` — frontmatter + markdown body
- `SkillFrontmatter` — metadata (name, description, source_model, extraction stats)
- `EvalReport` — evaluation result appended after `skillforge eval`

### `skillforge.models.run`

- `RunManifest` — run metadata and task results
- `TaskResult` — per-task outcome (task_id, passed, score, trace_path)

## Core functions

### `skillforge.tasks`

- `load_corpus(path) -> TaskCorpus` — load and validate a YAML/JSON corpus
- `validate_corpus(corpus) -> list[str]` — check for logical issues

### `skillforge.skill_io`

- `read(path) -> Skill` — read a SKILL.md from disk
- `write(skill, path)` — write a Skill to disk
- `parse(text) -> Skill` — parse SKILL.md text
- `dump(skill) -> str` — serialize a Skill to text

### `skillforge.runner`

- `run_corpus(corpus, provider, model, ...) -> RunManifest` — execute a corpus (async)

### `skillforge.recorder`

- `Recorder` — async context manager for writing traces
- `load_run(run_dir) -> (RunManifest, list[Trace])` — read a run from disk

### `skillforge.providers`

- `get_provider(name) -> type[Provider]` — look up a registered provider
- `PROVIDERS` — registry of available providers

### `skillforge.lint`

- `lint_skill(skill) -> list[LintIssue]` — validate a Skill artifact
