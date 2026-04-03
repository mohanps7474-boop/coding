import os, sys
from pathlib import Path
import django
from dotenv import load_dotenv

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_business_assist.settings')
django.setup()

from ai_business_assist.ai_utils import generate_ai_content

print("Testing Gemini AI Connection...")
try:
    res = generate_ai_content("Hello, this is a test and please answer with 'OK'.")
    if res:
        print(f"SUCCESS: {res}")
    else:
        print("FAILED: generate_ai_content returned None")
except Exception as e:
    print(f"CRITICAL SYSTEM ERROR: {e}")
