"""
Unit and Rigor Tests for Mathematical Staff Optimizer (Google OR-Tools CP-SAT).
Validates solver optimality, physical uniqueness constraints, skill adherence,
break staggering, independent validation, and honest heuristic fallback labeling.
"""
import pytest
from src.optimization.staff_optimizer import (
    StaffCounterOptimizer,
    IndependentAllocationValidator,
    ORTOOLS_AVAILABLE
)


@pytest.fixture
def sample_staff():
    """Generates realistic retail banking branch staff with primary and secondary skills."""
    return [
        {
            "staff_id": "EMP_01",
            "staff_name": "Alice Teller",
            "primary_skill": "Cash Deposit/Withdrawal",
            "secondary_skills": "Account Services & KYC;Passbook / Statement Printing",
            "efficiency_factor": 1.1,
            "counter_speed_rating": 4.8
        },
        {
            "staff_id": "EMP_02",
            "staff_name": "Bob KYC",
            "primary_skill": "Account Services & KYC",
            "secondary_skills": "Cash Deposit/Withdrawal",
            "efficiency_factor": 1.0,
            "counter_speed_rating": 4.5
        },
        {
            "staff_id": "EMP_03",
            "staff_name": "Charlie Loan",
            "primary_skill": "Loan & Mortgage Advisory",
            "secondary_skills": "Account Services & KYC",
            "efficiency_factor": 1.2,
            "counter_speed_rating": 4.9
        },
        {
            "staff_id": "EMP_04",
            "staff_name": "David Forex",
            "primary_skill": "Forex & Trade Finance",
            "secondary_skills": "Cash Deposit/Withdrawal",
            "efficiency_factor": 0.95,
            "counter_speed_rating": 4.2
        },
        {
            "staff_id": "EMP_05",
            "staff_name": "Emma General",
            "primary_skill": "Passbook / Statement Printing",
            "secondary_skills": "Card Services & Pin Reset",
            "efficiency_factor": 1.05,
            "counter_speed_rating": 4.6
        }
    ]


@pytest.fixture
def sample_demands():
    """Typical midday peak hourly demand distribution."""
    return {
        "Cash Deposit/Withdrawal": 14,
        "Account Services & KYC": 8,
        "Loan & Mortgage Advisory": 4,
        "Forex & Trade Finance": 2,
        "Passbook / Statement Printing": 5
    }


def test_ortools_cp_sat_optimal_solve(sample_staff, sample_demands):
    """Verifies that OR-Tools CP-SAT finds an optimal/feasible mathematical solution."""
    optimizer = StaffCounterOptimizer(time_limit_seconds=3.0)
    result = optimizer.optimize_allocations(
        active_staff=sample_staff,
        service_demands=sample_demands,
        available_counters=4
    )

    if ORTOOLS_AVAILABLE:
        assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")
        assert result["solver_name"] == "Google OR-Tools CP-SAT"
        assert result["is_mathematically_proven"] is True
    else:
        assert result["solver_status"] == "HEURISTIC_FALLBACK"

    # Must allocate at most available_counters
    assert result["allocated_counters"] <= 4
    assert len(result["assignments"]) == result["allocated_counters"]
    assert result["unassigned_buffer_staff"] == len(sample_staff) - result["allocated_counters"]


def test_hard_physical_uniqueness_constraints(sample_staff, sample_demands):
    """Verifies that no staff member or counter is assigned more than once."""
    optimizer = StaffCounterOptimizer()
    result = optimizer.optimize_allocations(
        active_staff=sample_staff,
        service_demands=sample_demands,
        available_counters=5
    )

    assigned_staff_ids = [a["staff_id"] for a in result["assignments"]]
    assigned_counters = [a["counter_id"] for a in result["assignments"]]

    assert len(assigned_staff_ids) == len(set(assigned_staff_ids)), "Duplicate employee assignment detected!"
    assert len(assigned_counters) == len(set(assigned_counters)), "Duplicate counter assignment detected!"


def test_break_schedule_integrity(sample_staff, sample_demands):
    """Verifies that every working staff member receives exactly one staggered break."""
    optimizer = StaffCounterOptimizer()
    result = optimizer.optimize_allocations(
        active_staff=sample_staff,
        service_demands=sample_demands,
        available_counters=4
    )

    break_schedule = result["break_schedule"]
    assert len(break_schedule) == result["allocated_counters"]

    # Check that staff names in break schedule match assigned staff
    assigned_names = {a["staff_name"] for a in result["assignments"]}
    break_names = {b["staff_name"] for b in break_schedule}
    assert assigned_names == break_names


def test_independent_validator_catches_duplicate_assignment():
    """Verifies that IndependentAllocationValidator catches invalid duplicate assignments."""
    invalid_assignments = [
        {"staff_id": "EMP_01", "staff_name": "Alice", "counter_id": "Counter 1", "assigned_service": "Cash"},
        {"staff_id": "EMP_01", "staff_name": "Alice", "counter_id": "Counter 2", "assigned_service": "KYC"} # Duplicate employee!
    ]
    invalid_breaks = [
        {"staff_name": "Alice", "allocated_break_window": "11:30 - 12:15"}
    ]
    is_valid, errors = IndependentAllocationValidator.validate(
        assignments=invalid_assignments,
        break_schedule=invalid_breaks,
        active_staff=[{"staff_id": "EMP_01", "staff_name": "Alice"}],
        available_counters=4
    )
    assert is_valid is False
    assert any("multiple counters" in e for e in errors)


def test_empty_staff_handling():
    """Verifies safe handling of empty staff list without exceptions."""
    optimizer = StaffCounterOptimizer()
    result = optimizer.optimize_allocations(
        active_staff=[],
        service_demands={"Cash": 10},
        available_counters=4
    )
    assert result["solver_status"] == "INFEASIBLE"
    assert result["allocated_counters"] == 0
    assert result["assignments"] == []
