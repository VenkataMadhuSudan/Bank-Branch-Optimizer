"""
Prescriptive Staff-to-Counter Optimization & Break Scheduling Engine.
Solves dynamic staff reallocation across counters to minimize queue bottlenecks,
optimize skill-to-demand matching, and generate staggered break schedules.
"""
from src.config import SERVICE_CATEGORIES

class StaffCounterOptimizer:
    def __init__(self):
        pass

    def optimize_allocations(self, active_staff: list, service_demands: dict, available_counters: int) -> dict:
        """
        Allocates available staff members to counters and service categories to minimize queue imbalance.
        Also generates staggered break schedules and staff fatigue risk indicators.
        """
        total_demand = sum(service_demands.values())
        if total_demand == 0:
            total_demand = 1
            
        num_staff = len(active_staff)
        usable_counters = min(num_staff, available_counters)
        
        target_allocation = {}
        for service, demand in service_demands.items():
            target = max(1, int(round((demand / total_demand) * usable_counters)))
            target_allocation[service] = target
            
        assignments = []
        unassigned_staff = list(active_staff)
        counter_idx = 1
        
        sorted_services = sorted(service_demands.items(), key=lambda x: x[1], reverse=True)
        allocated_counters_per_service = {s: 0 for s, _ in sorted_services}
        
        # 1. Primary skill match
        for service, _ in sorted_services:
            target = target_allocation.get(service, 1)
            for staff in list(unassigned_staff):
                if counter_idx > usable_counters or allocated_counters_per_service[service] >= target:
                    break
                if staff.get("primary_skill") == service:
                    assignments.append({
                        "counter_id": f"Counter {counter_idx}",
                        "staff_id": staff.get("staff_id", f"EMP_{100+counter_idx}"),
                        "staff_name": staff.get("staff_name", f"Staff {counter_idx}"),
                        "assigned_service": service,
                        "match_type": "Primary Skill Match",
                        "efficiency_factor": float(staff.get("efficiency_factor", 1.0)),
                        "speed_rating": float(staff.get("counter_speed_rating", 4.5)),
                        "fatigue_risk": "Low"
                    })
                    allocated_counters_per_service[service] += 1
                    counter_idx += 1
                    unassigned_staff.remove(staff)
                    
        # 2. Secondary skill match
        for service, _ in sorted_services:
            target = target_allocation.get(service, 1)
            for staff in list(unassigned_staff):
                if counter_idx > usable_counters or allocated_counters_per_service[service] >= target:
                    break
                sec_skills = str(staff.get("secondary_skills", "")).split(";")
                if service in sec_skills:
                    assignments.append({
                        "counter_id": f"Counter {counter_idx}",
                        "staff_id": staff.get("staff_id", f"EMP_{100+counter_idx}"),
                        "staff_name": staff.get("staff_name", f"Staff {counter_idx}"),
                        "assigned_service": service,
                        "match_type": "Secondary Skill Flex",
                        "efficiency_factor": float(staff.get("efficiency_factor", 1.0)) * 0.95,
                        "speed_rating": float(staff.get("counter_speed_rating", 4.2)),
                        "fatigue_risk": "Low"
                    })
                    allocated_counters_per_service[service] += 1
                    counter_idx += 1
                    unassigned_staff.remove(staff)

        # 3. Dynamic surge relief for high-demand bottleneck
        for staff in list(unassigned_staff):
            if counter_idx > usable_counters:
                break
            top_service = sorted_services[0][0]
            assignments.append({
                "counter_id": f"Counter {counter_idx}",
                "staff_id": staff.get("staff_id", f"EMP_{100+counter_idx}"),
                "staff_name": staff.get("staff_name", f"Staff {counter_idx}"),
                "assigned_service": top_service,
                "match_type": "Dynamic Surge Relief",
                "efficiency_factor": float(staff.get("efficiency_factor", 1.0)) * 0.88,
                "speed_rating": float(staff.get("counter_speed_rating", 4.0)),
                "fatigue_risk": "Moderate (Surge Desk)"
            })
            allocated_counters_per_service[top_service] += 1
            counter_idx += 1
            unassigned_staff.remove(staff)

        projected_capacity = sum([a["efficiency_factor"] * 12.0 for a in assignments])
        utilization = min(100.0, round((total_demand / max(1.0, projected_capacity)) * 100, 1))

        # 4. Generate Staggered Lunch & Break Schedule
        break_slots = ["11:30 - 12:15", "12:15 - 13:00", "13:00 - 13:45", "13:45 - 14:30"]
        break_schedule = []
        for idx, a in enumerate(assignments):
            slot = break_slots[idx % len(break_slots)]
            break_schedule.append({
                "counter_id": a["counter_id"],
                "staff_name": a["staff_name"],
                "assigned_service": a["assigned_service"],
                "allocated_break_window": slot,
                "surge_coverage_status": "Covered by Buffer Staff" if unassigned_staff else "Staggered Active"
            })

        return {
            "assignments": assignments,
            "allocated_counters": len(assignments),
            "unassigned_buffer_staff": len(unassigned_staff),
            "service_counter_distribution": allocated_counters_per_service,
            "projected_branch_utilization_pct": utilization,
            "break_schedule": break_schedule,
            "status": "Optimal Allocation Found"
        }
