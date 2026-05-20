"""Root CLI group and top-level error handling for skillforge."""

from __future__ import annotations

import sys

import click
from rich.console import Console

import skillforge.providers.mock as _mock_provider
from skillforge.errors import SkillForgeError

# Ensure provider registration side-effect is not pruned.
_PROVIDERS_LOADED = bool(_mock_provider)

console = Console()


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=False), default=None)
@click.option("-v", "--verbose", is_flag=True)
@click.option("-q", "--quiet", is_flag=True)
@click.version_option(package_name="d-skill-forge")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None, verbose: bool, quiet: bool) -> None:
    """Distill procedural skills from frontier model traces."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["console"] = console


# Register subcommands — imports at module level to satisfy PLC0415.
from skillforge.cli.eval import eval_cmd  # noqa: E402
from skillforge.cli.extract import extract_cmd  # noqa: E402
from skillforge.cli.init import init_cmd  # noqa: E402
from skillforge.cli.lint import lint_cmd  # noqa: E402
from skillforge.cli.run import run_cmd  # noqa: E402

cli.add_command(init_cmd)
cli.add_command(run_cmd)
cli.add_command(extract_cmd)
cli.add_command(eval_cmd)
cli.add_command(lint_cmd)


def main() -> None:
    """Entry point with top-level error handling."""
    try:
        cli(standalone_mode=False)
    except SystemExit as e:
        sys.exit(e.code)
    except click.Abort:
        console.print("[yellow]Aborted.[/yellow]")
        sys.exit(130)
    except SkillForgeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
