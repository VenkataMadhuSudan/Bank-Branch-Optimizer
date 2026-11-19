"""
Unit Tests for Normalized Relational Schema Definitions and Constraints.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schema import (
    Base, Organization, Region, Branch, BranchOperatingHour,
    Counter, ServiceCategory, Role, User, UserRole, UserBranchPermission,
    Employee, EmployeeSkill, CustomerArrival, AuditLog
)


@pytest.fixture
def test_db_session():
    """Provides a fresh isolated in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_organization_region_branch_hierarchy(test_db_session):
    """Verifies organizational cascade and relationships."""
    org = Organization(org_code="ORG_TEST", name="Test Bank Corp")
    test_db_session.add(org)
    test_db_session.flush()

    region = Region(organization_id=org.id, region_code="REG_NORTH", name="Northern Region")
    test_db_session.add(region)
    test_db_session.flush()

    branch = Branch(
        region_id=region.id,
        branch_code="BR_101",
        name="Metro North Main",
        cluster="Metro North",
        total_counters=8,
        peak_window="11:00-14:00"
    )
    test_db_session.add(branch)
    test_db_session.commit()

    # Query back through hierarchy
    queried_branch = test_db_session.query(Branch).filter_by(branch_code="BR_101").first()
    assert queried_branch is not None
    assert queried_branch.region.name == "Northern Region"
    assert queried_branch.region.organization.name == "Test Bank Corp"


def test_user_roles_and_branch_permissions(test_db_session):
    """Verifies RBAC and branch permission models."""
    user = User(
        username="manager_dan",
        email="dan@apexbank.local",
        password_hash="mock_hash_pbkdf2",
        full_name="Dan Branch Manager"
    )
    role = Role(role_name="BRANCH_MANAGER", description="Branch Manager Role")
    test_db_session.add_all([user, role])
    test_db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    test_db_session.add(user_role)
    test_db_session.commit()

    queried_user = test_db_session.query(User).filter_by(username="manager_dan").first()
    assert len(queried_user.user_roles) == 1
    assert queried_user.user_roles[0].role.role_name == "BRANCH_MANAGER"


def test_audit_log_fields(test_db_session):
    """Verifies that audit log model stores cryptographic hash fields."""
    log = AuditLog(
        actor_username="admin",
        action="UPDATE_COUNTER",
        resource_type="COUNTER",
        resource_id="C_01",
        prev_hash="0000000000000000000000000000000000000000000000000000000000000000",
        record_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    test_db_session.add(log)
    test_db_session.commit()

    retrieved = test_db_session.query(AuditLog).first()
    assert retrieved is not None
    assert len(retrieved.prev_hash) == 64
    assert len(retrieved.record_hash) == 64
