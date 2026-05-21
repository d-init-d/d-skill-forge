"""Eval screen — shows baseline vs with-skill comparison."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, DataTable, RichLog, Static


class EvalScreen(Screen[None]):
    """Screen for evaluating skill effectiveness."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        """Compose eval screen."""
        yield Static("[bold]📊 Evaluating Skill[/bold]\n")
        table = DataTable(id="eval-table")
        table.add_columns("Metric", "Baseline", "With Skill", "Delta")
        yield table
        yield RichLog(id="eval-log", highlight=True, markup=True)
        yield Button("Back", variant="default", id="btn-back")

    def on_mount(self) -> None:
        """Start evaluation."""
        log = self.query_one("#eval-log", RichLog)
        log.write("[cyan]Running evaluation...[/cyan]")
        self.notify("Eval — pipeline orchestrator will be wired in Phase E")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back."""
        if event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        """Return to dashboard."""
        self.app.pop_screen()
