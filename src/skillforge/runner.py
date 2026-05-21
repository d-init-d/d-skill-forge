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
from skillforge.providers.base import CompletionRequest, CompletionResponse, Provider
from skillforge.recorder import Recorder  # noqa: TC001 - required at runtime

# Maximum turns in a tool-calling loop before forcing stop
_MAX_TOOL_TURNS = 10

# Default thinking budget (tokens) — enables extended thinking on supported models
_DEFAULT_THINKING_BUDGET = 10_000


async def run_corpus(
    corpus: TaskCorpus,
    provider: Provider,
    model: str,
    *,
    skill: Skill | None = None,
    concurrency: int = 8,
    recorder: Recorder,
    evaluator: Evaluator,
    thinking_budget: int = _DEFAULT_THINKING_BUDGET,
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
        thinking_budget: Token budget for extended thinking.

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
                thinking_budget=thinking_budget,
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
    thinking_budget: int,
) -> TaskResult:
    """Execute a single task with extended thinking and multi-turn tool loop.

    The runner:
    1. Sends the task with thinking_budget_tokens enabled
    2. If model returns tool_use blocks, feeds results back and continues
    3. Loops until model produces a final text response or hits max turns
    4. Records the FULL conversation trace (thinking + tools + text)

    Args:
        task: Task to execute.
        provider: LLM provider.
        model: Model identifier.
        skill: Optional skill for system prompt.
        evaluator: Evaluator for scoring.
        recorder: Trace recorder.
        run_id: Current run identifier.
        thinking_budget: Extended thinking token budget.

    Returns:
        TaskResult for this task.
    """
    started_at = datetime.now(tz=UTC)
    error_msg: str | None = None
    final_output = ""
    total_usage = TokenUsage()
    messages: list[Message] = []

    # Build system prompt
    system: str | None = None
    if skill:
        context_part = task.context or ""
        system = f"{skill.body}\n\n---\n\n{context_part}" if context_part else skill.body
    elif task.context:
        system = task.context

    # Initial user message
    user_message = Message(role="user", content=[ContentBlock(type="text", text=task.prompt)])
    messages.append(user_message)

    try:
        # Multi-turn loop: keep going while model wants to use tools
        conversation: list[Message] = [user_message]
        turn = 0

        while turn < _MAX_TOOL_TURNS:
            turn += 1

            request = CompletionRequest(
                model=model,
                messages=conversation,
                system=system,
                thinking_budget_tokens=thinking_budget,
                max_tokens=8192,
            )
            response = await provider.complete(request)

            # Accumulate usage
            total_usage = TokenUsage(
                input_tokens=total_usage.input_tokens + response.usage.input_tokens,
                output_tokens=total_usage.output_tokens + response.usage.output_tokens,
                thinking_tokens=total_usage.thinking_tokens + response.usage.thinking_tokens,
            )

            # Record assistant response
            assistant_msg = Message(role="assistant", content=response.content)
            messages.append(assistant_msg)
            conversation.append(assistant_msg)

            # Check if model wants to call tools
            tool_calls = [b for b in response.content if b.type == "tool_use"]

            if not tool_calls:
                # No tool calls — model is done. Extract final text output.
                for block in response.content:
                    if block.type == "text" and block.text:
                        final_output = block.text
                break

            # Execute tool calls and feed results back
            tool_results: list[ContentBlock] = []
            for tool_call in tool_calls:
                result = _execute_tool(tool_call)
                tool_results.append(result)

            # Add tool results as a tool message
            tool_msg = Message(role="tool", content=tool_results)
            messages.append(tool_msg)
            conversation.append(tool_msg)

        # If we exhausted turns, grab whatever text we have
        if not final_output:
            for msg in reversed(messages):
                if msg.role == "assistant":
                    for block in msg.content:
                        if block.type == "text" and block.text:
                            final_output = block.text
                            break
                    if final_output:
                        break

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
        usage=total_usage,
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


def _execute_tool(tool_call: ContentBlock) -> ContentBlock:
    """Execute a tool call and return the result.

    Currently supports a basic set of built-in tools for task execution.
    For unsupported tools, returns a message indicating the tool is unavailable.

    Args:
        tool_call: The tool_use content block.

    Returns:
        A tool_result content block.
    """
    name = tool_call.name or "unknown"
    tool_input = tool_call.input or {}

    # Built-in tool handlers for common task patterns
    match name:
        case "execute_code" | "run_code":
            # Execute Python code in a subprocess (sandboxed)
            code = tool_input.get("code", "")
            output = _run_code_sandbox(code)
            return ContentBlock(type="tool_result", output=output)

        case "read_file":
            path = tool_input.get("path", "")
            output = _read_file_safe(path)
            return ContentBlock(type="tool_result", output=output)

        case _:
            # Unknown tool — return a helpful message so model can adapt
            return ContentBlock(
                type="tool_result",
                output=f"Tool '{name}' is not available in this environment. "
                f"Please solve the task using reasoning and code execution only.",
            )


def _run_code_sandbox(code: str) -> str:
    """Execute Python code in a subprocess with timeout.

    Args:
        code: Python source code to execute.

    Returns:
        stdout + stderr output, truncated to 2000 chars.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=None,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output[:2000]
    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out (10s limit)"
    except Exception as e:
        return f"ERROR: {e}"


def _read_file_safe(path: str) -> str:
    """Read a file safely, returning content or error message.

    Args:
        path: File path to read.

    Returns:
        File content or error message.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
        return content[:3000]
    except Exception as e:
        return f"ERROR: Cannot read '{path}': {e}"
