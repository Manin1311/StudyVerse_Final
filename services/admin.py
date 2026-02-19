
from flask import request
from extensions import db
from models import AdminAction, User, SyllabusDocument, Group, GroupMember, ChatMessage, GroupChatMessage, StudySession, Todo, XPHistory, SupportTicket, UserItem, Badge, UserBadge
from datetime import datetime, timedelta
from sqlalchemy import func

class AdminService:
    """Admin operations and utilities"""
    
    @staticmethod
    def log_action(admin_id, action, target_type=None, target_id=None, details=None):
        """Log admin action for audit trail"""
        # IP address usually comes from request context
        ip = request.remote_addr if request else '0.0.0.0'
        
        log = AdminAction(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip
        )
        db.session.add(log)
        db.session.commit()
    
    @staticmethod
    def get_dashboard_stats():
        """Get statistics for admin dashboard"""
        total_users = User.query.count()
        active_users = User.query.filter(
            User.last_seen >= datetime.utcnow() - timedelta(days=7)
        ).count()
        total_pdfs = SyllabusDocument.query.count()
        total_groups = Group.query.count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_pdfs': total_pdfs,
            'total_groups': total_groups
        }
    
    @staticmethod
    def ban_user(user_id, reason, admin_id):
        """Ban a user"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.is_banned = True
        user.ban_reason = reason
        user.banned_at = datetime.utcnow()
        user.banned_by = admin_id
        
        db.session.commit()
        
        AdminService.log_action(
            admin_id=admin_id,
            action='ban_user',
            target_type='user',
            target_id=user_id,
            details={'reason': reason}
        )
    
    @staticmethod
    def unban_user(user_id, admin_id):
        """Unban a user"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.is_banned = False
        user.ban_reason = None
        user.banned_at = None
        user.banned_by = None
        
        db.session.commit()
        
        AdminService.log_action(
            admin_id=admin_id,
            action='unban_user',
            target_type='user',
            target_id=user_id
        )

    @staticmethod
    def get_analytics():
        """View system analytics"""
        # User growth (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Activity stats
        total_messages = ChatMessage.query.count() + GroupChatMessage.query.count()
        total_tasks = Todo.query.count()
        completed_tasks = Todo.query.filter_by(completed=True).count()
        
        # Study sessions
        total_sessions = StudySession.query.count()
        total_study_time = db.session.query(func.sum(StudySession.duration)).scalar() or 0
        
        # Group activity
        total_groups = Group.query.count()
        total_group_members = GroupMember.query.count()
        
        # XP activity
        total_xp_earned = db.session.query(func.sum(XPHistory.amount)).filter(XPHistory.amount > 0).scalar() or 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = User.query.filter(User.created_at >= seven_days_ago).count()
        recent_sessions = StudySession.query.filter(StudySession.completed_at >= seven_days_ago).count()
        recent_tasks = Todo.query.filter(Todo.created_at >= seven_days_ago).count()
        
        stats = {
            'new_users_30d': new_users_30d,
            'total_messages': total_messages,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0,
            'total_sessions': total_sessions,
            'total_study_hours': round(total_study_time / 60, 1),
            'total_groups': total_groups,
            'total_group_members': total_group_members,
            'total_xp_earned': int(total_xp_earned),
            'recent_users_7d': recent_users,
            'recent_sessions_7d': recent_sessions,
            'recent_tasks_7d': recent_tasks
        }
        return stats
