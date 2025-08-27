"""
Google Gemini provider for economy flow generation with deep research capabilities
"""

import json
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from .base_provider import BaseEconomyProvider
from .prompts import (
    gemini_phase1_prompt,
    gemini_phase2_prompt,
    gemini_phase3_prompt,
    gemini_synthesis_prompt,
    final_json_instructions_prompt,
    economy_json_response_schema,
    detail_requirements,
    repair_prompt,
    system_instruction_text,
    classification_stage_prompt,
    good_bad_examples,
)


class GeminiProvider(BaseEconomyProvider):
    """Gemini-based economy flow provider with deep research."""
    
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash-exp', depth: int = 0, required_categories: Optional[List[str]] = None):
        """Initialize Gemini provider with configurable model.
        
        Args:
            api_key: Google API key
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
                       Options: gemini-2.0-flash-exp (stable), gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash
                       Note: gemini-2.5-pro temporarily disabled due to safety blocking issues
        """
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.depth = depth
        self.required_categories = required_categories or []
        
        # Configure safety settings - but NOT for Gemini 2.5 which has a bug
        if 'gemini-2.5' in model_name:
            # Gemini 2.5 has a bug where custom safety settings cause it to block everything
            self.model = genai.GenerativeModel(model_name, system_instruction=system_instruction_text())
        else:
            # Other models work fine with custom safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            self.model = genai.GenerativeModel(model_name, safety_settings=safety_settings, system_instruction=system_instruction_text())
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
    
    def get_generation_config(self, max_tokens=16384):
        """Get generation config based on model compatibility"""
        if 'gemini-2.5' in self.model_name:
            # Gemini 2.5 has issues with all 4 params together
            # Use only 3 params to avoid safety filter false positives
            return {
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": max_tokens,
            }
        else:
            # Other models work fine with all params
            return {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
    
    def comprehensive_research(self, game_info: str, game_title: str) -> str:
        """Phase 1: Comprehensive research on game mechanics, resource flows, and progression.
        
        With Gemini 2.5's enhanced capabilities, we can analyze all aspects in a single pass:
        - Core gameplay loops and mechanics
        - Resource systems and economy flows
        - Progression and optimization paths
        - Monetization strategies
        """
        # Combine the best aspects of all three previous phases into one comprehensive prompt
        research_prompt = f"""Analyze the game economy of {game_title} comprehensively.

{game_info}

Provide a detailed analysis covering:

1. **Core Systems & Mechanics**
   - Primary gameplay loops
   - Key game mechanics and how they interconnect
   - Player actions and their outcomes

2. **Resource Flows & Economy**
   - All resource types (time, currency, items, energy, etc.)
   - How resources flow between systems
   - Conversion rates and exchange mechanisms
   - Bottlenecks and constraints

3. **Progression & Optimization**
   - Short-term, mid-term, and long-term goals
   - Progression systems and unlocks
   - Optimization strategies players use
   - End-game content and retention mechanics

4. **Monetization & Engagement**
   - How the game monetizes (if applicable)
   - Time-limited events and seasons
   - Social features and competitive elements
   - Collection and completion mechanics

Provide a thorough, structured analysis that captures all economic relationships."""

        try:
            response = self.model.generate_content(
                research_prompt + detail_requirements(self.depth, self.required_categories),
                generation_config=self.get_generation_config(16384)
            )
            
            # Check if response was blocked
            if not response.parts:
                error_msg = f"Model {self.model_name} blocked the response"
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        # Map finish_reason values to meaningful messages
                        if finish_reason == 1:
                            error_msg += " (SAFETY: Content was blocked due to safety filters)"
                        elif finish_reason == 2:
                            error_msg += " (MAX_TOKENS: Response exceeded token limit)"
                        elif finish_reason == 3:
                            error_msg += " (RECITATION: Response blocked due to recitation)"
                        elif finish_reason == 4:
                            error_msg += " (OTHER: Response blocked for other reasons)"
                        else:
                            error_msg += f" (finish_reason: {finish_reason})"
                print(f"ERROR: {error_msg}")
                
                # Suggest alternative for 2.5-pro blocking
                if self.model_name == 'gemini-2.5-pro' and finish_reason == 1:
                    print("TIP: Try using --model gemini-2.0-flash-exp or gemini-1.5-pro instead")
                    
                raise ValueError(error_msg)
            
            return response.text
            
        except Exception as e:
            print(f"ERROR in comprehensive research with {self.model_name}: {e}")
            raise
    
    def synthesize_research(self, research_phases: List[str], game_title: str) -> str:
        """Synthesize all research phases into a coherent economy model."""
        synthesis_prompt = gemini_synthesis_prompt(research_phases[0], research_phases[1], research_phases[2], game_title)

        try:
            response = self.model.generate_content(
                synthesis_prompt + detail_requirements(self.depth, self.required_categories),
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
        """Generate economy flow JSON using 2-phase deep research optimized for Gemini 2.5."""
        try:
            # Phase 1: Comprehensive research (combines previous 3 phases)
            print(f"Gemini 2.5 Phase 1: Comprehensive analysis of {game_title}...")
            comprehensive_analysis = self.comprehensive_research(game_info, game_title)
            
            # Optional classification stage for better structure
            print("Gemini 2.5 Phase 2a: Building classification table...")
            class_table_resp = self.model.generate_content(
                classification_stage_prompt(comprehensive_analysis),
                generation_config=self.get_generation_config(4096)
            )
            class_table = class_table_resp.text

            # Phase 2b: Direct JSON generation from research + classification + examples
            print("Gemini 2.5 Phase 2b: Generating structured economy JSON...")
            json_prompt = f"""Based on this comprehensive economy analysis for {game_title}:

{comprehensive_analysis}

Classification table (reference to guide JSON, not to output directly):
{class_table}

Examples to emulate:
{good_bad_examples()}

{final_json_instructions_prompt(game_title)}

IMPORTANT: Generate a complete, well-structured JSON that accurately represents all the economic relationships identified in the analysis above."""

            # For JSON generation, use minimal config for 2.5 models
            if 'gemini-2.5' in self.model_name:
                gen_cfg = {
                    "temperature": 0,
                    "max_output_tokens": 16384,  # Increased for 2.5 models
                    "response_mime_type": "application/json",
                }
            else:
                gen_cfg = {
                    "temperature": 0,
                    "top_p": 1.0,
                    "top_k": 1,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                }
            # Attempt structured schema if the SDK supports it
            try:
                gen_cfg["response_schema"] = economy_json_response_schema()
            except Exception:
                pass

            response = self.model.generate_content(
                json_prompt,
                generation_config=gen_cfg,
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
                "research_phases": 2,  # Optimized for Gemini 2.5
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

    def repair_economy_json(self, game_title: str, current_json: Dict[str, Any], issues: str) -> Dict[str, Any]:
        try:
            snippet = json.dumps(current_json, indent=2)[:6000]
            prompt = repair_prompt(game_title, snippet, issues) + "\n\n" + final_json_instructions_prompt(game_title)
            # For JSON generation, use minimal config for 2.5 models
            if 'gemini-2.5' in self.model_name:
                gen_cfg = {
                    "temperature": 0,
                    "max_output_tokens": 16384,  # Increased for 2.5 models
                    "response_mime_type": "application/json",
                }
            else:
                gen_cfg = {
                    "temperature": 0,
                    "top_p": 1.0,
                    "top_k": 1,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                }
            try:
                gen_cfg["response_schema"] = economy_json_response_schema()
            except Exception:
                pass
            response = self.model.generate_content(prompt, generation_config=gen_cfg)
            json_text = response.text.strip()
            repaired = json.loads(json_text)
            required = ["inputs", "nodes", "edges"]
            for k in required:
                if k not in repaired:
                    raise ValueError(f"Repaired JSON missing key: {k}")
            repaired["_metadata"] = {
                "provider": "gemini",
                "model": self.model_name,
                "repair": True,
                "game_title": game_title,
            }
            return repaired
        except Exception as e:
            print(f"Error repairing economy JSON: {e}")
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
            'gemini-2.5-pro',            # Gemini 2.5 Pro (stable, default)
            'gemini-2.5-flash',          # Gemini 2.5 Flash (faster)
            'gemini-2.0-flash-exp',      # 2.0 Flash experimental
            'gemini-1.5-pro-002',        # 1.5 Pro latest version
            'gemini-1.5-pro',            # 1.5 Pro (stable)
            'gemini-1.5-flash-002',      # 1.5 Flash latest version  
            'gemini-1.5-flash',          # 1.5 Flash (faster)
        ]
