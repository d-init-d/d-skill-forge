"""CLI subcommands for managing provider authentication."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from skillforge.auth import AuthStore
from skillforge.providers.presets import PRESETS, get_all_provider_ids

console = Console()


@click.group("auth")
def auth_cmd() -> None:
    """Manage provider credentials."""


@auth_cmd.command("list")
def auth_list() -> None:
    """Show configured providers and their auth status."""
    store = AuthStore()
    configured = store.list_providers()

    table = Table(title="Provider Credentials")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Source")

    for pid in get_all_provider_ids():
        if pid in configured:
            table.add_row(pid, "✓ configured", "auth.json")
        else:
            preset = PRESETS.get(pid)
            env_var = preset.api_key_env if preset else ""
            table.add_row(pid, "✗ not set", env_var or "—")

    console.print(table)


@auth_cmd.command("add")
@click.argument("provider")
def auth_add(provider: str) -> None:
    """Add or update credentials for a provider."""
    preset = PRESETS.get(provider)
    label = preset.name if preset else provider

    api_key = click.prompt(f"Enter API key for {label}", hide_input=True)
    if not api_key.strip():
        console.print("[red]Error:[/red] API key cannot be empty.")
        raise SystemExit(1)

    store = AuthStore()
    store.set(provider, api_key.strip())
    console.print(f"[green]✓[/green] Credentials saved for [cyan]{provider}[/cyan]")


@auth_cmd.command("remove")
@click.argument("provider")
def auth_remove(provider: str) -> None:
    """Remove credentials for a provider."""
    store = AuthStore()
    if store.delete(provider):
        console.print(f"[green]✓[/green] Removed credentials for [cyan]{provider}[/cyan]")
    else:
        console.print(f"[yellow]No credentials found for {provider}[/yellow]")


@auth_cmd.command("test")
@click.argument("provider")
def auth_test(provider: str) -> None:
    """Test connectivity for a provider (sends a minimal request)."""
    store = AuthStore()
    key = store.get(provider)
    if not key:
        console.print(f"[red]No credentials for {provider}. Run: skillforge auth add {provider}[/red]")
        raise SystemExit(1)

    preset = PRESETS.get(provider)
    if not preset:
        console.print(f"[yellow]{provider} is not a known preset. Cannot auto-test.[/yellow]")
        return

    console.print(f"Testing [cyan]{preset.name}[/cyan] at {preset.base_url}...")

    import asyncio

    from skillforge.providers.openai_compat import OpenAICompatibleProvider

    async def _test() -> None:
        from skillforge.models.trace import ContentBlock, Message
        from skillforge.providers.base import CompletionRequest

        p = OpenAICompatibleProvider(
            base_url=preset.base_url,
            api_key=key,
            provider_name=preset.name,
        )
        req = CompletionRequest(
            model=preset.default_model,
            messages=[Message(role="user", content=[ContentBlock(type="text", text="hi")])],
            max_tokens=1,
        )
        resp = await p.complete(req)
        console.print(f"[green]✓ Connected![/green] Model: {resp.model}")

    try:
        asyncio.run(_test())
    except Exception as exc:
        console.print(f"[red]✗ Failed:[/red] {exc}")
        raise SystemExit(1) from exc
