"""
Database connection, session management, and schema initialization.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import config
from database.base import Base

# Engine configuration for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}

engine = create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionFactory)


@contextmanager
def get_db_session():
    """Context manager for safe transactional database sessions."""
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create all database tables if they do not exist."""
    # Import all models to ensure metadata registration
    import models.user
    import models.student
    import models.score_history
    Base.metadata.create_all(bind=engine)
