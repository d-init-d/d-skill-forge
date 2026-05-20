"""Corpus runner orchestrating parallel task execution against an LLM provider."""

from __future__ import annotations

import asyncio
import traceback
from datetime import UTC, datetime
from pathlib import Path

from skillforge.evaluator.base import Evaluator  # noqa: TC001 - required at runtime
from skillforge.models.run import RunManifest, TaskResult
from skillforge.models.skill import Skill  # noqa: TC001 - required at runtime
from skillforge.models.task import Task, TaskCorpus  # noqa: TC001 - required at runtime
from skillforge.models.trace import ContentBlock, Message, Score, TokenUsage, Trace
from skillforge.paths import generate_ulid
from skillforge.providers.base import CompletionRequest, Provider
from skillforge.recorder import Recorder  # noqa: TC001 - required at runtime


async def run_corpus(
    corpus: TaskCorpus,
    provider: Provider,
    model: str,
    *,
    skill: Skill | None = None,
    concurrency: int = 8,
    recorder: Recorder,
    evaluator: Evaluator,
) -> RunManifest:
    """Execute a task corpus against a provider and record traces.

    Args:
        corpus: The task corpus to execute.
        provider: LLM provider to use.
        model: Model identifier.
        skill: Optional skill to prepend to system prompt.
        concurrency: Maximum parallel tasks.
        recorder: Trace recorder instance.
        evaluator: Evaluator for scoring traces.

    Returns:
        A RunManifest with all task results.
    """
    run_id = generate_ulid()
    started_at = datetime.now(tz=UTC)
    semaphore = asyncio.Semaphore(concurrency)

    async def _run_task(task: Task) -> TaskResult:
        async with semaphore:
            return await _execute_task(
                task=task,
                provider=provider,
                model=model,
                skill=skill,
                evaluator=evaluator,
                recorder=recorder,
                run_id=run_id,
            )

    task_results = await asyncio.gather(*[_run_task(t) for t in corpus.tasks])

    manifest = RunManifest(
        run_id=run_id,
        started_at=started_at,
        finished_at=datetime.now(tz=UTC),
        provider=provider.name,
        model=model,
        corpus_path=Path("tasks.yaml"),
        config_path=Path("skillforge.toml"),
        task_results=list(task_results),
    )

    await recorder.finalise(manifest)
    return manifest


async def _execute_task(
    *,
    task: Task,
    provider: Provider,
    model: str,
    skill: Skill | None,
    evaluator: Evaluator,
    recorder: Recorder,
    run_id: str,
) -> TaskResult:
    """Execute a single task, handling errors gracefully.

    Args:
        task: Task to execute.
        provider: LLM provider.
        model: Model identifier.
        skill: Optional skill for system prompt.
        evaluator: Evaluator for scoring.
        recorder: Trace recorder.
        run_id: Current run identifier.

    Returns:
        TaskResult for this task.
    """
    started_at = datetime.now(tz=UTC)
    error_msg: str | None = None
    final_output = ""
    usage = TokenUsage()
    messages: list[Message] = []

    system: str | None = None
    if skill:
        context_part = task.context or ""
        system = f"{skill.body}\n\n---\n\n{context_part}" if context_part else skill.body
    elif task.context:
        system = task.context

    user_message = Message(role="user", content=[ContentBlock(type="text", text=task.prompt)])
    messages.append(user_message)

    try:
        request = CompletionRequest(model=model, messages=[user_message], system=system)
        response = await provider.complete(request)

        for block in response.content:
            if block.type == "text" and block.text:
                final_output = block.text

        usage = response.usage
        messages.append(Message(role="assistant", content=response.content))
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"

    finished_at = datetime.now(tz=UTC)
    latency_ms = int((finished_at - started_at).total_seconds() * 1000)

    trace = Trace(
        run_id=run_id,
        task_id=task.id,
        provider=provider.name,
        model=model,
        started_at=started_at,
        finished_at=finished_at,
        latency_ms=latency_ms,
        messages=messages,
        final_output=final_output,
        usage=usage,
        error=error_msg,
    )

    score: Score | None = None
    if not error_msg:
        try:
            score = await evaluator.score(task, trace)
        except Exception:
            score = Score(passed=False, score=0.0, rationale="Evaluator error", evaluator="error")
    else:
        score = Score(passed=False, score=0.0, rationale="Task execution failed", evaluator="error")

    trace.score = score
    await recorder.record_trace(trace)

    return TaskResult(
        task_id=task.id,
        trace_path=Path(f"traces/{task.id}.jsonl"),
        passed=score.passed if score else False,
        score=score.score if score else 0.0,
    )
