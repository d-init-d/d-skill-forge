---
inclusion: always
---

# Repository structure and file ownership

The repo layout below is **canonical**. Tasks in `.kiro/specs/d-skill-forge/tasks.md` reference these paths.

When subagents work in parallel, each task **owns** an exclusive set of files. Two tasks never own the same file. This rule is what makes parallel execution conflict-free.

```
d-skill-forge/
├── .github/workflows/{ci,release}.yml
├── .pre-commit-config.yaml
├── .gitignore
├── .python-version
├── LICENSE                          # Apache-2.0
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── uv.lock
├── mkdocs.yml
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   ├── concepts.md
│   ├── architecture.md
│   ├── reference/{cli,api}.md
│   └── examples/python-debug.md
├── examples/
│   └── python-debug/
│       ├── tasks.yaml
│       ├── README.md
│       └── expected_skill/SKILL.md
├── src/
│   └── skillforge/
│       ├── __init__.py
│       ├── __main__.py
│       ├── version.py
│       ├── errors.py
│       ├── logging.py
│       ├── paths.py
│       ├── config.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── task.py
│       │   ├── trace.py
│       │   ├── skill.py
│       │   └── run.py
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── anthropic.py
│       │   ├── anthropic_prices.py
│       │   ├── openai.py
│       │   ├── openai_prices.py
│       │   └── mock.py
│       ├── tasks.py
│       ├── recorder.py
│       ├── runner.py
│       ├── extractor/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── reflective.py
│       │   └── _prompts.py
│       ├── evaluator/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── exact_match.py
│       │   ├── llm_judge.py
│       │   └── runner.py
│       ├── skill_io.py
│       ├── lint.py
│       └── cli/
│           ├── __init__.py
│           ├── main.py
│           ├── init.py
│           ├── run.py
│           ├── extract.py
│           ├── eval.py
│           └── lint.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── tasks_minimal.yaml
    │   ├── trace_sample.jsonl
    │   └── skill_sample.md
    ├── unit/
    │   ├── test_models.py
    │   ├── test_errors.py
    │   ├── test_config.py
    │   ├── test_tasks.py
    │   ├── test_recorder.py
    │   ├── test_skill_io.py
    │   ├── test_lint.py
    │   ├── providers/{test_base,test_mock,test_anthropic,test_openai}.py
    │   ├── extractor/{test_base,test_reflective}.py
    │   └── evaluator/{test_base,test_exact_match,test_llm_judge,test_runner}.py
    ├── integration/
    │   ├── test_run_cli.py
    │   ├── test_extract_cli.py
    │   ├── test_eval_cli.py
    │   └── test_full_pipeline.py
    └── e2e/
        └── test_python_debug_example.py
```

## Module boundaries (hard rules)

- `providers/*` must **not** import from `cli`, `runner`, `extractor`, `evaluator`.
- `models/*` must **not** import anything from `skillforge` except other `models`.
- `cli/*` is the only place that calls `asyncio.run`.
- Side effects (filesystem writes, HTTP calls) happen below the CLI layer, never inside `models` or `errors`.

## File ownership matrix

For any task that creates or modifies code, the task description in `tasks.md` lists "Owns" paths. Subagents must not touch any path outside their owned list. If they think they need to, they post a comment on the spec and stop.
