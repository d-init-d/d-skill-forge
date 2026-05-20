# Requirements — d-skill-forge MVP

## 1. Vision

Build a professional Python CLI tool that distills procedural skills from frontier model traces into reusable `SKILL.md` artifacts that measurably improve weaker models when loaded into their context.

## 2. User stories and acceptance criteria

Acceptance criteria use EARS-style: **WHEN** \<condition\>, **THE** system **SHALL** \<action\>.

---

### 2.1 As an AI engineer, I want to scaffold a fresh project so I can start curating tasks immediately.

**Acceptance criteria**

- 2.1.1 — WHEN the user runs `skillforge init <dir>` in an empty directory, THE system SHALL create `<dir>/skillforge.toml`, `<dir>/tasks.yaml` (with a 3-task example), and `<dir>/skills/` (empty).
- 2.1.2 — WHEN `<dir>` already exists and is non-empty, THE system SHALL exit with code 2 and print a friendly error, without overwriting any file.
- 2.1.3 — WHEN `skillforge init` completes, THE generated `tasks.yaml` SHALL validate against the `TaskCorpus` model and the generated `skillforge.toml` SHALL load via `skillforge.config.load_config`.

---

### 2.2 As an AI engineer, I want to execute a corpus against a strong model and capture full traces.

**Acceptance criteria**

- 2.2.1 — WHEN the user runs `skillforge run --corpus tasks.yaml --provider mock`, THE system SHALL produce a `runs/<run_id>/` directory containing `manifest.json` and one `traces/<task_id>.jsonl` file per task.
- 2.2.2 — WHEN any task raises an error, THE system SHALL record a `Trace` with the `error` field set and SHALL continue executing remaining tasks.
- 2.2.3 — WHEN `--concurrency N` is supplied, THE runner SHALL execute up to N tasks in parallel via `asyncio.Semaphore`.
- 2.2.4 — WHEN `--provider anthropic` is supplied without `ANTHROPIC_API_KEY` set, THE system SHALL exit with code 3 and a typed `AuthError`.
- 2.2.5 — WHEN `--skill <path>` is supplied, THE runner SHALL prepend the skill body to the system prompt of every task.
- 2.2.6 — EVERY recorded `Trace` SHALL include `messages`, `final_output`, `latency_ms`, `provider`, `model`, and a `cost_usd` value if cost is computable for that provider.

---

### 2.3 As an AI engineer, I want to distill a run into a reusable SKILL.md.

**Acceptance criteria**

- 2.3.1 — WHEN the user runs `skillforge extract --run <dir> --provider mock --out skills/foo/SKILL.md`, THE system SHALL produce a valid SKILL.md whose frontmatter validates against `SkillFrontmatter`.
- 2.3.2 — THE extractor SHALL emit a body that contains at minimum the markdown sections: `## When to use`, `## Procedure`, `## Examples`, `## Anti-patterns`.
- 2.3.3 — THE extractor SHALL record its own distillation call into `runs/<run_id>/extraction.jsonl`.
- 2.3.4 — WHEN no traces exist in `<dir>`, THE system SHALL exit with code 2 and a typed `ExtractionError`.
- 2.3.5 — THE produced frontmatter's `extracted_from` field SHALL accurately reflect the count of passed and failed traces in the source run.

---

### 2.4 As an AI engineer, I want to evaluate the benefit of a skill on a weaker model.

**Acceptance criteria**

- 2.4.1 — WHEN the user runs `skillforge eval --skill <path> --corpus tasks.yaml --provider mock --weak-model mock-weak`, THE system SHALL run the corpus twice (with and without the skill) and SHALL print a delta table to stdout.
- 2.4.2 — THE eval command SHALL append an `EvalReport` entry to the SKILL.md frontmatter's `eval` list and rewrite the file.
- 2.4.3 — WHEN `--baseline-run <dir>` is supplied, THE eval command SHALL skip the baseline run and use traces from `<dir>` instead.
- 2.4.4 — THE eval report SHALL contain at least: `target_model`, `baseline_score`, `with_skill_score`, `delta`, `tasks_evaluated`, `timestamp`.

---

### 2.5 As an AI engineer, I want to validate SKILL.md format before publishing.

**Acceptance criteria**

- 2.5.1 — WHEN the user runs `skillforge lint <path>` on a valid SKILL.md, THE system SHALL exit with code 0 and print "OK".
- 2.5.2 — WHEN the file is missing a required frontmatter field, THE system SHALL exit non-zero and print one `LintIssue` per missing field.
- 2.5.3 — WHEN the body is missing a required section heading (`## When to use`, `## Procedure`, `## Examples`, `## Anti-patterns`), THE system SHALL emit a `LintIssue` of severity `error`.
- 2.5.4 — WHEN the body contains a string that matches a known secret pattern (Anthropic key, OpenAI key, AWS access key), THE system SHALL emit a `LintIssue` of severity `error`.

---

### 2.6 As an open-source maintainer, I want the project to be installable and CI-clean.

**Acceptance criteria**

- 2.6.1 — WHEN a developer runs `uv sync` on a fresh checkout with Python 3.11 or 3.12, THE installation SHALL succeed.
- 2.6.2 — WHEN GitHub Actions runs the CI workflow, THE matrix SHALL include Python 3.11 and 3.12 and SHALL run `ruff check`, `ruff format --check`, `pyright`, and `pytest --cov`.
- 2.6.3 — `pyright` with strict mode SHALL report zero errors on `src/`.
- 2.6.4 — Line coverage on `src/skillforge/` SHALL be ≥ 80% in the final wave.
- 2.6.5 — THE repo SHALL ship with `mkdocs build --strict` passing.

---

### 2.7 As a downstream user, I want a working example I can copy.

**Acceptance criteria**

- 2.7.1 — THE repo SHALL ship an `examples/python-debug/` directory with ≥ 15 tasks in `tasks.yaml`, an `expected_skill/SKILL.md`, and a `README.md` explaining the flow.
- 2.7.2 — WHEN a developer runs the full pipeline (`run` → `extract` → `eval` → `lint`) on the example using `--provider mock`, THE pipeline SHALL succeed end-to-end without API keys.
- 2.7.3 — THE e2e test `tests/e2e/test_python_debug_example.py` SHALL exercise the full pipeline on every CI run.

---

## 3. Non-functional requirements

- **NFR-1** Python 3.11+ only. No Python 2 compatibility, no Python 3.10 support.
- **NFR-2** All persisted artifacts are valid JSON / YAML and round-trip through Pydantic v2 models with `model_validate` / `model_dump_json`.
- **NFR-3** No network calls inside unit tests. Integration tests use the `mock` provider. Real-network tests are gated by `pytest -m smoke` + `RUN_SMOKE=1`.
- **NFR-4** No secret value SHALL appear in committed files, including fixtures. References use env-var indirection (`${ANTHROPIC_API_KEY}`).
- **NFR-5** Apache-2.0 license. `LICENSE` file at repo root.
- **NFR-6** SemVer. Initial release is `0.1.0`.

## 4. Out of scope (deferred to v0.2+)

- Extractor strategies other than `reflective` (e.g. `contrastive`, `pattern-mine`).
- Provider plugins beyond Anthropic, OpenAI, and Mock (e.g. Bedrock, Gemini, Mistral, OpenRouter).
- Any web UI.
- Vector store or RAG retrieval.
- Fine-tuning dataset export.
- Multi-tenant or authentication.
- Streaming terminal dashboards.
