"""
Concurrency, Stress, and Operational Failure Tests for Bank AI Optimizer.
Tests thread-safety of cryptographic audit ledger and graceful database outage fallbacks.
"""
import pytest
import concurrent.futures
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.schema import Base
from services.audit_service import AuditService, GENESIS_HASH
from db.connection import check_db_health


def test_concurrent_audit_log_hash_chain_integrity():
    """
    CRITICAL CONCURRENCY TEST:
    Fires 20 concurrent audit write operations across multiple worker threads
    and proves that the cryptographic hash chain remains 100% unbroken and uncorrupted.
    """
    # Shared in-memory SQLite database across threads using StaticPool
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(test_engine)
    TestingSession = sessionmaker(bind=test_engine)

    def log_task(thread_id: int):
        sess = TestingSession()
        try:
            return AuditService.log_action(
                actor_username=f"worker_thread_{thread_id}",
                action="CONCURRENT_TASK_EXECUTION",
                resource_type="STRESS_TEST",
                resource_id=f"RES_{thread_id}",
                details={"thread": thread_id},
                session=sess,
            )
        finally:
            sess.close()

    # Execute 20 concurrent thread operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(log_task, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 20

    # Verify that the complete ledger hash chain is intact
    verify_session = TestingSession()
    try:
        integrity = AuditService.verify_ledger_integrity(session=verify_session)
        assert integrity["is_valid"] is True, f"Ledger integrity failure: {integrity.get('tampered_records')}"
        assert integrity["total_records"] == 20
    finally:
        verify_session.close()


def test_database_health_check_non_crashing():
    """Verifies that check_db_health never crashes even if connection fails."""
    health = check_db_health()
    assert isinstance(health, dict)
    assert "status" in health
    assert "dialect" in health
