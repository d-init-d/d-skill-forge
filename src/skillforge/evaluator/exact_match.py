"""Deterministic evaluators: exact, contains, regex, executes_ok."""

from __future__ import annotations

import asyncio
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from skillforge.models.task import Task  # noqa: TC001 - required at runtime
from skillforge.models.trace import Score, Trace

from .base import Evaluator


class ExactMatchEvaluator(Evaluator):
    """Evaluator handling exact, contains, regex, and executes_ok strategies."""

    async def score(self, task: Task, trace: Trace) -> Score:
        """Score a trace using deterministic matching strategies.

        Args:
            task: The task with expected outcome.
            trace: The trace to evaluate.

        Returns:
            Score with pass/fail and rationale.
        """
        expected = task.expected
        output = trace.final_output

        if expected.kind == "exact":
            passed = output.strip() == (expected.value or "")
            return Score(
                passed=passed,
                score=1.0 if passed else 0.0,
                rationale=f"Exact match: {'yes' if passed else 'no'}",
                evaluator="exact_match",
            )

        if expected.kind == "contains":
            value = expected.value or ""
            passed = value in output
            return Score(
                passed=passed,
                score=1.0 if passed else 0.0,
                rationale=f"Contains '{value}': {'yes' if passed else 'no'}",
                evaluator="contains",
            )

        if expected.kind == "regex":
            pattern = expected.value or ""
            passed = re.search(pattern, output) is not None
            return Score(
                passed=passed,
                score=1.0 if passed else 0.0,
                rationale=f"Regex '{pattern}': {'match' if passed else 'no match'}",
                evaluator="regex",
            )

        if expected.kind == "executes_ok":
            return await self._eval_executes_ok(output)

        return Score(
            passed=False,
            score=0.0,
            rationale=f"Unsupported kind: {expected.kind}",
            evaluator="exact_match",
        )

    async def _eval_executes_ok(self, code: str) -> Score:
        """Run code as a Python script and check exit code.

        Args:
            code: Python source code to execute.

        Returns:
            Score based on whether execution succeeds.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            script_path = Path(f.name)

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            except TimeoutError:
                proc.kill()
                await proc.communicate()
                return Score(
                    passed=False,
                    score=0.0,
                    rationale="Execution timed out (5s)",
                    evaluator="executes_ok",
                )

            passed = proc.returncode == 0
            rationale = "Execution succeeded" if passed else f"Exit code {proc.returncode}"
            if not passed and stderr:
                rationale += f": {stderr.decode(errors='replace')[:200]}"
            return Score(
                passed=passed,
                score=1.0 if passed else 0.0,
                rationale=rationale,
                evaluator="executes_ok",
            )
        finally:
            script_path.unlink(missing_ok=True)
