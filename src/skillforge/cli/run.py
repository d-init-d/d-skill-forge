"""CLI command: skillforge run — execute a task corpus against a provider."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from skillforge.config import Config, load_config
from skillforge.errors import SkillForgeError
from skillforge.evaluator import ExactMatchEvaluator
from skillforge.paths import runs_dir
from skillforge.providers import get_provider
from skillforge.recorder import Recorder
from skillforge.runner import run_corpus
from skillforge.skill_io import read as read_skill
from skillforge.tasks import load_corpus


@click.command("run")
@click.option("--corpus", "corpus_path", type=click.Path(exists=True), required=True)
@click.option("--provider", "provider_name", type=str, default=None)
@click.option("--model", "model_name", type=str, default=None)
@click.option("--concurrency", type=int, default=None)
@click.option("--skill", "skill_path", type=click.Path(exists=True), default=None)
@click.pass_context
def run_cmd(
    ctx: click.Context,
    corpus_path: str,
    provider_name: str | None,
    model_name: str | None,
    concurrency: int | None,
    skill_path: str | None,
) -> None:
    """Execute a task corpus and record traces.

    Args:
        ctx: Click context.
        corpus_path: Path to the task corpus YAML.
        provider_name: Provider name override.
        model_name: Model name override.
        concurrency: Concurrency override.
        skill_path: Optional skill to load into system prompt.
    """
    console = ctx.obj["console"]
    config_path = ctx.obj.get("config_path")

    try:
        config = load_config(Path(config_path) if config_path else None)
    except SkillForgeError:
        # No config file is OK — use defaults
        config = Config()

    prov_name = provider_name or config.default_provider
    mdl_name = model_name or config.default_model
    conc = concurrency or config.concurrency

    corpus = load_corpus(Path(corpus_path))
    provider_cls = get_provider(prov_name)
    provider = provider_cls()

    skill = read_skill(Path(skill_path)) if skill_path else None

    run_dir = runs_dir(config.project_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    evaluator = ExactMatchEvaluator()

    async def _run() -> None:
        recorder = Recorder.open(run_dir / "pending")
        async with recorder:
            manifest = await run_corpus(
                corpus=corpus,
                provider=provider,
                model=mdl_name,
                skill=skill,
                concurrency=conc,
                recorder=recorder,
                evaluator=evaluator,
            )
        # Rename pending dir to run_id
        final_dir = run_dir / manifest.run_id
        (run_dir / "pending").rename(final_dir)
        # Rewrite manifest with correct paths
        manifest_path = final_dir / "manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        passed = sum(1 for r in manifest.task_results if r.passed)
        total = len(manifest.task_results)
        console.print(
            f"[green]✓[/green] Run complete: [bold]{manifest.run_id}[/bold] "
            f"({passed}/{total} passed)"
        )
        console.print(f"  Path: {final_dir}")

    try:
        asyncio.run(_run())
    except SkillForgeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
