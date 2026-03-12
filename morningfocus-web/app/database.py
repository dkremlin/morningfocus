"""SQLAlchemy engine and session factory."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Default DB path; override with MORNINGFOCUS_DB env var.
# On Vercel the project directory is read-only, so fall back to /tmp which is
# writable — note data is ephemeral there. Set MORNINGFOCUS_DB to a
# postgresql:// URL for a persistent hosted database.
_local_db = Path(__file__).parent.parent / "data" / "tasks.db"
_tmp_db = Path("/tmp/morningfocus_tasks.db")
_default_db = _local_db if os.access(_local_db.parent, os.W_OK) else _tmp_db
DB_URL = os.environ.get("MORNINGFOCUS_DB", f"sqlite:///{_default_db}")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    _default_db.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

