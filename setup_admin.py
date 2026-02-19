"""
Admin Setup Script
==================
This script creates the admin account and updates the database schema.

Run this once to set up the admin panel.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import generate_password_hash

def setup_admin():
    """Create admin account and update database"""
    
    with app.app_context():
        print("🔧 Setting up admin panel...")
        
        # Create all tables (including new AdminAction table)
        print("📊 Creating database tables...")
        db.create_all()
        print("✅ Database tables created!")
        
        # Admin credentials
        admin_email = "admin@studyversefinal.com"
        admin_password = "adminfinal@12345"
        
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if existing_admin:
            # Update existing user to be admin
            existing_admin.is_admin = True
            existing_admin.password_hash = generate_password_hash(admin_password)
            db.session.commit()
            print(f"✅ Updated existing user '{admin_email}' to admin!")
        else:
            # Create new admin user
            admin_user = User(
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                first_name="Admin",
                last_name="User",
                is_admin=True,
                total_xp=0,
                level=1
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Created new admin user '{admin_email}'!")
        
        print("\n" + "="*60)
        print("🎉 Admin Panel Setup Complete!")
        print("="*60)
        print(f"\n📧 Admin Email: {admin_email}")
        print(f"🔑 Admin Password: {admin_password}")
        print(f"\n🌐 Access admin panel at: http://localhost:5000/admin")
        print("\n⚠️  IMPORTANT: Change the admin password after first login!")
        print("="*60 + "\n")

if __name__ == "__main__":
    setup_admin()
