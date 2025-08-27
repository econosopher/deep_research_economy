# Deep Research Economy JSON Builder

A sophisticated tool for generating game economy flow charts using AI providers with deep research capabilities. This tool analyzes game economies through multi-phase research processes to create comprehensive JSON representations of resource flows, progression systems, and monetization strategies.

## Features

- **Multi-Provider Support**: Seamlessly switch between Claude (3.5 Sonnet) and Gemini (2.5 Pro) for economy analysis
- **Deep Research Process**: Optimized 2-phase research approach leveraging Gemini 2.5's enhanced capabilities
- **Secure API Management**: Encrypted storage of API keys with machine-specific encryption
- **Validated Output**: Ensures generated JSON follows the required economy flow schema
- **Modular Architecture**: Clean separation between providers, configuration, and core logic
- **Extensible Design**: Easy to add new AI providers or modify research strategies
 - **Structured JSON Generation (Gemini)**: Uses schema-guided responses to enforce the correct shape
 - **Auto ID Normalization**: Automatically converts ids to snake_case and updates edges

## Installation

1. Clone the repository:
```bash
git clone https://github.com/econosopher/deep_research_economy.git
cd deep_research_economy
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
- Setting up API keys for Gemini and/or Claude (encrypted and stored securely)
- Configuring your default provider (Gemini by default)
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
python3 economy_json_builder.py generate --provider gemini inputs/rainbow_six_siege.md "Rainbow Six Siege"

# Specify output filename
python3 economy_json_builder.py generate --output-name custom_name.json inputs/game_info.md "Game Title"

# Use a specific Gemini model (defaults to gemini-2.5-pro)
python3 economy_json_builder.py generate --provider gemini --model gemini-2.5-flash inputs/game_info.md "Game Title"

# Skip creating a pull request
python3 economy_json_builder.py generate --no-pr inputs/game_info.md "Game Title"

# Increase detail depth and auto-repair retries
python3 economy_json_builder.py generate \
  --provider gemini \
  --depth 2 \
  --retries 1 \
  game_info.md "Game Title"

### Quick Generate: Palia (Gemini)

With `inputs/palia.md` included, generate a Palia economy JSON (skipping PR):

```bash
python3 economy_json_builder.py generate --provider gemini --no-pr inputs/palia.md "Palia"
```

### Validate Existing JSON

Use the built-in validator to ensure JSON conforms to the schema rules:

```bash
python3 economy_json_builder.py validate output/palia_gemini.json
# Auto-fix structural issues and normalize ids in-place (writes .bak)
python3 economy_json_builder.py validate --fix output/palia_gemini.json
```

Notes:
- Gemini generation uses a structured response schema where supported, reducing invalid JSON.
- During generation, the tool normalizes ids to snake_case and updates all edge references accordingly.
- Validator can auto-fix common issues with `--fix` (safely writes a .bak first).
 - `--depth` asks for more granular nodes per category; `--retries` will auto-repair if lint/validation flags issues.

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
    {"id": "time", "label": "Time", "kind": "initial_sink_node"},
    {"id": "money", "label": "Money", "kind": "initial_sink_node"}
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
deep_research_economy/
├── economy_json_builder.py     # Main entry point
├── api_server.py              # Flask REST API server
├── providers/                  # AI provider implementations
│   ├── base_provider.py       # Abstract base class
│   ├── claude_provider.py     # Claude implementation
│   ├── gemini_provider.py     # Gemini implementation
│   ├── prompts.py            # Centralized prompt templates
│   ├── config.py             # Configuration management
│   └── secure_config.py      # Secure API key storage
├── agents.readme/             # Agent-specific documentation
│   ├── api_server.md         # API server instructions
│   ├── economy_json.md       # Economy JSON guidelines
│   ├── prompts.md           # Prompt engineering docs
│   ├── providers.md         # Provider implementation docs
│   └── testing.md           # Testing guidelines
├── tests/                     # Test suite
│   ├── debug/               # Debug and inspection scripts
│   ├── test_api.py         # API endpoint tests
│   └── test_builder.py     # Builder tests
├── tools/                     # Utility scripts
│   └── batch_generate_validate.py
├── inputs/                    # Example input files
└── output/                    # Generated JSON files
```

## Flask REST API Integration

The project includes a Flask REST API server that enables integration with external tools like the Figma Economy Flow Plugin.

### Starting the API Server

```bash
# Install Flask dependencies
pip3 install flask flask-cors

# Start the server (default port 5001)
PORT=5001 python3 api_server.py
```

### API Endpoints

- `GET /health` - Server health check
- `POST /api/research/cache` - Generate research cache for prompt building
- `POST /api/research/generate` - Generate complete economy JSON using LLM
- `POST /api/research/validate` - Validate economy JSON structure
- `GET /api/research/session/{id}` - Retrieve session data
- `GET /api/templates` - List available template files

### Integration with Figma Plugin

The Flask API enables the Figma Economy Flow Plugin to:
1. Generate research caches for game economy analysis
2. Create complete economy JSONs using Gemini/Claude providers
3. Validate JSON structures before visualization
4. Manage research sessions across requests

For detailed implementation documentation, see the relevant files in the [agents.readme](./agents.readme/) directory.

### Testing the API

```bash
# Run unit tests
python3 test_api.py

# Test endpoints manually
curl http://localhost:5001/health
```

## Provider Details

### Claude Provider
- Uses Claude 3.5 Sonnet (latest)
- Implements iterative research with follow-up questions
- Excels at understanding complex game systems

### Gemini Provider
- Supports multiple models (2.5 Pro default, 2.5 Flash, 2.0 Flash, 1.5 Pro, 1.5 Flash)
- Optimized 2-phase deep research process (leveraging Gemini 2.5's enhanced reasoning)
- Comprehensive analysis in Phase 1, direct JSON generation in Phase 2
- Better structured output with native JSON mode

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
# Run API tests
python3 tests/test_api.py

# Run builder tests
python3 tests/test_builder.py

# Run debug/inspection scripts
python3 tests/debug/test_gemini_models.py
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
