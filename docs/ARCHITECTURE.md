# SYSTEM ARCHITECTURE: BANK AI OPTIMIZER

**Author:** Antigravity Principal Architecture Team  
**System Classification:** Enterprise Banking Operations Intelligence & Resource Optimization Platform  
**Target Maturity:** VitalOptima Architectural Equivalence & Beyond  

---

## 1. High-Level Architectural Topology

```
+---------------------------------------------------------------------------------+
|                               PRESENTATION TIER                                |
|  Streamlit Multi-Persona Cockpit (Central Admin, Regional, Branch Mgr, Teller) |
+----------------------------------------+----------------------------------------+
                                         | REST / Session
                                         v
+---------------------------------------------------------------------------------+
|                                APPLICATION TIER                                |
|           FastAPI Modular Router Architecture (Asynchronous & Pydantic v2)     |
|   /api/auth  /api/branches  /api/forecasts  /api/optimization  /api/simulation |
|   /api/intelligence         /api/datasets   /api/audit         /api/health     |
+----------------------------------------+----------------------------------------+
                                         | Service Layer Boundaries
                                         v
+---------------------------------------------------------------------------------+
|                                  SERVICE TIER                                  |
|   +-----------------------+ +-----------------------+ +-----------------------+ |
|   |     AuthService       | |     AuditService      | |    DatasetService     | |
|   | PBKDF2 600k / RBAC    | | SHA-256 Hash Chain    | | Schema Ingestion CSV  | |
|   +-----------------------+ +-----------------------+ +-----------------------+ |
|   +-----------------------+ +-----------------------+ +-----------------------+ |
|   |   DemandForecaster    | |  StaffCounterOpt      | |  BranchQueueSimulator | |
|   | Chronological Conformal| | OR-Tools CP-SAT MILP  | | Discrete-Event MonteC | |
|   +-----------------------+ +-----------------------+ +-----------------------+ |
|   +-----------------------+ +-----------------------+ +-----------------------+ |
|   |  StochasticOptimizer  | |   ScenarioSimulator   | |  ExplainabilityEngine | |
|   | Two-Stage Recourse    | | Stress Shock Testing  | | Evidence-Grounded XAI | |
|   +-----------------------+ +-----------------------+ +-----------------------+ |
+----------------------------------------+----------------------------------------+
                                         | Transactional Sessions
                                         v
+---------------------------------------------------------------------------------+
|                               PERSISTENCE TIER                                  |
|  SQLAlchemy 2.0 Modern Declarative ORM | Connection Pooling | Alembic Migrations |
|  Authoritative: Neon Serverless PostgreSQL | Local Dev Fallback: SQLite         |
+---------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Decoupled Tier Separation:** UI (`app.py`), API (`server.py`), Domain Services (`services/`, `src/models/`, `src/optimization/`), and Persistence (`db/`) are strictly separated.
2. **Zero Import-Time Side Effects:** Training ML models at startup has been completely eliminated. Training workflows are explicit and decoupled.
3. **Defense-in-Depth Security:** RBAC and branch-level data isolation are enforced in backend services rather than relying merely on UI component hiding.
4. **Authoritative ACID Persistence:** Replaces static CSV memory reads with normalized relational PostgreSQL tables.
5. **Non-Destructive Initialization:** Tables, constraints, and initial seeds are verified idempotently without dropping tables or discarding operational records.
6. **Scientific Rigor & Honest Reporting:** Heuristic fallbacks are explicitly labeled as `HEURISTIC_FALLBACK` and never falsely reported as optimal mathematical proofs.
