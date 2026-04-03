import os
from google import genai
from django.conf import settings

def get_gemini_client():
    """
    Initializes and returns a Gemini client using the API key from settings.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in Django settings.")
    
    return genai.Client(api_key=api_key)

def generate_ai_content(prompt, model=None):
    """
    Generates content using Gemini API with multi-model fallback.
    Prioritizes lighter models first for better quota management.
    """
    client = get_gemini_client()
    
    # Ordered by quota efficiency: lighter models first, then heavier ones
    models_to_try = [
        "models/gemini-2.0-flash-lite",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash-8b",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemma-3-1b-it",
        "models/gemma-3-12b-it",
        "models/gemma-3-27b-it",
    ]
    
    # If a specific model was requested, try it first
    if model:
        models_to_try.insert(0, model)
    
    last_err = None
    for m in models_to_try:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt
            )
            if response and hasattr(response, 'text') and response.text:
                print(f"GenAI: Success with {m}")
                return response.text
        except Exception as e:
            last_err = e
            error_str = str(e)
            print(f"GenAI: {m} failed: {error_str[:150]}")
            # Only stop cycling if ALL requests are exhausted (global quota)
            if 'RESOURCE_EXHAUSTED' in error_str and 'GenerateContent' not in error_str:
                break
            continue
            
    print(f"CRITICAL: All AI models failed. Last error: {last_err}")
    return None

def generate_marketing_message(business_type, target_audience, core_benefit):
    """
    Helper function to generate a specific marketing message.
    """
    prompt = f"Create a compelling marketing message for a {business_type} business targeting {target_audience}. The main benefit is {core_benefit}. Keep it concise and engaging."
    return generate_ai_content(prompt)
