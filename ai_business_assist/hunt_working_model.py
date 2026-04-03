import os, sys
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

print(f"Searching for a working model on key {api_key[:8]}...")
client = genai.Client(api_key=api_key)

found = False
try:
    for m in client.models.list():
        # Clean up the name if it has the models/ prefix already or not
        name = getattr(m, 'name', None) or getattr(m, 'model_id', None)
        if not name: continue
        
        print(f"Trying {name}...", end=" ")
        try:
            res = client.models.generate_content(model=name, contents="hi")
            if res and res.text:
                print("✅ WORKED!")
                print(f"\n--- USE THIS IN SETTINGS: {name} ---")
                with open("working_model.txt", "w") as f:
                    f.write(name)
                found = True
                break
        except Exception as e:
            print(f"❌ (Error: {str(e)[:50]})")
except Exception as e:
    print(f"FATAL: {e}")

if not found:
    print("\nNo models worked. Please check if your API key has 'Generative AI' enabled in the Google Cloud Console.")
