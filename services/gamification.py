
from extensions import db
from models import User, ActivePowerUp, XPHistory, Badge, UserBadge
from constants import SHOP_ITEMS
from utils import get_rank_info
from datetime import datetime, timedelta

class GamificationService:
    """
    GamificationService - Business logic for XP, levels, ranks, and badges.
    """
    
    @staticmethod
    def calculate_level(total_xp):
        # Level = floor(total_xp / 500) + 1
        return max(1, int(total_xp / 500) + 1)

    @staticmethod
    def get_rank(level):
        return get_rank_info(level)

    @staticmethod
    def add_xp(user_id, source, amount, force_deduct=False):
        user = User.query.get(user_id)
        if not user:
            return
        
        # Prevent XP changes for demo/test users
        demo_emails = ['daksh@gmail.com', 'daksh@studyverse.com', 'demo@studyverse.com']
        if user.email and user.email.lower() in demo_emails:
            print(f"XP change blocked for demo user: {user.email}")
            return {'earned': 0, 'message': 'Demo account - XP locked'}

        # 1. Fetch ALL active power-ups for the user
        active_powerups = ActivePowerUp.query.filter_by(
            user_id=user.id,
            is_active=True
        ).all()
        
        # 2. Categorize and clean up expired power-ups
        xp_multiplier = 1.0
        time_multiplier = 1.0
        has_protection = False
        active_boost = None

        for powerup in active_powerups:
            if powerup.is_expired():
                powerup.is_active = False
                continue
            
            # Fetch item details from catalog to know the effect type
            item_id = powerup.power_up_id
            cat_item = SHOP_ITEMS.get(item_id)
            if not cat_item: continue

            effect = cat_item.get('effect')
            
            if effect in ['xp_multiplier', 'mega_xp_multiplier']:
                if powerup.multiplier > xp_multiplier:
                    xp_multiplier = powerup.multiplier
                    active_boost = item_id
            elif effect == 'time_multiplier':
                if powerup.multiplier > time_multiplier:
                    time_multiplier = powerup.multiplier
            elif effect == 'xp_protection':
                has_protection = True
        
        # 3. Handle XP loss protection
        if amount < 0:
            if not force_deduct and has_protection:
                return {'earned': 0, 'message': 'XP Protection Active! No XP lost.'}
            
            # Direct deduction logic
            user.total_xp = max(0, user.total_xp + amount) 
            
            # Log negative history
            log = XPHistory(user_id=user.id, source=source, amount=amount)
            db.session.add(log)
            db.session.commit()
            return {'earned': amount, 'new_total': user.total_xp}

        # 4. Apply special multipliers based on source (e.g., Double Time for focus)
        actual_multiplier = xp_multiplier
        if source == 'focus' and time_multiplier > 1.0:
            actual_multiplier *= time_multiplier

        # 5. Cap Focus XP daily (Check BEFORE multipliers to keep cap consistent)
        if source == 'focus':
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_focus_xp = db.session.query(db.func.sum(XPHistory.amount))\
                .filter(XPHistory.user_id == user.id, XPHistory.source == 'focus', XPHistory.timestamp >= today_start)\
                .scalar() or 0
            
            if daily_focus_xp >= 500:
                return {'earned': 0, 'message': 'Daily Focus XP cap reached!'}
            
            if daily_focus_xp + amount > 500:
                amount = 500 - daily_focus_xp

        if amount <= 0:
            return

        # Apply multiplier
        original_amount = amount
        if actual_multiplier > 1.0:
            amount = int(amount * actual_multiplier)

        user.total_xp += amount
        
        # Level Up Check
        new_level = GamificationService.calculate_level(user.total_xp)
        leveled_up = False
        if new_level > user.level:
            user.level = new_level
            leveled_up = True
            
        # Log History
        log = XPHistory(user_id=user.id, source=source, amount=amount)
        db.session.add(log)
        
        # Update Streak (if not already updated today)
        GamificationService.update_streak(user)
        
        # Check Badges
        GamificationService.check_badges(user)
        
        db.session.commit()
        
        result = {
            'earned': amount, 
            'new_total': user.total_xp, 
            'leveled_up': leveled_up,
            'new_level': user.level,
            'rank': GamificationService.get_rank(user.level)
        }
        
        if actual_multiplier > 1.0:
            result['multiplier'] = actual_multiplier
            result['base_amount'] = original_amount
            result['boost_active'] = active_boost
        
        return result

    @staticmethod
    def update_streak(user):
        today = datetime.utcnow().date()
        if user.last_activity_date == today:
            return # Already active today
        
        if user.last_activity_date == today - timedelta(days=1):
            user.current_streak += 1
        else:
            user.current_streak = 1 # Reset if missed a day (or first time)
            
        user.last_activity_date = today
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak

    @staticmethod
    def check_badges(user):
        # 1. Streak Badges
        if user.current_streak >= 30:
            GamificationService.award_badge(user, 'Consistency King')
        
        # 2. XP Badges (Level based roughly)
        if user.level >= 10:
             GamificationService.award_badge(user, 'Rising Star')
        if user.level >= 50:
             GamificationService.award_badge(user, 'Dedicated Scholar')
        if user.level >= 100:
             GamificationService.award_badge(user, 'Centurion')
        
    @staticmethod
    def award_badge(user, badge_name):
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge:
            # Create default if missing (lazy init)
            if badge_name == 'Consistency King':
                badge = Badge(name='Consistency King', description='Achieve a 30-day streak', icon='fa-fire', criteria_type='streak', criteria_value=30)
            elif badge_name == 'Rising Star':
                badge = Badge(name='Rising Star', description='Reach Level 10', icon='fa-star', criteria_type='level', criteria_value=10)
            elif badge_name == 'Dedicated Scholar':
                badge = Badge(name='Dedicated Scholar', description='Reach Level 50', icon='fa-book-open', criteria_type='level', criteria_value=50)
            elif badge_name == 'Centurion':
                badge = Badge(name='Centurion', description='Reach Level 100', icon='fa-crown', criteria_type='level', criteria_value=100)
            else:
                return 
            db.session.add(badge)
            db.session.commit()
            
        if not UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
            ub = UserBadge(user_id=user.id, badge_id=badge.id)
            db.session.add(ub)
