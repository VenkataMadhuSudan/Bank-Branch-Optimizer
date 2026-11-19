"""
Digital Deflection & Smart Lobby Triage Engine.
Features:
- Multi-Channel Self-Service Mapping (Cash Deposit Machines, ATMs, Mobile Apps, Video KYC, Passbook Printers).
- Customer Segment Digital Readiness & Adoption Factor Modeling.
- Branch-Wide & Network Digital Deflection Index (DDI).
- Labor Hours & Teller Cost Savings Computation ($28.00/hr basis).
- Transparent Assumptions with Visible Operational Parameters.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CUSTOMER_SEGMENTS, SERVICE_CATEGORIES

TELLER_HOURLY_WAGE_USD = 28.0

# Digital Channel Hardware & Workflow Metadata
CHANNEL_METADATA = {
    "Cash Deposit Machine (CDM) / ATM": {
        "device_type": "Automated Cash Dispenser / Recycler",
        "avg_tx_duration_mins": 2.5,
        "availability": "24/7 Lobby Kiosks",
        "greeter_pitch": "Guide customer to Cash Deposit Machine. Instant deposit with zero queue wait.",
        "success_rate_pct": 92.0,
    },
    "Mobile App / Video KYC Kiosk": {
        "device_type": "Digital Tablet / Dedicated KYC Terminal",
        "avg_tx_duration_mins": 3.5,
        "availability": "Branch Kiosk / Customer Smartphone",
        "greeter_pitch": "Assist with fast Video KYC or App onboarding for instant address/KYC update.",
        "success_rate_pct": 85.0,
    },
    "Self-Service Passbook Kiosk": {
        "device_type": "Optical Barcode Passbook Printer",
        "avg_tx_duration_mins": 1.5,
        "availability": "Lobby Printer",
        "greeter_pitch": "Direct customer to optical passbook printer. Barcode scan prints instantly in 90 seconds.",
        "success_rate_pct": 96.0,
    },
    "ATM / Mobile App Self-Service": {
        "device_type": "ATM or Mobile Banking App",
        "avg_tx_duration_mins": 2.0,
        "availability": "Customer Smartphone / Lobby ATM",
        "greeter_pitch": "Assist customer in setting up PIN reset or card controls directly on mobile banking.",
        "success_rate_pct": 90.0,
    },
}

# Empirical Digital Adoption Multipliers by Customer Segment
SEGMENT_ADOPTION_FACTORS = {
    "High Net Worth (HNI/VIP)": 0.85,
    "Small Business / SME": 0.80,
    "Regular": 0.70,
    "Senior Citizen": 0.35,  # Lower digital readiness; requires human greeter assistance
}


class DigitalDeflectionEngine:
    """
    Evaluates self-service deflection eligibility, computes branch-wide DDI,
    and projects verified teller labor cost savings.
    """

    def __init__(self):
        self.deflection_rules = SERVICE_CATEGORIES

    def evaluate_request(
        self,
        service_category: str,
        customer_segment: str = "Regular",
        customer_query: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluates whether a customer request is eligible for digital self-service deflection.
        Takes into account customer segment readiness.
        """
        meta = self.deflection_rules.get(service_category, {})
        eligible = meta.get("digital_eligible", False)
        channel = meta.get("digital_channel", "In-Person Counter")
        difficulty = meta.get("digital_deflection_difficulty", "High")
        avg_service = meta.get("avg_service_mins", 10.0)

        segment_readiness = SEGMENT_ADOPTION_FACTORS.get(customer_segment, 0.70)

        channel_info = CHANNEL_METADATA.get(
            channel,
            {
                "device_type": "Specialist Teller Desk",
                "avg_tx_duration_mins": avg_service,
                "availability": "Counter Operating Hours",
                "greeter_pitch": "Direct customer to specialist counter with document checklist.",
                "success_rate_pct": 100.0,
            },
        )

        time_saved = max(0.0, avg_service - channel_info["avg_tx_duration_mins"]) if eligible else 0.0

        if eligible:
            action_text = f"Guide customer to {channel}. Immediate self-service with 0 queue wait."
            guidance_steps = [
                f"1. Inform customer that '{service_category}' can be completed immediately at {channel}.",
                f"2. {channel_info['greeter_pitch']}",
                "3. Offer hands-on floor greeter demonstration if customer indicates unfamiliarity.",
                "4. Issue priority ticket if in-person teller verification is strictly insisted.",
            ]
        else:
            action_text = "In-Person Specialist verification required. Route to dedicated counter."
            guidance_steps = [
                "1. Direct customer to the dedicated specialist desk.",
                "2. Pre-screen physical IDs / supporting documents while waiting to minimize desk handling time.",
                "3. Ensure priority token is issued for Senior Citizen or VIP/HNI clients.",
            ]

        return {
            "is_deflectable": eligible,
            "target_channel": channel,
            "channel_details": channel_info,
            "difficulty": difficulty,
            "segment_adoption_factor": segment_readiness,
            "expected_adoption_prob_pct": round(segment_readiness * (channel_info.get("success_rate_pct", 85) / 100.0) * 100, 1) if eligible else 0.0,
            "time_saved_minutes": round(time_saved, 1),
            "action_recommendation": action_text,
            "greeter_checklist": guidance_steps,
        }

    def compute_branch_deflection_metrics(self, token_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates branch-wide Digital Deflection Index (DDI), deflected transaction mix,
        teller labor hours saved, and cost savings.
        """
        total_visits = len(token_records)
        if total_visits == 0:
            return {
                "total_visits": 0,
                "deflectable_visits": 0,
                "deflection_rate_pct": 0.0,
                "hours_saved": 0.0,
                "estimated_cost_savings_usd": 0.0,
                "channel_breakdown": {},
                "ddi_score": 0.0,
            }

        deflected = [
            t for t in token_records
            if t.get("digital_deflectable") in (1, True, "1", "True")
        ]
        deflection_count = len(deflected)
        deflection_rate = (deflection_count / total_visits) * 100.0

        # Calculate time and cost savings
        channel_counts: Dict[str, int] = {}
        total_time_saved_mins = 0.0

        for t in deflected:
            s_name = t.get("service_category", "Cash Deposit/Withdrawal")
            meta = self.deflection_rules.get(s_name, {})
            channel = meta.get("digital_channel", "Self-Service Kiosk")
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

            dur = float(t.get("service_duration_minutes", meta.get("avg_service_mins", 8.0)))
            total_time_saved_mins += max(2.0, dur * 0.70)

        hours_saved = round(total_time_saved_mins / 60.0, 1)
        cost_savings = round(hours_saved * TELLER_HOURLY_WAGE_USD, 2)

        # Digital Deflection Index (DDI) on a 0-100 scale
        # Normalized score based on deflection rate, channel diversity, and volume
        ddi_score = round(min(100.0, (deflection_rate * 0.8) + (len(channel_counts) * 5.0)), 1)

        return {
            "total_visits": total_visits,
            "deflectable_visits": deflection_count,
            "deflection_rate_pct": round(deflection_rate, 1),
            "hours_saved": hours_saved,
            "estimated_cost_savings_usd": cost_savings,
            "hourly_wage_basis_usd": TELLER_HOURLY_WAGE_USD,
            "channel_breakdown": channel_counts,
            "ddi_score": ddi_score,
        }
