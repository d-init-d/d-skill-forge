# TUI Guide

d-skill-forge includes a full-screen Terminal User Interface (TUI) for interactive skill distillation.

## Quick Start

```bash
# Launch TUI (default when no args)
skillforge

# Or explicitly with CLI fallback
skillforge --no-tui run --provider mock
```

## Requirements

Install with TUI support:

```bash
pip install d-skill-forge[tui]
```

## Screens

### Welcome Screen
Shown on first run when no providers are configured. Press **Enter** to connect your first provider.

### Connect Screen (`/connect`)
Interactive wizard to add provider credentials:
1. Select a provider from the list
2. Paste your API key
3. Connection is tested automatically
4. Credentials saved to `~/.config/skillforge/auth.json`

### Models Screen (`/models`)
Select which model to use for the active provider.

### Dashboard
Main view with pipeline controls:
- **[1] Run** — Execute task corpus
- **[2] Extract** — Distill SKILL.md from traces
- **[3] Eval** — Compare baseline vs with-skill
- **[4] Lint** — Validate skill format

### Run Screen
Live progress during corpus execution:
- Per-task status table
- Progress bar
- Cost ticker
- Press **Esc** to cancel

### Extract Screen
Shows extraction progress and skill preview.

### Eval Screen
Displays comparison table: baseline score vs with-skill score.

### Skill Viewer
Renders the generated SKILL.md with syntax highlighting.

### Lint Screen
Shows validation results with severity icons.

## Keybinds

| Key | Action | Context |
|-----|--------|---------|
| `q` | Quit | Global |
| `Tab` | Next pipeline step | Dashboard |
| `1-4` | Jump to step | Dashboard |
| `c` | Connect provider | Dashboard |
| `m` | Select model | Dashboard |
| `s` | View skill | Dashboard |
| `Ctrl+P` | Command palette | Global |
| `/` | Slash commands | Global |
| `Esc` | Cancel/Back | Screens |
| `F1` | Help | Global |

## Commands

| Command | Description |
|---------|-------------|
| `/connect` | Add/change provider |
| `/models` | Select model |
| `/run` | Start corpus run |
| `/extract` | Extract skill |
| `/eval` | Evaluate skill |
| `/lint` | Lint skill |
| `/quit` | Exit |

## Theme

The TUI uses a Catppuccin Mocha-inspired color scheme. The theme file is at `src/skillforge/tui/theme.tcss`.
