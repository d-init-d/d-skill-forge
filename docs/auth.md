# Authentication

d-skill-forge supports multiple ways to configure provider credentials.

## Resolution Order

Credentials are resolved in this priority:

1. **auth.json** — Set via `/connect` in TUI or `skillforge auth add`
2. **Environment variables** — e.g. `ANTHROPIC_API_KEY`
3. **Config file** — `api_key_env` reference in `skillforge.toml`

## Auth Store

Credentials are stored in:
- **Linux/macOS:** `~/.config/skillforge/auth.json`
- **Windows:** `%APPDATA%/skillforge/auth.json`

File permissions are set to owner-only (600) on Unix.

## CLI Commands

```bash
# List all providers and their auth status
skillforge auth list

# Add credentials interactively
skillforge auth add groq

# Remove credentials
skillforge auth remove groq

# Test connectivity
skillforge auth test groq
```

## TUI Connect

In the TUI, press `c` or run `/connect` to open the provider wizard:
1. Select provider from list
2. Paste API key
3. Connection tested automatically
4. Saved to auth.json

## Environment Variables

| Provider | Variable |
|----------|----------|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Groq | `GROQ_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Together AI | `TOGETHER_API_KEY` |
| Fireworks AI | `FIREWORKS_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| xAI | `XAI_API_KEY` |
| NVIDIA | `NVIDIA_API_KEY` |
| Cerebras | `CEREBRAS_API_KEY` |
| Bedrock | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` |
| Gemini | `GOOGLE_API_KEY` |

## Security

- auth.json is never committed to git (add to `.gitignore`)
- File permissions restricted to owner-only on Unix
- Keys are never logged or printed in full
