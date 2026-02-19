
from extensions import db
from models import Group, GroupMember
import random
import string

class GroupService:
    """Group operations: create, join, membership check."""

    @staticmethod
    def _generate_invite_code(length: int = 6) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(random.choice(alphabet) for _ in range(length))

    @staticmethod
    def create_group(admin_user_id: int, name: str) -> Group:
        invite_code = GroupService._generate_invite_code()
        while Group.query.filter_by(invite_code=invite_code).first() is not None:
            invite_code = GroupService._generate_invite_code()

        group = Group(name=name, admin_id=admin_user_id, invite_code=invite_code)
        db.session.add(group)
        db.session.commit()

        db.session.add(GroupMember(group_id=group.id, user_id=admin_user_id))
        db.session.commit()
        return group

    @staticmethod
    def join_group(user_id: int, invite_code: str) -> Group:
        group = Group.query.filter_by(invite_code=invite_code).first()
        if not group:
            raise ValueError("Invalid invite code")

        existing = GroupMember.query.filter_by(group_id=group.id, user_id=user_id).first()
        if existing:
            return group

        db.session.add(GroupMember(group_id=group.id, user_id=user_id))
        db.session.commit()
        return group

    @staticmethod
    def get_user_group(user_id: int):
        membership = GroupMember.query.filter_by(user_id=user_id).order_by(GroupMember.joined_at.desc()).first()
        if not membership:
            return None
        return Group.query.get(membership.group_id)
