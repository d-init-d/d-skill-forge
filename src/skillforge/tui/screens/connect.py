"""Connect screen for adding provider credentials."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option

from skillforge.auth import AuthStore
from skillforge.providers.presets import PRESETS, get_all_provider_ids


class ConnectScreen(Screen[None]):
    """Provider connection wizard."""

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self) -> None:
        super().__init__()
        self._selected_provider: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the connect wizard."""
        yield Static("[bold]Connect a Provider[/bold]\n", id="connect-title")
        yield Static("Select a provider:", id="connect-prompt")
        options = [Option(f"{pid} — {PRESETS[pid].name}" if pid in PRESETS else pid, id=pid) for pid in get_all_provider_ids()]
        yield OptionList(*options, id="provider-list")
        yield Static("", id="key-prompt")
        yield Input(placeholder="Paste your API key here...", password=True, id="key-input")
        yield Button("Save", variant="primary", id="btn-save", disabled=True)
        yield Button("Back", variant="default", id="btn-back")

    def on_mount(self) -> None:
        """Hide key input initially."""
        self.query_one("#key-input", Input).display = False
        self.query_one("#btn-save", Button).display = False
        self.query_one("#key-prompt", Static).display = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle provider selection."""
        self._selected_provider = str(event.option.id)
        preset = PRESETS.get(self._selected_provider)

        if preset and not preset.requires_key:
            # Local provider, no key needed
            store = AuthStore()
            store.set(self._selected_provider, "")
            self.notify(f"✓ {preset.name} configured (no key needed)", severity="information")
            self._go_to_dashboard()
            return

        label = preset.name if preset else self._selected_provider
        self.query_one("#key-prompt", Static).update(f"\nEnter API key for [cyan]{label}[/cyan]:")
        self.query_one("#key-prompt", Static).display = True
        self.query_one("#key-input", Input).display = True
        self.query_one("#btn-save", Button).display = True
        self.query_one("#btn-save", Button).disabled = False
        self.query_one("#key-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save":
            self._save_key()
        elif event.button.id == "btn-back":
            self.action_go_back()

    def _save_key(self) -> None:
        """Save the entered API key."""
        key = self.query_one("#key-input", Input).value.strip()
        if not key:
            self.notify("API key cannot be empty", severity="error")
            return
        if not self._selected_provider:
            return

        store = AuthStore()
        store.set(self._selected_provider, key)
        preset = PRESETS.get(self._selected_provider)
        name = preset.name if preset else self._selected_provider
        self.notify(f"✓ Credentials saved for {name}", severity="information")
        self._go_to_dashboard()

    def _go_to_dashboard(self) -> None:
        """Navigate to dashboard."""
        from skillforge.tui.screens.dashboard import DashboardScreen

        self.app.switch_screen(DashboardScreen())

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
