"""Run screen — executes corpus and shows live progress."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, ProgressBar, RichLog, Static

from skillforge.tui.widgets.cost_ticker import CostTicker
from skillforge.tui.widgets.task_table import TaskTable


class RunScreen(Screen[None]):
    """Screen for running a task corpus with live progress."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        """Compose run screen layout."""
        yield Static("[bold]▶ Running Corpus[/bold]\n", id="run-title")
        yield ProgressBar(total=100, id="run-progress")
        yield CostTicker()
        yield TaskTable()
        yield RichLog(id="run-log", highlight=True, markup=True)
        yield Button("Cancel", variant="error", id="btn-cancel")

    def on_mount(self) -> None:
        """Start the run when screen mounts."""
        self._start_run()

    def _start_run(self) -> None:
        """Kick off the corpus run."""
        log = self.query_one("#run-log", RichLog)
        log.write("[cyan]Starting corpus run...[/cyan]")
        log.write("Looking for tasks.yaml in current directory...")
        # Actual run logic will be wired in Phase E (Pipeline Orchestrator)
        self.notify("Run started — pipeline orchestrator will be wired in Phase E")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel."""
        if event.button.id == "btn-cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        """Cancel and return to dashboard."""
        self.notify("Run cancelled", severity="warning")
        self.app.pop_screen()
