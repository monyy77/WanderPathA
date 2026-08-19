import os
from dotenv import load_dotenv
from groq import Groq

# تحميل ملف .env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"Key loaded: {api_key[:8]}...{api_key[-4:] if api_key else 'None'}")

try:
    client = Groq(api_key=api_key)
    models = client.models.list()
    print("\nAvailable models on your API Key:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"\nError: {e}")