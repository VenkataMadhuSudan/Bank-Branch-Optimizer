"""
Unit Tests for Operational Intelligence, Explainability, NLP Sentiment, and Digital Deflection.
"""
import pytest
from src.optimization.explainability import BranchExplainabilityEngine
from src.models.nlp_sentiment import FeedbackSentimentAnalyzer
from src.models.digital_deflection import DigitalDeflectionEngine


def test_explainability_normalized_impact_percentages():
    """Verifies that root-cause driver impact percentages are properly normalized to 100%."""
    engine = BranchExplainabilityEngine()
    res = engine.explain_branch_congestion(
        predicted_arrivals=42,
        active_counters=4,
        avg_wait=22.5,
        sla_target=15.0,
        is_month_end=True,
        top_service="Cash Deposit/Withdrawal",
        digital_deflection_rate=0.15,
        unassigned_staff=1
    )

    assert res["status_flag"] in ("CRITICAL BOTTLENECK", "MODERATE PRESSURE")
    assert len(res["root_cause_drivers"]) > 0

    total_pct = sum(d["impact_pct"] for d in res["root_cause_drivers"])
    assert round(total_pct, 0) == 100.0, f"Driver percentages must sum to 100%, got {total_pct}"
    assert "recommended_actions" in res
    assert len(res["recommended_actions"]) > 0
    assert res["is_mathematically_grounded"] is True


def test_sentiment_polarity_and_topic_detection():
    """Verifies lexical sentiment scoring and topic detection."""
    analyzer = FeedbackSentimentAnalyzer()

    # Positive review
    pos_res = analyzer.analyze_sentiment("Teller was very helpful, efficient and friendly!")
    assert pos_res["sentiment"] == "Positive"
    assert pos_res["sentiment_score"] > 0.0

    # Negative complaint about wait time and counter shortage
    neg_res = analyzer.analyze_sentiment("Waited for 45 minutes in a long queue. Counter 2 was closed!")
    assert neg_res["sentiment"] == "Negative"
    assert neg_res["sentiment_score"] < 0.0
    assert "Excessive Wait Time / Queue Bottleneck" in neg_res["topics"]
    assert neg_res["mentioned_counter"] == "C_02"
    assert neg_res["is_actionable"] is True


def test_sentiment_batch_aggregation():
    """Verifies batch aggregation across multiple customer reviews."""
    analyzer = FeedbackSentimentAnalyzer()
    batch = [
        {"feedback_text": "Great service at counter 1, very fast!", "rating": 5},
        {"feedback_text": "Awful delay, horrible crowd.", "rating": 1},
        {"feedback_text": "Standard bank visit.", "rating": 3}
    ]
    summary = analyzer.aggregate_feedback_batch(batch)
    assert summary["total_reviews"] == 3
    assert summary["positive_pct"] > 0.0
    assert summary["negative_pct"] > 0.0
    assert summary["actionable_alerts_count"] >= 1


def test_digital_deflection_eligibility_and_segment_factor():
    """Verifies digital deflection eligibility and segment adoption factors."""
    deflection = DigitalDeflectionEngine()

    # Passbook Printing -> Deflectable to lobby kiosk
    passbook = deflection.evaluate_request("Passbook / Statement Printing", customer_segment="Regular")
    assert passbook["is_deflectable"] is True
    assert "Passbook" in passbook["target_channel"]
    assert passbook["time_saved_minutes"] > 0.0

    # Loan & Mortgage -> In-person verification required
    loan = deflection.evaluate_request("Loan & Mortgage Advisory", customer_segment="Regular")
    assert loan["is_deflectable"] is False

    # Senior Citizen adoption factor should be lower than regular
    senior_passbook = deflection.evaluate_request("Passbook / Statement Printing", customer_segment="Senior Citizen")
    assert senior_passbook["segment_adoption_factor"] < passbook["segment_adoption_factor"]


def test_branch_deflection_kpi_computation():
    """Verifies branch-wide DDI, hours saved, and cost calculation."""
    deflection = DigitalDeflectionEngine()
    sample_tokens = [
        {"service_category": "Passbook / Statement Printing", "digital_deflectable": 1, "service_duration_minutes": 4.0},
        {"service_category": "Cash Deposit/Withdrawal", "digital_deflectable": 1, "service_duration_minutes": 6.0},
        {"service_category": "Loan & Mortgage Advisory", "digital_deflectable": 0, "service_duration_minutes": 25.0},
    ]
    kpis = deflection.compute_branch_deflection_metrics(sample_tokens)
    assert kpis["total_visits"] == 3
    assert kpis["deflectable_visits"] == 2
    assert round(kpis["deflection_rate_pct"], 1) == 66.7
    assert kpis["hours_saved"] > 0.0
    assert kpis["estimated_cost_savings_usd"] == round(kpis["hours_saved"] * 28.0, 2)
    assert kpis["ddi_score"] > 0.0
