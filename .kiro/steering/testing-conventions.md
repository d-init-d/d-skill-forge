---
inclusion: fileMatch
fileMatchPattern: ["tests/**/*.py"]
---

# Testing conventions

## Framework

- `pytest` with `pytest-asyncio` (async mode = "auto").
- `respx` for HTTP-level mocking of `httpx`.
- `pytest-mock` for in-process patching.
- `pytest-cov` for coverage.

## File layout

- Unit tests mirror source modules: `src/skillforge/foo/bar.py` → `tests/unit/foo/test_bar.py`.
- Integration tests live in `tests/integration/`. They exercise CLI commands via `click.testing.CliRunner`.
- End-to-end tests live in `tests/e2e/` and run the full pipeline against the `mock` provider.

## Mock provider rule

Every test that needs a provider uses `providers.mock.MockProvider`. Tests that require real network use the `@pytest.mark.smoke` marker and are skipped unless `RUN_SMOKE=1` is set.

## Determinism

- All tests are deterministic. No `random`, no real clocks.
- Fix datetimes via `freezegun` or by injecting a clock callable.
- Use `tmp_path` from pytest for filesystem isolation.

## Fixture rules

- Shared fixtures in `tests/conftest.py`.
- Per-module fixtures in `tests/<area>/conftest.py`.
- Fixtures that build Pydantic objects use the `_factory_` naming pattern: `task_factory`, `trace_factory`, `skill_factory`.

## Coverage targets per wave (gate-blocking)

- After Wave 1: ≥ 60% line coverage on `src/skillforge/`.
- After Wave 2: ≥ 70%.
- After Wave 3: ≥ 75%.
- After Wave 4 and Wave 5: ≥ 80%.

## Forbidden in tests

- Real network calls (without `smoke` marker).
- Reading env vars (use `monkeypatch.setenv`).
- Sleeping for more than 100 ms.
- Asserting on exception strings — assert on exception type only.
