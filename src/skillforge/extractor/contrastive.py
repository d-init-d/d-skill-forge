"""Contrastive skill extractor comparing strong vs weak model traces."""

from __future__ import annotations

from skillforge.errors import ExtractionError
from skillforge.models.run import RunManifest  # noqa: TC001 - required at runtime
from skillforge.models.skill import Skill  # noqa: TC001 - required at runtime
from skillforge.models.trace import ContentBlock, Message, Trace
from skillforge.paths import now_iso
from skillforge.providers.base import CompletionRequest, Provider
from skillforge.skill_io import parse

from ._prompts import CONTRASTIVE_EXTRACTION_MARKER, CONTRASTIVE_EXTRACTION_PROMPT_V1
from .base import Extractor


class ContrastiveExtractor(Extractor):
    """Extracts skills by contrasting strong vs weak model traces on the same tasks."""

    async def extract(
        self,
        manifest: RunManifest,
        traces: list[Trace],
        provider: Provider,
        model: str,
        *,
        weak_manifest: RunManifest | None = None,
        weak_traces: list[Trace] | None = None,
    ) -> Skill:
        """Extract a skill by contrasting strong and weak traces.

        Args:
            manifest: The strong run manifest.
            traces: Strong model traces.
            provider: LLM provider for extraction.
            model: Model identifier for extraction.
            weak_manifest: The weak run manifest.
            weak_traces: Weak model traces.

        Returns:
            A distilled Skill artifact.

        Raises:
            ExtractionError: If extraction or parsing fails.
        """
        if not weak_manifest or not weak_traces:
            msg = "Contrastive extraction requires --weak-run"
            raise ExtractionError(msg)

        pairs = self._build_pairs(traces, weak_traces)
        if not pairs:
            msg = "No matching task pairs found between strong and weak runs"
            raise ExtractionError(msg)

        strong_passed = sum(1 for s, _ in pairs if s.score and s.score.passed)
        weak_passed = sum(1 for _, w in pairs if w.score and w.score.passed)

        pairs_text = self._format_pairs(pairs)

        prompt_text = CONTRASTIVE_EXTRACTION_PROMPT_V1.format(
            marker=CONTRASTIVE_EXTRACTION_MARKER,
            strong_run_id=manifest.run_id,
            strong_model=manifest.model,
            weak_run_id=weak_manifest.run_id,
            weak_model=weak_manifest.model,
            domain="general",
            total_pairs=len(pairs),
            strong_passed=strong_passed,
            weak_passed=weak_passed,
            pairs_text=pairs_text,
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
            msg = "Contrastive extraction produced empty response"
            raise ExtractionError(msg)

        try:
            return parse(text)
        except Exception as exc:
            msg = f"Failed to parse extracted skill: {exc}"
            raise ExtractionError(msg) from exc

    def _build_pairs(self, strong: list[Trace], weak: list[Trace]) -> list[tuple[Trace, Trace]]:
        """Match traces by task_id to form comparison pairs.

        Args:
            strong: Strong model traces.
            weak: Weak model traces.

        Returns:
            List of (strong_trace, weak_trace) pairs matched by task_id.
        """
        weak_by_task = {t.task_id: t for t in weak}
        pairs: list[tuple[Trace, Trace]] = []
        for s_trace in strong:
            w_trace = weak_by_task.get(s_trace.task_id)
            if w_trace:
                pairs.append((s_trace, w_trace))
        return pairs

    def _format_pairs(self, pairs: list[tuple[Trace, Trace]]) -> str:
        """Format trace pairs into text for the prompt.

        Args:
            pairs: List of (strong, weak) trace pairs.

        Returns:
            Formatted text representation.
        """
        parts: list[str] = []
        for i, (strong, weak) in enumerate(pairs, 1):
            s_status = "PASSED" if (strong.score and strong.score.passed) else "FAILED"
            w_status = "PASSED" if (weak.score and weak.score.passed) else "FAILED"
            parts.append(f"### Pair {i} (task: {strong.task_id})")
            parts.append(f"**Strong [{s_status}]:** {strong.final_output[:300]}")
            parts.append(f"**Weak [{w_status}]:** {weak.final_output[:300]}")
            if weak.error:
                parts.append(f"Weak error: {weak.error}")
            parts.append("")
        return "\n".join(parts)
