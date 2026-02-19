
from datetime import datetime
from pytz import timezone, utc
from constants import RANKS
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

# Indian Standard Time (IST) timezone
IST = timezone('Asia/Kolkata')

def to_ist_time(utc_datetime):
    """
    Convert UTC datetime to IST and return formatted 12-hour time string.
    
    Args:
        utc_datetime: datetime object in UTC timezone
    
    Returns:
        str: Formatted time string in 12-hour format (e.g., "02:30 PM")
    """
    if not utc_datetime:
        return ""
    
    # Ensure datetime is timezone-aware (UTC)
    if utc_datetime.tzinfo is None:
        utc_datetime = utc.localize(utc_datetime)
    
    # Convert to IST
    ist_datetime = utc_datetime.astimezone(IST)
    
    # Format as 12-hour time with AM/PM
    return ist_datetime.strftime('%I:%M %p')

def get_rank_info(level):
    """
    Get rank details based on level.
    """
    if level is None: level = 1
    # Check regular ranks
    for (min_lvl, max_lvl), (name, icon, color) in RANKS.items():
        if min_lvl <= level <= max_lvl:
            return {'name': name, 'icon': icon, 'color': color}
            
    # If level > 100, return generic Grandmaster or similar logic
    return {'name': 'Grandmaster', 'icon': 'fa-crown', 'color': '#FFD700'}

def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.auth'))
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.dashboard_view'))
        return f(*args, **kwargs)
    return decorated_function

class Stack:
    """Simple LIFO stack used for undo functionality."""
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            return None
        return self._items.pop()

    def is_empty(self):
        return len(self._items) == 0


class LRUCache:
    """LRU Cache using dict + list (simplified)."""
    def __init__(self, capacity=50):
        self.capacity = capacity
        self.cache = {}
        self.order = []  # most recent at end

    def get(self, key):
        if key not in self.cache:
            return None
        if key in self.order:
            self.order.remove(key)
        self.order.append(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache[key] = value
            if key in self.order:
                self.order.remove(key)
            self.order.append(key)
            return

        if len(self.cache) >= self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]

        self.cache[key] = value
        self.order.append(key)
