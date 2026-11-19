"""
FastAPI Security & Authorization Dependencies.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Header, status

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.auth_service import AuthService


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates Bearer token from Authorization header and extracts user payload.
    Provides graceful optional fallback for public endpoints if authorization is not sent.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = AuthService.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or token invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_permission(permission: str):
    """Factory dependency verifying that the current user possesses required RBAC permission."""
    def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        perms = user.get("permissions", [])
        roles = user.get("roles", [])
        if "CENTRAL_ADMIN" in roles:
            return user
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required capability: '{permission}'",
            )
        return user
    return dependency


def require_branch_access(branch_id: int, capability: str = "can_view"):
    """Factory dependency verifying that the user has explicit authorization for this branch."""
    def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        has_access = AuthService.check_branch_access(user, branch_id=branch_id, required_capability=capability)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for Branch ID {branch_id}. Branch isolation policy enforced.",
            )
        return user
    return dependency
