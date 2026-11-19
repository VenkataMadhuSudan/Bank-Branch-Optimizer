"""
Unit and Rigor Tests for Discrete-Event Queue Simulation, Two-Stage Stochastic Optimization, and Stress Scenarios.
"""
import pytest
from src.optimization.queue_simulator import BranchQueueSimulator, erlang_c_waiting_time
from src.optimization.stochastic_optimizer import TwoStageStochasticOptimizer
from src.optimization.scenario_simulator import BankingScenarioSimulator, BANKING_SCENARIO_PRESETS


def test_erlang_c_formula_calculation():
    """Verifies that theoretical Erlang-C waiting time matches standard queueing theory."""
    # lambda = 20 cust/hr, mu = 10 cust/hr per server (6 mins/cust), c = 3 servers
    # rho = 20 / 30 = 0.667 < 1.0 (stable queue)
    wait_mins = erlang_c_waiting_time(arrival_rate=20.0, service_rate=10.0, num_servers=3)
    assert wait_mins is not None
    assert 0.0 < wait_mins < 15.0

    # Unstable queue (rho >= 1.0) returns None
    unstable_wait = erlang_c_waiting_time(arrival_rate=40.0, service_rate=10.0, num_servers=3)
    assert unstable_wait is None


def test_queue_simulator_reproducibility():
    """Verifies that explicit random seed produces deterministic, reproducible simulation runs."""
    sim1 = BranchQueueSimulator(random_seed=123)
    res1 = sim1.run_simulation(base_hourly_arrivals=30, active_counters=4, replications=2, random_seed=123)

    sim2 = BranchQueueSimulator(random_seed=123)
    res2 = sim2.run_simulation(base_hourly_arrivals=30, active_counters=4, replications=2, random_seed=123)

    assert res1["avg_wait_minutes"] == res2["avg_wait_minutes"]
    assert res1["total_customers_served"] == res2["total_customers_served"]
    assert res1["p90_wait_minutes"] == res2["p90_wait_minutes"]


def test_queue_simulator_metrics():
    """Verifies that discrete-event simulation generates complete statistical metrics."""
    sim = BranchQueueSimulator(random_seed=42)
    res = sim.run_simulation(
        base_hourly_arrivals=35,
        active_counters=4,
        avg_service_mins=7.5,
        digital_deflection_pct=20.0,
        replications=3
    )

    assert res["total_customers_served"] > 0
    assert res["avg_wait_minutes"] >= 0.0
    assert res["p90_wait_minutes"] >= res["avg_wait_minutes"]
    assert len(res["ci_95_wait_minutes"]) == 2
    assert res["ci_95_wait_minutes"][0] <= res["avg_wait_minutes"] <= res["ci_95_wait_minutes"][1]
    assert 0.0 <= res["sla_breach_rate_pct"] <= 100.0
    assert len(res["hourly_progression"]) == 6


def test_two_stage_stochastic_optimizer():
    """Verifies two-stage stochastic optimization under demand uncertainty."""
    optimizer = TwoStageStochasticOptimizer(time_limit_seconds=3.0)
    staff = [
        {"staff_id": f"EMP_{i}", "staff_name": f"Staff {i}", "primary_skill": "Cash Deposit/Withdrawal"}
        for i in range(1, 9)
    ]
    res = optimizer.solve(
        active_staff=staff,
        available_counters=6,
        base_demand=35,
        conformal_halfwidth=6.0
    )

    assert res["solver_status"] in ("OPTIMAL", "FEASIBLE", "HEURISTIC_FALLBACK")
    assert res["stage_1_base_counters"] > 0
    assert res["stage_1_base_counters"] <= 6
    assert res["expected_hourly_cost_usd"] > 0.0
    assert "scenario_evaluations" in res


def test_stress_scenario_simulator():
    """Verifies that scenario simulator runs month-end rush and computes BEFORE vs AFTER comparison."""
    stress_sim = BankingScenarioSimulator()
    staff = [
        {"staff_id": f"EMP_{i}", "staff_name": f"Staff {i}", "primary_skill": "Cash Deposit/Withdrawal"}
        for i in range(1, 7)
    ]
    res = stress_sim.run_scenario(
        scenario_key="month_end_rush",
        active_staff=staff,
        available_counters=6,
        base_hourly_arrivals=30
    )

    assert "baseline" in res
    assert "post_shock" in res
    assert "operational_impact" in res
    assert res["post_shock"]["hourly_arrivals"] > res["baseline"]["hourly_arrivals"]
    assert "recommended_actions" in res
    assert len(res["recommended_actions"]) > 0

