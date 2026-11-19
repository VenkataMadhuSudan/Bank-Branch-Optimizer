"""
Database Seeding Engine for Bank AI Optimizer.
Populates normalized initial tables from domain configuration and existing CSV files.
Non-destructive: Uses existence checks to prevent duplicate inserts or overwriting.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from db.connection import get_db_session
from db.schema import (
    Organization, Region, Branch, BranchOperatingHour, Counter,
    ServiceCategory, Role, User, UserRole, UserBranchPermission,
    Employee, EmployeeSkill
)
from src.config import BRANCH_NETWORK, SERVICE_CATEGORIES, RAW_DATA_DIR
from src.utils.logger import logger


def seed_core_hierarchy() -> Dict[str, Any]:
    """Seeds Organization, Regions, Branches, Operating Hours, and Counters."""
    logger.info("Starting core hierarchy seeding...")
    stats = {"organizations": 0, "regions": 0, "branches": 0, "counters": 0, "services": 0}

    with get_db_session() as session:
        # 1. Organization
        org = session.execute(
            select(Organization).where(Organization.org_code == "APEX_BANK_CORP")
        ).scalar_one_or_none()

        if not org:
            org = Organization(
                org_code="APEX_BANK_CORP",
                name="Apex Commercial Banking Group",
                country_code="US"
            )
            session.add(org)
            session.flush()
            stats["organizations"] += 1
            logger.info("Created organization: Apex Commercial Banking Group")

        # 2. Regions
        clusters = list({b["cluster"] for b in BRANCH_NETWORK})
        region_map = {}
        for idx, cluster_name in enumerate(clusters, 1):
            reg_code = f"REG_{idx:02d}"
            region = session.execute(
                select(Region).where(Region.region_code == reg_code)
            ).scalar_one_or_none()

            if not region:
                region = Region(
                    organization_id=org.id,
                    region_code=reg_code,
                    name=cluster_name
                )
                session.add(region)
                session.flush()
                stats["regions"] += 1
            region_map[cluster_name] = region.id

        # 3. Branches & Counters & Operating Hours
        for b_meta in BRANCH_NETWORK:
            branch = session.execute(
                select(Branch).where(Branch.branch_code == b_meta["branch_id"])
            ).scalar_one_or_none()

            if not branch:
                reg_id = region_map.get(b_meta["cluster"], list(region_map.values())[0])
                branch = Branch(
                    region_id=reg_id,
                    branch_code=b_meta["branch_id"],
                    name=b_meta["name"],
                    cluster=b_meta["cluster"],
                    total_counters=b_meta["total_counters"],
                    peak_window=b_meta["peak_window"],
                    is_active=True
                )
                session.add(branch)
                session.flush()
                stats["branches"] += 1

                # Add Counters
                for c_num in range(1, b_meta["total_counters"] + 1):
                    counter = Counter(
                        branch_id=branch.id,
                        counter_code=f"C_{c_num:02d}",
                        counter_type="Universal Teller" if c_num <= 4 else "Specialist Desk",
                        is_active=True
                    )
                    session.add(counter)
                    stats["counters"] += 1

                # Add Operating Hours (Mon-Fri 09-17, Sat 09-13, Sun closed)
                for day in range(7):
                    is_sunday = (day == 6)
                    is_saturday = (day == 5)
                    session.add(BranchOperatingHour(
                        branch_id=branch.id,
                        day_of_week=day,
                        open_time="09:00",
                        close_time="13:00" if is_saturday else "17:00",
                        is_closed=is_sunday
                    ))

        # 4. Service Categories
        for s_name, s_meta in SERVICE_CATEGORIES.items():
            code = s_name.upper().replace(" ", "_").replace("/", "_").replace("&", "AND")[:40]
            existing_svc = session.execute(
                select(ServiceCategory).where(ServiceCategory.service_code == code)
            ).scalar_one_or_none()

            if not existing_svc:
                session.add(ServiceCategory(
                    service_code=code,
                    name=s_name,
                    sla_wait_mins=float(s_meta["sla_wait_mins"]),
                    avg_service_mins=float(s_meta["avg_service_mins"]),
                    digital_eligible=bool(s_meta["digital_eligible"]),
                    digital_channel=str(s_meta["digital_channel"]),
                    digital_deflection_difficulty=str(s_meta["digital_deflection_difficulty"])
                ))
                stats["services"] += 1

    logger.info(f"Core hierarchy seeded successfully: {stats}")
    return stats


def seed_roles() -> Dict[str, int]:
    """Seeds standardized banking RBAC roles."""
    roles = [
        ("CENTRAL_ADMIN", "Full network-wide operational and administrative authority across all regions and branches."),
        ("REGIONAL_MANAGER", "Operational monitoring, branch comparisons, and decisions across authorized regions."),
        ("BRANCH_MANAGER", "Local branch resource allocation, staff shifts, optimization, and queue management."),
        ("EMPLOYEE", "Restricted counter terminal execution, token processing, and personal schedule viewing.")
    ]
    created = 0
    with get_db_session() as session:
        for r_name, r_desc in roles:
            existing = session.execute(
                select(Role).where(Role.role_name == r_name)
            ).scalar_one_or_none()
            if not existing:
                session.add(Role(role_name=r_name, description=r_desc))
                created += 1
    logger.info(f"Roles seeded: {created} new roles added.")
    return {"roles_created": created}


def seed_employees_from_csv(csv_path: Path = RAW_DATA_DIR / "staff_rosters.csv") -> Dict[str, int]:
    """Seeds employees and skills from raw staff rosters CSV."""
    if not csv_path.exists():
        logger.warning(f"Staff roster CSV not found at {csv_path}, skipping employee seed.")
        return {"employees_seeded": 0}

    logger.info(f"Seeding employees from {csv_path}...")
    seeded_count = 0
    with get_db_session() as session:
        # Load branch ID map
        branches = session.execute(select(Branch)).scalars().all()
        branch_map = {b.branch_code: b.id for b in branches}

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("staff_id") or row.get("staff_code")
                b_code = row.get("branch_id")
                if not code or not b_code:
                    continue

                b_id = branch_map.get(b_code)
                if not b_id:
                    continue

                existing = session.execute(
                    select(Employee).where(Employee.staff_code == code)
                ).scalar_one_or_none()

                if not existing:
                    emp = Employee(
                        branch_id=b_id,
                        staff_code=code,
                        full_name=row.get("staff_name", f"Staff {code}"),
                        primary_skill=row.get("primary_skill", "Cash Deposit/Withdrawal"),
                        secondary_skills=row.get("secondary_skills", ""),
                        efficiency_factor=float(row.get("efficiency_factor", 1.0)),
                        counter_speed_rating=float(row.get("counter_speed_rating", 4.5)),
                        hourly_rate_usd=float(row.get("hourly_rate_usd", 28.0)),
                        max_weekly_hours=float(row.get("max_weekly_hours", 40.0)),
                        is_active=True
                    )
                    session.add(emp)
                    session.flush()
                    seeded_count += 1

                    # Add primary skill
                    session.add(EmployeeSkill(
                        employee_id=emp.id,
                        service_category=emp.primary_skill,
                        proficiency_level="Expert",
                        is_certified=True
                    ))

                    # Add secondary skills
                    sec_skills = [s.strip() for s in str(emp.secondary_skills).split(";") if s.strip()]
                    for sec in sec_skills:
                        session.add(EmployeeSkill(
                            employee_id=emp.id,
                            service_category=sec,
                            proficiency_level="Competent",
                            is_certified=True
                        ))

    logger.info(f"Employees seeded: {seeded_count} records inserted.")
    return {"employees_seeded": seeded_count}


def run_all_seeds() -> Dict[str, Any]:
    """Runs all database seeders idempotently."""
    hierarchy_stats = seed_core_hierarchy()
    role_stats = seed_roles()
    employee_stats = seed_employees_from_csv()
    return {
        **hierarchy_stats,
        **role_stats,
        **employee_stats
    }

if __name__ == "__main__":
    print("Running seeds...")
    res = run_all_seeds()
    print("Seed Results:", res)
