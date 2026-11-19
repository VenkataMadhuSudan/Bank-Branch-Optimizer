"""
Database Connection, Pooling, Session Management, and Health Checks.
Authoritative support for Neon PostgreSQL with safe, non-destructive local fallback.
"""
from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_database_url, get_pooled_database_url
from src.utils.logger import logger
from db.schema import Base

# Module-level singletons
_ENGINE: Optional[Engine] = None
_SESSION_FACTORY: Optional[sessionmaker] = None
_IS_PG_AVAILABLE: Optional[bool] = None


def get_engine(use_pooled: bool = False) -> Engine:
    """
    Retrieves or initializes the singleton SQLAlchemy Engine with robust connection pooling.
    Uses pool_pre_ping=True to guard against stale disconnected sockets (crucial for serverless Neon).
    """
    global _ENGINE, _SESSION_FACTORY, _IS_PG_AVAILABLE

    if _ENGINE is not None:
        return _ENGINE

    db_url = get_pooled_database_url() if use_pooled else get_database_url()
    is_sqlite = db_url.startswith("sqlite")

    engine_kwargs: Dict[str, Any] = {
        "future": True,
    }

    if is_sqlite:
        # SQLite local development configuration
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        logger.warning(
            "Using local SQLite database fallback. Configure Neon DATABASE_URL in .env for production PostgreSQL."
        )
    else:
        # Neon PostgreSQL enterprise connection pooling
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_pre_ping"] = True      # Automatic reconnect on stale serverless endpoints
        engine_kwargs["pool_recycle"] = 300        # Recycle connections every 5 minutes
        engine_kwargs["connect_args"] = {"connect_timeout": 4}

    try:
        _ENGINE = create_engine(db_url, **engine_kwargs)
        _SESSION_FACTORY = sessionmaker(
            bind=_ENGINE,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        _IS_PG_AVAILABLE = not is_sqlite
        logger.info(f"Database engine initialized successfully with dialect: {_ENGINE.dialect.name}")
        return _ENGINE
    except Exception as exc:
        logger.error(f"Failed to initialize database engine: {exc}")
        _IS_PG_AVAILABLE = False
        raise


def get_session_factory() -> sessionmaker:
    """Returns the singleton sessionmaker."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        get_engine()
    return _SESSION_FACTORY


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for transactional database operations with automatic rollback on error."""
    session_factory = get_session_factory()
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session."""
    session_factory = get_session_factory()
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_health() -> Dict[str, Any]:
    """
    Performs comprehensive database availability and latency diagnostics.
    Never crashes the application; returns structured status dictionary.
    """
    start_time = time.perf_counter()
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Query standard version information
            if engine.dialect.name == "postgresql":
                version_str = conn.execute(text("SELECT version();")).scalar()
            else:
                version_str = conn.execute(text("SELECT sqlite_version();")).scalar()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Inspect existing tables
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            return {
                "status": "HEALTHY",
                "dialect": engine.dialect.name,
                "latency_ms": latency_ms,
                "version": str(version_str)[:80],
                "table_count": len(existing_tables),
                "tables": existing_tables,
                "is_authoritative_pg": engine.dialect.name == "postgresql",
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning(f"Database health check failed ({latency_ms}ms): {exc}")
        return {
            "status": "UNHEALTHY",
            "dialect": "unknown",
            "latency_ms": latency_ms,
            "error": str(exc),
            "table_count": 0,
            "tables": [],
            "is_authoritative_pg": False,
        }


def init_db(check_compatibility: bool = True) -> Dict[str, Any]:
    """
    Safely creates all database tables if they do not exist.
    NON-DESTRUCTIVE: Never drops tables or deletes existing operational records.
    """
    engine = get_engine()
    logger.info("Verifying and initializing database schema (non-destructive)...")
    Base.metadata.create_all(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    created_tables = inspector.get_table_names()
    logger.info(f"Database schema verified: {len(created_tables)} tables present.")
    return {
        "status": "INITIALIZED",
        "table_count": len(created_tables),
        "tables": created_tables,
    }
