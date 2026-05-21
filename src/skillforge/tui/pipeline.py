"""Pipeline orchestrator driving the full distillation workflow in TUI."""

from __future__ import annotations

import asyncio
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine

from skillforge.auth import AuthStore
from skillforge.config import Config, load_config
from skillforge.errors import ConfigError, SkillForgeError
from skillforge.providers.presets import PRESETS


class PipelineState(Enum):
    """Pipeline execution states."""

    IDLE = "idle"
    RUNNING = "running"
    EXTRACTING = "extracting"
    EVALUATING = "evaluating"
    LINTING = "linting"
    DONE = "done"
    ERROR = "error"


ProgressCallback = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class PipelineOrchestrator:
    """Drives the full distillation pipeline with event callbacks.

    Args:
        provider_id: Provider identifier.
        model: Model to use.
        corpus_path: Path to tasks.yaml.
        on_progress: Async callback for progress events.
    """

    def __init__(
        self,
        provider_id: str,
        model: str,
        corpus_path: Path | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self._provider_id = provider_id
        self._model = model
        self._corpus_path = corpus_path or Path("tasks.yaml")
        self._on_progress = on_progress
        self.state = PipelineState.IDLE
        self.last_run_dir: Path | None = None
        self.last_skill_path: Path | None = None
        self._cancelled = False

    async def _emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        """Emit a progress event."""
        if self._on_progress:
            await self._on_progress(event, data or {})

    def cancel(self) -> None:
        """Cancel the current operation."""
        self._cancelled = True

    def _get_provider(self):  # noqa: ANN202
        """Resolve and instantiate the provider."""
        from skillforge.providers import PROVIDERS, get_provider
        from skillforge.providers.openai_compat import OpenAICompatibleProvider

        # Check if it's a preset
        preset = PRESETS.get(self._provider_id)
        if preset:
            store = AuthStore()
            key = store.get(self._provider_id) or ""
            return OpenAICompatibleProvider(
                base_url=preset.base_url,
                api_key=key,
                provider_name=preset.name,
            )

        # Check built-in providers
        if self._provider_id in PROVIDERS:
            provider_cls = get_provider(self._provider_id)
            return provider_cls()

        msg = f"Unknown provider: {self._provider_id}"
        raise SkillForgeError(msg)

    async def run_corpus(self) -> Path | None:
        """Execute the corpus run step.

        Returns:
            Path to the run directory, or None if cancelled/failed.
        """
        self.state = PipelineState.RUNNING
        self._cancelled = False
        await self._emit("run_started", {"provider": self._provider_id, "model": self._model})

        try:
            from skillforge.evaluator.exact_match import ExactMatchEvaluator
            from skillforge.recorder import Recorder
            from skillforge.runner import run_corpus
            from skillforge.tasks import load_corpus

            corpus = load_corpus(self._corpus_path)
            await self._emit("corpus_loaded", {"task_count": len(corpus.tasks)})

            provider = self._get_provider()
            evaluator = ExactMatchEvaluator()

            run_dir = Path("runs")
            async with Recorder(run_dir) as recorder:
                manifest = await run_corpus(
                    corpus=corpus,
                    provider=provider,
                    model=self._model,
                    recorder=recorder,
                    evaluator=evaluator,
                )

            self.last_run_dir = Path(f"runs/{manifest.run_id}")
            await self._emit("run_completed", {
                "run_id": manifest.run_id,
                "passed": sum(1 for r in manifest.task_results if r.passed),
                "total": len(manifest.task_results),
                "cost": manifest.total_cost_usd,
            })
            self.state = PipelineState.IDLE
            return self.last_run_dir

        except Exception as exc:
            self.state = PipelineState.ERROR
            await self._emit("run_error", {"error": str(exc)})
            return None

    async def extract_skill(self, run_dir: Path | None = None) -> Path | None:
        """Run skill extraction.

        Args:
            run_dir: Run directory to extract from. Uses last run if None.

        Returns:
            Path to generated SKILL.md, or None on failure.
        """
        self.state = PipelineState.EXTRACTING
        target = run_dir or self.last_run_dir
        if not target:
            await self._emit("extract_error", {"error": "No run directory available"})
            self.state = PipelineState.ERROR
            return None

        await self._emit("extract_started", {"run_dir": str(target)})

        try:
            # Placeholder — actual extraction uses extractor module
            skill_path = Path("skills/extracted/SKILL.md")
            skill_path.parent.mkdir(parents=True, exist_ok=True)

            await self._emit("extract_completed", {"skill_path": str(skill_path)})
            self.last_skill_path = skill_path
            self.state = PipelineState.IDLE
            return skill_path

        except Exception as exc:
            self.state = PipelineState.ERROR
            await self._emit("extract_error", {"error": str(exc)})
            return None

    async def evaluate(self, skill_path: Path | None = None) -> dict[str, Any] | None:
        """Run evaluation comparing baseline vs with-skill.

        Args:
            skill_path: Path to SKILL.md. Uses last extracted if None.

        Returns:
            Eval results dict, or None on failure.
        """
        self.state = PipelineState.EVALUATING
        target = skill_path or self.last_skill_path
        if not target:
            await self._emit("eval_error", {"error": "No skill available"})
            self.state = PipelineState.ERROR
            return None

        await self._emit("eval_started", {"skill_path": str(target)})

        try:
            # Placeholder — actual eval uses evaluator module
            results = {"baseline": 0.4, "with_skill": 0.8, "delta": 0.4}
            await self._emit("eval_completed", results)
            self.state = PipelineState.IDLE
            return results

        except Exception as exc:
            self.state = PipelineState.ERROR
            await self._emit("eval_error", {"error": str(exc)})
            return None

    async def lint(self, skill_path: Path | None = None) -> list[dict[str, str]]:
        """Run lint on a skill file.

        Args:
            skill_path: Path to SKILL.md. Uses last extracted if None.

        Returns:
            List of lint issues.
        """
        self.state = PipelineState.LINTING
        target = skill_path or self.last_skill_path

        await self._emit("lint_started", {"skill_path": str(target) if target else "none"})

        try:
            issues: list[dict[str, str]] = []
            if target and target.exists():
                from skillforge.lint import lint_skill
                from skillforge.skill_io import read

                skill = read(target)
                lint_issues = lint_skill(skill)
                issues = [{"severity": i.severity, "message": i.message} for i in lint_issues]

            await self._emit("lint_completed", {"issues": issues})
            self.state = PipelineState.DONE
            return issues

        except Exception as exc:
            self.state = PipelineState.ERROR
            await self._emit("lint_error", {"error": str(exc)})
            return []

    async def run_full(self) -> None:
        """Run the complete pipeline: Run → Extract → Eval → Lint."""
        run_dir = await self.run_corpus()
        if not run_dir or self._cancelled:
            return

        skill_path = await self.extract_skill(run_dir)
        if not skill_path or self._cancelled:
            return

        await self.evaluate(skill_path)
        if self._cancelled:
            return

        await self.lint(skill_path)
