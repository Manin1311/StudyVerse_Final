# 📧 How to Fix Gmail Email Issues - Quick Guide

## Your Current Setup
- **Gmail Account**: maninbuch13112006@gmail.com
- **Current App Password**: `iyty tgjc gssi bepl`

## Problem
Emails were working at the beginning but now they're not sending for new users.

## Solution: Generate a NEW Gmail App Password

### Step-by-Step Instructions:

1. **Go to Google Account Security**
   - Visit: https://myaccount.google.com/security
   - Log in with: maninbuch13112006@gmail.com

2. **Enable 2-Step Verification** (if not already enabled)
   - Scroll down to "How you sign in to Google"
   - Click "2-Step Verification"
   - Follow instructions to enable

3. **Generate App Password**
   - Search for "App Passwords" or go to: https://myaccount.google.com/apppasswords
   - Select app: **Mail**
   - Select device: **Windows Computer** (or Other)
   - Click **Generate**

4. **Copy the 16-Digit Code**
   - You'll see a 16-character code like: `abcd efgh ijkl mnop`
   - **IMPORTANT**: Remove all spaces! Final code should be: `abcdefghijklmnop`

5. **Update Your `.env` File**
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=maninbuch13112006@gmail.com
   MAIL_PASSWORD=yournew16digitcode
   MAIL_DEFAULT_SENDER=StudyVerse <maninbuch13112006@gmail.com>
   ```

6. **Restart Your Application**
   - Stop the server (Ctrl+C)
   - Start again: `python app.py`

## Test If It Works

### Method 1: Sign Up a New Test Account
1. Go to your StudyVerse auth page
2. Sign up with a NEW email (use your personal email for testing)
3. Check that email's inbox (and spam folder)
4. You should receive "Welcome to StudyVerse" email!

### Method 2: Test Programmatically
```python
# Open Python in your project directory
python

# Then run:
from app import app
from email_service import send_welcome_email

with app.app_context():
    send_welcome_email('youremail@gmail.com', 'Test', 'User')
```

Watch the console - you should see:
```
✓ Email sent successfully to ['youremail@gmail.com']
```

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Authentication failed" | Generate NEW App Password, old one expired |
| "Connection timed out" | Check internet connection, verify MAIL_PORT=587 |
| "Username/Password not accepted" | Ensure no spaces in password, username is full email |
| Email not arriving | Check spam folder, try different test email |
| "Less secure apps" error | Use App Password (not regular password) |

## Why This Happens

Gmail App Passwords can:
- Expire after some time
- Be revoked if you changed your Google password
- Stop working if 2-Step Verification is disabled

**The solution is always**: Generate a fresh new App Password!

## Quick Checklist

- [ ] 2-Step Verification enabled on Google Account
- [ ] Generated NEW App Password for Mail
- [ ] Copied 16-digit code WITHOUT spaces
- [ ] Updated `.env` file with new password
- [ ] Restarted the Flask application
- [ ] Tested with a new signup or test email
- [ ] Checked spam folder if email missing

## Still Not Working?

1. **Verify Gmail Settings**:
   - Check that IMAP/SMTP is enabled in Gmail settings
   - Go to: Settings → Forwarding and POP/IMAP → Enable IMAP

2. **Check Firewall**:
   - Your network might block port 587
   - Try on different network/hotspot

3. **Console Logs**:
   - Look for error messages when sending email
   - Should show "✓ Email sent" or "✗ Failed to send email: [error]"

4. **Alternative Email Service**:
   - If Gmail keeps failing, consider using SendGrid or Mailgun
   - They offer free tiers and are more reliable for apps

---

## Final Note

**YES, you should create a new 16-digit Gmail App Password if emails aren't working!**

The old password (`iyty tgjc gssi bepl`) may have expired or been revoked.

Follow the steps above to generate a fresh one. It only takes 2 minutes! ⏱️

