"""
Comprehensive Security, Authentication, RBAC, and Branch-Level Isolation Tests.
Validates PBKDF2 hashing, lockout throttling, JWT signing, branch isolation, and cryptographic audit hash chain.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from services.auth_service import (
    AuthService,
    ROLE_CENTRAL_ADMIN,
    ROLE_REGIONAL_MANAGER,
    ROLE_BRANCH_MANAGER,
    ROLE_EMPLOYEE
)
from services.audit_service import AuditService, GENESIS_HASH


def test_password_hashing_and_verification():
    """Verifies NIST PBKDF2-HMAC-SHA256 password hashing with salt."""
    raw_password = "SecureEnterprisePassword2026!"
    hashed = AuthService.hash_password(raw_password)

    assert hashed.startswith("pbkdf2:sha256:600000$")
    assert AuthService.verify_password(raw_password, hashed) is True
    assert AuthService.verify_password("WrongPassword!", hashed) is False
    assert AuthService.verify_password("", hashed) is False


def test_password_complexity_rejection():
    """Verifies that short passwords are rejected."""
    with pytest.raises(ValueError):
        AuthService.hash_password("short")


def test_account_lockout_throttling():
    """Verifies account lockout occurs after 5 failed attempts."""
    test_user = "brute_force_target_user"
    AuthService.clear_failed_attempts(test_user)

    for _ in range(4):
        AuthService.record_failed_attempt(test_user)
        locked, _ = AuthService.is_locked_out(test_user)
        assert locked is False

    # 5th attempt locks the account
    AuthService.record_failed_attempt(test_user)
    locked, remaining_secs = AuthService.is_locked_out(test_user)
    assert locked is True
    assert remaining_secs > 0

    # Clear unlocks
    AuthService.clear_failed_attempts(test_user)
    locked, _ = AuthService.is_locked_out(test_user)
    assert locked is False


def test_jwt_access_token_lifecycle():
    """Verifies JWT issuance and decoding with expiration."""
    user_payload = {
        "user_id": 42,
        "username": "tester",
        "roles": [ROLE_BRANCH_MANAGER]
    }
    token = AuthService.create_access_token(user_payload, expires_delta=timedelta(minutes=15))
    decoded = AuthService.decode_access_token(token)
    assert decoded is not None
    assert decoded["username"] == "tester"
    assert ROLE_BRANCH_MANAGER in decoded["roles"]

    # Expired token test
    expired_token = AuthService.create_access_token(user_payload, expires_delta=timedelta(seconds=-10))
    decoded_expired = AuthService.decode_access_token(expired_token)
    assert decoded_expired is None


def test_branch_level_data_isolation():
    """
    CRITICAL SECURITY INVARIANT:
    Proves that a Branch Manager assigned strictly to Branch 1 CANNOT access Branch 2's data!
    """
    branch_1_manager = {
        "user_id": 101,
        "username": "manager_branch_1",
        "roles": [ROLE_BRANCH_MANAGER],
        "branch_permissions": [
            {
                "branch_id": 1,
                "can_view": True,
                "can_optimize": True,
                "can_manage_staff": True
            }
        ]
    }

    # Accessing assigned Branch 1 -> ALLOWED
    assert AuthService.check_branch_access(branch_1_manager, branch_id=1, required_capability="can_view") is True
    assert AuthService.check_branch_access(branch_1_manager, branch_id=1, required_capability="can_optimize") is True

    # Accessing unassigned Branch 2 -> STRICTLY DENIED
    assert AuthService.check_branch_access(branch_1_manager, branch_id=2, required_capability="can_view") is False
    assert AuthService.check_branch_access(branch_1_manager, branch_id=2, required_capability="can_optimize") is False
    assert AuthService.check_branch_access(branch_1_manager, branch_id=3, required_capability="can_view") is False


def test_central_admin_universal_access():
    """Verifies Central Administrator has network-wide access across all branches."""
    central_admin = {
        "user_id": 1,
        "username": "superadmin",
        "roles": [ROLE_CENTRAL_ADMIN],
        "branch_permissions": []
    }
    assert AuthService.check_branch_access(central_admin, branch_id=1) is True
    assert AuthService.check_branch_access(central_admin, branch_id=2) is True
    assert AuthService.check_branch_access(central_admin, branch_id=99) is True


def test_audit_hash_chain_computation():
    """Verifies SHA-256 forward-linked cryptographic hash computation."""
    h1 = AuditService._compute_hash(
        prev_hash=GENESIS_HASH,
        timestamp_str="2026-11-19 12:00:00.000000",
        actor_username="admin",
        action="LOGIN",
        resource_type="USER",
        resource_id="1",
        details_json="{}"
    )
    assert len(h1) == 64
    assert h1 != GENESIS_HASH

    # Hash changes when data changes
    h2 = AuditService._compute_hash(
        prev_hash=h1,
        timestamp_str="2026-11-19 12:01:00.000000",
        actor_username="admin",
        action="OPTIMIZE_STAFF",
        resource_type="BRANCH",
        resource_id="BR_001",
        details_json="{\"counters\": 6}"
    )
    assert len(h2) == 64
    assert h2 != h1
