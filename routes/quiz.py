
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import TopicProficiency
from services.gamification import GamificationService

quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/quiz')
@login_required
def index():
    return render_template('quiz.html')


@quiz_bp.route('/api/quiz/generate', methods=['POST'])
@login_required
def generate():
    """Generate AI quiz questions based on user's topic proficiencies."""
    data = request.get_json() or {}
    num_questions = int(data.get('num_questions', 5))
    difficulty = data.get('difficulty', 'medium')
    syllabus_id = data.get('syllabus_id')

    # Get user topics to quiz on
    topics = TopicProficiency.query.filter_by(user_id=current_user.id).order_by(
        TopicProficiency.proficiency.asc()
    ).limit(10).all()

    topic_names = [t.topic_name for t in topics] if topics else ['General Knowledge']

    # Build AI prompt
    topics_str = ', '.join(topic_names[:5]) if topic_names else 'General Knowledge'
    prompt = (
        f"Generate {num_questions} multiple-choice quiz questions at {difficulty} difficulty "
        f"about these topics: {topics_str}. "
        f"Return a JSON object with a 'questions' key containing a list. "
        f"Each question must have: 'question' (string), 'topic' (string), "
        f"'options' (list of 4 strings), 'correct_index' (integer 0-3). "
        f"Return ONLY the raw JSON, no markdown or explanation."
    )

    try:
        from services.ai import call_ai_api
        import json
        raw = call_ai_api([{'role': 'user', 'content': prompt}])
        clean = raw.strip().replace('```json', '').replace('```', '').strip()
        parsed = json.loads(clean)
        questions = parsed.get('questions', parsed) if isinstance(parsed, dict) else parsed
        # Validate structure
        validated = []
        for q in questions:
            if all(k in q for k in ('question', 'options', 'correct_index')):
                validated.append({
                    'question': str(q['question']),
                    'topic': str(q.get('topic', topics_str)),
                    'options': [str(o) for o in q['options'][:4]],
                    'correct_index': int(q['correct_index'])
                })
        if not validated:
            raise ValueError("No valid questions parsed")
        return jsonify({'status': 'ok', 'questions': validated})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Could not generate quiz: {str(e)}'}), 500


@quiz_bp.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit():
    """Process quiz results, award XP and update topic proficiency."""
    data = request.get_json() or {}
    answers = data.get('answers', [])  # List of {topic, correct}
    total = int(data.get('total', len(answers)))

    if not answers or total == 0:
        return jsonify({'score': 0, 'xp_earned': 0})

    correct_count = sum(1 for a in answers if a.get('correct'))

    # Award XP: 10 per correct answer
    xp_per_correct = 10
    xp_earned = correct_count * xp_per_correct
    if xp_earned > 0:
        GamificationService.add_xp(current_user.id, 'quiz', xp_earned)

    # Update topic proficiency
    topic_scores = {}
    for a in answers:
        topic = a.get('topic', '').strip()
        if not topic:
            continue
        if topic not in topic_scores:
            topic_scores[topic] = {'correct': 0, 'total': 0}
        topic_scores[topic]['total'] += 1
        if a.get('correct'):
            topic_scores[topic]['correct'] += 1

    for topic_name, scores in topic_scores.items():
        pct = int((scores['correct'] / scores['total']) * 100) if scores['total'] else 0
        topic = TopicProficiency.query.filter_by(
            user_id=current_user.id, topic_name=topic_name
        ).first()
        if topic:
            # Blend: weighted average of existing and new score
            topic.proficiency = int((topic.proficiency * 0.7) + (pct * 0.3))
        else:
            topic = TopicProficiency(
                user_id=current_user.id,
                topic_name=topic_name,
                proficiency=pct
            )
            db.session.add(topic)

    db.session.commit()

    return jsonify({
        'score': correct_count,
        'total': total,
        'xp_earned': xp_earned
    })
