"""CLI command: skillforge diff — compare two SKILL.md files."""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

import click

from skillforge.skill_io import read as read_skill


@click.command("diff")
@click.argument("skill_a", type=click.Path(exists=True))
@click.argument("skill_b", type=click.Path(exists=True))
@click.pass_context
def diff_cmd(ctx: click.Context, skill_a: str, skill_b: str) -> None:
    """Compare two SKILL.md files and show differences."""
    console = ctx.obj["console"]

    a = read_skill(Path(skill_a))
    b = read_skill(Path(skill_b))

    has_diff = False

    # Frontmatter diff
    dict_a = a.frontmatter.model_dump(mode="json")
    dict_b = b.frontmatter.model_dump(mode="json")
    all_keys = sorted(set(dict_a) | set(dict_b))
    for key in all_keys:
        if dict_a.get(key) != dict_b.get(key):
            has_diff = True
            console.print(f"[bold]frontmatter.{key}:[/bold]")
            console.print(f"  [red]- {dict_a.get(key)!r}[/red]")
            console.print(f"  [green]+ {dict_b.get(key)!r}[/green]")

    # Body diff
    body_diff = list(
        difflib.unified_diff(
            a.body.splitlines(keepends=True),
            b.body.splitlines(keepends=True),
            fromfile=skill_a,
            tofile=skill_b,
        )
    )
    if body_diff:
        has_diff = True
        console.print("\n[bold]Body diff:[/bold]")
        for line in body_diff:
            stripped = line.rstrip("\n")
            if line.startswith("+"):
                console.print(f"[green]{stripped}[/green]")
            elif line.startswith("-"):
                console.print(f"[red]{stripped}[/red]")
            else:
                console.print(stripped)

    if has_diff:
        ctx.exit(1)
        sys.exit(1)
    else:
        console.print("[green]Skills are identical.[/green]")
