"""CLI command: skillforge init — scaffold a new project directory."""

from __future__ import annotations

import sys
from pathlib import Path

import click

_TOML_TEMPLATE = """\
[project]
default_provider = "mock"
default_model = "mock-strong"
concurrency = 8

[providers.mock]

[providers.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
default_model = "claude-opus-4"

[providers.openai]
api_key_env = "OPENAI_API_KEY"
default_model = "gpt-4o"
"""

_TASKS_TEMPLATE = """\
version: 1
name: "example-corpus"
description: "Example task corpus for testing."
domain: "general"
tasks:
  - id: "task-math"
    prompt: "What is 2 + 2?"
    expected:
      kind: "exact"
      value: "4"
    tags: ["math"]

  - id: "task-explain"
    prompt: "Explain recursion briefly."
    expected:
      kind: "contains"
      value: "function"
    tags: ["explanation"]

  - id: "task-email"
    prompt: "Generate a valid email address."
    expected:
      kind: "regex"
      value: "^[\\\\w.+-]+@[\\\\w-]+\\\\.[a-zA-Z]{2,}$"
    tags: ["generation"]
"""


@click.command("init")
@click.argument("directory", type=click.Path())
@click.pass_context
def init_cmd(ctx: click.Context, directory: str) -> None:
    """Scaffold a new skillforge project directory.

    Args:
        ctx: Click context.
        directory: Target directory to create.
    """
    console = ctx.obj["console"]
    target = Path(directory)

    if target.exists() and any(target.iterdir()):
        console.print(f"[red]Error:[/red] Directory '{target}' exists and is non-empty.")
        ctx.exit(2)
        sys.exit(2)

    target.mkdir(parents=True, exist_ok=True)
    (target / "skillforge.toml").write_text(_TOML_TEMPLATE, encoding="utf-8")
    (target / "tasks.yaml").write_text(_TASKS_TEMPLATE, encoding="utf-8")
    (target / "skills").mkdir(exist_ok=True)

    console.print(f"[green]✓[/green] Initialized project in [bold]{target}[/bold]")
