"""Bootstrap confidence intervals for eval delta significance."""

from __future__ import annotations

import random
from pathlib import Path  # noqa: TC003 - required at runtime for write_delta_report

from pydantic import BaseModel, Field

from skillforge.models.run import RunManifest  # noqa: TC001 - required at runtime


class BootstrapResult(BaseModel):
    """Result of bootstrap confidence interval estimation.

    Attributes:
        mean_delta: Mean score delta (with_skill - baseline).
        ci_lower: Lower bound of confidence interval.
        ci_upper: Upper bound of confidence interval.
        confidence: Confidence level (e.g. 0.95).
        n_resamples: Number of bootstrap resamples performed.
        wins: Number of tasks where skill improved score.
        losses: Number of tasks where skill decreased score.
        ties: Number of tasks with no score change.
        significant: Whether CI excludes zero.
    """

    mean_delta: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_resamples: int
    wins: int
    losses: int
    ties: int
    significant: bool


class DeltaReport(BaseModel):
    """Full delta report with per-task breakdown and bootstrap stats.

    Attributes:
        baseline_score: Mean baseline score.
        with_skill_score: Mean with-skill score.
        delta: Mean delta.
        tasks_evaluated: Number of tasks.
        bootstrap: Bootstrap CI result.
        per_task: Per-task score breakdown.
    """

    baseline_score: float
    with_skill_score: float
    delta: float
    tasks_evaluated: int
    bootstrap: BootstrapResult
    per_task: list[dict[str, object]] = Field(default_factory=list)


def compute_bootstrap_delta(
    baseline: RunManifest,
    with_skill: RunManifest,
    *,
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int | None = None,
) -> DeltaReport:
    """Compute paired bootstrap CI on the score delta.

    Args:
        baseline: Run manifest without skill.
        with_skill: Run manifest with skill.
        n_resamples: Number of bootstrap resamples.
        confidence: Confidence level for the interval.
        seed: Optional random seed for reproducibility.

    Returns:
        A DeltaReport with bootstrap statistics.
    """
    rng = random.Random(seed)

    baseline_scores = {r.task_id: r.score for r in baseline.task_results}
    skill_scores = {r.task_id: r.score for r in with_skill.task_results}
    common_tasks = sorted(set(baseline_scores) & set(skill_scores))

    if not common_tasks:
        return DeltaReport(
            baseline_score=0.0,
            with_skill_score=0.0,
            delta=0.0,
            tasks_evaluated=0,
            bootstrap=BootstrapResult(
                mean_delta=0.0,
                ci_lower=0.0,
                ci_upper=0.0,
                confidence=confidence,
                n_resamples=n_resamples,
                wins=0,
                losses=0,
                ties=0,
                significant=False,
            ),
        )

    # Compute per-task deltas
    deltas = [skill_scores[t] - baseline_scores[t] for t in common_tasks]
    n = len(deltas)

    mean_delta = sum(deltas) / n
    b_avg = sum(baseline_scores[t] for t in common_tasks) / n
    s_avg = sum(skill_scores[t] for t in common_tasks) / n

    # Win/loss/tie
    wins = sum(1 for d in deltas if d > 0)
    losses = sum(1 for d in deltas if d < 0)
    ties = n - wins - losses

    # Bootstrap resampling
    bootstrap_means: list[float] = []
    for _ in range(n_resamples):
        sample = [rng.choice(deltas) for _ in range(n)]
        bootstrap_means.append(sum(sample) / n)

    bootstrap_means.sort()
    alpha = 1 - confidence
    lower_idx = int(alpha / 2 * n_resamples)
    upper_idx = int((1 - alpha / 2) * n_resamples) - 1
    ci_lower = bootstrap_means[max(0, lower_idx)]
    ci_upper = bootstrap_means[min(n_resamples - 1, upper_idx)]

    significant = ci_lower > 0 or ci_upper < 0

    per_task = [
        {
            "task_id": t,
            "baseline": baseline_scores[t],
            "with_skill": skill_scores[t],
            "delta": skill_scores[t] - baseline_scores[t],
        }
        for t in common_tasks
    ]

    return DeltaReport(
        baseline_score=b_avg,
        with_skill_score=s_avg,
        delta=mean_delta,
        tasks_evaluated=n,
        bootstrap=BootstrapResult(
            mean_delta=mean_delta,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            confidence=confidence,
            n_resamples=n_resamples,
            wins=wins,
            losses=losses,
            ties=ties,
            significant=significant,
        ),
        per_task=per_task,
    )


def write_delta_report(report: DeltaReport, path: Path) -> None:
    """Write delta report as JSON.

    Args:
        report: The delta report to write.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
