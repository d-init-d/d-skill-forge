"""CLI command: skillforge eval — compare weak model with and without a skill."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import click
from rich.table import Table

from skillforge.errors import SkillForgeError
from skillforge.evaluator import ExactMatchEvaluator, compare_runs
from skillforge.models.skill import EvalReport
from skillforge.paths import runs_dir
from skillforge.providers import get_provider
from skillforge.recorder import Recorder, load_run
from skillforge.runner import run_corpus
from skillforge.skill_io import read as read_skill
from skillforge.skill_io import write as write_skill
from skillforge.tasks import load_corpus


@click.command("eval")
@click.option("--skill", "skill_path", type=click.Path(exists=True), required=True)
@click.option("--corpus", "corpus_path", type=click.Path(exists=True), required=True)
@click.option("--provider", "provider_name", type=str, default="mock")
@click.option("--weak-model", "weak_model", type=str, default="mock-weak")
@click.option("--baseline-run", "baseline_run_path", type=click.Path(exists=True), default=None)
@click.pass_context
def eval_cmd(
    ctx: click.Context,
    skill_path: str,
    corpus_path: str,
    provider_name: str,
    weak_model: str,
    baseline_run_path: str | None,
) -> None:
    """Evaluate a skill by comparing weak model performance.

    Args:
        ctx: Click context.
        skill_path: Path to the SKILL.md file.
        corpus_path: Path to the task corpus.
        provider_name: Provider name.
        weak_model: Weak model identifier.
        baseline_run_path: Optional pre-existing baseline run.
    """
    console = ctx.obj["console"]

    skill = read_skill(Path(skill_path))
    corpus = load_corpus(Path(corpus_path))
    provider_cls = get_provider(provider_name)
    provider = provider_cls()
    evaluator = ExactMatchEvaluator()

    base_dir = runs_dir(Path.cwd())
    base_dir.mkdir(parents=True, exist_ok=True)

    async def _eval() -> None:
        # Baseline run (without skill)
        if baseline_run_path:
            baseline_manifest, _ = load_run(Path(baseline_run_path))
        else:
            baseline_dir = base_dir / "eval-baseline"
            recorder = Recorder.open(baseline_dir)
            async with recorder:
                baseline_manifest = await run_corpus(
                    corpus=corpus,
                    provider=provider,
                    model=weak_model,
                    concurrency=4,
                    recorder=recorder,
                    evaluator=evaluator,
                )

        # Skill-augmented run
        skill_dir = base_dir / "eval-with-skill"
        recorder = Recorder.open(skill_dir)
        async with recorder:
            skill_manifest = await run_corpus(
                corpus=corpus,
                provider=provider,
                model=weak_model,
                skill=skill,
                concurrency=4,
                recorder=recorder,
                evaluator=evaluator,
            )

        delta = compare_runs(baseline_manifest, skill_manifest)

        # Print results table
        table = Table(title="Eval Results")
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        table.add_row("Baseline score", f"{delta.baseline_score:.3f}")
        table.add_row("With skill score", f"{delta.with_skill_score:.3f}")
        table.add_row("Delta", f"{delta.delta:+.3f}")
        table.add_row("Tasks evaluated", str(delta.tasks_evaluated))
        console.print(table)

        # Append EvalReport to skill frontmatter
        report = EvalReport(
            target_model=weak_model,
            baseline_score=delta.baseline_score,
            with_skill_score=delta.with_skill_score,
            delta=delta.delta,
            tasks_evaluated=delta.tasks_evaluated,
            timestamp=datetime.now(tz=UTC),
        )
        skill.frontmatter.eval.append(report)
        write_skill(skill, Path(skill_path))
        console.print(f"[green]✓[/green] EvalReport appended to [bold]{skill_path}[/bold]")

    try:
        asyncio.run(_eval())
    except SkillForgeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
