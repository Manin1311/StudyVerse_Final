
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Group, GroupMember, User, GroupChatMessage
from services.group import GroupService
from services.chat import ChatService
from utils import to_ist_time
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app
from extensions import socketio
from flask_socketio import emit

group_bp = Blueprint('group', __name__)

@group_bp.route('/group')
@login_required
def index():
    group = GroupService.get_user_group(current_user.id)
    messages = []
    members = []
    online_count = 0
    if group:
        # Load messages
        messages = (
            GroupChatMessage.query
            .filter_by(group_id=group.id)
            .order_by(GroupChatMessage.created_at.asc())
            .limit(100)
            .all()
        )
        # Load members
        members = (
            db.session.query(User)
            .join(GroupMember, GroupMember.user_id == User.id)
            .filter(GroupMember.group_id == group.id)
            .all()
        )
        
        # Attach online status (Active within last 5 minutes)
        now = datetime.utcnow()

        for m in members:
            # If last_seen is None, assume offline.
            # 5 minutes threshold
            if m.last_seen and (now - m.last_seen).total_seconds() < 300:
                m.is_online_status = True
                online_count += 1
            else:
                m.is_online_status = False

    return render_template('group_chat.html', group=group, group_messages=messages, group_members=members, online_count=online_count)

@group_bp.route('/group/create', methods=['POST'])
@login_required
def create():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Group name is required.', 'error')
        return redirect(url_for('group.index'))

    GroupService.create_group(current_user.id, name)
    return redirect(url_for('group.index'))

@group_bp.route('/group/join', methods=['POST'])
@login_required
def join():
    invite_code = request.form.get('invite_code', '').strip().upper()
    if not invite_code:
        flash('Invite code is required.', 'error')
        return redirect(url_for('group.index'))

    try:
        GroupService.join_group(current_user.id, invite_code)
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('group.index'))

@group_bp.route('/group/leave', methods=['POST'])
@login_required
def leave():
    """Leave the current group."""
    membership = GroupMember.query.filter_by(user_id=current_user.id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash('You have left the group.', 'success')
    return redirect(url_for('group.index'))

@group_bp.route('/group/send', methods=['POST'])
@login_required
def send():
    group = GroupService.get_user_group(current_user.id)
    if not group:
        flash('Join or create a group first.', 'error')
        return redirect(url_for('group.index'))

    content = request.form.get('message', '').strip()
    if not content:
        return redirect(url_for('group.index'))

    db.session.add(GroupChatMessage(group_id=group.id, user_id=current_user.id, role='user', content=content))
    db.session.commit()

    # Group AI: trigger if user mentions @StudyVerse
    if '@StudyVerse' in content.lower() or '@assistant' in content.lower():
        reply = ChatService.personal_reply(current_user, content)
        db.session.add(GroupChatMessage(group_id=group.id, user_id=None, role='assistant', content=reply))
        db.session.commit()

    return redirect(url_for('group.index'))

@group_bp.route('/group/<int:group_id>/messages')
@login_required
def get_messages(group_id):
    """Polling endpoint for group messages."""
    # Check membership
    membership = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not membership:
        return jsonify({'error': 'Not a member'}), 403

    since_id = request.args.get('since', 0, type=int)
    
    messages = (
        GroupChatMessage.query
        .filter(GroupChatMessage.group_id == group_id)
        .filter(GroupChatMessage.id > since_id)
        .order_by(GroupChatMessage.created_at.asc())
        .limit(50)
        .all()
    )
    
    # Format messages for JSON
    msg_list = []
    for m in messages:
        sender_name = 'Unknown'
        avatar = None
        if m.role == 'assistant':
            sender_name = 'AI Coach'
        elif m.user:
            sender_name = m.user.first_name
            avatar = m.user.get_avatar(64)
            
        msg_list.append({
            'id': m.id,
            'user_id': m.user_id,
            'username': sender_name,
            'avatar': avatar,
            'content': m.content,
            'file_path': m.file_path,
            'created_at': to_ist_time(m.created_at),
            'role': m.role
        })
        
    return jsonify({'messages': msg_list})

@group_bp.route('/group/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(save_path)
    
    return jsonify({
        'url': url_for('static', filename=f'uploads/{unique_filename}'),
        'filename': filename
    })
