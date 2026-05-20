# d-skill-forge — Kiro build bundle

This bundle contains everything Kiro needs to autonomously build the `d-skill-forge` MVP using its spec workflow and subagent system.

## What you got

```
.kiro/
├── agents/                              # custom subagent definitions
│   ├── scaffolder.md                    # for repo init + release infra
│   ├── python-implementer.md            # for src/skillforge/*.py modules
│   ├── test-author.md                   # for integration + e2e tests
│   └── docs-writer.md                   # for docs/* and README
├── specs/
│   └── d-skill-forge/
│       ├── requirements.md              # user stories + acceptance criteria
│       ├── design.md                    # architecture, sequence diagrams, module contracts
│       └── tasks.md                     # 27 trackable tasks across 7 phases, with explicit deps
└── steering/                            # persistent context for every interaction
    ├── product.md           (always)    # what we're building, MVP definition of done
    ├── tech.md              (always)    # tech stack, pyproject.toml shape, hard style rules
    ├── structure.md         (always)    # canonical repo layout + file ownership
    ├── models-contract.md   (always)    # Pydantic v2 data models — single source of truth
    ├── git-workflow.md      (always)    # branches, commits, PRs, merging
    ├── python-style.md      (*.py)      # imports, typing, docstrings, async discipline
    └── testing-conventions.md (tests/)  # pytest, respx, mock-provider rules, coverage gates
```

## How to deploy

1. **Create a new empty directory** for the project (e.g. `mkdir d-skill-forge && cd d-skill-forge`).
2. **Initialize a git repo**: `git init && git branch -m main`.
3. **Copy the `.kiro/` folder** from this bundle into the repo root.
4. **Open the directory in Kiro IDE** (or attach via Kiro CLI).
5. **Trigger the build** using one of the kickoff prompts below.

## Kickoff prompts

### Option A — fully autonomous (recommended)

Paste this exact prompt into the Kiro chat:

> Read `.kiro/specs/d-skill-forge/requirements.md`, `design.md`, and `tasks.md`. Treat the spec as approved (no further user review). Run all tasks. Use the dependency graph to maximise parallelism. After each wave, run the wave gate (`uv sync --all-extras`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run pyright`, `uv run pytest --cov=skillforge --cov-fail-under=<wave-threshold>`) and only proceed if it passes. Use the custom subagents declared in `.kiro/agents/`. Stop only when Task 7.2 is complete or a gate fails twice with the same root cause; in the failure case, summarise the issue and wait for instructions.

### Option B — wave-by-wave (more control)

For each phase in `tasks.md`, paste:

> Run the tasks in Phase N of `.kiro/specs/d-skill-forge/tasks.md` using subagents in parallel where the dependency graph allows. After all PRs are merged, run the wave gate and report.

## How parallelism works

Kiro's "Run all Tasks" button auto-builds a dependency graph and groups independent tasks into waves. The `tasks.md` in this bundle makes dependencies explicit via `_Depends on: Task X.Y_` annotations and file ownership via `_Owns_`. With the 20-subagent budget you mentioned, the maximum-concurrency wave (Phase 2: models + foundations) runs 6 subagents simultaneously; later waves fan out across 3–6 subagents each.

## Quality gates (between waves)

| Phase | Coverage gate | Lint gate | Type gate |
|---|---|---|---|
| 2 | ≥ 60% | clean | clean |
| 3 | ≥ 70% | clean | clean |
| 4 | ≥ 75% | clean | clean |
| 5 | ≥ 75% | clean | clean |
| 6 | ≥ 80% | clean | clean |
| 7 | ≥ 80% | clean | clean |

The main agent runs these commands between waves and refuses to start the next wave until they all pass.

## How subagents stay out of each other's way

- **File ownership is exclusive per task**. The `_Owns_` annotation lists the exact files a subagent may touch. Two tasks never own the same file.
- **One branch per task**. Subagents commit to `feat/<task-id>-<summary>`.
- **The main agent merges in order**. After all PRs in a wave have green CI, the main agent squash-merges them in deterministic order (by task ID) to avoid race conditions.
- **Subagents can't see specs**. They only see the slice of `design.md` and `models-contract.md` the main agent embeds in their prompt, plus the always-injected steering files.

## Provider keys

The MVP works **without any API key** thanks to the `mock` provider. To run against real providers later, set:

```bash
export ANTHROPIC_API_KEY="..."
export OPENAI_API_KEY="..."
```

The build itself does not need these. Smoke tests gated by `RUN_SMOKE=1` use them.

## Expected output

After the build:

- A GitHub-ready Python repo at the project root with `pyproject.toml`, `src/skillforge/`, `tests/`, `docs/`, `examples/`, CI workflows.
- A passing CI matrix on Python 3.11 and 3.12.
- A working `skillforge` CLI installable via `pip install -e .` or `uv sync`.
- A demo example under `examples/python-debug/` that runs end-to-end against the mock provider.
- An e2e test that exercises `run → extract → eval → lint` on the example.
- A docs site under `site/` built by `mkdocs build --strict`.

## If something fails

The main agent should:

1. Identify the failing task by ID.
2. Inspect the PR diff and CI logs.
3. Either patch the PR via a follow-up commit on the same branch, or re-dispatch the task to a fresh subagent.
4. If a task fails twice with the same root cause, post a summary to the chat and stop.

Common failure modes and where to look:

| Symptom | Likely file | Fix |
|---|---|---|
| `pyright` errors about Pydantic field types | `models/*.py` | Re-read `.kiro/steering/models-contract.md`; do not redefine types. |
| `respx` test failures with "no matching route" | `tests/unit/providers/*.py` | Use the exact URL the provider sends; check `httpx` request structure. |
| `pytest --cov-fail-under` failures | various | Add focused tests to the failing module; never lower the threshold. |
| Merge conflicts | n/a | Means file ownership was violated; investigate which two tasks both touched a file. |

## License

The bundle itself is provided as-is. The repo it builds will ship under Apache-2.0.
