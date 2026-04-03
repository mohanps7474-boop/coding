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

def generate_ai_content(prompt, model="models/gemini-2.5-flash"):
    """
    Generates content using Gemini. 
    Switched to gemini-2.5-flash based on availability check.
    Includes a robust multi-model fallback loop.
    """
    client = get_gemini_client()
    
    # Try models in order of preference (Gemma 3 prioritized based on key discovery)
    models_to_try = [
        "models/gemma-3-27b-it",
        "models/gemma-3-12b-it",
        "models/gemma-3-1b-it",
        "models/gemini-2.5-flash",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
    ]
    
    last_err = None
    for m in models_to_try:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt
            )
            if response and hasattr(response, 'text'):
                return response.text
        except Exception as e:
            last_err = e
            error_str = str(e)
            print(f"GenAI: Attempt with {m} failed: {error_str}")
            if 'RESOURCE_EXHAUSTED' in error_str:
                # Quota hit, don't keep trying others
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
