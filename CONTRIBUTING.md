# Contributing to d-skill-forge

## Development Setup

```bash
git clone https://github.com/d-init-d/d-skill-forge.git
cd d-skill-forge
uv sync --all-extras
uv run pre-commit install
```

## Running Tests

```bash
uv run pytest
uv run pytest --cov=skillforge --cov-fail-under=90
```

Coverage threshold is **90%**. PRs that drop coverage below this will not be merged.

## Code Style

We use **ruff** for linting/formatting and **pyright** in strict mode:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright
```

All code must pass these checks before merge.

## Smoke Tests

Smoke tests hit real provider APIs and are skipped by default:

```bash
RUN_SMOKE=1 uv run pytest -m smoke
```

You need valid API keys in your environment to run these.

## Anti-Cheating Policy

Mock providers must not be tuned to pass eval benchmarks artificially. Skills extracted using mock providers are for development/testing workflow only and must not be presented as real performance results.

## Adding a New Provider

1. Create `src/skillforge/providers/<name>.py` implementing the `Provider` protocol.
2. Register it in `src/skillforge/providers/__init__.py`.
3. Add smoke tests in `tests/smoke/test_<name>.py`.
4. Document required env vars in `docs/providers.md` and the README provider matrix.

## Adding a New Extractor Strategy

1. Create `src/skillforge/extractors/<name>.py` implementing the `Extractor` protocol.
2. Register it in `src/skillforge/extractors/__init__.py`.
3. Add unit tests in `tests/unit/test_extractor_<name>.py`.
4. Document usage in `docs/extractors.md`.

## PR Process

1. Fork the repo and create a branch from `main`.
2. Make your changes with tests.
3. Ensure `uv run pytest` and `uv run pyright` pass.
4. Add a CHANGELOG.md entry under `## Unreleased`.
5. Open a PR using the pull request template.
6. Address review feedback.

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — adding or updating tests
- `chore:` — maintenance tasks
- `refactor:` — code change that neither fixes a bug nor adds a feature
