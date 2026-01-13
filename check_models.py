import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AI_API_KEY")
if not api_key:
    # Try hardcoded if not in env for this script context
    api_key = "AIzaSyDdiyf6Q7GGSWbFlBqonEkRaLyYKffqHqI"

print(f"Using key: {api_key[:10]}...")

genai.configure(api_key=api_key)

print("Listing acceptable models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
