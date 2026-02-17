# 🚀 Admin Panel - Quick Start Guide

## Step-by-Step Setup

### 1️⃣ Migrate Database (Add New Columns)

```bash
python migrate_database.py
```

This adds the new admin fields to your existing database.

### 2️⃣ Create Admin Account

```bash
python setup_admin.py
```

This creates your admin account with the credentials:
- **Email**: admin@studyversefinal.com
- **Password**: adminfinal@12345

### 3️⃣ Start the Application

```bash
python app.py
```

### 4️⃣ Login & Access Admin Panel

1. Go to `http://localhost:5000`
2. Click "Sign In"
3. Enter admin credentials
4. Navigate to `http://localhost:5000/admin`

---

## ✨ What You Can Do

### 👥 User Management
- View all users
- Search by name/email
- Ban/unban users
- Manually adjust XP
- View user statistics

### 📄 PDF Management
- View all uploaded PDFs
- Read extracted text
- Download original files
- Delete PDFs
- See usage stats

### 📋 Audit Logs
- Track all admin actions
- Filter by action type
- View timestamps & IP addresses

---

## 🎯 Common Tasks

### Ban a User
1. Go to `/admin/users`
2. Click "View" on the user
3. Click "Ban User"
4. Enter reason
5. Confirm

### Adjust User XP
1. Go to user detail page
2. Scroll to "Adjust XP" section
3. Enter amount (+ or -)
4. Enter reason
5. Click "Apply"

### View PDF Content
1. Go to `/admin/pdfs`
2. Click "View" on any PDF
3. See extracted text
4. Download or delete as needed

---

## ⚠️ Troubleshooting

### "Column does not exist" error
Run the migration script:
```bash
python migrate_database.py
```

### Can't access /admin
Make sure you:
1. Ran `setup_admin.py`
2. Logged in with admin credentials
3. The user has `is_admin=True` in database

### Eventlet warning
This is normal and can be ignored. It doesn't affect functionality.

---

## 🔒 Security Tips

1. **Change Password**: After first login, consider changing the admin password
2. **Backup Database**: Always backup before making bulk changes
3. **Review Logs**: Regularly check audit logs for suspicious activity
4. **Limit Access**: Only give admin access to trusted users

---

## 📞 Need Help?

Check these files for more info:
- `ADMIN_PANEL_COMPLETE.md` - Full feature list
- `ADMIN_PANEL_IMPLEMENTATION.md` - Technical details
- `ADMIN_PANEL_UI_DESIGN.md` - UI mockups

---

**Ready to go!** 🎉

Your admin panel is fully functional and ready to use!
