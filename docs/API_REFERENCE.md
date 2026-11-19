# RESTFUL API SPECIFICATION & ENDPOINT REFERENCE

**Framework:** FastAPI 0.110+  
**Documentation Endpoints:** Interactive Swagger UI at `/docs`, ReDoc at `/redoc`  
**Base URL:** `http://localhost:8000`  

---

## 1. Authentication Endpoints

### `POST /api/auth/login`
- **Description:** Authenticates user and issues signed JWT bearer token.
- **Request Body:**
  ```json
  {
    "username": "admin",
    "password": "AdminPassword2026!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "user_id": 1,
      "username": "admin",
      "roles": ["CENTRAL_ADMIN"]
    }
  }
  ```

### `GET /api/auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Description:** Returns profile, roles, and branch permissions of the caller.

---

## 2. Branch Operations Endpoints

### `GET /api/branches`
- **Description:** Returns all branches, operational counters, service categories, and SLA thresholds.

---

## 3. Demand Forecasting Endpoints

### `GET /api/forecasts/hourly`
- **Query Params:** `branch_id`, `hour`, `day_of_week`, `is_month_end`
- **Description:** Returns expected arrival volume, 90% conformal uncertainty interval (`lower_bound_p10`, `upper_bound_p90`), and surge risk.

### `GET /api/forecasts/daily`
- **Description:** Returns 9-hour operational shift progression with conformal intervals.

### `POST /api/forecasts/train`
- **Description:** Retrains forecasting and wait-time models on updated queue telemetry.

---

## 4. Mathematical Optimization Endpoints

### `POST /api/optimization/staff`
- **Description:** Solves mixed-integer staff-to-counter and break scheduling with Google OR-Tools CP-SAT.
- **Response:**
  ```json
  {
    "solver_name": "Google OR-Tools CP-SAT",
    "solver_status": "OPTIMAL",
    "is_mathematically_proven": true,
    "allocated_counters": 4,
    "assignments": [...],
    "break_schedule": [...]
  }
  ```

### `POST /api/optimization/stochastic`
- **Description:** Solves Two-Stage Stochastic Program under demand uncertainty.

### `POST /api/optimization/scenarios`
- **Description:** Evaluates banking stress shocks (month-end, staff sickness, ATM outage) with BEFORE vs. AFTER comparison.

---

## 5. Discrete-Event Simulation Endpoints

### `POST /api/simulation/run`
- **Description:** Runs Monte Carlo discrete-event queue simulation with lognormal handling times, priority classes, and abandonment.

### `GET /api/simulation/erlang-c`
- **Description:** Returns theoretical $M/M/c$ delay benchmark using Erlang-C queueing formula.

---

## 6. Audit & Health Endpoints

### `GET /api/audit/verify`
- **Description:** Scans entire SHA-256 forward-linked cryptographic hash chain and verifies zero tampering.

### `GET /api/health`
- **Description:** Returns database health, dialect, and query latency.
