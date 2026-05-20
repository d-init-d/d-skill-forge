"""Trace recording and persistence for run artifacts."""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003 - used at runtime in function bodies
from typing import TYPE_CHECKING

from skillforge.errors import TraceError
from skillforge.models.run import RunManifest
from skillforge.models.trace import Trace

if TYPE_CHECKING:
    from types import TracebackType


class Recorder:
    """Async context manager that records traces to disk.

    Usage:
        async with Recorder.open(run_dir) as recorder:
            await recorder.record_trace(trace)
            await recorder.finalise(manifest)
    """

    def __init__(self, run_dir: Path) -> None:
        """Initialise recorder with target directory.

        Args:
            run_dir: Directory where traces and manifest are written.
        """
        self._run_dir = run_dir
        self._traces_dir = run_dir / "traces"

    @classmethod
    def open(cls, run_dir: Path) -> Recorder:
        """Create a Recorder targeting the given run directory.

        Args:
            run_dir: Directory to write run artifacts into.

        Returns:
            A Recorder instance ready to be used as an async context manager.
        """
        return cls(run_dir)

    async def __aenter__(self) -> Recorder:
        """Enter the async context, creating directories."""
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._traces_dir.mkdir(parents=True, exist_ok=True)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context."""

    async def record_trace(self, trace: Trace) -> None:
        """Append a trace as a JSON line to the task's trace file.

        Args:
            trace: The trace to record.

        Raises:
            TraceError: If writing fails.
        """
        trace_file = self._traces_dir / f"{trace.task_id}.jsonl"
        try:
            with trace_file.open("a", encoding="utf-8") as f:
                f.write(trace.model_dump_json() + "\n")
        except OSError as exc:
            msg = f"Failed to write trace for task '{trace.task_id}': {exc}"
            raise TraceError(msg) from exc

    async def finalise(self, manifest: RunManifest) -> None:
        """Write the run manifest to disk.

        Args:
            manifest: The run manifest to persist.

        Raises:
            TraceError: If writing fails.
        """
        manifest_path = self._run_dir / "manifest.json"
        try:
            manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        except OSError as exc:
            msg = f"Failed to write manifest: {exc}"
            raise TraceError(msg) from exc


def load_run(run_dir: Path) -> tuple[RunManifest, list[Trace]]:
    """Load a run manifest and all traces from disk.

    Args:
        run_dir: Directory containing manifest.json and traces/.

    Returns:
        A tuple of (manifest, list of traces).

    Raises:
        TraceError: If reading or parsing fails.
    """
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        msg = f"Manifest not found: {manifest_path}"
        raise TraceError(msg)

    try:
        raw = manifest_path.read_text(encoding="utf-8")
        manifest = RunManifest.model_validate_json(raw)
    except Exception as exc:
        msg = f"Failed to parse manifest: {exc}"
        raise TraceError(msg) from exc

    traces: list[Trace] = []
    traces_dir = run_dir / "traces"
    if traces_dir.exists():
        for trace_file in sorted(traces_dir.glob("*.jsonl")):
            for raw_line in trace_file.read_text(encoding="utf-8").splitlines():
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    traces.append(Trace.model_validate(json.loads(stripped)))
                except Exception as exc:
                    msg = f"Failed to parse trace in {trace_file}: {exc}"
                    raise TraceError(msg) from exc

    return manifest, traces
