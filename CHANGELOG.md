# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
