# Bank AI Optimizer — Known Engineering Limitations & Operational Boundaries

This document provides a transparent, scientifically honest account of known technical, mathematical, computational, and architectural limitations in the Bank AI Optimizer platform. In compliance with enterprise engineering standards, theoretical optimality or production readiness is never fabricated.

---

## 1. Machine Learning & Forecasting Limitations

### 1.1 Synthetic Cold-Start Training Data
* **Current State:** The default ML models (demand forecaster and wait time regressor) are initially trained on statistically generated banking customer transaction distributions (`data/raw/synthetic_bank_data.csv`).
* **Limitation:** While diurnal seasonality, peak-hour distributions, and multi-service correlations are modeled rigorously using real-world banking patterns, synthetic data cannot replicate unmodeled macroeconomic shocks, hyper-local marketing campaigns, sudden branch closures, or black swan events (e.g., local weather disruptions or system-wide core banking outages).
* **Mitigation:** The system provides full dataset ingestion tooling (`services/dataset_service.py`) allowing bank operational teams to upload real core banking transaction logs (CSV/XLSX), validate historical records, and trigger incremental model retraining without codebase modifications.

### 1.2 Fixed Temporal Prediction Horizon
* **Current State:** Hourly demand forecasting operates over a rolling 1-to-7 day lookahead horizon with an 80/20 chronological validation split and 90% split conformal prediction intervals.
* **Limitation:** Multi-month or annual capacity planning forecasts do not currently incorporate holiday calendar shift effects (e.g., floating religious holidays or variable payroll schedules) unless explicitly featured in historical training logs.

### 1.3 Point-in-Time Wait Duration Estimation
* **Current State:** Wait-time predictions rely on a dual-head model (continuous wait duration + binary SLA breach probability) conditioned on current queue depth, active counters, and arrival rates.
* **Limitation:** Intra-day non-linear queue spikes (e.g., sudden arrival of 5 high-net-worth commercial clients requiring 45-minute complex wire audits) cannot be predicted prior to arrival without advance customer appointment scheduling data.

---

## 2. Operations Research & Optimization Limitations

### 2.1 Deterministic vs. Stochastic Solvers
* **Mixed-Integer Programming (CP-SAT):** The primary staff optimizer (`src/optimization/staff_optimizer.py`) is a deterministic mixed-integer constraint programming model solving for expected hourly arrival demand.
* **Limitation:** While CP-SAT guarantees provable global optimality within its specified solver budget for the *point demand*, it does not optimize for the variance of arrival times within an hour.
* **Mitigation:** The platform integrates the Two-Stage Stochastic Program (`src/optimization/stochastic_optimizer.py`) to quantify the Value of Stochastic Solution (VSS) under P10/P50/P90/Peak demand distributions, and the Discrete-Event Simulator (`src/optimization/queue_simulator.py`) to stress-test allocations against intra-hour Poisson burstiness.

### 2.2 OR-Tools Solver Wall-Clock Timeout Budget
* **Current State:** The CP-SAT solver is bounded by a 10.0-second execution time limit (`max_time_in_seconds=10.0`).
* **Limitation:** For extremely large branch networks (e.g., >50 counters, >100 staff members, 16 operating hours, and complex multi-skill overlap matrices), 10 seconds may yield an $\epsilon$-optimal feasible solution rather than an absolute mathematical proof of global optimality. The system honestly flags this status via `optimization_status = "FEASIBLE"` rather than `"OPTIMAL"`.

### 2.3 Static Multi-Skill Cross-Training
* **Current State:** Tellers are modeled with static primary and secondary skill sets (General, Teller, Loans, Forex, Commercial, Wealth).
* **Limitation:** Dynamic on-the-job fatigue degradation, varying service processing speeds across individual staff members, and real-time skill acquisition are not modeled in the constraint matrix.

---

## 3. Queue Simulation Boundaries

### 3.1 Markovian vs. Non-Markovian Assumptions
* **Analytical Benchmark:** The analytical queuing comparison uses the Erlang-C ($M/M/c$) delay model, which assumes Markovian (exponential) service and inter-arrival times.
* **Simulation Reality:** Real banking service times follow heavy-tailed distributions (lognormal or Weibull). The Discrete-Event Simulation (`QueueSimulator`) implements lognormal service distributions and non-homogeneous Poisson arrivals with customer balking and reneging. Consequently, discrepancies between analytical Erlang-C metrics and simulated metrics are expected and represent realistic customer behavior rather than modeling errors.

### 3.2 Customer Routing & Counter Assignment
* **Current State:** Queue simulation implements priority-tier FIFO scheduling with single-queue multi-server routing (common bank branch queue ticket dispensing model).
* **Limitation:** Individual teller-specific customer line jockeying (physically switching lines in branches without automated queue ticket dispensers) is not simulated.

---

## 4. Hardware, Telemetry & Real-Time Infrastructure

### 4.1 IoT / Hardware Sensor Telemetry
* **Current State:** Live queue depth and counter occupancy are ingested via REST API endpoints (`/api/simulation/queue-run`, `/api/branches/{id}/counters`).
* **Limitation:** The platform does not currently include direct proprietary device drivers for hardware ticket kiosks (e.g., Qmatic, Tensator) or overhead LiDAR/camera foot-traffic sensors. Integration relies on the standard JSON REST ingestion layer.

### 4.2 Push Notifications & Mobile Alerts
* **Current State:** Operational alerts and SLA breach warnings are logged transactionally to the PostgreSQL `alerts` and `audit_logs` tables and displayed live in the Streamlit Executive Dashboard.
* **Limitation:** Out-of-the-box outbound delivery mechanisms (SMS via Twilio, push notifications via Firebase FCM, or corporate email via SMTP) are architectural hooks requiring enterprise configuration; they are not active in default offline environments.

---

## 5. Architectural & Deployment Boundaries

### 5.1 Distributed Worker Queue
* **Current State:** FastAPI endpoints execute optimization and simulation runs synchronously within the worker process or through thread pools.
* **Limitation:** High-frequency, massive-scale Monte Carlo runs (>50,000 iterations across 500 branches simultaneously) will saturate CPU cores if invoked concurrently without an external distributed task queue (e.g., Celery with Redis/RabbitMQ).
* **Recommendation:** Deploy a Celery/Redis worker cluster for enterprise-wide batch optimization across regional networks exceeding 1,000 branches.

### 5.2 Read/Write Database Replicas
* **Current State:** The database layer (`db/connection.py`) maintains a single authoritative connection pool to Neon PostgreSQL with automated failover and fallback to local SQLite for isolated sandbox or offline testing.
* **Limitation:** Read/write splitting (routing reporting queries to read replicas and transactions to primary) is not configured; high-volume simultaneous analytical reporting during peak morning hours may compete for database connection pool capacity.

