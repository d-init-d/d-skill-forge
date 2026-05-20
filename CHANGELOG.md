# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
