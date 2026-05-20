# Providers

d-skill-forge supports multiple LLM providers through a pluggable adapter system.

## Provider Matrix

| Provider | Install | Env Var | Thinking Tokens | Streaming |
|----------|---------|---------|-----------------|-----------|
| anthropic | included | `ANTHROPIC_API_KEY` | ✓ native | ✓ |
| openai | included | `OPENAI_API_KEY` | ✓ via system prompt | ✓ |
| bedrock | `pip install d-skill-forge[bedrock]` | AWS credentials | ✓ native | ✓ |
| gemini | `pip install d-skill-forge[gemini]` | `GOOGLE_API_KEY` | partial | ✓ |
| mock | included | (none) | simulated | ✗ |

## Anthropic

The default provider for production use. Supports Claude models with native extended thinking.

**Setup:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
skillforge run --provider anthropic --model claude-opus-4 --corpus tasks.yaml
```

**Supported models:** `claude-opus-4`, `claude-sonnet-4`, `claude-haiku-3`

**Features:** Native thinking tokens, streaming, automatic retry with backoff.

## OpenAI

Supports GPT-4o and o-series models.

**Setup:**

```bash
export OPENAI_API_KEY=sk-...
skillforge run --provider openai --model gpt-4o --corpus tasks.yaml
```

**Supported models:** `gpt-4o`, `gpt-4o-mini`, `o3`, `o3-mini`

**Features:** Streaming, function calling support, automatic retry.

## Bedrock (AWS)

Access Anthropic Claude models via AWS Bedrock. Requires the `bedrock` extra.

**Setup:**

```bash
pip install d-skill-forge[bedrock]
# Uses standard AWS credential chain (env vars, ~/.aws/credentials, IAM role)
export AWS_DEFAULT_REGION=us-east-1
skillforge run --provider bedrock --model anthropic.claude-sonnet-4-20250514-v1:0 --corpus tasks.yaml
```

**Required AWS permissions:** `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`

**Known limitations:**

- Model IDs use Bedrock's full ARN-style naming
- Cross-region inference requires explicit region configuration
- Token counting may differ slightly from direct Anthropic API

## Gemini (Google)

Access Google's Gemini models. Requires the `gemini` extra.

**Setup:**

```bash
pip install d-skill-forge[gemini]
export GOOGLE_API_KEY=...
skillforge run --provider gemini --model gemini-2.5-pro --corpus tasks.yaml
```

**Known limitations:**

- Thinking-token semantics differ from Anthropic: Gemini's "thoughts" are not
  separately billed but are included in output token counts
- `thinking_budget` parameter is mapped to `thinking_config.thinking_budget`
  but behavior may vary across model versions
- Rate limits are more aggressive than Anthropic/OpenAI for free-tier keys

## Mock

A deterministic provider for testing and development. Requires no API keys.

**Setup:**

```bash
skillforge run --provider mock --corpus tasks.yaml
```

**Behavior:**

- `mock-strong`: Returns the expected answer from the corpus (score = 1.0)
- `mock-weak`: Returns a plausible but incorrect answer (score = 0.0)
- Deterministic: same input always produces same output
- Simulates thinking tokens for testing extraction pipelines

**Use cases:**

- CI/CD pipelines
- Testing skill extraction without API costs
- Validating eval pipeline logic
- Local development

## Checking Provider Health

Use `skillforge doctor` to verify provider configuration:

```bash
skillforge doctor
```

This checks API key presence, network connectivity, and model availability
for all configured providers.
