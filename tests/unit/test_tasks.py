# ruff: noqa: D102, PLR2004
"""Tests for task corpus loading, validation, and interpolation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillforge.errors import ConfigError
from skillforge.models.task import ExpectedOutcome, Task, TaskCorpus
from skillforge.tasks import interpolate, load_corpus, validate_corpus

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestLoadCorpus:
    """Tests for load_corpus."""

    def test_load_yaml(self) -> None:
        corpus = load_corpus(FIXTURES / "tasks_minimal.yaml")
        assert corpus.name == "minimal-test-corpus"
        assert len(corpus.tasks) == 5

    def test_load_json(self, tmp_path: Path) -> None:
        data = {
            "version": 1,
            "name": "json-corpus",
            "description": "test",
            "domain": "test",
            "tasks": [
                {
                    "id": "t1",
                    "prompt": "hello",
                    "expected": {"kind": "exact", "value": "world"},
                }
            ],
        }
        p = tmp_path / "corpus.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        corpus = load_corpus(p)
        assert corpus.name == "json-corpus"
        assert len(corpus.tasks) == 1

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_corpus(tmp_path / "missing.yaml")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        p = tmp_path / "corpus.txt"
        p.write_text("hello", encoding="utf-8")
        with pytest.raises(ConfigError, match="Unsupported corpus format"):
            load_corpus(p)

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text("{{invalid", encoding="utf-8")
        with pytest.raises(ConfigError, match="Failed to parse"):
            load_corpus(p)

    def test_invalid_schema(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text("version: 1\nname: x\n", encoding="utf-8")
        with pytest.raises(ConfigError, match="Invalid corpus schema"):
            load_corpus(p)


class TestValidateCorpus:
    """Tests for validate_corpus."""

    def test_valid_corpus(self) -> None:
        corpus = load_corpus(FIXTURES / "tasks_minimal.yaml")
        issues = validate_corpus(corpus)
        assert issues == []

    def test_duplicate_ids(self) -> None:
        corpus = TaskCorpus(
            name="dup",
            description="test",
            domain="test",
            tasks=[
                Task(
                    id="same",
                    prompt="a",
                    expected=ExpectedOutcome(kind="exact", value="x"),
                ),
                Task(
                    id="same",
                    prompt="b",
                    expected=ExpectedOutcome(kind="exact", value="y"),
                ),
            ],
        )
        issues = validate_corpus(corpus)
        assert any("Duplicate task ID" in i for i in issues)

    def test_empty_prompt(self) -> None:
        corpus = TaskCorpus(
            name="empty",
            description="test",
            domain="test",
            tasks=[
                Task(
                    id="t1",
                    prompt="   ",
                    expected=ExpectedOutcome(kind="exact", value="x"),
                ),
            ],
        )
        issues = validate_corpus(corpus)
        assert any("empty prompt" in i for i in issues)


class TestInterpolate:
    """Tests for interpolate."""

    def test_basic_substitution(self) -> None:
        task = Task(
            id="t",
            prompt="Hello {{ name }}!",
            expected=ExpectedOutcome(kind="exact", value="x"),
        )
        result = interpolate(task, {"name": "World"})
        assert result == "Hello World!"

    def test_uses_task_inputs(self) -> None:
        task = Task(
            id="t",
            prompt="Topic: {{ topic }}",
            inputs={"topic": "AI"},
            expected=ExpectedOutcome(kind="exact", value="x"),
        )
        result = interpolate(task, {})
        assert result == "Topic: AI"

    def test_run_vars_override_inputs(self) -> None:
        task = Task(
            id="t",
            prompt="{{ x }}",
            inputs={"x": "from_task"},
            expected=ExpectedOutcome(kind="exact", value="x"),
        )
        result = interpolate(task, {"x": "from_run"})
        assert result == "from_run"

    def test_missing_var_preserved(self) -> None:
        task = Task(
            id="t",
            prompt="{{ unknown }}",
            expected=ExpectedOutcome(kind="exact", value="x"),
        )
        result = interpolate(task, {})
        assert result == "{{ unknown }}"
