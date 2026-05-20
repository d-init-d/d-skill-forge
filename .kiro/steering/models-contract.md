---
inclusion: always
---

# Data models — single source of truth

Every persisted artifact (YAML, JSON, JSONL, SKILL.md frontmatter) MUST conform to one of the Pydantic v2 models below. Subagents implementing modules **import from `skillforge.models`** and do not redefine these types.

## `skillforge/models/task.py`

```python
from typing import Literal
from pydantic import BaseModel, Field

class ExpectedOutcome(BaseModel):
    kind: Literal["exact", "regex", "contains", "llm_judge", "executes_ok"]
    value: str | None = None
    judge_rubric: str | None = None  # required when kind == "llm_judge"

class Task(BaseModel):
    id: str = Field(min_length=1)
    prompt: str
    context: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)
    expected: ExpectedOutcome
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)

class TaskCorpus(BaseModel):
    version: Literal[1] = 1
    name: str
    description: str
    domain: str
    tasks: list[Task]
```

## `skillforge/models/trace.py`

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class ContentBlock(BaseModel):
    type: Literal["text", "thinking", "tool_use", "tool_result"]
    text: str | None = None
    name: str | None = None          # tool name when type == "tool_use"
    input: dict | None = None
    output: str | None = None

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: list[ContentBlock]

class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0

class Score(BaseModel):
    passed: bool
    score: float                     # 0.0 .. 1.0
    rationale: str | None = None
    evaluator: str                   # e.g. "exact_match" | "llm_judge:gpt-4o-mini"

class Trace(BaseModel):
    schema_version: Literal[1] = 1
    run_id: str
    task_id: str
    provider: str
    model: str
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    cost_usd: float | None = None
    messages: list[Message]
    final_output: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    score: Score | None = None
    error: str | None = None
```

## `skillforge/models/skill.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field

class ExtractionStats(BaseModel):
    total_traces: int
    passed_traces: int
    failed_traces: int
    extractor: str                   # e.g. "reflective@0.1"
    extracted_at: datetime

class EvalReport(BaseModel):
    target_model: str
    baseline_score: float
    with_skill_score: float
    delta: float
    tasks_evaluated: int
    timestamp: datetime

class SkillFrontmatter(BaseModel):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")  # kebab-case
    description: str
    version: str = "0.1.0"
    source_model: str
    extracted_from: ExtractionStats
    triggers: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    eval: list[EvalReport] = Field(default_factory=list)
    license: str = "Apache-2.0"

class Skill(BaseModel):
    frontmatter: SkillFrontmatter
    body: str                        # markdown body below the frontmatter
```

## `skillforge/models/run.py`

```python
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

class TaskResult(BaseModel):
    task_id: str
    trace_path: Path
    passed: bool
    score: float

class RunManifest(BaseModel):
    run_id: str                      # ulid
    started_at: datetime
    finished_at: datetime | None = None
    provider: str
    model: str
    corpus_path: Path
    config_path: Path
    skill_loaded: Path | None = None
    task_results: list[TaskResult] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
```

## Disk layout

```
runs/<run_id>/
├── manifest.json                    # RunManifest as JSON
├── traces/<task_id>.jsonl           # one Trace JSON object per line
└── extraction.jsonl                 # only present after `extract` ran
```

```
skills/<name>/
└── SKILL.md                         # YAML frontmatter (SkillFrontmatter) + markdown body
```

## Rules for changes

- These contracts are immutable for the MVP. No subagent may rename fields, add fields, or change types.
- If a subagent thinks a contract is wrong, they leave a TODO comment in their PR body and stop. The main agent (spec owner) is the only role allowed to amend `models-contract.md`.
