#!/usr/bin/env python3
"""Test script to debug Gemini 2.5 safety filter issues"""

import google.generativeai as genai
from providers.secure_config import SecureConfig

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

# Test prompts
simple_prompt = "What is Palia?"
game_economy_prompt = "Describe the economy of Palia, a cozy farming simulation game."
full_prompt = """Analyze the game economy of Palia comprehensively.

Palia is a cozy, community simulation MMO with life-sim mechanics like farming, foraging, fishing, cooking, bug catching, mining, and housing.

Provide a detailed analysis of the game's economy."""

# Safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

def test_model(model_name, prompt, use_safety=True):
    """Test a model with a given prompt"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Prompt: {prompt[:100]}...")
    print(f"Safety settings: {'Enabled' if use_safety else 'Default'}")
    print('-'*60)
    
    try:
        if use_safety:
            model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
        else:
            model = genai.GenerativeModel(model_name)
            
        response = model.generate_content(prompt)
        
        # Check response
        if not response.parts:
            print(f"❌ BLOCKED: No response parts")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    print(f"   Finish reason: {candidate.finish_reason}")
                    print(f"   Finish reason name: {candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else 'Unknown'}")
                if hasattr(candidate, 'safety_ratings'):
                    print(f"   Safety ratings:")
                    for rating in candidate.safety_ratings:
                        if rating.probability != 1:  # 1 = NEGLIGIBLE
                            print(f"     - {rating.category.name}: {rating.probability.name}")
        else:
            print(f"✅ SUCCESS: Got response ({len(response.text)} chars)")
            print(f"   Preview: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

# Test different models and prompts
print("Testing Gemini Models with Safety Issues\n")

# Test 1.5 Pro
test_model("gemini-1.5-pro", simple_prompt, use_safety=True)
test_model("gemini-1.5-pro", game_economy_prompt, use_safety=True)

# Test 2.5 Pro Preview with different safety configs
test_model("gemini-2.5-pro-preview-03-25", simple_prompt, use_safety=False)
test_model("gemini-2.5-pro-preview-03-25", simple_prompt, use_safety=True)
test_model("gemini-2.5-pro-preview-03-25", game_economy_prompt, use_safety=True)

# Try experimental model
test_model("gemini-exp-1206", simple_prompt, use_safety=True)

print("\n" + "="*60)
print("Testing complete")