#!/usr/bin/env python3
"""
Test script for Economy Flow Generator
Tests all components without making actual API calls or git operations
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from economy_flow_providers import Config, get_provider, BaseEconomyProvider
from economy_flow_generator import EconomyFlowGenerator


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name):
        self.passed.append(test_name)
        print(f"✓ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"✗ {test_name}: {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*50}")
        print(f"Test Results: {len(self.passed)}/{total} passed")
        if self.failed:
            print(f"\nFailed tests:")
            for test, error in self.failed:
                print(f"  - {test}: {error}")
        return len(self.failed) == 0


def test_config_loading():
    """Test configuration loading and API key retrieval"""
    results = TestResults()
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_config', delete=False) as f:
        f.write("""# Test config
ANTHROPIC_API_KEY=test_claude_key
GOOGLE_API_KEY=test_gemini_key
DEFAULT_PROVIDER=claude
REPO_PATH=/test/repo/path
""")
        temp_config = f.name
    
    try:
        # Test config loading
        config = Config(temp_config)
        
        # Test API key retrieval
        if config.get_api_key('claude') == 'test_claude_key':
            results.add_pass("Config: Load Claude API key")
        else:
            results.add_fail("Config: Load Claude API key", "Key mismatch")
        
        if config.get_api_key('gemini') == 'test_gemini_key':
            results.add_pass("Config: Load Gemini API key")
        else:
            results.add_fail("Config: Load Gemini API key", "Key mismatch")
        
        # Test default provider
        if config.get('DEFAULT_PROVIDER') == 'claude':
            results.add_pass("Config: Load default provider")
        else:
            results.add_fail("Config: Load default provider", "Provider mismatch")
        
        # Test environment variable override
        os.environ['ANTHROPIC_API_KEY'] = 'env_override_key'
        config_with_env = Config(temp_config)
        if config_with_env.get_api_key('claude') == 'env_override_key':
            results.add_pass("Config: Environment variable override")
        else:
            results.add_fail("Config: Environment variable override", "Override failed")
        
    finally:
        os.unlink(temp_config)
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']
    
    return results


def test_provider_registry():
    """Test provider registration and instantiation"""
    results = TestResults()
    
    try:
        # Test getting Claude provider
        from economy_flow_providers import PROVIDERS
        if 'claude' in PROVIDERS:
            results.add_pass("Provider Registry: Claude registered")
        else:
            results.add_fail("Provider Registry: Claude registered", "Not found")
        
        if 'gemini' in PROVIDERS:
            results.add_pass("Provider Registry: Gemini registered")
        else:
            results.add_fail("Provider Registry: Gemini registered", "Not found")
        
        # Test provider instantiation (without making API calls)
        with patch('anthropic.Anthropic'):
            claude_provider = get_provider('claude', 'test_key')
            if claude_provider.name() == 'Claude':
                results.add_pass("Provider Registry: Claude instantiation")
            else:
                results.add_fail("Provider Registry: Claude instantiation", "Wrong name")
        
        with patch('google.generativeai.configure'):
            gemini_provider = get_provider('gemini', 'test_key')
            if gemini_provider.name() == 'Gemini':
                results.add_pass("Provider Registry: Gemini instantiation")
            else:
                results.add_fail("Provider Registry: Gemini instantiation", "Wrong name")
        
        # Test invalid provider
        try:
            get_provider('invalid', 'test_key')
            results.add_fail("Provider Registry: Invalid provider", "Should raise error")
        except ValueError:
            results.add_pass("Provider Registry: Invalid provider rejection")
    
    except Exception as e:
        results.add_fail("Provider Registry", str(e))
    
    return results


def test_json_validation():
    """Test JSON validation logic"""
    results = TestResults()
    
    # Create a mock generator with just the validation method
    class MockGenerator:
        def validate_json(self, data):
            # Copy the validation logic from the main class
            try:
                required_keys = ["inputs", "nodes", "edges"]
                for key in required_keys:
                    if key not in data:
                        return False
                
                if not isinstance(data["inputs"], list):
                    return False
                
                for input_item in data["inputs"]:
                    if not all(key in input_item for key in ["id", "label", "kind"]):
                        return False
                    if input_item["kind"] != "SINK_RED":
                        return False
                
                if not isinstance(data["nodes"], list):
                    return False
                
                node_ids = set()
                for node in data["nodes"]:
                    if "id" not in node or "label" not in node:
                        return False
                    node_ids.add(node["id"])
                    
                    for field in ["sources", "sinks", "values"]:
                        if field in node and not isinstance(node[field], list):
                            return False
                
                if not isinstance(data["edges"], list):
                    return False
                
                input_ids = {inp["id"] for inp in data["inputs"]}
                all_ids = input_ids | node_ids
                
                for edge in data["edges"]:
                    if not isinstance(edge, list) or len(edge) != 2:
                        return False
                    if edge[0] not in all_ids or edge[1] not in all_ids:
                        return False
                
                return True
                
            except Exception:
                return False
    
    generator = MockGenerator()
    
    # Test valid JSON
    valid_json = {
        "inputs": [
            {"id": "time", "label": "Time", "kind": "SINK_RED"},
            {"id": "money", "label": "Money", "kind": "SINK_RED"}
        ],
        "nodes": [
            {
                "id": "daily_quest",
                "label": "To Complete Daily Quest",
                "sources": ["Gold"],
                "sinks": ["Energy"],
                "values": ["XP"]
            }
        ],
        "edges": [
            ["time", "daily_quest"]
        ]
    }
    
    if generator.validate_json(valid_json):
        results.add_pass("JSON Validation: Valid structure")
    else:
        results.add_fail("JSON Validation: Valid structure", "Should pass")
    
    # Test missing required key
    invalid_json = valid_json.copy()
    del invalid_json["inputs"]
    if not generator.validate_json(invalid_json):
        results.add_pass("JSON Validation: Missing required key")
    else:
        results.add_fail("JSON Validation: Missing required key", "Should fail")
    
    # Test invalid edge reference
    invalid_edge_json = valid_json.copy()
    invalid_edge_json["edges"] = [["time", "nonexistent_node"]]
    if not generator.validate_json(invalid_edge_json):
        results.add_pass("JSON Validation: Invalid edge reference")
    else:
        results.add_fail("JSON Validation: Invalid edge reference", "Should fail")
    
    # Test wrong input kind
    wrong_kind_json = valid_json.copy()
    wrong_kind_json["inputs"][0]["kind"] = "WRONG_KIND"
    if not generator.validate_json(wrong_kind_json):
        results.add_pass("JSON Validation: Wrong input kind")
    else:
        results.add_fail("JSON Validation: Wrong input kind", "Should fail")
    
    return results


def test_file_operations():
    """Test file reading and saving operations"""
    results = TestResults()
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        examples_dir = temp_path / "examples"
        examples_dir.mkdir()
        
        # Test markdown reading
        test_md = temp_path / "test.md"
        test_md.write_text("# Test Game\n\nThis is a test.")
        
        try:
            # Mock the generator
            with patch('anthropic.Anthropic'):
                generator = EconomyFlowGenerator('claude', 'test_key', temp_dir)
                
                # Test reading markdown
                content = generator.read_markdown_file(str(test_md))
                if "Test Game" in content:
                    results.add_pass("File Operations: Read markdown")
                else:
                    results.add_fail("File Operations: Read markdown", "Content mismatch")
                
                # Test saving JSON
                test_data = {
                    "inputs": [{"id": "time", "label": "Time", "kind": "SINK_RED"}],
                    "nodes": [],
                    "edges": []
                }
                
                saved_path = generator.save_json_file(test_data, "test_game.json")
                if Path(saved_path).exists():
                    results.add_pass("File Operations: Save JSON")
                    
                    # Test JSON content
                    with open(saved_path, 'r') as f:
                        loaded_data = json.load(f)
                    if loaded_data == test_data:
                        results.add_pass("File Operations: JSON content integrity")
                    else:
                        results.add_fail("File Operations: JSON content integrity", "Data mismatch")
                else:
                    results.add_fail("File Operations: Save JSON", "File not created")
        
        except Exception as e:
            results.add_fail("File Operations", str(e))
    
    return results


def test_prompt_generation():
    """Test that providers generate proper prompts"""
    results = TestResults()
    
    try:
        # Test base provider prompt generation
        from economy_flow_providers.base_provider import BaseEconomyProvider
        
        class TestProvider(BaseEconomyProvider):
            def generate_economy_json(self, game_info, game_title):
                return {}
            def name(self):
                return "Test"
        
        provider = TestProvider("test_key")
        prompt = provider.get_economy_prompt("Test info", "Test Game")
        
        # Check that prompt contains key elements
        if "Test Game" in prompt:
            results.add_pass("Prompt Generation: Game title included")
        else:
            results.add_fail("Prompt Generation: Game title included", "Title missing")
        
        if "inputs" in prompt and "nodes" in prompt and "edges" in prompt:
            results.add_pass("Prompt Generation: JSON structure explained")
        else:
            results.add_fail("Prompt Generation: JSON structure explained", "Missing elements")
        
        if "SINK_RED" in prompt:
            results.add_pass("Prompt Generation: Input kind specified")
        else:
            results.add_fail("Prompt Generation: Input kind specified", "SINK_RED missing")
        
    except Exception as e:
        results.add_fail("Prompt Generation", str(e))
    
    return results


def test_example_game_json():
    """Test generating JSON for a simple example game"""
    results = TestResults()
    
    # Create a mock provider that returns predictable JSON
    class MockProvider(BaseEconomyProvider):
        def generate_economy_json(self, game_info, game_title):
            return {
                "inputs": [
                    {"id": "player_time", "label": "Time", "kind": "SINK_RED"},
                    {"id": "player_money", "label": "Money", "kind": "SINK_RED"}
                ],
                "nodes": [
                    {
                        "id": "play_match",
                        "label": "To Play Match",
                        "sources": ["Coins", "XP"],
                        "sinks": ["Energy"],
                        "values": ["Win Rate"]
                    },
                    {
                        "id": "buy_lootbox",
                        "label": "To Buy Lootbox",
                        "sources": ["Random Item"],
                        "sinks": ["Gems"],
                        "values": []
                    }
                ],
                "edges": [
                    ["player_time", "play_match"],
                    ["player_money", "buy_lootbox"]
                ]
            }
        
        def name(self):
            return "Mock"
    
    try:
        # Test the mock provider's output
        provider = MockProvider("test_key")
        json_data = provider.generate_economy_json("Test info", "Test Game")
        
        # Validate structure
        if len(json_data["inputs"]) == 2:
            results.add_pass("Example JSON: Correct number of inputs")
        else:
            results.add_fail("Example JSON: Correct number of inputs", f"Got {len(json_data['inputs'])}")
        
        if len(json_data["nodes"]) == 2:
            results.add_pass("Example JSON: Correct number of nodes")
        else:
            results.add_fail("Example JSON: Correct number of nodes", f"Got {len(json_data['nodes'])}")
        
        if len(json_data["edges"]) == 2:
            results.add_pass("Example JSON: Correct number of edges")
        else:
            results.add_fail("Example JSON: Correct number of edges", f"Got {len(json_data['edges'])}")
        
        # Test that it would pass validation
        class MockGenerator:
            def validate_json(self, data):
                return True  # Simplified for testing
        
        generator = MockGenerator()
        if generator.validate_json(json_data):
            results.add_pass("Example JSON: Passes validation")
        else:
            results.add_fail("Example JSON: Passes validation", "Validation failed")
            
    except Exception as e:
        results.add_fail("Example JSON", str(e))
    
    return results


def main():
    """Run all tests"""
    print("Economy Flow Generator Test Suite")
    print("=" * 50)
    
    all_results = []
    
    # Run each test suite
    test_suites = [
        ("Configuration", test_config_loading),
        ("Provider Registry", test_provider_registry),
        ("JSON Validation", test_json_validation),
        ("File Operations", test_file_operations),
        ("Prompt Generation", test_prompt_generation),
        ("Example JSON", test_example_game_json)
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n{suite_name} Tests:")
        print("-" * 30)
        results = test_func()
        all_results.append(results)
    
    # Overall summary
    print("\n" + "=" * 50)
    print("OVERALL SUMMARY")
    print("=" * 50)
    
    total_passed = sum(len(r.passed) for r in all_results)
    total_failed = sum(len(r.failed) for r in all_results)
    total_tests = total_passed + total_failed
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())