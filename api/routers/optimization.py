"""
Mathematical Staff Optimization & Operations Research Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from api.schemas import StaffOptimizationRequest, StochasticOptimizationRequest, ScenarioStressRequest
from src.optimization.staff_optimizer import StaffCounterOptimizer
from src.optimization.stochastic_optimizer import TwoStageStochasticOptimizer
from src.optimization.scenario_simulator import BankingScenarioSimulator

router = APIRouter(prefix="/api/optimization", tags=["Mathematical Optimization"])

_STAFF_OPTIMIZER = StaffCounterOptimizer()
_STOCHASTIC_OPTIMIZER = TwoStageStochasticOptimizer()
_SCENARIO_SIMULATOR = BankingScenarioSimulator()


@router.post("/staff")
def optimize_staff_allocation(req: StaffOptimizationRequest):
    """
    Executes Google OR-Tools CP-SAT mathematical programming to find optimal staff-to-counter
    allocation and staggered break schedule.
    """
    return _STAFF_OPTIMIZER.optimize_allocations(
        active_staff=req.active_staff,
        service_demands=req.service_demands,
        available_counters=req.available_counters,
        break_slots=req.break_slots,
    )


@router.post("/stochastic")
def run_stochastic_optimization(req: StochasticOptimizationRequest):
    """
    Executes Two-Stage Stochastic Optimization under arrival demand uncertainty:
    Stage 1 base regular capacity and Stage 2 recourse flex.
    """
    return _STOCHASTIC_OPTIMIZER.solve(
        active_staff=req.active_staff,
        available_counters=req.available_counters,
        base_demand=req.base_demand,
        conformal_halfwidth=req.conformal_halfwidth,
    )


@router.post("/scenarios")
def run_stress_scenario(req: ScenarioStressRequest):
    """
    Simulates operational crises (month-end surges, staff sickness, ATM hardware outages)
    and produces rigorous BEFORE vs. AFTER comparative metrics and actionable checklists.
    """
    return _SCENARIO_SIMULATOR.run_scenario(
        scenario_key=req.scenario_key,
        active_staff=req.active_staff,
        available_counters=req.available_counters,
        base_hourly_arrivals=req.base_hourly_arrivals,
    )

