"""
What-If Banking Operations & Stress Scenario Simulator.
Simulates banking shocks (month-end surges, employee absenteeism, ATM lobby outages, loan advisory spikes),
couples with Google OR-Tools optimization and discrete-event queue simulation,
and generates rigorous BEFORE vs. AFTER operational risk assessments.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BRANCH_NETWORK, SERVICE_CATEGORIES
from src.optimization.queue_simulator import BranchQueueSimulator
from src.optimization.staff_optimizer import StaffCounterOptimizer
from src.utils.logger import logger

# Banking Operational Stress Scenario Presets
BANKING_SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "month_end_rush": {
        "id": "month_end_rush",
        "name": "Month-End Pension & Salary Rush",
        "description": "+45% footfall surge with concentrated cash deposits and passbook printing demand.",
        "demand_multiplier": 1.45,
        "staff_absence_pct": 0.0,
        "counter_loss": 0,
        "deflection_delta_pct": -5.0,  # Cash customers less deflectable
    },
    "staff_absenteeism": {
        "id": "staff_absenteeism",
        "name": "Unexpected Staff Sickness & Absenteeism",
        "description": "Sudden 30% teller shortage during normal business hours with unchanged demand.",
        "demand_multiplier": 1.0,
        "staff_absence_pct": 30.0,
        "counter_loss": 2,
        "deflection_delta_pct": 0.0,
    },
    "atm_kiosk_outage": {
        "id": "atm_kiosk_outage",
        "name": "ATM & Self-Service Kiosk Network Outage",
        "description": "Lobby machines offline. 100% of passbook and cash transactions forced onto counter tellers.",
        "demand_multiplier": 1.30,
        "staff_absence_pct": 0.0,
        "counter_loss": 0,
        "deflection_delta_pct": -90.0,  # Digital deflection collapsed
    },
    "loan_advisory_surge": {
        "id": "loan_advisory_surge",
        "name": "Promotional Interest-Rate & Mortgage Surge",
        "description": "Surge in high-duration loan and wealth advisory visits (average desk duration +40%).",
        "demand_multiplier": 1.25,
        "staff_absence_pct": 0.0,
        "counter_loss": 0,
        "deflection_delta_pct": 0.0,
        "avg_service_mins_multiplier": 1.40,
    },
}


class BankingScenarioSimulator:
    """
    Simulates operational stress scenarios and calculates rigorous BEFORE vs. AFTER comparisons.
    """

    def __init__(self):
        self.optimizer = StaffCounterOptimizer()
        self.queue_simulator = BranchQueueSimulator(random_seed=42)

    def run_scenario(
        self,
        scenario_key: str,
        active_staff: List[Dict[str, Any]],
        available_counters: int,
        base_hourly_arrivals: int = 35,
        base_service_demands: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a complete stress scenario simulation:
        1. Evaluates baseline operations (pre-shock).
        2. Applies scenario perturbation (demand multiplier, staff absence, machine outages).
        3. Optimizes staff allocation on post-shock conditions.
        4. Simulates queue dynamics on post-shock conditions.
        5. Computes delta metrics and evidence-grounded action checklist.
        """
        preset = BANKING_SCENARIO_PRESETS.get(scenario_key)
        if not preset:
            preset = {
                "id": scenario_key,
                "name": "Custom Scenario",
                "description": "Custom operational perturbation.",
                "demand_multiplier": 1.20,
                "staff_absence_pct": 10.0,
                "counter_loss": 1,
                "deflection_delta_pct": 0.0,
            }

        demands = base_service_demands or {
            "Cash Deposit/Withdrawal": 12,
            "Account Services & KYC": 8,
            "Passbook / Statement Printing": 6,
            "Loan & Mortgage Advisory": 4,
            "Card Services & Pin Reset": 3,
            "Forex & Trade Finance": 2,
        }

        # -------------------------------------------------------------
        # 1. Baseline Pre-Shock Evaluation
        # -------------------------------------------------------------
        base_opt = self.optimizer.optimize_allocations(
            active_staff=active_staff,
            service_demands=demands,
            available_counters=available_counters,
        )
        base_sim = self.queue_simulator.run_simulation(
            base_hourly_arrivals=base_hourly_arrivals,
            active_counters=base_opt["allocated_counters"],
            avg_service_mins=8.0,
            digital_deflection_pct=25.0,
            duration_hours=6,
            replications=3,
        )

        # -------------------------------------------------------------
        # 2. Apply Scenario Shock Parameters
        # -------------------------------------------------------------
        shocked_arrivals = int(round(base_hourly_arrivals * preset.get("demand_multiplier", 1.0)))
        service_mult = preset.get("avg_service_mins_multiplier", 1.0)
        shocked_service_mins = round(8.0 * service_mult, 1)

        # Staff reduction
        absence_pct = preset.get("staff_absence_pct", 0.0)
        remaining_staff_count = max(1, int(round(len(active_staff) * (1.0 - absence_pct / 100.0))))
        shocked_staff = active_staff[:remaining_staff_count]

        # Counter reduction
        counter_loss = preset.get("counter_loss", 0)
        shocked_counters = max(1, available_counters - counter_loss)

        # Deflection shift
        deflection_delta = preset.get("deflection_delta_pct", 0.0)
        shocked_deflection = max(2.0, 25.0 + deflection_delta)

        # Shocked demands
        shocked_demands = {
            s: max(1, int(round(dem * preset.get("demand_multiplier", 1.0))))
            for s, dem in demands.items()
        }

        # -------------------------------------------------------------
        # 3. Post-Shock Optimization & Queue Simulation
        # -------------------------------------------------------------
        shocked_opt = self.optimizer.optimize_allocations(
            active_staff=shocked_staff,
            service_demands=shocked_demands,
            available_counters=shocked_counters,
        )

        shocked_sim = self.queue_simulator.run_simulation(
            base_hourly_arrivals=shocked_arrivals,
            active_counters=shocked_opt["allocated_counters"],
            avg_service_mins=shocked_service_mins,
            digital_deflection_pct=shocked_deflection,
            duration_hours=6,
            replications=3,
        )

        # -------------------------------------------------------------
        # 4. Construct Delta Comparison
        # -------------------------------------------------------------
        wait_delta = round(shocked_sim["avg_wait_minutes"] - base_sim["avg_wait_minutes"], 1)
        breach_delta = round(shocked_sim["sla_breach_rate_pct"] - base_sim["sla_breach_rate_pct"], 1)
        abandon_delta = shocked_sim["total_customers_abandoned"] - base_sim["total_customers_abandoned"]

        # Action Recommendations
        actions = []
        if shocked_sim["avg_wait_minutes"] > 15.0:
            actions.append(f"Deploy emergency greeter to triage customers at door and enforce kiosk deflection.")
        if shocked_opt["unassigned_buffer_staff"] == 0 and shocked_sim["sla_breach_rate_pct"] > 20.0:
            actions.append("Authorize 2 hours of overtime flex or call in part-time teller reserve.")
        if preset.get("id") == "atm_kiosk_outage":
            actions.append("Place high-priority maintenance ticket with ATM service vendor for immediate dispatch.")
        actions.append(f"Implement staggered break schedule to keep {shocked_opt['allocated_counters']} counters operational.")

        return {
            "scenario": preset,
            "baseline": {
                "hourly_arrivals": base_hourly_arrivals,
                "active_staff": len(active_staff),
                "active_counters": base_opt["allocated_counters"],
                "avg_wait_minutes": base_sim["avg_wait_minutes"],
                "p90_wait_minutes": base_sim["p90_wait_minutes"],
                "sla_breach_rate_pct": base_sim["sla_breach_rate_pct"],
                "customers_abandoned": base_sim["total_customers_abandoned"],
                "branch_utilization_pct": base_opt["projected_branch_utilization_pct"],
            },
            "post_shock": {
                "hourly_arrivals": shocked_arrivals,
                "active_staff": len(shocked_staff),
                "active_counters": shocked_opt["allocated_counters"],
                "avg_wait_minutes": shocked_sim["avg_wait_minutes"],
                "p90_wait_minutes": shocked_sim["p90_wait_minutes"],
                "sla_breach_rate_pct": shocked_sim["sla_breach_rate_pct"],
                "customers_abandoned": shocked_sim["total_customers_abandoned"],
                "branch_utilization_pct": shocked_opt["projected_branch_utilization_pct"],
            },
            "operational_impact": {
                "wait_time_delta_mins": wait_delta,
                "sla_breach_rate_delta_pct": breach_delta,
                "abandonment_delta_count": abandon_delta,
                "risk_severity": "CRITICAL" if wait_delta > 10.0 or breach_delta > 25.0 else ("MODERATE" if wait_delta > 4.0 else "LOW"),
            },
            "post_shock_optimization": shocked_opt,
            "recommended_actions": actions,
        }

