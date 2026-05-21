"""Cost ticker widget for real-time cost tracking."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static


class CostTicker(Widget):
    """Displays running cost total."""

    DEFAULT_CSS = """
    CostTicker { height: 1; }
    """

    def __init__(self) -> None:
        super().__init__()
        self._total: float = 0.0

    def compose(self):  # noqa: ANN201
        """Compose the cost display."""
        yield Static(self._format(), id="cost-display")

    def _format(self) -> str:
        return f"💰 Total cost: ${self._total:.4f}"

    def add_cost(self, amount: float) -> None:
        """Add to running total and refresh."""
        self._total += amount
        try:
            self.query_one("#cost-display", Static).update(self._format())
        except Exception:
            pass

    def reset(self) -> None:
        """Reset cost to zero."""
        self._total = 0.0
