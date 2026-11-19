"""
Pydantic v2 Request & Response Data Schemas for Bank AI Optimizer API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr


# ----------------- AUTHENTICATION SCHEMAS -----------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    roles: List[str]
    permissions: List[str]
    branch_permissions: List[Dict[str, Any]]


# ----------------- BRANCH & COUNTER SCHEMAS -----------------

class BranchSummary(BaseModel):
    branch_id: str
    name: str
    cluster: str
    total_counters: int
    peak_window: str

class BranchListResponse(BaseModel):
    branches: List[Dict[str, Any]]
    services: List[str]
    segments: List[str]
    service_metadata: Dict[str, Any]


# ----------------- FORECASTING SCHEMAS -----------------

class HourlyForecastRequest(BaseModel):
    branch_id: str
    hour: int = Field(12, ge=9, le=17)
    day_of_week: int = Field(2, ge=0, le=6)
    is_month_end: int = Field(0, ge=0, le=1)

class DailyForecastRequest(BaseModel):
    branch_id: str
    date_str: Optional[str] = None
    day_of_week: int = Field(2, ge=0, le=6)
    is_month_end: int = Field(0, ge=0, le=1)

class HourlyForecastResponse(BaseModel):
    branch_id: str
    arrival_hour: int
    predicted_arrivals: float
    lower_bound_p10: float
    upper_bound_p90: float
    conformal_confidence_pct: float
    surge_risk: str
    service_demands: Dict[str, int]


# ----------------- OPTIMIZATION SCHEMAS -----------------

class StaffOptimizationRequest(BaseModel):
    active_staff: List[Dict[str, Any]]
    service_demands: Dict[str, int]
    available_counters: int = Field(..., ge=1, le=50)
    break_slots: Optional[List[str]] = None

class StochasticOptimizationRequest(BaseModel):
    active_staff: List[Dict[str, Any]]
    available_counters: int = Field(..., ge=1, le=50)
    base_demand: int = Field(35, ge=1)
    conformal_halfwidth: float = Field(6.0, ge=0.0)

class ScenarioStressRequest(BaseModel):
    scenario_key: str
    active_staff: List[Dict[str, Any]]
    available_counters: int = Field(..., ge=1)
    base_hourly_arrivals: int = Field(35, ge=1)


# ----------------- SIMULATION SCHEMAS -----------------

class SimulationRequest(BaseModel):
    base_hourly_arrivals: int = Field(40, ge=1, le=300)
    active_counters: int = Field(4, ge=1, le=30)
    avg_service_mins: float = Field(8.0, ge=1.0, le=60.0)
    digital_deflection_pct: float = Field(20.0, ge=0.0, le=95.0)
    sla_threshold_mins: float = Field(15.0, ge=1.0, le=120.0)
    duration_hours: int = Field(6, ge=1, le=12)
    replications: int = Field(3, ge=1, le=20)
    random_seed: Optional[int] = 42


# ----------------- INTELLIGENCE SCHEMAS -----------------

class SentimentAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)

class DigitalDeflectionRequest(BaseModel):
    service_category: str
    customer_segment: str = "Regular"
    customer_query: Optional[str] = ""

class ExplainabilityRequest(BaseModel):
    predicted_arrivals: int = Field(..., ge=0)
    active_counters: int = Field(..., ge=1)
    avg_wait: float = Field(..., ge=0.0)
    sla_target: float = Field(15.0, ge=1.0)
    is_month_end: bool = False
    top_service: str = "Cash Deposit/Withdrawal"
    digital_deflection_rate: float = Field(0.25, ge=0.0, le=1.0)
    unassigned_staff: int = 0


# ----------------- AUDIT & HEALTH SCHEMAS -----------------

class AuditVerificationResponse(BaseModel):
    is_valid: bool
    total_records: int
    tampered_records: List[Dict[str, Any]]
    message: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    app_env: str
    database: Dict[str, Any]

