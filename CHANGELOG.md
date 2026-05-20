# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0-rc1] - 2026-05-21

### Added

- Iterative extractor strategy (`--strategy iterative --max-rounds N`)
- Multi-pass refinement with convergence detection (early stop on identical output)
- `ITERATIVE_EXTRACTION_MARKER` and `ITERATIVE_REFINEMENT_PROMPT_V1`
- Unit tests for iterative extractor (5 cases)

## [0.2.3] - 2026-05-21

### Added

- `skillforge diff <a> <b>` command for comparing two SKILL.md files
- `skillforge lint --strict` flag (warnings become errors)
- `skillforge eval --format json` output mode
- Integration tests for diff command

## [0.2.2] - 2026-05-21

### Added

- HTML eval report (`--format html`) with inline CSS, SVG sparkline, color-coded table
- Kiro subagent `.kiro/agents/skill-learner.md` for skill extraction workflow
- `docs/extractors.md` — reflective vs contrastive comparison
- `docs/providers.md` — all 5 providers documented

### Changed

- README updated with v0.2 features (doctor, contrastive, provider matrix, bootstrap CI)
- mkdocs nav expanded with Extractors and Providers pages

## [0.2.1] - 2026-05-21

### Added

- Unit tests for contrastive extractor, delta bootstrap, bedrock/gemini providers
- Unit tests for logging module, __main__ entrypoint, CLI error handling
- `PerTaskRow` model replacing untyped dict in DeltaReport

### Changed

- Coverage threshold raised to 90% (actual: 92%+)
- CI workflow now enforces `--cov-fail-under=90`
- Removed `delta.py` from pyright strict exclusion (fully typed now)
- Removed `bedrock.py` and `gemini.py` from coverage omit

## [0.2.0] - 2026-05-20

### Added

- Bootstrap confidence intervals for eval delta (`--bootstrap N --confidence 0.95`)
- `delta_report.json` output with per-task breakdown and CI statistics
- Win/loss/tie breakdown and significance verdict in eval output

## [0.2.0-rc2] - 2026-05-20

### Added

- Bedrock provider (Anthropic Claude via AWS, optional dep: `boto3`)
- Gemini provider (Google Gemini via REST API, optional dep: `google-generativeai`)
- Optional dependency groups: `[bedrock]`, `[gemini]`

## [0.2.0-rc1] - 2026-05-20

### Added

- Contrastive extractor strategy (`--strategy contrastive --strong-run --weak-run`)
- `CONTRASTIVE_EXTRACTION_MARKER` for mock provider detection
- CLI `extract` command now supports `--strategy` choice (reflective/contrastive)

## [0.1.2] - 2026-05-20

### Added

- `skillforge doctor` command for environment diagnostics
- Hypothesis property-based tests for all data models (round-trip preservation)
- `hypothesis>=6.100` dev dependency

### Changed

- Coverage threshold raised to 85% (actual: 92%)

## [0.1.1] - 2026-05-20

### Fixed

- Gate smoke tests behind `RUN_SMOKE=1` env var so `pytest` passes without API keys
- MockProvider now recognizes reflective-extraction prompts and returns valid SKILL.md
- Integration test `test_extract_cli.py` asserts pipeline success (was inverted)
- E2E test uses actual extracted SKILL.md instead of hand-copied fixture
- Removed committed `d-skill-forge-kiro-bundle/` and duplicate root `tasks.md`

## [0.1.0] - 2026-05-20

### Added

- CLI commands: `init`, `run`, `extract`, `eval`, `lint`
- Providers: Anthropic, OpenAI, Mock (deterministic, no API key required)
- Reflective skill extraction from execution traces
- Evaluation framework comparing weak model with/without skill
- SKILL.md linter with structural and secret-detection checks
- Pydantic v2 models for Task, Trace, Skill, and Run artifacts
- Python-debug example corpus (15 tasks)
- Full documentation (quickstart, concepts, architecture, CLI reference)
- CI with GitHub Actions (Python 3.11/3.12 matrix)
- Release workflow building wheels on tag push
