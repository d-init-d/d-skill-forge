"""Skill viewer screen — renders SKILL.md with syntax highlighting."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, RichLog, Static


class SkillViewerScreen(Screen[None]):
    """Screen for viewing generated SKILL.md files."""

    BINDINGS = [("escape", "go_back", "Back")]

    def __init__(self, skill_path: Path | None = None) -> None:
        super().__init__()
        self._skill_path = skill_path

    def compose(self) -> ComposeResult:
        """Compose skill viewer."""
        yield Static("[bold]📄 Skill Viewer[/bold]\n")
        yield RichLog(id="skill-content", highlight=True, markup=True)
        yield Button("Back", variant="default", id="btn-back")

    def on_mount(self) -> None:
        """Load and display skill content."""
        log = self.query_one("#skill-content", RichLog)

        if self._skill_path and self._skill_path.exists():
            content = self._skill_path.read_text(encoding="utf-8")
            log.write(content)
        else:
            # Try to find a skill in the default location
            candidates = list(Path.cwd().glob("skills/**/SKILL.md"))
            if candidates:
                content = candidates[0].read_text(encoding="utf-8")
                log.write(f"[dim]File: {candidates[0]}[/dim]\n")
                log.write(content)
            else:
                log.write("[yellow]No SKILL.md found. Run extract first.[/yellow]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle back."""
        if event.button.id == "btn-back":
            self.action_go_back()

    def action_go_back(self) -> None:
        """Return to dashboard."""
        self.app.pop_screen()
