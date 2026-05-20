"""Run-level evaluation and comparison utilities."""

from __future__ import annotations

from pydantic import BaseModel

from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.task import TaskCorpus  # noqa: TC001 - required at runtime
from skillforge.models.trace import Trace  # noqa: TC001 - required at runtime

from .base import Evaluator  # noqa: TC001 - required at runtime


class EvalDelta(BaseModel):
    """Comparison result between baseline and skill-augmented runs.

    Attributes:
        baseline_score: Average score without skill.
        with_skill_score: Average score with skill loaded.
        delta: Difference (with_skill_score - baseline_score).
        tasks_evaluated: Number of tasks compared.
    """

    baseline_score: float
    with_skill_score: float
    delta: float
    tasks_evaluated: int


async def evaluate_run(
    manifest: RunManifest,
    traces: list[Trace],
    corpus: TaskCorpus,
    evaluator: Evaluator,
) -> RunManifest:
    """Re-evaluate all traces in a run and update the manifest.

    Args:
        manifest: The run manifest to update.
        traces: All traces from the run.
        corpus: The task corpus for looking up task definitions.
        evaluator: The evaluator to use for scoring.

    Returns:
        Updated manifest with new task_results.
    """
    task_map = {t.id: t for t in corpus.tasks}
    results: list[TaskResult] = []

    for trace in traces:
        task = task_map.get(trace.task_id)
        if task is None:
            continue

        score = await evaluator.score(task, trace)
        trace.score = score

        results.append(
            TaskResult(
                task_id=trace.task_id,
                trace_path=manifest.corpus_path.parent / "traces" / f"{trace.task_id}.jsonl",
                passed=score.passed,
                score=score.score,
            )
        )

    manifest.task_results = results
    return manifest


def compare_runs(baseline: RunManifest, with_skill: RunManifest) -> EvalDelta:
    """Compare two run manifests and compute the score delta.

    Args:
        baseline: Run without skill loaded.
        with_skill: Run with skill loaded.

    Returns:
        EvalDelta with score comparison.
    """
    baseline_scores = {r.task_id: r.score for r in baseline.task_results}
    skill_scores = {r.task_id: r.score for r in with_skill.task_results}

    common_tasks = set(baseline_scores) & set(skill_scores)
    if not common_tasks:
        return EvalDelta(
            baseline_score=0.0,
            with_skill_score=0.0,
            delta=0.0,
            tasks_evaluated=0,
        )

    n = len(common_tasks)
    b_avg = sum(baseline_scores[t] for t in common_tasks) / n
    s_avg = sum(skill_scores[t] for t in common_tasks) / n

    return EvalDelta(
        baseline_score=b_avg,
        with_skill_score=s_avg,
        delta=s_avg - b_avg,
        tasks_evaluated=n,
    )
