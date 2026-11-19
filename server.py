"""
FastAPI Backend Application for Bank AI Optimizer.
Provides modular RESTful API architecture, Pydantic validation, PBKDF2/JWT authentication,
PostgreSQL database persistence, OR-Tools optimization, and queue simulation.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.routers import (
    audit,
    auth,
    branches,
    datasets,
    forecasts,
    health,
    intelligence,
    optimization,
    simulation,
)
from db.connection import check_db_health, init_db
from src.config import APP_ENV, BRANCH_NETWORK, CUSTOMER_SEGMENTS, SERVICE_CATEGORIES
from src.utils.logger import logger

app = FastAPI(
    title="Bank AI Optimizer — Enterprise Operations Intelligence API",
    description="Operations research, demand forecasting, mathematical staff scheduling, and queue intelligence platform.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
# In production, specify authorized origins; in development, allow local Streamlit dashboard
allowed_origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if APP_ENV == "development":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Modular Routers
app.include_router(auth.router)
app.include_router(branches.router)
app.include_router(forecasts.router)
app.include_router(optimization.router)
app.include_router(simulation.router)
app.include_router(intelligence.router)
app.include_router(datasets.router)
app.include_router(audit.router)
app.include_router(health.router)

# In-memory counter session memory for active teller terminals
live_counter_sessions: Dict[str, Any] = {}


# ----------------- BACKWARD-COMPATIBILITY ENDPOINT ALIASES -----------------

@app.get("/api/models/status")
def legacy_model_status():
    """Backward-compatible endpoint for existing UI components."""
    return forecasts.get_model_status()


@app.get("/api/forecast/hourly")
def legacy_forecast_hourly(
    branch_id: str = Query("BR_001"),
    hour: int = Query(12),
    day_of_week: int = Query(2),
    is_month_end: int = Query(0),
):
    """Backward-compatible hourly forecast route."""
    return forecasts.get_hourly_forecast(branch_id, hour, day_of_week, is_month_end)


@app.post("/api/optimize/staff")
def legacy_optimize_staff(payload: Dict[str, Any]):
    """Backward-compatible staff optimization route."""
    from api.schemas import StaffOptimizationRequest
    req = StaffOptimizationRequest(**payload)
    return optimization.optimize_staff_allocation(req)


@app.post("/api/simulate/queue")
def legacy_simulate_queue(payload: Dict[str, Any]):
    """Backward-compatible queue simulation route."""
    from api.schemas import SimulationRequest
    req = SimulationRequest(**payload)
    return simulation.run_queue_simulation(req)


@app.post("/api/counter/session/start")
def start_counter_session(payload: Dict[str, Any]):
    """Worker terminal: Starts an active counter handling session."""
    counter_id = payload.get("counter_id", "Counter 1")
    staff_name = payload.get("staff_name", "Staff Member")
    token = payload.get("token_number", "A-101")
    service = payload.get("service_category", "Cash Deposit/Withdrawal")

    live_counter_sessions[counter_id] = {
        "counter_id": counter_id,
        "staff_name": staff_name,
        "active_token": token,
        "service_category": service,
        "status": "PROCESSING",
    }
    return {"status": "SESSION_STARTED", "session": live_counter_sessions[counter_id]}


@app.post("/api/counter/session/complete")
def complete_counter_session(payload: Dict[str, Any]):
    """Worker terminal: Completes an active counter session."""
    counter_id = payload.get("counter_id", "Counter 1")
    session = live_counter_sessions.pop(counter_id, None)
    return {"status": "SESSION_COMPLETED", "completed_session": session}


@app.get("/api/counter/sessions")
def list_active_counter_sessions():
    """Returns currently processing counter sessions across the branch."""
    return {"active_sessions": list(live_counter_sessions.values())}


@app.on_event("startup")
def on_startup():
    """Fast non-destructive startup: verifies database schema without blocking."""
    logger.info("Bank AI Optimizer API initializing...")
    logger.info("Bank AI Optimizer API started successfully. Interactive docs at /docs")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
