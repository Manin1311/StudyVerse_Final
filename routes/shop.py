
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import UserItem
from services.shop import ShopService
from services.gamification import GamificationService
from datetime import datetime

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/shop')
@login_required
def index():
    # Only show active items
    active_items = {k: v for k, v in ShopService.ITEMS.items() if v.get('is_visible', True)}
    
    # Get user's purchased items
    user_items = UserItem.query.filter_by(user_id=current_user.id).all()
    owned_ids = [item.item_id for item in user_items]
    
    # Check what is currently equipped
    equipped_theme = None
    equipped_frame = None
    
    for item in user_items:
        if item.is_active:
            cat_item = ShopService.ITEMS.get(item.item_id)
            if cat_item:
                if cat_item['type'] == 'theme':
                    equipped_theme = item.item_id
                elif cat_item['type'] == 'frame':
                    equipped_frame = item.item_id

    return render_template(
        'shop.html', 
        shop_items=active_items, 
        owned_ids=owned_ids,
        equipped_theme=equipped_theme,
        equipped_frame=equipped_frame,
        user_coins=current_user.total_xp  # Using XP as coins for now
    )

@shop_bp.route('/shop/buy/<item_id>', methods=['POST'])
@login_required
def buy(item_id):
    success, msg = ShopService.buy_item(current_user.id, item_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('shop.index'))

@shop_bp.route('/shop/equip/<item_id>', methods=['POST'])
@login_required
def equip(item_id):
    success, msg = ShopService.equip_item(current_user.id, item_id)
    if success:
        # If theme, we might want to reload page to apply changes or just flash
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('shop.index'))

@shop_bp.route('/shop/unequip/<item_id>', methods=['POST'])
@login_required
def unequip(item_id):
    # Logic to unequip
    user_item = UserItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if user_item:
        user_item.is_active = False
        db.session.commit()
        flash('Item unequipped.', 'success')
    return redirect(url_for('shop.index'))
