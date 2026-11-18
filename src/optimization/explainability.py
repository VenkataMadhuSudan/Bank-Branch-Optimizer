"""
Explainable AI (XAI) & Manager Decision Support Generator.
Transforms complex ML predictions and queue anomalies into plain-English root causes and action checklists.
"""

class BranchExplainabilityEngine:
    def __init__(self):
        pass

    def explain_branch_congestion(
        self,
        predicted_arrivals: int,
        active_counters: int,
        avg_wait: float,
        sla_target: float,
        is_month_end: bool,
        top_service: str,
        digital_deflection_rate: float
    ) -> dict:
        """
        Generates root-cause attribution scores and plain-language explanation for branch managers.
        """
        drivers = []
        
        # Factor 1: Footfall Volume Surge
        if predicted_arrivals >= 30:
            drivers.append({
                "factor": "Heavy Footfall Surge",
                "impact_pct": 38,
                "detail": f"Predicted hourly arrival of {predicted_arrivals} customers exceeds standard counter capacity."
            })
        elif predicted_arrivals >= 20:
            drivers.append({
                "factor": "Moderate Traffic Volume",
                "impact_pct": 20,
                "detail": f"Moderate load ({predicted_arrivals} arrivals/hr)."
            })
            
        # Factor 2: Counter / Staffing Level
        if active_counters <= 3:
            drivers.append({
                "factor": "Counter Capacity Bottleneck",
                "impact_pct": 32,
                "detail": f"Only {active_counters} counters currently active, causing queue backlog to accumulate."
            })
        elif active_counters <= 5 and predicted_arrivals >= 25:
            drivers.append({
                "factor": "Tight Counter Availability",
                "impact_pct": 22,
                "detail": f"{active_counters} counters active under peak arrival conditions."
            })
            
        # Factor 3: Calendar & Month-End Effect
        if is_month_end:
            drivers.append({
                "factor": "Month-End Pension & Salary Rush",
                "impact_pct": 18,
                "detail": "Month-end cycle drives higher in-person cash and passbook transactions."
            })
            
        # Factor 4: Service Mix & Complexity
        if top_service in ["Loan & Mortgage Advisory", "Wealth & Investment Planning"]:
            drivers.append({
                "factor": "High-Duration Service Mix",
                "impact_pct": 25,
                "detail": f"High proportion of {top_service} transactions with long desk handling times."
            })
            
        # Factor 5: Underutilized Digital Kiosks
        if digital_deflection_rate < 0.25:
            drivers.append({
                "factor": "Low Digital Channel Adoption",
                "impact_pct": 15,
                "detail": f"Only {int(digital_deflection_rate*100)}% of eligible transactions are being deflected to ATMs/Kiosks."
            })
            
        # Compile natural language summary
        status = "CRITICAL BOTTLENECK" if avg_wait > sla_target * 1.4 else ("MODERATE PRESSURE" if avg_wait > sla_target else "OPTIMAL FLOW")
        
        action_checklist = []
        if active_counters < 6 and predicted_arrivals >= 25:
            action_checklist.append("⚡ Open 1 additional counter for Cash / KYC to absorb surge.")
        if digital_deflection_rate < 0.35:
            action_checklist.append("📲 Deploy floor greeter to redirect passbook and cash deposit customers to Self-Service Kiosks.")
        if is_month_end:
            action_checklist.append("📅 Pre-schedule staggered staff lunch breaks to keep all counters staffed between 11:30 and 14:00.")
        action_checklist.append("⏱️ Monitor VIP/HNI token alerts to prioritize high-value relationship clients.")

        return {
            "status_flag": status,
            "root_cause_drivers": drivers,
            "executive_summary": (
                f"Branch is experiencing {status.lower()} (Avg Wait: {avg_wait:.1f} mins vs SLA: {sla_target:.1f} mins). "
                f"Primary root causes are {', '.join([d['factor'] for d in drivers[:2]])}."
            ),
            "recommended_actions": action_checklist
        }
