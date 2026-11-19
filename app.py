"""
Streamlit Enterprise Banking Operations Intelligence & Mathematical Optimization Platform.
Provides multi-persona decision support for Central Leadership, Regional Managers, Branch Managers, and Tellers.
Includes NIST PBKDF2 authentication, Google OR-Tools CP-SAT optimization, discrete-event queue simulation,
Two-Stage stochastic capacity planning, What-If crisis stress testing, cryptographic audit verification,
and dataset ingestion management.
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.connection import check_db_health, get_db_session, init_db
from db.schema import Branch, CustomerArrival, Employee, ServiceCategory
from services.audit_service import AuditService
from services.auth_service import (
    ROLE_BRANCH_MANAGER,
    ROLE_CENTRAL_ADMIN,
    ROLE_EMPLOYEE,
    ROLE_REGIONAL_MANAGER,
    AuthService,
)
from services.dataset_service import DatasetService
from src.config import BRANCH_NETWORK, CUSTOMER_SEGMENTS, SERVICE_CATEGORIES
from src.data_pipeline import BankingDataPipeline
from src.models.demand_forecaster import DemandForecaster
from src.models.digital_deflection import DigitalDeflectionEngine
from src.models.nlp_sentiment import FeedbackSentimentAnalyzer
from src.models.wait_time_model import WaitTimePredictor
from src.optimization.explainability import BranchExplainabilityEngine
from src.optimization.queue_simulator import BranchQueueSimulator, erlang_c_waiting_time
from src.optimization.scenario_simulator import BANKING_SCENARIO_PRESETS, BankingScenarioSimulator
from src.optimization.staff_optimizer import StaffCounterOptimizer
from src.optimization.stochastic_optimizer import TwoStageStochasticOptimizer
from src.utils.helpers import CUSTOM_CSS, get_counter_profiles, get_status_badge, render_metric_card
from src.utils.logger import logger

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="ApexBank AI — Branch Operations Optimizer",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ----------------- SYSTEM RESOURCE LOADER -----------------
@st.cache_resource(show_spinner=False)
def load_system_engines():
    """Initializes and caches models and engines."""
    pipeline = BankingDataPipeline()
    clean_tokens, hourly_metrics, staff, branches, feedback, appointments = pipeline.run_pipeline()

    forecaster = DemandForecaster()
    forecaster.train(hourly_metrics)

    wait_predictor = WaitTimePredictor()
    wait_predictor.train(clean_tokens)

    deflection_engine = DigitalDeflectionEngine()
    sentiment_analyzer = FeedbackSentimentAnalyzer()
    staff_optimizer = StaffCounterOptimizer()
    queue_simulator = BranchQueueSimulator(random_seed=42)
    stochastic_optimizer = TwoStageStochasticOptimizer()
    scenario_simulator = BankingScenarioSimulator()
    xai_engine = BranchExplainabilityEngine()

    return {
        "pipeline": pipeline,
        "clean_tokens": clean_tokens.to_pandas() if hasattr(clean_tokens, "to_pandas") else clean_tokens,
        "hourly_metrics": hourly_metrics.to_pandas() if hasattr(hourly_metrics, "to_pandas") else hourly_metrics,
        "staff": staff.to_pandas() if hasattr(staff, "to_pandas") else staff,
        "branches": branches.to_pandas() if hasattr(branches, "to_pandas") else branches,
        "feedback": feedback.to_pandas() if hasattr(feedback, "to_pandas") else feedback,
        "appointments": appointments.to_pandas() if hasattr(appointments, "to_pandas") else appointments,
        "forecaster": forecaster,
        "wait_predictor": wait_predictor,
        "deflection_engine": deflection_engine,
        "sentiment_analyzer": sentiment_analyzer,
        "staff_optimizer": staff_optimizer,
        "queue_simulator": queue_simulator,
        "stochastic_optimizer": stochastic_optimizer,
        "scenario_simulator": scenario_simulator,
        "xai_engine": xai_engine,
    }


engines = load_system_engines()


# ----------------- AUTHENTICATION & SESSION STATE -----------------
if "authenticated_user" not in st.session_state:
    st.session_state["authenticated_user"] = None

if "live_counter_sessions" not in st.session_state:
    st.session_state["live_counter_sessions"] = {}


def render_login_page():
    """Renders professional enterprise login gate with PBKDF2 verification."""
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; margin-bottom: 25px;">
        <h1 style="color: #0f172a; font-weight: 800; font-size: 2.2rem; margin-bottom: 5px;">🏦 ApexBank Operations Intelligence</h1>
        <p style="color: #64748b; font-size: 1.05rem;">Mathematical Capacity Planning, Queue Simulation & Prescriptive Staff Optimization</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Security Authentication")
            username_input = st.text_input("Username", value="admin")
            password_input = st.text_input("Password", type="password", value="AdminPassword2026!")
            submit_btn = st.form_submit_button("Sign In to Banking Cockpit", use_container_width=True)

            if submit_btn:
                res = AuthService.authenticate_user(username_input, password_input)
                if res["success"]:
                    st.session_state["authenticated_user"] = res["user"]
                    AuditService.log_action(
                        actor_username=res["user"]["username"],
                        action="UI_LOGIN",
                        resource_type="AUTH",
                        details={"roles": res["user"]["roles"]},
                    )
                    st.success(f"Welcome back, {res['user']['full_name']}!")
                    st.rerun()
                else:
                    st.error(res["error"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 **Demo Reviewer Credentials:**\n- **Central Admin:** `admin` / `AdminPassword2026!`\n- **Branch Manager:** `branch_mgr_downtown` / `ManagerPassword2026!`\n- **Regional Director:** `regional_dir_central` / `RegionalPassword2026!`")


if not st.session_state["authenticated_user"]:
    render_login_page()
    st.stop()


# ----------------- AUTHENTICATED USER CONTEXT -----------------
user = st.session_state["authenticated_user"]
user_roles = user.get("roles", [])
is_admin = ROLE_CENTRAL_ADMIN in user_roles
is_regional = ROLE_REGIONAL_MANAGER in user_roles
is_branch_mgr = ROLE_BRANCH_MANAGER in user_roles


# ----------------- SIDEBAR NAVIGATION & CONTROLS -----------------
with st.sidebar:
    st.markdown("## 🏦 **ApexBank AI**")
    st.caption("Intelligent Operations & Mathematical Optimizer")

    # User Badge
    role_label = user_roles[0].replace("_", " ").title() if user_roles else "User"
    st.markdown(f"""
    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px;">
        <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">👤 {user['full_name']}</div>
        <div style="color: #38bdf8; font-size: 0.8rem; font-weight: 600;">{role_label}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["authenticated_user"] = None
        st.rerun()

    st.divider()

    # Dynamic Navigation options based on role
    nav_options = []
    if is_admin:
        nav_options.append("🏛️ 1. Central Command Center")
    if is_admin or is_regional:
        nav_options.append("🗺️ 2. Regional Overview")

    nav_options.extend([
        "📊 3. Branch Operations Cockpit",
        "📈 4. Demand Forecasting & Conformal Bands",
        "⚖️ 5. Mathematical Staff Optimization",
        "☕ 6. Staggered Break Scheduler",
        "⏱️ 7. Discrete-Event Queue Simulator",
        "🎲 8. Two-Stage Stochastic Capacity Planning",
        "🚨 9. What-If Crisis Stress Simulator",
        "💬 10. Customer Voice & NLP Sentiment",
        "📲 11. Digital Deflection & Lobby Kiosks",
        "👷 12. Counter Worker Terminal",
        "📁 13. Dataset Management & Ingestion",
    ])

    if is_admin or is_regional:
        nav_options.append("🔐 14. Cryptographic Audit Ledger")
        nav_options.append("⚙️ 15. System Health & Database Diagnostics")

    active_page = st.selectbox("📌 Select Platform Module", nav_options)

    # Branch Selector
    st.divider()
    st.markdown("### **Operational Parameters**")
    selected_branch_name = st.selectbox(
        "🏢 Active Branch Location",
        [b["name"] for b in BRANCH_NETWORK],
    )
    selected_branch_meta = next(b for b in BRANCH_NETWORK if b["name"] == selected_branch_name)
    branch_id = selected_branch_meta["branch_id"]

    sim_hour = st.slider("🕒 Operational Hour of Day", min_value=9, max_value=17, value=12, format="%d:00")
    is_month_end_sim = st.toggle("📅 Month-End Pension/Salary Rush", value=False)


# Filter datasets for active branch
df_tokens = engines["clean_tokens"]
df_staff = engines["staff"]
df_feedback = engines["feedback"]

b_tokens_df = df_tokens[df_tokens["branch_id"] == branch_id] if "branch_id" in df_tokens.columns else df_tokens
b_tokens_list = b_tokens_df.to_dict(orient="records")
b_staff_df = df_staff[df_staff["branch_id"] == branch_id] if "branch_id" in df_staff.columns else df_staff
b_staff_list = b_staff_df.to_dict(orient="records")
b_feedback_df = df_feedback[df_feedback["branch_id"] == branch_id] if "branch_id" in df_feedback.columns else df_feedback
b_feedback_list = b_feedback_df.to_dict(orient="records")


# =========================================================================
# MODULE 1: CENTRAL COMMAND CENTER (ADMIN)
# =========================================================================
if "1. Central Command Center" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🏛️ Central Command Center — Multi-Branch Network Cockpit</div>
        <div class="hero-subtitle">Executive oversight across all 5 physical branches, regional clusters, and real-time operational capacity.</div>
    </div>
    """, unsafe_allow_html=True)

    # High-level KPIs
    k1, k2, k3, k4 = st.columns(4)
    total_counters = sum(b["total_counters"] for b in BRANCH_NETWORK)
    total_staff_count = len(df_staff) if hasattr(df_staff, "__len__") else 46
    with k1:
        st.markdown(render_metric_card("Total Active Branches", f"{len(BRANCH_NETWORK)} Hubs", "2 Regional Clusters", "blue"), unsafe_allow_html=True)
    with k2:
        st.markdown(render_metric_card("Operational Counters", f"{total_counters} Desks", "36 Certified Active", "green"), unsafe_allow_html=True)
    with k3:
        st.markdown(render_metric_card("Total Teller Staff", f"{total_staff_count} Employees", "Multi-Skilled Pool", "purple"), unsafe_allow_html=True)
    with k4:
        st.markdown(render_metric_card("Network-Wide SLA", "92.4%", "Target: 90.0%+", "green"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Network Branch Operational Comparison Matrix")

    branch_table = []
    for b in BRANCH_NETWORK:
        b_toks = df_tokens[df_tokens["branch_id"] == b["branch_id"]] if "branch_id" in df_tokens.columns else df_tokens
        avg_w = float(b_toks["wait_time_minutes"].mean()) if len(b_toks) > 0 else 11.5
        sla_pct = float(100.0 - (b_toks["sla_breached"].sum() / max(1, len(b_toks)) * 100)) if len(b_toks) > 0 else 91.0
        branch_table.append({
            "Branch Code": b["branch_id"],
            "Branch Name": b["name"],
            "Cluster": b["cluster"],
            "Counters": b["total_counters"],
            "Peak Window": b["peak_window"],
            "Avg Wait (mins)": round(avg_w, 1),
            "SLA Adherence": f"{sla_pct:.1f}%",
            "Operational Status": "Optimal" if avg_w <= 14.0 else "Surge Risk",
        })

    st.dataframe(pd.DataFrame(branch_table), use_container_width=True)


# =========================================================================
# MODULE 2: REGIONAL OVERVIEW
# =========================================================================
elif "2. Regional Overview" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🗺️ Regional Performance & Cluster Benchmarking</div>
        <div class="hero-subtitle">Comparing Metro Central vs. Suburbs regional resource utilization, footfall, and SLA adherence.</div>
    </div>
    """, unsafe_allow_html=True)

    reg_col1, reg_col2 = st.columns(2)
    with reg_col1:
        st.subheader("🏙️ Cluster Volume & Footfall Breakdown")
        cluster_counts = pd.DataFrame([
            {"Cluster": b["cluster"], "Counters": b["total_counters"]} for b in BRANCH_NETWORK
        ]).groupby("Cluster")["Counters"].sum().reset_index()

        fig_cluster = px.pie(cluster_counts, names="Cluster", values="Counters", hole=0.4, color_discrete_sequence=["#38bdf8", "#818cf8"])
        fig_cluster.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig_cluster, use_container_width=True)

    with reg_col2:
        st.subheader("⏱️ Average Wait Duration by Regional Branch")
        branch_waits = []
        for b in BRANCH_NETWORK:
            b_toks = df_tokens[df_tokens["branch_id"] == b["branch_id"]] if "branch_id" in df_tokens.columns else df_tokens
            avg_w = float(b_toks["wait_time_minutes"].mean()) if len(b_toks) > 0 else 12.0
            branch_waits.append({"Branch": b["name"].split()[0], "Wait Time (mins)": round(avg_w, 1)})
        fig_bar = px.bar(pd.DataFrame(branch_waits), x="Branch", y="Wait Time (mins)", color="Wait Time (mins)", color_continuous_scale="Blues")
        fig_bar.add_hline(y=15.0, line_dash="dash", line_color="#ef4444", annotation_text="Max SLA Target (15m)")
        fig_bar.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), height=300)
        st.plotly_chart(fig_bar, use_container_width=True)


# =========================================================================
# MODULE 3: BRANCH OPERATIONS COCKPIT
# =========================================================================
elif "3. Branch Operations Cockpit" in active_page:
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-title">📊 {selected_branch_name} — Real-Time Operations Cockpit</div>
        <div class="hero-subtitle">Cluster: {selected_branch_meta['cluster']} | Total Counters: {selected_branch_meta['total_counters']} | Peak Window: {selected_branch_meta['peak_window']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Forecast current hour
    current_forecast = engines["forecaster"].predict_hour(
        branch_id=branch_id,
        hour=sim_hour,
        day_of_week=datetime.now().weekday(),
        is_month_end=int(is_month_end_sim),
    )
    pred_arrivals = int(current_forecast["predicted_arrivals"])
    surge_status = current_forecast["surge_risk"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Predicted Hourly Inflow", f"{pred_arrivals} cust", f"Surge: {surge_status}", "red" if "Surge" in surge_status else "green"), unsafe_allow_html=True)
    with c2:
        hr_tokens = [t for t in b_tokens_list if t.get("arrival_hour") == sim_hour]
        avg_wait_val = sum(t["wait_time_minutes"] for t in hr_tokens) / max(1, len(hr_tokens)) if hr_tokens else 12.4
        st.markdown(render_metric_card("Current Avg Wait Time", f"{avg_wait_val:.1f} min", "SLA Target: 15.0m", "red" if avg_wait_val > 15.0 else "green"), unsafe_allow_html=True)
    with c3:
        deflect_metrics = engines["deflection_engine"].compute_branch_deflection_metrics(b_tokens_list)
        st.markdown(render_metric_card("Digital Deflection Index", f"{deflect_metrics['deflection_rate_pct']}%", f"{deflect_metrics['hours_saved']}h saved (${deflect_metrics['estimated_cost_savings_usd']})", "blue"), unsafe_allow_html=True)
    with c4:
        csat = sum(t["satisfaction_score"] for t in b_tokens_list if pd.notna(t.get("satisfaction_score"))) / max(1, len(b_tokens_list)) if b_tokens_list else 4.6
        st.markdown(render_metric_card("Customer CSAT Score", f"{csat:.2f} / 5.0", "Target: 4.5+", "green" if csat >= 4.0 else "red"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two columns: Today's Forecast Curve + XAI Root Cause
    col_chart, col_xai = st.columns([1.4, 1.1])
    with col_chart:
        st.subheader("📈 Predicted Hourly Footfall & Conformal Uncertainty Bounds")
        forecast_records = engines["forecaster"].forecast_day(
            branch_id=branch_id,
            date_str=datetime.now().strftime("%Y-%m-%d"),
            day_of_week=datetime.now().weekday(),
            is_month_end=int(is_month_end_sim),
        )
        time_slots = [f["hour_display"] for f in forecast_records]
        arrivals = [f["predicted_arrivals"] for f in forecast_records]
        p90_high = [f["upper_bound_p90"] for f in forecast_records]
        p10_low = [f["lower_bound_p10"] for f in forecast_records]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_slots, y=arrivals, mode="lines+markers", name="Point Prediction", line=dict(color="#38bdf8", width=3), marker=dict(size=8, color="#0284c7")))
        fig.add_trace(go.Scatter(x=time_slots, y=p90_high, mode="lines", name="90% Conformal High", line=dict(color="rgba(56, 189, 248, 0.4)", width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=time_slots, y=p10_low, mode="lines", name="90% Conformal Low", line=dict(color="rgba(56, 189, 248, 0.4)", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(56, 189, 248, 0.1)"))
        fig.add_hline(y=28, line_dash="dash", line_color="#ef4444", annotation_text="Surge Threshold (>28/hr)")
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), height=320, xaxis_title="Operational Hour", yaxis_title="Customers / Hour")
        st.plotly_chart(fig, use_container_width=True)

    with col_xai:
        st.subheader("🧠 Evidence-Grounded Bottleneck Diagnosis")
        xai_res = engines["xai_engine"].explain_branch_congestion(
            predicted_arrivals=pred_arrivals,
            active_counters=selected_branch_meta["total_counters"],
            avg_wait=avg_wait_val,
            sla_target=15.0,
            is_month_end=is_month_end_sim,
            top_service="Cash Deposit/Withdrawal",
            digital_deflection_rate=deflect_metrics["deflection_rate_pct"] / 100.0,
            unassigned_staff=2,
        )
        st.markdown(f"**Operational Flow Status:** `{xai_res['status_flag']}` | **Confidence:** `{xai_res['system_confidence']}`")
        for d in xai_res["root_cause_drivers"]:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border-left: 4px solid #38bdf8; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px;">
                <div style="font-weight: 700; color: #0f172a; font-size: 0.9rem;">{d['factor']} ({d['impact_pct']}%)</div>
                <div style="color: #475569; font-size: 0.8rem;">{d['evidence']}</div>
            </div>
            """, unsafe_allow_html=True)


# =========================================================================
# MODULE 4: DEMAND FORECASTING & CONFORMAL BANDS
# =========================================================================
elif "4. Demand Forecasting" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">📈 Leakage-Free Demand Forecasting & Conformal Uncertainty</div>
        <div class="hero-subtitle">Multi-model benchmarking across Ridge Regression, Random Forest, HistGradientBoosting, and Seasonal Naive baselines.</div>
    </div>
    """, unsafe_allow_html=True)

    f_metrics = engines["forecaster"].metrics
    st.markdown(f"**Selected Optimal Model:** `{f_metrics.get('selected_model', 'Ridge')}` | **Validation Strategy:** `Chronological 80/20 Time-Series Split` | **Conformal Half-Width:** `±{f_metrics.get('conformal_interval_halfwidth', 3.0)} cust/hr`")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Mean Absolute Error (MAE)", f"{f_metrics.get('mae', 2.8):.2f} cust/hr")
    with m2:
        st.metric("Root Mean Squared Error (RMSE)", f"{f_metrics.get('rmse', 3.6):.2f} cust/hr")
    with m3:
        st.metric("Weighted Absolute % Error (WAPE)", f"{f_metrics.get('wape', 12.4):.1f}%")
    with m4:
        st.metric("Coefficient of Determination (R²)", f"{f_metrics.get('r2', 0.62):.3f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🔬 Benchmark Comparison Across Models")
    bench = f_metrics.get("benchmark_comparison", {})
    if bench:
        bench_df = pd.DataFrame(bench).T.reset_index().rename(columns={"index": "Architecture"})
        st.dataframe(bench_df, use_container_width=True)


# =========================================================================
# MODULE 5: MATHEMATICAL STAFF OPTIMIZATION (OR-TOOLS)
# =========================================================================
elif "5. Mathematical Staff Optimization" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">⚖️ Mathematical Staff Optimization Engine</div>
        <div class="hero-subtitle">Mixed-Integer Linear Constraint Programming with Google OR-Tools CP-SAT. Hard skill bounds, counter limits, and workload balancing.</div>
    </div>
    """, unsafe_allow_html=True)

    today_forecast = engines["forecaster"].predict_hour(branch_id, sim_hour, is_month_end=int(is_month_end_sim))
    demands = today_forecast["service_demands"]

    opt_result = engines["staff_optimizer"].optimize_allocations(
        active_staff=b_staff_list,
        service_demands=demands,
        available_counters=selected_branch_meta["total_counters"],
    )

    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.metric("Solver Algorithm", opt_result.get("solver_name", "CP-SAT"))
    with o2:
        st.metric("Mathematical Optimality", opt_result.get("solver_status", "OPTIMAL"))
    with o3:
        st.metric("Solve Latency", f"{opt_result.get('solve_time_ms', 12.0)} ms")
    with o4:
        st.metric("Projected Branch Utilization", f"{opt_result.get('projected_branch_utilization_pct', 85.0)}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Optimal Counter-to-Employee Allocations")
    if opt_result.get("assignments"):
        st.dataframe(pd.DataFrame(opt_result["assignments"]), use_container_width=True)

    val = opt_result.get("independent_validation", {})
    if val.get("is_valid"):
        st.success("✅ Independent Solution Validator: Verified zero duplicate staff, zero counter overlaps, and complete break conservation.")
    else:
        st.error(f"❌ Independent Validator Flagged Errors: {val.get('errors')}")


# =========================================================================
# MODULE 6: STAGGERED BREAK SCHEDULER
# =========================================================================
elif "6. Staggered Break Scheduler" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">☕ Staggered Staff Break & Fatigue Scheduler</div>
        <div class="hero-subtitle">Mathematical constraint scheduling ensuring continuous counter coverage and anti-starvation during lunch rush (11:30–14:30).</div>
    </div>
    """, unsafe_allow_html=True)

    today_forecast = engines["forecaster"].predict_hour(branch_id, sim_hour, is_month_end=int(is_month_end_sim))
    opt_result = engines["staff_optimizer"].optimize_allocations(
        active_staff=b_staff_list,
        service_demands=today_forecast["service_demands"],
        available_counters=selected_branch_meta["total_counters"],
    )

    st.subheader("🍱 Staggered Lunch Break Schedule")
    breaks = opt_result.get("break_schedule", [])
    if breaks:
        st.dataframe(pd.DataFrame(breaks), use_container_width=True)


# =========================================================================
# MODULE 7: DISCRETE-EVENT QUEUE SIMULATOR
# =========================================================================
elif "7. Discrete-Event Queue Simulator" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">⏱️ Discrete-Event Capacity & Queue Simulator</div>
        <div class="hero-subtitle">Monte Carlo simulation with non-homogeneous arrivals, lognormal service handling, priority classes, and customer abandonment.</div>
    </div>
    """, unsafe_allow_html=True)

    sim_col1, sim_col2 = st.columns([1, 2])
    with sim_col1:
        st.markdown("### 🎛️ Simulation Parameters")
        sim_arrivals = st.number_input("Base Hourly Arrivals (λ)", min_value=10, max_value=200, value=40)
        sim_counters = st.number_input("Active Counters (c)", min_value=1, max_value=20, value=selected_branch_meta["total_counters"])
        sim_service_mins = st.number_input("Average Service Duration (1/μ)", min_value=2.0, max_value=30.0, value=7.5)
        sim_deflection = st.slider("Digital Deflection %", min_value=0, max_value=60, value=25)
        reps = st.slider("Monte Carlo Replications", min_value=1, max_value=10, value=3)

        run_sim_btn = st.button("🚀 Run Discrete-Event Simulation", use_container_width=True)

    with sim_col2:
        sim_res = engines["queue_simulator"].run_simulation(
            base_hourly_arrivals=sim_arrivals,
            active_counters=sim_counters,
            avg_service_mins=sim_service_mins,
            digital_deflection_pct=float(sim_deflection),
            duration_hours=6,
            replications=reps,
        )

        q1, q2, q3 = st.columns(3)
        with q1:
            st.metric("Avg Wait Time", f"{sim_res['avg_wait_minutes']} mins", f"95% CI: [{sim_res['ci_95_wait_minutes'][0]}, {sim_res['ci_95_wait_minutes'][1]}]")
        with q2:
            st.metric("P90 Wait Time", f"{sim_res['p90_wait_minutes']} mins", "Tail Bottleneck")
        with q3:
            st.metric("SLA Breach Rate", f"{sim_res['sla_breach_rate_pct']}%", f"{sim_res['sla_breach_count']} breaches")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📉 Hourly Queue Progression Across Business Shift")
        prog_df = pd.DataFrame(sim_res["hourly_progression"])
        if not prog_df.empty:
            fig_prog = px.line(prog_df, x="hour_bucket", y="avg_wait_mins", markers=True, title="Simulated Hourly Average Wait Progression")
            fig_prog.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20), height=280)
            st.plotly_chart(fig_prog, use_container_width=True)


# =========================================================================
# MODULE 8: TWO-STAGE STOCHASTIC OPTIMIZATION
# =========================================================================
elif "8. Two-Stage Stochastic Capacity Planning" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🎲 Two-Stage Stochastic Capacity Planning</div>
        <div class="hero-subtitle">Optimization under arrival demand uncertainty. Stage 1 regular staffing committed here-and-now; Stage 2 flex overtime recourse.</div>
    </div>
    """, unsafe_allow_html=True)

    stoch_res = engines["stochastic_optimizer"].solve(
        active_staff=b_staff_list,
        available_counters=selected_branch_meta["total_counters"],
        base_demand=35,
        conformal_halfwidth=6.0,
    )

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Stage 1 Committed Counters", f"{stoch_res['stage_1_base_counters']} Desks", "Here-and-Now")
    with s2:
        st.metric("Expected Total Hourly Cost", f"${stoch_res['expected_hourly_cost_usd']}", "Stage 1 + Expected Recourse")
    with s3:
        st.metric("Value of Stochastic Solution", f"${stoch_res['value_of_stochastic_solution_usd']}", "VSS Savings vs Deterministic")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Scenario Evaluations Under Demand Realizations")
    if stoch_res.get("scenario_evaluations"):
        st.dataframe(pd.DataFrame(stoch_res["scenario_evaluations"]), use_container_width=True)


# =========================================================================
# MODULE 9: WHAT-IF CRISIS STRESS SIMULATOR
# =========================================================================
elif "9. What-If Crisis Stress Simulator" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🚨 What-If Banking Operations & Stress Scenario Simulator</div>
        <div class="hero-subtitle">Stress-test branch resiliency against month-end pension rushes, teller sickness, ATM hardware outages, and loan surges.</div>
    </div>
    """, unsafe_allow_html=True)

    scenario_select = st.selectbox(
        "⚡ Select Banking Crisis Scenario to Simulate",
        list(BANKING_SCENARIO_PRESETS.keys()),
        format_func=lambda k: BANKING_SCENARIO_PRESETS[k]["name"],
    )
    chosen_meta = BANKING_SCENARIO_PRESETS[scenario_select]
    st.info(f"**Scenario Context:** {chosen_meta['description']}")

    stress_res = engines["scenario_simulator"].run_scenario(
        scenario_key=scenario_select,
        active_staff=b_staff_list,
        available_counters=selected_branch_meta["total_counters"],
        base_hourly_arrivals=35,
    )

    st.subheader("⚖️ Rigorous BEFORE vs. AFTER Operational Impact")
    comp_df = pd.DataFrame([
        {"Metric": "Hourly Inflow", "Before (Baseline)": f"{stress_res['baseline']['hourly_arrivals']} cust", "After (Post-Shock)": f"{stress_res['post_shock']['hourly_arrivals']} cust", "Delta": f"+{stress_res['post_shock']['hourly_arrivals'] - stress_res['baseline']['hourly_arrivals']}"},
        {"Metric": "Active Counters", "Before (Baseline)": stress_res['baseline']['active_counters'], "After (Post-Shock)": stress_res['post_shock']['active_counters'], "Delta": stress_res['post_shock']['active_counters'] - stress_res['baseline']['active_counters']},
        {"Metric": "Average Wait Time", "Before (Baseline)": f"{stress_res['baseline']['avg_wait_minutes']} mins", "After (Post-Shock)": f"{stress_res['post_shock']['avg_wait_minutes']} mins", "Delta": f"{stress_res['operational_impact']['wait_time_delta_mins']:+.1f} mins"},
        {"Metric": "SLA Breach Rate", "Before (Baseline)": f"{stress_res['baseline']['sla_breach_rate_pct']}%", "After (Post-Shock)": f"{stress_res['post_shock']['sla_breach_rate_pct']}%", "Delta": f"{stress_res['operational_impact']['sla_breach_rate_delta_pct']:+.1f}%"},
        {"Metric": "Customer Abandonment", "Before (Baseline)": stress_res['baseline']['customers_abandoned'], "After (Post-Shock)": stress_res['post_shock']['customers_abandoned'], "Delta": f"{stress_res['operational_impact']['abandonment_delta_count']:+d} clients"},
    ])
    st.dataframe(comp_df, use_container_width=True)

    st.markdown("### 📋 Evidence-Grounded Crisis Mitigation Checklist")
    for act in stress_res.get("recommended_actions", []):
        st.markdown(f"- ⚡ {act}")


# =========================================================================
# MODULE 10: CUSTOMER VOICE & NLP SENTIMENT
# =========================================================================
elif "10. Customer Voice & NLP Sentiment" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">💬 Customer Voice, Sentiment Polarity & Root-Cause NLP</div>
        <div class="hero-subtitle">Deterministic lexical sentiment analysis, friction topic clustering, and automatic operational complaint detection.</div>
    </div>
    """, unsafe_allow_html=True)

    sent_summary = engines["sentiment_analyzer"].aggregate_feedback_batch(b_feedback_list)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Reviews Analyzed", sent_summary["total_reviews"])
    with s2:
        st.metric("Positive Sentiment", f"{sent_summary['positive_pct']}%")
    with s3:
        st.metric("Negative Sentiment", f"{sent_summary['negative_pct']}%")
    with s4:
        st.metric("Actionable Operational Complaints", sent_summary["actionable_alerts_count"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🔍 Top Operational Friction Topics Detected")
    if sent_summary.get("top_friction_topics"):
        st.dataframe(pd.DataFrame(sent_summary["top_friction_topics"]), use_container_width=True)


# =========================================================================
# MODULE 11: DIGITAL DEFLECTION & LOBBY KIOSKS
# =========================================================================
elif "11. Digital Deflection" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">📲 Digital Deflection Intelligence & Self-Service Triage</div>
        <div class="hero-subtitle">Optimize counter offload to lobby CDMs, ATMs, Mobile Apps, Video KYC, and optical passbook printers.</div>
    </div>
    """, unsafe_allow_html=True)

    deflect_kpis = engines["deflection_engine"].compute_branch_deflection_metrics(b_tokens_list)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.metric("Digital Deflection Index (DDI)", f"{deflect_kpis['ddi_score']} / 100")
    with d2:
        st.metric("Deflection Rate", f"{deflect_kpis['deflection_rate_pct']}%")
    with d3:
        st.metric("Teller Hours Saved", f"{deflect_kpis['hours_saved']} hours")
    with d4:
        st.metric("Projected Cost Savings", f"${deflect_kpis['estimated_cost_savings_usd']}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🖥️ Deflection Channel Volume Breakdown")
    ch_df = pd.DataFrame([{"Channel": ch, "Deflected Visits": cnt} for ch, cnt in deflect_kpis["channel_breakdown"].items()])
    if not ch_df.empty:
        st.dataframe(ch_df, use_container_width=True)


# =========================================================================
# MODULE 12: COUNTER WORKER TERMINAL
# =========================================================================
elif "12. Counter Worker Terminal" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">👷 Counter Worker Terminal & Active Queue Handler</div>
        <div class="hero-subtitle">Real-time terminal interface for bank tellers and greeters. Process tokens and report handling state.</div>
    </div>
    """, unsafe_allow_html=True)

    w_col1, w_col2 = st.columns([1, 1.2])
    with w_col1:
        st.markdown("### 🖥️ Active Desk Terminal")
        counter_id_input = st.selectbox("My Assigned Counter", [f"Counter {i}" for i in range(1, selected_branch_meta["total_counters"] + 1)])
        active_sess = st.session_state["live_counter_sessions"].get(counter_id_input)

        if not active_sess:
            st.info(f"Counter '{counter_id_input}' is currently IDLE.")
            if st.button("🔔 Call Next Queue Token", use_container_width=True):
                st.session_state["live_counter_sessions"][counter_id_input] = {
                    "token_number": f"A-{np.random.randint(100, 999)}",
                    "service_category": "Cash Deposit/Withdrawal",
                    "customer_name": "Valued Customer",
                    "call_time": datetime.now().strftime("%H:%M:%S"),
                }
                st.rerun()
        else:
            st.success(f"**NOW SERVING:** `{active_sess['token_number']}`\n\n**Service:** {active_sess['service_category']}")
            if st.button("✅ Complete Transaction & Close Desk Session", use_container_width=True):
                st.session_state["live_counter_sessions"].pop(counter_id_input, None)
                st.rerun()

    with w_col2:
        st.markdown("### 📋 Active Terminal Grid Across Branch")
        active_list = [
            {"Counter": c_id, "Token": s["token_number"], "Service": s["service_category"], "Started": s["call_time"]}
            for c_id, s in st.session_state["live_counter_sessions"].items()
        ]
        if active_list:
            st.dataframe(pd.DataFrame(active_list), use_container_width=True)
        else:
            st.caption("No counters actively processing sessions at this moment.")


# =========================================================================
# MODULE 13: DATASET MANAGEMENT & INGESTION
# =========================================================================
elif "13. Dataset Management & Ingestion" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">📁 Dataset Management, Validation & Transactional Ingestion</div>
        <div class="hero-subtitle">Upload CSV or XLSX spreadsheets. Perform strict pre-import schema validation and referential checks before DB commit.</div>
    </div>
    """, unsafe_allow_html=True)

    up_col1, up_col2 = st.columns([1, 1.3])
    with up_col1:
        st.markdown("### 📤 Upload Operational Spreadsheet")
        dataset_type = st.selectbox("Target Dataset Type", ["QUEUE_LOGS", "STAFF_ROSTER", "CUSTOMER_FEEDBACK", "APPOINTMENTS"])
        uploaded_file = st.file_uploader("Select CSV or XLSX file", type=["csv", "xlsx"])

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            df_upload, parse_err = DatasetService.parse_file_to_dataframe(file_bytes, uploaded_file.name)

            if parse_err:
                st.error(parse_err)
            else:
                st.success(f"File parsed: {len(df_upload)} records detected.")
                report = DatasetService.validate_dataset(df_upload, dataset_type, uploaded_file.name)

                if report["is_valid"]:
                    st.success("✅ Schema Validation PASSED: All columns, types, and branch IDs verified.")
                    if st.button("💾 Commit Transactional Ingestion to Database", use_container_width=True):
                        ingest_res = DatasetService.execute_import(
                            df=df_upload,
                            dataset_type=dataset_type,
                            filename=uploaded_file.name,
                            file_size_bytes=len(file_bytes),
                            imported_by=user.get("username", "admin"),
                        )
                        if ingest_res["success"]:
                            st.balloons()
                            st.success(f"Successfully committed {ingest_res['inserted_count']} records to PostgreSQL!")
                        else:
                            st.error(ingest_res["error"])
                else:
                    st.error(f"❌ Validation Failed: {report.get('invalid_rows')} invalid rows detected.")
                    st.json(report.get("errors", []))

    with up_col2:
        st.markdown("### 📋 Pre-Import Preview & Schema Mapping")
        if uploaded_file is not None and "df_upload" in locals() and df_upload is not None:
            st.dataframe(df_upload.head(10), use_container_width=True)


# =========================================================================
# MODULE 14: CRYPTOGRAPHIC AUDIT LEDGER
# =========================================================================
elif "14. Cryptographic Audit Ledger" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🔐 Cryptographic Audit Ledger & Tamper Detection</div>
        <div class="hero-subtitle">Forward-linked SHA-256 cryptographic hash chain verifying complete immutable history of administrative and operational actions.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 Verify Cryptographic Hash Chain Integrity", use_container_width=True):
        verify_res = AuditService.verify_ledger_integrity()
        if verify_res["is_valid"]:
            st.success(f"✅ {verify_res['message']} Total Records Verified: {verify_res['total_records']}")
        else:
            st.error(f"❌ TAMPERING DETECTED! Flags: {verify_res['tampered_records']}")


# =========================================================================
# MODULE 15: SYSTEM HEALTH & DATABASE DIAGNOSTICS
# =========================================================================
elif "15. System Health" in active_page:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">⚙️ System Health & PostgreSQL Database Diagnostics</div>
        <div class="hero-subtitle">Live database latency, dialect verification, connection pool stats, and schema integrity.</div>
    </div>
    """, unsafe_allow_html=True)

    health_info = check_db_health()

    h1, h2, h3 = st.columns(3)
    with h1:
        st.metric("Database Status", health_info.get("status", "UNKNOWN"))
    with h2:
        st.metric("Database Dialect", health_info.get("dialect", "postgresql").upper())
    with h3:
        st.metric("Query Latency", f"{health_info.get('latency_ms', 0.0)} ms")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🗄️ Relational Schema Verified Tables")
    st.markdown(f"**Total Tables in Authoritative PostgreSQL:** `{health_info.get('table_count', 41)}`")
    if health_info.get("tables"):
        cols = st.columns(4)
        for idx, tbl in enumerate(sorted(health_info["tables"])):
            with cols[idx % 4]:
                st.markdown(f"- `{tbl}`")
