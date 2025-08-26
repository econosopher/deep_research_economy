# Economy JSON Builder

A modular tool for generating game economy flow charts using AI providers with deep research capabilities.

## Features

- **Multi-Provider Support**: Use Claude (3.5 Sonnet) or Gemini (2.0 Flash) for economy analysis
- **Deep Research**: Multi-phase research process for comprehensive analysis
- **Secure Storage**: API keys are encrypted and stored locally
- **Validated Output**: Ensures JSON follows the required schema
- **Model Selection**: Easy switching between different AI models

## Installation

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Configure API keys securely:
```bash
python3 economy_json_builder.py setup
```

This will guide you through:
- Setting up API keys (encrypted and stored securely)
- Configuring default provider (Gemini by default)
- Setting repository path

Your API keys are encrypted using machine-specific keys and stored in `~/.economy_json_builder/`

## API Key Setup

### Claude
1. Go to https://console.anthropic.com/
2. Create an account or sign in
3. Generate an API key
4. Add to config as `ANTHROPIC_API_KEY`

**Note**: Claude Mac subscription is separate from API access. You need an API key from the console.

## Security

API keys are stored securely:
- Encrypted using machine-specific keys (based on hardware ID)
- Stored in `~/.economy_json_builder/.credentials`
- Never exposed in plain text after initial setup
- Can be removed using the setup menu

### Gemini
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create an API key
4. Add to config as `GOOGLE_API_KEY`

## Usage

First time setup:
```bash
python3 economy_json_builder.py setup
```

Generate economy JSON (output will be game_title_provider.json):
```bash
python3 economy_json_builder.py generate game_info.md "Game Title"
# Creates: game_title_gemini.json (Gemini is default)
```

With specific provider:
```bash
python3 economy_json_builder.py generate game_info.md "Apex Legends" --provider gemini
# Creates: apex_legends_gemini.json
```

Skip PR creation:
```bash
python3 economy_json_builder.py generate game_info.md "Fortnite" --no-pr
```

Custom output name (provider will be appended):
```bash
python3 economy_json_builder.py generate game_info.md "Call of Duty" --output-name cod_warzone.json
# Creates: cod_warzone_gemini.json (Gemini is default)
```

With specific Gemini model:
```bash
# Using Gemini 2.0 Pro (experimental)
python3 economy_json_builder.py generate game_info.md "Fortnite" --provider gemini --model gemini-2.0-pro-exp
# Creates: fortnite_gemini.json

# Using Gemini 1.5 Flash (faster)
python3 economy_json_builder.py generate game_info.md "Fortnite" --provider gemini --model gemini-1.5-flash
# Creates: fortnite_gemini.json
```

## Command Line Options

- `markdown_file`: Path to markdown file with game information
- `game_title`: Title of the game to research
- `--provider`: Choose provider (claude, gemini)
- `--api-key`: Override config file API key
- `--repo-path`: Override repository path
- `--output-name`: Custom output filename
- `--no-pr`: Skip pull request creation (if repo configured)
- `--model`: Specify model for Gemini provider (e.g., gemini-2.0-flash-exp, gemini-1.5-pro)

## Provider Details

### Claude Provider
- Default model: `claude-3-5-sonnet-latest` (always uses newest version)
- Note: Claude provider doesn't support model selection via CLI
- Model is hardcoded to latest Sonnet for best performance
- 3-step process:
  1. Initial analysis (or research extraction if detected)
  2. Structured economy analysis
  3. JSON generation
- **Research-Ready**: Optimized to process both direct game information and research-generated content
- Best for: Detailed analysis with nuanced understanding

### Gemini Provider  
- Default model: `gemini-1.5-pro`
- Available models for `--model` flag:
  - `gemini-2.0-flash-exp` (2.0 Flash - newest, experimental)
  - `gemini-2.0-pro-exp` (2.0 Pro - most capable, experimental)
  - `gemini-1.5-pro` (default - stable, high quality)
  - `gemini-1.5-flash` (faster, good quality)
  - `gemini-1.0-pro` (older stable version)
- 4-step deep research process:
  1. Game systems inventory
  2. Resource flow analysis
  3. Optimization paths and goals
  4. Synthesis and JSON generation
- Best for: Comprehensive multi-phase analysis

## Output Format

The tool generates JSON files compatible with the Economy-Flow FigJam plugin:

```json
{
  "inputs": [
    {"id": "time", "label": "Time", "kind": "initial_sink_node"},
    {"id": "money", "label": "Money", "kind": "initial_sink_node"}
  ],
  "nodes": [
    {
      "id": "daily_quest",
      "label": "To Complete Daily Quest",
      "sources": ["Gold", "XP"],
      "sinks": ["Energy"],
      "values": ["Daily Streak"]
    }
  ],
  "edges": [
    ["time", "daily_quest"],
    ["daily_quest", "upgrade_gear"]
  ]
}
```

## Example Workflow

1. Create a markdown file with game information:
```markdown
# Mobile RPG Game

## Overview
A fantasy RPG with gacha mechanics...

## Currencies
- Gems (premium)
- Gold (soft currency)
- Energy (time-gated)

## Core Loop
Players complete quests to earn gold...
```

2. Run the generator:
```bash
python economy_flow_generator.py mobile_rpg.md "Fantasy Quest"
```

3. The tool will:
   - Research the game using your chosen provider
   - Generate a validated JSON flow chart
   - Save to the examples folder
   - Create a GitHub PR (unless --no-pr is used)

## Troubleshooting

### API Key Issues
- Run `python3 economy_json_builder.py setup` to reconfigure
- Verify keys are active in provider consoles
- Check `~/.economy_json_builder/` directory permissions
- API keys can also be set via environment variables (ANTHROPIC_API_KEY, GOOGLE_API_KEY)

### JSON Validation Errors
- Check all node IDs use snake_case
- Ensure all edges reference existing nodes
- Verify arrays don't have trailing commas
- All inputs must have `kind: "initial_sink_node"`
