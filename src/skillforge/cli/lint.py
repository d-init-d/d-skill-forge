"""CLI command: skillforge lint — validate a SKILL.md file."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from skillforge.errors import SkillFormatError
from skillforge.lint import lint_skill
from skillforge.skill_io import read as read_skill


@click.command("lint")
@click.argument("path", type=click.Path())
@click.pass_context
def lint_cmd(ctx: click.Context, path: str) -> None:
    """Lint a SKILL.md file for structural and content issues.

    Args:
        ctx: Click context.
        path: Path to the SKILL.md file.
    """
    console = ctx.obj["console"]
    skill_path = Path(path)

    if not skill_path.exists():
        console.print(f"[red]Error:[/red] File not found: {skill_path}")
        ctx.exit(2)
        sys.exit(2)

    try:
        skill = read_skill(skill_path)
    except SkillFormatError as e:
        console.print(f"[red]Error:[/red] Cannot parse {skill_path}: {e}")
        ctx.exit(2)
        sys.exit(2)

    issues = lint_skill(skill)

    if not issues:
        console.print("[green]OK[/green]")
        return

    has_errors = False
    for issue in issues:
        loc = f" ({issue.location})" if issue.location else ""
        if issue.severity == "error":
            has_errors = True
            console.print(f"[red]ERROR[/red]{loc}: {issue.message}")
        else:
            console.print(f"[yellow]WARN[/yellow]{loc}: {issue.message}")

    if has_errors:
        ctx.exit(1)
        sys.exit(1)
