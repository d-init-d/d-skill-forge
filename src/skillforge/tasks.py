"""Task corpus loading, validation, and template interpolation."""

from __future__ import annotations

import json
import re
from pathlib import Path  # noqa: TC003 - used at runtime in function bodies

import yaml

from skillforge.errors import ConfigError
from skillforge.models.task import Task, TaskCorpus


def load_corpus(path: Path) -> TaskCorpus:
    """Load a task corpus from a YAML or JSON file.

    Args:
        path: Path to the corpus file (.yaml, .yml, or .json).

    Returns:
        A validated TaskCorpus instance.

    Raises:
        ConfigError: If the file cannot be read or parsed.
    """
    if not path.exists():
        msg = f"Corpus file not found: {path}"
        raise ConfigError(msg)

    text = path.read_text(encoding="utf-8")

    try:
        if path.suffix in (".yaml", ".yml"):
            raw = yaml.safe_load(text)
        elif path.suffix == ".json":
            raw = json.loads(text)
        else:
            msg = f"Unsupported corpus format: {path.suffix}"
            raise ConfigError(msg)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse corpus file {path}: {exc}"
        raise ConfigError(msg) from exc

    try:
        return TaskCorpus.model_validate(raw)
    except Exception as exc:
        msg = f"Invalid corpus schema in {path}: {exc}"
        raise ConfigError(msg) from exc


def validate_corpus(corpus: TaskCorpus) -> list[str]:
    """Validate a corpus for logical issues beyond schema correctness.

    Args:
        corpus: The corpus to validate.

    Returns:
        A list of human-readable issue descriptions. Empty if valid.
    """
    issues: list[str] = []

    seen_ids: set[str] = set()
    for task in corpus.tasks:
        if task.id in seen_ids:
            issues.append(f"Duplicate task ID: '{task.id}'")
        seen_ids.add(task.id)

        if not task.prompt.strip():
            issues.append(f"Task '{task.id}' has an empty prompt")

        if task.expected.kind == "llm_judge" and not task.expected.judge_rubric:
            issues.append(f"Task '{task.id}' uses llm_judge but has no judge_rubric")

    return issues


_VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def interpolate(task: Task, run_vars: dict[str, str]) -> str:
    """Substitute {{ var }} placeholders in a task prompt.

    Args:
        task: The task whose prompt to interpolate.
        run_vars: Variable name-to-value mapping.

    Returns:
        The interpolated prompt string.
    """
    merged = {**task.inputs, **run_vars}

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return merged.get(key, match.group(0))

    return _VAR_PATTERN.sub(_replace, task.prompt)
