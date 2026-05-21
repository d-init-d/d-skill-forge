"""Main TUI application for d-skill-forge."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from skillforge.tui.screens.dashboard import DashboardScreen
from skillforge.tui.screens.welcome import WelcomeScreen


class SkillForgeApp(App[None]):
    """d-skill-forge TUI application.

    Provides a full-screen terminal interface for running the skill
    distillation pipeline: connect providers, run corpus, extract skills,
    evaluate, and lint.
    """

    TITLE = "d-skill-forge"
    SUB_TITLE = "Skill Distillation Engine"
    CSS_PATH = "theme.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+p", "command_palette", "Commands"),
        Binding("f1", "help", "Help"),
        Binding("slash", "slash_command", "/Command"),
    ]

    def on_mount(self) -> None:
        """Determine initial screen based on auth state."""
        from skillforge.auth import AuthStore

        store = AuthStore()
        if store.list_providers():
            self.push_screen(DashboardScreen())
        else:
            self.push_screen(WelcomeScreen())

    def compose(self) -> ComposeResult:
        """Compose the base app layout."""
        yield Header()
        yield Footer()

    def action_help(self) -> None:
        """Show help notification."""
        self.notify(
            "Keybinds: q=Quit, Tab=Next step, 1-4=Jump to step, /=Command",
            title="Help",
        )

    def action_command_palette(self) -> None:
        """Open command palette."""
        from skillforge.tui.screens.connect import ConnectScreen

        self.push_screen(ConnectScreen())

    def action_slash_command(self) -> None:
        """Handle slash command input."""
        self.notify(
            "Commands: /connect, /models, /run, /extract, /eval, /lint, /quit",
            title="Available Commands",
        )
