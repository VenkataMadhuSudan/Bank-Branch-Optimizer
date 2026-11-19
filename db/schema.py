"""
Normalized Relational Database Schema for Bank AI Optimizer (SQLAlchemy 2.0).
Provides comprehensive enterprise models for organizations, authentication, branch operations,
employees, forecasting, mathematical optimization, queue simulation, and tamper-evident audit trails.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

# Cross-dialect JSON column type (JSONB on PostgreSQL, JSON on SQLite)
JsonType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Declarative Base class for all database entities."""
    pass


# =========================================================================
# 1. ORGANIZATION HIERARCHY
# =========================================================================

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), default="US", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    regions: Mapped[List["Region"]] = relationship("Region", back_populates="organization", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    region_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="regions")
    branches: Mapped[List["Branch"]] = relationship("Branch", back_populates="region", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cluster: Mapped[str] = mapped_column(String(100), default="Metro Central", nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    total_counters: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    peak_window: Mapped[str] = mapped_column(String(50), default="11:00-14:00", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    region: Mapped["Region"] = relationship("Region", back_populates="branches")
    counters: Mapped[List["Counter"]] = relationship("Counter", back_populates="branch", cascade="all, delete-orphan")
    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="branch")
    operating_hours: Mapped[List["BranchOperatingHour"]] = relationship("BranchOperatingHour", back_populates="branch", cascade="all, delete-orphan")
    customer_arrivals: Mapped[List["CustomerArrival"]] = relationship("CustomerArrival", back_populates="branch")
    demand_forecasts: Mapped[List["DemandForecast"]] = relationship("DemandForecast", back_populates="branch")
    optimization_runs: Mapped[List["OptimizationRun"]] = relationship("OptimizationRun", back_populates="branch")
    alerts: Mapped[List["SystemAlert"]] = relationship("SystemAlert", back_populates="branch")


class BranchOperatingHour(Base):
    __tablename__ = "branch_operating_hours"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    open_time: Mapped[str] = mapped_column(String(10), default="09:00", nullable=False)
    close_time: Mapped[str] = mapped_column(String(10), default="17:00", nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="operating_hours")
    __table_args__ = (UniqueConstraint("branch_id", "day_of_week", name="uq_branch_day_hours"),)


# =========================================================================
# 2. AUTHENTICATION & ACCESS CONTROL (RBAC)
# =========================================================================

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    users: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="users")
    user_roles: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    branch_permissions: Mapped[List["UserBranchPermission"]] = relationship("UserBranchPermission", back_populates="user", cascade="all, delete-orphan")
    login_attempts: Mapped[List["LoginAttempt"]] = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)


class UserBranchPermission(Base):
    __tablename__ = "user_branch_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_optimize: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_manage_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_import_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="branch_permissions")
    branch: Mapped["Branch"] = relationship("Branch")
    __table_args__ = (UniqueConstraint("user_id", "branch_id", name="uq_user_branch"),)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username_attempted: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempt_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="login_attempts")


# =========================================================================
# 3. EMPLOYEE & SKILL MANAGEMENT
# =========================================================================

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_skill: Mapped[str] = mapped_column(String(100), nullable=False)
    secondary_skills: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Semicolon separated
    efficiency_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    counter_speed_rating: Mapped[float] = mapped_column(Float, default=4.5, nullable=False)
    hourly_rate_usd: Mapped[float] = mapped_column(Float, default=28.0, nullable=False)
    max_weekly_hours: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="employees")
    skills: Mapped[List["EmployeeSkill"]] = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    shifts: Mapped[List["EmployeeShift"]] = relationship("EmployeeShift", back_populates="employee", cascade="all, delete-orphan")
    availabilities: Mapped[List["EmployeeAvailability"]] = relationship("EmployeeAvailability", back_populates="employee", cascade="all, delete-orphan")
    breaks: Mapped[List["EmployeeBreak"]] = relationship("EmployeeBreak", back_populates="employee", cascade="all, delete-orphan")


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    service_category: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency_level: Mapped[str] = mapped_column(String(20), default="Competent", nullable=False)  # Novice, Competent, Expert
    is_certified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="skills")
    __table_args__ = (UniqueConstraint("employee_id", "service_category", name="uq_emp_service_skill"),)


class EmployeeCertification(Base):
    __tablename__ = "employee_certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cert_name: Mapped[str] = mapped_column(String(150), nullable=False)
    issuing_body: Mapped[str] = mapped_column(String(150), nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    employee: Mapped["Employee"] = relationship("Employee")


class EmployeeShift(Base):
    __tablename__ = "employee_shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(String(10), default="09:00", nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), default="17:00", nullable=False)
    shift_type: Mapped[str] = mapped_column(String(50), default="Regular", nullable=False)  # Regular, Morning, Evening, Overtime
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="shifts")


class EmployeeAvailability(Base):
    __tablename__ = "employee_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date_available: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reason_unavailable: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Sick, Vacation, Training

    employee: Mapped["Employee"] = relationship("Employee", back_populates="availabilities")


class EmployeeBreak(Base):
    __tablename__ = "employee_breaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    break_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    duration_mins: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    break_type: Mapped[str] = mapped_column(String(50), default="Lunch", nullable=False)  # Lunch, Rest
    is_taken: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="breaks")


# =========================================================================
# 4. COUNTERS, SERVICES & QUEUE TELEMETRY
# =========================================================================

class Counter(Base):
    __tablename__ = "counters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    counter_code: Mapped[str] = mapped_column(String(50), nullable=False)
    counter_type: Mapped[str] = mapped_column(String(50), default="Universal Teller", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="counters")
    __table_args__ = (UniqueConstraint("branch_id", "counter_code", name="uq_branch_counter"),)


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sla_wait_mins: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    avg_service_mins: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    digital_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    digital_channel: Mapped[str] = mapped_column(String(150), default="Mobile App", nullable=False)
    digital_deflection_difficulty: Mapped[str] = mapped_column(String(50), default="Medium", nullable=False)


class CustomerArrival(Base):
    __tablename__ = "customer_arrivals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    token_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    customer_segment: Mapped[str] = mapped_column(String(50), default="Regular", nullable=False)
    service_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    arrival_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    service_start_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    service_end_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    wait_time_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    service_duration_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    counter_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    staff_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    digital_deflectable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_abandoned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="customer_arrivals")


class ServiceRecord(Base):
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    arrival_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer_arrivals.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_segment: Mapped[str] = mapped_column(String(50), default="Regular", nullable=False)
    service_category: Mapped[str] = mapped_column(String(100), nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", nullable=False)  # SCHEDULED, COMPLETED, NO_SHOW, CANCELLED


# =========================================================================
# 5. CUSTOMER INTELLIGENCE & SENTIMENT
# =========================================================================

class CustomerFeedback(Base):
    __tablename__ = "customer_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    token_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    service_category: Mapped[str] = mapped_column(String(100), nullable=False)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    sentiment_result: Mapped[Optional["SentimentResult"]] = relationship("SentimentResult", back_populates="feedback", uselist=False, cascade="all, delete-orphan")


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer_feedback.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)  # Positive, Neutral, Negative
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    detected_topics: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mentioned_counter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    feedback: Mapped["CustomerFeedback"] = relationship("CustomerFeedback", back_populates="sentiment_result")


class DigitalDeflectionEvent(Base):
    __tablename__ = "digital_deflection_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    service_category: Mapped[str] = mapped_column(String(100), nullable=False)
    target_channel: Mapped[str] = mapped_column(String(100), nullable=False)
    time_saved_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_cost_saved_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    deflected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)


# =========================================================================
# 6. ML PREDICTION & FORECASTING
# =========================================================================

class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    arrival_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_arrivals: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound_p10: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    upper_bound_p90: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    surge_risk: Mapped[str] = mapped_column(String(50), default="Normal", nullable=False)
    model_version_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="demand_forecasts")


class WaitTimePrediction(Base):
    __tablename__ = "wait_time_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    service_category: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_segment: Mapped[str] = mapped_column(String(50), default="Regular", nullable=False)
    predicted_wait_mins: Mapped[float] = mapped_column(Float, nullable=False)
    sla_breach_probability: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_interval_low: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_interval_high: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    evaluations: Mapped[List["ModelEvaluation"]] = relationship("ModelEvaluation", back_populates="model_version", cascade="all, delete-orphan")


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    r2_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", back_populates="evaluations")


# =========================================================================
# 7. MATHEMATICAL OPTIMIZATION
# =========================================================================

class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    solver_name: Mapped[str] = mapped_column(String(50), default="OR-Tools CP-SAT", nullable=False)
    solver_status: Mapped[str] = mapped_column(String(50), nullable=False)  # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN
    solve_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    objective_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    allocated_counters: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unassigned_buffer_staff: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    branch_utilization_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    config_parameters: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="optimization_runs")
    staff_allocations: Mapped[List["StaffAllocation"]] = relationship("StaffAllocation", back_populates="optimization_run", cascade="all, delete-orphan")
    break_schedules: Mapped[List["BreakSchedule"]] = relationship("BreakSchedule", back_populates="optimization_run", cascade="all, delete-orphan")


class StaffAllocation(Base):
    __tablename__ = "staff_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    optimization_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    counter_code: Mapped[str] = mapped_column(String(50), nullable=False)
    staff_code: Mapped[str] = mapped_column(String(50), nullable=False)
    staff_name: Mapped[str] = mapped_column(String(150), nullable=False)
    assigned_service: Mapped[str] = mapped_column(String(100), nullable=False)
    match_type: Mapped[str] = mapped_column(String(50), default="Primary Skill Match", nullable=False)
    efficiency_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    speed_rating: Mapped[float] = mapped_column(Float, default=4.5, nullable=False)
    fatigue_risk: Mapped[str] = mapped_column(String(50), default="Low", nullable=False)

    optimization_run: Mapped["OptimizationRun"] = relationship("OptimizationRun", back_populates="staff_allocations")


class BreakSchedule(Base):
    __tablename__ = "break_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    optimization_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    counter_code: Mapped[str] = mapped_column(String(50), nullable=False)
    staff_name: Mapped[str] = mapped_column(String(150), nullable=False)
    assigned_service: Mapped[str] = mapped_column(String(100), nullable=False)
    allocated_break_window: Mapped[str] = mapped_column(String(50), nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(100), default="Staggered Active", nullable=False)

    optimization_run: Mapped["OptimizationRun"] = relationship("OptimizationRun", back_populates="break_schedules")


class OptimizationConstraint(Base):
    __tablename__ = "optimization_constraints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    constraint_name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_hard_constraint: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class OptimizationMetric(Base):
    __tablename__ = "optimization_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    optimization_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)


# =========================================================================
# 8. QUEUE SIMULATION
# =========================================================================

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    scenario_name: Mapped[str] = mapped_column(String(150), default="Base Operations", nullable=False)
    base_hourly_arrivals: Mapped[int] = mapped_column(Integer, default=40, nullable=False)
    active_counters: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    avg_service_mins: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    digital_deflection_pct: Mapped[float] = mapped_column(Float, default=20.0, nullable=False)
    sla_threshold_mins: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    total_customers_served: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_wait_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    p90_wait_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_wait_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sla_breach_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_breach_rate_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    abandonment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    random_seed: Mapped[Optional[int]] = mapped_column(Integer, default=42, nullable=True)

    results: Mapped[List["SimulationResult"]] = relationship("SimulationResult", back_populates="simulation_run", cascade="all, delete-orphan")


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    arrival_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    service_time_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    counter_delta: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deflection_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_preconfigured: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    simulation_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    hour_bucket: Mapped[int] = mapped_column(Integer, nullable=False)
    customers_served: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_wait_mins: Mapped[float] = mapped_column(Float, nullable=False)
    sla_breaches: Mapped[int] = mapped_column(Integer, nullable=False)

    simulation_run: Mapped["SimulationRun"] = relationship("SimulationRun", back_populates="results")


# =========================================================================
# 9. MANAGEMENT, ALERTS, DECISIONS & TAMPER-EVIDENT AUDIT LOGS
# =========================================================================

class SystemAlert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SURGE, WAIT_TIME, STAFF_SHORTAGE, SLA_BREACH
    severity: Mapped[str] = mapped_column(String(20), default="WARNING", nullable=False)  # INFO, WARNING, CRITICAL
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="alerts")


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_username: Mapped[str] = mapped_column(String(100), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)  # REALLOCATE_STAFF, OPEN_COUNTER, STAGGER_BREAK
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_data: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    action_taken: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)


class AuditLog(Base):
    """
    Cryptographically Hash-Chained Tamper-Evident Audit Ledger.
    Each record binds to the previous record's SHA-256 hash.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actor_username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)


# =========================================================================
# 10. DATASET INGESTION & VALIDATION
# =========================================================================

class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(100), nullable=False)  # QUEUE_LOGS, STAFF_ROSTER, FEEDBACK, APPOINTMENTS
    source_type: Mapped[str] = mapped_column(String(50), default="UPLOAD", nullable=False)  # UPLOAD, SYNTHETIC, SIMULATION
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, VALIDATED, IMPORTED, REJECTED
    imported_by: Mapped[str] = mapped_column(String(100), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    errors: Mapped[List["DatasetImportError"]] = relationship("DatasetImportError", back_populates="import_record", cascade="all, delete-orphan")
    validation_reports: Mapped[List["DatasetValidationReport"]] = relationship("DatasetValidationReport", back_populates="import_record", cascade="all, delete-orphan")


class DatasetImportError(Base):
    __tablename__ = "dataset_import_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_id: Mapped[int] = mapped_column(Integer, ForeignKey("dataset_imports.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(String(255), nullable=False)

    import_record: Mapped["DatasetImport"] = relationship("DatasetImport", back_populates="errors")


class DatasetValidationReport(Base):
    __tablename__ = "dataset_validation_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_id: Mapped[int] = mapped_column(Integer, ForeignKey("dataset_imports.id", ondelete="CASCADE"), nullable=False, index=True)
    report_json: Mapped[dict] = mapped_column(JsonType, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    import_record: Mapped["DatasetImport"] = relationship("DatasetImport", back_populates="validation_reports")
