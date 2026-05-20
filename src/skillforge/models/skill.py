"""Skill and SkillFrontmatter models for SKILL.md artifacts."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - required at runtime by Pydantic

from pydantic import BaseModel, Field


class ExtractionStats(BaseModel):
    """Statistics about the extraction process that produced a skill.

    Attributes:
        total_traces: Total number of traces in the source run.
        passed_traces: Number of traces that passed evaluation.
        failed_traces: Number of traces that failed evaluation.
        extractor: Identifier of the extractor used (e.g. "reflective@0.1").
        extracted_at: Timestamp when extraction was performed.
    """

    total_traces: int
    passed_traces: int
    failed_traces: int
    extractor: str
    extracted_at: datetime


class EvalReport(BaseModel):
    """Report from evaluating a skill against a weak model.

    Attributes:
        target_model: The weak model evaluated.
        baseline_score: Score without the skill loaded.
        with_skill_score: Score with the skill loaded.
        delta: Difference (with_skill_score - baseline_score).
        tasks_evaluated: Number of tasks in the evaluation.
        timestamp: When the evaluation was performed.
    """

    target_model: str
    baseline_score: float
    with_skill_score: float
    delta: float
    tasks_evaluated: int
    timestamp: datetime


class SkillFrontmatter(BaseModel):
    """YAML frontmatter metadata for a SKILL.md file.

    Attributes:
        name: Kebab-case skill identifier.
        description: One-sentence description of the skill.
        version: SemVer version string.
        source_model: Model that generated the traces.
        extracted_from: Statistics about the extraction.
        triggers: Keywords that indicate when to apply this skill.
        domains: Knowledge domains this skill covers.
        eval: List of evaluation reports.
        license: SPDX license identifier.
    """

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")
    description: str
    version: str = "0.1.0"
    source_model: str
    extracted_from: ExtractionStats
    triggers: list[str] = Field(default_factory=list[str])
    domains: list[str] = Field(default_factory=list[str])
    eval: list[EvalReport] = Field(default_factory=list[EvalReport])
    license: str = "Apache-2.0"


class Skill(BaseModel):
    """A complete SKILL.md artifact with frontmatter and markdown body.

    Attributes:
        frontmatter: Parsed YAML frontmatter metadata.
        body: Markdown body below the frontmatter.
    """

    frontmatter: SkillFrontmatter
    body: str
