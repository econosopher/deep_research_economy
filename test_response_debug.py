#!/usr/bin/env python3
"""Debug response structure"""

import google.generativeai as genai
from providers.secure_config import SecureConfig
import json

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

# Test with 2.5
model = genai.GenerativeModel('gemini-2.5-pro-preview-03-25')
prompt = "What is 2 + 2?"  # Simple prompt that shouldn't trigger safety

try:
    response = model.generate_content(prompt)
    
    print("Response object attributes:")
    for attr in dir(response):
        if not attr.startswith('_'):
            print(f"  {attr}: {getattr(response, attr, 'N/A')}")
    
    print("\n" + "="*60)
    
    if response.candidates:
        candidate = response.candidates[0]
        print("Candidate attributes:")
        for attr in dir(candidate):
            if not attr.startswith('_'):
                try:
                    val = getattr(candidate, attr, 'N/A')
                    print(f"  {attr}: {val}")
                except:
                    print(f"  {attr}: [error getting value]")
                
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()