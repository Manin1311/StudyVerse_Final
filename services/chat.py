
from models import User, Todo, ChatMessage
from utils import LRUCache
from services.ai import call_ai_api
from services.syllabus import SyllabusService

class ChatService:
    """Personal + group AI chat.
    Uses LRU cache to avoid repeated calls for same query.
    """

    _cache = LRUCache(capacity=100)

    @staticmethod
    def build_system_prompt(user: User, syllabus_text: str) -> str:
        base = (
            "You are StudyVerse, an expert AI Study Coach and academic mentor. "
            "Your goal is to help students learn effectively, stay motivated, and organize their studies.\n"
            "Guidelines:\n"
            "1. Be encouraging, structured, and clear. Use Markdown (bold, lists) for readability.\n"
            "2. The user has uploaded their syllabus/course material for REFERENCE. Do NOT generate solutions, summaries, or lessons from it unless the user EXPLICITLY asks.\n"
            "3. If the user says 'Hello' or similar, just greet them warmly and ask how you can help.\n"
            "4. Keep responses concise but helpful. Avoid long monologues unless necessary.\n"
            "5. Remember the context of the conversation."
        )
        if syllabus_text:
            base += "\n\n[REFERENCE MATERIAL - SYLLABUS/CONTENT]\n" + syllabus_text[:3000] + "\n[END REFERENCE MATERIAL]\n(Use the above material ONLY if the user asks about it.)"
        return base

    @staticmethod
    def generate_focus_plan(user: User) -> str:
        # Get pending tasks
        todos = Todo.query.filter_by(user_id=user.id, completed=False).limit(10).all()
        tasks_text = "\n".join([f"- {t.title} (Priority: {t.priority})" for t in todos])
        
        syllabus_text = SyllabusService.get_syllabus_text(user.id)
        
        prompt = (
            "You are a study coach. Based on the user's pending tasks and syllabus, "
            "create a short, actionable 3-step study plan for today. "
            "Format nicely with Markdown. Keep it encouraging.\n\n"
            f"Pending Tasks:\n{tasks_text}\n\n"
            f"Syllabus Context:\n{syllabus_text[:1000]}"
        )
        
        # Wrapping prompt in messages list expected by call_ai_api
        messages = [{'role': 'user', 'content': prompt}]
        return call_ai_api(messages)

    @staticmethod
    def generate_chat_response(user: User, message: str) -> str:
        # 1. Check Cache
        cached = ChatService._cache.get(message)
        if cached:
            return cached

        # 2. Get Context (Syllabus)
        syllabus_text = SyllabusService.get_syllabus_text(user.id)
        
        # 3. Build Prompt
        system_prompt = ChatService.build_system_prompt(user, syllabus_text)
        
        # Fetch recent chat history
        recent_chats = ChatMessage.query.filter_by(user_id=user.id, is_group=False).order_by(ChatMessage.created_at.desc()).limit(5).all()
        history = []
        for msg in reversed(recent_chats):
            history.append({'role': msg.role, 'content': msg.content})
            
        # Combine history + current question
        # Note: call_ai_api handles list of messages.
        # But we need to inject system prompt. 
        # Usually system prompt is separate, or we prepend it to first user message.
        # Here we prepend to the last user message for simplicity if API supports chat history array
        # `call_ai_api` implementation iterates messages and builds a string.
        # So we can just put system prompt at the start of the string or as a first message.
        
        # Let's add system prompt as a 'system' role or just prepend to first message?
        # `call_ai_api` logic: "User" if role=='user' else "Model"
        # It doesn't handle 'system'.
        # We'll prepend system guidelines to the very first message or the latest one?
        # App.py implementation did: `messages = history + [{'role': 'user', 'content': f"{system_prompt}\n\nUser Question: {message}"}]`
        # This attaches the huge system prompt to the latest question. That works for stateless, but consumes tokens repeatedly.
        # Given it's a simple implementation, let's stick to what app.py did.
        
        messages = history + [{'role': 'user', 'content': f"{system_prompt}\n\nUser Question: {message}"}]
        
        # 4. Call API
        try:
            response = call_ai_api(messages)
            # 5. Cache Result
            ChatService._cache.put(message, response)
            return response
        except Exception as e:
            return f"I'm having trouble connecting to my brain right now. Please try again later. (Error: {str(e)})"
            
    @staticmethod
    def personal_reply(user: User, message: str) -> str:
        """Wrapper for generate_chat_response"""
        return ChatService.generate_chat_response(user, message)
