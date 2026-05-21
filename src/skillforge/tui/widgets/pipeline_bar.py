"""Pipeline progress bar widget showing distillation steps."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class PipelineBar(Widget):
    """Horizontal bar showing pipeline steps: Run → Extract → Eval → Lint."""

    DEFAULT_CSS = """
    PipelineBar {
        height: 3;
        background: #313244;
        layout: horizontal;
        padding: 1 2;
    }
    PipelineBar .step {
        width: 1fr;
        text-align: center;
    }
    """

    STEPS = ["Run", "Extract", "Eval", "Lint"]

    def __init__(self, active: int = 0) -> None:
        super().__init__()
        self._active = active

    def compose(self) -> ComposeResult:
        """Compose step labels."""
        for i, step in enumerate(self.STEPS):
            label = f"[{i + 1}] {step}"
            if i < self._active:
                css_class = "step step-done"
            elif i == self._active:
                css_class = "step step-active"
            else:
                css_class = "step step-pending"
            yield Static(label, classes=css_class)

    def set_active(self, index: int) -> None:
        """Update the active step."""
        self._active = index
        self.refresh(layout=True)
