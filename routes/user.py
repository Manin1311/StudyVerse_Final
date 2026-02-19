
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, UserBadge, Todo, StudySession, TopicProficiency, UserItem, Friendship
from services.gamification import GamificationService
from services.shop import ShopService
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from flask import current_app

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Ensure badges are up to date
    GamificationService.check_badges(user)
    db.session.commit()
    
    badges = UserBadge.query.filter_by(user_id=user.id).all()
    # Calculate stats for the target user
    total_focus_minutes = db.session.query(db.func.sum(StudySession.duration))\
        .filter(StudySession.user_id == user.id).scalar() or 0
    total_focus_hours = round(total_focus_minutes / 60, 1)

    # Fetch tasks for Calendar (only if viewing own profile)
    calendar_events = []
    if current_user.is_authenticated and user.id == current_user.id:
        calendar_events = Todo.query.filter_by(user_id=user.id, completed=False)\
            .filter(Todo.due_date.isnot(None))\
            .filter(Todo.due_date != '')\
            .order_by(Todo.due_date.asc())\
            .all()

    # Get Active Frame
    active_frame = None
    active_items = UserItem.query.filter_by(user_id=user.id, is_active=True).all()
    for u_item in active_items:
        cat_item = ShopService.ITEMS.get(u_item.item_id)
        if cat_item and cat_item['type'] == 'frame':
            active_frame = cat_item
            break

    return render_template('profile.html', user=user, badges=badges, total_focus_hours=total_focus_hours, calendar_events=calendar_events, active_frame=active_frame)

@user_bp.route('/settings')
@login_required
def settings():
    return redirect(url_for('user.profile', user_id=current_user.id))

@user_bp.route('/settings/update', methods=['POST'])
@login_required
def settings_update():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip().lower()

    if not first_name or not email:
        return jsonify({'status': 'error', 'message': 'First Name and Email are required'}), 400

    current_user.first_name = first_name
    current_user.last_name = last_name
    
    # Check if email is being changed and if it's taken
    if email != current_user.email:
        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({'status': 'error', 'message': 'Email already in use'}), 400
        current_user.email = email
    current_user.about_me = data.get('about_me', current_user.about_me)

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@user_bp.route('/settings/public-profile', methods=['POST'])
@login_required
def update_public_profile():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    is_public = data.get('is_public', True)
    current_user.is_public_profile = bool(is_public)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@user_bp.route('/calendar')
@login_required
def calendar_view():
    # Only show uncompleted tasks with due dates for the calendar
    calendar_events = Todo.query.filter_by(user_id=current_user.id, completed=False)\
        .filter(Todo.due_date.isnot(None))\
        .filter(Todo.due_date != '')\
        .order_by(Todo.due_date.asc())\
        .all()
    
    return render_template('calendar.html', calendar_events=calendar_events)

@user_bp.route('/leaderboard')
@login_required
def leaderboard():
    """Global leaderboard based on level and XP - Excludes admins."""
    # Get top 50 users ordered by level (desc), then by total_xp (desc)
    # EXCLUDE ADMINS from leaderboard
    top_users = (
        User.query
        .filter(User.is_public_profile == True, User.is_admin == False)
        .order_by(User.level.desc(), User.total_xp.desc(), User.id.asc())
        .limit(50)
        .all()
    )
    
    # Calculate display ranks handling ties (Standard Competition Ranking like 1, 2, 2, 4)
    for i, user in enumerate(top_users):
        if i == 0:
            user.display_rank = 1
        else:
            prev = top_users[i-1]
            # Check for tie
            if user.total_xp == prev.total_xp and user.level == prev.level:
                user.display_rank = prev.display_rank
            else:
                user.display_rank = i + 1
    
    # Calculate current user's rank much more efficiently
    # Rank is 1 + number of users who have more level OR same level but more XP
    # EXCLUDE ADMINS from rank calculation
    my_rank = User.query.filter(
        User.is_public_profile == True,
        User.is_admin == False,
        db.or_(
            User.level > current_user.level,
            db.and_(
                User.level == current_user.level,
                User.total_xp > current_user.total_xp
            )
        )
    ).count() + 1
    
    return render_template(
        'leaderboard.html',
        leaderboard=top_users,
        my_rank=my_rank
    )

@user_bp.route('/progress')
@login_required
def progress():
    total_todos = Todo.query.filter_by(user_id=current_user.id).count()
    completed_todos = Todo.query.filter_by(user_id=current_user.id, completed=True).count()
    completion_percent = int((completed_todos / total_todos) * 100) if total_todos else 0

    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_minutes = (
        db.session.query(db.func.coalesce(db.func.sum(StudySession.duration), 0))
        .filter(StudySession.user_id == current_user.id)
        .filter(StudySession.completed_at >= week_ago)
        .scalar()
    )
    weekly_hours = round((weekly_minutes or 0) / 60.0, 2)
    sessions_week = StudySession.query.filter_by(user_id=current_user.id).filter(StudySession.completed_at >= week_ago).count()

    # Consecutive-day streak based on completed sessions.
    streak = current_user.current_streak if current_user.current_streak else 0
    # Calculate Monday of the current week
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday()) # Monday = 0
    
    daily = []
    max_hours = 0.0
    
    # Iterate Mon (0) to Sun (6)
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        start_dt = datetime.combine(day, datetime.min.time())
        end_dt = datetime.combine(day, datetime.max.time())
        
        minutes = (
            db.session.query(db.func.coalesce(db.func.sum(StudySession.duration), 0))
            .filter(StudySession.user_id == current_user.id)
            .filter(StudySession.completed_at >= start_dt)
            .filter(StudySession.completed_at <= end_dt)
            .scalar()
        )
        hours = round((minutes or 0) / 60.0, 2)
        max_hours = max(max_hours, hours)
        
        # Format label (e.g. "1.5h" or "45m")
        total_minutes = int(minutes or 0)
        display_val = ""
        if total_minutes > 0:
            if total_minutes < 60:
                display_val = f"{total_minutes}m"
            else:
                h = total_minutes // 60
                m = total_minutes % 60
                display_val = f"{h}h {m}m" if m > 0 else f"{h}h"
                
        daily.append({
            'label': day.strftime('%a'),
            'hours': hours,
            'minutes': total_minutes,
            'display': display_val,
            'is_future': day > today
        })

    for d in daily:
        # Use minutes for more precise percentage relative to max
        max_minutes = max([x['minutes'] for x in daily]) if daily else 0
        
        if max_minutes > 0:
            d['percent'] = int((d['minutes'] / max_minutes) * 100)
            if d['minutes'] > 0 and d['percent'] < 5:
                d['percent'] = 5
        else:
            d['percent'] = 0

    top_topics = (
        TopicProficiency.query
        .filter_by(user_id=current_user.id)
        .order_by(TopicProficiency.proficiency.desc())
        .limit(5)
        .all()
    )
    
    # Fetch user inventory count for streak freezes
    streak_freezes = UserItem.query.filter_by(user_id=current_user.id, item_id='streak_freeze').count()

    # Category Distribution for Pie Chart
    categories = db.session.query(Todo.category, db.func.count(Todo.id))\
        .filter(Todo.user_id == current_user.id)\
        .group_by(Todo.category).all()
    category_data = {cat or 'Uncategorized': count for cat, count in categories}

    return render_template(
        'progress.html',
        total_todos=total_todos,
        completed_todos=completed_todos,
        completion_percent=completion_percent,
        weekly_hours=weekly_hours,
        sessions_week=sessions_week,
        day_streak=streak,
        daily_hours=daily,
        top_topics=top_topics,
        streak_freezes=streak_freezes,
        category_distribution=category_data
    )

@user_bp.route('/profile/upload_cover', methods=['POST'])
@login_required
def upload_cover():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        # Use timestamp to avoid caching issues
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"cover_{current_user.id}_{timestamp}_{filename}"
        
        # Use current_app.config to access UPLOAD_FOLDER
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(save_path)
        
        # Update user profile
        current_user.cover_image = f"uploads/{unique_filename}"
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'url': url_for('static', filename=f'uploads/{unique_filename}')
        })
    
    return jsonify({'error': 'Upload failed'}), 500
