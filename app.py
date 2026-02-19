
# ============================================================================
# StudyVerse - AI-Powered Study Companion Platform
# ============================================================================

import eventlet
eventlet.monkey_patch()

import os
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import join_room, emit

# Extensions and Models
from extensions import db, login_manager, socketio, oauth
from models import (
    User, Todo, Habit, HabitLog, ChatMessage, StudySession, TopicProficiency,
    Group, GroupMember, GroupChatMessage, SyllabusDocument, Event, AdminAction,
    SupportTicket, SupportMessage, Friendship, Badge, UserBadge, XPHistory,
    UserItem, ActivePowerUp
)

# Services
from services.auth import AuthService
from services.gamification import GamificationService
from services.group import GroupService
from services.chat import ChatService
from services.shop import ShopService
from services.support import SupportService

# Utils
from utils import to_ist_time

# Config
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# APP CONFIGURATION
# ============================================================================

from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
database_url = os.getenv('DATABASE_URL', 'sqlite:///StudyVerse.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from sqlalchemy.pool import NullPool
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': NullPool,
    'pool_pre_ping': True,
}
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Google OAuth
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

# Session
IS_PRODUCTION = os.getenv('RENDER', False) or os.getenv('PRODUCTION', False)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Init Extensions
db.init_app(app)
login_manager.init_app(app)
oauth.init_app(app)
socketio.init_app(app)

oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

login_manager.login_view = 'auth.auth'

# ============================================================================
# BLUEPRINTS REGISTRATION
# ============================================================================

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.admin import admin_bp
from routes.todos import todos_bp
from routes.user import user_bp
from routes.group import group_bp
from routes.chat import chat_bp
from routes.shop import shop_bp
from routes.support import support_bp
from routes.syllabus import syllabus_bp
from routes.battle import battle_bp
from routes.quiz import quiz_bp
from routes.friends import friends_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(todos_bp)
app.register_blueprint(user_bp)
app.register_blueprint(group_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(support_bp)
app.register_blueprint(syllabus_bp)
app.register_blueprint(battle_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(friends_bp)

# ============================================================================
# GLOBAL HANDLERS
# ============================================================================

@app.template_filter('ist_time')
def ist_time_filter(utc_datetime):
    return to_ist_time(utc_datetime)

app.jinja_env.globals.update(to_ist_time=to_ist_time)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def check_ban_status():
    if request.endpoint and (request.endpoint.startswith('static') or request.endpoint.startswith('auth.')):
        return None
    
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        if user and user.is_banned:
            logout_user()
            flash(f'Your account has been banned. Reason: {user.ban_reason or "Violation of terms"}', 'error')
            return redirect(url_for('auth.auth'))
    return None

@app.context_processor
def inject_support_notifications():
    unread_support = 0
    if current_user.is_authenticated:
        try:
            if current_user.is_admin:
                unread_support = SupportTicket.query.filter(
                    SupportTicket.status.in_(['open', 'in_progress']),
                    SupportTicket.admin_unread_count > 0
                ).count()
            else:
                unread_support = SupportTicket.query.filter(
                    SupportTicket.user_id == current_user.id,
                    SupportTicket.user_unread_count > 0
                ).count()
        except:
            pass
    return dict(unread_support_count=unread_support)

@app.context_processor
def inject_gamification():
    if current_user.is_authenticated:
        try:
            rank_info = GamificationService.get_rank(current_user.level)
            next_level_xp = current_user.level * 500
            progress_percent = int(((current_user.total_xp % 500) / 500) * 100)
            
            active_theme = None
            active_frame = None
            # Need to join or simple query
            active_items = UserItem.query.filter_by(user_id=current_user.id, is_active=True).all()
            for u_item in active_items:
                 cat_item = ShopService.ITEMS.get(u_item.item_id)
                 if cat_item:
                     if cat_item['type'] == 'theme':
                         active_theme = u_item.item_id
                     elif cat_item['type'] == 'frame':
                         active_frame = u_item.item_id

            return dict(
                rank_name=rank_info['name'],
                rank_icon=rank_info['icon'],
                rank_color=rank_info['color'],
                next_level_xp=next_level_xp,
                level_progress=progress_percent,
                xp_remaining=next_level_xp - current_user.total_xp,
                active_theme=active_theme,
                active_frame=active_frame
            )
        except Exception:
            return dict()
    return dict()

# ============================================================================
# SOCKET.IO EVENTS
# ============================================================================

@socketio.on('join')
def on_join(data):
    group_id = data.get('group_id')
    if group_id:
        room_name = str(group_id)
        join_room(room_name)
        print(f"✓ User {current_user.id if current_user.is_authenticated else 'Unknown'} joined room {room_name}")
        emit('joined_room', {'room': room_name})

@socketio.on('send_message')
def handle_message(data):
    group_id = data.get('group_id')
    content = data.get('content', '')
    file_path = data.get('file_path')
    
    if not group_id or not current_user.is_authenticated:
        return

    membership = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not membership:
        return

    msg = GroupChatMessage(
        group_id=group_id,
        user_id=current_user.id,
        role='user',
        content=content,
        file_path=file_path
    )
    db.session.add(msg)
    db.session.commit()

    ist_time = to_ist_time(msg.created_at)
    
    message_data = {
        'id': msg.id,
        'user_id': current_user.id,
        'username': current_user.first_name or 'User',
        'content': msg.content,
        'file_path': msg.file_path,
        'created_at': ist_time,
        'role': 'user'
    }

    emit('receive_message', message_data, room=str(group_id), broadcast=True)

    # AI Logic
    if '@StudyVerse' in content.lower() or '@assistant' in content.lower():
        reply = ChatService.personal_reply(current_user, content)
        ai_msg = GroupChatMessage(group_id=group_id, user_id=None, role='assistant', content=reply)
        db.session.add(ai_msg)
        db.session.commit()
        
        ai_ist_time = to_ist_time(ai_msg.created_at)
        
        socketio.emit('receive_message', {
            'id': ai_msg.id,
            'user_id': None,
            'username': 'StudyVerse',
            'content': ai_msg.content,
            'created_at': ai_ist_time,
            'role': 'assistant'
        }, room=str(group_id), include_self=True)

# BATTLE SOCKETS
# In-memory battle state
battles = {}

def generate_room_code(length=4):
    import random, string
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in battles:
            return code

@socketio.on('battle_create')
def on_battle_create(data):
    if not current_user.is_authenticated:
        return
    
    room_code = generate_room_code()
    battles[room_code] = {
        'host': current_user.id,
        'players': {
            current_user.id: {
                'name': current_user.first_name or 'Player 1',
                'sid': request.sid,
                'joined_at': datetime.utcnow()
            }
        },
        'state': 'waiting',
        'config': {'difficulty': None, 'language': None},
        'problem': None,
        'submissions': {},
        'rematch_votes': {},
        'pending_join': None
    }
    
    join_room(room_code)
    emit('battle_created', {'room_code': room_code, 'player_id': current_user.id})

@socketio.on('battle_rejoin_attempt')
def on_battle_rejoin_attempt(data):
    if not current_user.is_authenticated:
        return
        
    room_code = data.get('room_code', '').strip().upper()
    if room_code not in battles:
        emit('battle_error', {'message': 'Room invalid or expired.'})
        return
        
    room = battles[room_code]
    
    if current_user.id in room['players']:
        room['players'][current_user.id]['sid'] = request.sid
        join_room(room_code)
        
        is_host = (room['host'] == current_user.id)
        
        emit('battle_rejoined', {
            'state': room['state'], 
            'room_code': room_code,
            'is_host': is_host,
            'players': [{'id': p, 'name': v['name']} for p,v in room['players'].items()]
        })
    else:
        emit('battle_error', {'message': 'You are not in this room.'})

@socketio.on('battle_join_request')
def on_battle_join_request(data):
    if not current_user.is_authenticated:
        return
        
    room_code = data.get('room_code', '').strip().upper()
    if room_code not in battles:
        emit('battle_error', {'message': 'Invalid room code.'})
        return
        
    room = battles[room_code]
    if len(room['players']) >= 2:
        emit('battle_error', {'message': 'Room is full.'})
        return

    if current_user.id in room['players']:
        room['players'][current_user.id]['sid'] = request.sid
        join_room(room_code)
        emit('battle_rejoined', {'state': room['state'], 'room_code': room_code})
        return

    room['pending_join'] = {
        'id': current_user.id,
        'name': current_user.first_name or 'Opponent',
        'sid': request.sid
    }
    
    host_sid = room['players'][room['host']]['sid']
    socketio.emit('battle_player_requesting', {
        'name': current_user.first_name or 'Opponent'
    }, room=host_sid)

@socketio.on('battle_handle_join')
def on_battle_handle_join(data):
    room_code = data.get('room_code')
    action = data.get('action') # accept / reject
    
    if room_code not in battles: return
    room = battles[room_code]
    
    if room['host'] != current_user.id: return
    
    pending = room.get('pending_join')
    if not pending: return

    if action == 'accept':
        room['players'][pending['id']] = {
            'name': pending['name'],
            'sid': pending['sid'],
            'joined_at': datetime.utcnow()
        }
        
        # Join the pending player to the room
        # We can't join_room for another SID easily here without them sending an event, 
        # but we updated their SID in our state.
        # Ideally the 'pending' player should emit 'join_room_confirmed'?
        # A simpler way: The host tells us "Accept", we broadcast "Accepted". 
        # The pending player (who is listening) then emits "battle_finalize_join".
        
        socketio.emit('battle_join_accepted', {'room_code': room_code}, room=pending['sid'])
        room['pending_join'] = None
        
        # Notify host
        emit('battle_player_joined', {'players': [{'id': p, 'name': v['name']} for p,v in room['players'].items()]}, room=room_code)
        
    else:
        socketio.emit('battle_error', {'message': 'Host rejected request.'}, room=pending['sid'])
        room['pending_join'] = None

@socketio.on('battle_finalize_join')
def on_battle_finalize_join(data):
    room_code = data.get('room_code')
    if room_code in battles and current_user.id in battles[room_code]['players']:
        join_room(room_code)

@socketio.on('battle_config')
def on_battle_config(data):
    room_code = data.get('room_code')
    if room_code not in battles: return
    room = battles[room_code]
    
    if room['host'] != current_user.id: return

    # Update config
    if 'difficulty' in data: room['config']['difficulty'] = data['difficulty']
    if 'language' in data: room['config']['language'] = data['language']
    
    emit('battle_config_updated', room['config'], room=room_code)

@socketio.on('battle_start')
def on_battle_start(data):
    room_code = data.get('room_code')
    if room_code not in battles: return
    room = battles[room_code]
    
    if room['host'] != current_user.id: return
    
    if len(room['players']) < 2:
        return # Need 2 players
        
    room['state'] = 'battle'
    
    # Generate problem using AI
    from services.ai import call_ai_api
    
    diff = room['config'].get('difficulty', 'Medium')
    lang = room['config'].get('language', 'Python')
    
    prompt = f"Generate a {diff} level coding interview problem in {lang}. Return JSON with 'title', 'description', 'examples' (list of {{input, output}}), 'constraints'."
    
    try:
        import json
        resp = call_ai_api([{'role': 'user', 'content': prompt}])
        # Clean markdown
        clean = resp.replace('```json', '').replace('```', '')
        problem = json.loads(clean)
        room['problem'] = problem
    except:
        room['problem'] = {
            'title': 'Sum of Arrays',
            'description': 'Calculate sum of array elements.', 
            'examples': [{'input': '[1,2]', 'output': '3'}]
        }

    emit('battle_started', {'problem': room['problem']}, room=room_code)

@socketio.on('battle_submit')
def on_battle_submit(data):
    room_code = data.get('room_code')
    code = data.get('code')
    
    if room_code not in battles: return
    room = battles[room_code]
    
    room['submissions'][current_user.id] = code
    
    # Notify others that this player submitted
    emit('battle_opponent_submitted', {'player_id': current_user.id}, room=room_code)
    
    # If both submitted, judge
    if len(room['submissions']) == len(room['players']):
        room['state'] = 'judging'
        emit('battle_judging', {}, room=room_code)
        
        # Trigger judging in background
        socketio.start_background_task(judge_battle, room_code)

def judge_battle(room_code):
    """Refereed by AI"""
    room = battles.get(room_code)
    if not room: return
    
    problem = room['problem']
    subs = room['submissions']
    
    # Construct AI Prompt
    prompt = f"Judge this coding battle.\nProblem: {problem['title']} - {problem['description']}\n"
    for pid, code in subs.items():
        prompt += f"Player {pid} Code:\n{code}\n\n"
        
    prompt += "Determine the winner based on correctness and efficiency. Return JSON: {'winner_id': <id or null for draw>, 'reason': '...'}"
    
    try:
        from services.ai import call_ai_api
        import json
        resp = call_ai_api([{'role': 'user', 'content': prompt}])
        clean = resp.replace('```json', '').replace('```', '')
        result = json.loads(clean)
        
        winner_id = result.get('winner_id')
        
        # Award XP
        with app.app_context():
            if winner_id:
                winner_id = int(winner_id)
                GamificationService.add_xp(winner_id, 'battle_win', 50)
                # Loser gets participation
                for pid in room['players']:
                    if int(pid) != winner_id:
                        GamificationService.add_xp(int(pid), 'battle_loss', 10)
            else:
                # Draw
                for pid in room['players']:
                    GamificationService.add_xp(int(pid), 'battle_draw', 20)
            
            db.session.commit()
            
        socketio.emit('battle_result', result, room=room_code)
        room['state'] = 'result'
        
    except Exception as e:
        print(f"Judging error: {e}")
        socketio.emit('battle_result', {'winner_id': None, 'reason': 'Error during judging'}, room=room_code)

@socketio.on('battle_rematch_vote')
def on_battle_rematch(data):
    room_code = data.get('room_code')
    if room_code not in battles: return
    
    room = battles[room_code]
    room['rematch_votes'][current_user.id] = 'yes'
    
    if len(room['rematch_votes']) == 2:
        # Reset game
        room['state'] = 'setup'
        room['problem'] = None
        room['submissions'] = {}
        room['rematch_votes'] = {}
        emit('battle_reset', {}, room=room_code)

# ============================================================================
# SCHEDULER
# ============================================================================

def check_task_reminders():
    while True:
        try:
            with app.app_context():
                now_utc = datetime.utcnow()
                now_ist = now_utc + timedelta(hours=5, minutes=30)
                current_time_str = now_ist.strftime('%H:%M')
                current_date_str = now_ist.strftime('%Y-%m-%d')
                
                upcoming_tasks = Todo.query.filter(
                    Todo.due_date == current_date_str,
                    Todo.completed == False,
                    Todo.is_notified == False
                ).all()
                
                for task in upcoming_tasks:
                    should_notify = False
                    if not task.due_time:
                         should_notify = True
                    else:
                         if current_time_str >= task.due_time:
                             should_notify = True
                    
                    if should_notify:
                        # Email logic removed, but marking notified is important
                        task.is_notified = True
                
                db.session.commit()
        except:
            pass
        eventlet.sleep(60)

# ============================================================================
# MAIN
# ============================================================================

def init_db_schema():
    with app.app_context():
        db.create_all()
        # Add migrations logic if needed

if __name__ == '__main__':
    init_db_schema()
    eventlet.spawn(check_task_reminders)
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
