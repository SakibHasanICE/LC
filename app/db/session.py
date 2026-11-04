from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they don't exist (fine for MVP; switch to Alembic later)."""
    from app.db import models  # noqa: F401  (registers models on Base)
    Base.metadata.create_all(bind=engine)
