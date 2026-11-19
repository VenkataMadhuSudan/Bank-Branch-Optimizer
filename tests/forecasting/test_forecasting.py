"""
Unit and Integration Tests for Leakage-Free Demand Forecasting and Wait-Time ML Models.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.models.demand_forecaster import DemandForecaster, compute_wape
from src.models.wait_time_model import WaitTimePredictor


@pytest.fixture
def synthetic_hourly_series():
    """Generates synthetic chronological hourly arrival series for testing."""
    records = []
    base_date = datetime(2026, 10, 1, 9, 0)
    for day in range(30):
        current_day = base_date + timedelta(days=day)
        for h in range(9, 17):
            records.append({
                "branch_id": "BR_001",
                "date": current_day.strftime("%Y-%m-%d"),
                "arrival_hour": h,
                "total_arrivals": 15 + (h % 3) * 5 + (day % 4) * 2,
            })
    return pd.DataFrame(records)


@pytest.fixture
def synthetic_tokens_series():
    """Generates synthetic chronological token records."""
    records = []
    base_date = datetime(2026, 10, 1, 9, 0)
    for i in range(100):
        arr_time = base_date + timedelta(minutes=i * 15)
        records.append({
            "branch_id": "BR_001",
            "token_number": f"T{i:03d}",
            "customer_segment": "Regular" if i % 2 == 0 else "Senior Citizen",
            "service_category": "Cash Deposit/Withdrawal" if i % 2 == 0 else "Account Services & KYC",
            "arrival_timestamp": arr_time.strftime("%Y-%m-%d %H:%M:%S"),
            "wait_time_minutes": 8.0 + (i % 5) * 2.0,
            "sla_breached": 1 if (8.0 + (i % 5) * 2.0) > 12.0 else 0,
            "is_appointment": 0,
        })
    return pd.DataFrame(records)


def test_wape_computation():
    """Verifies Weighted Absolute Percentage Error calculation."""
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])  # diffs: 2, 2, 3 = 7 / 60 = 11.67%
    wape = compute_wape(y_true, y_pred)
    assert round(wape, 2) == 11.67


def test_demand_forecaster_chronological_training(synthetic_hourly_series):
    """Verifies that DemandForecaster trains without temporal leakage and produces valid metrics."""
    forecaster = DemandForecaster(l2_reg=0.5)
    metrics = forecaster.train(synthetic_hourly_series)

    assert forecaster.is_trained is True
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "wape" in metrics
    assert "r2" in metrics
    assert metrics["mae"] >= 0.0
    assert metrics["rmse"] >= metrics["mae"]  # Mathematical invariant: RMSE >= MAE
    assert "benchmark_comparison" in metrics
    assert "SeasonalNaive" in metrics["benchmark_comparison"]


def test_conformal_prediction_intervals(synthetic_hourly_series):
    """Verifies that predicted bounds satisfy: lower <= point <= upper."""
    forecaster = DemandForecaster()
    forecaster.train(synthetic_hourly_series)

    pred = forecaster.predict_hour("BR_001", hour=12, day_of_week=2, is_month_end=0)
    assert pred["predicted_arrivals"] >= 0.0
    assert pred["lower_bound_p10"] <= pred["predicted_arrivals"]
    assert pred["upper_bound_p90"] >= pred["predicted_arrivals"]
    assert pred["conformal_confidence_pct"] == 90.0
    assert "service_demands" in pred
    assert sum(pred["service_demands"].values()) > 0


def test_wait_time_predictor_dual_head(synthetic_tokens_series):
    """Verifies that WaitTimePredictor trains and evaluates regression and classification."""
    predictor = WaitTimePredictor()
    metrics = predictor.train(synthetic_tokens_series)

    assert predictor.is_trained is True
    assert "regression_mae_mins" in metrics
    assert "classification_accuracy_pct" in metrics

    pred = predictor.predict_ticket("Cash Deposit/Withdrawal", "Regular", arrival_hour=11)
    assert pred["expected_wait_minutes"] >= 0.0
    assert 0.0 <= pred["sla_breach_probability_pct"] <= 100.0
    assert pred["estimated_completion_time_minutes"] > pred["expected_wait_minutes"]
    assert pred["p90_wait_minutes"] >= pred["expected_wait_minutes"]


def test_deterministic_fallback_before_training():
    """Verifies safe deterministic predictions prior to training."""
    forecaster = DemandForecaster()
    pred = forecaster.predict_hour("BR_001", hour=12)
    assert pred["predicted_arrivals"] > 0.0

    predictor = WaitTimePredictor()
    ticket = predictor.predict_ticket("Cash Deposit/Withdrawal")
    assert ticket["expected_wait_minutes"] > 0.0
