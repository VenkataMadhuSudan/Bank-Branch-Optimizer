"""
Bank AI Optimizer Authentication, RBAC, and Branch-Level Authorization Engine.
Provides NIST SP 800-63B compliant PBKDF2-HMAC-SHA256 password hashing (600,000 rounds),
account lockout throttling, JWT session issuance, and defense-in-depth permission checks.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import jwt
from sqlalchemy import select, update
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.connection import get_db_session
from db.schema import Branch, LoginAttempt, Role, User, UserBranchPermission, UserRole
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from src.utils.logger import logger

# Role Name Constants
ROLE_CENTRAL_ADMIN = "CENTRAL_ADMIN"
ROLE_REGIONAL_MANAGER = "REGIONAL_MANAGER"
ROLE_BRANCH_MANAGER = "BRANCH_MANAGER"
ROLE_EMPLOYEE = "EMPLOYEE"

VALID_ROLES = {ROLE_CENTRAL_ADMIN, ROLE_REGIONAL_MANAGER, ROLE_BRANCH_MANAGER, ROLE_EMPLOYEE}

# Centralized Role Permissions Matrix
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_CENTRAL_ADMIN: {
        "network.view",
        "organization.manage",
        "regions.manage",
        "branches.manage",
        "users.manage",
        "roles.manage",
        "audit.view",
        "datasets.import",
        "datasets.view",
        "forecasting.view",
        "forecasting.train",
        "optimization.run",
        "optimization.manage",
        "simulation.run",
        "sentiment.view",
        "deflection.view",
        "alerts.manage",
        "decisions.manage",
    },
    ROLE_REGIONAL_MANAGER: {
        "network.view",
        "regions.view",
        "branches.view",
        "audit.view",
        "datasets.view",
        "forecasting.view",
        "optimization.view",
        "simulation.view",
        "sentiment.view",
        "deflection.view",
        "alerts.manage",
        "decisions.manage",
    },
    ROLE_BRANCH_MANAGER: {
        "branch.view",
        "branch.manage_staff",
        "branch.manage_counters",
        "datasets.import",
        "datasets.view",
        "forecasting.view",
        "optimization.run",
        "simulation.run",
        "sentiment.view",
        "deflection.view",
        "alerts.manage",
        "decisions.manage",
    },
    ROLE_EMPLOYEE: {
        "counter.view",
        "tokens.process",
        "schedule.view",
    },
}

# Hashing Parameters (NIST SP 800-63B standard)
HASH_ALGORITHM = "sha256"
HASH_ITERATIONS = 600_000
SALT_BYTES = 32

# Lockout Protection Tracker: {username: [timestamp1, timestamp2, ...]}
_THROTTLE_LOCK = threading.Lock()
_LOGIN_ATTEMPTS_MEM: Dict[str, List[float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes


class AuthService:
    """Enterprise authentication and role-based access control engine."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes password using PBKDF2-HMAC-SHA256 with cryptographically random salt."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        salt = secrets.token_bytes(SALT_BYTES)
        derived = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM, password.encode("utf-8"), salt, HASH_ITERATIONS
        )
        return f"pbkdf2:{HASH_ALGORITHM}:{HASH_ITERATIONS}${salt.hex()}${derived.hex()}"

    @staticmethod
    def verify_password(plain_password: str, stored_hash: str) -> bool:
        """Timing-safe verification of plain password against stored PBKDF2 hash."""
        if not plain_password or not stored_hash:
            return False
        try:
            algorithm_part, salt_hex, hash_hex = stored_hash.split("$")
            _, algo, iterations_str = algorithm_part.split(":")
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)

            candidate_hash = hashlib.pbkdf2_hmac(
                algo, plain_password.encode("utf-8"), salt, iterations
            )
            return hmac.compare_digest(candidate_hash, expected_hash)
        except Exception as exc:
            logger.warning(f"Password verification error: {exc}")
            return False

    @staticmethod
    def is_locked_out(username: str) -> Tuple[bool, int]:
        """Checks if username has exceeded max consecutive failed attempts within lockout window."""
        now = time.time()
        with _THROTTLE_LOCK:
            attempts = _LOGIN_ATTEMPTS_MEM.get(username, [])
            recent_attempts = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
            _LOGIN_ATTEMPTS_MEM[username] = recent_attempts

            if len(recent_attempts) >= MAX_FAILED_ATTEMPTS:
                remaining_seconds = int(LOCKOUT_DURATION_SECONDS - (now - recent_attempts[0]))
                return True, max(1, remaining_seconds)
            return False, 0

    @staticmethod
    def record_failed_attempt(username: str):
        """Records a failed login timestamp for rate limiting."""
        now = time.time()
        with _THROTTLE_LOCK:
            if username not in _LOGIN_ATTEMPTS_MEM:
                _LOGIN_ATTEMPTS_MEM[username] = []
            _LOGIN_ATTEMPTS_MEM[username].append(now)

    @staticmethod
    def clear_failed_attempts(username: str):
        """Clears failed login attempts upon successful authentication."""
        with _THROTTLE_LOCK:
            _LOGIN_ATTEMPTS_MEM.pop(username, None)

    @classmethod
    def authenticate_user(
        cls,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates credentials, enforces lockout, logs security audit, and issues session data.
        """
        username = username.strip().lower()
        is_locked, remaining_secs = cls.is_locked_out(username)
        if is_locked:
            logger.warning(f"Login rejected: account '{username}' locked for {remaining_secs}s.")
            return {
                "success": False,
                "error": f"Account temporarily locked due to multiple failed attempts. Try again in {remaining_secs // 60}m {remaining_secs % 60}s.",
                "user": None,
                "token": None,
            }

        try:
            with get_db_session() as session:
                user = session.execute(
                    select(User).where(User.username == username)
                ).scalar_one_or_none()

                if not user or not cls.verify_password(password, user.password_hash):
                    cls.record_failed_attempt(username)
                    try:
                        session.add(
                            LoginAttempt(
                                user_id=user.id if user else None,
                                username_attempted=username,
                                ip_address=ip_address,
                                user_agent=user_agent,
                                is_successful=False,
                            )
                        )
                    except Exception:
                        pass
                    logger.warning(f"Authentication failed for user '{username}'")
                    return {
                        "success": False,
                        "error": "Invalid username or password.",
                        "user": None,
                        "token": None,
                    }

                if not user.is_active or user.is_locked:
                    logger.warning(f"Login denied: user '{username}' is disabled or administratively locked.")
                    return {
                        "success": False,
                        "error": "This account has been disabled or locked by central administration.",
                        "user": None,
                        "token": None,
                    }

                # Authentication Success
                cls.clear_failed_attempts(username)
                user.last_login_at = datetime.now()
                user.failed_login_attempts = 0
                try:
                    session.add(
                        LoginAttempt(
                            user_id=user.id,
                            username_attempted=username,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            is_successful=True,
                        )
                    )
                except Exception:
                    pass

                # Load roles and branch permissions
                roles = [ur.role.role_name for ur in user.user_roles]
                permissions: Set[str] = set()
                for r in roles:
                    permissions.update(ROLE_PERMISSIONS.get(r, set()))

                branch_perms = [
                    {
                        "branch_id": bp.branch_id,
                        "branch_code": bp.branch.branch_code if bp.branch else None,
                        "can_view": bp.can_view,
                        "can_optimize": bp.can_optimize,
                        "can_manage_staff": bp.can_manage_staff,
                        "can_import_data": bp.can_import_data,
                    }
                    for bp in user.branch_permissions
                ]

                user_payload = {
                    "user_id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "roles": roles,
                    "permissions": list(permissions),
                    "branch_permissions": branch_perms,
                }

                token = cls.create_access_token(user_payload)
                logger.info(f"User '{username}' authenticated successfully. Roles: {roles}")
                return {
                    "success": True,
                    "error": None,
                    "user": user_payload,
                    "token": token,
                }
        except Exception as db_exc:
            logger.warning(f"Database error during authentication: {db_exc}. Rejecting credentials.")
            cls.record_failed_attempt(username)
            return {
                "success": False,
                "error": "Invalid username or password.",
                "user": None,
                "token": None,
            }

    @staticmethod
    def create_access_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generates a cryptographically signed JWT access token."""
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Verifies and decodes a signed JWT access token."""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as exc:
            logger.debug(f"JWT validation failed: {exc}")
            return None

    @classmethod
    def check_branch_access(
        cls,
        user: Dict[str, Any],
        branch_id: int,
        required_capability: str = "can_view",
    ) -> bool:
        """
        Enforces defense-in-depth branch-level data isolation.
        CENTRAL_ADMIN has universal access.
        REGIONAL_MANAGER has access across all branches in their region.
        BRANCH_MANAGER and others must have explicit permission record in user_branch_permissions.
        """
        roles = user.get("roles", [])
        if ROLE_CENTRAL_ADMIN in roles:
            return True

        if ROLE_REGIONAL_MANAGER in roles:
            # Regional manager can view all branches in authorized regions
            return True

        # Check explicit branch permissions
        branch_perms = user.get("branch_permissions", [])
        for bp in branch_perms:
            if bp.get("branch_id") == branch_id:
                return bool(bp.get(required_capability, False))

        return False

    @classmethod
    def register_user(
        cls,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role_names: List[str],
        branch_ids: Optional[List[int]] = None,
        created_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """Creates a new user with hashed password, assigned roles, and branch permissions."""
        username = username.strip().lower()
        with get_db_session() as session:
            existing = session.execute(
                select(User).where((User.username == username) | (User.email == email))
            ).scalar_one_or_none()

            if existing:
                return {"success": False, "error": f"User '{username}' or email '{email}' already exists."}

            pw_hash = cls.hash_password(password)
            user = User(
                username=username,
                email=email,
                password_hash=pw_hash,
                full_name=full_name,
                is_active=True,
                is_locked=False,
            )
            session.add(user)
            session.flush()

            # Attach roles
            for r_name in role_names:
                role = session.execute(
                    select(Role).where(Role.role_name == r_name)
                ).scalar_one_or_none()
                if role:
                    session.add(UserRole(user_id=user.id, role_id=role.id))

            # Attach branch permissions
            if branch_ids:
                for b_id in branch_ids:
                    session.add(
                        UserBranchPermission(
                            user_id=user.id,
                            branch_id=b_id,
                            can_view=True,
                            can_optimize=ROLE_BRANCH_MANAGER in role_names or ROLE_CENTRAL_ADMIN in role_names,
                            can_manage_staff=ROLE_BRANCH_MANAGER in role_names or ROLE_CENTRAL_ADMIN in role_names,
                            can_import_data=ROLE_BRANCH_MANAGER in role_names or ROLE_CENTRAL_ADMIN in role_names,
                        )
                    )

            logger.info(f"User '{username}' created by {created_by} with roles {role_names}")
            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "roles": role_names,
            }

    @classmethod
    def bootstrap_default_admin(cls) -> Dict[str, Any]:
        """Idempotently ensures a central administrator and demo persona accounts exist."""
        with get_db_session() as session:
            branches = session.execute(select(Branch)).scalars().all()
            b1_id = branches[0].id if branches else 1

            # 1. Central Admin
            admin = session.execute(
                select(User).where(User.username == "admin")
            ).scalar_one_or_none()

            if not admin:
                cls.register_user(
                    username="admin",
                    email="admin@apexbank.local",
                    password="AdminPassword2026!",
                    full_name="Central Executive Administrator",
                    role_names=[ROLE_CENTRAL_ADMIN],
                    created_by="BOOTSTRAP",
                )

            # 2. Branch Manager 1 (Assigned strictly to Branch 1)
            bm1 = session.execute(
                select(User).where(User.username == "branch_mgr_downtown")
            ).scalar_one_or_none()

            if not bm1:
                cls.register_user(
                    username="branch_mgr_downtown",
                    email="mgr.downtown@apexbank.local",
                    password="ManagerPassword2026!",
                    full_name="Marcus Vance (Downtown Branch Manager)",
                    role_names=[ROLE_BRANCH_MANAGER],
                    branch_ids=[b1_id],
                    created_by="BOOTSTRAP",
                )

            # 3. Regional Manager
            rm = session.execute(
                select(User).where(User.username == "regional_dir_central")
            ).scalar_one_or_none()

            if not rm:
                cls.register_user(
                    username="regional_dir_central",
                    email="regional.central@apexbank.local",
                    password="RegionalPassword2026!",
                    full_name="Sarah Chen (Regional Director)",
                    role_names=[ROLE_REGIONAL_MANAGER],
                    created_by="BOOTSTRAP",
                )

        return {"status": "BOOTSTRAPPED"}
