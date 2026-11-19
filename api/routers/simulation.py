"""
Discrete-Event Queue Simulation & Erlang-C Endpoints.
"""
from fastapi import APIRouter, Depends, Query
from api.schemas import SimulationRequest
from src.optimization.queue_simulator import BranchQueueSimulator, erlang_c_waiting_time

router = APIRouter(prefix="/api/simulation", tags=["Queue Simulation"])

_SIMULATOR = BranchQueueSimulator()


@router.post("/run")
def run_queue_simulation(req: SimulationRequest):
    """
    Runs multi-replication discrete-event Monte Carlo simulation for customer queues
    with lognormal handling times, priority classes, and abandonment dynamics.
    """
    return _SIMULATOR.run_simulation(
        base_hourly_arrivals=req.base_hourly_arrivals,
        active_counters=req.active_counters,
        avg_service_mins=req.avg_service_mins,
        digital_deflection_pct=req.digital_deflection_pct,
        sla_threshold_mins=req.sla_threshold_mins,
        duration_hours=req.duration_hours,
        replications=req.replications,
        random_seed=req.random_seed,
    )


@router.get("/erlang-c")
def get_erlang_c_benchmark(
    arrival_rate: float = Query(30.0, description="Customer arrival rate (cust/hr)"),
    service_rate: float = Query(7.5, description="Service rate per server (cust/hr)"),
    num_servers: int = Query(4, description="Number of active teller counters"),
):
    """Calculates theoretical M/M/c queue delay using Erlang-C formula."""
    wait_mins = erlang_c_waiting_time(arrival_rate, service_rate, num_servers)
    rho = round(arrival_rate / max(0.1, num_servers * service_rate), 3)
    return {
        "arrival_rate_lambda": arrival_rate,
        "service_rate_mu": service_rate,
        "active_counters_c": num_servers,
        "traffic_intensity_rho": rho,
        "is_stable_queue": rho < 1.0,
        "erlang_expected_wait_minutes": round(wait_mins, 2) if wait_mins is not None else None,
    }

