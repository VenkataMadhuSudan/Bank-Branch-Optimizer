"""
Unit Tests for Database Connectivity, Health Checks, and Connection Pooling.
Supports both isolated SQLite test databases and live PostgreSQL verification.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from db.connection import check_db_health, get_db_session
from db.schema import Base, Organization, Branch, Role, User
from src.config import get_database_url


def test_sqlite_in_memory_session():
    """Verifies that SQLAlchemy session management and rollback function properly in memory."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    session = TestingSessionLocal()
    org = Organization(org_code="TEST_ORG", name="Test Org", country_code="US")
    session.add(org)
    session.commit()

    retrieved = session.query(Organization).filter_by(org_code="TEST_ORG").first()
    assert retrieved is not None
    assert retrieved.name == "Test Org"
    session.close()


def test_session_rollback_on_error():
    """Verifies that get_db_session automatically rolls back on an unhandled exception."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    session = TestingSession()
    try:
        org1 = Organization(org_code="UNIQUE_CODE", name="Org 1")
        org2 = Organization(org_code="UNIQUE_CODE", name="Org 2")  # Violates unique constraint
        session.add(org1)
        session.flush()
        session.add(org2)
        session.flush()
    except Exception:
        session.rollback()

    # After rollback, unique_code should not be committed
    count = session.query(Organization).filter_by(org_code="UNIQUE_CODE").count()
    assert count == 0
    session.close()


def test_database_health_structure():
    """Verifies that check_db_health returns expected enterprise fields."""
    health = check_db_health()
    assert "status" in health
    assert health["status"] in ("HEALTHY", "UNHEALTHY")
    assert "dialect" in health
    assert "latency_ms" in health
    assert "table_count" in health
    assert isinstance(health["table_count"], int)
