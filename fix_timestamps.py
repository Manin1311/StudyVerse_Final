
from app import app, db, Todo
from datetime import datetime

with app.app_context():
    # Find completed tasks with no timestamp
    todos = Todo.query.filter(Todo.completed == True, Todo.completed_at == None).all()
    count = 0
    for t in todos:
        # Fallback: use created_at or now if you prefer. 
        # Using created_at implies they were done same day (stats will show up on creation day)
        # Using now() implies they were done just now (stats will show up today)
        # Given user said "i completed two task", let's assume 'now' is a better proxy or created_at.
        # Let's use created_at so it doesn't skew today's "focus" artificialy if they were old.
        # ACTUALLY, user expects them to appear. If I use created_at and it was 3 days ago, they might appear on Wed.
        # But if the user just clicked them, they want to see them today.
        
        # Best approach: Since I added the column NOW, any previously completed task is "history".
        # I'll set it to created_at to avoid falsifying "today's" activity if it was actually old.
        t.completed_at = t.created_at 
        count += 1
    
    db.session.commit()
    print(f"Fixed timestamps for {count} tasks.")
