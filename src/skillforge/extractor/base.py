"""Abstract base class for skill extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from skillforge.models.run import RunManifest  # noqa: TC001 - required at runtime
from skillforge.models.skill import Skill  # noqa: TC001 - required at runtime
from skillforge.models.trace import Trace  # noqa: TC001 - required at runtime
from skillforge.providers.base import Provider  # noqa: TC001 - required at runtime


class Extractor(ABC):
    """Abstract extractor that distills traces into a Skill artifact."""

    @abstractmethod
    async def extract(
        self,
        manifest: RunManifest,
        traces: list[Trace],
        provider: Provider,
        model: str,
    ) -> Skill:
        """Extract a skill from run traces.

        Args:
            manifest: The run manifest.
            traces: Traces from the run.
            provider: LLM provider for extraction.
            model: Model identifier.

        Returns:
            A distilled Skill artifact.
        """
