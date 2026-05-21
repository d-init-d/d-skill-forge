"""Models selection screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option

from skillforge.providers.presets import PRESETS


class ModelsScreen(Screen[str]):
    """Screen for selecting a model for the active provider."""

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self, provider_id: str) -> None:
        super().__init__()
        self._provider_id = provider_id

    def compose(self) -> ComposeResult:
        """Compose model selection."""
        preset = PRESETS.get(self._provider_id)
        title = preset.name if preset else self._provider_id
        yield Static(f"[bold]Select Model for {title}[/bold]\n")

        if preset:
            yield OptionList(
                Option(preset.default_model, id=preset.default_model),
                id="model-list",
            )
        yield Static("\nOr enter a custom model ID:")
        yield Input(placeholder="model-name", id="model-input")
        yield Button("Select", variant="primary", id="btn-select")
        yield Button("Back", variant="default", id="btn-back")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle model selection from list."""
        self.dismiss(str(event.option.id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle buttons."""
        if event.button.id == "btn-select":
            model = self.query_one("#model-input", Input).value.strip()
            if model:
                self.dismiss(model)
        elif event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        """Go back."""
        self.app.pop_screen()
