"""
Cryptographic Audit Ledger & Tamper Verification Endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from api.dependencies import get_current_user, require_permission
from api.schemas import AuditVerificationResponse
from db.connection import get_db_session
from db.schema import AuditLog
from services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["Security & Audit"])


@router.get("/verify", response_model=AuditVerificationResponse)
def verify_audit_ledger_integrity(user=Depends(require_permission("audit.view"))):
    """Scans entire cryptographic SHA-256 forward hash chain from genesis to prove zero tamper history."""
    return AuditService.verify_ledger_integrity()


@router.get("/logs")
def get_recent_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    user=Depends(require_permission("audit.view")),
):
    """Returns recent cryptographic audit entries."""
    with get_db_session() as session:
        records = session.execute(
            select(AuditLog).order_by(desc(AuditLog.id)).limit(limit)
        ).scalars().all()

        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "actor_username": r.actor_username,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "details": r.details,
                "prev_hash_short": r.prev_hash[:16] + "...",
                "record_hash_short": r.record_hash[:16] + "...",
                "ip_address": r.ip_address,
            }
            for r in records
        ]

