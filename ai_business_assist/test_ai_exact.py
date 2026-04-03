import os, sys, traceback
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print(f"Using Key: {api_key[:10]}...")

def test_specific_model(m):
    print(f"\n--- Testing: {m} ---")
    client = genai.Client(api_key=api_key)
    try:
        res = client.models.generate_content(model=m, contents="Say hi")
        print(f"SUCCESS: {res.text}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

# The list showed these!
models = [
    "gemini-2.5-flash-n", # I saw n earlier 
    "gemini-2.5-flash-live-preview-preview-12-2025",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "models/gemini-1.5-flash",
]

for m in models:
    if test_specific_model(m): break
