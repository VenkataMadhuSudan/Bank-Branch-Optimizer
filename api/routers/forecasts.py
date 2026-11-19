"""
Demand Forecasting & ML Model Governance Endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from api.schemas import HourlyForecastRequest, HourlyForecastResponse, DailyForecastRequest
from src.models.demand_forecaster import DemandForecaster
from src.models.wait_time_model import WaitTimePredictor
from src.data_pipeline import BankingDataPipeline
from src.utils.logger import logger

router = APIRouter(prefix="/api/forecasts", tags=["Machine Learning Forecasting"])

# Lazy singleton instances
_FORECASTER: DemandForecaster = DemandForecaster()
_WAIT_PREDICTOR: WaitTimePredictor = WaitTimePredictor()


def get_forecaster() -> DemandForecaster:
    global _FORECASTER
    if not _FORECASTER.is_trained:
        try:
            pipeline = BankingDataPipeline()
            _, hourly_metrics, _, _, _, _ = pipeline.run_pipeline()
            _FORECASTER.train(hourly_metrics)
        except Exception as exc:
            logger.warning(f"Forecaster automated lazy train failed, using heuristic: {exc}")
    return _FORECASTER


def get_wait_predictor() -> WaitTimePredictor:
    global _WAIT_PREDICTOR
    if not _WAIT_PREDICTOR.is_trained:
        try:
            pipeline = BankingDataPipeline()
            clean_tokens, _, _, _, _, _ = pipeline.run_pipeline()
            _WAIT_PREDICTOR.train(clean_tokens)
        except Exception as exc:
            logger.warning(f"Wait predictor automated lazy train failed, using heuristic: {exc}")
    return _WAIT_PREDICTOR


@router.get("/hourly", response_model=HourlyForecastResponse)
def get_hourly_forecast(
    branch_id: str = Query("BR_001"),
    hour: int = Query(12, ge=9, le=17),
    day_of_week: int = Query(2, ge=0, le=6),
    is_month_end: int = Query(0, ge=0, le=1),
):
    """Predicts hourly customer arrivals with 90% conformal prediction interval and surge risk classification."""
    forecaster = get_forecaster()
    return forecaster.predict_hour(
        branch_id=branch_id,
        hour=hour,
        day_of_week=day_of_week,
        is_month_end=is_month_end,
    )


@router.get("/daily")
def get_daily_forecast(
    branch_id: str = Query("BR_001"),
    day_of_week: int = Query(2, ge=0, le=6),
    is_month_end: int = Query(0, ge=0, le=1),
):
    """Generates 9-hour operational progression forecast (09:00 - 17:00) with conformal bands."""
    forecaster = get_forecaster()
    today_str = datetime.now().strftime("%Y-%m-%d")
    return {
        "branch_id": branch_id,
        "date": today_str,
        "forecasts": forecaster.forecast_day(
            branch_id=branch_id,
            date_str=today_str,
            day_of_week=day_of_week,
            is_month_end=is_month_end,
        ),
    }


@router.post("/train")
def train_forecasting_models():
    """Explicitly trains all forecasting and wait-time models on processed queue telemetry."""
    pipeline = BankingDataPipeline()
    clean_tokens, hourly_metrics, _, _, _, _ = pipeline.run_pipeline()

    f_metrics = _FORECASTER.train(hourly_metrics)
    w_metrics = _WAIT_PREDICTOR.train(clean_tokens)

    return {
        "status": "TRAINED",
        "timestamp": datetime.now().isoformat(),
        "demand_forecast_metrics": f_metrics,
        "wait_time_metrics": w_metrics,
    }


@router.get("/status")
def get_model_status():
    """Returns training metrics, selected algorithms, and feature attributions."""
    forecaster = get_forecaster()
    wait_predictor = get_wait_predictor()
    return {
        "demand_forecaster": forecaster.metrics,
        "wait_predictor": wait_predictor.metrics,
    }

