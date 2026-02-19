
from extensions import db
from models import SyllabusDocument, Todo, TopicProficiency
from services.ai import call_ai_api
import random
import json

class QuizService:
    @staticmethod
    def generate_weakness_quiz(user_id: int, **kwargs):
        # 1. Identify Active Syllabus (Context Awareness)
        # By default, use the most recent (Active) syllabus.
        # IF syllabus_id is passed specifically, use that!
        requested_syllabus_id = kwargs.get('syllabus_id')
        
        if requested_syllabus_id:
             active_syllabus_id = requested_syllabus_id
        else:
             active_doc = SyllabusDocument.query.filter_by(user_id=user_id).order_by(SyllabusDocument.created_at.desc()).first()
             active_syllabus_id = active_doc.id if active_doc else None

        # 2. Get Topics from Active Syllabus Tasks
        topics_list = []
        
        if active_syllabus_id:
            # Plan A: Get categories from Todos linked to this syllabus
            # Efficient query for distinct categories in this syllabus
            relevant_todos = (
                db.session.query(Todo.category)
                .filter(Todo.user_id == user_id)
                .filter(Todo.syllabus_id == active_syllabus_id)
                .filter(Todo.category != None)
                .distinct()
                .limit(20)
                .all()
            )
            
            syllabus_categories = [r[0] for r in relevant_todos if r[0]]
            
            # Now, from these categories, which ones are "Weak"?
            if syllabus_categories:
                # Find proficiencies for these specific categories
                prof_records = (
                    TopicProficiency.query
                    .filter_by(user_id=user_id)
                    .filter(TopicProficiency.topic_name.in_(syllabus_categories))
                    .order_by(TopicProficiency.proficiency.asc()) # Lowest first
                    .limit(5)
                    .all()
                )
                
                # Add the weakest ones first
                topics_list.extend([p.topic_name for p in prof_records])
                
                # If we need more, just add random ones from the syllabus
                if len(topics_list) < 3:
                    remaining = list(set(syllabus_categories) - set(topics_list))
                    random.shuffle(remaining)
                    topics_list.extend(remaining[:3])
        
        # Fallback (If no active syllabus or no topics found in it)
        if not topics_list:
            # Fallback to old behavior: Global Weakness
            weak_topics = (
                TopicProficiency.query
                .filter_by(user_id=user_id)
                .filter(TopicProficiency.proficiency < 70)
                .order_by(TopicProficiency.proficiency.asc())
                .limit(5)
                .all()
            )
            topics_list = [t.topic_name for t in weak_topics]

        # Final Fill (if still empty)
        if len(topics_list) < 3:
             if active_syllabus_id:
                  # Force find ANY tasks from this syllabus
                  some_todos = Todo.query.filter_by(user_id=user_id, syllabus_id=active_syllabus_id).limit(20).all()
                  cats = list(set([t.category for t in some_todos if t.category]))
                  topics_list.extend(cats)
             else:
                  topics_list = ["General Study Skills", "Time Management", "Focus"]
        
        # Deduplicate and Limit
        topics_list = list(set(topics_list))[:5]
        if not topics_list:
             topics_list = ["General Knowledge"]

        num_questions = kwargs.get('num_questions', 5)
        difficulty = kwargs.get('difficulty', 'medium')
        
        # 2. Call AI
        # Minimal prompt to save tokens and ensure JSON
        topic_str = ", ".join(topics_list[:3]) # Limit to 3 topics for context
        prompt = (
            f"Create a {num_questions}-question multiple choice quiz testing knowledge on: {topic_str}. "
            f"Difficulty level: {difficulty}. "
            "Focus on identifying weaknesses. "
            "Output strictly valid JSON (no markdown formatting) in this specific format: "
            '{"questions": [{"question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0, "topic": "..."}]}'
        )

        messages = [{'role': 'user', 'content': prompt}]
        response_text = call_ai_api(messages)
        
        # 3. Parse JSON
        # Clean potential markdown codes
        clean_text = response_text.replace('```json', '').replace('```', '').strip()
        try:
            data = json.loads(clean_text)
            return data.get('questions', [])
        except json.JSONDecodeError:
            # Fallback or retry? For now, return error or mock
            print(f"Quiz JSON Parse Error: {clean_text}")
            return []
