#!/usr/bin/env python3
"""Inspect the actual response structure"""

import google.generativeai as genai
from providers.secure_config import SecureConfig

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

def inspect_response(model_name):
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print('-'*60)
    
    model = genai.GenerativeModel(model_name)
    
    try:
        response = model.generate_content("What is 2 + 2?")
        
        # Inspect response
        print("Response attributes:")
        for attr in dir(response):
            if not attr.startswith('_'):
                try:
                    val = getattr(response, attr)
                    if not callable(val):
                        print(f"  response.{attr} = {val}")
                except:
                    pass
        
        if response.candidates:
            print("\nCandidate[0] attributes:")
            candidate = response.candidates[0]
            for attr in dir(candidate):
                if not attr.startswith('_'):
                    try:
                        val = getattr(candidate, attr)
                        if not callable(val) and attr != 'safety_ratings':
                            print(f"  candidate.{attr} = {val}")
                    except:
                        pass
            
            # Check content structure
            if hasattr(candidate, 'content'):
                print("\nCandidate.content attributes:")
                content = candidate.content
                for attr in dir(content):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(content, attr)
                            if not callable(val):
                                print(f"  content.{attr} = {val}")
                        except:
                            pass
                            
                # Try to access parts directly
                if hasattr(content, 'parts'):
                    print(f"\nContent has parts: {content.parts}")
                            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Compare response structures
inspect_response("gemini-1.5-pro")
inspect_response("gemini-2.5-pro")
inspect_response("gemini-2.5-flash")