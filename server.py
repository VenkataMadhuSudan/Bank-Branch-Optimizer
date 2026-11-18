"""
FastAPI Backend Server & Web Cockpit for Intelligent Bank Branch Optimizer.
Provides multi-persona decision intelligence for Branch Managers, Bank Workers (Tellers/Greeters),
and Regional/Executive Bank Officials.
"""
import uvicorn
from fastapi import FastAPI, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import random
from datetime import datetime

from src.config import BRANCH_NETWORK, SERVICE_CATEGORIES, CUSTOMER_SEGMENTS
from src.data_generator import generate_all_data
from src.data_pipeline import BankingDataPipeline
from src.models.demand_forecaster import DemandForecaster
from src.models.wait_time_model import WaitTimePredictor
from src.models.digital_deflection import DigitalDeflectionEngine
from src.models.nlp_sentiment import FeedbackSentimentAnalyzer
from src.optimization.staff_optimizer import StaffCounterOptimizer
from src.optimization.queue_simulator import BranchQueueSimulator
from src.optimization.explainability import BranchExplainabilityEngine

app = FastAPI(title="Bank Branch Optimizer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- SYSTEM STATE & DATA INGESTION -----------------
pipeline = BankingDataPipeline()
clean_tokens, hourly_metrics, staff_df, branches_df, feedback_df, appointments_df = pipeline.run_pipeline()

# Train ML Models on Raw Data
forecaster = DemandForecaster()
demand_metrics = forecaster.train(hourly_metrics)

wait_predictor = WaitTimePredictor()
wait_metrics = wait_predictor.train(clean_tokens)

deflection_engine = DigitalDeflectionEngine()
sentiment_analyzer = FeedbackSentimentAnalyzer()
staff_optimizer = StaffCounterOptimizer()
queue_simulator = BranchQueueSimulator()
xai_engine = BranchExplainabilityEngine()

# Simulated Live Counter Session Memory for Workers
live_counter_sessions = {}

# ----------------- ENDPOINTS -----------------

@app.get("/api/branches")
def get_branches():
    """Returns network metadata, service categories, and customer segments."""
    return {
        "branches": BRANCH_NETWORK,
        "services": list(SERVICE_CATEGORIES.keys()),
        "segments": list(CUSTOMER_SEGMENTS.keys()),
        "service_metadata": SERVICE_CATEGORIES
    }

@app.get("/api/models/status")
def get_model_status():
    """Returns training performance metrics, data sizes, and feature importances."""
    return {
        "demand_forecaster": forecaster.metrics,
        "wait_time_model": wait_predictor.metrics,
        "total_tokens_trained": len(clean_tokens),
        "total_hourly_windows": len(hourly_metrics),
        "total_feedback_logs": len(feedback_df),
        "last_trained": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/models/retrain")
def retrain_models():
    """Retrains all ML models on raw datasets and updates internal states."""
    global clean_tokens, hourly_metrics, staff_df, branches_df, feedback_df, appointments_df
    clean_tokens, hourly_metrics, staff_df, branches_df, feedback_df, appointments_df = pipeline.run_pipeline()
    f_metrics = forecaster.train(hourly_metrics)
    w_metrics = wait_predictor.train(clean_tokens)
    return {
        "status": "success",
        "message": "All models successfully retrained on latest raw datasets!",
        "demand_metrics": f_metrics,
        "wait_metrics": w_metrics
    }

# -------------------------------------------------------------
# 1. PERSONA: BANK BRANCH MANAGER COCKPIT
# -------------------------------------------------------------
@app.get("/api/dashboard")
def get_dashboard(branch_id: str = "BR_001", hour: int = 12, is_month_end: int = 0):
    branch_meta = next((b for b in BRANCH_NETWORK if b["branch_id"] == branch_id), BRANCH_NETWORK[0])
    
    # 1. Hourly Forecast
    forecast = forecaster.forecast_day(branch_id=branch_id, date_str="2026-09-30", day_of_week=2, is_month_end=is_month_end)
    current_hr_forecast = next((f for f in forecast if f["arrival_hour"] == hour), forecast[3])
    
    # 2. Branch Token Metrics
    b_tokens = clean_tokens.filter(clean_tokens["branch_id"] == branch_id)
    b_tokens_dicts = b_tokens.to_dicts()
    
    # Hour specific tokens
    hr_tokens = [t for t in b_tokens_dicts if t.get("arrival_hour") == hour]
    avg_wait = sum(t["wait_time_minutes"] for t in hr_tokens) / max(1, len(hr_tokens)) if hr_tokens else 14.5
    csat = sum(t["satisfaction_score"] for t in b_tokens_dicts) / max(1, len(b_tokens_dicts))
    
    # 3. Digital Deflection Metrics
    deflect_summary = deflection_engine.compute_branch_deflection_metrics(b_tokens_dicts)
    
    # 4. Explainability (XAI)
    xai_res = xai_engine.explain_branch_congestion(
        predicted_arrivals=current_hr_forecast["predicted_arrivals"],
        active_counters=branch_meta["total_counters"],
        avg_wait=avg_wait,
        sla_target=15.0,
        is_month_end=bool(is_month_end),
        top_service="Cash Deposit/Withdrawal",
        digital_deflection_rate=deflect_summary["deflection_rate_pct"] / 100.0
    )
    
    # 5. Prescriptive Staff Optimization
    staff_for_branch = staff_df.filter(staff_df["branch_id"] == branch_id).to_dicts()
    service_demand_map = {
        "Cash Deposit/Withdrawal": int(current_hr_forecast["cash_kyc_share"] * 0.6),
        "Account Services & KYC": int(current_hr_forecast["cash_kyc_share"] * 0.4),
        "Passbook / Statement Printing": int(current_hr_forecast["quick_services_share"] * 0.5),
        "Card Services & Pin Reset": int(current_hr_forecast["quick_services_share"] * 0.5),
        "Loan & Mortgage Advisory": int(current_hr_forecast["loans_investments_share"] * 0.6),
        "Forex & Trade Finance": max(1, int(current_hr_forecast["loans_investments_share"] * 0.4))
    }
    
    opt_res = staff_optimizer.optimize_allocations(
        active_staff=staff_for_branch,
        service_demands=service_demand_map,
        available_counters=branch_meta["total_counters"]
    )
    
    # 6. Staff Productivity & Fatigue Scorecard
    staff_scorecard = []
    for s in staff_for_branch:
        s_tokens = [t for t in b_tokens_dicts if t.get("staff_id") == s.get("staff_id")]
        t_count = len(s_tokens)
        aht = sum(t.get("service_duration_minutes", 0) for t in s_tokens) / max(1, t_count) if t_count else 7.8
        s_csat = sum(t.get("satisfaction_score", 4.5) for t in s_tokens) / max(1, t_count) if t_count else 4.6
        
        staff_scorecard.append({
            "staff_id": s.get("staff_id"),
            "name": s.get("name", s.get("staff_name", "Staff Member")),
            "primary_skill": s.get("primary_skill"),
            "tokens_served_today": t_count if t_count > 0 else random.randint(18, 36),
            "avg_handling_time_mins": round(aht, 1),
            "csat_score": round(s_csat, 2),
            "speed_rating": s.get("counter_speed_rating", 4.5),
            "fatigue_index": "Normal" if aht < 12.0 else "Elevated (Rotate to Express Desk)"
        })

    # Recent Live Queue Stream
    recent_queue = b_tokens_dicts[-8:] if len(b_tokens_dicts) >= 8 else b_tokens_dicts

    return {
        "branch_meta": branch_meta,
        "kpis": {
            "predicted_arrivals": current_hr_forecast["predicted_arrivals"],
            "ci_lower": current_hr_forecast["ci_lower"],
            "ci_upper": current_hr_forecast["ci_upper"],
            "surge_status": current_hr_forecast["surge_risk"],
            "avg_wait_minutes": round(avg_wait, 1),
            "sla_target_minutes": 15.0,
            "deflection_rate_pct": deflect_summary["deflection_rate_pct"],
            "hours_saved": deflect_summary["hours_saved"],
            "cost_savings_usd": deflect_summary["estimated_cost_savings_usd"],
            "csat_score": round(csat, 2),
            "active_counters": branch_meta["total_counters"],
            "total_staff_on_duty": len(staff_for_branch)
        },
        "forecast": forecast,
        "explainability": xai_res,
        "optimization": opt_res,
        "staff_scorecard": staff_scorecard,
        "recent_queue": recent_queue,
        "model_metrics": forecaster.metrics
    }

# -------------------------------------------------------------
# 2. PERSONA: BANK WORKER / TELLER COUNTER PORTAL
# -------------------------------------------------------------
@app.get("/api/worker/terminal")
def get_worker_terminal(branch_id: str = "BR_001", counter_id: str = "Counter 1"):
    branch_meta = next((b for b in BRANCH_NETWORK if b["branch_id"] == branch_id), BRANCH_NETWORK[0])
    b_staff = staff_df.filter(staff_df["branch_id"] == branch_id).to_dicts()
    
    # Extract staff assigned to this counter
    cnt_num = int(counter_id.replace("Counter ", "").replace("C_", "")) if any(char.isdigit() for char in counter_id) else 1
    staff_idx = (cnt_num - 1) % max(1, len(b_staff))
    staff_member = b_staff[staff_idx] if b_staff else {"name": "Aisha Khan", "primary_skill": "Cash Deposit/Withdrawal", "staff_id": "EMP_101"}
    
    assigned_service = staff_member.get("primary_skill", "Cash Deposit/Withdrawal")
    
    # Create or fetch active customer session
    session_key = f"{branch_id}_{counter_id}"
    if session_key not in live_counter_sessions:
        sample_names = ["Robert Henderson", "Fatima Al-Mansoor", "Vikram Patel", "Elena Rostova", "Marcus Vance", "Mei-Ling Zhou", "Carlos Gomez"]
        segments = list(CUSTOMER_SEGMENTS.keys())
        token_num = random.randint(1040, 1099)
        
        live_counter_sessions[session_key] = {
            "token_id": f"TKN-{token_num}",
            "customer_name": random.choice(sample_names),
            "customer_segment": random.choice(segments),
            "requested_service": assigned_service,
            "wait_time_mins": round(random.uniform(4.5, 14.0), 1),
            "service_started_at": datetime.now().strftime("%H:%M:%S"),
            "is_appointment": random.choice([True, False]),
            "pre_verified_docs": True,
            "deflectable": deflection_engine.evaluate_request(assigned_service)["is_deflectable"]
        }
        
    current_token = live_counter_sessions[session_key]
    deflect_guide = deflection_engine.evaluate_request(assigned_service)
    
    # Next tokens in queue for this desk
    queue_preview = []
    for i in range(1, 6):
        queue_preview.append({
            "token_id": f"TKN-{int(current_token['token_id'].split('-')[1]) + i}",
            "customer_name": f"Customer #{i+1}",
            "segment": random.choice(list(CUSTOMER_SEGMENTS.keys())),
            "service": assigned_service,
            "est_wait": round(float(current_token["wait_time_mins"]) + i * 4.5, 1),
            "priority": "VIP Fast-Track" if i == 2 else "Standard Queue"
        })
        
    # Teller scorecard
    scorecard = {
        "staff_name": staff_member.get("name", "Teller Specialist"),
        "staff_id": staff_member.get("staff_id", "EMP_101"),
        "counter_id": counter_id,
        "assigned_service": assigned_service,
        "tokens_completed_today": random.randint(24, 38),
        "today_avg_handling_mins": 6.8,
        "today_csat": 4.85,
        "shift_schedule": "09:00 - 17:00 (Break: 12:15 - 13:00)",
        "queue_depth_for_service": len(queue_preview) + 1
    }
    
    return {
        "counter_id": counter_id,
        "branch_id": branch_id,
        "branch_name": branch_meta["name"],
        "worker_profile": scorecard,
        "active_customer": current_token,
        "deflection_guidance": deflect_guide,
        "upcoming_queue": queue_preview
    }

@app.post("/api/worker/action")
def perform_worker_action(payload: dict = Body(...)):
    """Handles teller actions: Call Next, Complete Service, or Kiosk Fast-Pass."""
    branch_id = payload.get("branch_id", "BR_001")
    counter_id = payload.get("counter_id", "Counter 1")
    action_type = payload.get("action", "call_next")
    
    session_key = f"{branch_id}_{counter_id}"
    sample_names = ["Daniel Craig", "Sophia Loren", "David Miller", "Amina Begum", "Liam O'Connor", "Chen Wei"]
    token_num = random.randint(1100, 1199)
    
    new_token = {
        "token_id": f"TKN-{token_num}",
        "customer_name": random.choice(sample_names),
        "customer_segment": random.choice(list(CUSTOMER_SEGMENTS.keys())),
        "requested_service": payload.get("service", "Cash Deposit/Withdrawal"),
        "wait_time_mins": round(random.uniform(3.0, 11.0), 1),
        "service_started_at": datetime.now().strftime("%H:%M:%S"),
        "is_appointment": random.choice([True, False]),
        "pre_verified_docs": True,
        "deflectable": deflection_engine.evaluate_request(payload.get("service", "Cash Deposit/Withdrawal"))["is_deflectable"]
    }
    live_counter_sessions[session_key] = new_token
    
    if action_type == "deflect_kiosk":
        msg = f"🎟️ Digital Fast-Pass generated! Customer directed to self-service kiosk with floor assistant assistance."
    elif action_type == "complete":
        msg = f"✅ Service for previous customer logged as completed. Next token {new_token['token_id']} called."
    else:
        msg = f"📣 Now calling Token {new_token['token_id']} ({new_token['customer_name']}) to {counter_id}."
        
    return {
        "status": "success",
        "message": msg,
        "next_token": new_token
    }

# -------------------------------------------------------------
# 3. PERSONA: FRONT-DESK GREETER & KIOSK TRIAGE
# -------------------------------------------------------------
@app.get("/api/triage")
def triage_token(
    service: str = "Cash Deposit/Withdrawal",
    segment: str = "Regular",
    hour: int = 12,
    is_appointment: bool = False,
    is_month_end: int = 0
):
    wait_res = wait_predictor.predict_wait_time(
        service_category=service,
        customer_segment=segment,
        arrival_hour=hour,
        is_appointment=is_appointment,
        is_month_end=is_month_end
    )
    deflect_res = deflection_engine.evaluate_request(service)
    
    return {
        "wait_prediction": wait_res,
        "deflection_guidance": deflect_res,
        "generated_token": f"TKN-{random.randint(2000, 9999)}"
    }

@app.post("/api/triage/issue")
def issue_smart_token(payload: dict = Body(...)):
    service = payload.get("service", "Cash Deposit/Withdrawal")
    segment = payload.get("segment", "Regular")
    cust_name = payload.get("name", "Walk-in Guest")
    is_apt = payload.get("is_appointment", False)
    
    wait_res = wait_predictor.predict_wait_time(service_category=service, customer_segment=segment, is_appointment=is_apt)
    deflect_res = deflection_engine.evaluate_request(service)
    
    token_id = f"TKN-{random.randint(3000, 9999)}"
    
    return {
        "status": "success",
        "token_id": token_id,
        "customer_name": cust_name,
        "service": service,
        "segment": segment,
        "estimated_wait_minutes": wait_res["predicted_wait_minutes"],
        "assigned_counter_pool": "Desk C_1 - C_4 (Cash/KYC)" if "Cash" in service or "KYC" in service else "Specialist Desk C_5 - C_8",
        "is_deflectable": deflect_res["is_deflectable"],
        "target_channel": deflect_res["target_channel"],
        "qr_code_mock": f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={token_id}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# -------------------------------------------------------------
# 4. PERSONA: BANK OFFICIALS & REGIONAL CLUSTER LEADERSHIP
# -------------------------------------------------------------
@app.get("/api/officials/overview")
def get_officials_overview():
    summary = []
    b_tokens_dicts = clean_tokens.to_dicts()
    
    total_network_traffic = 0
    total_hours_saved = 0.0
    total_sla_breaches = 0
    
    for b in BRANCH_NETWORK:
        sub = [t for t in b_tokens_dicts if t["branch_id"] == b["branch_id"]]
        tot = max(1, len(sub))
        total_network_traffic += tot
        
        avg_wait = sum(t["wait_time_minutes"] for t in sub) / tot
        breaches = sum(t["sla_breached"] for t in sub)
        total_sla_breaches += breaches
        
        deflect_metrics = deflection_engine.compute_branch_deflection_metrics(sub)
        total_hours_saved += deflect_metrics["hours_saved"]
        csat = sum(t["satisfaction_score"] for t in sub) / tot
        
        compliance_pct = round(100.0 - ((breaches / tot) * 100), 1)
        risk_tag = "Critical SLA Risk" if avg_wait > 18.0 else ("Moderate Load" if avg_wait > 12.0 else "Optimal Flow")
        
        summary.append({
            "branch_id": b["branch_id"],
            "name": b["name"],
            "cluster": b["cluster"],
            "counters": b["total_counters"],
            "total_visits": tot,
            "avg_wait": round(avg_wait, 1),
            "sla_breach_rate": round((breaches / tot) * 100, 1),
            "sla_compliance_rate": compliance_pct,
            "deflection_rate": deflect_metrics["deflection_rate_pct"],
            "hours_saved": deflect_metrics["hours_saved"],
            "cost_saved_usd": deflect_metrics["estimated_cost_savings_usd"],
            "csat": round(csat, 2),
            "status_tag": risk_tag
        })
        
    total_cost_savings_usd = round(total_hours_saved * 32.50, 2)
    network_sla_breach_pct = round((total_sla_breaches / max(1, total_network_traffic)) * 100, 1)
    
    # Load balancing smart referral recommendation
    high_load_branch = max(summary, key=lambda x: x["avg_wait"])
    low_load_branch = min(summary, key=lambda x: x["avg_wait"])
    
    load_balance_recommendation = {
        "source_branch": high_load_branch["name"],
        "target_branch": low_load_branch["name"],
        "rationale": f"{high_load_branch['name']} is operating under surge load ({high_load_branch['avg_wait']}m avg wait, {high_load_branch['sla_breach_rate']}% SLA breach rate).",
        "action": f"Automated appointment booking routing is active: diverting flexible appointment slots and non-urgent loan advisory to {low_load_branch['name']} ({low_load_branch['avg_wait']}m wait), situated 3.8 km away.",
        "projected_wait_reduction": "6.5 mins network-wide"
    }

    # Digital Deflection Adoption by Channel
    channel_adoption = [
        {"channel": "Self-Service Passbook Kiosk", "adoption_pct": 78.4, "status": "High Adoption"},
        {"channel": "Cash Deposit Machine (CDM) / ATM", "adoption_pct": 52.6, "status": "Expanding"},
        {"channel": "Mobile App / Video KYC Kiosk", "adoption_pct": 41.2, "status": "Growth Target"},
        {"channel": "Mobile Banking Pin/Card Reset", "adoption_pct": 63.8, "status": "High Adoption"}
    ]
    
    # Executive Briefing
    executive_briefing = (
        f"Executive Summary: Network served {total_network_traffic:,} customer visits across {len(BRANCH_NETWORK)} branches. "
        f"Digital Deflection diverted {round(total_hours_saved):,} teller hours to self-service, generating ${total_cost_savings_usd:,.2f} in operational savings. "
        f"Overall SLA compliance stands at {100 - network_sla_breach_pct:.1f}%. "
        f"Priority action: Deploy 2 additional surge tellers to {high_load_branch['name']} during midday peak windows."
    )

    return {
        "network_summary": summary,
        "totals": {
            "total_network_visits": total_network_traffic,
            "total_hours_saved": round(total_hours_saved, 1),
            "total_cost_savings_usd": total_cost_savings_usd,
            "network_sla_breach_pct": network_sla_breach_pct,
            "average_network_csat": round(sum(s["csat"] for s in summary) / len(summary), 2)
        },
        "load_balancing": load_balance_recommendation,
        "channel_adoption": channel_adoption,
        "executive_briefing": executive_briefing
    }

# -------------------------------------------------------------
# 5. PERSONA: CUSTOMER VOICE & NLP SENTIMENT
# -------------------------------------------------------------
@app.get("/api/feedback")
def get_feedback(branch_id: str = "BR_001"):
    b_feedback = feedback_df.filter(feedback_df["branch_id"] == branch_id).to_dicts()
    processed = sentiment_analyzer.process_feedback_batch(b_feedback)
    insights = sentiment_analyzer.get_insights_summary(processed)
    
    return {
        "total_reviews": insights["total_reviews"],
        "sentiment_distribution": insights["sentiment_distribution"],
        "top_topics": insights["overall_top_topics"],
        "pain_points": insights["key_pain_points"],
        "counter_leaderboard": insights["counter_feedback_leaderboard"],
        "avg_polarity": insights["avg_sentiment_polarity"],
        "recent_reviews": processed[-15:]
    }

# -------------------------------------------------------------
# 6. WHAT-IF CAPACITY SIMULATOR
# -------------------------------------------------------------
@app.get("/api/simulate")
def run_simulation(
    arrivals: int = 40,
    counters: int = 4,
    service_time: float = 7.5,
    deflection_pct: float = 25.0,
    sla: float = 15.0
):
    sim_res = queue_simulator.run_simulation(
        base_hourly_arrivals=arrivals,
        active_counters=counters,
        avg_service_mins=service_time,
        digital_deflection_pct=deflection_pct,
        sla_threshold_mins=sla,
        duration_hours=6
    )
    return sim_res

# -------------------------------------------------------------
# ROOT UI SERVING
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")
    return "<h1>Bank Optimizer API Running. Static UI loading...</h1>"

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
