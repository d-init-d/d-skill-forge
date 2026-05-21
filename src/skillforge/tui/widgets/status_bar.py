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
        background: #181825;
        layout: horizontal;
        padding: 0 2;
    }
    StatusBar .status-item {
        width: 1fr;
    }
    """

    def __init__(
        self,
        provider: str = "—",
        model: str = "—",
        cost: float = 0.0,
    ) -> None:
        super().__init__()
        self._provider = provider
        self._model = model
        self._cost = cost

    def compose(self) -> ComposeResult:
        """Compose status items."""
        yield Static(f"Provider: {self._provider}", classes="status-item provider-label")
        yield Static(f"Model: {self._model}", classes="status-item")
        yield Static(f"Cost: ${self._cost:.4f}", classes="status-item cost-label")

    def update_info(self, provider: str, model: str, cost: float) -> None:
        """Update displayed info."""
        self._provider = provider
        self._model = model
        self._cost = cost
        self.refresh(layout=True)
