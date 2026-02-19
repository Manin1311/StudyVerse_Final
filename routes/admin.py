
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import (
    User, Todo, SyllabusDocument, StudySession, TopicProficiency, AdminAction,
    SupportTicket, SupportMessage, Badge, UserBadge, XPHistory, UserItem,
    Group, GroupMember, ChatMessage, GroupChatMessage
)
from services.admin import AdminService
from services.support import SupportService
from services.gamification import GamificationService
from services.shop import ShopService
from utils import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with overview statistics"""
    stats = AdminService.get_dashboard_stats()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users)

# ============================================================================
# ADMIN - USER MANAGEMENT
# ============================================================================

@admin_bp.route('/admin/users')
@login_required
@admin_required
def users():
    """List all users with search and filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    # Filter base query - exclude admins
    query = User.query.filter(User.is_admin == False)
    
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
        )
    
    if filter_type == 'active':
        query = query.filter(User.last_seen >= datetime.utcnow() - timedelta(days=7))
    elif filter_type == 'banned':
        query = query.filter(User.is_banned == True)
    
    users_pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users/list.html', users=users_pagination, search=search, filter_type=filter_type)

@admin_bp.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View detailed user information"""
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    total_tasks = Todo.query.filter_by(user_id=user.id).count()
    completed_tasks = Todo.query.filter_by(user_id=user.id, completed=True).count()
    total_pdfs = SyllabusDocument.query.filter_by(user_id=user.id).count()
    
    # Recent XP activity
    recent_xp = XPHistory.query.filter_by(user_id=user.id).order_by(XPHistory.timestamp.desc()).limit(10).all()
    
    return render_template('admin/users/detail.html',
                         user=user,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         total_pdfs=total_pdfs,
                         recent_xp=recent_xp)

@admin_bp.route('/admin/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    """Ban a user - Prevents admin from banning himself"""
    # PREVENT ADMIN FROM BANNING HIMSELF
    if user_id == current_user.id:
        flash('You cannot ban yourself!', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    reason = request.form.get('reason', 'No reason provided')
    
    try:
        AdminService.ban_user(user_id, reason, current_user.id)
        flash('User banned successfully', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/admin/users/<int:user_id>/unban', methods=['POST'])
@login_required
@admin_required
def unban_user(user_id):
    """Unban a user"""
    try:
        AdminService.unban_user(user_id, current_user.id)
        flash('User unbanned successfully', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/admin/users/<int:user_id>/adjust-xp', methods=['POST'])
@login_required
@admin_required
def adjust_xp(user_id):
    """Manually adjust user XP"""
    amount = request.form.get('amount', type=int)
    reason = request.form.get('reason', 'Admin adjustment')
    
    if not amount:
        flash('Invalid XP amount', 'error')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    user = User.query.get_or_404(user_id)
    user.total_xp = max(0, user.total_xp + amount)
    user.level = GamificationService.calculate_level(user.total_xp)
    
    # Log XP change
    log = XPHistory(user_id=user.id, source='admin', amount=amount)
    db.session.add(log)
    
    # Log admin action
    AdminService.log_action(
        admin_id=current_user.id,
        action='adjust_xp',
        target_type='user',
        target_id=user_id,
        details={'amount': amount, 'reason': reason}
    )
    
    db.session.commit()
    
    flash(f'XP adjusted by {amount:+d}', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))

# ============================================================================
# ADMIN - SUPPORT TICKETS
# ============================================================================

@admin_bp.route('/admin/support')
@login_required
@admin_required
def support():
    """List all support tickets for admin"""
    status = request.args.get('status', 'all')
    tickets = SupportService.get_admin_tickets(status)
    return render_template('admin/support/list.html', tickets=tickets, current_status=status)

@admin_bp.route('/admin/support/<int:ticket_id>')
@login_required
@admin_required
def support_detail(ticket_id):
    """View and respond to support ticket"""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    user = User.query.get(ticket.user_id)
    
    # Mark as read by admin
    unread_msgs = SupportMessage.query.filter_by(
        ticket_id=ticket.id, 
        read_by_admin=False,
        is_admin=False # Messages from user
    ).all()
    for msg in unread_msgs:
        msg.read_by_admin = True
    
    if unread_msgs:
        ticket.admin_unread_count = 0
        db.session.commit()
    
    messages = SupportMessage.query.filter_by(ticket_id=ticket.id).order_by(SupportMessage.created_at.asc()).all()
    return render_template('admin/support/detail.html', ticket=ticket, user=user, messages=messages)

@admin_bp.route('/admin/support/<int:ticket_id>/reply', methods=['POST'])
@login_required
@admin_required
def support_reply(ticket_id):
    """Admin replies to a support ticket"""
    message = request.form.get('message')
    if not message:
        flash('Message cannot be empty', 'error')
        return redirect(url_for('admin.support_detail', ticket_id=ticket_id))
        
    SupportService.add_message(ticket_id, current_user.id, message, is_admin=True)
    return redirect(url_for('admin.support_detail', ticket_id=ticket_id))

@admin_bp.route('/admin/support/<int:ticket_id>/close', methods=['POST'])
@login_required
@admin_required
def support_close(ticket_id):
    """Close a support ticket"""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = 'closed'
    ticket.closed_at = datetime.utcnow()
    db.session.commit()
    flash('Ticket closed successfully', 'success')
    return redirect(url_for('admin.support'))

# ============================================================================
# ADMIN - AUDIT LOGS
# ============================================================================

@admin_bp.route('/admin/logs')
@login_required
@admin_required
def logs():
    """View admin action audit logs"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', 'all')
    
    query = AdminAction.query
    
    if action_filter != 'all':
        query = query.filter(AdminAction.action == action_filter)
    
    logs_pagination = query.order_by(AdminAction.timestamp.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/logs/list.html', logs=logs_pagination, action_filter=action_filter)

# ============================================================================
# ADMIN - GAMIFICATION MANAGEMENT
# ============================================================================

@admin_bp.route('/admin/gamification')
@login_required
@admin_required
def gamification():
    """Manage gamification settings"""
    # Get XP stats
    total_xp = db.session.query(func.sum(User.total_xp)).scalar() or 0
    avg_xp = db.session.query(func.avg(User.total_xp)).scalar() or 0
    max_level = db.session.query(func.max(User.level)).scalar() or 0
    avg_level = db.session.query(func.avg(User.level)).scalar() or 0
    
    # Top users
    top_users = User.query.filter_by(is_admin=False).order_by(User.total_xp.desc()).limit(10).all()
    
    # Recent XP transactions
    recent_xp = XPHistory.query.order_by(XPHistory.timestamp.desc()).limit(20).all()
    
    # Badge statistics
    total_badges = Badge.query.count()
    total_earned = UserBadge.query.count()
    
    # Most earned badges
    popular_badges = db.session.query(
        Badge, func.count(UserBadge.id).label('count')
    ).join(UserBadge).group_by(Badge.id).order_by(func.count(UserBadge.id).desc()).limit(5).all()
    
    stats = {
        'total_xp': int(total_xp),
        'avg_xp': round(avg_xp, 1),
        'max_level': max_level,
        'avg_level': round(avg_level, 1),
        'total_badges': total_badges,
        'total_earned': total_earned,
        'top_users': top_users,
        'recent_xp': recent_xp,
        'popular_badges': popular_badges
    }
    
    return render_template('admin/gamification/dashboard.html', stats=stats)


# ============================================================================
# ADMIN - SHOP MANAGEMENT
# ============================================================================

@admin_bp.route('/admin/shop')
@login_required
@admin_required
def shop():
    """Manage shop items and themes"""
    # Get all purchased items
    purchased_items = UserItem.query.all()
    
    # Group by item_id to get counts
    item_stats = db.session.query(
        UserItem.item_id,
        func.count(UserItem.id).label('purchase_count')
    ).group_by(UserItem.item_id).order_by(func.count(UserItem.id).desc()).all()
    
    # Total purchases
    total_purchases = UserItem.query.count()
    unique_items = len(item_stats)
    active_items = UserItem.query.filter_by(is_active=True).count()
    
    # Recent purchases
    recent_purchases = UserItem.query.order_by(UserItem.purchased_at.desc()).limit(20).all()
    
    stats = {
        'total_purchases': total_purchases,
        'unique_items': unique_items,
        'active_items': active_items,
        'item_stats': item_stats,
        'recent_purchases': recent_purchases
    }
    
    return render_template('admin/shop/dashboard.html', stats=stats)


# ============================================================================
# ADMIN - BATTLES MANAGEMENT (Study Sessions)
# ============================================================================

@admin_bp.route('/admin/battles')
@login_required
@admin_required
def battles():
    """Manage study sessions (battles)"""
    page = request.args.get('page', 1, type=int)
    
    # Use study sessions as "battles"
    sessions = StudySession.query.order_by(StudySession.completed_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    # Get stats
    total_sessions = StudySession.query.count()
    total_focus_time = db.session.query(func.sum(StudySession.duration)).filter_by(mode='focus').scalar() or 0
    total_break_time = db.session.query(func.sum(StudySession.duration)).filter(StudySession.mode.in_(['shortBreak', 'longBreak'])).scalar() or 0
    
    # Top studiers
    top_studiers = db.session.query(
        User, func.sum(StudySession.duration).label('total_time')
    ).join(StudySession).group_by(User.id).order_by(func.sum(StudySession.duration).desc()).limit(10).all()
    
    stats = {
        'total_sessions': total_sessions,
        'total_focus_hours': round(total_focus_time / 60, 1),
        'total_break_hours': round(total_break_time / 60, 1),
        'top_studiers': top_studiers
    }
    
    return render_template('admin/battles/list.html', sessions=sessions, stats=stats)


# ============================================================================
# ADMIN - ANALYTICS
# ============================================================================

@admin_bp.route('/admin/analytics')
@login_required
@admin_required
def analytics():
    """View system analytics"""
    stats = AdminService.get_analytics()
    return render_template('admin/analytics/dashboard.html', stats=stats)


# ============================================================================
# ONE-TIME MIGRATION ROUTE (For Render Deployment)
# ============================================================================

@admin_bp.route('/setup-admin-panel-once')
def setup_admin_panel_once():
    """
    ONE-TIME SETUP ROUTE for Render deployment
    
    This route runs the database migration and creates the admin account.
    Visit this URL ONCE after deploying to Render, then it will be disabled.
    
    IMPORTANT: This route is protected and will only work if no admin exists yet.
    """
    try:
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@studyversefinal.com').first()
        
        if existing_admin and existing_admin.is_admin:
            return """
            <html>
            <head>
                <title>Admin Panel Already Setup</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 100px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }
                    .container { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
                    h1 { color: #10b981; margin-bottom: 20px; }
                    .info { background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 16px; border-radius: 8px; margin: 20px 0; }
                    a { color: #3b82f6; text-decoration: none; font-weight: 600; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Admin Panel Already Setup!</h1>
                    <div class="info">
                        <p><strong>Admin account already exists and is ready to use.</strong></p>
                        <p>Email: <code>admin@studyversefinal.com</code></p>
                    </div>
                    <p>You can now:</p>
                    <ol>
                        <li><a href="/">Go to homepage</a></li>
                        <li>Login with admin credentials</li>
                        <li><a href="/admin">Access admin panel</a></li>
                    </ol>
                    <p style="margin-top: 30px; color: #94a3b8; font-size: 14px;">
                        This setup route is now disabled since admin already exists.
                    </p>
                </div>
            </body>
            </html>
            """
        
        # Run migration
        migration_log = []
        
        # Add columns to User table
        with db.engine.connect() as conn:
            try:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
                migration_log.append("✅ Added is_admin column")
            except Exception as e:
                migration_log.append(f"⚠️ is_admin: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE"))
                migration_log.append("✅ Added is_banned column")
            except Exception as e:
                migration_log.append(f"⚠️ is_banned: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS ban_reason TEXT"))
                migration_log.append("✅ Added ban_reason column")
            except Exception as e:
                migration_log.append(f"⚠️ ban_reason: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP"))
                migration_log.append("✅ Added banned_at column")
            except Exception as e:
                migration_log.append(f"⚠️ banned_at: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS banned_by INTEGER"))
                migration_log.append("✅ Added banned_by column")
            except Exception as e:
                migration_log.append(f"⚠️ banned_by: {str(e)[:50]}")
            
            conn.commit()
        
        # Add columns to SyllabusDocument table
        with db.engine.connect() as conn:
            try:
                conn.execute(db.text("ALTER TABLE syllabus_document ADD COLUMN IF NOT EXISTS file_path VARCHAR(255)"))
                migration_log.append("✅ Added file_path column")
            except Exception as e:
                migration_log.append(f"⚠️ file_path: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE syllabus_document ADD COLUMN IF NOT EXISTS file_size INTEGER"))
                migration_log.append("✅ Added file_size column")
            except Exception as e:
                migration_log.append(f"⚠️ file_size: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE syllabus_document ADD COLUMN IF NOT EXISTS extraction_status VARCHAR(20) DEFAULT 'pending'"))
                migration_log.append("✅ Added extraction_status column")
            except Exception as e:
                migration_log.append(f"⚠️ extraction_status: {str(e)[:50]}")
            
            try:
                conn.execute(db.text("ALTER TABLE syllabus_document ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
                migration_log.append("✅ Added is_active column")
            except Exception as e:
                migration_log.append(f"⚠️ is_active: {str(e)[:50]}")
            
            conn.commit()
        
        # Create AdminAction table
        try:
            db.create_all()
            migration_log.append("✅ Created AdminAction table")
        except Exception as e:
            migration_log.append(f"⚠️ AdminAction table: {str(e)[:50]}")
        
        # Create admin account
        
        admin_user = User(
            email='admin@studyversefinal.com',
            password_hash=generate_password_hash('adminfinal@12345'),
            first_name='Admin',
            last_name='User',
            is_admin=True,
            total_xp=0,
            level=1
        )
        db.session.add(admin_user)
        db.session.commit()
        
        migration_log.append("✅ Created admin account")
        
        # Return success page
        return f"""
        <html>
        <head>
            <title>Admin Panel Setup Complete</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }}
                .container {{ background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
                h1 {{ color: #10b981; margin-bottom: 20px; }}
                .success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 16px; border-radius: 8px; margin: 20px 0; }}
                .credentials {{ background: #334155; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .log {{ background: #1e293b; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 13px; margin: 20px 0; max-height: 300px; overflow-y: auto; }}
                code {{ background: #334155; padding: 4px 8px; border-radius: 4px; color: #3b82f6; }}
                a {{ color: #3b82f6; text-decoration: none; font-weight: 600; }}
                a:hover {{ text-decoration: underline; }}
                .warning {{ background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; padding: 16px; border-radius: 8px; margin: 20px 0; color: #f59e0b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 Admin Panel Setup Complete!</h1>
                
                <div class="success">
                    <strong>✅ Database migration successful!</strong><br>
                    <strong>✅ Admin account created!</strong>
                </div>
                
                <div class="credentials">
                    <h3 style="margin-top: 0; color: #e2e8f0;">Admin Credentials:</h3>
                    <p><strong>Email:</strong> <code>admin@studyversefinal.com</code></p>
                    <p><strong>Password:</strong> <code>adminfinal@12345</code></p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ IMPORTANT:</strong> Change your admin password after first login for security!
                </div>
                
                <h3>Next Steps:</h3>
                <ol>
                    <li><a href="/">Go to homepage</a></li>
                    <li>Click "Sign In"</li>
                    <li>Login with admin credentials above</li>
                    <li><a href="/admin">Access admin panel</a></li>
                </ol>
                
                <h3>Migration Log:</h3>
                <div class="log">
                    {'<br>'.join(migration_log)}
                </div>
                
                <p style="margin-top: 30px; color: #94a3b8; font-size: 14px;">
                    This setup route will be disabled on next visit since admin account now exists.
                </p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        return f"""
        <html>
        <head>
            <title>Setup Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }}
                .container {{ background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
                h1 {{ color: #ef4444; margin-bottom: 20px; }}
                .error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 16px; border-radius: 8px; margin: 20px 0; }}
                pre {{ background: #0f172a; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Setup Error</h1>
                <div class="error">
                    <strong>An error occurred during setup:</strong>
                    <pre>{str(e)}</pre>
                </div>
                <h3>Full Error Trace:</h3>
                <pre>{error_trace}</pre>
                <p>Please contact support or try running the migration manually using Render Shell.</p>
            </div>
        </body>
        </html>
        """
