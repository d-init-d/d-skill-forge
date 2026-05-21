"""Extract screen — runs skill extraction and shows progress."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, RichLog, Static


class ExtractScreen(Screen[None]):
    """Screen for extracting a SKILL.md from run traces."""

    BINDINGS = [("escape", "go_back", "Back")]

    def compose(self) -> ComposeResult:
        """Compose extract screen."""
        yield Static("[bold]⚗ Extracting Skill[/bold]\n")
        yield RichLog(id="extract-log", highlight=True, markup=True)
        yield Button("Back", variant="default", id="btn-back")

    def on_mount(self) -> None:
        """Start extraction."""
        log = self.query_one("#extract-log", RichLog)
        log.write("[cyan]Starting reflective extraction...[/cyan]")
        log.write("Analyzing traces from latest run...")
        self.notify("Extraction — pipeline orchestrator will be wired in Phase E")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back button."""
        if event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        """Return to dashboard."""
        self.app.pop_screen()
