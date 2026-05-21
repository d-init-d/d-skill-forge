"""Status bar widget showing provider, model, cost info."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class StatusBar(Widget):
    """Bottom status bar with provider/model/cost info."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: #0a0a0a;
        layout: horizontal;
        padding: 0 3;
        dock: bottom;
    }
    StatusBar .status-item {
        width: 1fr;
        color: #555555;
    }
    """

    def __init__(
        self,
        provider: str = "-",
        model: str = "-",
        cost: float = 0.0,
    ) -> None:
        super().__init__()
        self._provider = provider
        self._model = model
        self._cost = cost

    def compose(self) -> ComposeResult:
        """Compose status items."""
        yield Static(f"provider: {self._provider}", classes="status-item")
        yield Static(f"model: {self._model}", classes="status-item")
        yield Static(f"cost: ${self._cost:.4f}", classes="status-item")

    def update_info(self, provider: str, model: str, cost: float) -> None:
        """Update displayed info."""
        self._provider = provider
        self._model = model
        self._cost = cost
        self.refresh(layout=True)
