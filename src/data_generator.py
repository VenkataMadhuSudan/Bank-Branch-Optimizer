"""
Synthetic Banking Operational Data Generator.
Uses Python standard library & numpy to generate realistic multi-branch banking logs.
"""
import random
import csv
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from src.config import SERVICE_CATEGORIES, CUSTOMER_SEGMENTS, BRANCH_NETWORK, RAW_DATA_DIR

np.random.seed(42)
random.seed(42)

STAFF_NAMES = [
    "Sarah Jenkins", "Michael Chang", "Priya Sharma", "David Miller",
    "Elena Rostova", "Marcus Vance", "Anita Desai", "Carlos Gomez",
    "Fatima Al-Sayed", "James O'Connor", "Aisha Khan", "Robert Chen"
]

FEEDBACK_TEMPLATES = {
    "positive": [
        "Very fast service today at counter {counter}! Staff was very helpful.",
        "Smooth experience with {service}, barely waited 5 minutes.",
        "Excellent support by {staff}. Solved my account issue quickly.",
        "Kiosk made passbook printing effortless. Happy with the branch.",
        "Quick turnaround on my loan query, clear explanation from advisor."
    ],
    "negative_wait": [
        "Waited over 40 minutes for simple cash deposit! Only 2 counters were open.",
        "Long queue during lunch hour. Staff seemed overwhelmed.",
        "Terrible wait time for KYC update. Could have done this on the app if guided.",
        "Waited 35 mins just for a statement print. Why no one guided me to the kiosk?",
        "Heavy crowd at {branch}. Needs better queue management and extra counters."
    ],
    "digital_deflection_opportunity": [
        "I only came to update my mobile number and check balance, waited 25 mins.",
        "Came for card PIN reset, learned later I could do it at the ATM outside.",
        "Waited in line just to deposit a small cheque. Self-service machine was empty!",
        "Branch visit was just to verify KYC documents, hope they enable video KYC soon."
    ]
}

def write_csv(filepath, rows, fieldnames):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def generate_all_data(days=14, records_per_day=300):
    print("Generating synthetic banking datasets...")
    
    # 1. Staff Rosters
    staff_records = []
    service_keys = list(SERVICE_CATEGORIES.keys())
    
    staff_id_counter = 101
    for branch in BRANCH_NETWORK:
        num_staff = branch["total_counters"] + 2
        for i in range(num_staff):
            name = random.choice(STAFF_NAMES) + f" ({branch['branch_id']}-{i+1})"
            primary_skill = random.choice(service_keys)
            secondary_skills = random.sample([s for s in service_keys if s != primary_skill], k=random.randint(1, 3))
            efficiency = round(random.uniform(0.85, 1.25), 2)
            
            staff_records.append({
                "staff_id": f"EMP_{staff_id_counter}",
                "staff_name": name,
                "branch_id": branch["branch_id"],
                "primary_skill": primary_skill,
                "secondary_skills": ";".join(secondary_skills),
                "shift_start": "09:00",
                "shift_end": "17:30",
                "efficiency_factor": efficiency,
                "preferred_counter": (i % branch["total_counters"]) + 1
            })
            staff_id_counter += 1
            
    write_csv(
        RAW_DATA_DIR / "staff_rosters.csv",
        staff_records,
        ["staff_id", "staff_name", "branch_id", "primary_skill", "secondary_skills", "shift_start", "shift_end", "efficiency_factor", "preferred_counter"]
    )
    print(f" Saved staff_rosters.csv ({len(staff_records)} records)")

    # 2. Branch Metadata
    write_csv(
        RAW_DATA_DIR / "branch_metadata.csv",
        BRANCH_NETWORK,
        ["branch_id", "name", "cluster", "total_counters", "peak_window"]
    )
    print(f" Saved branch_metadata.csv ({len(BRANCH_NETWORK)} branches)")

    # 3. Queue & Token Logs
    token_records = []
    feedback_records = []
    appointment_records = []
    
    start_date = datetime.now() - timedelta(days=days)
    
    token_counter = 10001
    apt_counter = 5001
    fb_counter = 20001
    
    for d in range(days):
        current_date = start_date + timedelta(days=d)
        is_weekend = current_date.weekday() >= 5
        if is_weekend:
            continue
            
        is_month_start_end = current_date.day in [1, 2, 3, 28, 29, 30, 31]
        
        for branch in BRANCH_NETWORK:
            daily_volume = int(records_per_day * random.uniform(0.7, 1.4))
            if is_month_start_end:
                daily_volume = int(daily_volume * 1.35)
                
            active_staff = [s for s in staff_records if s["branch_id"] == branch["branch_id"]]
            
            for _ in range(daily_volume // len(BRANCH_NETWORK)):
                token_counter += 1
                
                hour_choice = random.choices(
                    population=list(range(9, 17)),
                    weights=[5, 12, 22, 25, 18, 14, 8, 3],
                    k=1
                )[0]
                minute_choice = random.randint(0, 59)
                second_choice = random.randint(0, 59)
                arrival_time = current_date.replace(hour=hour_choice, minute=minute_choice, second=second_choice)
                
                service = random.choices(
                    population=list(SERVICE_CATEGORIES.keys()),
                    weights=[32, 22, 14, 10, 8, 9, 5],
                    k=1
                )[0]
                service_meta = SERVICE_CATEGORIES[service]
                
                segment = random.choices(
                    population=list(CUSTOMER_SEGMENTS.keys()),
                    weights=[65, 15, 8, 12],
                    k=1
                )[0]
                seg_meta = CUSTOMER_SEGMENTS[segment]
                
                is_appointment = random.random() < 0.15
                if is_appointment:
                    apt_counter += 1
                    appointment_records.append({
                        "appointment_id": f"APT_{apt_counter}",
                        "branch_id": branch["branch_id"],
                        "customer_segment": segment,
                        "service_category": service,
                        "scheduled_time": arrival_time.strftime("%Y-%m-%d %H:%M"),
                        "status": "Completed"
                    })
                
                is_peak_hour = hour_choice in [11, 12, 13, 14]
                congestion_mult = 1.6 if is_peak_hour else 0.9
                if is_month_start_end:
                    congestion_mult *= 1.3
                    
                base_wait = service_meta["sla_wait_mins"] * 0.7
                random_noise = np.random.exponential(scale=4.0)
                actual_wait = max(1.0, (base_wait * congestion_mult + random_noise) / seg_meta["priority_weight"])
                
                assigned_agent = random.choice(active_staff)
                agent_eff = assigned_agent["efficiency_factor"]
                base_service_time = service_meta["avg_service_mins"]
                actual_service_time = max(1.5, np.random.normal(loc=base_service_time, scale=1.5) / agent_eff)
                
                service_start = arrival_time + timedelta(minutes=actual_wait)
                service_end = service_start + timedelta(minutes=actual_service_time)
                
                can_deflect = service_meta["digital_eligible"] and (random.random() < 0.65)
                
                sla_threshold = service_meta["sla_wait_mins"]
                if actual_wait <= sla_threshold:
                    sat_score = random.choices([4, 5], weights=[35, 65])[0]
                elif actual_wait <= sla_threshold * 1.5:
                    sat_score = random.choices([3, 4], weights=[60, 40])[0]
                elif actual_wait <= sla_threshold * 2.2:
                    sat_score = random.choices([2, 3], weights=[70, 30])[0]
                else:
                    sat_score = random.choices([1, 2], weights=[80, 20])[0]
                    
                counter_num = assigned_agent["preferred_counter"]
                
                token_records.append({
                    "token_id": f"TKN_{token_counter}",
                    "branch_id": branch["branch_id"],
                    "branch_name": branch["name"],
                    "arrival_timestamp": arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "service_start_timestamp": service_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "service_end_timestamp": service_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "service_category": service,
                    "customer_segment": segment,
                    "is_appointment": 1 if is_appointment else 0,
                    "counter_id": f"C_{counter_num}",
                    "staff_id": assigned_agent["staff_id"],
                    "staff_name": assigned_agent["staff_name"],
                    "wait_time_minutes": round(float(actual_wait), 2),
                    "service_duration_minutes": round(float(actual_service_time), 2),
                    "sla_wait_minutes": float(service_meta["sla_wait_mins"]),
                    "sla_breached": 1 if actual_wait > service_meta["sla_wait_mins"] else 0,
                    "digital_deflectable": 1 if can_deflect else 0,
                    "deflection_target_channel": service_meta["digital_channel"] if can_deflect else "In-Person Required",
                    "satisfaction_score": sat_score
                })
                
                if random.random() < 0.20:
                    fb_counter += 1
                    if sat_score >= 4:
                        template = random.choice(FEEDBACK_TEMPLATES["positive"])
                    elif can_deflect and random.random() < 0.5:
                        template = random.choice(FEEDBACK_TEMPLATES["digital_deflection_opportunity"])
                    else:
                        template = random.choice(FEEDBACK_TEMPLATES["negative_wait"])
                        
                    comment = template.format(
                        counter=f"C_{counter_num}",
                        service=service,
                        staff=assigned_agent["staff_name"],
                        branch=branch["name"]
                    )
                    
                    feedback_records.append({
                        "feedback_id": f"FB_{fb_counter}",
                        "token_id": f"TKN_{token_counter}",
                        "branch_id": branch["branch_id"],
                        "timestamp": service_end.strftime("%Y-%m-%d %H:%M:%S"),
                        "service_category": service,
                        "rating": sat_score,
                        "feedback_text": comment
                    })

    write_csv(
        RAW_DATA_DIR / "branch_queue_logs.csv",
        token_records,
        [
            "token_id", "branch_id", "branch_name", "arrival_timestamp",
            "service_start_timestamp", "service_end_timestamp", "service_category",
            "customer_segment", "is_appointment", "counter_id", "staff_id",
            "staff_name", "wait_time_minutes", "service_duration_minutes",
            "sla_wait_minutes", "sla_breached", "digital_deflectable",
            "deflection_target_channel", "satisfaction_score"
        ]
    )
    print(f" Saved branch_queue_logs.csv ({len(token_records)} records)")
    
    write_csv(
        RAW_DATA_DIR / "appointments.csv",
        appointment_records,
        ["appointment_id", "branch_id", "customer_segment", "service_category", "scheduled_time", "status"]
    )
    print(f" Saved appointments.csv ({len(appointment_records)} records)")
    
    write_csv(
        RAW_DATA_DIR / "customer_feedback.csv",
        feedback_records,
        ["feedback_id", "token_id", "branch_id", "timestamp", "service_category", "rating", "feedback_text"]
    )
    print(f" Saved customer_feedback.csv ({len(feedback_records)} records)")

if __name__ == "__main__":
    generate_all_data(days=14, records_per_day=300)
