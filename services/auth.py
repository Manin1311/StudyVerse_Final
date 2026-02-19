
from extensions import db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    """Authentication service."""

    @staticmethod
    def create_user(email: str, password: str, first_name: str, last_name: str) -> "User":
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(email: str, password: str):
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        
        if not user.password_hash:
            return None
        
        if check_password_hash(user.password_hash, password):
            return user
        
        return None
