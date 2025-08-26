"""
Claude provider for economy flow generation with enhanced research support
"""

import json
from typing import Dict, Any, List
import anthropic
from anthropic import Anthropic
from .base_provider import BaseEconomyProvider
from .prompts import final_json_instructions_prompt


class ClaudeProvider(BaseEconomyProvider):
    """Claude-based economy flow provider with enhanced research support."""
    
    def __init__(self, api_key: str):
        """Initialize Claude provider."""
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
        # Use latest Claude 3.5 Sonnet model
        self.model = "claude-3-5-sonnet-latest"
    
    def name(self) -> str:
        """Return the name of the provider."""
        return "Claude"
    
    def detect_research_content(self, content: str) -> bool:
        """Detect if the content appears to be from Claude's research feature."""
        research_indicators = [
            "based on my research",
            "according to recent",
            "from what i've found",
            "research shows",
            "sources indicate",
            "current data suggests",
            "as of 20",  # Date references
            "updated information",
            "recent updates",
            "latest patch",
            "current meta",
            "according to the wiki",
            "community data"
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in research_indicators)
    
    def process_research_content(self, game_info: str, game_title: str) -> str:
        """Process content that appears to be from Claude's research feature."""
        extraction_prompt = f"""You are analyzing comprehensive research data about "{game_title}". 
The following content contains detailed research information that needs to be extracted and organized for economy analysis.

Research Content:
{game_info}

Extract and structure the following information:

1. **Currency Systems**:
   - List ALL currencies (premium, soft, event-specific)
   - Exchange rates and conversion mechanics
   - How each currency is earned and spent

2. **Monetization Model**:
   - Base game cost (if applicable)
   - Premium currency packages and pricing
   - Battle passes, subscriptions, or season passes
   - Direct purchase options

3. **Core Gameplay Activities**:
   - Main gameplay loops (matches, missions, etc.)
   - Daily/weekly activities
   - Special events or limited-time modes
   - What each activity costs and rewards

4. **Progression Systems**:
   - Player levels/ranks
   - Character/unit progression
   - Account-wide progression
   - Skill trees or mastery systems

5. **Resource Generation**:
   - How players earn each resource
   - Time-gated vs unlimited earning
   - F2P vs paying player differences

6. **Resource Sinks**:
   - What players spend resources on
   - Temporary vs permanent purchases
   - Progression gates requiring resources

7. **End Game Economy**:
   - Long-term goals and resource requirements
   - Prestige systems
   - Collection completion
   - Competitive/ranked rewards

Organize this into a clear economy structure showing how resources flow from player inputs (time/money) through various activities to achieve different goals."""
        
        return extraction_prompt
    
    def deep_research(self, game_info: str, game_title: str) -> str:
        """Perform deep research on the game to gather comprehensive economy information."""
        # Check if the input already contains research-generated content
        is_research_content = self.detect_research_content(game_info)
        
        if is_research_content:
            # Content appears to be from Claude's research feature
            research_prompt = self.process_research_content(game_info, game_title)
        else:
            # Standard analysis of provided information
            research_prompt = f"""You are an expert video game analyst. Perform comprehensive analysis of "{game_title}" based on the provided information. Focus on:

1. **Core Gameplay Loop**: Identify the primary activities players engage in repeatedly
2. **Monetization Systems**: How the game generates revenue (purchases, subscriptions, ads)
3. **Resource Types**: All currencies, materials, and progression metrics
4. **Progression Systems**: How players advance (levels, ranks, unlocks)
5. **Time Gates**: Activities limited by time (dailies, energy systems)
6. **Social Features**: Multiplayer, guilds, trading that affect economy
7. **End Game Content**: Long-term goals and activities for veteran players
8. **Event Systems**: Limited-time events that modify the economy

Based on this information:
{game_info}

Provide a detailed analysis of {game_title}'s economy, focusing on:
- All resource types and their relationships
- Player journey from start to endgame
- Monetization touchpoints
- Key gameplay loops and their rewards
- Resource sinks and sources
- Value accumulation systems

Be thorough and specific about resource names, quantities, and relationships."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": research_prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error during deep research: {e}")
            raise
    
    def refine_economy_structure(self, research_results: str, game_title: str) -> str:
        """Refine the research into a structured economy analysis."""
        refinement_prompt = f"""Based on this research about {game_title}:

{research_results}

Create a structured economy analysis with these specific sections:

1. **Primary Inputs** (what players invest):
   - List each input with its role

2. **Core Activities** (main gameplay actions):
   - List each activity with:
     - What it consumes (sinks)
     - What it produces (sources)
     - What permanent value it creates (values)

3. **Resource Flow Chains**:
   - Trace how resources flow from inputs through activities to outputs
   - Identify conversion points and exchange rates

4. **Progression Milestones**:
   - Key goals players work towards
   - What makes them "final goods" in the economy

5. **Economy Loops**:
   - Identify closed loops where resources cycle
   - Note any resource drains or infinite sources

Structure this information clearly for conversion to the JSON format."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": refinement_prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error refining economy structure: {e}")
            raise
    
    def generate_economy_json(self, game_info: str, game_title: str) -> Dict[str, Any]:
        """Generate economy flow JSON using deep research process."""
        try:
            # Detect if we're working with research-generated content
            is_research_content = self.detect_research_content(game_info)
            
            # Step 1: Deep research or extraction
            if is_research_content:
                print(f"Processing Claude research data for {game_title}...")
            else:
                print(f"Performing analysis on {game_title}...")
            research_results = self.deep_research(game_info, game_title)
            
            # Step 2: Refine into structured format
            print("Refining into structured economy analysis...")
            structured_analysis = self.refine_economy_structure(research_results, game_title)
            
            # Step 3: Generate final JSON
            print("Generating economy flow JSON...")
            json_prompt = f"""Based on this structured economy analysis of {game_title}:

{structured_analysis}

{final_json_instructions_prompt(game_title)}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": json_prompt
                    }
                ]
            )
            
            # Extract and parse JSON
            json_text = response.content[0].text.strip()
            economy_data = json.loads(json_text)
            
            # Validate required keys
            required_keys = ["inputs", "nodes", "edges"]
            for key in required_keys:
                if key not in economy_data:
                    raise ValueError(f"Missing required key: {key}")
            
            # Add metadata about the generation process
            economy_data["_metadata"] = {
                "provider": "claude",
                "model": self.model,
                "used_research_content": is_research_content,
                "game_title": game_title
            }
            
            return economy_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Claude's response: {e}")
            print(f"Response text: {json_text[:500]}...")
            raise
        except Exception as e:
            print(f"Error generating economy JSON: {e}")
            raise
    
    def validate_api_key(self) -> bool:
        """Validate that the API key works."""
        try:
            # Try a simple request to validate the key
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "Say 'OK'"
                    }
                ]
            )
            return True
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False
