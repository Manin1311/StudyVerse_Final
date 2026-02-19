
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, oauth
from models import User
from services.auth import AuthService
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth')
def auth():
    # Check if user is authenticated
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_view'))
    return render_template('auth.html')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Create account using standard HTML form POST (no JSON)."""
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()

    if not email or not password:
        flash('Email and password are required.', 'error')
        return render_template('auth.html', active_tab='signup', form_data=request.form)

    # Password Strength Validation
    import re
    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return render_template('auth.html', active_tab='signup', form_data=request.form)
    
    if not re.search(r"[A-Z]", password):
        flash('Password must contain at least one uppercase letter.', 'error')
        return render_template('auth.html', active_tab='signup', form_data=request.form)

    if not re.search(r"[0-9]", password):
        flash('Password must contain at least one number.', 'error')
        return render_template('auth.html', active_tab='signup', form_data=request.form)

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        flash('Password must contain at least one special character (!@#$%^&*).', 'error')
        return render_template('auth.html', active_tab='signup', form_data=request.form)

    try:
        user = AuthService.create_user(email, password, first_name, last_name)
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('auth.html', active_tab='signup', form_data=request.form)

    # Automatically log in the user after signup
    login_user(user, remember=True)
    session.permanent = True
    
    return redirect(url_for('dashboard.dashboard_view'))

@auth_bp.route('/signin', methods=['POST'])
def signin():
    """Sign in using standard HTML form POST (no JSON)."""
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    # Check if user exists first
    user = User.query.filter_by(email=email).first()
    
    if user and not user.password_hash:
        # User signed up with Google OAuth
        flash('This account was created with Google Sign-In. Please use the "Sign in with Google" button.', 'error')
        return redirect(url_for('auth.auth')) # Note: blueprint endpoint
    
    # Authenticate with password
    user = AuthService.authenticate(email, password)
    if not user:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.auth'))

    login_user(user, remember=True)  # Enable remember me for persistent sessions
    session.permanent = True

    return redirect(url_for('dashboard.dashboard_view'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    try:
        current_user.last_seen = datetime.utcnow() - timedelta(minutes=15)
        db.session.commit()
    except:
        pass
        
    logout_user()
    session.clear()
    
    # Create response to clear cookies explicitly
    response = redirect(url_for('auth.auth'))
    
    # Clear Flask-Login 'remember me' cookie
    # We access app config via current_app if needed, or just assume default name
    # But usually redirect is enough. To be safe, let's delete cookies.
    response.delete_cookie('remember_token')
    response.delete_cookie('session')
    
    flash('You have been logged out.', 'success')
    return response

# Google OAuth Routes
@auth_bp.route('/login/google')
def login_google():
    # Use _external=True to generate absolute URL, required for OAuth callbacks
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/login/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token, nonce=None)
        
        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name', '')
        picture = user_info.get('picture')

        # Check if user exists
        user = User.query.filter_by(email=email).first()

        if not user:
            # Create new user
            names = name.split(' ', 1) if name else ['', '']
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                profile_image=picture,
                password_hash=None # No password for Google users
            )
            db.session.add(user)
            db.session.commit()
            
        else:
            # Update existing user info
            if not user.google_id:
                user.google_id = google_id
            if picture:
                user.profile_image = picture
            db.session.commit()

        # Log the user in
        login_user(user, remember=True)
        session.permanent = True
        
        return redirect(url_for('dashboard.dashboard_view'))
    
    except Exception as e:
        flash(f"Google authentication failed: {str(e)}", "error")
        return redirect(url_for('auth.auth'))

@auth_bp.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Handle Google OAuth sign-in from Firebase/Client-Side."""
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    email = data.get('email')
    display_name = data.get('displayName', '')
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Create new user from Google account
        names = display_name.split(' ', 1) if display_name else ['', '']
        first_name = names[0] if names else ''
        last_name = names[1] if len(names) > 1 else ''
        
        user = User(
            email=email,
            password_hash=generate_password_hash(str(uuid.uuid4())),  # Random password for OAuth users
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        db.session.commit()
    
    # Log in the user
    login_user(user, remember=True)
    session.permanent = True
    
    return jsonify({'status': 'success', 'message': 'Authentication successful'})
