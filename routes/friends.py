
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Friendship
from utils import get_rank_info

friends_bp = Blueprint('friends', __name__)


def _friendship_status(user_id, other_id):
    """Return the friendship status between two users from user_id's perspective."""
    f = Friendship.query.filter(
        ((Friendship.user_id == user_id) & (Friendship.friend_id == other_id)) |
        ((Friendship.user_id == other_id) & (Friendship.friend_id == user_id))
    ).first()
    if not f:
        return 'none'
    if f.status == 'accepted':
        return 'accepted'
    # Pending: determine direction
    if f.user_id == user_id:
        return 'sent'       # current user sent the request
    return 'received'       # current user received the request


@friends_bp.route('/friends')
@login_required
def index():
    # Pending friend requests received by current user
    pending_ids = Friendship.query.filter_by(
        friend_id=current_user.id, status='pending'
    ).all()

    friend_requests = []
    for f in pending_ids:
        sender = User.query.get(f.user_id)
        if sender:
            rank_data = get_rank_info(sender.level)
            friend_requests.append({
                'request_id': f.id,
                'name': f'{sender.first_name or ""} {sender.last_name or ""}'.strip() or sender.email,
                'avatar': sender.get_avatar(),
                'level': sender.level,
                'rank': rank_data,
            })

    # Accepted friends
    accepted = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)),
        Friendship.status == 'accepted'
    ).all()

    my_friends = []
    for f in accepted:
        other_id = f.friend_id if f.user_id == current_user.id else f.user_id
        other = User.query.get(other_id)
        if other:
            rank_data = get_rank_info(other.level)
            my_friends.append({
                'id': other.id,
                'name': f'{other.first_name or ""} {other.last_name or ""}'.strip() or other.email,
                'avatar': other.get_avatar(),
                'level': other.level,
                'rank': rank_data,
                'is_public': other.is_public_profile,
            })

    return render_template('friends.html',
                           friend_requests=friend_requests,
                           my_friends=my_friends)


@friends_bp.route('/api/users/search')
@login_required
def search_users():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    users = User.query.filter(
        User.id != current_user.id,
        User.is_banned == False,
        (User.first_name.ilike(f'%{q}%')) |
        (User.last_name.ilike(f'%{q}%')) |
        (User.email.ilike(f'%{q}%'))
    ).limit(10).all()

    result = []
    for u in users:
        status = _friendship_status(current_user.id, u.id)
        result.append({
            'id': u.id,
            'name': f'{u.first_name or ""} {u.last_name or ""}'.strip() or u.email,
            'email': u.email,
            'avatar': u.get_avatar(size=64),
            'status': status,
        })
    return jsonify(result)


@friends_bp.route('/friends/request/<int:user_id>', methods=['POST'])
@login_required
def send_request(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot add yourself'}), 400

    existing = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
    ).first()

    if existing:
        return jsonify({'error': 'Request already exists or already friends'}), 400

    f = Friendship(user_id=current_user.id, friend_id=user_id, status='pending')
    db.session.add(f)
    db.session.commit()
    return jsonify({'status': 'success'})


@friends_bp.route('/friends/accept/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    f = Friendship.query.filter_by(id=request_id, friend_id=current_user.id, status='pending').first()
    if not f:
        return jsonify({'error': 'Request not found'}), 404
    f.status = 'accepted'
    db.session.commit()
    return jsonify({'status': 'success'})


@friends_bp.route('/friends/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    f = Friendship.query.filter_by(id=request_id, friend_id=current_user.id, status='pending').first()
    if not f:
        return jsonify({'error': 'Request not found'}), 404
    db.session.delete(f)
    db.session.commit()
    return jsonify({'status': 'success'})
