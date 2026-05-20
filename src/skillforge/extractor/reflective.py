"""Reflective skill extractor using stratified trace sampling."""

from __future__ import annotations

from skillforge.errors import ExtractionError
from skillforge.models.run import RunManifest  # noqa: TC001 - required at runtime
from skillforge.models.skill import Skill  # noqa: TC001 - required at runtime
from skillforge.models.trace import ContentBlock, Message, Trace
from skillforge.paths import now_iso
from skillforge.providers.base import CompletionRequest, Provider
from skillforge.skill_io import parse

from ._prompts import REFLECTIVE_EXTRACTION_PROMPT_V1
from .base import Extractor


class ReflectiveExtractor(Extractor):
    """Extracts skills via reflective distillation of execution traces."""

    async def extract(
        self,
        manifest: RunManifest,
        traces: list[Trace],
        provider: Provider,
        model: str,
        *,
        max_traces_per_pass: int = 20,
    ) -> Skill:
        """Extract a skill using stratified sampling and reflective prompting.

        Args:
            manifest: The run manifest.
            traces: All traces from the run.
            provider: LLM provider for extraction.
            model: Model identifier.
            max_traces_per_pass: Maximum traces to include in prompt.

        Returns:
            A distilled Skill artifact.

        Raises:
            ExtractionError: If extraction or parsing fails.
        """
        sampled = self._stratified_sample(traces, max_traces_per_pass)
        passed_count = sum(1 for t in sampled if t.score and t.score.passed)
        failed_count = len(sampled) - passed_count

        traces_text = self._format_traces(sampled)

        prompt_text = REFLECTIVE_EXTRACTION_PROMPT_V1.format(
            run_id=manifest.run_id,
            model=model,
            domain="general",
            total_traces=len(sampled),
            passed_count=passed_count,
            failed_count=failed_count,
            traces_text=traces_text,
            extracted_at=now_iso(),
        )

        request = CompletionRequest(
            model=model,
            messages=[Message(role="user", content=[ContentBlock(type="text", text=prompt_text)])],
            temperature=0.3,
            max_tokens=8192,
        )

        response = await provider.complete(request)

        text = ""
        for block in response.content:
            if block.type == "text" and block.text:
                text = block.text
                break

        if not text.strip():
            msg = "Extraction produced empty response"
            raise ExtractionError(msg)

        try:
            return parse(text)
        except Exception as exc:
            msg = f"Failed to parse extracted skill: {exc}"
            raise ExtractionError(msg) from exc

    def _stratified_sample(self, traces: list[Trace], max_n: int) -> list[Trace]:
        """Sample traces with bias toward passed, ensuring >=25% failed when available.

        Args:
            traces: All available traces.
            max_n: Maximum number to sample.

        Returns:
            Stratified sample of traces.
        """
        if len(traces) <= max_n:
            return traces

        passed = [t for t in traces if t.score and t.score.passed]
        failed = [t for t in traces if not t.score or not t.score.passed]

        failed_budget = min(len(failed), max(1, max_n // 4))
        passed_budget = max_n - failed_budget

        if len(passed) < passed_budget:
            passed_budget = len(passed)
            failed_budget = min(len(failed), max_n - passed_budget)

        return passed[:passed_budget] + failed[:failed_budget]

    def _format_traces(self, traces: list[Trace]) -> str:
        """Format traces into a text block for the prompt.

        Args:
            traces: Traces to format.

        Returns:
            Formatted text representation.
        """
        parts: list[str] = []
        for i, trace in enumerate(traces, 1):
            status = "PASSED" if (trace.score and trace.score.passed) else "FAILED"
            parts.append(f"### Trace {i} [{status}] (task: {trace.task_id})")
            parts.append(f"Output: {trace.final_output[:500]}")
            if trace.error:
                parts.append(f"Error: {trace.error}")
            parts.append("")
        return "\n".join(parts)
