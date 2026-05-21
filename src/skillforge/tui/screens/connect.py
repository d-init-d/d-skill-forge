"""Connect screen — paste key and go. Zero config needed."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option

from skillforge.auth import AuthStore
from skillforge.providers.presets import PRESETS, get_all_provider_ids


class ConnectScreen(Screen[None]):
    """Provider connection — just pick and paste key."""

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self) -> None:
        super().__init__()
        self._selected_provider: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the connect wizard."""
        yield Static("\n  [bold]Connect Provider[/bold]\n")
        yield Static("  Select a provider:\n", id="connect-prompt")

        options = []
        for pid in get_all_provider_ids():
            preset = PRESETS.get(pid)
            label = f"  {preset.name}" if preset else f"  {pid}"
            options.append(Option(label, id=pid))
        yield OptionList(*options, id="provider-list")

        yield Static("", id="key-prompt")
        yield Input(placeholder="Paste API key...", password=True, id="key-input")
        yield Button("Save", variant="primary", id="btn-save")
        yield Button("Back", id="btn-back")

    def on_mount(self) -> None:
        """Hide key input until provider selected."""
        self.query_one("#key-input", Input).display = False
        self.query_one("#btn-save", Button).display = False
        self.query_one("#key-prompt", Static).display = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Provider selected — show key input or auto-save for local."""
        self._selected_provider = str(event.option.id)
        preset = PRESETS.get(self._selected_provider)

        # Local providers (ollama, lmstudio) — no key needed
        if preset and not preset.requires_key:
            store = AuthStore()
            store.set(self._selected_provider, "")
            self.notify(f"{preset.name} configured", severity="information")
            self._go_to_dashboard()
            return

        # Show key input
        label = preset.name if preset else self._selected_provider
        self.query_one("#key-prompt", Static).update(f"\n  API key for {label}:")
        self.query_one("#key-prompt", Static).display = True
        self.query_one("#key-input", Input).display = True
        self.query_one("#btn-save", Button).display = True
        self.query_one("#key-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter pressed in key input — save."""
        if event.input.id == "key-input":
            self._save_key()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle buttons."""
        if event.button.id == "btn-save":
            self._save_key()
        elif event.button.id == "btn-back":
            self.action_go_back()

    def _save_key(self) -> None:
        """Save key — no extra config questions."""
        key = self.query_one("#key-input", Input).value.strip()
        if not key:
            self.notify("Key cannot be empty", severity="error")
            return
        if not self._selected_provider:
            return

        store = AuthStore()
        store.set(self._selected_provider, key)

        preset = PRESETS.get(self._selected_provider)
        name = preset.name if preset else self._selected_provider
        self.notify(f"{name} connected", severity="information")
        self._go_to_dashboard()

    def _go_to_dashboard(self) -> None:
        """Navigate to dashboard."""
        from skillforge.tui.screens.dashboard import DashboardScreen

        self.app.switch_screen(DashboardScreen())

    def action_go_back(self) -> None:
        """Go back."""
        self.app.pop_screen()
