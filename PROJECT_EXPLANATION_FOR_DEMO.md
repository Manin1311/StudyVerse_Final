# StudyVerse Project - Complete Explanation for Demo

## 📚 Table of Contents
1. [What is StudyVerse?](#what-is-studyverse)
2. [How Flask Works (Simple Explanation)](#how-flask-works)
3. [Project Architecture](#project-architecture)
4. [Step-by-Step: How Everything Works](#step-by-step-flow)
5. [Key Features Explained](#key-features-explained)
6. [Database & Data Flow](#database--data-flow)
7. [Demo Talking Points](#demo-talking-points)

---

## What is StudyVerse?

**StudyVerse** is an AI-powered study companion platform that helps students:
- ✅ Manage tasks and assignments
- ✅ Track study time with Pomodoro timer
- ✅ Get AI help for studying
- ✅ Take quizzes based on their syllabus
- ✅ Compete with friends in study battles
- ✅ Earn XP and level up (gamification)

**Tech Stack:**
- **Backend**: Python Flask (web framework)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL (cloud database)
- **AI**: Google Gemini API
- **Deployment**: Render.com

---

## How Flask Works (Simple Explanation)

### What is Flask?
Flask is a **Python web framework** that helps you build websites. Think of it as a waiter in a restaurant:

1. **User (Customer)** → Visits a URL (orders food)
2. **Flask (Waiter)** → Receives the request
3. **Python Code (Kitchen)** → Processes the request
4. **Database (Storage)** → Gets/saves data
5. **HTML Template (Plate)** → Presents the result
6. **User (Customer)** → Sees the webpage (receives food)

### Basic Flask Concepts:

#### 1. **Routes** - URLs that users visit
```python
@app.route('/dashboard')  # When user visits /dashboard
def dashboard():          # This function runs
    return render_template('dashboard.html')  # Show this page
```

#### 2. **Templates** - HTML files with dynamic data
```html
<h1>Welcome, {{ current_user.name }}!</h1>
<!-- Flask fills in the user's actual name -->
```

#### 3. **Database** - Where data is stored
```python
user = User.query.get(1)  # Get user with ID 1
user.xp = 100            # Update their XP
db.session.commit()      # Save to database
```

---

## Project Architecture

### File Structure:
```
StudyVerse/
├── app.py                    # Main Flask application (BRAIN)
├── email_service.py          # Email sending functionality
├── requirements.txt          # Python packages needed
├── .env                      # Secret keys (API keys, database URL)
│
├── templates/                # HTML files (what users see)
│   ├── layout.html          # Base template (sidebar, header)
│   ├── dashboard.html       # Main dashboard page
│   ├── todos.html           # Task management page
│   ├── pomodoro.html        # Study timer page
│   ├── quiz.html            # Quiz page
│   ├── battle.html          # Battle mode page
│   ├── chat.html            # AI chat page
│   └── ...
│
└── static/                   # CSS, JavaScript, Images
    ├── css/
    │   └── style.css        # All styling
    ├── js/
    │   ├── main.js          # Core JavaScript
    │   ├── pomodoro.js      # Timer logic
    │   ├── battle.js        # Battle game logic
    │   ├── chat.js          # AI chat logic
    │   └── ...
    └── img/                 # Images, videos
```

---

## Step-by-Step: How Everything Works

### 🔹 Step 1: User Opens Website
**URL**: `https://studyverse-final.onrender.com`

**What Happens:**
1. Browser sends request to Render.com server
2. Render runs your Flask app (`app.py`)
3. Flask checks: Is user logged in?
   - ❌ No → Redirect to `/auth` (login page)
   - ✅ Yes → Redirect to `/dashboard`

**Code in app.py:**
```python
@app.route('/')
def index():
    if current_user.is_authenticated:  # Check if logged in
        return redirect(url_for('dashboard'))  # Go to dashboard
    return redirect(url_for('auth'))  # Go to login
```

---

### 🔹 Step 2: User Logs In

**What Happens:**
1. User enters email & password in `auth.html`
2. Form submits to `/signin` route
3. Flask checks database: Does this user exist?
4. Flask verifies password (using bcrypt hashing)
5. If correct → Log user in, redirect to dashboard
6. If wrong → Show error message

**Code Flow:**
```python
@app.route('/signin', methods=['POST'])
def signin():
    email = request.form.get('email')      # Get email from form
    password = request.form.get('password') # Get password from form
    
    user = User.query.filter_by(email=email).first()  # Find user in database
    
    if user and user.check_password(password):  # Verify password
        login_user(user)  # Log them in (Flask-Login)
        return redirect(url_for('dashboard'))  # Go to dashboard
    else:
        flash('Invalid credentials', 'error')  # Show error
        return redirect(url_for('auth'))
```

---

### 🔹 Step 3: Dashboard Loads

**What Happens:**
1. Flask runs `dashboard()` function
2. Queries database for user's data:
   - Total XP
   - Study hours this week
   - Completed tasks
   - Upcoming events
3. Passes all this data to `dashboard.html`
4. Jinja2 (template engine) fills in the data
5. Browser displays the page

**Code:**
```python
@app.route('/dashboard')
@login_required  # Must be logged in to access
def dashboard():
    # Get user's statistics from database
    total_todos = Todo.query.filter_by(user_id=current_user.id).count()
    completed_todos = Todo.query.filter_by(user_id=current_user.id, completed=True).count()
    
    # Calculate study hours this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_minutes = db.session.query(db.func.sum(StudySession.duration))\
        .filter(StudySession.user_id == current_user.id)\
        .filter(StudySession.completed_at >= week_ago)\
        .scalar()
    weekly_hours = round((weekly_minutes or 0) / 60.0, 1)
    
    # Get upcoming tasks
    upcoming_todos = Todo.query.filter_by(user_id=current_user.id, completed=False)\
        .order_by(Todo.id.desc()).limit(5).all()
    
    # Pass all data to template
    return render_template('dashboard.html',
        total_todos=total_todos,
        completed_todos=completed_todos,
        weekly_hours=weekly_hours,
        upcoming_todos=upcoming_todos
    )
```

**In dashboard.html:**
```html
<!-- Flask fills in these values -->
<div>Total XP: {{ current_user.total_xp }}</div>
<div>Study Hours: {{ weekly_hours }}h</div>
<div>Tasks: {{ completed_todos }}</div>

<!-- Loop through tasks -->
{% for todo in upcoming_todos %}
    <div class="task">{{ todo.title }}</div>
{% endfor %}
```

---

### 🔹 Step 4: User Creates a Task

**What Happens:**
1. User clicks "New Task" button
2. Modal (popup) opens with form
3. User fills in task details
4. JavaScript sends data to Flask via AJAX
5. Flask saves to database
6. Page refreshes to show new task

**Frontend (JavaScript in todos.html):**
```javascript
function submitTask() {
    const category = document.getElementById('taskTitle').value;
    const priority = document.getElementById('taskPriority').value;
    const dueDate = document.getElementById('taskDueDate').value;
    
    // Send to backend
    fetch('/todos/add_batch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            category: category,
            priority: priority,
            due_date: dueDate,
            subtasks: currentSubtasks
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload();  // Refresh page
        }
    });
}
```

**Backend (app.py):**
```python
@app.route('/todos/add_batch', methods=['POST'])
@login_required
def todos_add_batch():
    data = request.get_json()  # Get JSON data from frontend
    
    category = data.get('category')
    priority = data.get('priority')
    due_date = data.get('due_date')
    subtasks = data.get('subtasks', [])
    
    # Create each subtask in database
    for subtask_title in subtasks:
        new_todo = Todo(
            user_id=current_user.id,
            title=subtask_title,
            category=category,
            priority=priority,
            due_date=due_date,
            completed=False
        )
        db.session.add(new_todo)
    
    db.session.commit()  # Save to database
    return jsonify({'status': 'success'})
```

---

### 🔹 Step 5: Pomodoro Timer

**What Happens:**
1. User starts 25-minute focus session
2. JavaScript timer counts down on frontend
3. When timer ends, JavaScript sends data to backend
4. Backend calculates XP based on time studied
5. Backend updates user's XP in database
6. User sees XP increase

**Frontend (pomodoro.js):**
```javascript
function completeSession() {
    const duration = 25;  // 25 minutes
    
    fetch('/pomodoro/complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({duration: duration})
    })
    .then(response => response.json())
    .then(data => {
        // Show XP earned
        showNotification(`+${data.xp_earned} XP!`);
    });
}
```

**Backend (app.py):**
```python
@app.route('/pomodoro/complete', methods=['POST'])
@login_required
def complete_pomodoro():
    data = request.get_json()
    duration = data.get('duration', 25)
    
    # Save session to database
    session = StudySession(
        user_id=current_user.id,
        duration=duration,
        completed_at=datetime.utcnow()
    )
    db.session.add(session)
    
    # Award XP (1 XP per minute)
    xp_amount = duration
    result = GamificationService.add_xp(current_user.id, 'focus', xp_amount)
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'xp_earned': result['earned']
    })
```

---

### 🔹 Step 6: AI Chat Assistant

**What Happens:**
1. User types question in chat
2. JavaScript sends message to Flask
3. Flask sends message to Google Gemini API
4. Gemini AI generates response
5. Flask sends response back to frontend
6. JavaScript displays AI response with markdown formatting

**Frontend (chat.js):**
```javascript
function sendMessage() {
    const message = document.getElementById('userInput').value;
    
    fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        // Display AI response
        displayMessage(data.response, 'ai');
    });
}
```

**Backend (app.py):**
```python
@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message')
    
    # Get user's syllabus for context
    syllabus = SyllabusDocument.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).first()
    
    context = syllabus.extracted_text if syllabus else ""
    
    # Send to Gemini AI
    prompt = f"Context: {context}\n\nQuestion: {user_message}"
    response = ai_model.generate_content(prompt)
    
    return jsonify({
        'status': 'success',
        'response': response.text
    })
```

---

## Key Features Explained

### 1. **Gamification System**

**How it works:**
- Users earn XP for completing tasks, studying, taking quizzes
- XP → Levels (every 500 XP = 1 level)
- Levels → Ranks (Bronze → Silver → Gold → Platinum → Diamond → Master)
- Badges for achievements (7-day streak, 100 tasks, etc.)

**Code:**
```python
class GamificationService:
    @staticmethod
    def add_xp(user_id, source, amount):
        user = User.query.get(user_id)
        user.total_xp += amount
        
        # Calculate new level
        new_level = int(user.total_xp / 500) + 1
        if new_level > user.level:
            user.level = new_level
            # Award level-up badge
        
        db.session.commit()
        return {'earned': amount, 'new_total': user.total_xp}
```

---

### 2. **Battle Mode**

**How it works:**
- Two players answer questions
- Fastest correct answer wins the round
- Best of 5 rounds wins the battle
- Winner gets XP

**Flow:**
1. Player creates battle room
2. Friend joins using room code
3. Socket.IO (real-time) syncs both players
4. Questions generated from syllabus
5. Players race to answer
6. Winner determined, XP awarded

---

### 3. **Quiz System**

**How it works:**
- AI generates questions from uploaded syllabus
- Multiple choice format
- Immediate feedback
- XP based on score

**Process:**
1. User uploads PDF syllabus
2. Backend extracts text from PDF
3. Stores in database
4. When quiz starts, AI generates 10 questions
5. User answers, backend checks correctness
6. XP awarded based on score

---

### 4. **Task Management**

**Features:**
- Category-based grouping (like folders)
- Priority levels (High, Medium, Low)
- Due dates with reminders
- Subtasks (parent-child hierarchy)
- Progress tracking

**Database Structure:**
```python
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    category = db.Column(db.String(50))  # Groups tasks
    priority = db.Column(db.String(20))  # High/Medium/Low
    due_date = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
```

---

## Database & Data Flow

### Database Tables:

1. **User** - User accounts
   - id, email, password_hash, name, total_xp, level, streak

2. **Todo** - Tasks
   - id, user_id, title, category, priority, due_date, completed

3. **StudySession** - Pomodoro sessions
   - id, user_id, duration, completed_at

4. **SyllabusDocument** - Uploaded PDFs
   - id, user_id, filename, extracted_text, is_active

5. **Quiz** - Quiz attempts
   - id, user_id, score, total_questions, completed_at

6. **Battle** - Battle rooms
   - id, player1_id, player2_id, status, winner_id

7. **Badge** - Available badges
   - id, name, description, icon, criteria

8. **UserBadge** - Earned badges
   - id, user_id, badge_id, earned_at

### Data Flow Example (Creating a Task):

```
User Browser
    ↓ (1) Fills form, clicks submit
JavaScript (todos.html)
    ↓ (2) Sends JSON via fetch()
Flask Route (/todos/add_batch)
    ↓ (3) Receives data, validates
Database (PostgreSQL)
    ↓ (4) Saves new Todo record
Flask Response
    ↓ (5) Returns success JSON
JavaScript
    ↓ (6) Reloads page
User Browser
    ↓ (7) Shows updated task list
```

---

## Demo Talking Points

### Opening (1 minute):
> "StudyVerse is an AI-powered study companion that helps students stay organized, focused, and motivated through gamification. It combines task management, study timers, AI tutoring, and competitive features to make studying engaging."

### Feature Walkthrough (5-7 minutes):

#### 1. **Dashboard** (1 min)
- "This is the central hub showing all key metrics"
- Point out: XP, study hours, active tasks, calendar
- "Everything updates in real-time as you use the platform"

#### 2. **Task Management** (1 min)
- "Students can organize assignments by category"
- Demo: Create a task with subtasks
- "Tasks can have priorities and due dates with email reminders"

#### 3. **Pomodoro Timer** (1 min)
- "25-minute focus sessions based on Pomodoro Technique"
- Demo: Start timer, show XP reward
- "Tracks total study time and awards XP for consistency"

#### 4. **AI Chat** (1 min)
- "Context-aware AI tutor powered by Google Gemini"
- Demo: Ask a question related to uploaded syllabus
- "AI has access to your course materials for relevant answers"

#### 5. **Quiz System** (1 min)
- "AI generates quizzes from your syllabus"
- Demo: Take a quick quiz
- "Immediate feedback and XP rewards for learning"

#### 6. **Battle Mode** (1 min)
- "Competitive study mode - race against friends"
- Demo: Show battle interface
- "Makes studying social and fun"

#### 7. **Gamification** (1 min)
- "XP, levels, ranks, and badges motivate consistent study"
- Show: Profile with level, rank, badges
- "Streaks encourage daily engagement"

### Technical Stack (1 minute):
> "Built with Python Flask backend, PostgreSQL database, and deployed on Render.com. Frontend uses vanilla JavaScript for interactivity. AI integration via Google Gemini API. Real-time features powered by Socket.IO."

### Closing (30 seconds):
> "StudyVerse transforms studying from a chore into an engaging experience by combining productivity tools with game-like elements, helping students stay motivated and achieve their academic goals."

---

## Quick Reference Commands

### Run Locally:
```bash
python app.py
```

### Access Database:
```python
# In Python shell
from app import app, db, User
with app.app_context():
    users = User.query.all()
    print(users)
```

### Check Logs on Render:
1. Go to Render.com dashboard
2. Click on your service
3. Click "Logs" tab
4. See real-time server logs

---

## Common Questions & Answers

**Q: How does the XP system work?**
A: Users earn XP for activities (1 XP per minute of study, 10 XP per task, etc.). Every 500 XP = 1 level up. Levels determine rank (Bronze, Silver, Gold, etc.).

**Q: How is the AI integrated?**
A: We use Google Gemini API. When a user asks a question, we send it to Gemini along with their syllabus text as context. Gemini generates a relevant response.

**Q: How do real-time battles work?**
A: Socket.IO creates a WebSocket connection between both players. When one player answers, the event is instantly broadcast to the other player's browser.

**Q: Where is the database hosted?**
A: PostgreSQL database is hosted on Render.com's cloud infrastructure, same as the Flask app.

**Q: How are passwords secured?**
A: Passwords are hashed using bcrypt before storing in database. We never store plain text passwords.

---

## Tips for Demo Day

1. ✅ **Test everything beforehand** - Make sure all features work
2. ✅ **Prepare demo account** - Pre-populate with tasks, study sessions
3. ✅ **Have backup plan** - Screenshots if internet fails
4. ✅ **Practice timing** - Know what to show in 10 minutes
5. ✅ **Explain the "why"** - Why gamification? Why AI? Why this matters?
6. ✅ **Show the code** - Briefly show app.py structure
7. ✅ **Highlight challenges** - What was difficult? How did you solve it?
8. ✅ **Future improvements** - What would you add next?

---

**Good luck with your demo! 🚀**

*Last Updated: February 8, 2026*
