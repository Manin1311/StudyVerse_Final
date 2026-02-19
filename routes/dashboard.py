
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
    
    # -------------------------
    # TODAY'S STUDY MINUTES
    # -------------------------
    today_study_mins = (
        db.session.query(db.func.coalesce(db.func.sum(StudySession.duration), 0))
        .filter(StudySession.user_id == current_user.id)
        .filter(db.func.date(StudySession.completed_at) == datetime.utcnow().date())
        .scalar()
    ) or 0

    # -------------------------
    # IMPORTANT CARD DATA
    # -------------------------
    # Next upcoming event (soonest future event)
    today_str = today_date.strftime('%Y-%m-%d')
    important_event = (
        Event.query
        .filter_by(user_id=current_user.id)
        .filter(Event.date >= today_str)
        .order_by(Event.date.asc(), Event.time.asc())
        .first()
    )

    # Important todo: first try high priority due soon, else just first incomplete
    important_todo = (
        Todo.query
        .filter_by(user_id=current_user.id, completed=False, priority='High')
        .order_by(Todo.due_date.asc())
        .first()
    )
    important_todo_label = 'High Priority Task'

    if not important_todo:
        important_todo = (
            Todo.query
            .filter_by(user_id=current_user.id, completed=False)
            .order_by(Todo.due_date.asc())
            .first()
        )
        important_todo_label = 'Due Soon'

    # -------------------------
    # DAILY QUESTS
    # -------------------------
    quests = []
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
    
    quests.append({
        'description': 'Study for 30 mins',
        'icon': 'fa-clock',
        'xp_reward': 100,
        'progress': int(today_study_mins),
        'target': 30,
        'completed': today_study_mins >= 30,
        'unit': 'min'
    })
    
    quests.append({
        'description': 'Daily Login Streak',
        'icon': 'fa-fire',
        'xp_reward': 20,
        'progress': current_user.current_streak,
        'target': current_user.current_streak + 1,
        'completed': True
    })

    # -------------------------
    # WEEKLY STATS (with chart data for template)
    # -------------------------
    chart_data = []
    total_focus_mins = 0
    total_tasks_done = 0

    # Find max values for percentage scaling
    max_focus = 1
    max_tasks = 1
    raw_days = []
    for i in range(6, -1, -1):
        day = today_utc - timedelta(days=i)
        day_label = day.strftime('%a')
        focus_mins = (
            db.session.query(db.func.coalesce(db.func.sum(StudySession.duration), 0))
            .filter(StudySession.user_id == current_user.id)
            .filter(db.func.date(StudySession.completed_at) == day.date())
            .scalar()
        ) or 0
        task_count = Todo.query.filter_by(user_id=current_user.id, completed=True).filter(
            db.func.date(Todo.completed_at) == day.date()
        ).count()
        raw_days.append({'day': day_label, 'focus_mins': focus_mins, 'task_count': task_count})
        total_focus_mins += focus_mins
        total_tasks_done += task_count
        if focus_mins > max_focus:
            max_focus = focus_mins
        if task_count > max_tasks:
            max_tasks = task_count

    for d in raw_days:
        chart_data.append({
            'day': d['day'],
            'focus_mins': d['focus_mins'],
            'task_count': d['task_count'],
            'focus_pct': int(d['focus_mins'] / max_focus * 100) if max_focus > 0 else 0,
            'task_pct': int(d['task_count'] / max_tasks * 100) if max_tasks > 0 else 0,
        })

    weekly_stats = {
        'chart': chart_data,
        'total_focus': total_focus_mins,
        'total_tasks': total_tasks_done,
    }

    # Habit Tracking
    habits = []
    
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
        weekly_stats=weekly_stats,
        habits=habits,
        important_items=important_items,
        completed_parent_tasks=completed_parent_tasks,
        completed_events_week=completed_events_week,
        # Variables required by template
        today_study_mins=today_study_mins,
        important_event=important_event,
        important_todo=important_todo,
        important_todo_label=important_todo_label,
    )
