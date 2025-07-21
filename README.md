# Deep Research Economy JSON Builder

A sophisticated tool for generating game economy flow charts using AI providers with deep research capabilities. This tool analyzes game economies through multi-phase research processes to create comprehensive JSON representations of resource flows, progression systems, and monetization strategies.

## Features

- **Multi-Provider Support**: Seamlessly switch between Claude (3.5 Sonnet) and Gemini (2.0 Flash) for economy analysis
- **Deep Research Process**: Multi-phase research approach for comprehensive game economy analysis
- **Secure API Management**: Encrypted storage of API keys with machine-specific encryption
- **Validated Output**: Ensures generated JSON follows the required economy flow schema
- **Modular Architecture**: Clean separation between providers, configuration, and core logic
- **Extensible Design**: Easy to add new AI providers or modify research strategies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/econosopher/deep-research-economy.git
cd deep-research-economy
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Configure API keys securely:
```bash
python3 economy_json_builder.py setup
```

This will guide you through:
- Setting up API keys for Claude and/or Gemini (encrypted and stored securely)
- Configuring your default provider
- Setting the repository path (optional)

Your API keys are encrypted using machine-specific keys and stored in `~/.economy_json_builder/`

## Usage

### Basic Usage

Generate an economy JSON for a game:

```bash
python3 economy_json_builder.py generate game_info.md "Game Title"
```

### Advanced Options

```bash
# Use a specific provider
python3 economy_json_builder.py generate --provider gemini game_info.md "Rainbow Six Siege"

# Specify output filename
python3 economy_json_builder.py generate --output-name custom_name.json game_info.md "Game Title"

# Use a specific Gemini model
python3 economy_json_builder.py generate --provider gemini --model gemini-1.5-pro game_info.md "Game Title"

# Skip creating a pull request
python3 economy_json_builder.py generate --no-pr game_info.md "Game Title"
```

### Input Format

Create a markdown file with basic information about the game:

```markdown
# Game Title

A brief description of the game, its genre, and core gameplay mechanics.
```

The AI providers will conduct deep research to understand:
- Core gameplay loops
- Resource systems and currencies
- Progression mechanics
- Monetization strategies
- Player engagement systems

### Output Format

The tool generates a JSON file following the economy flow schema with:
- **Inputs**: External resources (time, money, attention)
- **Nodes**: Game systems that process resources
- **Edges**: Connections showing resource flow between systems
- **Subsections**: Logical groupings of related systems

Example output structure:
```json
{
  "inputs": [
    {"id": "time", "label": "Time", "kind": "SINK_RED"},
    {"id": "money", "label": "Money", "kind": "SINK_RED"}
  ],
  "nodes": [
    {
      "id": "gameplay",
      "label": "Core Gameplay",
      "sources": ["xp", "currency"],
      "sinks": ["time"],
      "values": ["skill_level"]
    }
  ],
  "edges": [
    ["time", "gameplay"],
    ["gameplay", "progression"]
  ]
}
```

## Architecture

```
economy_json_providers/
├── economy_json_builder.py     # Main entry point
├── providers/                  # AI provider implementations
│   ├── base_provider.py       # Abstract base class
│   ├── claude_provider.py     # Claude implementation
│   ├── gemini_provider.py     # Gemini implementation
│   ├── config.py             # Configuration management
│   └── secure_config.py      # Secure API key storage
├── output/                    # Generated JSON files
└── test_economy_json.py      # Test suite
```

## Provider Details

### Claude Provider
- Uses Claude 3.5 Sonnet (latest)
- Implements iterative research with follow-up questions
- Excels at understanding complex game systems

### Gemini Provider
- Supports multiple models (2.0 Flash, 1.5 Pro, 1.5 Flash)
- Three-phase deep research process
- Optimized for fast, comprehensive analysis

## Security

- API keys are encrypted using `cryptography.fernet`
- Machine-specific encryption keys
- Keys stored in user home directory
- Never committed to version control

## Development

### Adding a New Provider

1. Create a new file in `providers/` extending `BaseEconomyProvider`
2. Implement the `generate_economy_json` method
3. Register the provider in `providers/__init__.py`

### Running Tests

```bash
python3 test_economy_json.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for analyzing game economies and progression systems
- Inspired by the need for systematic game economy documentation
- Leverages cutting-edge AI models for deep game analysis