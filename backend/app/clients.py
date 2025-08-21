from google import genai
from dotenv import load_dotenv
import os

def get_google_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ GOOGLE_API_KEY is not found in the .env file")
    return genai.Client(api_key=api_key)
