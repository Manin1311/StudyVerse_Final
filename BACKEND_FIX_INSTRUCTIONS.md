# BACKEND FIX FOR WEEKLY STATS CHART
# ====================================

## Problem:
The backend only sends percentages (focus_pct, task_pct) but the chart needs actual values (minutes, task count).

## Solution:
Update app.py to include actual values in the daily_stats.

---

## STEP 1: Update app.py

Find this section (around line 1330):

```python
daily_stats.append({
    'day': d.strftime('%a'),
    'focus_pct': int(focus_pct),
    'task_pct': int(task_pct)
})
```

**REPLACE IT WITH:**

```python
daily_stats.append({
    'day': d.strftime('%a'),
    'focus_pct': int(focus_pct),
    'task_pct': int(task_pct),
    'focus_mins': d_focus,      # ← Add actual minutes
    'task_count': d_tasks       # ← Add actual task count
})
```

---

## STEP 2: Verify the fix

After making this change:

1. Restart your Flask server
2. Refresh the dashboard
3. The chart should now show:
   - "1m" above red bars (for 1 minute of focus)
   - "1" above green bars (for 1 task completed)
   - No bars on days with 0 activity

---

## What this does:

### Before:
```json
{
  "day": "Mon",
  "focus_pct": 0,
  "task_pct": 20
}
```

### After:
```json
{
  "day": "Mon",
  "focus_pct": 0,
  "task_pct": 20,
  "focus_mins": 0,    ← NEW
  "task_count": 1     ← NEW
}
```

---

## Complete Example:

Here's the full section that should be in your app.py:

```python
# Around line 1315-1340
daily_stats = []
for d in dates:
    # 1. Daily Focus Mins
    d_focus = db.session.query(db.func.sum(StudySession.duration)).filter(
        StudySession.user_id == current_user.id,
        db.func.date(StudySession.completed_at) == d
    ).scalar() or 0
    
    # 2. Daily Tasks Completed
    d_tasks = Todo.query.filter(
        Todo.user_id == current_user.id,
        Todo.completed == True,
        db.func.date(Todo.completed_at) == d
    ).count()
    
    # 3. Daily Goals
    d_goals = Todo.query.filter(
        Todo.user_id == current_user.id,
        Todo.completed == True,
        Todo.priority == 'high',
        db.func.date(Todo.completed_at) == d
    ).count()
    
    total_focus_week += d_focus
    total_tasks_week += d_tasks
    total_goals_week += d_goals
    
    # Normalize for chart (Max 4 hours focus = 100%, Max 5 tasks = 100%)
    focus_pct = min((d_focus / 240) * 100, 100)  # 4 hours max bar
    task_pct = min((d_tasks / 5) * 100, 100)     # 5 tasks max bar
    
    daily_stats.append({
        'day': d.strftime('%a'),
        'focus_pct': int(focus_pct),
        'task_pct': int(task_pct),
        'focus_mins': d_focus,      # ← ADD THIS
        'task_count': d_tasks       # ← ADD THIS
    })
```

---

## Testing:

After the fix, check browser console. You should see:

```javascript
Chart data: [
  {day: "Mon", focus_pct: 0, task_pct: 20, focus_mins: 0, task_count: 1},
  {day: "Tue", focus_pct: 0, task_pct: 0, focus_mins: 0, task_count: 0},
  ...
]
```

If you see `focus_mins` and `task_count` in the console, the fix worked! ✅
