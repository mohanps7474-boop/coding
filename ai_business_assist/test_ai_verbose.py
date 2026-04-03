import os, sys, traceback
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print(f"DEBUG: Key starts with {api_key[:5]}..." if api_key else "DEBUG: Key is MISSING")

try:
    from google import genai
    print("DEBUG: google.genai imported successfully")
except ImportError:
    print("DEBUG: FAILED TO IMPORT google-genai")
    sys.exit(1)

def test_model(model_name):
    print(f"\n--- Testing model: {model_name} ---")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'OK'"
        )
        print(f"RESULT: {response.text}")
        return True
    except Exception as e:
        print(f"ERROR with {model_name}:")
        traceback.print_exc()
        return False

models_to_try = [
    "gemini-1.5-flash",
    "models/gemini-1.5-flash",
    "gemini-1.5-pro",
    "models/gemini-1.5-pro",
    "gemini-1.0-pro"
]

for m in models_to_try:
    if test_model(m):
        print(f"\n✅ FOUND WORKING MODEL: {m}")
        break
else:
    print("\n❌ ALL MODELS FAILED")
