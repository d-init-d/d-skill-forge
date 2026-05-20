# Extractors

d-skill-forge supports two extraction strategies for distilling traces into SKILL.md artifacts.

## Reflective Strategy

The **reflective** extractor analyzes traces from a single strong model run. It asks the model to reflect on its own reasoning process and extract the procedural patterns that led to success.

**Best for:**

- Single-model workflows where you only have one set of traces
- Domains where the strong model consistently succeeds
- Quick iteration when you want a skill draft fast

**CLI example:**

```bash
skillforge extract --run runs/<run-id> --strategy reflective --provider anthropic --model claude-opus-4 --out skills/SKILL.md
```

## Contrastive Strategy

The **contrastive** extractor compares traces from a strong model run against a weak model run on the same tasks. It identifies what the strong model does differently — the "delta" in reasoning — and encodes those differences as teachable procedures.

**Best for:**

- When you have both strong and weak model traces on the same corpus
- Identifying specific gaps in the weak model's reasoning
- Producing skills that target known failure modes

**CLI example:**

```bash
skillforge extract --strategy contrastive \
  --strong-run runs/<strong-id> \
  --weak-run runs/<weak-id> \
  --provider anthropic --model claude-opus-4 \
  --out skills/SKILL.md
```

## Comparison

| Aspect | Reflective | Contrastive |
|--------|-----------|-------------|
| Input | Single strong-model run | Strong + weak model runs |
| Focus | What the strong model does well | What the weak model does wrong |
| Speed | Faster (one run needed) | Slower (two runs needed) |
| Precision | Broader patterns | Targeted gap-filling |
| Best delta | Moderate | High (targets specific weaknesses) |
| Required traces | 1 run | 2 runs (same corpus) |

## Choosing a Strategy

1. **Start with reflective** if you only have strong model traces or want a quick first skill.
2. **Switch to contrastive** once you have eval data showing where the weak model fails — the contrastive extractor will produce more targeted improvements.
3. **Iterate**: extract → eval → re-extract with contrastive using the eval runs as weak traces.
