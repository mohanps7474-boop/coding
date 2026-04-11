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
    
    # Debug print to confirm which key is active in the running server
    print(f"--- BIZBOT AI: Initializing with API key: {api_key[:6]}... (last {api_key[-4:]}) ---")
    
    return genai.Client(api_key=api_key)

def generate_ai_content(prompt, model=None):
    """
    Generates content using Gemini API with multi-model fallback.
    Prioritizes stable models first for better reliability.
    """
    client = get_gemini_client()
    
    # Available models in this environment: 2.0, 2.5, and 3.x
    models_to_try = [
        "models/gemini-flash-lite-latest",
        "models/gemini-2.0-flash",
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-lite",
        "models/gemini-3.1-flash-lite-preview",
        "models/gemini-2.5-pro",
        "models/gemini-3.1-pro-preview",
    ]
    
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
            
            # Critical check for leaked keys
            if 'leaked' in error_str.lower() or '403' in error_str:
                print(f"CRITICAL SECURITY ERROR: API key in .env has been LEAKED/BLOCKED by Google.")
                print(f"Details: {error_str}")
                return None # Stop immediately, cycling won't help a blocked key
                
            print(f"GenAI: {m} failed: {error_str[:150]}")
            
            if 'RESOURCE_EXHAUSTED' in error_str:
                # If we hit a global quota, wait/stop
                continue
            
            continue
            
    print(f"CRITICAL AI FAILURE: All models exhausted. Last error: {last_err}")
    return None

def generate_marketing_message(business_type, target_audience, core_benefit):
    """
    Helper function to generate a specific marketing message.
    """
    prompt = f"Create a compelling marketing message for a {business_type} business targeting {target_audience}. The main benefit is {core_benefit}. Keep it concise and engaging."
    return generate_ai_content(prompt)
