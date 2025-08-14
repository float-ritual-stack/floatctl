#!/usr/bin/env python3
"""
Test LangExtract API connection and extraction capabilities.
This script helps diagnose why extractions aren't returning results.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import langextract as lx

# Load environment variables
env_local = Path.home() / '.env.local'
if env_local.exists():
    load_dotenv(env_local)
    print(f"✅ Loaded environment from {env_local}")

# Get API key
api_key = os.environ.get('LANGEXTRACT_API_KEY') or os.environ.get('GEMINI_API_KEY')

if not api_key:
    print("❌ No API key found in environment")
    exit(1)

print(f"🔑 API Key loaded: {api_key[:20]}... (length: {len(api_key)})")

# Test 1: Simple extraction with minimal example
print("\n" + "="*50)
print("TEST 1: Minimal extraction test")
print("="*50)

try:
    # Super simple test case
    simple_text = "The cat is brown."
    simple_prompt = "Extract the color of the cat"
    simple_examples = [
        lx.data.ExampleData(
            text="The dog is black.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="color",
                    extraction_text="black"
                )
            ]
        )
    ]
    
    print(f"Input text: {simple_text}")
    print(f"Prompt: {simple_prompt}")
    
    result = lx.extract(
        text_or_documents=simple_text,
        prompt_description=simple_prompt,
        examples=simple_examples,
        model_id="gemini-2.0-flash-exp",  # Try the newer model
        api_key=api_key,
    )
    
    print(f"✅ API call successful!")
    print(f"Extractions found: {len(result.extractions)}")
    for ext in result.extractions:
        print(f"  → {ext.extraction_class}: {ext.extraction_text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

# Test 2: FLOAT pattern extraction
print("\n" + "="*50)
print("TEST 2: FLOAT pattern extraction")
print("="*50)

try:
    float_text = "ctx::2025-08-14 @ 3:00 PM - working on evna fix"
    float_prompt = "Extract FLOAT consciousness patterns"
    float_examples = [
        lx.data.ExampleData(
            text="ctx::2025-08-14 @ 12:30 PM - [mode:: work]",
            extractions=[
                lx.data.Extraction(
                    extraction_class="ctx",
                    extraction_text="2025-08-14 @ 12:30 PM - [mode:: work]"
                )
            ]
        )
    ]
    
    print(f"Input text: {float_text}")
    print(f"Prompt: {float_prompt}")
    
    result = lx.extract(
        text_or_documents=float_text,
        prompt_description=float_prompt,
        examples=float_examples,
        model_id="gemini-2.0-flash-exp",
        api_key=api_key,
    )
    
    print(f"✅ API call successful!")
    print(f"Extractions found: {len(result.extractions)}")
    for ext in result.extractions:
        print(f"  → {ext.extraction_class}: {ext.extraction_text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

# Test 3: Multi-pattern extraction (the evna killer)
print("\n" + "="*50)
print("TEST 3: Multi-pattern extraction (evna killer)")
print("="*50)

try:
    multi_text = "eureka:: Found it! decision:: Fix tomorrow"
    multi_prompt = "Extract all FLOAT patterns"
    multi_examples = [
        lx.data.ExampleData(
            text="eureka:: Bug found! decision:: Patch it",
            extractions=[
                lx.data.Extraction(
                    extraction_class="eureka",
                    extraction_text="Bug found!"
                ),
                lx.data.Extraction(
                    extraction_class="decision",
                    extraction_text="Patch it"
                )
            ]
        )
    ]
    
    print(f"Input text: {multi_text}")
    print(f"Prompt: {multi_prompt}")
    
    result = lx.extract(
        text_or_documents=multi_text,
        prompt_description=multi_prompt,
        examples=multi_examples,
        model_id="gemini-2.0-flash-exp",
        api_key=api_key,
    )
    
    print(f"✅ API call successful!")
    print(f"Extractions found: {len(result.extractions)}")
    for ext in result.extractions:
        print(f"  → {ext.extraction_class}: {ext.extraction_text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

# Test 4: Try different model variants
print("\n" + "="*50)
print("TEST 4: Testing different Gemini models")
print("="*50)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-pro"
]

test_text = "highlight:: Important finding"
test_prompt = "Extract the highlight"
test_examples = [
    lx.data.ExampleData(
        text="highlight:: Key insight",
        extractions=[
            lx.data.Extraction(
                extraction_class="highlight",
                extraction_text="Key insight"
            )
        ]
    )
]

for model in models_to_test:
    try:
        print(f"\nTrying model: {model}")
        result = lx.extract(
            text_or_documents=test_text,
            prompt_description=test_prompt,
            examples=test_examples,
            model_id=model,
            api_key=api_key,
        )
        print(f"  ✅ {model} works! Found {len(result.extractions)} extractions")
        if result.extractions:
            for ext in result.extractions:
                print(f"    → {ext.extraction_class}: {ext.extraction_text}")
            break  # Found a working model
    except Exception as e:
        print(f"  ❌ {model} failed: {str(e)[:50]}...")

print("\n" + "="*50)
print("Diagnostics complete!")
print("="*50)