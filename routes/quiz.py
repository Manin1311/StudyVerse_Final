
import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import TopicProficiency
from services.quiz import QuizService
from services.gamification import GamificationService

quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/quiz')
@login_required
def index():
    return render_template('quiz.html')


@quiz_bp.route('/api/quiz/generate', methods=['POST'])
@login_required
def generate():
    """Generate AI quiz questions via QuizService."""
    data = request.get_json() or {}
    num_questions = int(data.get('num_questions', 5))
    difficulty    = str(data.get('difficulty', 'medium'))
    syllabus_id   = data.get('syllabus_id')

    try:
        questions = QuizService.generate_weakness_quiz(
            current_user.id,
            num_questions=num_questions,
            difficulty=difficulty,
            syllabus_id=syllabus_id
        )

        if not questions:
            return jsonify({
                'status': 'error',
                'message': 'Could not generate quiz questions. Please try again.'
            }), 500

        # Validate / sanitise each question
        validated = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            if not all(k in q for k in ('question', 'options', 'correct_index')):
                continue
            validated.append({
                'question':      str(q['question']),
                'topic':         str(q.get('topic', 'General')),
                'options':       [str(o) for o in q['options'][:4]],
                'correct_index': int(q['correct_index'])
            })

        if not validated:
            return jsonify({
                'status': 'error',
                'message': 'AI returned questions in an unexpected format. Please try again.'
            }), 500

        return jsonify({'status': 'ok', 'questions': validated})

    except Exception as e:
        print(f"[Quiz Generate Error] {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@quiz_bp.route('/api/quiz/submit', methods=['POST'])
@login_required
def submit():
    """Process quiz results: award XP and update topic proficiency."""
    data    = request.get_json() or {}
    answers = data.get('answers', [])   # list of {topic, correct}
    total   = int(data.get('total', len(answers)))

    if not answers or total == 0:
        return jsonify({'score': 0, 'xp_earned': 0, 'total': 0})

    correct_count = sum(1 for a in answers if a.get('correct'))

    # Award XP: 10 per correct answer
    xp_earned = correct_count * 10
    if xp_earned > 0:
        GamificationService.add_xp(current_user.id, 'quiz', xp_earned)

    # Update topic proficiency scores
    topic_scores = {}
    for a in answers:
        topic = (a.get('topic') or '').strip()
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
            user_id=current_user.id,
            topic_name=topic_name
        ).first()
        if topic:
            # Weighted blend: 70% existing, 30% new score
            topic.proficiency = int(topic.proficiency * 0.7 + pct * 0.3)
        else:
            topic = TopicProficiency(
                user_id=current_user.id,
                topic_name=topic_name,
                proficiency=pct
            )
            db.session.add(topic)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[Quiz Submit DB Error] {e}")

    return jsonify({
        'score':     correct_count,
        'total':     total,
        'xp_earned': xp_earned
    })
