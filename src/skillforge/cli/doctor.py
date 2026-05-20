"""Diagnostic command for checking skillforge environment health."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.table import Table

from skillforge.version import __version__

if TYPE_CHECKING:
    from rich.console import Console


@click.command("doctor")
@click.pass_context
def doctor_cmd(ctx: click.Context) -> None:
    """Run diagnostics on the skillforge environment."""
    console: Console = ctx.obj["console"]
    table = Table(title="skillforge doctor")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail")

    has_fail = False

    # Python version
    py_ver = platform.python_version()
    py_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python version",
        "[green]OK[/green]" if py_ok else "[red]FAIL[/red]",
        py_ver,
    )
    if not py_ok:
        has_fail = True

    # Package version
    table.add_row(
        "skillforge version",
        "[green]OK[/green]",
        __version__,
    )

    # Provider env vars
    providers_found: list[str] = []
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(key):
            providers_found.append(key.split("_")[0].lower())
    prov_status = "[green]OK[/green]" if providers_found else "[yellow]WARN[/yellow]"
    prov_detail = ", ".join(providers_found) if providers_found else "none (mock only)"
    table.add_row("Providers detected", prov_status, prov_detail)

    # Workspace status
    cwd = Path.cwd()
    has_toml = (cwd / "skillforge.toml").exists()
    has_tasks = (cwd / "tasks.yaml").exists()
    has_runs = (cwd / "runs").exists()
    ws_parts: list[str] = []
    if has_toml:
        ws_parts.append("skillforge.toml")
    if has_tasks:
        ws_parts.append("tasks.yaml")
    if has_runs:
        ws_parts.append("runs/")
    ws_ok = has_toml and has_tasks
    ws_status = "[green]OK[/green]" if ws_ok else "[yellow]WARN[/yellow]"
    ws_detail = ", ".join(ws_parts) if ws_parts else "no workspace files found"
    table.add_row("Workspace", ws_status, ws_detail)

    # Disk free
    disk = shutil.disk_usage(cwd)
    free_gb = disk.free / (1024**3)
    disk_ok = free_gb > 1.0
    disk_status = "[green]OK[/green]" if disk_ok else "[red]FAIL[/red]"
    table.add_row("Disk free", disk_status, f"{free_gb:.1f} GB")
    if not disk_ok:
        has_fail = True

    console.print(table)
    ctx.exit(1 if has_fail else 0)
