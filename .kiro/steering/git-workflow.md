---
inclusion: always
---

# Git workflow

## Branches

- `main` is always green (CI passes).
- Subagents commit to feature branches named `feat/<task-id>-<kebab-summary>` — e.g. `feat/3-2-mock-provider`.
- One task → one branch → one PR.

## Commits

- Conventional Commits format. Examples:
  - `feat(providers): add Anthropic provider`
  - `fix(runner): handle per-task exceptions without aborting the run`
  - `test(extractor): cover failed-trace stratification`
  - `chore(ci): bump pyright to 1.1.380`
  - `docs(quickstart): correct mock-provider example`
- Subject line ≤ 72 chars, imperative mood.

## Pull requests

- One PR per task. PR body includes:
  - Link to the task ID (e.g. `Task 3.2`).
  - Link to the requirement IDs (e.g. `Requirements: 2.2.4, 2.7.2`).
  - List of owned files (matches `_Owns_` in `tasks.md`).
  - Verification output excerpt: `ruff`, `pyright`, `pytest` commands and pass/fail.
  - Any `TODO:` items the subagent left for follow-up.

## Merging

- The main agent merges PRs in **deterministic order by task ID** to avoid spurious conflicts.
- Squash-merge only. Never merge-commit, never rebase-merge.
- Never `git push --force` to `main`. `--force-with-lease` is allowed only on feature branches.
- Never amend a published commit.

## Hooks

- `pre-commit install` once at scaffold time.
- Pre-commit hooks must pass before any commit. Never use `--no-verify` to bypass.
