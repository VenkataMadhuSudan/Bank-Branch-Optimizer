"""
Health & Diagnostic Endpoints.
"""
from datetime import datetime
from fastapi import APIRouter
from api.schemas import HealthResponse
from db.connection import check_db_health
from src.config import APP_ENV

router = APIRouter(prefix="/api/health", tags=["Health & Diagnostics"])


@router.get("", response_model=HealthResponse)
def get_system_health():
    """Performs end-to-end system health check including database latency and dialect verification."""
    db_status = check_db_health()
    overall = "HEALTHY" if db_status["status"] == "HEALTHY" else "DEGRADED"

    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "app_env": APP_ENV,
        "database": db_status,
    }
