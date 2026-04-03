# Gemini LLM Integration Guide

This guide provides step-by-step instructions to integrate Google Gemini API into your Django application using the `google-genai` Python package.

## Prerequisites

- Python 3.8 or higher
- Django installed in your project
- Google account with access to Google AI Studio

## Step 1: Obtain API Key

1. Visit [Google AI Studio API Keys](https://aistudio.google.com/api-keys)
2. Create a new API key or copy an existing one
3. Keep the key secure and never commit it to version control

## Step 2: Install Dependencies

Install the Google Generative AI package using pip:

```bash
pip install google-genai
```

For more information, refer to the [Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart).

## Step 3: Configure API Key

Create a `.env` file in your project root and add your API key:

```env
GEMINI_API_KEY=your_api_key_here
```

**Alternative:** You can pass the API key directly to the client function (less secure).

## Step 4: Initialize and Use the Model

Here's a sample Python implementation:

```python
import google.generativeai as genai
from django.conf import settings

# Load API key from environment or settings
GEMINI_API_KEY = "your api key"
# or os.getenv("GEMINI_API_KEY")


# Initialize client
client = genai.Client(api_key=GEMINI_API_KEY)

# Generate content
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words"
)

# Get the response
answer = response.text
print(answer)
```

### Parameters Explained

- **model**: The model to use (see [Available Models](#available-models) section). Choose based on your usage requirements.
- **contents**: Your input prompt or system message

## Available Models

For the most up-to-date information on rate limits, visit:
- [Gemini API Rate Limits Documentation](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Google AI Studio Rate Limit Dashboard](https://aistudio.google.com/rate-limit?timeRange=last-28-days) (most precise)

### Rate Limits Overview

| Model Name | Model ID | Category | RPM | TPM (Input) | RPD |
|------------|----------|----------|-----|-------------|-----|
| Gemini 2.5 Flash | `gemini-2.5-flash` | Text-out models | 5 | 250K | 20 |
| Gemini 2.5 Flash-Lite | `gemini-2.5-flash-lite` | Text-out models | 10 | 250K | 20 |
| Gemini 3 Flash Preview | `gemini-3-flash-preview` | Text-out models | 5 | 250K | 20 |
| Gemini 3.1 Flash-Lite Preview | `gemini-3.1-flash-lite-preview` | Text-out models | 15 | 250K | 500 |
| Gemini 2.5 Pro | `gemini-2.5-pro` | Text-out models | - | - | - |
| Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | Text-out models | - | - | - |
| Gemini Embedding 001 | `gemini-embedding-001` | Embeddings | 100 | 30K | 1K |
| Gemini Embedding 2 Preview | `gemini-embedding-2-preview` | Embeddings | 100 | 30K | 1K |
| Gemini 2.5 Flash Live Preview | `gemini-2.5-flash-native-audio-preview-12-2025` | Live API | Unlimited | 1M | Unlimited |
| Imagen 4 Generate | `imagen-4.0-generate-001` | Image Generation | - | - | 25 |
| Veo 3.1 Generate Preview | `veo-3.1-generate-preview` | Video Generation | - | - | - |
| Nano Banana (Image) | `gemini-2.5-flash-image` | Image Generation | - | - | - |

**Legend:**
- **RPM**: Requests per minute
- **TPM**: Tokens per minute (input)
- **RPD**: Requests per day

## Best Practices

1. **Security**: Store your API key in environment variables, not in code
2. **Rate Limiting**: Monitor your usage against the rate limits to avoid restrictions
3. **Model Selection**: Choose models based on your performance and cost requirements
4. **Error Handling**: Implement proper error handling for API calls
5. **Caching**: Consider caching responses to reduce API calls

## Common Issues

### API Key Not Found
Ensure your `.env` file is in the project root and your Django settings properly load the environment variables using a package like `python-dotenv`.

### Rate Limit Exceeded
Check your current usage in the [Rate Limit Dashboard](https://aistudio.google.com/rate-limit) and adjust your request frequency accordingly.

## References

- [Google Gemini API Documentation](https://ai.google.dev/)
- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [AI Studio](https://aistudio.google.com/)
