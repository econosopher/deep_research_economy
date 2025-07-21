"""
Google Gemini provider for economy flow generation with deep research capabilities
"""

import json
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from .base_provider import BaseEconomyProvider


class GeminiProvider(BaseEconomyProvider):
    """Gemini-based economy flow provider with deep research."""
    
    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-pro'):
        """Initialize Gemini provider with configurable model.
        
        Args:
            api_key: Google API key
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
                       Options: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
        """
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        # Configure generation settings for JSON output
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
    
    def name(self) -> str:
        """Return the name of the provider."""
        return "Gemini"
    
    def deep_research_phase1(self, game_info: str, game_title: str) -> str:
        """Phase 1: Initial comprehensive research on game mechanics."""
        research_prompt = f"""You are an expert video game economist conducting deep research on "{game_title}".

Based on this information:
{game_info}

Conduct Phase 1 research focusing on:

1. **Game Overview**:
   - Genre and core mechanics
   - Target audience and play patterns
   - Platform and business model

2. **Core Systems Inventory**:
   - List ALL currencies (premium, soft, event-specific)
   - List ALL resources (materials, items, consumables)
   - List ALL progression metrics (XP, levels, ranks, prestige)
   - List ALL time-gated systems (energy, tickets, cooldowns)

3. **Activity Mapping**:
   - Primary gameplay activities (battles, quests, matches)
   - Secondary activities (crafting, trading, socializing)
   - Meta activities (collection, achievements, leaderboards)
   - Monetized activities (purchases, passes, subscriptions)

4. **Player Journey Stages**:
   - Tutorial/Onboarding phase
   - Early game (first 7 days)
   - Mid game (first month)
   - Late game (month+)
   - End game (max level/prestige)

Provide comprehensive details for each section. Be specific about names, quantities, and relationships."""

        try:
            response = self.model.generate_content(
                research_prompt,
                generation_config=self.generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error in research phase 1: {e}")
            raise
    
    def deep_research_phase2(self, phase1_results: str, game_title: str) -> str:
        """Phase 2: Analyze resource flows and economy loops."""
        research_prompt = f"""Based on Phase 1 research of {game_title}:

{phase1_results}

Conduct Phase 2 research focusing on RESOURCE FLOWS:

1. **Input-Output Analysis**:
   For each activity, specify:
   - Inputs required (costs, tickets, energy)
   - Outputs produced (rewards, currencies, items)
   - Permanent gains (XP, achievements, unlocks)
   - Success rates and variability

2. **Conversion Mechanisms**:
   - Currency exchanges (e.g., gems to gold)
   - Crafting recipes (materials to items)
   - Upgrade paths (items to better items)
   - Time-to-resource conversions

3. **Economy Loops**:
   - Daily loops (login → play → rewards → logout)
   - Progression loops (play → earn → upgrade → play better)
   - Monetization loops (want item → need currency → buy or grind)
   - Social loops (join guild → contribute → receive benefits)

4. **Resource Sinks**:
   - Temporary sinks (consumables, repairs)
   - Permanent sinks (upgrades, unlocks)
   - Competitive sinks (leaderboard entries)
   - Social sinks (gifts, guild contributions)

Map every significant flow of resources through the game's economy."""

        try:
            response = self.model.generate_content(
                research_prompt,
                generation_config=self.generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error in research phase 2: {e}")
            raise
    
    def deep_research_phase3(self, phase2_results: str, game_title: str) -> str:
        """Phase 3: Identify optimization paths and final goods."""
        research_prompt = f"""Based on Phase 2 research of {game_title}:

{phase2_results}

Conduct Phase 3 research on OPTIMIZATION and GOALS:

1. **Player Optimization Paths**:
   - Free-to-play optimal strategies
   - Low spender optimization ($1-20/month)
   - Whale optimization ($100+/month)
   - Time-rich vs money-rich strategies

2. **Bottlenecks and Gates**:
   - Progress bottlenecks (level gates, gear requirements)
   - Resource bottlenecks (rare materials, premium currency)
   - Time bottlenecks (energy regeneration, cooldowns)
   - Social bottlenecks (guild requirements, friend limits)

3. **Final Goods Identification**:
   - Ultimate achievements (max level, all collectibles)
   - Prestige goals (leaderboard positions, rare titles)
   - Completion goals (all content cleared, all items owned)
   - Social goals (guild leadership, community recognition)

4. **Value Propositions**:
   - What makes players feel progression?
   - What drives monetization decisions?
   - What creates long-term retention?
   - What are the "must have" vs "nice to have" purchases?

Synthesize how all systems work together to create player value and drive the economy."""

        try:
            response = self.model.generate_content(
                research_prompt,
                generation_config=self.generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error in research phase 3: {e}")
            raise
    
    def synthesize_research(self, research_phases: List[str], game_title: str) -> str:
        """Synthesize all research phases into a coherent economy model."""
        synthesis_prompt = f"""Based on comprehensive research of {game_title}, synthesize the findings into a structured economy model:

Phase 1 (Game Overview and Systems):
{research_phases[0][:2000]}...

Phase 2 (Resource Flows):
{research_phases[1][:2000]}...

Phase 3 (Optimization and Goals):
{research_phases[2][:2000]}...

Create a COMPREHENSIVE ECONOMY MODEL with:

1. **Primary Inputs**: What players invest (time, money, attention)
2. **Core Activity Nodes**: 
   - Group related activities into logical nodes
   - Each node should represent a meaningful game activity
   - Include what each node consumes, produces, and accumulates

3. **Resource Classifications**:
   - Sources: Spendable resources produced
   - Sinks: Resources consumed from elsewhere
   - Values: Permanent accumulations (cannot be spent)

4. **Flow Connections**: How activities connect and feed into each other
5. **Final Goods**: Ultimate goals and achievements
6. **Subsection Groupings**: Logical groupings of related activities

Structure this for easy conversion to the required JSON format."""

        try:
            response = self.model.generate_content(
                synthesis_prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temperature for synthesis
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error synthesizing research: {e}")
            raise
    
    def generate_economy_json(self, game_info: str, game_title: str) -> Dict[str, Any]:
        """Generate economy flow JSON using multi-phase deep research."""
        try:
            # Phase 1: Initial research
            print(f"Gemini Deep Research Phase 1: Analyzing {game_title} systems...")
            phase1 = self.deep_research_phase1(game_info, game_title)
            time.sleep(1)  # Rate limiting
            
            # Phase 2: Resource flow analysis
            print("Gemini Deep Research Phase 2: Mapping resource flows...")
            phase2 = self.deep_research_phase2(phase1, game_title)
            time.sleep(1)
            
            # Phase 3: Goals and optimization
            print("Gemini Deep Research Phase 3: Identifying optimization paths...")
            phase3 = self.deep_research_phase3(phase2, game_title)
            time.sleep(1)
            
            # Synthesize all research
            print("Synthesizing research findings...")
            synthesis = self.synthesize_research([phase1, phase2, phase3], game_title)
            
            # Generate final JSON
            print("Generating economy flow JSON...")
            json_prompt = f"""Based on this comprehensive economy model for {game_title}:

{synthesis}

{self.get_economy_prompt("", game_title)}"""

            response = self.model.generate_content(
                json_prompt,
                generation_config={
                    "temperature": 0,  # Zero temperature for JSON generation
                    "top_p": 1.0,
                    "top_k": 1,
                    "max_output_tokens": 8192,
                }
            )
            
            # Extract and parse JSON
            json_text = response.text.strip()
            
            # Clean up any markdown formatting if present
            if json_text.startswith("```"):
                json_text = json_text.split("```")[1]
                if json_text.startswith("json"):
                    json_text = json_text[4:]
            json_text = json_text.strip()
            
            economy_data = json.loads(json_text)
            
            # Validate required keys
            required_keys = ["inputs", "nodes", "edges"]
            for key in required_keys:
                if key not in economy_data:
                    raise ValueError(f"Missing required key: {key}")
            
            # Add metadata about the generation process
            economy_data["_metadata"] = {
                "provider": "gemini",
                "model": self.model_name,
                "deep_research": True,
                "research_phases": 3,
                "game_title": game_title
            }
            
            return economy_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Gemini's response: {e}")
            print(f"Response text: {json_text[:500]}...")
            raise
        except Exception as e:
            print(f"Error generating economy JSON: {e}")
            raise
    
    def validate_api_key(self) -> bool:
        """Validate that the API key works."""
        try:
            # Try a simple request to validate the key
            test_model = genai.GenerativeModel('gemini-1.5-flash')  # Use a basic model for testing
            response = test_model.generate_content("Say 'OK'")
            return True
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False
    
    @staticmethod
    def available_models():
        """Return list of available Gemini models."""
        return [
            'gemini-2.0-flash-exp',      # 2.0 Flash experimental
            'gemini-2.0-pro-exp',        # 2.0 Pro experimental
            'gemini-1.5-pro',            # 1.5 Pro (stable, default)
            'gemini-1.5-flash',          # 1.5 Flash (faster)
            'gemini-1.0-pro',            # 1.0 Pro (older stable)
        ]