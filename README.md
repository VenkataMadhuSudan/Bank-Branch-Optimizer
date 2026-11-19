# 🏦 Bank AI Optimizer — Enterprise Operations Intelligence Platform

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%2018.7-336791.svg)](https://neon.tech/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Google OR-Tools](https://img.shields.io/badge/OR--Tools-CP--SAT-4285F4.svg)](https://developers.google.com/optimization)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/Tests-48%20Passed%20(100%25)-brightgreen.svg)](tests/)
[![Security](https://img.shields.io/badge/Auth-NIST%20SP%20800--63B-blueviolet.svg)](docs/AUTHENTICATION_SECURITY.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, mathematically rigorous operations intelligence and prescriptive staff allocation platform designed for retail banking networks. The platform unifies **Neon PostgreSQL 18.7** persistence, **Google OR-Tools CP-SAT Mixed-Integer Constraint Programming**, **Two-Stage Stochastic Programming**, **Discrete-Event Queue Simulation (DES)**, **Conformal Prediction**, and **NIST SP 800-63B Zero-Trust Security**.

---

## 📑 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [Key Core Capabilities](#-key-core-capabilities)
  - [1. Authoritative Neon PostgreSQL Persistence (41 Tables)](#1-authoritative-neon-postgresql-persistence-41-tables)
  - [2. Mathematical Staff Optimization (Google OR-Tools CP-SAT)](#2-mathematical-staff-optimization-google-or-tools-cp-sat)
  - [3. Two-Stage Stochastic Program under Uncertainty](#3-two-stage-stochastic-program-under-uncertainty)
  - [4. Discrete-Event Queue Simulation & Erlang-C Delay Benchmarking](#4-discrete-event-queue-simulation--erlang-c-delay-benchmarking)
  - [5. Demand Forecasting & Split Conformal Prediction](#5-demand-forecasting--split-conformal-prediction)
  - [6. NIST SP 800-63B Authentication & Cryptographic Audit Ledger](#6-nist-sp-800-63b-authentication--cryptographic-audit-ledger)
  - [7. Enterprise Dataset Ingestion Engine](#7-enterprise-dataset-ingestion-engine)
- [Multi-Persona User Interface](#-multi-persona-user-interface)
- [Complete Test Suite & Verification (48/48 Passing)](#-complete-test-suite--verification-4848-passing)
- [Quickstart & Installation](#-quickstart--installation)
- [RESTful API Reference](#-restful-api-reference)
- [Docker & Containerized Deployment](#-docker--containerized-deployment)
- [Engineering Documentation Suite](#-engineering-documentation-suite)

---

## 🏗️ Architectural Overview

The system is decoupled into four clean, scalable operational tiers:

```
Streamlit Executive Operations Cockpit (15 Interactive Modules, Multi-Persona UI)
                                |
                   HTTP / REST (JWT Bearer Auth)
                                v
FastAPI Application Server (9 Modular Sub-Routers, Pydantic v2 Schemas)
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
Machine Learning Services   Operations Research    Operational Intelligence
• Chronological Backtesting • CP-SAT MILP Solver   • Root-Cause Attribution XAI
• Conformal 90% Bounds     • 2-Stage Stoch. Prog. • Deterministic Lexical NLP
• Dual-Head Wait Models    • Discrete-Event DES    • Digital Deflection ROI
        |                       |                       |
        +-----------------------+-----------------------+
                                |
                 Domain Services & Security Tier
                 • AuthService (PBKDF2-HMAC-SHA256, RBAC)
                 • AuditService (SHA-256 Hash Chain)
                 • DatasetService (CSV/XLSX Validator)
                                |
                                v
               Authoritative Database Layer
               • Neon PostgreSQL 18.7 (41 Tables)
               • SQLAlchemy 2.0 Connection Pooling
               • Alembic Schema Migration Engine
```

---

## 🚀 Key Core Capabilities

### 1. Authoritative Neon PostgreSQL Persistence (41 Tables)
* **Authoritative Engine:** Connects to remote Neon PostgreSQL (`PostgreSQL 18.7`) with automated pre-ping pooling (`pool_size=10, max_overflow=20, pool_recycle=300`) and graceful SQLite fallback for network-isolated testing.
* **41 Relational Tables:** Full normalization covering Organizations, Regions, Branches, Users, Roles, Permissions, Employees, Skills, Certifications, Counters, Service Categories, Queue Arrivals, Wait Predictions, Demand Forecasts, CP-SAT Allocations, Simulation Runs, Datasets, and Audits.
* **Migrations:** Controlled via Alembic (`alembic/`).
* **Seeded Hierarchy:** Includes 1 Organization, 3 Regions, 5 Branches, 36 Counters, 7 Service Categories, 4 Roles, and 46 Staff Members with detailed skill matrices.

### 2. Mathematical Staff Optimization (Google OR-Tools CP-SAT)
Replaces naive heuristic division with a rigorous **Mixed-Integer Constraint Programming** formulation:
* **Objective:** Minimizes idle teller costs, customer queue under-capacity shortages, and overtime penalties.
* **Hard Constraints:**
  - Physical counter bounds: $\sum_{i} x_{i,t} \le C_{\text{physical}}$.
  - Demand-capacity flow balance: $\sum_{i} x_{i,t} \cdot \mu_i + U_t - I_t = D_t$.
  - Mandatory staggered lunch breaks inside the 11:30–14:30 window ($\sum_{t \in \text{Lunch}} b_{i,t} = 1$).
  - Mutual exclusion between active counter service and break intervals ($x_{i,t} + b_{i,t} \le 1$).
  - Anti-starvation minimum teller staffing per branch ($M_{\text{min}}$).
  - Multi-skill certification eligibility ($x_{i,t} \le Q_{i, k(t)}$).
* **Independent Validator:** `IndependentAllocationValidator` mathematically inspects schedules post-solve against 6 physical invariants, guaranteeing zero invalid allocations.

### 3. Two-Stage Stochastic Program under Uncertainty
* **Stage 1 (Here-and-Now):** Base counter commitments before demand realization.
* **Stage 2 (Recourse):** Overtime activations and floating relief teller call-ins evaluated across scenarios $s \in \{\text{P10}, \text{P50}, \text{P90}, \text{Peak}\}$.
* **Value of Stochastic Solution (VSS):** Quantifies cost savings achieved over expected-value deterministic models.

### 4. Discrete-Event Queue Simulation & Erlang-C Delay Benchmarking
* **Isolated RNG Streams:** Independent `numpy.random.default_rng(seed)` streams eliminate global random state contamination.
* **Non-Homogeneous Poisson Arrivals:** Diurnal arrival curves modeling morning, lunch, and closing rush periods.
* **Heavy-Tailed Service Times:** Lognormal service distributions tailored to transaction complexity.
* **Customer Abandonment:** Dynamic customer balking (line avoidance) and reneging (queue drop-off).
* **Analytical Benchmark:** Validates empirical queue wait distributions against theoretical Erlang-C ($M/M/c$) delay formulas:
  $$P(\text{Wait} > 0) = C(c, a) = \frac{\frac{a^c}{c!} \frac{c}{c - a}}{\sum_{k=0}^{c-1} \frac{a^k}{k!} + \frac{a^c}{c!} \frac{c}{c - a}}$$

### 5. Demand Forecasting & Split Conformal Prediction
* **Leakage-Free Validation:** Strict 80/20 chronological train/test split.
* **Multi-Model Benchmark:** Evaluates Seasonal Naive, Ridge Regression, Random Forest, and Histogram Gradient Boosting (`HistGradientBoostingRegressor`).
* **90% Split Conformal Intervals:** Computes finite-sample distribution-free nonconformity bounds guaranteeing rigorous prediction intervals.
* **Dual-Head Wait Time Model:** Continuous regression estimating expected minutes + calibrated classification predicting 15-minute SLA breach probability.

### 6. NIST SP 800-63B Authentication & Cryptographic Audit Ledger
* **NIST-Compliant Hashing:** PBKDF2-HMAC-SHA256 with 600,000 iterations, 16-byte random salt, and timing-safe comparison (`hmac.compare_digest`).
* **Account Lockout:** 5 consecutive failed login attempts locks account for 15 minutes.
* **4-Tier RBAC:** `CENTRAL_ADMIN`, `REGIONAL_MANAGER`, `BRANCH_MANAGER`, `EMPLOYEE`.
* **Branch Data Isolation:** Enforces strict multi-tenant boundary checks (Branch Manager 1 cannot read/write Branch 2).
* **SHA-256 Forward-Linked Hash Chain:** Tamper-evident blockchain-style ledger recording every optimization, dataset import, and access attempt. Includes automated tamper detection.

### 7. Enterprise Dataset Ingestion Engine
* Supports CSV and XLSX uploads.
* Validates schema columns, data types, negative values, unknown branch IDs, and duplicate records.
* Provides pre-import preview with error auditing and transactional batch insertion into PostgreSQL.

---

## 👥 Multi-Persona User Interface

The Streamlit operations cockpit (`app.py`) provides 15 interactive modules filtered by role:
1. **🔐 Authentication & RBAC Gate:** Secure PBKDF2 login with session state management.
2. **🏛️ Executive Overview:** Network-wide KPIs, branch health cards, and active counter status.
3. **📈 Demand Forecasting Studio:** Chronological predictions with 90% conformal intervals.
4. **⚙️ CP-SAT Staff Optimizer:** Provable constraint scheduling with independent validator status.
5. **🎲 Discrete-Event Simulator:** Live queue simulation with balking/reneging and Erlang-C curves.
6. **🌪️ What-If Crisis Simulator:** Stress-testing month-end rushes, staff absenteeism, and ATM outages.
7. **💡 Root-Cause XAI Attribution:** Mathematical attribution of wait spikes to capacity deltas.
8. **💬 Customer Voice NLP:** Lexical sentiment scoring, topic clustering, and action alarms.
9. **🔄 Digital Deflection & ROI:** Multi-channel deflection triage and dollar savings calculations.
10. **📂 Dataset Management:** CSV/XLSX file upload, schema validation, and database insertion.
11. **📜 Cryptographic Audit Ledger:** Real-time tamper verification of the SHA-256 hash chain.
12. **👥 Staff Roster & Skill Matrix:** Teller skills, certifications, and shift allocations.
13. **🏢 Multi-Branch Navigation:** Hierarchical switcher for Central, Regional, and Local views.
14. **⚡ Real-Time Operational Alerts:** Unacknowledged SLA breach warnings and counter shortages.
15. **📊 System Health & Diagnostics:** Neon PostgreSQL pooling status and driver metrics.

---

## 🧪 Complete Test Suite & Verification (48/48 Passing)

The test suite covers 7 specialized testing categories:

| Category | Test File | Tests | Status | Verification Focus |
| :--- | :--- | :---: | :---: | :--- |
| **Database** | `tests/unit/test_database.py` | 2 | **PASSED** | Connection pooling, pre-ping health checks, fallback. |
| **Schema** | `tests/unit/test_schema.py` | 4 | **PASSED** | 41-table relationships, UUID uniqueness, cascading, UTC timestamps. |
| **Dataset Ingestion** | `tests/unit/test_dataset_service.py` | 5 | **PASSED** | Schema validation, duplicate detection, invalid values, batch ingest. |
| **Security & RBAC** | `tests/security/test_auth_and_rbac.py` | 11 | **PASSED** | PBKDF2 600k rounds, lockout, JWT, 4 roles, branch isolation, SHA-256 chain. |
| **Forecasting** | `tests/forecasting/test_forecasting.py` | 5 | **PASSED** | Chronological split, no future leakage, conformal bounds, dual-head wait. |
| **Optimization** | `tests/optimization/test_staff_optimizer.py` | 5 | **PASSED** | CP-SAT feasibility, counter bounds, lunch breaks, skills, independent validator. |
| **Simulation & OR** | `tests/simulation/test_queue_and_stochastic.py` | 5 | **PASSED** | DES mechanics, RNG reproducibility, abandonment, 2-Stage SP, Erlang-C. |
| **Operational Intel** | `tests/operational/test_operational_intelligence.py` | 5 | **PASSED** | XAI capacity deltas, sentiment scoring, deflection triage, ROI. |
| **Concurrency & Resilience** | `tests/operational/test_database_failure.py` | 2 | **PASSED** | 20 concurrent threads writing audit logs with 100% hash chain integrity. |
| **API Endpoints** | `tests/api/test_api_endpoints.py` | 9 | **PASSED** | Modular FastAPI routers, JWT auth, schema compliance, legacy aliases. |
| **TOTAL** | **All Categories** | **48** | **100% PASS** | **Zero failures, zero regressions, full validation.** |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10 or higher.
- A Neon PostgreSQL database instance (or local PostgreSQL 14+).

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
# Database Configuration (Neon PostgreSQL)
DATABASE_URL=postgresql+psycopg2://username:password@ep-crimson-bar-bdurbnps.c-8.us-east-2.aws.neon.tech/neondb?sslmode=require

# Security & Authentication
JWT_SECRET=your-super-secret-hex-encoded-key-here-minimum-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-cov alembic argon2-cffi
```

### 4. Seed Database Hierarchy
Populate the database with organizations, regions, branches, counters, and staff:
```bash
python -m db.seed
```

### 5. Run the Automated Test Suite
```bash
# Run complete offline unit, security, math, and operational test suite:
python -m pytest tests/unit tests/security tests/forecasting tests/optimization tests/simulation tests/operational -v

# Run FastAPI integration test suite:
python -m pytest tests/api/test_api_endpoints.py -v
```

### 6. Launch the Application Servers
```bash
# Terminal 1: Launch FastAPI Backend Server (Port 8000)
python server.py

# Terminal 2: Launch Streamlit Operations Cockpit (Port 8501)
streamlit run app.py
```

### 7. Default Demo Accounts
| Username | Password | Role | Access Scope |
| :--- | :--- | :--- | :--- |
| `admin` | `Admin@123` | `CENTRAL_ADMIN` | All Branches, System-Wide Config |
| `branch_mgr_downtown` | `Downtown@123` | `BRANCH_MANAGER` | Downtown Flagship Branch (`BR001`) |
| `regional_dir_central` | `Regional@123` | `REGIONAL_MANAGER` | Central Metro Region Branches |

---

## 🌐 RESTful API Reference

The FastAPI backend exposes modular, documented REST endpoints at `http://localhost:8000/docs`:

* **Authentication:** `POST /api/auth/login`, `GET /api/auth/me`
* **Branch Operations:** `GET /api/branches/`, `GET /api/branches/{id}`, `GET /api/branches/{id}/counters`
* **Forecasting:** `POST /api/forecasts/hourly`, `GET /api/forecasts/status`
* **Optimization:** `POST /api/optimization/solve-staff`, `GET /api/optimization/runs`
* **Queue Simulation:** `POST /api/simulation/queue-run`, `POST /api/simulation/stochastic-run`
* **Operational Intelligence:** `POST /api/intelligence/sentiment`, `POST /api/intelligence/deflection-roi`
* **Dataset Ingestion:** `POST /api/datasets/validate`, `POST /api/datasets/import`
* **Cryptographic Audit:** `GET /api/audit/logs`, `GET /api/audit/verify-chain`
* **System Health:** `GET /api/health/live`, `GET /api/health/db`

---

## 🐳 Docker & Containerized Deployment

Deploy with Docker Compose:
```bash
# Build and start services in detached mode
docker-compose up --build -d

# Check service logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📚 Engineering Documentation Suite

Comprehensive technical documentation is available in the `docs/` directory:

1. [`docs/INITIAL_CODEBASE_AUDIT.md`](docs/INITIAL_CODEBASE_AUDIT.md): Complete baseline repository inspection and gap analysis.
2. [`docs/IMPLEMENTATION_TRACKER.md`](docs/IMPLEMENTATION_TRACKER.md): Phase-by-phase implementation record and decision log.
3. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Decoupled 4-tier architectural specification and data flow diagrams.
4. [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md): Complete data dictionary and ERD for all 41 relational tables.
5. [`docs/AUTHENTICATION_SECURITY.md`](docs/AUTHENTICATION_SECURITY.md): NIST SP 800-63B authentication, token issuance, and account lockout.
6. [`docs/DATA_GOVERNANCE.md`](docs/DATA_GOVERNANCE.md): Ingestion validation pipelines, duplicate prevention, and partial import rules.
7. [`docs/MATHEMATICAL_MODEL.md`](docs/MATHEMATICAL_MODEL.md): Formulations for queueing theory, flow conservation, and constraint models.
8. [`docs/OPTIMIZATION_METHODOLOGY.md`](docs/OPTIMIZATION_METHODOLOGY.md): CP-SAT MILP formulation, bounds, and independent validation.
9. [`docs/FORECASTING_METHODOLOGY.md`](docs/FORECASTING_METHODOLOGY.md): Chronological backtesting, split conformal intervals, and error metrics.
10. [`docs/QUEUE_SIMULATION.md`](docs/QUEUE_SIMULATION.md): Discrete-event mechanics, customer abandonment, and Erlang-C proofs.
11. [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md): OpenAPI endpoint specifications, request payloads, and response schemas.
12. [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md): Zero-trust architecture, threat modeling, and secret redaction filters.
13. [`docs/TESTING_STRATEGY.md`](docs/TESTING_STRATEGY.md): Testing pyramid, coverage standards, and verification procedures.
14. [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md): Production containerization, environment variables, and Neon PostgreSQL setup.
15. [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md): Transparent account of mathematical, operational, and computational boundaries.
16. [`docs/ENGINEERING_AUDIT.md`](docs/ENGINEERING_AUDIT.md): Direct comparative audit of baseline prototype vs. transformed system.
17. [`docs/FINAL_ENGINEERING_REPORT.md`](docs/FINAL_ENGINEERING_REPORT.md): Comprehensive executive transformation summary.

---

## 📄 License
This project is licensed under the MIT License.
