"""
Authentication & User Profile Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from api.schemas import LoginRequest, TokenResponse, UserProfileResponse
from api.dependencies import get_current_user
from services.auth_service import AuthService
from services.audit_service import AuditService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request):
    """Authenticates user with PBKDF2 verification, lockout protection, and issues JWT access token."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    res = AuthService.authenticate_user(
        username=req.username,
        password=req.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=res["error"],
        )

    # Log successful login to cryptographic audit ledger
    AuditService.log_action(
        actor_username=res["user"]["username"],
        action="USER_LOGIN",
        resource_type="AUTH",
        resource_id=str(res["user"]["user_id"]),
        details={"roles": res["user"]["roles"]},
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=res["token"],
        token_type="bearer",
        user=res["user"],
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user=Depends(get_current_user)):
    """Returns the verified profile and branch permissions of the currently authenticated user."""
    return user
