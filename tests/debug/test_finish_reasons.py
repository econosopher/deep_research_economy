#!/usr/bin/env python3
"""Test to understand finish_reason values"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import google.generativeai as genai
from providers.secure_config import SecureConfig

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

# Check finish reason enum
from google.generativeai.types import generation_types
print("Finish Reason Enum Values:")
for name, value in generation_types.FinishReason.__members__.items():
    print(f"  {name} = {value.value}")

# Test with 2.5
model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
prompt = "Analyze the economy of Palia, a cozy farming simulation game."

try:
    response = model.generate_content(prompt)
    print(f"\nResponse candidates: {len(response.candidates) if response.candidates else 0}")
    
    if response.candidates:
        candidate = response.candidates[0]
        print(f"Finish reason value: {candidate.finish_reason}")
        print(f"Finish reason name: {candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else 'Unknown'}")
        print(f"Has parts: {bool(candidate.parts)}")
        print(f"Content: {candidate.content if hasattr(candidate, 'content') else 'No content'}")
        
        if hasattr(candidate, 'safety_ratings'):
            print("\nSafety ratings:")
            for rating in candidate.safety_ratings:
                print(f"  {rating.category.name}: {rating.probability.name} (blocked: {rating.blocked})")
                
except Exception as e:
    print(f"Error: {e}")