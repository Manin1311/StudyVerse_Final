
import os
import requests
import json
import base64
from extensions import db
from models import SyllabusDocument, Todo, TopicProficiency

AI_API_KEY = os.getenv("AI_API_KEY", "")

class SyllabusService:
    """PDF syllabus upload + extraction and retrieval."""

    @staticmethod
    def save_syllabus(user_id: int, filename: str, extracted_text: str) -> SyllabusDocument:
        doc = SyllabusDocument(user_id=user_id, filename=filename, extracted_text=extracted_text)
        db.session.add(doc)
        db.session.commit()
        return doc

    @staticmethod
    def get_syllabus_text(user_id: int) -> str:
        doc = SyllabusDocument.query.filter_by(user_id=user_id).first()
        return doc.extracted_text if doc else ""

    @staticmethod
    def extract_tasks_from_pdf(pdf_bytes: bytes) -> list:
        if not AI_API_KEY:
            raise ValueError("AI_API_KEY not configured")

        model_id = os.environ.get("GEMINI_PDF_MODEL", "models/gemini-2.5-flash")
        if "/" in model_id:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:generateContent?key={AI_API_KEY}"
        else:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={AI_API_KEY}"

        prompt = (
            "You are a study assistant. Analyze the attached PDF notes. "
            "Identify the main chapters and key topics. "
            "Output ONLY valid JSON in this exact format: "
            "{\"tasks\": [{\"title\": \"Chapter Name\", \"subtasks\": [\"Topic 1\", \"Topic 2\"]}]}"
        )

        pdf_data = base64.b64encode(pdf_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }

        response = requests.post(endpoint, json=payload, headers={'Content-Type': 'application/json'}, timeout=120)
        result_data = response.json() if response.text else {}

        if response.status_code != 200:
            error_msg = result_data.get("error", {}).get("message", response.text or "Unknown error")
            raise ValueError(f"Google Error: {error_msg}")

        if "error" in result_data:
            error_msg = result_data["error"].get("message", "Unknown API Error")
            raise ValueError(f"Google Error: {error_msg}")

        raw = ""
        if "candidates" in result_data and result_data["candidates"]:
            raw = result_data["candidates"][0]["content"]["parts"][0].get("text", "")
        if not raw:
            raise ValueError("AI could not read this PDF")

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()

        parsed = None
        # Try to parse JSON with multiple fallback approaches
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            try:
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1 and end > start:
                    parsed = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        
        if parsed is None:
            raise ValueError("AI response could not be parsed as JSON. Please try again.")

        tasks = parsed.get("tasks", [])
        if not isinstance(tasks, list):
            raise ValueError("Invalid AI response: tasks is not a list")
        return tasks

    @staticmethod
    def build_chapters_from_todos(user_id: int, syllabus_id: int = None) -> list:
        query = Todo.query.filter_by(user_id=user_id, is_group=False)
        
        if syllabus_id:
            query = query.filter_by(syllabus_id=syllabus_id)
        
        todos = query.order_by(Todo.created_at.asc()).all()

        chapters = {}
        for t in todos:
            if not t.category:
                continue
            chapters.setdefault(t.category, []).append(t)

        result = []
        for category, items in chapters.items():
            total = len(items)
            completed = sum(1 for x in items if x.completed)
            percent = int((completed / total) * 100) if total else 0
            
            # Fetch proficiency for this chapter (category)
            prof_entry = TopicProficiency.query.filter_by(user_id=user_id, topic_name=category).first()
            proficiency = prof_entry.proficiency if prof_entry else 0
            
            result.append({
                'name': category,
                'todos': items,
                'total': total,
                'completed': completed,
                'percent': percent,
                'proficiency': proficiency
            })

        result.sort(key=lambda x: x['name'].lower())
        return result
