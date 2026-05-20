---
inclusion: fileMatch
fileMatchPattern: ["**/*.py"]
---

# Python style

## Imports

- Standard lib, third-party, then first-party. Blank line between groups. Ruff enforces this.
- Absolute imports only inside `src/skillforge/`. Relative imports only between sibling modules of the same subpackage.
- No `from module import *`.

## Type hints

- Every public function and method has full type hints. Use modern syntax (`list[int]`, `X | None`).
- `Self` from `typing` for fluent APIs.
- For Pydantic models, the model class is the type (no separate TypedDict).
- Forbid `typing.Any` in `src/skillforge/` except in `providers/*` adapter functions that map raw SDK payloads.

## Docstrings

- Module docstring: one-paragraph purpose statement at the top of every `*.py` file.
- Public functions/classes: Google-style with `Args / Returns / Raises`.
- Internal helpers (`_foo`): one-line docstring is enough.

## Errors

- Raise typed errors from `skillforge.errors`.
- `except Exception` is forbidden except at the CLI top level (`cli/main.py`).
- Wrap external library errors at the boundary; never let an `anthropic.APIError` or `openai.APIError` leak above `providers/`.

## Async

- Provider methods are `async def`. Runners orchestrate via `asyncio.gather` with a `Semaphore`.
- The CLI layer calls `asyncio.run(...)` exactly once per command.
- Never mix sync and async in the same function. If you call an async function, the caller is async.

## File templates

Every `*.py` source file starts with:

```python
"""<one-line purpose>."""
from __future__ import annotations
```

## Forbidden

- `print()` outside of `cli/*` modules. Use `logger` or `rich.console`.
- `time.sleep` in async code (use `asyncio.sleep`).
- Catching `BaseException`.
- Mutable default args (`def f(x: list = [])`).
- Reading env vars outside `config.py`.
- Hardcoded model IDs outside `providers/*_prices.py` and `config.py` defaults.
