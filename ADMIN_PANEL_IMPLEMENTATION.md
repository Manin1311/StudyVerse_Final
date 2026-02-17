# StudyVerse Admin Panel - Implementation Plan

## 🎯 Overview
Complete admin panel implementation for single administrator with full system control.

---

## 📋 Phase 1: Database & Authentication (Day 1)

### 1.1 Database Changes

#### Add to User Model (app.py):
```python
# Add to User class
is_admin = db.Column(db.Boolean, default=False)
```

#### Create AdminAction Model:
```python
class AdminAction(db.Model):
    """Audit log for all admin actions"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'ban_user', 'delete_message', etc.
    target_type = db.Column(db.String(50))  # 'user', 'message', 'group', 'pdf'
    target_id = db.Column(db.Integer)
    details = db.Column(db.JSON)  # Additional context
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('User', backref='admin_actions')
```

#### Update SyllabusDocument Model:
```python
class SyllabusDocument(db.Model):
    """PDF syllabus documents"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # Path to PDF file
    extracted_text = db.Column(db.Text, nullable=True)
    file_size = db.Column(db.Integer)  # Size in bytes
    extraction_status = db.Column(db.String(20), default='pending')  # pending, success, failed
    is_active = db.Column(db.Boolean, default=True)  # For archiving
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='syllabus_documents')
```

#### Add User Ban/Suspension:
```python
# Add to User model
is_banned = db.Column(db.Boolean, default=False)
ban_reason = db.Column(db.Text, nullable=True)
banned_at = db.Column(db.DateTime, nullable=True)
banned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
```

### 1.2 Migration Command
```bash
# After adding models, create migration
flask db migrate -m "Add admin panel tables"
flask db upgrade
```

### 1.3 Set Yourself as Admin
```python
# In Python shell or create a script
from app import db, User

admin_email = "your-email@example.com"  # Replace with your email
user = User.query.filter_by(email=admin_email).first()
if user:
    user.is_admin = True
    db.session.commit()
    print(f"✅ {admin_email} is now an admin!")
else:
    print("❌ User not found!")
```

---

## 📋 Phase 2: Admin Authentication & Decorators (Day 1)

### 2.1 Admin Decorator (app.py):
```python
from functools import wraps
from flask import abort

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth'))
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function
```

### 2.2 Admin Service Class:
```python
class AdminService:
    """Admin operations and utilities"""
    
    @staticmethod
    def log_action(admin_id, action, target_type=None, target_id=None, details=None):
        """Log admin action for audit trail"""
        log = AdminAction(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=request.remote_addr
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
        total_battles = Battle.query.count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_pdfs': total_pdfs,
            'total_groups': total_groups,
            'total_battles': total_battles
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
```

---

## 📋 Phase 3: Admin Routes Structure (Day 2)

### 3.1 Route Organization:
```
/admin
├── /                      # Dashboard (overview stats)
├── /users                 # User management
│   ├── /                  # List all users
│   ├── /<id>              # User details
│   ├── /<id>/ban          # Ban user
│   ├── /<id>/unban        # Unban user
│   ├── /<id>/adjust-xp    # Manually adjust XP
│   └── /<id>/delete       # Delete user
├── /pdfs                  # PDF management
│   ├── /                  # List all PDFs
│   ├── /<id>              # PDF details & extracted text
│   ├── /<id>/download     # Download original PDF
│   └── /<id>/delete       # Delete PDF
├── /messages              # Content moderation
│   ├── /personal          # Personal AI chats
│   └── /groups            # Group chat messages
├── /gamification          # XP & Badges
│   ├── /xp-history        # XP transaction logs
│   ├── /badges            # Badge management
│   └── /leaderboard       # Leaderboard control
├── /shop                  # Shop management
│   ├── /items             # Manage shop items
│   └── /transactions      # Purchase history
├── /groups                # Group management
│   ├── /                  # List all groups
│   └── /<id>              # Group details
├── /battles               # Battle monitoring
├── /analytics             # Reports & charts
└── /logs                  # Admin action audit logs
```

---

## 📋 Phase 4: Admin Templates (Day 2-3)

### 4.1 Template Structure:
```
templates/admin/
├── base.html              # Admin base template (sidebar, header)
├── dashboard.html         # Main admin dashboard
├── users/
│   ├── list.html          # User list with search/filter
│   └── detail.html        # User profile & actions
├── pdfs/
│   ├── list.html          # PDF list
│   └── detail.html        # PDF viewer with extracted text
├── messages/
│   ├── personal.html      # Personal chat logs
│   └── groups.html        # Group chat logs
├── gamification/
│   ├── xp_history.html    # XP transactions
│   ├── badges.html        # Badge management
│   └── leaderboard.html   # Leaderboard view
├── shop/
│   ├── items.html         # Shop item management
│   └── transactions.html  # Purchase logs
├── groups/
│   ├── list.html          # All groups
│   └── detail.html        # Group details
├── battles/
│   └── list.html          # Battle history
├── analytics/
│   └── dashboard.html     # Charts & reports
└── logs/
    └── list.html          # Audit logs
```

### 4.2 Admin Base Template (templates/admin/base.html):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin Panel{% endblock %} - StudyVerse</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="admin-panel">
    <!-- Admin Sidebar -->
    <aside class="admin-sidebar">
        <div class="admin-logo">
            <i class="fa-solid fa-shield-halved"></i>
            <span>Admin Panel</span>
        </div>
        
        <nav class="admin-nav">
            <a href="{{ url_for('admin_dashboard') }}" class="admin-nav-item">
                <i class="fa-solid fa-chart-line"></i>
                <span>Dashboard</span>
            </a>
            <a href="{{ url_for('admin_users') }}" class="admin-nav-item">
                <i class="fa-solid fa-users"></i>
                <span>Users</span>
            </a>
            <a href="{{ url_for('admin_pdfs') }}" class="admin-nav-item">
                <i class="fa-solid fa-file-pdf"></i>
                <span>PDFs</span>
            </a>
            <a href="{{ url_for('admin_messages') }}" class="admin-nav-item">
                <i class="fa-solid fa-comments"></i>
                <span>Messages</span>
            </a>
            <a href="{{ url_for('admin_gamification') }}" class="admin-nav-item">
                <i class="fa-solid fa-trophy"></i>
                <span>Gamification</span>
            </a>
            <a href="{{ url_for('admin_shop') }}" class="admin-nav-item">
                <i class="fa-solid fa-store"></i>
                <span>Shop</span>
            </a>
            <a href="{{ url_for('admin_groups') }}" class="admin-nav-item">
                <i class="fa-solid fa-user-group"></i>
                <span>Groups</span>
            </a>
            <a href="{{ url_for('admin_battles') }}" class="admin-nav-item">
                <i class="fa-solid fa-swords"></i>
                <span>Battles</span>
            </a>
            <a href="{{ url_for('admin_analytics') }}" class="admin-nav-item">
                <i class="fa-solid fa-chart-pie"></i>
                <span>Analytics</span>
            </a>
            <a href="{{ url_for('admin_logs') }}" class="admin-nav-item">
                <i class="fa-solid fa-clipboard-list"></i>
                <span>Audit Logs</span>
            </a>
            
            <div class="admin-nav-divider"></div>
            
            <a href="{{ url_for('dashboard') }}" class="admin-nav-item">
                <i class="fa-solid fa-arrow-left"></i>
                <span>Back to App</span>
            </a>
        </nav>
    </aside>
    
    <!-- Admin Main Content -->
    <main class="admin-main">
        <header class="admin-header">
            <div class="admin-header-left">
                <h1>{% block page_title %}Dashboard{% endblock %}</h1>
            </div>
            <div class="admin-header-right">
                <div class="admin-user">
                    <img src="{{ current_user.get_avatar(40) }}" alt="Admin">
                    <span>{{ current_user.first_name }}</span>
                </div>
            </div>
        </header>
        
        <div class="admin-content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            {% block content %}{% endblock %}
        </div>
    </main>
</body>
</html>
```

---

## 📋 Phase 5: Key Admin Features (Day 3-4)

### 5.1 Admin Dashboard Route:
```python
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    stats = AdminService.get_dashboard_stats()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_pdfs = SyllabusDocument.query.order_by(SyllabusDocument.created_at.desc()).limit(5).all()
    recent_actions = AdminAction.query.order_by(AdminAction.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_pdfs=recent_pdfs,
                         recent_actions=recent_actions)
```

### 5.2 User Management Routes:
```python
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')  # all, active, banned
    
    query = User.query
    
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
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/users/list.html', users=users, search=search, filter_type=filter_type)

@app.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user statistics
    total_xp = user.total_xp
    total_tasks = Todo.query.filter_by(user_id=user.id).count()
    completed_tasks = Todo.query.filter_by(user_id=user.id, completed=True).count()
    total_pdfs = SyllabusDocument.query.filter_by(user_id=user.id).count()
    total_battles = Battle.query.filter(
        db.or_(Battle.challenger_id == user.id, Battle.opponent_id == user.id)
    ).count()
    
    # Recent activity
    recent_xp = XPHistory.query.filter_by(user_id=user.id).order_by(XPHistory.timestamp.desc()).limit(10).all()
    
    return render_template('admin/users/detail.html',
                         user=user,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         total_pdfs=total_pdfs,
                         total_battles=total_battles,
                         recent_xp=recent_xp)

@app.route('/admin/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def admin_ban_user(user_id):
    reason = request.form.get('reason', 'No reason provided')
    
    try:
        AdminService.ban_user(user_id, reason, current_user.id)
        flash('User banned successfully', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_user_detail', user_id=user_id))

@app.route('/admin/users/<int:user_id>/adjust-xp', methods=['POST'])
@login_required
@admin_required
def admin_adjust_xp(user_id):
    amount = request.form.get('amount', type=int)
    reason = request.form.get('reason', 'Admin adjustment')
    
    if not amount:
        flash('Invalid XP amount', 'error')
        return redirect(url_for('admin_user_detail', user_id=user_id))
    
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
    return redirect(url_for('admin_user_detail', user_id=user_id))
```

### 5.3 PDF Management Routes:
```python
@app.route('/admin/pdfs')
@login_required
@admin_required
def admin_pdfs():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = SyllabusDocument.query
    
    if search:
        query = query.filter(
            db.or_(
                SyllabusDocument.filename.ilike(f'%{search}%'),
                SyllabusDocument.extracted_text.ilike(f'%{search}%')
            )
        )
    
    pdfs = query.order_by(SyllabusDocument.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/pdfs/list.html', pdfs=pdfs, search=search)

@app.route('/admin/pdfs/<int:pdf_id>')
@login_required
@admin_required
def admin_pdf_detail(pdf_id):
    pdf = SyllabusDocument.query.get_or_404(pdf_id)
    user = User.query.get(pdf.user_id)
    
    # Count related data
    tasks_count = Todo.query.filter_by(syllabus_id=pdf.id).count()
    
    # Log admin access
    AdminService.log_action(
        admin_id=current_user.id,
        action='view_pdf',
        target_type='syllabus_document',
        target_id=pdf.id
    )
    
    return render_template('admin/pdfs/detail.html',
                         pdf=pdf,
                         user=user,
                         tasks_count=tasks_count)

@app.route('/admin/pdfs/<int:pdf_id>/download')
@login_required
@admin_required
def admin_pdf_download(pdf_id):
    pdf = SyllabusDocument.query.get_or_404(pdf_id)
    
    # Log download
    AdminService.log_action(
        admin_id=current_user.id,
        action='download_pdf',
        target_type='syllabus_document',
        target_id=pdf.id
    )
    
    return send_file(pdf.file_path, as_attachment=True, download_name=pdf.filename)

@app.route('/admin/pdfs/<int:pdf_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_pdf_delete(pdf_id):
    pdf = SyllabusDocument.query.get_or_404(pdf_id)
    
    # Delete file from filesystem
    try:
        if os.path.exists(pdf.file_path):
            os.remove(pdf.file_path)
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    # Delete from database
    db.session.delete(pdf)
    
    # Log deletion
    AdminService.log_action(
        admin_id=current_user.id,
        action='delete_pdf',
        target_type='syllabus_document',
        target_id=pdf.id,
        details={'filename': pdf.filename, 'user_id': pdf.user_id}
    )
    
    db.session.commit()
    
    flash('PDF deleted successfully', 'success')
    return redirect(url_for('admin_pdfs'))
```

---

## 📋 Phase 6: Admin Styling (Day 4)

### 6.1 Admin CSS (static/css/admin.css):
```css
/* Admin Panel Styles */
.admin-panel {
    display: flex;
    min-height: 100vh;
    background: var(--bg-primary);
}

.admin-sidebar {
    width: 260px;
    background: var(--bg-card);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    overflow-y: auto;
}

.admin-logo {
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 20px;
    font-weight: 700;
    color: var(--primary);
    border-bottom: 1px solid var(--border);
}

.admin-nav {
    flex: 1;
    padding: 16px 0;
}

.admin-nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 24px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.2s;
}

.admin-nav-item:hover,
.admin-nav-item.active {
    background: rgba(var(--primary-rgb), 0.1);
    color: var(--primary);
}

.admin-nav-item i {
    width: 20px;
    text-align: center;
}

.admin-nav-divider {
    height: 1px;
    background: var(--border);
    margin: 16px 0;
}

.admin-main {
    flex: 1;
    margin-left: 260px;
    display: flex;
    flex-direction: column;
}

.admin-header {
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.admin-header h1 {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
}

.admin-user {
    display: flex;
    align-items: center;
    gap: 12px;
}

.admin-user img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
}

.admin-content {
    flex: 1;
    padding: 32px;
}

/* Admin Stats Cards */
.admin-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
}

.admin-stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.admin-stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

.admin-stat-info {
    flex: 1;
}

.admin-stat-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
}

.admin-stat-label {
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 4px;
}

/* Admin Tables */
.admin-table {
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
}

.admin-table table {
    width: 100%;
    border-collapse: collapse;
}

.admin-table th {
    background: rgba(var(--primary-rgb), 0.05);
    padding: 16px;
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
}

.admin-table td {
    padding: 16px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
}

.admin-table tr:last-child td {
    border-bottom: none;
}

.admin-table tr:hover {
    background: rgba(var(--primary-rgb), 0.02);
}

/* Admin Buttons */
.admin-btn {
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.admin-btn-primary {
    background: var(--primary);
    color: white;
}

.admin-btn-danger {
    background: #ef4444;
    color: white;
}

.admin-btn-secondary {
    background: rgba(var(--primary-rgb), 0.1);
    color: var(--primary);
}

.admin-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

---

## 📋 Phase 7: Testing & Deployment (Day 5)

### 7.1 Testing Checklist:
- [ ] Admin login works
- [ ] Non-admin users cannot access admin routes
- [ ] User management (view, ban, XP adjustment)
- [ ] PDF viewing and download
- [ ] Audit logs are created
- [ ] All admin pages render correctly
- [ ] Mobile responsiveness

### 7.2 Security Checklist:
- [ ] Admin decorator on all admin routes
- [ ] CSRF protection on forms
- [ ] Audit logging for sensitive actions
- [ ] Input validation on all forms
- [ ] SQL injection prevention (using ORM)

---

## 📋 Next Steps

1. **Review this plan** - Make sure it covers everything you need
2. **Start implementation** - Begin with Phase 1 (Database changes)
3. **Test incrementally** - Test each phase before moving to next
4. **Customize as needed** - Add/remove features based on your needs

---

## 🎯 Priority Features (If time is limited)

**Must Have:**
1. ✅ Admin authentication & dashboard
2. ✅ User management (view, ban)
3. ✅ PDF viewing
4. ✅ XP adjustment

**Nice to Have:**
5. Message moderation
6. Shop management
7. Analytics dashboard
8. Audit logs

**Can Add Later:**
9. Advanced analytics
10. Batch operations
11. Export features
12. Email notifications

---

**Ready to start implementation?** Let me know and I'll begin creating the files! 🚀
