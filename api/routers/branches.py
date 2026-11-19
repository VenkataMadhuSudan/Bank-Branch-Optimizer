"""
Branch Network & Organization Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from api.schemas import BranchListResponse
from src.config import BRANCH_NETWORK, CUSTOMER_SEGMENTS, SERVICE_CATEGORIES
from db.connection import get_db_session
from db.schema import Branch

router = APIRouter(prefix="/api/branches", tags=["Branch Operations"])


@router.get("", response_model=BranchListResponse)
def get_branches():
    """Returns network metadata, service categories, customer segments, and SLAs."""
    branches_list = BRANCH_NETWORK
    # Try querying live database branches if available
    try:
        with get_db_session() as session:
            db_branches = session.execute(select(Branch)).scalars().all()
            if db_branches:
                branches_list = [
                    {
                        "branch_id": b.branch_code,
                        "name": b.name,
                        "cluster": b.cluster,
                        "total_counters": b.total_counters,
                        "peak_window": b.peak_window,
                        "is_active": b.is_active,
                    }
                    for b in db_branches
                ]
    except Exception:
        pass  # Fall back gracefully to configuration metadata

    return {
        "branches": branches_list,
        "services": list(SERVICE_CATEGORIES.keys()),
        "segments": list(CUSTOMER_SEGMENTS.keys()),
        "service_metadata": SERVICE_CATEGORIES,
    }
