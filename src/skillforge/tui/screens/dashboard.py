"""Dashboard screen — main view after provider setup."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Static

from skillforge.auth import AuthStore
from skillforge.providers.presets import PRESETS
from skillforge.tui.widgets.pipeline_bar import PipelineBar
from skillforge.tui.widgets.status_bar import StatusBar


class DashboardScreen(Screen[None]):
    """Main dashboard with pipeline controls and undo."""

    BINDINGS = [
        Binding("1", "step_run", "Run"),
        Binding("2", "step_extract", "Extract"),
        Binding("3", "step_eval", "Eval"),
        Binding("4", "step_lint", "Lint"),
        Binding("tab", "next_step", "Next"),
        Binding("c", "connect", "Connect"),
        Binding("s", "view_skill", "Skill"),
        Binding("u", "undo", "Undo"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._active_step = 0
        self._provider, self._model = self._detect_provider()
        self._has_run = False

    def _detect_provider(self) -> tuple[str, str]:
        """Auto-detect provider and model from auth store."""
        store = AuthStore()
        configured = store.list_providers()
        if not configured:
            return ("-", "-")

        # Pick first configured provider
        pid = configured[0]
        preset = PRESETS.get(pid)
        model = preset.default_model if preset else "-"
        return (pid, model)

    def compose(self) -> ComposeResult:
        """Compose dashboard layout."""
        yield PipelineBar(active=self._active_step)
        yield Static(
            "\n"
            "  [bold]Pipeline[/bold]\n"
            "\n"
            "  [dim]1[/dim] Run        Execute task corpus\n"
            "  [dim]2[/dim] Extract    Distill SKILL.md from traces\n"
            "  [dim]3[/dim] Eval       Measure skill effectiveness\n"
            "  [dim]4[/dim] Lint       Validate skill format\n"
            "\n"
            "  [dim]c[/dim] connect    [dim]s[/dim] view skill    [dim]u[/dim] undo\n",
            id="dashboard-info",
        )
        yield Button("Run", variant="primary", id="btn-run")
        yield Button("Extract", variant="success", id="btn-extract")
        yield Button("Eval", variant="warning", id="btn-eval")
        yield Button("Lint", id="btn-lint")
        yield Button("Undo Last Run", id="btn-undo")
        yield StatusBar(provider=self._provider, model=self._model)

    def on_mount(self) -> None:
        """Hide undo button initially."""
        self.query_one("#btn-undo", Button).display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle pipeline buttons."""
        actions = {
            "btn-run": self.action_step_run,
            "btn-extract": self.action_step_extract,
            "btn-eval": self.action_step_eval,
            "btn-lint": self.action_step_lint,
            "btn-undo": self.action_undo,
        }
        action = actions.get(event.button.id)
        if action:
            action()

    def action_step_run(self) -> None:
        """Launch run screen."""
        from skillforge.tui.screens.run import RunScreen

        self.app.push_screen(RunScreen())

    def action_step_extract(self) -> None:
        """Launch extract screen."""
        from skillforge.tui.screens.extract import ExtractScreen

        self.app.push_screen(ExtractScreen())

    def action_step_eval(self) -> None:
        """Launch eval screen."""
        from skillforge.tui.screens.eval import EvalScreen

        self.app.push_screen(EvalScreen())

    def action_step_lint(self) -> None:
        """Launch lint screen."""
        from skillforge.tui.screens.lint import LintScreen

        self.app.push_screen(LintScreen())

    def action_next_step(self) -> None:
        """Advance to next pipeline step."""
        self._active_step = (self._active_step + 1) % 4
        actions = [
            self.action_step_run,
            self.action_step_extract,
            self.action_step_eval,
            self.action_step_lint,
        ]
        actions[self._active_step]()

    def action_connect(self) -> None:
        """Open connect screen."""
        from skillforge.tui.screens.connect import ConnectScreen

        self.app.push_screen(ConnectScreen())

    def action_view_skill(self) -> None:
        """Open skill viewer."""
        from skillforge.tui.screens.skill_viewer import SkillViewerScreen

        self.app.push_screen(SkillViewerScreen())

    def action_undo(self) -> None:
        """Undo last run — remove the latest run directory."""
        import shutil
        from pathlib import Path

        runs_dir = Path("runs")
        if not runs_dir.exists():
            self.notify("Nothing to undo", severity="warning")
            return

        # Find most recent run
        run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        run_dirs = [d for d in run_dirs if d.is_dir()]

        if not run_dirs:
            self.notify("Nothing to undo", severity="warning")
            return

        latest = run_dirs[0]
        shutil.rmtree(latest)
        self.notify(f"Removed: {latest.name}", severity="information")
        self.query_one("#btn-undo", Button).display = False

    def show_undo(self) -> None:
        """Show undo button after a run completes."""
        self._has_run = True
        try:
            self.query_one("#btn-undo", Button).display = True
        except Exception:
            pass
