"""Lint screen — shows skill validation results."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static


class LintScreen(Screen[None]):
    """Screen for displaying lint results."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        """Compose lint screen."""
        yield Static("[bold]✓ Lint Results[/bold]\n")
        table = DataTable(id="lint-table")
        table.add_columns("Severity", "Message", "Location")
        yield table
        yield Button("Back", variant="default", id="btn-back")

    def on_mount(self) -> None:
        """Run lint on available skills."""
        self.notify("Lint — pipeline orchestrator will be wired in Phase E")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back."""
        if event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        """Return to dashboard."""
        self.app.pop_screen()
