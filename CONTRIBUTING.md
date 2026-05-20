# Contributing

Thank you for your interest in contributing to d-skill-forge!

## Development Setup

```bash
uv sync --all-extras
uv run pre-commit install
```

## Running Tests

```bash
uv run pytest
```

## Code Quality

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright
```

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — adding or updating tests
- `chore:` — maintenance tasks
- `refactor:` — code change that neither fixes a bug nor adds a feature
