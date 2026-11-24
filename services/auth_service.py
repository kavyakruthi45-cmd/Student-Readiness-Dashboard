"""
Authentication service for password hashing, verification, and user management.
"""

import bcrypt
import logging
from typing import Optional
from database.connection import get_db_session
from models.user import User

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def authenticate_user(username_or_email: str, password: str) -> Optional[User]:
    """Authenticate a user by username or email and plaintext password."""
    with get_db_session() as session:
        user = session.query(User).filter(
            (User.username == username_or_email.strip()) |
            (User.email == username_or_email.strip().lower())
        ).first()

        if not user:
            return None

        if verify_password(password, user.password_hash):
            # Detach object from session for safe usage outside
            session.expunge(user)
            return user
        return None


def create_user(
    username: str,
    email: str,
    password: str,
    role: str = "student",
    student_id: Optional[int] = None
) -> User:
    """Create a new user with hashed password."""
    with get_db_session() as session:
        existing = session.query(User).filter(
            (User.username == username.strip()) | (User.email == email.strip().lower())
        ).first()
        if existing:
            raise ValueError(f"User with username '{username}' or email '{email}' already exists.")

        user = User(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role=role,
            student_id=student_id
        )
        session.add(user)
        session.flush()
        session.refresh(user)
        session.expunge(user)
        return user


def get_user_by_id(user_id: int) -> Optional[User]:
    """Fetch user by primary key ID."""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.expunge(user)
        return user


def get_user_by_username(username: str) -> Optional[User]:
    """Fetch user by username."""
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username.strip()).first()
        if user:
            session.expunge(user)
        return user
