
from flask import Blueprint, render_template, redirect, url_for, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Todo, StudySession, TopicProficiency, Event, User, SupportTicket, Event
from services.gamification import GamificationService
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard_view'))
    except:
        pass
    return render_template('landing.html')

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    # Redirect admins to admin panel
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard')) # Assuming admin blueprint
    
    # Dashboard logic starts here
    total_todos = Todo.query.filter_by(user_id=current_user.id).count()
    completed_todos = Todo.query.filter_by(user_id=current_user.id, completed=True).count()
    remaining_todos = max(total_todos - completed_todos, 0)

    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_minutes = (
        db.session.query(db.func.coalesce(db.func.sum(StudySession.duration), 0))
        .filter(StudySession.user_id == current_user.id)
        .filter(StudySession.completed_at >= week_ago)
        .scalar()
    )
    weekly_hours = round((weekly_minutes or 0) / 60.0, 1)

    completion_percent = int((completed_todos / total_todos) * 100) if total_todos else 0

    topic_rows = (
        TopicProficiency.query
        .filter_by(user_id=current_user.id)
        .order_by(TopicProficiency.updated_at.desc())
        .limit(6)
        .all()
    )
    
    # Calculate average proficiency
    avg_proficiency = (
        db.session.query(db.func.coalesce(db.func.avg(TopicProficiency.proficiency), 0))
        .filter(TopicProficiency.user_id == current_user.id)
        .scalar()
    )
    avg_proficiency = int(round(avg_proficiency or 0))
    topics_covered = TopicProficiency.query.filter_by(user_id=current_user.id).count()

    recent_todos = (
        Todo.query
        .filter_by(user_id=current_user.id)
        .order_by(Todo.created_at.desc())
        .limit(5)
        .all()
    )
    upcoming_todos = (
        Todo.query
        .filter_by(user_id=current_user.id, completed=False)
        .order_by(Todo.id.desc())
        .limit(5)
        .all()
    )

    # -------------------------
    # COMPLETED PARENT TASKS
    # (Categories where every subtask is done)
    # -------------------------
    all_user_todos = Todo.query.filter_by(user_id=current_user.id).all()
    cat_map = {}
    for t in all_user_todos:
        cat = t.category if (t.category and t.category.strip()) else None
        if not cat: continue
        if cat not in cat_map:
            cat_map[cat] = []
        cat_map[cat].append(t)
    
    completed_parent_tasks = []
    today_utc = datetime.utcnow()
    start_of_week = today_utc - timedelta(days=today_utc.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    for cat, tasks in cat_map.items():
        if all(tk.completed for tk in tasks):
            # Check if at least one was completed this week
            # Or if it's a recently finished project
            recent_completion = any(tk.completed_at and tk.completed_at >= start_of_week for tk in tasks)
            if recent_completion:
                completed_parent_tasks.append(cat)

    # -------------------------
    # WEEKLY COMPLETED EVENTS
    # -------------------------
    today_date = datetime.utcnow().date()
    start_of_week_date = today_date - timedelta(days=today_date.weekday())
    week_date_strs = [(start_of_week_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    completed_events_week = (
        Event.query
        .filter_by(user_id=current_user.id, is_notified=True)
        .filter(Event.date.in_(week_date_strs))
        .order_by(Event.date.desc(), Event.time.desc())
        .all()
    )
    
    # Count online users (active in last 5 minutes)
    online_threshold = datetime.utcnow() - timedelta(minutes=5)
    online_users = User.query.filter(User.last_seen >= online_threshold).count()
    if online_users < 1:
        online_users = 1
    
    # Daily Quests (simple example quests based on user activity)
    quests = []
    # Quest 1: Complete 3 tasks today
    today_completed = Todo.query.filter_by(user_id=current_user.id, completed=True).filter(
        db.func.date(Todo.created_at) == datetime.utcnow().date()
    ).count()
    quests.append({
        'description': 'Complete 3 tasks',
        'icon': 'fa-check-circle',
        'xp_reward': 50,
        'progress': min(today_completed, 3),
        'target': 3,
        'completed': today_completed >= 3
    })
    
    # Quest 2: Study for 30 minutes
    today_study_mins = (
        db.session.query(db.func.coalesce(db.func.sum(StudySession.duration), 0))
        .filter(StudySession.user_id == current_user.id)
        .filter(db.func.date(StudySession.completed_at) == datetime.utcnow().date())
        .scalar()
    ) or 0
    quests.append({
        'description': 'Study for 30 mins',
        'icon': 'fa-clock',
        'xp_reward': 100,
        'progress': int(today_study_mins),
        'target': 30,
        'completed': today_study_mins >= 30,
        'unit': 'min'
    })
    
    # Quest 3: Maintain streak
    quests.append({
        'description': 'Daily Login Streak',
        'icon': 'fa-fire',
        'xp_reward': 20,
        'progress': current_user.current_streak,
        'target': current_user.current_streak + 1, # Always +1 target for next day
        'completed': True # Login is done
    })

    # Weekly Stats (Last 7 days)
    weekly_stats = {
        'labels': [],
        'data': []
    }
    for i in range(6, -1, -1):
        day = today_utc - timedelta(days=i)
        day_str = day.strftime('%a') # Mon, Tue...
        weekly_stats['labels'].append(day_str)
        
        # Count tasks completed on this day
        cnt = Todo.query.filter_by(user_id=current_user.id, completed=True).filter(
            db.func.date(Todo.completed_at) == day.date()
        ).count()
        weekly_stats['data'].append(cnt)

    # Habit Tracking (Mock data or real if habit table used)
    # We'll fetch habits if they exist
    habits = [] # Add habit logic if needed
    
    # Important items (Due soon)
    important_items = (
        Todo.query
        .filter_by(user_id=current_user.id, completed=False)
        .filter(Todo.priority == 'High')
        .order_by(Todo.due_date.asc())
        .limit(3)
        .all()
    )

    return render_template(
        'dashboard.html',
        total_todos=total_todos,
        completed_todos=completed_todos,
        remaining_todos=remaining_todos,
        weekly_hours=weekly_hours,
        completion_percent=completion_percent,
        topic_rows=topic_rows,
        avg_proficiency=avg_proficiency,
        topics_covered=topics_covered,
        recent_todos=recent_todos,
        upcoming_todos=upcoming_todos,
        online_users=online_users,
        quests=quests,
        # Serialize for Chart.js
        weekly_labels=weekly_stats['labels'],
        weekly_data=weekly_stats['data'],
        habits=habits,
        important_items=important_items,
        completed_parent_tasks=completed_parent_tasks,
        completed_events_week=completed_events_week
    )
