"""Welcome screen shown on first run when no providers are configured."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static


class WelcomeScreen(Screen[None]):
    """First-run welcome screen prompting user to connect a provider."""

    BINDINGS = [("enter", "connect", "Connect"), ("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Compose welcome layout."""
        yield Static(
            "\n\n\n"
            "        d-skill-forge\n"
            "\n"
            "        Distill skills from frontier models.\n"
            "        No fine-tuning required.\n"
            "\n\n"
            "        No providers configured.\n"
            "\n"
            "        [dim]Press Enter to connect your first provider.[/dim]\n",
            id="welcome-text",
        )
        yield Button("Connect", variant="primary", id="btn-connect")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-connect":
            self.action_connect()

    def action_connect(self) -> None:
        """Navigate to connect screen."""
        from skillforge.tui.screens.connect import ConnectScreen

        self.app.push_screen(ConnectScreen())
