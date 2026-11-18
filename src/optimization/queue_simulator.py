"""
Discrete-Event "What-If" Queue & Capacity Simulator.
Simulates minute-by-minute branch arrivals, token queues, counter processing, and SLA breaches using NumPy.
"""
import numpy as np

class BranchQueueSimulator:
    def __init__(self):
        pass

    def run_simulation(
        self,
        base_hourly_arrivals: int = 40,
        active_counters: int = 4,
        avg_service_mins: float = 8.0,
        digital_deflection_pct: float = 20.0,
        sla_threshold_mins: float = 15.0,
        duration_hours: int = 6
    ) -> dict:
        """
        Runs a discrete-event Monte Carlo simulation for queue dynamics over a shift.
        """
        np.random.seed(42)
        total_minutes = duration_hours * 60
        
        effective_hourly_arrivals = base_hourly_arrivals * (1.0 - (digital_deflection_pct / 100.0))
        arrival_rate_per_min = effective_hourly_arrivals / 60.0
        
        counter_free_time = np.zeros(active_counters)
        
        customers = []
        current_time = 0.0
        cust_id = 1
        
        while current_time < total_minutes:
            inter_arrival = np.random.exponential(1.0 / max(0.01, arrival_rate_per_min))
            current_time += inter_arrival
            if current_time >= total_minutes:
                break
                
            service_dur = max(1.5, np.random.normal(avg_service_mins, scale=2.0))
            
            earliest_counter_idx = int(np.argmin(counter_free_time))
            earliest_counter_avail = counter_free_time[earliest_counter_idx]
            
            if earliest_counter_avail <= current_time:
                start_service = current_time
                wait_time = 0.0
            else:
                start_service = earliest_counter_avail
                wait_time = start_service - current_time
                
            end_service = start_service + service_dur
            counter_free_time[earliest_counter_idx] = end_service
            
            customers.append({
                "cust_id": cust_id,
                "arrival_time": round(current_time, 1),
                "wait_time": round(wait_time, 1),
                "service_duration": round(service_dur, 1),
                "hour_bucket": int(current_time // 60) + 1,
                "is_sla_breached": 1 if wait_time > sla_threshold_mins else 0
            })
            cust_id += 1
            
        if not customers:
            return {
                "total_customers_served": 0,
                "avg_wait_minutes": 0,
                "p90_wait_minutes": 0,
                "max_wait_minutes": 0,
                "sla_breach_count": 0,
                "sla_breach_rate_pct": 0,
                "hourly_progression": []
            }
            
        waits = [c["wait_time"] for c in customers]
        breaches = [c["is_sla_breached"] for c in customers]
        
        total_cust = len(customers)
        avg_wait = float(np.mean(waits))
        p90_wait = float(np.percentile(waits, 90))
        max_wait = float(np.max(waits))
        sla_breach_count = int(np.sum(breaches))
        sla_breach_rate = (sla_breach_count / total_cust) * 100
        
        # Hourly progression
        hourly_prog = []
        for h in range(1, duration_hours + 1):
            h_custs = [c for c in customers if c["hour_bucket"] == h]
            if h_custs:
                h_avg = float(np.mean([c["wait_time"] for c in h_custs]))
                h_breaches = int(sum(c["is_sla_breached"] for c in h_custs))
            else:
                h_avg = 0.0
                h_breaches = 0
            hourly_prog.append({
                "hour_bucket": h,
                "customers_served": len(h_custs),
                "avg_wait_mins": round(h_avg, 1),
                "sla_breaches": h_breaches
            })

        return {
            "total_customers_served": total_cust,
            "avg_wait_minutes": round(avg_wait, 1),
            "p90_wait_minutes": round(p90_wait, 1),
            "max_wait_minutes": round(max_wait, 1),
            "sla_breach_count": sla_breach_count,
            "sla_breach_rate_pct": round(sla_breach_rate, 1),
            "hourly_progression": hourly_prog
        }
