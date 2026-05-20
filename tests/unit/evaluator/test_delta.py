# ruff: noqa: D101, D102, PLR2004
"""Tests for compute_bootstrap_delta and write_delta_report."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from skillforge.evaluator.delta import DeltaReport, compute_bootstrap_delta, write_delta_report
from skillforge.models.run import RunManifest, TaskResult


def _make_manifest(
    run_id: str, task_scores: dict[str, float], *, skill: bool = False
) -> RunManifest:
    results = [
        TaskResult(
            task_id=tid,
            trace_path=Path(f"traces/{tid}.jsonl"),
            passed=score >= 0.5,
            score=score,
        )
        for tid, score in task_scores.items()
    ]
    return RunManifest(
        run_id=run_id,
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
        provider="mock",
        model="mock-strong",
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
        skill_loaded=Path("skill.md") if skill else None,
        task_results=results,
    )


class TestIdenticalScores:
    def test_ci_is_zero_and_not_significant(self) -> None:
        scores = {"t1": 0.8, "t2": 0.6, "t3": 0.7}
        baseline = _make_manifest("r1", scores)
        with_skill = _make_manifest("r2", scores, skill=True)

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        assert report.bootstrap.ci_lower == 0.0
        assert report.bootstrap.ci_upper == 0.0
        assert report.bootstrap.significant is False


class TestAllWins:
    def test_significant_positive(self) -> None:
        baseline = _make_manifest("r1", {"t1": 0.0, "t2": 0.0, "t3": 0.0, "t4": 0.0, "t5": 0.0})
        with_skill = _make_manifest(
            "r2", {"t1": 1.0, "t2": 1.0, "t3": 1.0, "t4": 1.0, "t5": 1.0}, skill=True
        )

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        assert report.bootstrap.significant is True
        assert report.bootstrap.ci_lower > 0


class TestAllLosses:
    def test_significant_negative(self) -> None:
        baseline = _make_manifest("r1", {"t1": 1.0, "t2": 1.0, "t3": 1.0, "t4": 1.0, "t5": 1.0})
        with_skill = _make_manifest(
            "r2", {"t1": 0.0, "t2": 0.0, "t3": 0.0, "t4": 0.0, "t5": 0.0}, skill=True
        )

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        assert report.bootstrap.significant is True
        assert report.bootstrap.ci_upper < 0


class TestEmptyCommonTasks:
    def test_delta_zero_n_zero(self) -> None:
        baseline = _make_manifest("r1", {"t1": 0.5})
        with_skill = _make_manifest("r2", {"t99": 0.9}, skill=True)

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        assert report.delta == 0.0
        assert report.tasks_evaluated == 0


class TestSingleTask:
    def test_ci_equals_delta(self) -> None:
        baseline = _make_manifest("r1", {"t1": 0.3})
        with_skill = _make_manifest("r2", {"t1": 0.8}, skill=True)

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        assert report.delta == pytest.approx(0.5)
        # With a single task, all bootstrap samples are the same value
        assert report.bootstrap.ci_lower == pytest.approx(0.5)
        assert report.bootstrap.ci_upper == pytest.approx(0.5)


class TestDeterminism:
    def test_same_seed_same_result(self) -> None:
        baseline = _make_manifest("r1", {"t1": 0.2, "t2": 0.4, "t3": 0.6})
        with_skill = _make_manifest("r2", {"t1": 0.5, "t2": 0.3, "t3": 0.9}, skill=True)

        r1 = compute_bootstrap_delta(baseline, with_skill, seed=123)
        r2 = compute_bootstrap_delta(baseline, with_skill, seed=123)
        assert r1.bootstrap.ci_lower == r2.bootstrap.ci_lower
        assert r1.bootstrap.ci_upper == r2.bootstrap.ci_upper
        assert r1.bootstrap.mean_delta == r2.bootstrap.mean_delta


class TestWriteDeltaReport:
    def test_json_round_trip(self, tmp_path: Path) -> None:
        baseline = _make_manifest("r1", {"t1": 0.3, "t2": 0.7})
        with_skill = _make_manifest("r2", {"t1": 0.8, "t2": 0.9}, skill=True)

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        out_path = tmp_path / "delta.json"
        write_delta_report(report, out_path)

        loaded = json.loads(out_path.read_text(encoding="utf-8"))
        roundtrip = DeltaReport.model_validate(loaded)
        assert roundtrip.delta == report.delta
        assert roundtrip.bootstrap.ci_lower == report.bootstrap.ci_lower


class TestPerTaskKeys:
    def test_per_task_has_correct_keys(self) -> None:
        baseline = _make_manifest("r1", {"t1": 0.3, "t2": 0.7})
        with_skill = _make_manifest("r2", {"t1": 0.8, "t2": 0.9}, skill=True)

        report = compute_bootstrap_delta(baseline, with_skill, seed=42)
        assert len(report.per_task) == 2
        for entry in report.per_task:
            assert entry.task_id
            assert isinstance(entry.baseline, float)
            assert isinstance(entry.with_skill, float)
            assert isinstance(entry.delta, float)
