"""LLM-based judge evaluator for subjective scoring."""

from __future__ import annotations

import json

from skillforge.errors import EvaluationError
from skillforge.models.task import Task  # noqa: TC001 - required at runtime
from skillforge.models.trace import ContentBlock, Message, Score, Trace
from skillforge.providers.base import CompletionRequest, Provider

from .base import Evaluator

_JUDGE_SYSTEM = (
    "You are an evaluation judge. Score the assistant's output against the rubric.\n"
    'Respond with ONLY a JSON object: {"passed": bool, "score": float, "rationale": str}\n'
    "score must be between 0.0 and 1.0. passed is true if score >= 0.7."
)


class LLMJudgeEvaluator(Evaluator):
    """Evaluator that uses an LLM to judge output quality against a rubric."""

    def __init__(self, provider: Provider, model: str) -> None:
        """Initialize with a provider and model for judging.

        Args:
            provider: LLM provider instance.
            model: Model identifier.
        """
        self._provider = provider
        self._model = model

    async def score(self, task: Task, trace: Trace) -> Score:
        """Score a trace using an LLM judge.

        Args:
            task: The task with judge_rubric in expected outcome.
            trace: The trace to evaluate.

        Returns:
            Score from the LLM judge.

        Raises:
            EvaluationError: If the judge response cannot be parsed.
        """
        rubric = task.expected.judge_rubric or ""
        prompt = (
            f"## Rubric\n{rubric}\n\n"
            f"## Task Prompt\n{task.prompt}\n\n"
            f"## Assistant Output\n{trace.final_output}"
        )

        request = CompletionRequest(
            model=self._model,
            system=_JUDGE_SYSTEM,
            messages=[Message(role="user", content=[ContentBlock(type="text", text=prompt)])],
            temperature=0.0,
            max_tokens=512,
        )

        response = await self._provider.complete(request)

        text = ""
        for block in response.content:
            if block.type == "text" and block.text:
                text = block.text
                break

        try:
            data = json.loads(text)
            passed = bool(data["passed"])
            score_val = float(data["score"])
            rationale = str(data.get("rationale", ""))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            msg = f"Failed to parse judge response: {text[:200]}"
            raise EvaluationError(msg) from exc

        return Score(
            passed=passed,
            score=max(0.0, min(1.0, score_val)),
            rationale=rationale,
            evaluator=f"llm_judge:{self._model}",
        )
