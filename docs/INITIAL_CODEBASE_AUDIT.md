# INITIAL CODEBASE AUDIT: BANK AI OPTIMIZER

**Author:** Antigravity Engineering Architecture Team  
**Date:** November 19, 2026  
**Project Baseline:** C:\Projects\bank-branch-optimizer (Commit: 1a99291)  
**Reference Benchmark:** C:\Projects\VitalOptima  
**Target:** Enterprise-Grade Banking Operations Intelligence & Mathematical Resource Optimization Platform

---

## 1. Executive Summary & Audit Context

Bank AI Optimizer is an operational decision support system originally envisioned to bridge the gap between retail bank branch queue telemetry, predictive customer demand, and counter staffing. While the project presents a functioning prototype demonstrating multi-persona Streamlit interfaces and FastAPI server endpoints, a rigorous engineering and mathematical audit reveals substantial architectural, algorithmic, security, and operational deficits when contrasted against production benchmarks like **VitalOptima**.

This audit details the existing baseline, exposes structural flaws and data leakage, identifies high-value components to preserve, and lays out a phased, non-destructive transformation plan to achieve research-grade mathematical rigor, ACID database persistence, strict RBAC/branch data isolation, and comprehensive QA testability.

---

## 2. Existing Architecture Assessment

### Current Architecture Topology
```
Streamlit (app.py) / FastAPI (server.py)
       │ (Import-time execution)
       ▼
InMemory Pipeline (BankingDataPipeline)
       │ (In-memory DataFrames, zero database)
       ├─► DemandForecaster (Closed-form L2 Ridge, shuffle split)
       ├─► WaitTimePredictor (NumPy Logistic / Linear)
       ├─► StaffCounterOptimizer (Greedy heuristic matching)
       ├─► BranchQueueSimulator (NumPy Monte Carlo, resets global seed)
       ├─► FeedbackSentimentAnalyzer (Hardcoded regex/lexicon)
       └─► BranchExplainabilityEngine (Hardcoded arbitrary weights)
```

### Architectural Deficits
1. **Absence of Persistent Database & ORM:** There is no database layer. All data is read from static raw CSV files (`data/raw/*.csv`) or memory. There is no relational schema, no ACID transaction boundaries, no audit ledger, and no migration tooling.
2. **Startup-Time Model Training Side Effects:** Both `server.py` and `app.py` execute full pipeline ingestion and model training upon module import. This introduces severe latency, high cold-start failure risk, non-deterministic state across workers, and blocks horizontal scaling.
3. **Monolithic API Structure:** `server.py` defines all endpoints in a single file without modular routers (`/api/auth`, `/api/branches`, `/api/optimization`, etc.), lacks Pydantic request/response schema validation, uses wildcard CORS (`allow_origins=["*"]`), and exposes in-memory mutable dictionaries (`live_counter_sessions`) prone to race conditions.
4. **Lack of Authentication & Authorization:** There is zero authentication. Users switch personas via an unauthenticated Streamlit dropdown or API queries without credential validation, session tokens, password hashing, or role/branch permissions.
5. **No Test Infrastructure:** Prior to this audit, the repository possessed zero test files (`tests/` directory was entirely absent).

---

## 3. Existing Functionality Matrix

| Module | Location | Current Capability | Audit Status |
| :--- | :--- | :--- | :--- |
| **Data Generator** | `src/data_generator.py` | Generates synthetic tokens, feedback, rosters, appointments | Functional for dev/demo; must not overwrite uploaded or operational datasets. |
| **Data Pipeline** | `src/data_pipeline.py` | Polars preprocessing, datetime extraction, hourly aggregation | Good foundation using Polars; needs validation rules, error tracking, and database sync. |
| **Demand Forecaster** | `src/models/demand_forecaster.py` | Ridge regression on hourly arrivals with polynomial hour features | **Critical Flaw:** Uses random shuffle split instead of chronological backtesting, causing severe data leakage. |
| **Wait Time Predictor** | `src/models/wait_time_model.py` | Linear wait regression + logistic SLA breach classification | Functional matrix math, but lacks conformal uncertainty intervals, calibration, and temporal splits. |
| **Staff Optimizer** | `src/optimization/staff_optimizer.py` | Greedy skill-matching and ratio-based counter assignment | **Critical Flaw:** Heuristic greedy loop falsely reporting `"Optimal Allocation Found"` without any solver or hard constraints. |
| **Queue Simulator** | `src/optimization/queue_simulator.py` | Monte Carlo queue simulation | **Critical Flaw:** Calls `np.random.seed(42)` inside function, resetting global RNG state. Lacks abandonment and dynamic break impacts. |
| **Digital Deflection** | `src/models/digital_deflection.py` | Rules mapping service categories to digital channels | Sound domain logic; requires configurable parameters and transaction suitability models. |
| **NLP Sentiment** | `src/models/nlp_sentiment.py` | Lexicon keyword matching and regex topic clustering | Useful deterministic baseline; needs structured sentiment analytics and database logging. |
| **Explainability** | `src/optimization/explainability.py` | Hardcoded if-else statements with invented `impact_pct` | **Critical Flaw:** Inaccurate explainability based on arbitrary numbers rather than actual model weights and sensitivity. |
| **FastAPI Backend** | `server.py` | Single-file API exposing endpoints | Needs decomposition into modular routers with Pydantic validation, auth dependencies, and DB sessions. |
| **Streamlit Frontend** | `app.py` | Multi-persona dashboard with custom CSS and Plotly charts | Rich interactive charts; needs decoupling from training calls, authentication gating, and multi-branch RBAC. |

---

## 4. Existing Mathematical & Operations Research Models

### A. Staff-to-Counter Allocation (`src/optimization/staff_optimizer.py`)
- **Current Formulation:** Computes target counter counts per service by:
  $$\text{target}_s = \max\left(1, \text{round}\left(\frac{\text{demand}_s}{\sum \text{demand}} \cdot \text{usable\_counters}\right)\right)$$
  Followed by a sequential 3-pass greedy assignment (Primary Skill -> Secondary Skill -> Dynamic Surge Relief).
- **Mathematical Evaluation:**
  - **No Optimization Formulation:** This is a greedy heuristic, not mathematical optimization.
  - **No Constraint Guarantees:** Cannot handle complex joint constraints (e.g., maximum consecutive working hours, certified compliance rules, multi-skilled simultaneous optimization, overtime boundaries).
  - **Misleading Reporting:** Returns `"status": "Optimal Allocation Found"` which violates scientific integrity.

### B. Queue Simulator (`src/optimization/queue_simulator.py`)
- **Current Formulation:** Sequential arrival loop using exponential inter-arrivals and normal service times:
  $$\tau_{i+1} = \tau_i + \text{Exp}(\lambda), \quad S_i \sim \mathcal{N}(\mu, \sigma^2)$$
- **Mathematical Evaluation:**
  - Resets `np.random.seed(42)` on every execution, destroying reproducibility for parallel or stochastic callers.
  - Does not model customer balking, reneging/abandonment, priority queuing disciplines (e.g. Senior/VIP token tiers), or discrete shift break transitions.

### C. Demand Forecaster (`src/models/demand_forecaster.py`)
- **Current Formulation:** Closed-form regularized normal equation:
  $$\hat{\beta} = (X^T X + \lambda I)^{-1} X^T y$$
- **Mathematical Evaluation:**
  - Uses `np.random.shuffle(indices)` before splitting 80/20. In time-series forecasting, randomly selecting future points into the training set leaks seasonal, trend, and calendar signals into past predictions.
  - Evaluates $R^2$, MAE, RMSE, and MAPE, but lacks chronological expanding/rolling window cross-validation and prediction intervals.

---

## 5. Security & Reliability Vulnerabilities

1. **Unprotected Endpoints & Credential Absence:**
   - No authentication system exists. Any client can access or trigger state changes.
   - CORS is configured with `allow_origins=["*"]`, opening cross-origin request abuse.
2. **Missing Input Validation & Injection Risks:**
   - API endpoints accept raw Python types without Pydantic schema validation.
   - No sanitization for uploaded files or query filters.
3. **Absence of Audit Logging:**
   - Critical managerial actions (reallocating staff, changing branch hours, altering queue parameters) leave zero audit trail.
   - Contrast with VitalOptima's cryptographic SHA-256 tamper-evident hash-chained audit ledger.
4. **Thread Safety & State Mutation:**
   - `live_counter_sessions` in `server.py` is a naked in-memory dictionary mutated directly across asynchronous worker threads without locks.

---

## 6. Components Worth Preserving vs. Requiring Replacement

### Components Worth Preserving
- **Data Generator Logic (`src/data_generator.py`):** Rich domain taxonomy for retail banking (High Net Worth, Retail Individual, Small Business, Senior Citizen, Student/Youth) and service categories (Cash Deposit/Withdrawal, Loan & Mortgage, KYC, Forex, Account Opening).
- **Core Domain Entities & Config (`src/config.py`):** Branch networks, cluster categorizations, operating hours, SLA thresholds, and digital deflection channel mappings.
- **Data Preprocessing Foundation (`src/data_pipeline.py`):** High-speed Polars aggregation logic for token metrics.
- **UI Styling & Card Layouts (`src/utils/helpers.py`):** Polished CSS design system, metric cards, status badges, and interactive visualizations.
- **Rule-Based Sentiment Baseline (`src/models/nlp_sentiment.py`):** Deterministic NLP lexicon and topic regexes provide a clean fallback baseline.

### Components Requiring Complete Replacement / Deep Upgrade
- **Staff Optimizer:** Replace greedy loop with **Google OR-Tools CP-SAT / MILP** mathematical optimization engine and **Two-Stage Stochastic Optimization** under demand uncertainty.
- **Queue Simulator:** Upgrade to a robust discrete-event simulation engine with independent `numpy.random.Generator` seeds, customer abandonment curves, and priority service classes.
- **Demand Forecaster:** Replace shuffle-split regression with **leakage-free chronological backtesting**, multi-model benchmarking (Ridge, Random Forest, HistGradientBoosting, Seasonal Baseline), and conformal prediction intervals.
- **Explainability Engine:** Replace hardcoded percentage dicts with mathematical sensitivity and feature attribution grounded in actual model weights and constraint bottlenecks.
- **Backend Architecture:** Build a modular FastAPI application with dedicated routers, Pydantic v2 schemas, JWT/PBKDF2 authentication, and SQLAlchemy 2.0 async/pooled database sessions.
- **Database Engine:** Implement normalized relational PostgreSQL schema via SQLAlchemy 2.x and Alembic migrations, supporting central org, regions, branches, employees, counters, tokens, and audit logs.

---

## 7. Phased Implementation Roadmap

```
Phase 0: Baseline & Audit (Complete)
Phase 1: Engineering Foundation (SQLAlchemy 2.x, PostgreSQL/SQLite fallback, Schema, Alembic, Central Config)
Phase 2: Authentication & RBAC (PBKDF2/Argon2id, JWT/Session, Branch-Level Permissions, Audit Hash-Chain)
Phase 3: Machine Learning Rigor (Chronological Split, Multi-Model Forecasting, Conformal Intervals, Wait-Time ML)
Phase 4: Mathematical Staff Optimization (Google OR-Tools CP-SAT MILP, Hard/Soft Constraints, Infeasibility Diagnostics)
Phase 5: Advanced OR & Queue Simulation (Discrete-Event Simulator with Abandonment, Two-Stage Stochastic Optimization)
Phase 6: Operational Intelligence & Explainability (Grounded XAI, Digital Deflection ROI, Sentiment Analytics)
Phase 7: Frontend & API Unification (Modular FastAPI Routers, Streamlit Multi-Page Cockpit, Ingestion UI)
Phase 8: Engineering Hardening & CI/CD (Pytest Suite, Dockerfile, Docker Compose, GitHub Actions, Security Audit)
Phase 9: Research Benchmarking & Final Documentation (Comprehensive Evaluation, Benchmark Matrix, Docs)
```

---
*End of Initial Codebase Audit Report.*
