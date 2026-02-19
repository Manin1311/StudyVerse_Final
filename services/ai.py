
import os
import requests
import json
import base64

# Load AI API credentials from environment
AI_API_KEY = os.getenv("AI_API_KEY", "")

def call_ai_api(messages):
    """
    Call Google Gemini API (or other configured AI).
    messages: list of dicts [{'role': 'user', 'content': '...'}]
    Returns: str (response content)
    """
    if not AI_API_KEY:
         raise ValueError("AI_API_KEY not configured. Please set it in .env")

    # Extract the last user prompt
    conversation_history = ""
    for msg in messages:
        role = "User" if msg['role'] == 'user' else "Model"
        conversation_history += f"{role}: {msg['content']}\n"
    
    # Use the flash model for speed
    model_id = os.environ.get("AI_MODEL", "models/gemini-2.5-flash")
    
    # Fix for full URL in env var
    if "/" in model_id and not model_id.startswith("models/"):
         # Assume it's a model name like 'gemini-1.5-flash'
         pass 

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:generateContent?key={AI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": conversation_history}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
        }
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
        
        if response.status_code != 200:
            return f"Error: API returned {response.status_code} - {response.text}"
            
        data = response.json()
        
        # Parse Gemini response structure
        if 'candidates' in data and data['candidates']:
            content = data['candidates'][0]['content']['parts'][0]['text']
            return content
        
        return "Error: No content returned from AI."
        
    except Exception as e:
        print(f"AI API Call Failed: {e}")
        raise e
