
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Todo, TopicProficiency, Habit, HabitLog, StudySession
from services.gamification import GamificationService
from utils import Stack
from datetime import datetime, timedelta

todos_bp = Blueprint('todos', __name__)

@todos_bp.route('/todos')
@login_required
def index():
    personal = Todo.query.filter_by(user_id=current_user.id, is_group=False).order_by(Todo.created_at.desc()).all()
    group = Todo.query.filter_by(user_id=current_user.id, is_group=True).order_by(Todo.created_at.desc()).all()
    return render_template('todos.html', personal_todos=personal, group_todos=group)

@todos_bp.route('/todos/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title', '').strip()
    is_group = request.form.get('is_group') == '1'
    if not title:
        return redirect(url_for('todos.index'))

    todo = Todo(
        user_id=current_user.id,
        title=title,
        completed=False,
        priority=request.form.get('priority', 'medium'),
        due_date=request.form.get('due_date'),
        category=request.form.get('category'),
        is_group=is_group,
    )
    db.session.add(todo)
    db.session.commit()
    
    next_url = request.form.get('next') or request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('todos.index'))

@todos_bp.route('/todos/add_batch', methods=['POST'])
@login_required
def add_batch():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    category = data.get('category', '').strip()
    priority = data.get('priority', 'Medium')
    due_date = data.get('due_date')
    due_time = data.get('due_time')
    is_group = data.get('is_group') == '1' or data.get('is_group') is True
    subtasks = data.get('subtasks', [])

    if not subtasks:
        return jsonify({'error': 'No subtasks provided'}), 400

    created_count = 0
    for sub_title in subtasks:
        sub_title = str(sub_title).strip()
        if not sub_title:
            continue
        
        todo = Todo(
            user_id=current_user.id,
            title=sub_title,
            completed=False,
            priority=priority,
            due_date=due_date,
            due_time=due_time,
            is_notified=False,
            category=category,
            is_group=is_group,
        )
        db.session.add(todo)
        created_count += 1

    if created_count > 0:
        db.session.commit()
        return jsonify({'status': 'success', 'count': created_count})
    
    return jsonify({'status': 'no_tasks_created'})

@todos_bp.route('/todos/toggle/<int:todo_id>', methods=['POST'])
@login_required
def toggle(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()
    todo.completed = not todo.completed
    
    # Update timestamp
    if todo.completed:
        todo.completed_at = datetime.utcnow()
    else:
        todo.completed_at = None
    
    # Award XP if completing
    if todo.completed:
        GamificationService.add_xp(current_user.id, 'task', 10)
        flash('Task completed! +10 XP', 'success')
        
        # Update Topic Proficiency
        if todo.category:
            topic = TopicProficiency.query.filter_by(user_id=current_user.id, topic_name=todo.category).first()
            if not topic:
                topic = TopicProficiency(user_id=current_user.id, topic_name=todo.category, proficiency=0)
                db.session.add(topic)
            topic.proficiency += 10
            topic.updated_at = datetime.utcnow()
            
    else:
        # Deduct XP if unchecked
        GamificationService.add_xp(current_user.id, 'task_undo', -10, force_deduct=True)
        flash('Task unchecked. -10 XP', 'info')

        # Deduct Proficiency if unchecked
        if todo.category:
            topic = TopicProficiency.query.filter_by(user_id=current_user.id, topic_name=todo.category).first()
            if topic and topic.proficiency >= 10:
                topic.proficiency -= 10

    db.session.commit()
    
    next_url = request.form.get('next') or request.args.get('next')
    if next_url:
        return redirect(next_url)

    return redirect(url_for('todos.index'))

@todos_bp.route('/todos/delete/<int:todo_id>', methods=['POST'])
@login_required
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first_or_404()

    # DS concept: push deleted item into undo stack stored in session
    undo_stack = session.get('todo_undo_stack', [])
    undo_stack.append({
        'title': todo.title,
        'priority': todo.priority,
        'due_date': todo.due_date,
        'category': todo.category,
        'is_group': bool(todo.is_group),
    })
    session['todo_undo_stack'] = undo_stack[-20:]  # cap stack size

    db.session.delete(todo)
    db.session.commit()

    next_url = request.form.get('next') or request.args.get('next')
    if next_url:
        return redirect(next_url)

    return redirect(url_for('todos.index'))

@todos_bp.route('/todos/undo', methods=['POST'])
@login_required
def undo():
    undo_stack = Stack()
    for item in session.get('todo_undo_stack', []):
        undo_stack.push(item)

    last = undo_stack.pop()
    if last is None:
        return redirect(url_for('todos.index'))

    # Write the updated stack back to session
    remaining = []
    while not undo_stack.is_empty():
        remaining.append(undo_stack.pop())
    session['todo_undo_stack'] = list(reversed(remaining))

    db.session.add(Todo(
        user_id=current_user.id,
        title=last['title'],
        completed=False,
        priority=last.get('priority', 'medium'),
        due_date=last.get('due_date'),
        category=last.get('category'),
        is_group=last.get('is_group', False)
    ))
    db.session.commit()
    flash('Undo successful.', 'success')

    return redirect(url_for('todos.index'))

# -------------------------
# POMODORO ROUTES
# -------------------------
@todos_bp.route('/pomodoro')
@login_required
def pomodoro():
    return render_template('pomodoro.html')

@todos_bp.route('/pomodoro/sessions', methods=['POST'])
@login_required
def pomodoro_save_session():
    """Save completed Pomodoro session to database."""
    duration = request.form.get('duration', type=int)
    mode = request.form.get('mode', 'focus')
    
    if duration:
        study_session = StudySession(
            user_id=current_user.id,
            duration=duration,
            mode=mode,
            completed_at=datetime.utcnow()
        )
        db.session.add(study_session)
        
        # Award XP: 1 XP per minute of focus
        if mode == 'focus':
            # Check for Double Time power-up
            from models import ActivePowerUp
            active_time_boost = ActivePowerUp.query.filter_by(
                user_id=current_user.id, 
                power_up_id='double_time',
                is_active=True
            ).first()
            
            if active_time_boost and not active_time_boost.is_expired():
                study_session.duration = duration * 2
                xp_amount = duration # add_xp will handle the multiplier
            else:
                xp_amount = duration
                
            result = GamificationService.add_xp(current_user.id, 'focus', xp_amount)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Session saved'})
    
    return jsonify({'status': 'error', 'message': 'Invalid duration'}), 400

@todos_bp.route('/pomodoro/goals', methods=['GET'])
@login_required
def pomodoro_get_goals():
    """Fetch session goals (Todos with category='Session Goal')."""
    goals = Todo.query.filter_by(user_id=current_user.id, category='Session Goal').order_by(Todo.created_at.asc()).all()
    return jsonify([
        {
            'id': g.id,
            'title': g.title,
            'completed': g.completed
        } for g in goals
    ])

# -------------------------
# POMODORO GOALS (Using Todo model)
# -------------------------

@todos_bp.route('/pomodoro/goals', methods=['POST'])
@login_required
def pomodoro_add_goal():
    """Add a new session goal."""
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    goal = Todo(
        user_id=current_user.id,
        title=title,
        completed=False,
        category='Session Goal',
        priority='medium',
        is_group=False
    )
    db.session.add(goal)
    db.session.commit()
    
    return jsonify({
        'id': goal.id,
        'title': goal.title,
        'completed': goal.completed
    })

@todos_bp.route('/pomodoro/goals/<int:goal_id>/toggle', methods=['POST'])
@login_required
def pomodoro_toggle_goal(goal_id):
    """Toggle completion status of a session goal."""
    goal = Todo.query.filter_by(id=goal_id, user_id=current_user.id, category='Session Goal').first_or_404()
    goal.completed = not goal.completed
    
    if goal.completed:
        # Mini reward for session goals
        GamificationService.add_xp(current_user.id, 'session_goal', 5)
        
    db.session.commit()
    return jsonify({'status': 'success', 'completed': goal.completed})

@todos_bp.route('/pomodoro/goals/<int:goal_id>/update', methods=['POST'])
@login_required
def pomodoro_update_goal(goal_id):
    """Update title of a session goal."""
    goal = Todo.query.filter_by(id=goal_id, user_id=current_user.id, category='Session Goal').first_or_404()
    
    data = request.get_json()
    new_title = data.get('title', '').strip()
    
    if new_title:
        goal.title = new_title
        db.session.commit()
        return jsonify({'status': 'success', 'title': goal.title})
    
    return jsonify({'error': 'Empty title'}), 400

@todos_bp.route('/pomodoro/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def pomodoro_delete_goal(goal_id):
    """Delete a session goal."""
    goal = Todo.query.filter_by(id=goal_id, user_id=current_user.id, category='Session Goal').first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'status': 'success'})

# -------------------------
# HABIT TRACKER ROUTES
# -------------------------
@todos_bp.route('/habits/add', methods=['POST'])
@login_required
def habits_add():
    title = request.form.get('title', '').strip()
    if title:
        habit = Habit(user_id=current_user.id, title=title)
        db.session.add(habit)
        db.session.commit()
        flash('Habit added!', 'success')
    return redirect(url_for('dashboard.dashboard_view'))

@todos_bp.route('/habits/toggle/<int:habit_id>', methods=['POST'])
@login_required
def habits_toggle(habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    today = datetime.utcnow().date()
    
    # Check if logged for today
    log = HabitLog.query.filter_by(habit_id=habit.id, completed_date=today).first()
    
    if log:
        # Uncheck
        db.session.delete(log)
        db.session.commit()
    else:
        # Check
        log = HabitLog(habit_id=habit.id, completed_date=today)
        db.session.add(log)
        db.session.commit()
        
        # Reward
        GamificationService.add_xp(current_user.id, 'habit', 5)
        
    return jsonify({'status': 'success'})

@todos_bp.route('/habits/stats')
@login_required
def habits_stats():
    """Return JSON stats for habits (heatmap data)."""
    # Get last 365 days of habit logs for this user
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=365)
    
    logs = (
        db.session.query(HabitLog.completed_date, db.func.count(HabitLog.id))
        .join(Habit)
        .filter(Habit.user_id == current_user.id)
        .filter(HabitLog.completed_date >= start_date)
        .group_by(HabitLog.completed_date)
        .all()
    )
    
    # Convert to list of dicts {date: 'YYYY-MM-DD', count: N}
    data = {}
    for d, c in logs:
        data[d.isoformat()] = c
        
    # Format for heatmap (e.g., standard format day -> value)
    # We will assume frontend needs simple mapping date->value
    return jsonify(data)

@todos_bp.route('/habits/weekly_stats')
@login_required
def habits_weekly_stats():
    """Return percent complete per day for last 7 days."""
    today = datetime.utcnow().date()
    # Total active habits
    total_habits = Habit.query.filter_by(user_id=current_user.id).count()
    if total_habits == 0:
        return jsonify([])
        
    stats = []
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Calculate start of current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    
    for i in range(7):
        date_only = start_of_week + timedelta(days=i)
        
        # Count logs for this date
        logs_count = (
            db.session.query(db.func.count(HabitLog.id))
            .join(Habit)
            .filter(Habit.user_id == current_user.id)
            .filter(HabitLog.completed_date == date_only)
            .scalar()
        )
        
        pct = int((logs_count / total_habits) * 100)
        stats.append({
            'day': days[i],
            'pct': pct,
            'date': date_only.isoformat()
        })
        
    return jsonify(stats)

@todos_bp.route('/habit-debugger')
@login_required
def habit_debugger():
    return render_template('habit-debugger.html')
