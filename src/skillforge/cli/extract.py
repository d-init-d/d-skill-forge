"""CLI command: skillforge extract — distill traces into a SKILL.md."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click

from skillforge.errors import ExtractionError, SkillForgeError
from skillforge.extractor import ReflectiveExtractor
from skillforge.providers import get_provider
from skillforge.recorder import load_run
from skillforge.skill_io import write as write_skill


@click.command("extract")
@click.option("--run", "run_path", type=click.Path(exists=True), required=True)
@click.option("--provider", "provider_name", type=str, default="mock")
@click.option("--model", "model_name", type=str, default="mock-strong")
@click.option("--out", "out_path", type=click.Path(), default=None)
@click.pass_context
def extract_cmd(
    ctx: click.Context,
    run_path: str,
    provider_name: str,
    model_name: str,
    out_path: str | None,
) -> None:
    """Extract a skill from recorded run traces.

    Args:
        ctx: Click context.
        run_path: Path to the run directory.
        provider_name: Provider for extraction LLM.
        model_name: Model for extraction.
        out_path: Output path for SKILL.md.
    """
    console = ctx.obj["console"]
    run_dir = Path(run_path)

    manifest, traces = load_run(run_dir)

    if not traces:
        console.print("[red]Error:[/red] No traces found in run directory.")
        ctx.exit(2)
        sys.exit(2)

    provider_cls = get_provider(provider_name)
    provider = provider_cls()
    extractor = ReflectiveExtractor()

    output = Path(out_path) if out_path else run_dir / "SKILL.md"

    async def _extract() -> None:
        skill = await extractor.extract(
            manifest=manifest,
            traces=traces,
            provider=provider,
            model=model_name,
        )
        write_skill(skill, output)

        # Record extraction trace
        extraction_log = run_dir / "extraction.jsonl"
        record = {
            "extractor": "reflective@0.1",
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
