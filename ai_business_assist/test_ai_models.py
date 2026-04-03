import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ai_business_assist.settings')
import django
django.setup()

from ai_business_assist.ai_utils import generate_ai_content

print("Testing AI with updated model list...")
result = generate_ai_content("Say hello in one sentence.")
if result:
    print(f"SUCCESS: {result[:200]}")
else:
    print("FAILED: All models exhausted or errored.")
