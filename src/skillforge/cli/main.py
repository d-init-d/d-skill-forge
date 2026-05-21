"""Root CLI group and top-level error handling for skillforge."""

from __future__ import annotations

import sys

import click
from rich.console import Console

import skillforge.providers.bedrock as _bedrock_provider
import skillforge.providers.gemini as _gemini_provider
import skillforge.providers.mock as _mock_provider
from skillforge.errors import SkillForgeError

# Ensure provider registration side-effect is not pruned.
_PROVIDERS_LOADED = bool(_mock_provider) and bool(_bedrock_provider) and bool(_gemini_provider)

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
from skillforge.cli.auth import auth_cmd  # noqa: E402
from skillforge.cli.diff import diff_cmd  # noqa: E402
from skillforge.cli.doctor import doctor_cmd  # noqa: E402
from skillforge.cli.eval import eval_cmd  # noqa: E402
from skillforge.cli.extract import extract_cmd  # noqa: E402
from skillforge.cli.init import init_cmd  # noqa: E402
from skillforge.cli.lint import lint_cmd  # noqa: E402
from skillforge.cli.run import run_cmd  # noqa: E402

cli.add_command(auth_cmd)
cli.add_command(diff_cmd)
cli.add_command(init_cmd)
cli.add_command(run_cmd)
cli.add_command(extract_cmd)
cli.add_command(eval_cmd)
cli.add_command(lint_cmd)
cli.add_command(doctor_cmd)


def main() -> None:
    """Entry point: TUI by default (no args), CLI otherwise."""
    import sys as _sys

    # If no arguments → launch TUI
    if len(_sys.argv) == 1:
        try:
            from skillforge.tui.app import SkillForgeApp

            app = SkillForgeApp()
            app.run()
        except ImportError:
            console.print(
                "[yellow]TUI requires textual. Install with:[/yellow] "
                "pip install d-skill-forge[tui]"
            )
            console.print("Falling back to CLI. Run: skillforge --help")
            _sys.exit(1)
        return

    # --no-tui flag: strip it and proceed with CLI
    if "--no-tui" in _sys.argv:
        _sys.argv.remove("--no-tui")

    try:
        cli(standalone_mode=False)
    except SystemExit as e:
        _sys.exit(e.code)
    except click.Abort:
        console.print("[yellow]Aborted.[/yellow]")
        _sys.exit(130)
    except SkillForgeError as e:
        console.print(f"[red]Error:[/red] {e}")
        _sys.exit(1)
