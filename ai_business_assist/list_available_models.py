import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print("Fetching available models...")
client = genai.Client(api_key=api_key)

try:
    models = client.models.list()
    print("\nAVAILABLE MODELS:")
    for m in models:
        # Some SDKs use m.name, others use m.model_id
        name = getattr(m, 'name', None) or getattr(m, 'model_id', None)
        print(f"- {name}")
except Exception as e:
    print(f"FAILED TO LIST MODELS: {e}")
