"""Deep skill extractor using multi-pass knowledge extraction."""

from __future__ import annotations

from skillforge.errors import ExtractionError
from skillforge.models.run import RunManifest
from skillforge.models.skill import Skill
from skillforge.models.trace import ContentBlock, Message, Trace
from skillforge.paths import now_iso
from skillforge.providers.base import CompletionRequest, Provider
from skillforge.skill_io import parse

from ._prompts import DEEP_PASS1_REASONING, DEEP_PASS2_TOOLS, DEEP_PASS3_ERRORS, DEEP_PASS4_SYNTHESIS
from .base import Extractor
from .budget import allocate_budgets
from .formatter import format_trace_deep


class DeepExtractor(Extractor):
    """Multi-pass extractor for comprehensive knowledge distillation.

    Runs 4 extraction passes:
    1. Reasoning patterns & procedures
    2. Tool strategies & decision heuristics
    3. Error recovery & anti-patterns
    4. Synthesis into SKILL.md
    """

    async def extract(
        self,
        manifest: RunManifest,
        traces: list[Trace],
        provider: Provider,
        model: str,
        *,
        max_traces: int = 15,
    ) -> Skill:
        """Extract a skill using multi-pass deep analysis.

        Args:
            manifest: The run manifest.
            traces: All traces from the run.
            provider: LLM provider for extraction.
            model: Model identifier.
            max_traces: Maximum traces to analyze per pass.

        Returns:
            A distilled Skill artifact.

        Raises:
            ExtractionError: If extraction fails.
        """
        if not traces:
            msg = "No traces available for extraction"
            raise ExtractionError(msg)

        # Separate passed/failed
        passed = [t for t in traces if t.score and t.score.passed]
        failed = [t for t in traces if not t.score or not t.score.passed]

        # Select traces for each pass
        all_selected = self._select_traces(passed, failed, max_traces)
        budgets = allocate_budgets(all_selected)

        # Format traces with budgets
        all_formatted = [format_trace_deep(t, b) for t, b in zip(all_selected, budgets)]
        all_text = "\n\n---\n\n".join(all_formatted)

        # Format failed/success separately for pass 3
        failed_selected = failed[:max_traces // 3] if failed else []
        success_selected = passed[:max_traces // 3] if passed else []
        failed_budgets = allocate_budgets(failed_selected) if failed_selected else []
        success_budgets = allocate_budgets(success_selected) if success_selected else []
        failed_text = "\n\n---\n\n".join(
            format_trace_deep(t, b) for t, b in zip(failed_selected, failed_budgets)
        ) if failed_selected else "(no failed traces)"
        success_text = "\n\n---\n\n".join(
            format_trace_deep(t, b) for t, b in zip(success_selected, success_budgets)
        ) if success_selected else "(no successful traces)"

        # Pass 1: Reasoning & Procedures
        pass1 = await self._run_pass(
            provider, model,
            DEEP_PASS1_REASONING.format(traces_text=all_text),
        )

        # Pass 2: Tool Strategies & Heuristics
        pass2 = await self._run_pass(
            provider, model,
            DEEP_PASS2_TOOLS.format(traces_text=all_text),
        )

        # Pass 3: Error Recovery & Anti-Patterns
        pass3 = await self._run_pass(
            provider, model,
            DEEP_PASS3_ERRORS.format(traces_text=failed_text, success_traces=success_text),
        )

        # Pass 4: Synthesis
        passed_count = len(passed)
        failed_count = len(failed)
        synthesis_prompt = DEEP_PASS4_SYNTHESIS.format(
            pass1_output=pass1,
            pass2_output=pass2,
            pass3_output=pass3,
            model=manifest.model,
            domain="general",
            total_traces=len(traces),
            passed_count=passed_count,
            failed_count=failed_count,
            extracted_at=now_iso(),
        )
        skill_text = await self._run_pass(provider, model, synthesis_prompt)

        if not skill_text.strip():
            msg = "Deep extraction produced empty result"
            raise ExtractionError(msg)

        try:
            return parse(skill_text)
        except Exception as exc:
            msg = f"Failed to parse deep-extracted skill: {exc}"
            raise ExtractionError(msg) from exc

    async def _run_pass(self, provider: Provider, model: str, prompt: str) -> str:
        """Execute a single extraction pass.

        Args:
            provider: LLM provider.
            model: Model identifier.
            prompt: Pass prompt text.

        Returns:
            Model response text.
        """
        request = CompletionRequest(
            model=model,
            messages=[Message(role="user", content=[ContentBlock(type="text", text=prompt)])],
            temperature=0.2,
            max_tokens=8192,
        )
        response = await provider.complete(request)
        for block in response.content:
            if block.type == "text" and block.text:
                return block.text
        return ""

    def _select_traces(
        self, passed: list[Trace], failed: list[Trace], max_n: int
    ) -> list[Trace]:
        """Select traces with bias toward richest content.

        Args:
            passed: Passed traces.
            failed: Failed traces.
            max_n: Maximum total traces.

        Returns:
            Selected traces.
        """
        # Ensure at least 25% failed traces
        failed_budget = min(len(failed), max(1, max_n // 4))
        passed_budget = min(len(passed), max_n - failed_budget)

        # Sort by richness (traces with thinking/tools first)
        def richness(t: Trace) -> int:
            score = 0
            for m in t.messages:
                for b in m.content:
                    if b.type == "thinking":
                        score += 3
                    elif b.type == "tool_use":
                        score += 2
            return score

        passed_sorted = sorted(passed, key=richness, reverse=True)
        failed_sorted = sorted(failed, key=richness, reverse=True)

        return passed_sorted[:passed_budget] + failed_sorted[:failed_budget]
