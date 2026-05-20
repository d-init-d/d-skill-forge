# Implementation Plan — d-skill-forge MVP

> Format: Kiro spec tasks. The main agent reads this file and dispatches each task to a subagent.
> Parallel execution: Kiro builds a dependency graph and runs independent tasks concurrently in waves.
> The `_Depends on_` and `_Owns_` annotations make the graph explicit and prevent merge conflicts.
> The `_Requirements_` annotation references sections in `requirements.md`.
> The `_Agent_` annotation tells Kiro which custom subagent (`.kiro/agents/<name>.md`) should pick the task.
>
> **Subagent rule**: Subagents do not have access to specs. The main agent embeds the relevant slice of `design.md` and `models-contract.md` into each subagent invocation. Subagents only touch files listed under `_Owns_`.

---

## Phase 1: Scaffold (single agent, blocks all subsequent waves)

- [x] **Task 1.1**: Initialize repo skeleton, tooling, and CI
  - Create `pyproject.toml` exactly as documented in `.kiro/steering/tech.md`.
  - Create `.python-version` containing `3.11`.
  - Create `.gitignore` (Python defaults + `runs/`, `skills/`, `site/`, `.venv/`, `dist/`, `.coverage`).
  - Create `LICENSE` with the Apache-2.0 text.
  - Create stub `README.md` (≤ 20 lines, replaced later by Task 6.5).
  - Create empty `CHANGELOG.md` and `CONTRIBUTING.md` skeletons.
  - Create `.pre-commit-config.yaml` with hooks: ruff, ruff-format, pyright (fast), pytest (`-q -x` on changed tests only).
  - Create `.github/workflows/ci.yml` exactly as documented in `design.md §8`.
  - Create `mkdocs.yml` with `material` theme and nav placeholders for `index.md`, `quickstart.md`, `concepts.md`, `architecture.md`, `reference/cli.md`.
  - Create the full directory tree under `src/skillforge/` and `tests/` per `.kiro/steering/structure.md`. Every Python directory must contain an `__init__.py` with a module docstring; subdirectories of `tests/` get empty `__init__.py`.
  - Create `src/skillforge/version.py` defining `__version__ = "0.1.0"` and `src/skillforge/__main__.py` calling `from skillforge.cli.main import cli; cli()`.
  - Run `uv sync --all-extras` and commit the resulting `uv.lock`.
  - Run `uv run ruff check src tests` and `uv run pyright` to confirm an empty-but-valid project compiles.
  - _Owns: pyproject.toml, .python-version, .gitignore, LICENSE, README.md (stub), CHANGELOG.md, CONTRIBUTING.md, .pre-commit-config.yaml, .github/workflows/ci.yml, mkdocs.yml, uv.lock, every __init__.py in src/skillforge/ and tests/, src/skillforge/version.py, src/skillforge/__main__.py, tests/conftest.py, tests/fixtures/.gitkeep_
  - _Agent: scaffolder_
  - _Requirements: 2.6.1, 2.6.2, 2.6.5_

---

## Phase 2: Models and foundations (parallel — wave 2)

- [x] **Task 2.1**: Implement Task and TaskCorpus models
  - Implement `src/skillforge/models/task.py` exactly per `.kiro/steering/models-contract.md §task.py`.
  - Add `ExpectedOutcome`, `Task`, `TaskCorpus` with full type hints and module docstring.
  - Add `tests/unit/test_models.py::TestTask*` covering: valid task, missing prompt rejected, `llm_judge` without rubric rejected, weight default = 1.0.
  - _Owns: src/skillforge/models/task.py, tests/unit/test_models.py (TestTask* class only)_
  - _Depends on: Task 1.1_
  - _Agent: python-implementer_
  - _Requirements: NFR-2_

- [ ] **Task 2.2**: Implement Trace models
  - Implement `src/skillforge/models/trace.py` per spec: `ContentBlock`, `Message`, `TokenUsage`, `Score`, `Trace`.
  - Round-trip test: build a `Trace` with mixed content blocks, dump to JSON, load back, assert equality.
  - Verify `schema_version` Literal is enforced.
  - _Owns: src/skillforge/models/trace.py, tests/unit/test_models.py (TestTrace* class only)_
  - _Depends on: Task 1.1_
  - _Agent: python-implementer_
  - _Requirements: NFR-2, 2.2.6_

- [ ] **Task 2.3**: Implement Skill models
  - Implement `src/skillforge/models/skill.py` per spec: `ExtractionStats`, `EvalReport`, `SkillFrontmatter`, `Skill`.
  - Validate kebab-case regex for `SkillFrontmatter.name`.
  - Tests round-trip a full Skill including `eval` list.
  - _Owns: src/skillforge/models/skill.py, tests/unit/test_models.py (TestSkill* class only)_
  - _Depends on: Task 1.1_
  - _Agent: python-implementer_
  - _Requirements: NFR-2, 2.3.1_

- [ ] **Task 2.4**: Implement Run manifest models
  - Implement `src/skillforge/models/run.py`: `TaskResult`, `RunManifest`.
  - `RunManifest` must JSON-serialize `Path` fields using `pydantic.types.Path` validator (string output).
  - Tests cover empty manifest (no results) and a manifest with three task results.
  - _Owns: src/skillforge/models/run.py, tests/unit/test_models.py (TestRunManifest* class only)_
  - _Depends on: Task 1.1_
  - _Agent: python-implementer_
  - _Requirements: NFR-2_

- [ ] **Task 2.5**: Implement typed error hierarchy
  - Implement `src/skillforge/errors.py` with all classes listed in `design.md §3.1`.
  - Add `tests/unit/test_errors.py` asserting `issubclass(AuthError, ProviderError)` etc.
  - _Owns: src/skillforge/errors.py, tests/unit/test_errors.py_
  - _Depends on: Task 1.1_
  - _Agent: python-implementer_
  - _Requirements: 2.2.4_

- [ ] **Task 2.6**: Implement logging and paths utilities
  - Implement `src/skillforge/logging.py`: `get_console()` returning a `rich.console.Console`, `get_logger(name)` returning a stdlib logger configured with a `RichHandler`.
  - Implement `src/skillforge/paths.py`: `ulid()` returning a new ULID string, `now_iso()` returning a UTC ISO-8601 timestamp, `runs_dir(config)` and `skills_dir(config)` helpers.
  - Tests for `ulid()` (length 26, charset), `now_iso()` (regex match).
  - _Owns: src/skillforge/logging.py, src/skillforge/paths.py, tests/unit/test_paths.py_
  - _Depends on: Task 1.1_
  - _Agent: python-implementer_

- [ ] **Task 2.7**: Implement config loader
  - Implement `src/skillforge/config.py`: Pydantic `Config` model, `load_config(path: Path | None = None) -> Config`.
  - Support TOML (default) and YAML.
  - Resolve `api_key_env` references via `os.environ` at access time (lazy property, not at load time, so test fixtures can patch env vars).
  - On missing required env var when a provider is requested at runtime, raise `AuthError` (not at config-load time).
  - Tests: load a valid TOML, load a valid YAML, missing file → `ConfigError`, invalid TOML syntax → `ConfigError`.
  - _Owns: src/skillforge/config.py, tests/unit/test_config.py, tests/fixtures/skillforge_minimal.toml_
  - _Depends on: Task 2.5_
  - _Agent: python-implementer_
  - _Requirements: 2.2.4, 2.6.1_

- [ ] **Task 2.8**: Implement skill IO (read/parse/dump/write)
  - Implement `src/skillforge/skill_io.py`: `parse(text) -> Skill`, `dump(skill) -> str`, `read(path) -> Skill`, `write(skill, path) -> None`.
  - Frontmatter parser uses `yaml.safe_load`; body is everything after the closing `---`.
  - Dump produces deterministic output: sorted YAML keys, LF line endings, trailing newline.
  - Tests: round-trip a Skill, parse a skill with no frontmatter → `SkillFormatError`, parse a skill with malformed frontmatter → `SkillFormatError`.
  - Fixture `tests/fixtures/skill_sample.md` is a 30-line minimal valid SKILL.md.
  - _Owns: src/skillforge/skill_io.py, tests/unit/test_skill_io.py, tests/fixtures/skill_sample.md_
  - _Depends on: Task 2.3, Task 2.5_
  - _Agent: python-implementer_
  - _Requirements: 2.3.1, 2.5.1_

---

## Phase 3: Providers, tasks loader, recorder (parallel — wave 3)

- [ ] **Task 3.1**: Provider base class and registry
  - Implement `src/skillforge/providers/base.py`: `Provider` ABC, `CompletionRequest`, `CompletionResponse` Pydantic models per `design.md §3.3`.
  - Implement `src/skillforge/providers/__init__.py` exposing `PROVIDERS`, `@register(name)`, `get_provider(name) -> Provider`.
  - Tests: register a fake provider, `get_provider` returns it; unknown name → `ProviderError`.
  - _Owns: src/skillforge/providers/base.py, src/skillforge/providers/__init__.py, tests/unit/providers/test_base.py_
  - _Depends on: Task 2.2, Task 2.5_
  - _Agent: python-implementer_

- [ ] **Task 3.2**: Mock provider (always available, network-free)
  - Implement `src/skillforge/providers/mock.py`: register `name = "mock"`.
  - `complete()` is deterministic per `(model, last_user_message)` pair.
  - `model="mock-strong"` returns a 3-step plan + correct answer designed to PASS exact-match / contains evaluators on the standard fixture corpus.
  - `model="mock-weak"` returns a shorter, less-correct answer designed to FAIL more often than `mock-strong` on the same corpus.
  - `estimate_cost` returns `0.0`.
  - Tests: assert `mock-strong` outperforms `mock-weak` on `tests/fixtures/tasks_minimal.yaml` (used by Task 3.5).
  - _Owns: src/skillforge/providers/mock.py, tests/unit/providers/test_mock.py_
  - _Depends on: Task 3.1, Task 3.5_
  - _Agent: python-implementer_
  - _Requirements: 2.7.2_

- [ ] **Task 3.3**: Anthropic provider
  - Implement `src/skillforge/providers/anthropic.py`: register `name = "anthropic"`.
  - Wraps `anthropic.AsyncAnthropic.messages.create`.
  - Maps Anthropic content blocks (`text`, `thinking`, `tool_use`, `tool_result`) to our `ContentBlock`.
  - Pulls `api_key` from `config.providers.anthropic.api_key_env` env var at call time; raises `AuthError` if unset.
  - Implement `src/skillforge/providers/anthropic_prices.py` with a `PRICES: dict[str, ModelPrice]` table for at least `claude-opus-4`, `claude-sonnet-4`, `claude-haiku-4`; `estimate_cost(response)` uses input/output/thinking token counts.
  - Tests use `respx` to mock the Anthropic HTTPS endpoint; assert correct request shape, correct mapping of content blocks, cost calculation.
  - No real network. No `RUN_SMOKE` test in this task.
  - _Owns: src/skillforge/providers/anthropic.py, src/skillforge/providers/anthropic_prices.py, tests/unit/providers/test_anthropic.py_
  - _Depends on: Task 3.1_
  - _Agent: python-implementer_
  - _Requirements: 2.2.4, 2.2.6_

- [ ] **Task 3.4**: OpenAI provider
  - Implement `src/skillforge/providers/openai.py`: register `name = "openai"`.
  - Wraps `openai.AsyncOpenAI` Responses API.
  - Maps `reasoning` items to `ContentBlock(type="thinking")`.
  - Implement `src/skillforge/providers/openai_prices.py` with `PRICES` for at least `gpt-5`, `gpt-5-mini`, `gpt-4o`, `gpt-4o-mini`.
  - Tests with `respx`.
  - _Owns: src/skillforge/providers/openai.py, src/skillforge/providers/openai_prices.py, tests/unit/providers/test_openai.py_
  - _Depends on: Task 3.1_
  - _Agent: python-implementer_
  - _Requirements: 2.2.4, 2.2.6_

- [ ] **Task 3.5**: Tasks corpus loader
  - Implement `src/skillforge/tasks.py`: `load_corpus(path) -> TaskCorpus`, `validate_corpus(corpus) -> list[str]`, `interpolate(task, vars) -> str`.
  - Accept YAML and JSON corpora.
  - `validate_corpus` returns human-readable issues (does not raise).
  - Create `tests/fixtures/tasks_minimal.yaml` with 5 tasks of mixed `ExpectedOutcome.kind` (`exact`, `contains`, `regex`, `executes_ok`, `llm_judge`).
  - Tests: load minimal yaml, duplicate ID detected, missing rubric for `llm_judge` detected, interpolation substitutes `{{ var }}`.
  - _Owns: src/skillforge/tasks.py, tests/unit/test_tasks.py, tests/fixtures/tasks_minimal.yaml_
  - _Depends on: Task 2.1, Task 2.5_
  - _Agent: python-implementer_
  - _Requirements: 2.1.3, 2.7.1_

- [ ] **Task 3.6**: Recorder (run directory + trace JSONL writer)
  - Implement `src/skillforge/recorder.py`: `Recorder` async context manager.
  - `await recorder.record_trace(trace)` appends one JSON line to `traces/<task_id>.jsonl`.
  - `await recorder.finalise(manifest)` writes `manifest.json`.
  - `load_run(run_dir) -> tuple[RunManifest, list[Trace]]` reads everything back.
  - Tests in `tmp_path`: write 3 traces + manifest, read back, assert equality.
  - _Owns: src/skillforge/recorder.py, tests/unit/test_recorder.py_
  - _Depends on: Task 2.2, Task 2.4_
  - _Agent: python-implementer_
  - _Requirements: 2.2.1, 2.2.2_

---

## Phase 4: Runner, extractor, evaluator, lint (parallel — wave 4)

- [ ] **Task 4.1**: Runner — orchestrates corpus execution with bounded concurrency
  - Implement `src/skillforge/runner.py`: `async def run_corpus(corpus, provider, model, *, skill, concurrency, recorder, evaluator) -> RunManifest`.
  - Use `asyncio.Semaphore(concurrency)`.
  - When `skill` is provided, prepend `skill.body` to the system prompt of every task.
  - Per-task exceptions are caught and stored as `Trace.error`; the run continues.
  - Tests: 5-task corpus on mock provider, concurrency=2, no skill: returns valid manifest with 5 results.
  - Tests: same corpus with skill loaded asserts the system prompt prepending logic by inspecting a recorded Trace's messages.
  - _Owns: src/skillforge/runner.py, tests/unit/test_runner.py_
  - _Depends on: Task 3.1, Task 3.2, Task 3.5, Task 3.6_
  - _Agent: python-implementer_
  - _Requirements: 2.2.1, 2.2.2, 2.2.3, 2.2.5_

- [ ] **Task 4.2**: Reflective extractor
  - Implement `src/skillforge/extractor/base.py`: `Extractor` ABC.
  - Implement `src/skillforge/extractor/reflective.py`: `ReflectiveExtractor.extract(manifest, traces, provider, model) -> Skill`.
  - Implement `src/skillforge/extractor/_prompts.py`: `REFLECTIVE_EXTRACTION_PROMPT_V1` template per `design.md §4`.
  - Strategy: stratified sampling capped by `config.extractor.reflective.max_traces_per_pass`, biased toward passed traces but including ≥ 25% failed traces when available.
  - After extraction, parse the model's response via `skill_io.parse`; if parsing fails, raise `ExtractionError`.
  - Tests: feed a fake manifest + traces to a mock provider that returns a valid SKILL.md block; assert extractor returns a `Skill` with correct `extracted_from` counts.
  - _Owns: src/skillforge/extractor/base.py, src/skillforge/extractor/reflective.py, src/skillforge/extractor/_prompts.py, tests/unit/extractor/test_base.py, tests/unit/extractor/test_reflective.py_
  - _Depends on: Task 3.1, Task 3.6, Task 2.8_
  - _Agent: python-implementer_
  - _Requirements: 2.3.1, 2.3.2, 2.3.5_

- [ ] **Task 4.3**: Evaluator suite (exact-match, llm-judge, compare_runs)
  - Implement `src/skillforge/evaluator/base.py`: `Evaluator` ABC.
  - Implement `src/skillforge/evaluator/exact_match.py`: handles `exact`, `regex`, `contains`, `executes_ok` (subprocess with 5 s timeout, no shell, working dir = `tmp_path`).
  - Implement `src/skillforge/evaluator/llm_judge.py`: posts rubric to a judge provider, parses `{passed, score, rationale}` JSON.
  - Implement `src/skillforge/evaluator/runner.py`: `evaluate_run(manifest, corpus)` and `compare_runs(baseline, with_skill)` returning an `EvalDelta`.
  - Tests for each evaluator kind. `executes_ok` test must run a trivial `print('ok')` script.
  - _Owns: src/skillforge/evaluator/base.py, src/skillforge/evaluator/exact_match.py, src/skillforge/evaluator/llm_judge.py, src/skillforge/evaluator/runner.py, tests/unit/evaluator/*.py_
  - _Depends on: Task 3.1, Task 3.2, Task 3.6_
  - _Agent: python-implementer_
  - _Requirements: 2.4.1, 2.4.2, 2.4.4_

- [ ] **Task 4.4**: Skill lint
  - Implement `src/skillforge/lint.py`: `LintIssue` Pydantic model, `lint_skill(skill) -> list[LintIssue]`.
  - Checks: frontmatter fields, required body sections, section size, secret patterns (Anthropic, OpenAI, AWS), at least one `task_id` reference in `## Examples`.
  - Tests cover: valid skill → empty list; missing section → error; secret pattern → error; oversized section → warning.
  - _Owns: src/skillforge/lint.py, tests/unit/test_lint.py_
  - _Depends on: Task 2.3, Task 2.8_
  - _Agent: python-implementer_
  - _Requirements: 2.5.1, 2.5.2, 2.5.3, 2.5.4_

---

## Phase 5: CLI commands (parallel — wave 5)

- [ ] **Task 5.1**: CLI skeleton (root group, error handler, global options)
  - Implement `src/skillforge/cli/__init__.py` (empty exports).
  - Implement `src/skillforge/cli/main.py`: `cli` Click group with `--config`, `-v/--verbose`, `-q/--quiet`; top-level error handler per `design.md §6`.
  - Wire up `console.print` for all user-facing output via `rich`.
  - Tests: `CliRunner` invokes `cli --help`, asserts exit 0 and subcommand list contains `init run extract eval lint` placeholders.
  - _Owns: src/skillforge/cli/__init__.py, src/skillforge/cli/main.py, tests/integration/test_cli_root.py_
  - _Depends on: Task 2.5, Task 2.6, Task 2.7_
  - _Agent: python-implementer_

- [ ] **Task 5.2**: `skillforge init <dir>`
  - Implement `src/skillforge/cli/init.py`.
  - Behaviour matches requirements 2.1.1, 2.1.2, 2.1.3.
  - Embedded template files: a 3-task example `tasks.yaml`, a default `skillforge.toml`.
  - Integration tests: init into `tmp_path`, init into a non-empty dir → exit code 2.
  - Register the command into `cli/main.py` via the existing wiring pattern.
  - _Owns: src/skillforge/cli/init.py, tests/integration/test_init_cli.py_
  - _Depends on: Task 5.1, Task 2.7, Task 3.5_
  - _Agent: python-implementer_
  - _Requirements: 2.1.1, 2.1.2, 2.1.3_

- [ ] **Task 5.3**: `skillforge run`
  - Implement `src/skillforge/cli/run.py`.
  - Wires CLI args to `runner.run_corpus` and `recorder.Recorder`.
  - Behaviour matches requirements 2.2.1 through 2.2.6.
  - Integration test: end-to-end `run` against `--provider mock` on `tasks_minimal.yaml`, asserts `runs/<id>/manifest.json` exists and contains 5 task results.
  - _Owns: src/skillforge/cli/run.py, tests/integration/test_run_cli.py_
  - _Depends on: Task 5.1, Task 4.1, Task 3.6_
  - _Agent: python-implementer_
  - _Requirements: 2.2.1, 2.2.2, 2.2.3, 2.2.4, 2.2.5, 2.2.6_

- [ ] **Task 5.4**: `skillforge extract`
  - Implement `src/skillforge/cli/extract.py`.
  - Behaviour matches requirements 2.3.1 through 2.3.5.
  - Integration test: feed a saved run directory (fixture) into the command and assert a valid SKILL.md is produced at `--out`.
  - _Owns: src/skillforge/cli/extract.py, tests/integration/test_extract_cli.py, tests/fixtures/run_sample/ (manifest + traces)_
  - _Depends on: Task 5.1, Task 4.2_
  - _Agent: python-implementer_
  - _Requirements: 2.3.1, 2.3.2, 2.3.3, 2.3.4, 2.3.5_

- [ ] **Task 5.5**: `skillforge eval`
  - Implement `src/skillforge/cli/eval.py`.
  - Behaviour matches requirements 2.4.1 through 2.4.4.
  - When `--baseline-run` is supplied, skip the baseline pass.
  - Integration test: load `skill_sample.md` + `tasks_minimal.yaml`, run eval against `--weak-model mock-weak`; assert that a delta is printed and that the SKILL.md frontmatter is updated with an `EvalReport`.
  - _Owns: src/skillforge/cli/eval.py, tests/integration/test_eval_cli.py_
  - _Depends on: Task 5.1, Task 5.3, Task 4.3_
  - _Agent: python-implementer_
  - _Requirements: 2.4.1, 2.4.2, 2.4.3, 2.4.4_

- [ ] **Task 5.6**: `skillforge lint`
  - Implement `src/skillforge/cli/lint.py`.
  - Behaviour matches requirements 2.5.1 through 2.5.4.
  - Exit code 0 if no errors, 1 if any error-severity issues, 2 if file unreadable.
  - Integration test: lint `skill_sample.md` → exit 0; lint a malformed fixture → non-zero with `LintIssue` printed.
  - _Owns: src/skillforge/cli/lint.py, tests/integration/test_lint_cli.py_
  - _Depends on: Task 5.1, Task 4.4_
  - _Agent: python-implementer_
  - _Requirements: 2.5.1, 2.5.2, 2.5.3, 2.5.4_

---

## Phase 6: Example, end-to-end, docs (parallel — wave 6)

- [ ] **Task 6.1**: Python-debug example corpus and expected skill
  - Create `examples/python-debug/tasks.yaml` with ≥ 15 tasks covering: `TypeError`, `AttributeError`, `KeyError`, `IndexError`, `ImportError`, `ValueError`, async misuse, off-by-one, mutable default args.
  - Each task uses `ExpectedOutcome.kind = "executes_ok"` with a small Python snippet whose fix is what the model must produce.
  - Create `examples/python-debug/README.md` with copy-pasteable quickstart commands.
  - Create `examples/python-debug/expected_skill/SKILL.md` showing the shape of a high-quality output skill (hand-authored, used as a reference, not asserted byte-for-byte).
  - _Owns: examples/python-debug/tasks.yaml, examples/python-debug/README.md, examples/python-debug/expected_skill/SKILL.md_
  - _Depends on: Task 3.5_
  - _Agent: python-implementer_
  - _Requirements: 2.7.1_

- [ ] **Task 6.2**: End-to-end test on the python-debug example
  - Implement `tests/e2e/test_python_debug_example.py`.
  - Invokes `cli` four times via `CliRunner`: `run` → `extract` → `eval` → `lint`, all with `--provider mock`.
  - Asserts each step succeeds with exit 0 and produces the expected artifacts (manifest, SKILL.md, eval delta, lint OK).
  - _Owns: tests/e2e/test_python_debug_example.py_
  - _Depends on: Task 5.2, Task 5.3, Task 5.4, Task 5.5, Task 5.6, Task 6.1_
  - _Agent: test-author_
  - _Requirements: 2.7.2, 2.7.3_

- [ ] **Task 6.3**: User-facing docs (concepts, quickstart, index)
  - Create `docs/index.md`, `docs/quickstart.md`, `docs/concepts.md` per `mkdocs.yml` nav.
  - Quickstart is the exact 4-command flow from `.kiro/steering/product.md §MVP`.
  - Concepts page explains: trace, corpus, reflective extraction, skill format, eval delta.
  - _Owns: docs/index.md, docs/quickstart.md, docs/concepts.md_
  - _Depends on: Task 1.1_
  - _Agent: docs-writer_

- [ ] **Task 6.4**: Architecture and CLI reference docs
  - Create `docs/architecture.md` with the Mermaid diagrams from `design.md §1 and §2`.
  - Create `docs/reference/cli.md` using `mkdocs-click` to autogenerate the CLI reference from the Click group `skillforge.cli.main:cli`.
  - Create `docs/reference/api.md` with a curated public API reference.
  - Ensure `uv run mkdocs build --strict` succeeds.
  - _Owns: docs/architecture.md, docs/reference/cli.md, docs/reference/api.md_
  - _Depends on: Task 5.1, Task 5.2, Task 5.3, Task 5.4, Task 5.5, Task 5.6_
  - _Agent: docs-writer_
  - _Requirements: 2.6.5_

- [ ] **Task 6.5**: Final README rewrite
  - Replace stub `README.md` with the production version: badges, one-paragraph elevator pitch, install (`pip` + `uv`), 4-command quickstart, link to docs, link to example, license note.
  - _Owns: README.md_
  - _Depends on: Task 6.1, Task 6.3, Task 6.4_
  - _Agent: docs-writer_

---

## Phase 7: Release prep (small, sequential — wave 7)

- [ ] **Task 7.1**: Smoke tests, release workflow, CHANGELOG
  - Add `tests/smoke/test_anthropic_smoke.py` and `tests/smoke/test_openai_smoke.py` marked `@pytest.mark.smoke`. Tests hit the real provider with a single 1-token request and assert no exception. Skipped by default; ran in CI only when `RUN_SMOKE=1`.
  - Add `.github/workflows/release.yml` building wheels on tag push. Do **not** publish to PyPI in MVP.
  - Populate `CHANGELOG.md` with `## [0.1.0] - <today>` and the user-visible features list.
  - _Owns: tests/smoke/test_anthropic_smoke.py, tests/smoke/test_openai_smoke.py, .github/workflows/release.yml, CHANGELOG.md_
  - _Depends on: Task 6.2, Task 6.4, Task 6.5_
  - _Agent: scaffolder_

- [ ] **Task 7.2**: Final lint and coverage sweep
  - Run `uv run ruff check . --fix` and `uv run ruff format .`.
  - Run `uv run pyright`. Fix any remaining errors.
  - Run `uv run pytest --cov=skillforge --cov-fail-under=80`.
  - If coverage is short, add focused unit tests; do not loosen the threshold.
  - Ensure `mkdocs build --strict` is green.
  - Tag the release commit `v0.1.0`.
  - _Owns: any tests/ files added to lift coverage; no source code changes allowed in this task_
  - _Depends on: Task 7.1_
  - _Agent: scaffolder_
  - _Requirements: 2.6.3, 2.6.4_

---

## Wave summary (for Kiro's "Run all Tasks" dependency planner)

| Wave | Tasks | Concurrency hint |
|---|---|---|
| 1 | 1.1 | 1 |
| 2 | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 | up to 6 in parallel |
| 2b | 2.7, 2.8 | up to 2 in parallel (depend on 2.5 / 2.3) |
| 3 | 3.1, 3.5, 3.6 | up to 3 |
| 3b | 3.2, 3.3, 3.4 | up to 3 (depend on 3.1) |
| 4 | 4.1, 4.2, 4.3, 4.4 | up to 4 |
| 5 | 5.1 → then 5.2…5.6 | 5.2-5.6 up to 5 in parallel after 5.1 |
| 6 | 6.1, 6.3 | 2 parallel |
| 6b | 6.2, 6.4, 6.5 | 3 parallel |
| 7 | 7.1 → 7.2 | sequential |

Maximum parallelism reached in Phase 2/3 (~6 subagents). Kiro will use as many of the available 20 subagent slots as the DAG allows.

## Wave gates (the main agent must run these between waves)

```
uv sync --all-extras
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright
uv run pytest --cov=skillforge --cov-fail-under=<wave-threshold>
```

Wave coverage thresholds: W2 60, W3 70, W4 75, W5 75, W6 80, W7 80.
