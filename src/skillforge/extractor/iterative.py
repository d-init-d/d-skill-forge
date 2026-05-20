"""Iterative skill extractor that refines output over multiple rounds."""

from __future__ import annotations

from skillforge.errors import ExtractionError
from skillforge.models.run import RunManifest  # noqa: TC001 - required at runtime
from skillforge.models.skill import Skill  # noqa: TC001 - required at runtime
from skillforge.models.trace import ContentBlock, Message, Trace
from skillforge.providers.base import CompletionRequest, Provider
from skillforge.skill_io import dump, parse

from ._prompts import ITERATIVE_EXTRACTION_MARKER, ITERATIVE_REFINEMENT_PROMPT_V1
from .base import Extractor
from .reflective import ReflectiveExtractor


class IterativeExtractor(Extractor):
    """Extracts skills via iterative refinement over multiple rounds."""

    def __init__(self, max_rounds: int = 3) -> None:
        """Initialize with the maximum number of refinement rounds.

        Args:
            max_rounds: Maximum extraction rounds (1 = reflective only).
        """
        self._max_rounds = max_rounds

    async def extract(
        self,
        manifest: RunManifest,
        traces: list[Trace],
        provider: Provider,
        model: str,
        **kwargs: object,
    ) -> Skill:
        """Extract a skill using iterative refinement.

        Round 1 uses ReflectiveExtractor. Subsequent rounds refine the draft
        until convergence or max_rounds is reached.

        Args:
            manifest: The run manifest.
            traces: Traces from the run.
            provider: LLM provider for extraction.
            model: Model identifier.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            A distilled Skill artifact.

        Raises:
            ExtractionError: If extraction or parsing fails.
        """
        if not traces:
            msg = "Iterative extraction requires at least one trace"
            raise ExtractionError(msg)

        # Round 1: reflective extraction
        reflective = ReflectiveExtractor()
        skill = await reflective.extract(manifest, traces, provider, model)
        prev_text = dump(skill)

        # Rounds 2..N: iterative refinement
        traces_text = self._format_traces_for_refinement(traces)

        for _ in range(1, self._max_rounds):
            prompt_text = ITERATIVE_REFINEMENT_PROMPT_V1.format(
                marker=ITERATIVE_EXTRACTION_MARKER,
                current_skill=prev_text,
                traces_text=traces_text,
            )

            request = CompletionRequest(
                model=model,
                messages=[
                    Message(role="user", content=[ContentBlock(type="text", text=prompt_text)])
                ],
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
                break

            try:
                new_skill = parse(text)
            except Exception:
                break

            new_text = dump(new_skill)

            # Early stop if output is byte-identical
            if new_text == prev_text:
                break

            skill = new_skill
            prev_text = new_text

        return skill

    def _format_traces_for_refinement(self, traces: list[Trace]) -> str:
        """Format traces into text for the refinement prompt.

        Args:
            traces: Traces to format.

        Returns:
            Formatted text representation.
        """
        parts: list[str] = []
        for i, trace in enumerate(traces[:10], 1):
            status = "PASSED" if (trace.score and trace.score.passed) else "FAILED"
            parts.append(f"### Trace {i} [{status}] (task: {trace.task_id})")
            parts.append(f"Output: {trace.final_output[:300]}")
            parts.append("")
        return "\n".join(parts)
