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
            "\n\n"
            "  ╔══════════════════════════════════════════╗\n"
            "  ║       🔥 d-skill-forge                   ║\n"
            "  ║   Skill Distillation Engine              ║\n"
            "  ╚══════════════════════════════════════════╝\n"
            "\n"
            "  Distill procedural skills from frontier\n"
            "  model traces into reusable SKILL.md files.\n"
            "\n"
            "  No providers configured yet.\n"
            "  Press [bold cyan]Enter[/] to connect your first provider.\n",
            id="welcome-text",
        )
        yield Button("Connect Provider", variant="primary", id="btn-connect")
        yield Button("Quit", variant="default", id="btn-quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-connect":
            self.action_connect()
        elif event.button.id == "btn-quit":
            self.app.exit()

    def action_connect(self) -> None:
        """Navigate to connect screen."""
        from skillforge.tui.screens.connect import ConnectScreen

        self.app.push_screen(ConnectScreen())
