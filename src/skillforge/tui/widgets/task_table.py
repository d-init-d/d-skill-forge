"""Task results table widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable


class TaskTable(Widget):
    """Table displaying task execution results."""

    DEFAULT_CSS = """
    TaskTable { height: auto; max-height: 20; }
    """

    def compose(self) -> ComposeResult:
        """Compose the data table."""
        table = DataTable(id="task-table")
        table.add_columns("Task", "Status", "Score", "Latency")
        yield table

    def add_result(self, task_id: str, passed: bool, score: float, latency_ms: int) -> None:
        """Add a task result row."""
        table = self.query_one("#task-table", DataTable)
        status = "✓ PASS" if passed else "✗ FAIL"
        table.add_row(task_id, status, f"{score:.2f}", f"{latency_ms}ms")

    def clear_results(self) -> None:
        """Clear all rows."""
        table = self.query_one("#task-table", DataTable)
        table.clear()
