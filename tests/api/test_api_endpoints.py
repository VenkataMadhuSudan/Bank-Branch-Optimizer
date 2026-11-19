"""
Integration Tests for FastAPI Endpoints using TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_health_endpoint():
    """Verifies that /api/health responds with system status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_branches_endpoint():
    """Verifies that /api/branches returns branch network and metadata."""
    response = client.get("/api/branches")
    assert response.status_code == 200
    data = response.json()
    assert "branches" in data
    assert len(data["branches"]) >= 5
    assert "services" in data
    assert "Cash Deposit/Withdrawal" in data["services"]


def test_login_failure_on_invalid_credentials():
    """Verifies that invalid login credentials return 401 Unauthorized."""
    response = client.post(
        "/api/auth/login",
        json={"username": "non_existent_user", "password": "WrongPassword123!"}
    )
    assert response.status_code == 401


def test_forecast_hourly_endpoint():
    """Verifies that /api/forecasts/hourly generates predictions with conformal intervals."""
    response = client.get("/api/forecasts/hourly?branch_id=BR_001&hour=12&day_of_week=2&is_month_end=0")
    assert response.status_code == 200
    data = response.json()
    assert "predicted_arrivals" in data
    assert data["predicted_arrivals"] >= 0.0
    assert "lower_bound_p10" in data
    assert "upper_bound_p90" in data
    assert data["upper_bound_p90"] >= data["lower_bound_p10"]


def test_staff_optimization_endpoint():
    """Verifies that /api/optimization/staff solves staff allocation."""
    payload = {
        "active_staff": [
            {
                "staff_id": "EMP_01",
                "staff_name": "Alice Teller",
                "primary_skill": "Cash Deposit/Withdrawal",
                "efficiency_factor": 1.0,
                "counter_speed_rating": 4.5
            },
            {
                "staff_id": "EMP_02",
                "staff_name": "Bob Advisor",
                "primary_skill": "Account Services & KYC",
                "efficiency_factor": 1.1,
                "counter_speed_rating": 4.8
            }
        ],
        "service_demands": {
            "Cash Deposit/Withdrawal": 10,
            "Account Services & KYC": 5
        },
        "available_counters": 3
    }
    response = client.post("/api/optimization/staff", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "solver_status" in data
    assert "assignments" in data
    assert data["allocated_counters"] <= 3


def test_queue_simulation_endpoint():
    """Verifies that /api/simulation/run executes discrete-event simulation."""
    payload = {
        "base_hourly_arrivals": 30,
        "active_counters": 4,
        "avg_service_mins": 8.0,
        "digital_deflection_pct": 20.0,
        "sla_threshold_mins": 15.0,
        "duration_hours": 4,
        "replications": 2
    }
    response = client.post("/api/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "avg_wait_minutes" in data
    assert "p90_wait_minutes" in data
    assert "sla_breach_rate_pct" in data


def test_sentiment_analysis_endpoint():
    """Verifies that /api/intelligence/sentiment scores customer feedback."""
    payload = {"text": "Very quick and courteous teller at counter 1!", "rating": 5}
    response = client.post("/api/intelligence/sentiment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment"] == "Positive"
    assert data["sentiment_score"] > 0.0


def test_digital_deflection_endpoint():
    """Verifies that /api/intelligence/deflection evaluates channel routing."""
    payload = {"service_category": "Passbook / Statement Printing", "customer_segment": "Regular"}
    response = client.post("/api/intelligence/deflection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_deflectable"] is True
    assert "Passbook" in data["target_channel"]


def test_explainability_endpoint():
    """Verifies that /api/intelligence/explain provides root-cause attributions."""
    payload = {
        "predicted_arrivals": 45,
        "active_counters": 4,
        "avg_wait": 24.0,
        "sla_target": 15.0,
        "is_month_end": True,
        "top_service": "Cash Deposit/Withdrawal",
        "digital_deflection_rate": 0.20,
        "unassigned_staff": 1
    }
    response = client.post("/api/intelligence/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "root_cause_drivers" in data
    assert "recommended_actions" in data

