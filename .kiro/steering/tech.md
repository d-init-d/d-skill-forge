---
inclusion: always
---

# Tech stack and conventions

## Language and tooling

| Concern | Choice | Notes |
|---|---|---|
| Python | **3.11+** | Use `match`, `Self`, `tomllib`, structural pattern matching. |
| Env & build | **`uv`** | `uv venv`, `uv sync`, `uv add`, `uv build`. Lockfile is `uv.lock` and is committed. |
| Layout | **`src/skillforge/`** | Src-layout, not flat. |
| CLI framework | **Click 8** | Not Typer. Use `@click.group()` and `@click.command()`. |
| Data models | **Pydantic v2** | All persisted artifacts (Task, Trace, Skill, Run) are Pydantic models. |
| HTTP | **httpx** | Async-capable. |
| Terminal output | **Rich** | Tables, progress bars, JSON pretty-print. |
| Lint + format | **Ruff** (latest) | Line length 100. `select = ["E","F","I","B","UP","SIM","RUF","TCH","PL","D"]`. |
| Type check | **Pyright** | `strict = true`; no `Any`, no `# type: ignore` without a reason comment. |
| Tests | **pytest** | Plugins: `pytest-asyncio`, `pytest-cov`, `pytest-mock`, `respx` (HTTP mocks). |
| Pre-commit | **pre-commit** | Hooks: ruff, ruff-format, pyright, fast pytest. |
| CI | **GitHub Actions** | Matrix 3.11 / 3.12 on ubuntu-latest. |
| Versioning | **SemVer**, start at `0.1.0` | `CHANGELOG.md` follows Keep-a-Changelog. |
| Commits | **Conventional Commits** | `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`. |

## License

Apache-2.0. The `LICENSE` file lives at repo root.

## Project metadata in `pyproject.toml`

```toml
[project]
name = "d-skill-forge"
version = "0.1.0"
description = "Distill procedural skills from frontier model traces into reusable SKILL.md artifacts."
authors = [{ name = "d-init-d" }]
license = "Apache-2.0"
requires-python = ">=3.11"
readme = "README.md"
dependencies = [
  "click>=8.1",
  "pydantic>=2.7",
  "httpx>=0.27",
  "anthropic>=0.39",
  "openai>=1.50",
  "rich>=13.7",
  "pyyaml>=6.0",
  "ulid-py>=1.1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5.0",
  "pytest-mock>=3.14",
  "respx>=0.21",
  "ruff>=0.6",
  "pyright>=1.1.380",
  "pre-commit>=3.8",
  "mkdocs-material>=9.5",
  "mkdocs-click>=0.8",
]

[project.scripts]
skillforge = "skillforge.cli.main:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF", "TCH", "PL", "D"]
ignore = ["D203", "D213", "PLR0913"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.pyright]
include = ["src"]
strict = ["src"]
pythonVersion = "3.11"

[tool.pytest.ini_options]
addopts = "-ra --strict-markers --strict-config"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
  "smoke: hits real provider APIs; skipped unless RUN_SMOKE=1.",
]
```

## Style rules (hard)

- Type hints on **every public function and method**. No `Any` outside provider-internal raw adapters.
- All public modules have a module docstring describing purpose and one-line usage.
- Public functions have docstrings with `Args / Returns / Raises` sections.
- No business logic at import time. Side effects live only in CLI entry points.
- No global mutable state. Pass objects.
- No bare `print()` outside CLI commands. Use a `rich.Console` injected via context.
- No hardcoded provider names or model IDs in core logic — everything is config-driven.
- Errors are typed (`skillforge.errors`). Broad `except` only at the CLI boundary.

## Forbidden patterns

- `yaml.load` → use `yaml.safe_load`.
- Vendored secrets or fake-looking API keys in fixtures.
- Real network calls in unit tests — use `respx`. Smoke tests live behind the `smoke` marker.
- Circular imports between `cli`, `runner`, `extractor`, and `providers`.
- Modifying `pyproject.toml` or `uv.lock` outside of scaffold tasks.
