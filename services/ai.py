
import os
import requests
import json

# Load AI API credentials from environment
AI_API_KEY = os.getenv("AI_API_KEY", "")

def call_ai_api(messages, max_tokens=2048):
    """
    Call Google Gemini API.
    messages: list of dicts [{'role': 'user', 'content': '...'}]
    Returns: str (response content) — raises on failure
    """
    if not AI_API_KEY:
        raise ValueError("AI_API_KEY not configured. Please set it in .env or Render environment.")

    # Build conversation text
    conversation_history = ""
    for msg in messages:
        role = "User" if msg['role'] == 'user' else "Model"
        conversation_history += f"{role}: {msg['content']}\n"

    # Model selection: prefer env override, default to gemini-2.5-flash
    model_id = os.environ.get("AI_MODEL", "gemini-2.5-flash")

    # Normalise model_id: accept both 'gemini-2.5-flash' and 'models/gemini-2.5-flash'
    if not model_id.startswith("models/"):
        model_id = f"models/{model_id}"

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:generateContent?key={AI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{"text": conversation_history}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens,
        }
    }

    response = requests.post(
        endpoint,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=45
    )

    if response.status_code != 200:
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text[:300]}")

    data = response.json()

    # Handle blocked / empty candidates
    candidates = data.get('candidates', [])
    if not candidates:
        # Check for promptFeedback block reason
        feedback = data.get('promptFeedback', {})
        reason = feedback.get('blockReason', 'unknown')
        raise RuntimeError(f"Gemini returned no candidates (blockReason: {reason})")

    candidate = candidates[0]

    # Safety checks for finish reason
    finish_reason = candidate.get('finishReason', 'STOP')
    if finish_reason not in ('STOP', 'MAX_TOKENS', None):
        raise RuntimeError(f"Gemini finished with reason: {finish_reason}")

    parts = candidate.get('content', {}).get('parts', [])
    if not parts:
        raise RuntimeError("Gemini candidate had no parts/text.")

    return parts[0].get('text', '').strip()
