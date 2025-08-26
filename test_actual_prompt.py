#!/usr/bin/env python3
"""Test with our actual prompts to find where it breaks"""

import google.generativeai as genai
from providers.secure_config import SecureConfig

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

game_info = """# Palia

Palia is a cozy, community simulation MMO with life-sim mechanics like farming, foraging, fishing, cooking, bug catching, mining, and housing. Players complete quests, build relationships with NPCs, craft and upgrade tools, decorate homes, and participate in events. Progression comes from skill levels, reputation, crafting tiers, and housing upgrades. Monetization includes cosmetic purchases and optional conveniences."""

# Build the actual prompt we use
research_prompt = f"""Analyze the game economy of Palia comprehensively.

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

def test_prompt(model_name, prompt, max_tokens=1000):
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Max tokens: {max_tokens}")
    print('-'*60)
    
    try:
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
        )
        
        text = response.text
        print(f"✅ SUCCESS! Got {len(text)} chars")
        print(f"Preview: {text[:200]}...")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        
        # Try without generation config
        print("\nRetrying without generation_config...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text
            print(f"✅ SUCCESS without config! Got {len(text)} chars")
            
        except Exception as e2:
            print(f"❌ Also failed without config: {e2}")

# Test progressively
print("Testing with simple prompt first...")
test_prompt("gemini-2.5-flash", "Describe Palia in one sentence", 100)

print("\n\nTesting with medium prompt...")
test_prompt("gemini-2.5-flash", "Describe the economy of Palia, a cozy farming simulation game.", 500)

print("\n\nTesting with our full prompt...")
test_prompt("gemini-2.5-flash", research_prompt, 8192)

print("\n\nTesting same with 1.5 Pro for comparison...")
test_prompt("gemini-1.5-pro", research_prompt, 8192)