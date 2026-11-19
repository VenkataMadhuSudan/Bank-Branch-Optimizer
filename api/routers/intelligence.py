"""
Operational Intelligence: Explainable AI, Customer Sentiment, and Digital Deflection Endpoints.
"""
from fastapi import APIRouter, Depends
from api.schemas import SentimentAnalysisRequest, DigitalDeflectionRequest, ExplainabilityRequest
from src.models.nlp_sentiment import FeedbackSentimentAnalyzer
from src.models.digital_deflection import DigitalDeflectionEngine
from src.optimization.explainability import BranchExplainabilityEngine

router = APIRouter(prefix="/api/intelligence", tags=["Operational Intelligence"])

_SENTIMENT_ANALYZER = FeedbackSentimentAnalyzer()
_DEFLECTION_ENGINE = DigitalDeflectionEngine()
_EXPLAIN_ENGINE = BranchExplainabilityEngine()


@router.post("/sentiment")
def analyze_customer_feedback(req: SentimentAnalysisRequest):
    """Analyzes customer review text: polarity score, friction topics, staff recognition, and actionability."""
    return _SENTIMENT_ANALYZER.analyze_sentiment(text=req.text, rating=req.rating)


@router.post("/deflection")
def evaluate_digital_deflection(req: DigitalDeflectionRequest):
    """Evaluates request eligibility for self-service deflection across kiosks, ATMs, and mobile banking."""
    return _DEFLECTION_ENGINE.evaluate_request(
        service_category=req.service_category,
        customer_segment=req.customer_segment,
        customer_query=req.customer_query or "",
    )


@router.post("/explain")
def explain_branch_congestion(req: ExplainabilityRequest):
    """Generates mathematically grounded root-cause drivers and manager checklists."""
    return _EXPLAIN_ENGINE.explain_branch_congestion(
        predicted_arrivals=req.predicted_arrivals,
        active_counters=req.active_counters,
        avg_wait=req.avg_wait,
        sla_target=req.sla_target,
        is_month_end=req.is_month_end,
        top_service=req.top_service,
        digital_deflection_rate=req.digital_deflection_rate,
        unassigned_staff=req.unassigned_staff,
    )

