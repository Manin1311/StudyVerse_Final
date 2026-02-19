
from extensions import db
from models import User, UserItem, ActivePowerUp
from constants import SHOP_ITEMS
from services.gamification import GamificationService
from datetime import datetime, timedelta

class ShopService:
    # Hardcoded catalog for now
    ITEMS = SHOP_ITEMS

    @staticmethod
    def buy_item(user: User, item_id: str):
        item = ShopService.ITEMS.get(item_id)
        if not item:
            return {'status': 'error', 'message': 'Item not found.'}
        
        # Check ownership (unless consumable)
        if item['type'] != 'consumable':
            owned = UserItem.query.filter_by(user_id=user.id, item_id=item_id).first()
            if owned:
                return {'status': 'error', 'message': 'You already own this item!'}

        # Check funds
        if user.total_xp < item['price']:
            needed = item['price'] - user.total_xp
            return {'status': 'error', 'message': f"Short on funds! You need {needed} more XP to unlock this."}

        # Deduct XP
        user.total_xp -= item['price']
        
        # Handle Consumables (Power-Ups)
        if item['type'] == 'consumable':
            effect = item.get('effect')
            
            if effect == 'instant_level':
                # Instant Level Up - Add 500 XP to level up
                user.total_xp += 500
                user.level = GamificationService.calculate_level(user.total_xp)
                db.session.commit()
                return {'status': 'success', 'message': f"Level Up! You are now level {user.level}! 🎉", 'new_xp': user.total_xp}
            
            elif effect in ['xp_multiplier', 'mega_xp_multiplier', 'time_multiplier', 'xp_protection']:
                # Duration-based power-ups
                duration = item.get('duration', 86400)  # Default 24 hours
                expires_at = datetime.utcnow() + timedelta(seconds=duration)
                
                # Determine multiplier
                if effect == 'xp_multiplier':
                    multiplier = 2.0
                elif effect == 'mega_xp_multiplier':
                    multiplier = 5.0
                elif effect == 'time_multiplier':
                    multiplier = 2.0
                else:  # xp_protection
                    multiplier = 0.0  # Special case - prevents XP loss
                
                # Create active power-up
                power_up = ActivePowerUp(
                    user_id=user.id,
                    power_up_id=item_id,
                    activated_at=datetime.utcnow(),
                    expires_at=expires_at,
                    multiplier=multiplier,
                    is_active=True
                )
                db.session.add(power_up)
                db.session.commit()
                
                # Calculate hours remaining
                hours = duration / 3600
                return {'status': 'success', 'message': f"{item['name']} activated! Effect lasts for {int(hours)} hours. ⚡", 'new_xp': user.total_xp}
            
            else:
                # Unknown effect - just store as item
                new_item = UserItem(user_id=user.id, item_id=item_id)
                db.session.add(new_item)
                db.session.commit()
                return {'status': 'success', 'message': f"Purchased {item['name']}!", 'new_xp': user.total_xp}
        
        # Handle Themes and Frames
        new_item = UserItem(user_id=user.id, item_id=item_id)
        db.session.add(new_item)
        db.session.commit()
        
        return {'status': 'success', 'message': f"Purchased {item['name']}!", 'new_xp': user.total_xp}

    @staticmethod
    def equip_item(user: User, item_id: str):
        item = ShopService.ITEMS.get(item_id)
        if not item:
            return {'status': 'error', 'message': 'Item not found.'}

        # Verify ownership
        owned = UserItem.query.filter_by(user_id=user.id, item_id=item_id).first()
        if not owned:
            return {'status': 'error', 'message': 'You do not own this item.'}

        # Handle Equipping based on type
        if item['type'] == 'theme':
            # Unequip other themes
            current_active = (
                db.session.query(UserItem)
                .filter(UserItem.user_id == user.id, UserItem.is_active == True)
                .all()
            )
            
            # Deactivate other themes
            for active_item in current_active:
                cat_item = ShopService.ITEMS.get(active_item.item_id)
                if cat_item and cat_item['type'] == 'theme':
                    active_item.is_active = False
            
            # Activate new
            owned.is_active = True
            db.session.commit()
            return {'status': 'success', 'message': f"Equipped {item['name']}!"}

        if item['type'] == 'frame':
            # Unequip other frames
            current_active = (
                db.session.query(UserItem)
                .filter(UserItem.user_id == user.id, UserItem.is_active == True)
                .all()
            )
            
            # Deactivate other frames
            for active_item in current_active:
                cat_item = ShopService.ITEMS.get(active_item.item_id)
                if cat_item and cat_item['type'] == 'frame':
                    active_item.is_active = False
            
            # Activate new
            owned.is_active = True
            db.session.commit()
            return {'status': 'success', 'message': f"Equipped {item['name']}!"}

        return {'status': 'error', 'message': 'This item cannot be equipped.'}
