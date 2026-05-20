"""CLI command: skillforge extract — distill traces into a SKILL.md."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click

from skillforge.errors import ExtractionError, SkillForgeError
from skillforge.extractor import ContrastiveExtractor, ReflectiveExtractor
from skillforge.providers import get_provider
from skillforge.recorder import load_run
from skillforge.skill_io import write as write_skill


@click.command("extract")
@click.option("--run", "run_path", type=click.Path(exists=True), default=None)
@click.option("--strategy", type=click.Choice(["reflective", "contrastive"]), default="reflective")
@click.option("--strong-run", "strong_run_path", type=click.Path(exists=True), default=None)
@click.option("--weak-run", "weak_run_path", type=click.Path(exists=True), default=None)
@click.option("--provider", "provider_name", type=str, default="mock")
@click.option("--model", "model_name", type=str, default="mock-strong")
@click.option("--out", "out_path", type=click.Path(), default=None)
@click.pass_context
def extract_cmd(
    ctx: click.Context,
    run_path: str | None,
    strategy: str,
    strong_run_path: str | None,
    weak_run_path: str | None,
    provider_name: str,
    model_name: str,
    out_path: str | None,
) -> None:
    """Extract a skill from recorded run traces.

    Args:
        ctx: Click context.
        run_path: Path to the run directory (reflective mode).
        strategy: Extraction strategy (reflective or contrastive).
        strong_run_path: Path to strong run (contrastive mode).
        weak_run_path: Path to weak run (contrastive mode).
        provider_name: Provider for extraction LLM.
        model_name: Model for extraction.
        out_path: Output path for SKILL.md.
    """
    console = ctx.obj["console"]

    # Validate options based on strategy
    if strategy == "contrastive":
        if not strong_run_path or not weak_run_path:
            console.print(
                "[red]Error:[/red] --strong-run and --weak-run are required "
                "for contrastive strategy."
            )
            ctx.exit(2)
            sys.exit(2)
        strong_dir = Path(strong_run_path)
        weak_dir = Path(weak_run_path)
        manifest, traces = load_run(strong_dir)
        weak_manifest, weak_traces = load_run(weak_dir)
        output = Path(out_path) if out_path else strong_dir / "SKILL.md"
    else:
        if not run_path:
            console.print("[red]Error:[/red] --run is required for reflective strategy.")
            ctx.exit(2)
            sys.exit(2)
        run_dir = Path(run_path)
        manifest, traces = load_run(run_dir)
        weak_manifest = None
        weak_traces = None
        output = Path(out_path) if out_path else run_dir / "SKILL.md"

    if not traces:
        console.print("[red]Error:[/red] No traces found in run directory.")
        ctx.exit(2)
        sys.exit(2)

    provider_cls = get_provider(provider_name)
    provider = provider_cls()

    async def _extract() -> None:
        if strategy == "contrastive":
            extractor = ContrastiveExtractor()
            skill = await extractor.extract(
                manifest=manifest,
                traces=traces,
                provider=provider,
                model=model_name,
                weak_manifest=weak_manifest,
                weak_traces=weak_traces,
            )
        else:
            extractor = ReflectiveExtractor()
            skill = await extractor.extract(
                manifest=manifest,
                traces=traces,
                provider=provider,
                model=model_name,
            )
        write_skill(skill, output)

        # Record extraction trace
        log_dir = Path(strong_run_path) if strategy == "contrastive" else Path(run_path)  # type: ignore[arg-type]
        extraction_log = log_dir / "extraction.jsonl"
        record = {
            "extractor": f"{strategy}@0.1",
            "model": model_name,
            "provider": provider_name,
            "traces_used": len(traces),
            "output_path": str(output),
        }
        with extraction_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        console.print(f"[green]✓[/green] Skill extracted to [bold]{output}[/bold]")

    try:
        asyncio.run(_extract())
    except ExtractionError as e:
        console.print(f"[red]Extraction failed:[/red] {e}")
        ctx.exit(2)
        sys.exit(2)
    except SkillForgeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
