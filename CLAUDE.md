# Claude Assistant Instructions

This project uses agent-specific readme files for Claude assistant guidance. Please refer to the appropriate agent readme file in the `agents.readme/` directory for task-specific instructions.

## Agent-Specific Instructions

Agent readme files contain specialized instructions for different aspects of the project:

- **agents.readme/economy_json.md** - Instructions for building and validating economy JSON structures
- **agents.readme/api_server.md** - Instructions for API server development and maintenance
- **agents.readme/providers.md** - Instructions for LLM provider integration
- **agents.readme/testing.md** - Instructions for test development and validation

## Why Agent Readmes?

Instead of maintaining a single monolithic Claude readme, this project uses agent-specific readmes to:
1. Provide focused, contextual instructions for specific tasks
2. Avoid regenerating global instructions unnecessarily
3. Allow different agents to have specialized knowledge without conflicts
4. Make it easier to update instructions for specific components

## Adding New Agent Instructions

When creating new agent-specific instructions:
1. Create a new file in `agents.readme/` with a descriptive name
2. Focus the instructions on that specific domain or task
3. Reference other agent readmes when there are dependencies
4. Keep instructions concise and actionable

## Note for Claude Assistants

When working on this project, first check if there's a relevant agent readme for your current task. Use the instructions in the agent readme as your primary guide, falling back to general best practices when specific guidance isn't available.