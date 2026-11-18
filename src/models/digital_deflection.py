"""
Digital Deflection & Smart Triage Engine.
Identifies in-person visits that can be diverted to self-service kiosks, ATMs, CDMs, or mobile banking,
and computes branch-wide and regional cost/time ROI metrics.
"""
from src.config import SERVICE_CATEGORIES

CHANNEL_METADATA = {
    "Cash Deposit Machine (CDM) / ATM": {
        "device_type": "Automated Cash Machine",
        "avg_tx_duration_mins": 2.5,
        "availability": "24/7 Lobby Kiosks",
        "greeter_pitch": "Guide customer to Cash Deposit Machine. Instant deposit with zero queue wait."
    },
    "Mobile App / Video KYC Kiosk": {
        "device_type": "Digital Tablet / Kiosk",
        "avg_tx_duration_mins": 3.0,
        "availability": "Branch Kiosk / Customer Phone",
        "greeter_pitch": "Assist with fast Video KYC or App onboarding for instant address/KYC update."
    },
    "Self-Service Passbook Kiosk": {
        "device_type": "Optical Passbook Printer",
        "avg_tx_duration_mins": 1.5,
        "availability": "Lobby Printer",
        "greeter_pitch": "Direct customer to optical passbook printer. Barcode scan prints instantly in 90 seconds."
    },
    "Mobile Banking App / NetBanking": {
        "device_type": "Mobile Banking",
        "avg_tx_duration_mins": 2.0,
        "availability": "Customer Smartphone",
        "greeter_pitch": "Assist customer in setting up PIN reset or card controls directly on mobile banking."
    }
}

class DigitalDeflectionEngine:
    def __init__(self):
        self.deflection_rules = SERVICE_CATEGORIES

    def evaluate_request(self, service_category: str, customer_query: str = "") -> dict:
        """
        Evaluates whether a customer request is eligible for digital self-service deflection.
        Returns redirection advice, estimated time saved, target channel, and floor greeter checklist.
        """
        meta = self.deflection_rules.get(service_category, {})
        eligible = meta.get("digital_eligible", False)
        channel = meta.get("digital_channel", "In-Person Counter")
        difficulty = meta.get("digital_deflection_difficulty", "High")
        avg_service = meta.get("avg_service_mins", 10.0)
        
        channel_info = CHANNEL_METADATA.get(channel, {
            "device_type": "Specialist Teller Desk",
            "avg_tx_duration_mins": avg_service,
            "availability": "Counter Hours",
            "greeter_pitch": "Direct customer to specialist counter with pre-verification checklist."
        })
        
        if eligible:
            action_text = f"📲 Guide customer to {channel}. Immediate self-service with 0 queue wait."
            guidance_steps = [
                f"1. Inform customer that '{service_category}' can be completed instantly on {channel}.",
                f"2. {channel_info['greeter_pitch']}",
                "3. Offer hands-on floor greeter demonstration if the customer is a first-time user.",
                "4. Issue a Fast-Pass digital ticket if in-person teller verification is strictly insisted."
            ]
        else:
            action_text = "🏛️ In-Person Specialist verification required. Route to dedicated counter."
            guidance_steps = [
                "1. Direct customer to the dedicated specialist desk.",
                "2. Pre-screen physical IDs / supporting documents while waiting to minimize desk handling time.",
                "3. Ensure priority token is issued for Senior Citizen or VIP/HNI clients."
            ]

        return {
            "is_deflectable": eligible,
            "target_channel": channel,
            "channel_details": channel_info,
            "difficulty": difficulty,
            "time_saved_minutes": avg_service if eligible else 0.0,
            "action_recommendation": action_text,
            "greeter_checklist": guidance_steps
        }

    def compute_branch_deflection_metrics(self, token_records: list) -> dict:
        """
        Calculates branch-wide Digital Deflection Index (DDI), deflected transaction mix,
        and potential teller labor cost savings.
        """
        total_visits = len(token_records)
        if total_visits == 0:
            return {
                "total_visits": 0,
                "deflectable_visits": 0,
                "deflection_rate_pct": 0,
                "hours_saved": 0,
                "estimated_cost_savings_usd": 0,
                "channel_breakdown": {}
            }
            
        deflected = [t for t in token_records if t.get("digital_deflectable") == 1 or t.get("digital_deflectable") is True]
        deflection_count = len(deflected)
        deflection_rate = (deflection_count / total_visits) * 100
        
        total_minutes_saved = sum(t.get("service_duration_minutes", 8.0) for t in deflected)
        hours_saved = total_minutes_saved / 60.0
        cost_savings_usd = hours_saved * 32.50  # Average blended teller operational hourly rate

        # Channel breakdown
        channel_counts = {}
        for t in deflected:
            ch = t.get("deflection_target_channel", "Self-Service Kiosks")
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        return {
            "total_visits": total_visits,
            "deflectable_visits": deflection_count,
            "deflection_rate_pct": round(deflection_rate, 1),
            "hours_saved": round(hours_saved, 1),
            "estimated_cost_savings_usd": round(cost_savings_usd, 2),
            "channel_breakdown": channel_counts
        }
