"""
Streamlit Multi-Persona Intelligent Branch Service Load & Customer Experience Optimizer.
Supports Bank Managers, Workers (Tellers/Greeters), and Regional Leadership.
"""
import streamlit as st
import polars as pl
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Import Internal Engine Modules
from src.config import (
    SERVICE_CATEGORIES, CUSTOMER_SEGMENTS, BRANCH_NETWORK,
    RAW_DATA_DIR, PROCESSED_DATA_DIR
)
from src.data_generator import generate_all_data
from src.data_pipeline import BankingDataPipeline
from src.models.demand_forecaster import DemandForecaster
from src.models.wait_time_model import WaitTimePredictor
from src.models.digital_deflection import DigitalDeflectionEngine
from src.models.nlp_sentiment import FeedbackSentimentAnalyzer
from src.optimization.staff_optimizer import StaffCounterOptimizer
from src.optimization.queue_simulator import BranchQueueSimulator
from src.optimization.explainability import BranchExplainabilityEngine
from src.utils.helpers import CUSTOM_CSS, render_metric_card, get_status_badge, get_counter_profiles

# Page Config
st.set_page_config(
    page_title="ApexBank AI Branch Load Optimizer",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------- CACHED DATA & MODEL LOADER -----------------
@st.cache_resource(show_spinner=False)
def initialize_system():
    pipeline = BankingDataPipeline()
    clean_tokens, hourly_metrics, staff, branches, feedback, appointments = pipeline.run_pipeline()
    
    # Train Models on Raw Data
    forecaster = DemandForecaster()
    forecaster.train(hourly_metrics)
    
    wait_predictor = WaitTimePredictor()
    wait_predictor.train(clean_tokens)
    
    deflection_engine = DigitalDeflectionEngine()
    sentiment_analyzer = FeedbackSentimentAnalyzer()
    staff_optimizer = StaffCounterOptimizer()
    queue_simulator = BranchQueueSimulator()
    xai_engine = BranchExplainabilityEngine()
    
    return {
        "pipeline": pipeline,
        "clean_tokens": clean_tokens,
        "hourly_metrics": hourly_metrics,
        "staff": staff,
        "branches": branches,
        "feedback": feedback,
        "appointments": appointments,
        "forecaster": forecaster,
        "wait_predictor": wait_predictor,
        "deflection_engine": deflection_engine,
        "sentiment_analyzer": sentiment_analyzer,
        "staff_optimizer": staff_optimizer,
        "queue_simulator": queue_simulator,
        "xai_engine": xai_engine
    }

system = initialize_system()

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("## 🏦 **ApexBank AI**")
    st.caption("Intelligent Branch Service Load & Experience Optimizer")
    st.divider()
    
    persona = st.selectbox(
        "👤 Select User Persona",
        [
            "📊 1. Branch Manager Cockpit",
            "👷 2. Teller & Worker Portal",
            "🎫 3. Front-Desk Greeter & Kiosk Triage",
            "🏛️ 4. Regional Network Leadership",
            "💬 5. Customer Voice & NLP Insights",
            "🔬 6. What-If Capacity Simulator"
        ]
    )
    
    selected_branch_name = st.selectbox(
        "🏢 Select Branch Location",
        [b["name"] for b in BRANCH_NETWORK]
    )
    selected_branch_meta = next(b for b in BRANCH_NETWORK if b["name"] == selected_branch_name)
    branch_id = selected_branch_meta["branch_id"]
    
    st.divider()
    
    st.markdown("### **Operational Controls**")
    sim_hour = st.slider("🕒 Operational Hour of Day", min_value=9, max_value=16, value=12, format="%d:00")
    is_month_end_sim = st.toggle("📅 Simulate Month-End Rush", value=False)
    
    if st.button("🔄 Retrain All ML Models", use_container_width=True):
        st.cache_resource.clear()
        st.success("All ML Models retrained on raw queue records!")
        st.rerun()

# ----------------- FILTER DATA FOR ACTIVE BRANCH -----------------
b_tokens = system["clean_tokens"].filter(pl.col("branch_id") == branch_id)
b_tokens_list = b_tokens.to_dicts()
b_staff = system["staff"].filter(pl.col("branch_id") == branch_id).to_dicts()
b_feedback = system["feedback"].filter(pl.col("branch_id") == branch_id).to_dicts()

# -------------------------------------------------------------
# 1. PERSONA: BRANCH MANAGER COCKPIT
# -------------------------------------------------------------
if "1. Branch Manager" in persona:
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-title">📊 {selected_branch_name} — Real-Time Operations Cockpit</div>
        <div class="hero-subtitle">Cluster: {selected_branch_meta['cluster']} | Active Counters: {selected_branch_meta['total_counters']} | Peak Window: {selected_branch_meta['peak_window']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate Today's Forecast
    forecast_records = system["forecaster"].forecast_day(
        branch_id=branch_id,
        date_str=datetime.now().strftime("%Y-%m-%d"),
        day_of_week=datetime.now().weekday(),
        is_month_end=int(is_month_end_sim)
    )
    
    current_forecast = next((f for f in forecast_records if f["arrival_hour"] == sim_hour), forecast_records[3])
    pred_arrivals = int(current_forecast["predicted_arrivals"])
    surge_status = current_forecast["surge_risk"]
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Predicted Hourly Inflow", f"{pred_arrivals} cust", f"Surge: {surge_status}", "red" if "Surge" in surge_status else "green"), unsafe_allow_html=True)
    with c2:
        hr_tokens = [t for t in b_tokens_list if t.get("arrival_hour") == sim_hour]
        avg_wait_val = sum(t["wait_time_minutes"] for t in hr_tokens) / max(1, len(hr_tokens)) if hr_tokens else 14.5
        st.markdown(render_metric_card("Current Avg Wait Time", f"{avg_wait_val:.1f} min", "SLA Target: 15.0m", "red" if avg_wait_val > 15.0 else "green"), unsafe_allow_html=True)
    with c3:
        deflect_metrics = system["deflection_engine"].compute_branch_deflection_metrics(b_tokens_list)
        st.markdown(render_metric_card("Digital Deflection Index", f"{deflect_metrics['deflection_rate_pct']}%", f"{deflect_metrics['hours_saved']}h teller time saved (${deflect_metrics['estimated_cost_savings_usd']})", "blue"), unsafe_allow_html=True)
    with c4:
        csat = sum(t["satisfaction_score"] for t in b_tokens_list) / max(1, len(b_tokens_list))
        st.markdown(render_metric_card("Customer CSAT Score", f"{csat:.2f} / 5.0", "Target: 4.5+", "green" if csat >= 4.0 else "red"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Two Columns: Forecast Curve & Explainable AI Diagnosis
    col_chart, col_xai = st.columns([1.5, 1])
    
    with col_chart:
        st.subheader("📈 Predicted Hourly Footfall & Surge Confidence Bands")
        time_slots = [f["time_slot"] for f in forecast_records]
        arrivals = [f["predicted_arrivals"] for f in forecast_records]
        ci_high = [f["ci_upper"] for f in forecast_records]
        ci_low = [f["ci_lower"] for f in forecast_records]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_slots, y=arrivals,
            mode="lines+markers",
            name="Forecasted Arrivals",
            line=dict(color="#38bdf8", width=3),
            marker=dict(size=8, color="#38bdf8")
        ))
        fig.add_trace(go.Scatter(
            x=time_slots, y=ci_high,
            mode="lines",
            name="95% Confidence Upper",
            line=dict(color="rgba(56, 189, 248, 0.3)", width=1, dash="dot")
        ))
        
        fig.add_hline(y=28, line_dash="dash", line_color="#ef4444", annotation_text="High Surge Threshold (>28/hr)")
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
            font=dict(color="#0f172a"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=320,
            xaxis_title="Time Slot",
            yaxis_title="Expected Customers / Hr"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_xai:
        st.subheader("🧠 Explainable AI (XAI) Bottleneck Diagnosis")
        xai_res = system["xai_engine"].explain_branch_congestion(
            predicted_arrivals=pred_arrivals,
            active_counters=selected_branch_meta["total_counters"],
            avg_wait=avg_wait_val,
            sla_target=15.0,
            is_month_end=is_month_end_sim,
            top_service="Cash Deposit/Withdrawal",
            digital_deflection_rate=deflect_metrics["deflection_rate_pct"] / 100.0
        )
        
        st.markdown(f"**Status:** {get_status_badge(xai_res['status_flag'])}", unsafe_allow_html=True)
        st.info(xai_res["executive_summary"])
        
        st.markdown("**Root-Cause Contributors:**")
        for driver in xai_res["root_cause_drivers"]:
            st.markdown(f"• **{driver['factor']}** ({driver['impact_pct']}%): {driver['detail']}")
            
    st.divider()
    
    # Prescriptive Counter Optimization Section
    st.subheader("⚡ Prescriptive Staff-to-Counter Reallocation (Optimization Engine)")
    st.caption("Automated skill-to-demand matching with dynamic surge relief and staggered break schedules.")
    
    service_demand_map = {
        "Cash Deposit/Withdrawal": int(current_forecast["cash_kyc_share"] * 0.6),
        "Account Services & KYC": int(current_forecast["cash_kyc_share"] * 0.4),
        "Passbook / Statement Printing": int(current_forecast["quick_services_share"] * 0.5),
        "Card Services & Pin Reset": int(current_forecast["quick_services_share"] * 0.5),
        "Loan & Mortgage Advisory": int(current_forecast["loans_investments_share"] * 0.6),
        "Forex & Trade Finance": max(1, int(current_forecast["loans_investments_share"] * 0.4))
    }
    
    opt_res = system["staff_optimizer"].optimize_allocations(
        active_staff=b_staff,
        service_demands=service_demand_map,
        available_counters=selected_branch_meta["total_counters"]
    )
    
    col_opt1, col_opt2 = st.columns([1.8, 1])
    with col_opt1:
        st.markdown(f"**Optimal Counter Configuration (Capacity Utilization: {opt_res['projected_branch_utilization_pct']}%)**")
        st.dataframe(pl.DataFrame([
            {
                "Counter": a["counter_id"],
                "Assigned Service Desk": a["assigned_service"],
                "Staff Member": a["staff_name"],
                "Skill Match Type": a["match_type"],
                "Speed Rating": a["speed_rating"]
            }
            for a in opt_res["assignments"]
        ]), use_container_width=True, hide_index=True)
    with col_opt2:
        st.markdown("**Staggered Lunch & Surge Coverage Schedule:**")
        break_data = [
            {
                "Counter": b["counter_id"],
                "Staff": b["staff_name"],
                "Break Window": b["allocated_break_window"],
                "Coverage": b["surge_coverage_status"]
            }
            for b in opt_res.get("break_schedule", [])
        ]
        if break_data:
            st.dataframe(pl.DataFrame(break_data), use_container_width=True, hide_index=True)
        
        if st.button("✅ 1-Click Broadcast Counter Realignment", use_container_width=True):
            st.success(f"Dynamic counter assignments broadcasted to {len(opt_res['assignments'])} teller terminals!")

# -------------------------------------------------------------
# 2. PERSONA: TELLER & WORKER PORTAL
# -------------------------------------------------------------
elif "2. Teller & Worker" in persona:
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-title">👷 Teller Counter Terminal & Frontline Assistant</div>
        <div class="hero-subtitle">Intra-Branch Tier-2 Redirection Engine: Desk caller, skill-based transfers, queue rebalancing, and digital fast-pass.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate unique operational profiles for all branch counters
    branch_counters = get_counter_profiles(selected_branch_meta['total_counters'])
    counter_options = [f"{c['counter_id']} — {c['service']} ({c['staff_name']})" for c in branch_counters]
    
    selected_option = st.selectbox("🎯 Select Active Counter Desk Terminal", counter_options, index=0)
    selected_idx = counter_options.index(selected_option)
    curr_c = branch_counters[selected_idx]
    
    # Counter Staff & Status Bar
    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 18px; margin-bottom: 18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
            <span style="font-size:12px; color:#64748b; font-weight:700; text-transform:uppercase;">ASSIGNED STAFF</span><br>
            <b style="color:#0f172a; font-size:16px;">👤 {curr_c['staff_name']}</b> <span style="color:#2563eb; font-size:13px; font-weight:600;">({curr_c['staff_role']})</span>
        </div>
        <div>
            <span style="font-size:12px; color:#64748b; font-weight:700; text-transform:uppercase;">PRIMARY DESK ROLE</span><br>
            <b style="color:#0f172a; font-size:14px;">🏷️ {curr_c['service']}</b>
        </div>
        <div>
            <span style="font-size:12px; color:#64748b; font-weight:700; text-transform:uppercase;">CURRENT LINE DEPTH</span><br>
            <b style="color:{'#dc2626' if curr_c['queue_depth'] > 4 else '#059669'}; font-size:15px;">👥 {curr_c['queue_depth']} Customers Waiting</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2 = st.columns([1.4, 1])
    with col_w1:
        st.subheader("Current Active Customer at Desk")
        
        # Segment styling badge
        seg_color = "#2563eb" if "VIP" in curr_c['customer_segment'] else ("#d97706" if "Senior" in curr_c['customer_segment'] else ("#7c3aed" if "SME" in curr_c['customer_segment'] else "#475569"))
        
        st.markdown(f"""
        <div style="background: #ffffff; border: 2px solid #0284c7; border-radius: 16px; padding: 22px; box-shadow: 0 4px 16px rgba(2, 132, 199, 0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:12px; color:#64748b; font-weight:700; letter-spacing:0.05em;">ACTIVE TOKEN</div>
                    <div style="font-size:38px; font-weight:900; color:#0284c7; line-height:1.1;">{curr_c['active_token']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:12px; color:#64748b; font-weight:700; letter-spacing:0.05em;">SERVICE DURATION</div>
                    <div style="font-size:32px; font-weight:800; color:#059669; line-height:1.1;">⏱️ {curr_c['service_timer']}</div>
                </div>
            </div>
            <hr style="border-color: #e2e8f0; margin: 14px 0;">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <p style="color: #1e293b; margin: 3px 0;"><b>Customer:</b> {curr_c['customer_name']}</p>
                <p style="color: #1e293b; margin: 3px 0;"><b>Segment:</b> <span style="background:{seg_color}15; color:{seg_color}; padding:2px 8px; border-radius:6px; font-weight:700; font-size:12px;">{curr_c['customer_segment']}</span></p>
                <p style="color: #1e293b; margin: 3px 0;"><b>Service:</b> {curr_c['service']}</p>
                <p style="color: #1e293b; margin: 3px 0;"><b>Wait in Lobby:</b> {curr_c['wait_time_mins']} mins</p>
            </div>
            <p style="color: #475569; font-size:13px; margin: 8px 0 0 0; background:#f8fafc; padding:6px 10px; border-radius:6px;"><b>📝 Transaction Details:</b> {curr_c['amount_note']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_act1, c_act2, c_act3 = st.columns(3)
        with c_act1:
            if st.button("✅ Complete Service", use_container_width=True):
                st.toast(f"Token {curr_c['active_token']} completed and logged in analytics!")
        with c_act2:
            if st.button("📣 Call Next Token", use_container_width=True):
                next_t = curr_c['upcoming_queue'][0]['token'] if curr_c['upcoming_queue'] else 'TKN-1250'
                st.toast(f"Calling next token {next_t} to {curr_c['counter_id']}!")
        with c_act3:
            if st.button("📲 Issue Kiosk Fast-Pass", use_container_width=True):
                if curr_c['deflectable']:
                    st.toast(f"Customer redirected to {curr_c['deflection_channel']} with Fast-Pass!")
                else:
                    st.toast("Customer requires in-person teller verification.")
                    
        st.divider()
        
        # -------------------------------------------------------------
        # TIER-2: INTRA-BRANCH COUNTER REDIRECTION & QUEUE REBALANCING
        # -------------------------------------------------------------
        st.subheader("🔀 Tier-2 Intra-Branch Redirection & Skill Transfers")
        st.caption("Transfer active token to a specialized counter or pull waiting customers from congested desks.")
        
        tab_transfer, tab_rebalance = st.tabs(["📤 Transfer Active Customer to Counter", "⚡ Pull Token from Overcrowded Desk"])
        
        with tab_transfer:
            other_counters = [c for c in branch_counters if c['counter_id'] != curr_c['counter_id']]
            other_labels = [f"{c['counter_id']} — {c['service']} ({c['staff_name']} - {c['staff_role']})" for c in other_counters]
            
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                target_dest = st.selectbox("Select Target Specialist Counter", other_labels, key="transfer_target")
            with t_col2:
                transfer_reason = st.selectbox(
                    "Select Intra-Branch Redirection Reason",
                    [
                        "📌 Escalation / Senior Officer Sign-Off Required",
                        "💼 Cross-Sell Opportunity (Wealth/Loan Advisory)",
                        "🌐 Specialist Skill / Language Match Needed",
                        "⚡ VIP / Priority Fast-Track Desk Escalation",
                        "⚠️ Complex Multi-Product Inquiry"
                    ],
                    key="transfer_reason"
                )
            
            if st.button(f"🚀 Execute Intra-Branch Transfer ({curr_c['active_token']} ➔ {target_dest.split(' — ')[0]})", use_container_width=True):
                target_cid = target_dest.split(' — ')[0]
                st.success(f"✅ **Intra-Branch Redirection Complete:** Token **{curr_c['active_token']}** ({curr_c['customer_name']}) transferred to **{target_cid}**.")
                st.info(f"📋 **Routing Ticket #RED-{curr_c['counter_num']}09:** Logged under *{transfer_reason}*. Customer assigned top priority in {target_cid}'s queue.")
                
        with tab_rebalance:
            # Find the most congested counter in the branch
            busy_counters = sorted([c for c in branch_counters if c['counter_id'] != curr_c['counter_id']], key=lambda x: x['queue_depth'], reverse=True)
            busy_c = busy_counters[0] if busy_counters else None
            
            if busy_c and busy_c['queue_depth'] > 0:
                st.markdown(f"""
                <div style="background: #fffbeb; border: 1px solid #fcd34d; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                    <b style="color: #b45309;">⚠️ Queue Bottleneck Detected at {busy_c['counter_id']} ({busy_c['service']})</b><br>
                    <span style="color: #78350f; font-size:13px;">{busy_c['queue_depth']} customers are currently waiting in line for {busy_c['staff_name']}. You can pull the next customer to balance the branch load.</span>
                </div>
                """, unsafe_allow_html=True)
                
                next_candidate = busy_c['upcoming_queue'][0] if busy_c['upcoming_queue'] else {"token": "TKN-1090", "name": "Waiting Client", "service": busy_c['service']}
                if st.button(f"📥 Pull Next Customer ({next_candidate['token']} - {next_candidate['name']}) to {curr_c['counter_id']}", use_container_width=True):
                    st.success(f"⚡ **Load Balanced:** Pulled token **{next_candidate['token']}** from **{busy_c['counter_id']}** to **{curr_c['counter_id']}**! Expected wait time reduced by 6.5 mins.")
            else:
                st.info("✓ All counters are operating within SLA threshold with balanced queue depths.")
                
    with col_w2:
        st.subheader("Shift Performance Scorecard")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.metric("Tokens Served", f"{curr_c['today_served']} cust", "+5 vs avg")
        with sc2:
            st.metric("Avg Handling Time", f"{curr_c['aht_mins']}m", "Target: <8m")
            
        sc3, sc4 = st.columns(2)
        with sc3:
            st.metric("Customer CSAT", f"{curr_c['csat_score']} / 5.0", "Top Tier")
        with sc4:
            st.metric("Queue in Line", f"{curr_c['queue_depth']} cust", f"{curr_c['wait_time_mins']}m wait")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader(f"Upcoming Queue for {curr_c['counter_id']}")
        
        for q in curr_c['upcoming_queue']:
            st.markdown(f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="color:#0284c7; font-size:15px;">{q['token']}</b>
                    <span style="font-size:12px; background:#f1f5f9; color:#334155; padding:2px 8px; border-radius:12px; font-weight:600;">⏱️ Est. {q['wait']}</span>
                </div>
                <div style="font-size:13px; color:#1e293b; margin-top:3px;"><b>{q['name']}</b> ({q['segment']})</div>
                <div style="font-size:12px; color:#64748b;">Requested: {q['service']}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.divider()
    
    # -------------------------------------------------------------
    # LIVE INTRA-BRANCH COUNTER FLEET MATRIX (TIER-2 OVERVIEW)
    # -------------------------------------------------------------
    st.subheader(f"🏢 {selected_branch_name} — Live Counter Fleet Status (Intra-Branch Load)")
    fleet_data = [
        {
            "Counter Desk": c["counter_id"],
            "Staff Member": c["staff_name"],
            "Desk Service": c["service"],
            "Active Token": c["active_token"],
            "Active Customer": c["customer_name"],
            "Queue Waiting": f"{c['queue_depth']} cust",
            "Est. Wait": f"{c['wait_time_mins']} min",
            "Deflectable": "📲 Yes (Kiosk)" if c["deflectable"] else "🏛️ In-Person",
            "CSAT": c["csat_score"]
        }
        for c in branch_counters
    ]
    st.dataframe(pl.DataFrame(fleet_data), use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# 3. PERSONA: FRONT-DESK GREETER & KIOSK TRIAGE
# -------------------------------------------------------------
elif "3. Front-Desk Greeter" in persona:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🎫 Smart Token Triage & Self-Service Deflection Assistant</div>
        <div class="hero-subtitle">Intake kiosk & floor greeter assistant to divert digital-ready customers and fast-track priority clients.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_triage1, col_triage2 = st.columns([1, 1.2])
    
    with col_triage1:
        st.subheader("New Customer Arrival Intake")
        customer_name = st.text_input("Customer Name / Identifier", value="Alex Johnson (VIP Client)")
        cust_segment = st.selectbox("Customer Segment", list(CUSTOMER_SEGMENTS.keys()))
        selected_service = st.selectbox("Service Requested", list(SERVICE_CATEGORIES.keys()))
        is_prebooked = st.checkbox("Has Pre-Booked Appointment", value=False)
        
        wait_pred = system["wait_predictor"].predict_wait_time(
            service_category=selected_service,
            customer_segment=cust_segment,
            arrival_hour=sim_hour,
            is_appointment=is_prebooked,
            is_month_end=int(is_month_end_sim)
        )
        
        deflect_eval = system["deflection_engine"].evaluate_request(selected_service)
        
        if st.button("🎟️ Issue Smart Token Ticket", use_container_width=True):
            st.toast(f"Token Issued for {customer_name}!")
            
    with col_triage2:
        st.subheader("Real-Time Triage & Deflection Recommendation")
        
        if deflect_eval["is_deflectable"]:
            st.markdown(f"""
            <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
                <h4 style="color: #047857; margin-top:0; font-weight: 800;">📲 DIGITAL DEFLECTION RECOMMENDED (0 Min Wait)</h4>
                <p style="color: #1f2937;">This request can be fulfilled immediately via <b>{deflect_eval['target_channel']}</b> without waiting at teller desks.</p>
                <p style="color: #1f2937;"><b>Time saved for customer:</b> ~{deflect_eval['time_saved_minutes']} minutes.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Floor Assistant Action Steps:**")
            for step in deflect_eval["greeter_checklist"]:
                st.markdown(f"- {step}")
        else:
            st.markdown(f"""
            <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 12px; padding: 18px; margin-bottom: 16px;">
                <h4 style="color: #1d4ed8; margin-top:0; font-weight: 800;">🏛️ IN-PERSON SPECIALIST REQUIRED</h4>
                <p style="color: #1f2937;">Routing to dedicated counter with pre-verification checklist.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("### Estimated Wait Time (EWT) Badge")
        ewt_col1, ewt_col2 = st.columns(2)
        with ewt_col1:
            st.metric("Predicted Wait Time", f"{wait_pred['predicted_wait_minutes']} mins", f"SLA: {wait_pred['sla_target_minutes']} mins")
        with ewt_col2:
            st.markdown(f"**Risk Level:**<br>{get_status_badge(wait_pred['risk_level'])}", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. PERSONA: REGIONAL NETWORK LEADERSHIP
# -------------------------------------------------------------
elif "4. Regional Network" in persona:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🏛️ Regional Network Intelligence & Tier-3 Inter-Branch Redirection Hub</div>
        <div class="hero-subtitle">Cross-branch load balancing, real-time footfall diverting, incentive dispatching, and cluster governance.</div>
    </div>
    """, unsafe_allow_html=True)
    
    b_tokens_all = system["clean_tokens"].to_dicts()
    
    # Calculate real-time branch network health
    network_summary = []
    for b in BRANCH_NETWORK:
        sub = [t for t in b_tokens_all if t["branch_id"] == b["branch_id"]]
        tot = max(1, len(sub))
        avg_wait = sum(t["wait_time_minutes"] for t in sub) / tot
        breaches = sum(t["sla_breached"] for t in sub)
        deflect_metrics = system["deflection_engine"].compute_branch_deflection_metrics(sub)
        csat = sum(t["satisfaction_score"] for t in sub) / tot
        
        # Determine congestion tier
        if avg_wait > 20.0 or (breaches / tot) > 0.25:
            status_role = "⚠️ Source (Overburdened - Divert Out)"
            role_badge = "Critical"
        elif avg_wait < 13.0 and b["total_counters"] >= 6:
            status_role = "🟢 Target (Surplus Capacity - Receive)"
            role_badge = "Optimal"
        else:
            status_role = "✓ Balanced (Normal Operations)"
            role_badge = "Balanced"
            
        network_summary.append({
            "Branch Name": b["name"],
            "branch_id": b["branch_id"],
            "Cluster": b["cluster"],
            "Counters": b["total_counters"],
            "Visits": tot,
            "Avg Wait (min)": round(avg_wait, 1),
            "SLA Breach %": round((breaches / tot) * 100, 1),
            "Deflection Rate %": deflect_metrics["deflection_rate_pct"],
            "Hours Saved": deflect_metrics["hours_saved"],
            "Cost Saved ($)": deflect_metrics["estimated_cost_savings_usd"],
            "CSAT": round(csat, 2),
            "Network Role": status_role,
            "role_badge": role_badge
        })
        
    # Regional KPI Row
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(render_metric_card("Network Active Branches", f"{len(BRANCH_NETWORK)} Branches", "Metro & Suburb Clusters", "blue"), unsafe_allow_html=True)
    with r2:
        cluster_breach_avg = sum(n["SLA Breach %"] for n in network_summary) / len(network_summary)
        st.markdown(render_metric_card("Cluster SLA Compliance", f"{100 - cluster_breach_avg:.1f}%", "Target: >90%", "green" if cluster_breach_avg < 15 else "red"), unsafe_allow_html=True)
    with r3:
        st.markdown(render_metric_card("Active Inter-Branch Routes", "3 Clusters Active", "Dynamic Geo-Balancing", "green"), unsafe_allow_html=True)
    with r4:
        total_saved_usd = sum(n["Cost Saved ($)"] for n in network_summary)
        st.markdown(render_metric_card("Cluster Cost Savings", f"${total_saved_usd:,}", "Labor & Deflection ROI", "blue"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # -------------------------------------------------------------
    # TIER-3 INTER-BRANCH REDIRECTION DISPATCHER
    # -------------------------------------------------------------
    st.subheader("🌐 Tier-3 Cross-Branch Customer Redirection & Geo-Load Dispatcher")
    st.caption("Re-route non-urgent appointments, mobile token arrivals, and flex walk-ins from congested hubs to surplus branches.")
    
    col_geo1, col_geo2 = st.columns([1.3, 1])
    
    with col_geo1:
        st.markdown("**1. Configure Inter-Branch Redirection Channel:**")
        g_c1, g_c2 = st.columns(2)
        with g_c1:
            source_options = [f"{n['Branch Name']} (Wait: {n['Avg Wait (min)']}m)" for n in network_summary if "Source" in n['Network Role'] or n['Avg Wait (min)'] > 15]
            if not source_options:
                source_options = [f"{network_summary[0]['Branch Name']} (Wait: {network_summary[0]['Avg Wait (min)']}m)"]
            selected_source = st.selectbox("🔴 Source Overburdened Branch", source_options, index=0)
            
        with g_c2:
            target_options = [f"{n['Branch Name']} (Wait: {n['Avg Wait (min)']}m — {n['Counters']} counters)" for n in network_summary if "Target" in n['Network Role'] or n['Avg Wait (min)'] <= 15]
            if not target_options:
                target_options = [f"{network_summary[1]['Branch Name']} (Wait: {network_summary[1]['Avg Wait (min)']}m)"]
            selected_target = st.selectbox("🟢 Destination Target Branch (Surplus Capacity)", target_options, index=0)
            
        redirection_incentive = st.selectbox(
            "🎁 Customer Redirection Incentive & Channel Strategy",
            [
                "🎟️ Guaranteed Zero-Wait Priority Pass + $10 Coffee Voucher",
                "📲 Pre-Arrival Mobile App Push Notification (Geofenced Divert)",
                "📅 Dynamic Online Appointment Re-Routing (Flexible Time Slots)",
                "🚐 Free Express Cluster Shuttle & Fast-Pass Desk Check-In",
                "💳 500 Bonus Reward Points for Visiting Neighboring Branch"
            ]
        )
        
        divert_volume = st.slider(
            "👥 Redirection Volume (Customers to Divert / Hour)",
            min_value=5,
            max_value=35,
            value=18,
            step=1,
            help="Simulate the footfall shifted from the congested branch to the nearby receiving branch."
        )
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("📢 1-Click Launch Inter-Branch Campaign", use_container_width=True):
                st.success(f"🚀 **Inter-Branch Redirection Active:** Diverting {divert_volume} customers/hr from **{selected_source.split(' (')[0]}** ➔ **{selected_target.split(' (')[0]}**!")
                st.toast("Campaign broadcasted to Mobile App & Kiosk Routing Engine!")
        with c_btn2:
            if st.button("📱 Send App Push Notifications", use_container_width=True):
                st.info(f"📲 Sent geo-targeted redirect notification to {divert_volume * 2} customers en route to {selected_source.split(' (')[0]}.")
                
    with col_geo2:
        st.markdown("**2. Simulated Redirection Impact (Predictive Engine):**")
        
        # Calculate simulation deltas
        orig_wait = 28.5
        new_source_wait = max(11.0, round(orig_wait - (divert_volume * 0.8), 1))
        target_orig_wait = 11.2
        new_target_wait = round(target_orig_wait + (divert_volume * 0.22), 1)
        breaches_saved = int(divert_volume * 0.75)
        
        st.markdown(f"""
        <div style="background: #ffffff; border: 2px solid #2563eb; border-radius: 14px; padding: 18px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);">
            <div style="font-size:13px; font-weight:700; color:#2563eb; text-transform:uppercase; margin-bottom:8px;">SIMULATION RESULTS SUMMARY</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="color:#64748b;">Source Branch Wait:</span>
                <b><span style="color:#dc2626; text-decoration:line-through;">{orig_wait}m</span> ➔ <span style="color:#059669; font-size:16px;">{new_source_wait}m</span> (-{int((orig_wait-new_source_wait)/orig_wait*100)}%)</b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="color:#64748b;">Target Branch Wait:</span>
                <b>{target_orig_wait}m ➔ <span style="color:#2563eb;">{new_target_wait}m</span> (Within SLA ✓)</b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="color:#64748b;">SLA Breaches Averted:</span>
                <b style="color:#059669;">🛡️ {breaches_saved} Breaches / Hr</b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#64748b;">Cluster Network Balance:</span>
                <b style="color:#2563eb;">92% Optimal Capacity</b>
            </div>
            <hr style="border-color:#e2e8f0; margin:10px 0;">
            <p style="font-size:12px; color:#475569; margin:0;"><b>📢 Customer Push Message Preview:</b><br>
            <i>"High wait times at Downtown Financial Hub ({orig_wait}m). Tap here to divert to Suburban Tech Park (10 min away) for instant 0-wait priority desk allocation + $10 coffee voucher."</i></p>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # -------------------------------------------------------------
    # REGIONAL CLUSTER TABLE & COMPARISON CHART
    # -------------------------------------------------------------
    st.subheader("📊 Regional Branch Network Fleet & Inter-Branch Routing Matrix")
    
    col_tbl, col_cht = st.columns([1.5, 1])
    with col_tbl:
        disp_data = [
            {
                "Branch Name": n["Branch Name"],
                "Cluster": n["Cluster"],
                "Counters": n["Counters"],
                "Avg Wait": f"{n['Avg Wait (min)']} min",
                "SLA Breach": f"{n['SLA Breach %']}%",
                "Deflection Rate": f"{n['Deflection Rate %']}%",
                "Inter-Branch Role": n["Network Role"],
                "CSAT": n["CSAT"]
            }
            for n in network_summary
        ]
        st.dataframe(pl.DataFrame(disp_data), use_container_width=True, hide_index=True)
        
    with col_cht:
        b_names = [n["Branch Name"].replace(" Branch", "").replace(" Commercial", "") for n in network_summary]
        b_waits = [n["Avg Wait (min)"] for n in network_summary]
        
        fig_net = go.Figure()
        fig_net.add_trace(go.Bar(
            x=b_names,
            y=b_waits,
            marker_color=["#ef4444" if w > 20 else ("#f59e0b" if w > 15 else "#10b981") for w in b_waits],
            text=[f"{w}m" for w in b_waits],
            textposition="auto"
        ))
        fig_net.add_hline(y=15.0, line_dash="dash", line_color="#dc2626", annotation_text="15m SLA Target")
        fig_net.update_layout(
            title="Cluster Average Wait Times (Mins)",
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
            font=dict(color="#0f172a"),
            margin=dict(l=10, r=10, t=35, b=10),
            height=260,
            yaxis_title="Avg Wait (min)"
        )
        st.plotly_chart(fig_net, use_container_width=True)

# -------------------------------------------------------------
# 5. PERSONA: CUSTOMER VOICE & NLP INSIGHTS
# -------------------------------------------------------------
elif "5. Customer Voice" in persona:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">💬 Customer Voice & Sentiment Root-Cause Studio</div>
        <div class="hero-subtitle">NLP topic modeling and sentiment diagnostics to uncover why customers are waiting and what drives friction.</div>
    </div>
    """, unsafe_allow_html=True)
    
    nlp_records = system["sentiment_analyzer"].process_feedback_batch(b_feedback)
    insights = system["sentiment_analyzer"].get_insights_summary(nlp_records)
    
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown(render_metric_card("Analyzed Feedback Logs", f"{insights['total_reviews']}", "Customer Responses", "blue"), unsafe_allow_html=True)
    with f2:
        pos_count = insights["sentiment_distribution"].get("Positive", 0)
        st.markdown(render_metric_card("Positive Sentiment", f"{pos_count}", f"{int(pos_count/max(1, insights['total_reviews'])*100)}% of total", "green"), unsafe_allow_html=True)
    with f3:
        neg_count = insights["sentiment_distribution"].get("Negative", 0)
        st.markdown(render_metric_card("Critical / Friction Logs", f"{neg_count}", f"{int(neg_count/max(1, insights['total_reviews'])*100)}% of total", "red"), unsafe_allow_html=True)
    with f4:
        st.markdown(render_metric_card("Avg Sentiment Polarity", f"{insights['avg_sentiment_polarity']}", "Scale [-1.0 to +1.0]", "green" if insights['avg_sentiment_polarity'] > 0 else "red"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Top Friction Drivers (Root Cause)")
    for topic, cnt in insights["key_pain_points"].items():
        st.markdown(f"• **{topic}:** {cnt} negative customer reviews logged")

# -------------------------------------------------------------
# 6. PERSONA: WHAT-IF CAPACITY SIMULATOR
# -------------------------------------------------------------
elif "6. What-If Capacity" in persona:
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🔬 Discrete-Event "What-If" Capacity & Queue Simulator</div>
        <div class="hero-subtitle">Simulate the impact of counter changes, digital deflection campaigns, and surge stress tests.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_sim_ctrl, col_sim_res = st.columns([1, 1.8])
    with col_sim_ctrl:
        st.subheader("Simulation Parameters")
        sim_arrivals = st.slider("Hourly Arrival Rate (Lambda)", min_value=15, max_value=80, value=42, step=1)
        sim_counters = st.slider("Active Counters (c)", min_value=1, max_value=12, value=4, step=1)
        sim_service_time = st.slider("Avg Service Duration (mins)", min_value=3.0, max_value=25.0, value=7.5, step=0.5)
        sim_deflection_pct = st.slider("Digital Deflection % (Diverted to Kiosks)", min_value=0, max_value=60, value=25, step=5)
        sim_sla_threshold = st.slider("SLA Wait Threshold (mins)", min_value=5, max_value=30, value=15, step=1)
        
        sim_out = system["queue_simulator"].run_simulation(
            base_hourly_arrivals=sim_arrivals,
            active_counters=sim_counters,
            avg_service_mins=sim_service_time,
            digital_deflection_pct=sim_deflection_pct,
            sla_threshold_mins=sim_sla_threshold,
            duration_hours=6
        )
        
    with col_sim_res:
        st.subheader("Simulation Outcome & Performance Impact")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Simulated Customers", f"{sim_out['total_customers_served']}")
        m2.metric("Avg Wait Time", f"{sim_out['avg_wait_minutes']}m")
        m3.metric("90th Percentile Wait", f"{sim_out['p90_wait_minutes']}m")
        m4.metric("SLA Breach Rate", f"{sim_out['sla_breach_rate_pct']}%")
        
        prog = sim_out["hourly_progression"]
        hours = [f"Hour {h['hour_bucket']}" for h in prog]
        waits = [h['avg_wait_mins'] for h in prog]
        
        fig_prog = px.bar(
            x=hours, y=waits,
            labels={"x": "Hour of Shift", "y": "Avg Wait (mins)"},
            title="Hourly Simulated Wait Dynamics Over 6-Hour Shift",
            color=waits,
            color_continuous_scale="Reds"
        )
        fig_prog.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
            font=dict(color="#0f172a"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=300
        )
        st.plotly_chart(fig_prog, use_container_width=True)
