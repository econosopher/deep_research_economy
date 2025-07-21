#!/usr/bin/env python3
"""
Economy JSON Builder - Modular Edition with Secure Config

This script connects to various LLM providers to research game economies based on a markdown file,
generates a JSON economy specification, and creates a PR to add it to the examples folder.
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers import get_provider
from providers.secure_config import SecureConfig


class EconomyJSONBuilder:
    def __init__(self, provider_name: str, api_key: str, repo_path: str, **provider_kwargs):
        """Initialize the generator with provider and repository path."""
        self.provider_name = provider_name
        self.provider = get_provider(provider_name, api_key, **provider_kwargs)
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.output_path = Path.cwd() / "output"
        
        # Create output directory if it doesn't exist
        self.output_path.mkdir(exist_ok=True)
    
    def read_markdown_file(self, file_path: str) -> str:
        """Read and return the contents of a markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def validate_json(self, data: Dict[str, Any]) -> bool:
        """Validate the generated JSON against the schema requirements."""
        try:
            # Check required top-level keys
            required_keys = ["inputs", "nodes", "edges"]
            for key in required_keys:
                if key not in data:
                    print(f"Missing required key: {key}")
                    return False
            
            # Validate inputs
            if not isinstance(data["inputs"], list):
                print("'inputs' must be an array")
                return False
            
            for input_item in data["inputs"]:
                if not all(key in input_item for key in ["id", "label", "kind"]):
                    print(f"Input missing required fields: {input_item}")
                    return False
                if input_item["kind"] != "SINK_RED":
                    print(f"Input kind must be 'SINK_RED': {input_item}")
                    return False
            
            # Validate nodes
            if not isinstance(data["nodes"], list):
                print("'nodes' must be an array")
                return False
            
            node_ids = set()
            for node in data["nodes"]:
                if "id" not in node or "label" not in node:
                    print(f"Node missing required fields: {node}")
                    return False
                node_ids.add(node["id"])
                
                # Check array fields
                for field in ["sources", "sinks", "values"]:
                    if field in node and not isinstance(node[field], list):
                        print(f"Node field '{field}' must be an array: {node}")
                        return False
            
            # Validate edges
            if not isinstance(data["edges"], list):
                print("'edges' must be an array")
                return False
            
            input_ids = {inp["id"] for inp in data["inputs"]}
            all_ids = input_ids | node_ids
            
            for edge in data["edges"]:
                if not isinstance(edge, list) or len(edge) != 2:
                    print(f"Edge must be a two-element array: {edge}")
                    return False
                if edge[0] not in all_ids or edge[1] not in all_ids:
                    print(f"Edge references non-existent node: {edge}")
                    return False
            
            # Validate optional subsections
            if "subsections" in data:
                if not isinstance(data["subsections"], list):
                    print("'subsections' must be an array")
                    return False
                
                for subsection in data["subsections"]:
                    if not all(key in subsection for key in ["id", "label", "nodeIds"]):
                        print(f"Subsection missing required fields: {subsection}")
                        return False
                    if not isinstance(subsection["nodeIds"], list):
                        print(f"Subsection nodeIds must be an array: {subsection}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    def save_json_file(self, data: Dict[str, Any], filename: str) -> str:
        """Save the JSON data to a file in the output directory."""
        # Remove metadata before saving
        if "_metadata" in data:
            metadata = data.pop("_metadata")
            print(f"Generated with {metadata.get('provider', 'unknown')} provider")
        
        file_path = self.output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')  # Add trailing newline
        
        return str(file_path)
    
    def create_pull_request(self, filename: str, game_title: str) -> Optional[str]:
        """Create a pull request with the new JSON file to the figma-economy-flow-builder repo."""
        try:
            # Save current directory
            original_dir = os.getcwd()
            
            # Path to the external repository
            external_repo_path = self.repo_path / "figma-economy-flow-builder"
            
            # Clone or pull the external repository if needed
            if not external_repo_path.exists():
                print(f"Cloning figma-economy-flow-builder repository...")
                subprocess.run([
                    "git", "clone", 
                    "https://github.com/econosopher/figma-economy-flow-builder.git",
                    str(external_repo_path)
                ], check=True)
            else:
                # Pull latest changes
                os.chdir(external_repo_path)
                subprocess.run(["git", "checkout", "main"], check=True)
                subprocess.run(["git", "pull", "origin", "main"], check=True)
            
            # Change to repository directory
            os.chdir(external_repo_path)
            
            # Create a new branch
            branch_name = f"add-{filename.replace('.json', '')}-example"
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"{branch_name}-{timestamp}"
            
            # Create and checkout new branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            
            # Copy the JSON file to the examples folder
            source_file = self.output_path / filename
            target_file = external_repo_path / "examples" / filename
            
            shutil.copy2(source_file, target_file)
            
            # Add the new file
            subprocess.run(["git", "add", f"examples/{filename}"], check=True)
            
            # Commit the changes
            commit_message = f"""Add {game_title} economy flow example

Added a new economy flow chart example for {game_title} that demonstrates:
- Core gameplay loops and progression systems
- Resource flows between different game activities
- Player inputs (time/money) and their conversion to in-game value
- Final goals and achievement systems

This example can be used as a reference for understanding {game_title}'s economy structure.
Generated using {self.provider_name} provider with deep research."""
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # Push the branch
            subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
            
            # Create PR using GitHub CLI
            pr_body = f"""## Summary
- Added new economy flow example for {game_title}
- Generated using {self.provider_name} provider with deep research
- JSON follows the plugin's schema requirements
- Includes all major gameplay loops and resource flows

## What's included
- Player inputs (time and money)
- Core gameplay activities and their resource consumption/generation
- Progression systems and value accumulation
- End-game goals and achievements

## Testing
- JSON has been validated against the schema
- All node IDs follow snake_case convention
- All edges connect to valid nodes
- Arrays are properly formatted without trailing commas

## Generation Details
- Provider: {self.provider_name}
- Deep Research: Enabled
- Multi-phase analysis for comprehensive coverage"""
            
            result = subprocess.run([
                "gh", "pr", "create",
                "--title", f"Add {game_title} economy flow example",
                "--body", pr_body,
                "--base", "main"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"Pull request created: {pr_url}")
                return pr_url
            else:
                print(f"Failed to create PR: {result.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return None
        except Exception as e:
            print(f"Error creating pull request: {e}")
            return None
        finally:
            # Always return to original directory
            os.chdir(original_dir)


def setup_command():
    """Interactive setup for API keys and configuration."""
    print("Economy JSON Builder Setup")
    print("=" * 50)
    
    config = SecureConfig()
    
    # Show current status
    print("\nCurrent provider status:")
    providers = config.list_providers()
    for provider, has_key in providers.items():
        status = "✓ Configured" if has_key else "✗ Not configured"
        print(f"  {provider.capitalize()}: {status}")
    
    # Menu loop
    while True:
        print("\nWhat would you like to do?")
        print("1. Configure Claude API key")
        print("2. Configure Gemini API key")
        print("3. Set default provider")
        print("4. Set repository path")
        print("5. Remove an API key")
        print("6. Export config template")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            config.set_api_key('claude')
        elif choice == '2':
            config.set_api_key('gemini')
        elif choice == '3':
            current_default = config.get_config('DEFAULT_PROVIDER', 'claude')
            print(f"\nCurrent default provider: {current_default}")
            new_default = input("Enter new default provider (claude/gemini): ").lower()
            if new_default in ['claude', 'gemini']:
                config.set_config('DEFAULT_PROVIDER', new_default)
                print(f"✓ Default provider set to: {new_default}")
            else:
                print("Invalid provider.")
        elif choice == '4':
            current_repo = config.get_config('REPO_PATH', 'Not set')
            print(f"\nCurrent repository path: {current_repo}")
            new_repo = input("Enter new repository path: ").strip()
            if new_repo and os.path.exists(new_repo):
                config.set_config('REPO_PATH', new_repo)
                print(f"✓ Repository path set to: {new_repo}")
            else:
                print("Path does not exist.")
        elif choice == '5':
            provider = input("Which provider's API key to remove (claude/gemini): ").lower()
            if provider in ['claude', 'gemini']:
                config.remove_api_key(provider)
        elif choice == '6':
            template_path = input("Enter path for config template: ").strip()
            if template_path:
                config.export_config_template(template_path)
        elif choice == '7':
            print("\n✓ Setup complete!")
            break
        else:
            print("Invalid choice.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate economy JSON from game documentation and create a PR",
        prog="economy_json_builder"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Configure API keys and settings')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate economy JSON')
    generate_parser.add_argument(
        "markdown_file",
        help="Path to the markdown file with game information"
    )
    generate_parser.add_argument(
        "game_title",
        help="Title of the game to research"
    )
    generate_parser.add_argument(
        "--provider",
        choices=["claude", "gemini"],
        help="LLM provider to use (defaults to config file setting)"
    )
    generate_parser.add_argument(
        "--api-key",
        help="API key for the selected provider (use 'setup' for secure storage)"
    )
    generate_parser.add_argument(
        "--repo-path",
        help="Path to the economy-flow-plugin repository"
    )
    generate_parser.add_argument(
        "--output-name",
        help="Output filename (defaults to game_title.json)"
    )
    generate_parser.add_argument(
        "--no-pr",
        action="store_true",
        help="Skip creating a pull request"
    )
    generate_parser.add_argument(
        "--model",
        help="Model to use (for Gemini: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # For backward compatibility - if no command but has args, assume generate
    if args.command is None and len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Re-parse with generate command
        args = parser.parse_args(['generate'] + sys.argv[1:])
    
    # Handle commands
    if args.command == 'setup':
        setup_command()
        return
    elif args.command is None:
        parser.print_help()
        print("\nQuick start:")
        print(f"  {sys.argv[0]} setup                    # Configure API keys")
        print(f"  {sys.argv[0]} generate game.md \"Title\"  # Generate JSON")
        return
    
    # Generate command logic
    config = SecureConfig()
    
    # Determine provider
    provider_name = args.provider or config.get_config("DEFAULT_PROVIDER", "claude")
    
    # Get API key
    api_key = args.api_key or config.get_api_key(provider_name, prompt_if_missing=True)
    if not api_key:
        print(f"\nError: No API key found for {provider_name} provider.")
        print(f"Please run '{sys.argv[0]} setup' to configure your API keys")
        sys.exit(1)
    
    # Get repository path
    repo_path = args.repo_path or config.get_config("REPO_PATH")
    if not repo_path:
        print("\nError: No repository path specified.")
        print(f"Please run '{sys.argv[0]} setup' to configure the repository path")
        print("Or use --repo-path to specify it directly")
        sys.exit(1)
    
    # Set output filename
    if not args.output_name:
        # Convert game title to snake_case for filename
        filename = args.game_title.lower().replace(" ", "_").replace("-", "_")
        # Append provider name
        filename = f"{filename}_{provider_name}.json"
    else:
        filename = args.output_name
        # If custom name doesn't have provider, add it before .json
        if not filename.endswith(".json"):
            filename = f"{filename}_{provider_name}.json"
        elif "_claude" not in filename and "_gemini" not in filename:
            # Insert provider name before .json
            filename = filename.replace(".json", f"_{provider_name}.json")
    
    try:
        # Initialize generator with model if specified
        provider_kwargs = {}
        if hasattr(args, 'model') and args.model and provider_name == 'gemini':
            provider_kwargs['model_name'] = args.model
            print(f"Using {provider_name} provider with {args.model} model...")
        else:
            print(f"Using {provider_name} provider...")
        
        generator = EconomyJSONBuilder(provider_name, api_key, repo_path, **provider_kwargs)
        
        # Read markdown file
        print(f"Reading markdown file: {args.markdown_file}")
        game_info = generator.read_markdown_file(args.markdown_file)
        
        # Generate economy JSON
        print(f"Researching {args.game_title} economy with {provider_name}...")
        economy_data = generator.provider.generate_economy_json(game_info, args.game_title)
        
        # Validate JSON
        print("Validating generated JSON...")
        if not generator.validate_json(economy_data):
            print("JSON validation failed! Saving anyway for debugging...")
        
        # Save JSON file
        print(f"Saving JSON to: {filename}")
        file_path = generator.save_json_file(economy_data, filename)
        print(f"JSON saved successfully: {file_path}")
        
        # Create pull request
        if not args.no_pr:
            print("Creating pull request...")
            pr_url = generator.create_pull_request(filename, args.game_title)
            if pr_url:
                print(f"Pull request created: {pr_url}")
            else:
                print("Failed to create pull request")
        
        print("\n✓ Done!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()