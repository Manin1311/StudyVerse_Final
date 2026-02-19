
from extensions import db
from flask_login import UserMixin
from datetime import datetime
from utils import get_rank_info
from constants import SHOP_ITEMS

# ============================================================================
# DATABASE MODELS
# ============================================================================

class UserItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.String(50), nullable=False) # e.g., 'theme_cyberpunk'
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False) # For themes/frames that need activation

class ActivePowerUp(db.Model):
    """Track active power-ups with duration and effects"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    power_up_id = db.Column(db.String(50), nullable=False)  # e.g., 'xp_boost', 'mega_xp_boost'
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # None for instant effects
    multiplier = db.Column(db.Float, default=1.0)  # For XP/time multipliers
    is_active = db.Column(db.Boolean, default=True)
    
    def is_expired(self):
        """Check if power-up has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

class User(UserMixin, db.Model):
    """User Model - Core entity representing a StudyVerse user"""
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication Fields
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(100), nullable=True, unique=True)
    
    # Profile Fields
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_image = db.Column(db.String(255), nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)
    about_me = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Gamification Fields
    total_xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)
    
    # Ban/Moderation Fields
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text, nullable=True)
    banned_at = db.Column(db.DateTime, nullable=True)
    banned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 

    # Privacy & Status
    is_public_profile = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def rank_info(self):
        return get_rank_info(self.level)

    @property
    def active_frame_color(self):
        """Returns the color of the user's equipped profile frame"""
        try:
            active_items = UserItem.query.filter_by(user_id=self.id, is_active=True).all()
            for u_item in active_items:
                cat_item = SHOP_ITEMS.get(u_item.item_id)
                if cat_item and cat_item.get('type') == 'frame':
                    return cat_item.get('color')
        except Exception:
            pass
        return None

    # Backward Compatibility
    @property
    def rank(self):
        return self.rank_info['name']

    @property
    def rank_name(self):
        return self.rank_info['name']

    @property
    def rank_icon(self):
        return self.rank_info['icon']

    @property
    def rank_color(self):
        return self.rank_info['color']
    
    def get_avatar(self, size=200):
        if self.profile_image and "ui-avatars.com" not in self.profile_image:
            return self.profile_image
        
        f_name = (self.first_name or '').strip()
        # Use single initial from first name as requested
        initials = f_name[0].upper() if f_name else "U"
        
        return f"https://ui-avatars.com/api/?name={initials}&background=0ea5e9&color=fff&size={size}"
    
    def to_dict(self):
        rank_data = get_rank_info(self.level)
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'level': self.level,
            'total_xp': self.total_xp,
            'rank': rank_data['name'],
            'rank_icon': rank_data['icon'],
            'rank_color': rank_data['color'],
            'avatar': self.get_avatar(),
            'is_public': self.is_public_profile
        }

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('support_tickets', lazy=True), foreign_keys=[user_id])
    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='general')
    status = db.Column(db.String(20), default='open')
    priority = db.Column(db.String(20), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    user_unread_count = db.Column(db.Integer, default=0)
    admin_unread_count = db.Column(db.Integer, default=1)

class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    message = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_by_user = db.Column(db.Boolean, default=False)
    read_by_admin = db.Column(db.Boolean, default=False)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), default='fa-medal')
    criteria_type = db.Column(db.String(50))
    criteria_value = db.Column(db.Integer)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='badges')
    badge = db.relationship('Badge')

class XPHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='medium')
    due_date = db.Column(db.String(50))
    due_time = db.Column(db.String(20), nullable=True)
    is_notified = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    is_group = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    syllabus_id = db.Column(db.Integer, db.ForeignKey('syllabus_document.id'), nullable=True)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    completed_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_group = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    mode = db.Column(db.String(20), default='focus')
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class TopicProficiency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_name = db.Column(db.String(200), nullable=False)
    proficiency = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invite_code = db.Column(db.String(10), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
    )

class GroupChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='group_messages')

class SyllabusDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    extracted_text = db.Column(db.Text, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    extraction_status = db.Column(db.String(20), default='pending')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='syllabus_documents')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=True)
    is_notified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship('User', backref='admin_actions')
