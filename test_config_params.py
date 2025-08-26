#!/usr/bin/env python3
"""Test which generation_config parameter causes issues"""

import google.generativeai as genai
from providers.secure_config import SecureConfig

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

prompt = "Describe Palia in one paragraph"

def test_config(model_name, config_desc, **config):
    print(f"\nTesting {model_name} with {config_desc}:")
    print(f"  Config: {config}")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config=config)
        text = response.text
        print(f"  ✅ SUCCESS: Got {len(text)} chars")
    except Exception as e:
        print(f"  ❌ FAILED: {str(e)[:100]}...")

print("="*60)
print("Testing different generation_config parameters\n")

# Test each parameter individually
test_config("gemini-2.5-flash", "temperature only", temperature=0.7)
test_config("gemini-2.5-flash", "top_p only", top_p=0.95)
test_config("gemini-2.5-flash", "top_k only", top_k=40)
test_config("gemini-2.5-flash", "max_output_tokens only", max_output_tokens=1000)

# Test combinations
test_config("gemini-2.5-flash", "temperature + top_p", temperature=0.7, top_p=0.95)
test_config("gemini-2.5-flash", "temperature + top_k", temperature=0.7, top_k=40)
test_config("gemini-2.5-flash", "top_p + top_k", top_p=0.95, top_k=40)

# Test the full config
test_config("gemini-2.5-flash", "ALL params", 
            temperature=0.7, top_p=0.95, top_k=40, max_output_tokens=1000)

# Compare with 1.5
print("\n" + "="*60)
print("Comparison with Gemini 1.5 Pro:\n")
test_config("gemini-1.5-pro", "ALL params", 
            temperature=0.7, top_p=0.95, top_k=40, max_output_tokens=1000)