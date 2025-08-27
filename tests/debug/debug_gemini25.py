#!/usr/bin/env python3
"""Debug Gemini 2.5 - find the real issue"""

import google.generativeai as genai
from providers.secure_config import SecureConfig

# Get API key
config = SecureConfig()
api_key = config.get_api_key('gemini')
genai.configure(api_key=api_key)

print("Testing Gemini 2.5 Models - Finding Root Cause\n")

def test_basic(model_name):
    """Test the absolute basics"""
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print('-'*60)
    
    # Create model with NO custom settings
    model = genai.GenerativeModel(model_name)
    
    # Super simple prompt
    prompt = "Say hello"
    
    try:
        print(f"Prompt: '{prompt}'")
        response = model.generate_content(prompt)
        
        print(f"Response type: {type(response)}")
        print(f"Has candidates: {bool(response.candidates)}")
        
        if response.candidates:
            candidate = response.candidates[0]
            print(f"Candidate finish_reason: {candidate.finish_reason}")
            print(f"Has parts: {bool(candidate.parts)}")
            print(f"Has content: {bool(candidate.content)}")
            
            if candidate.parts:
                print(f"Parts: {candidate.parts}")
            else:
                print("No parts in response")
                
            # Check the raw content
            if hasattr(candidate, 'content'):
                print(f"Content role: {candidate.content.role if hasattr(candidate.content, 'role') else 'N/A'}")
                print(f"Content parts: {candidate.content.parts if hasattr(candidate.content, 'parts') else 'N/A'}")
                
        # Try to get text
        try:
            text = response.text
            print(f"✅ Got text: {text[:100]}")
        except Exception as e:
            print(f"❌ Cannot get text: {e}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

# Test different models
test_basic("gemini-1.5-pro")
test_basic("gemini-2.5-flash") 
test_basic("gemini-2.5-pro")

print("\n" + "="*60)
print("\nNow testing with generation config...")

def test_with_config(model_name):
    """Test with generation config"""
    print(f"\n{'='*60}")
    print(f"Model: {model_name} WITH generation_config")
    print('-'*60)
    
    model = genai.GenerativeModel(model_name)
    
    prompt = "What is 2 + 2?"
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 100,
            }
        )
        
        text = response.text
        print(f"✅ Got text: {text[:100]}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

test_with_config("gemini-1.5-pro")
test_with_config("gemini-2.5-pro")