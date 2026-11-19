# DATABASE SCHEMA & RELATIONAL ARCHITECTURE

**Project:** Bank AI Optimizer  
**Database Engine:** Neon Serverless PostgreSQL (PostgreSQL 18.x compatible)  
**ORM Framework:** SQLAlchemy 2.0 (Modern Declarative Mapped Models)  
**Driver:** Psycopg2-binary with connection pooling and serverless pre-ping reconnects  
**Local Development Fallback:** Isolated SQLite file database (`data/bank_optimizer.db`)  

---

## 1. Relational Topology Overview

The database architecture is designed with strict 3NF normalization, foreign key referential integrity, and cascading delete rules across 10 functional subsystems.

```
                           +-------------------+
                           |   organizations   |
                           +---------+---------+
                                     | 1:N
                           +---------v---------+
                           |      regions      |
                           +---------+---------+
                                     | 1:N
                           +---------v---------+
                     +---->|     branches      |<----+
                     |     +----+----+----+----+     |
                     | 1:N      |    |    |          | 1:N
           +---------+-----+    |    |    +----+     +-------------+
           |   employees   |    |    |         |     |   counters  |
           +---+-----+-----+    |    |         |     +-------------+
               |     |          |    |         |
               |     | 1:N      |    | 1:N     | 1:N
    +----------+--+  |     +----+    |     +---v------------------+
    | employee_   |  |     | branch_ |     |  customer_arrivals   |
    | skills      |  |     | hours   |     +----------+-----------+
    +-------------+  |     +---------+                | 1:1
                     |                                v
           +---------v-------+             +----------------------+
           | employee_shifts |             |   service_records    |
           +-----------------+             +----------------------+
```

---

## 2. Table Specifications by Subsystem

### 2.1 Organization & Multi-Branch Hierarchy
1. `organizations`: Root enterprise entity.
   - `id` (PK, Integer, autoincrement)
   - `org_code` (String(50), Unique, Indexed)
   - `name` (String(200), Not Null)
   - `country_code` (String(10), Default 'US')
   - `created_at`, `updated_at` (DateTime)

2. `regions`: Regional administrative clusters (e.g., Metro Central, East Suburbs).
   - `id` (PK)
   - `organization_id` (FK -> `organizations.id`, ON DELETE CASCADE)
   - `region_code` (String(50), Unique, Indexed)
   - `name` (String(200))

3. `branches`: Individual physical bank branches.
   - `id` (PK)
   - `region_id` (FK -> `regions.id`, ON DELETE CASCADE)
   - `branch_code` (String(50), Unique, Indexed, e.g., 'BR_001')
   - `name` (String(200))
   - `cluster` (String(100))
   - `total_counters` (Integer)
   - `peak_window` (String(50))
   - `is_active` (Boolean)

4. `branch_operating_hours`: Weekly opening schedules per branch.
   - `id` (PK)
   - `branch_id` (FK -> `branches.id`, ON DELETE CASCADE)
   - `day_of_week` (Integer: 0=Mon, 6=Sun)
   - `open_time`, `close_time` (String)
   - `is_closed` (Boolean)
   - *Constraint:* `UNIQUE(branch_id, day_of_week)`

### 2.2 Authentication & Access Control (RBAC)
5. `roles`: Standardized roles (`CENTRAL_ADMIN`, `REGIONAL_MANAGER`, `BRANCH_MANAGER`, `EMPLOYEE`).
6. `users`: System users with PBKDF2/Argon2 password hashes and lockout trackers.
7. `user_roles`: Many-to-many relationship mapping users to roles.
8. `user_branch_permissions`: Granular branch-level data access enforcement.
9. `login_attempts`: Security event log capturing IP, user agent, success flag, and timestamp.

### 2.3 Employee & Skills Management
10. `employees`: Staff members associated with specific branches.
11. `employee_skills`: Matrix of skills, proficiency levels (Novice, Competent, Expert), and certification flags.
12. `employee_certifications`: Official compliance licenses and valid-until dates.
13. `employee_shifts`: Scheduled shift allocations and shift types.
14. `employee_availability`: Daily availability records and unavailability reasons.
15. `employee_breaks`: Approved meal and rest break windows.

### 2.4 Branch Operations & Queue Telemetry
16. `counters`: Physical service counters assigned to branches.
17. `service_categories`: Standard banking transaction types, SLA thresholds, and digital deflectability.
18. `customer_arrivals`: Token logs containing arrival time, service start/end, wait durations, SLA breach status, and satisfaction scores.
19. `service_records`: Completed teller service transactions.
20. `appointments`: Pre-booked customer appointments.

### 2.5 Customer Intelligence & Sentiment
21. `customer_feedback`: Unstructured textual customer reviews and 1-5 ratings.
22. `sentiment_results`: Polarity scores, detected friction topics, and staff/counter attributions.
23. `digital_deflection_events`: Log of transactions successfully deflected to CDMs, ATMs, or mobile banking.

### 2.6 ML Prediction & Model Governance
24. `demand_forecasts`: Hourly customer arrival predictions with P10/P90 prediction intervals.
25. `wait_time_predictions`: In-queue wait duration and SLA breach probability estimates.
26. `model_versions`: Registry tracking model names, version tags, algorithms, and hyperparameters.
27. `model_evaluations`: Chronological benchmark metrics (MAE, RMSE, WAPE, R²).

### 2.7 Mathematical Optimization
28. `optimization_runs`: Solve metadata (OR-Tools CP-SAT status, solve time ms, objective value).
29. `staff_allocations`: Assigned staff-to-counter records with match type and fatigue ratings.
30. `break_schedules`: Staggered break windows generated by mathematical constraint programming.
31. `optimization_constraints`: Configurable objective weights and penalty parameters.
32. `optimization_metrics`: Quantitative solver outcomes.

### 2.8 Queue Simulation
33. `simulation_runs`: Monte Carlo and discrete-event runs with explicit random seeds.
34. `simulation_scenarios`: Pre-configured parameter perturbation scenarios (e.g., month-end surge).
35. `simulation_results`: Hourly queue progression distributions.

### 2.9 Management, Alerts & Tamper-Evident Audit Ledger
36. `alerts`: Real-time operational alarms (SLA breach, staff shortage).
37. `decision_logs`: Log of management overrides and operational choices.
38. `audit_logs`: SHA-256 hash-chained immutable audit ledger.

### 2.10 Dataset Ingestion Management
39. `dataset_imports`: Upload audit trail tracking source, record counts, and status.
40. `dataset_import_errors`: Row-by-row validation error details.
41. `dataset_validation_reports`: Structured JSON diagnostic reports.
