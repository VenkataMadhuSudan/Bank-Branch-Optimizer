# AUTOMATED TESTING & VERIFICATION STRATEGY

**Framework:** Pytest 8.x / Pytest-Cov  
**Total Automated Tests:** 48 Passing Tests (100% Pass Rate)  
**Execution Time:** ~8 seconds offline suite, ~56 seconds full live PostgreSQL suite  

---

## 1. Test Package Organization

The test suite is structured into dedicated operational and subsystem packages:

```
tests/
├── unit/
│   ├── test_database.py              # In-memory sessions, health check, rollback integrity
│   ├── test_schema.py                # 41 table definitions, cascades, FK constraints
│   └── test_dataset_service.py       # CSV parsing, missing column validation, negative value checks
├── security/
│   └── test_auth_and_rbac.py         # PBKDF2 600k hashing, account lockout, JWT, branch data isolation
├── forecasting/
│   └── test_forecasting.py           # Chronological validation, WAPE, conformal bands, wait time dual head
├── optimization/
│   └── test_staff_optimizer.py       # OR-Tools CP-SAT optimality, uniqueness constraints, break staggering
├── simulation/
│   └── test_queue_and_stochastic.py  # Erlang-C formula, RNG reproducibility, abandonment, 2-stage stochastic
├── operational/
│   ├── test_operational_intelligence.py # Grounded explainability, sentiment topics, deflection DDI
│   └── test_database_failure.py      # Concurrent thread writes, SHA-256 hash chain verification
└── api/
    └── test_api_endpoints.py         # FastAPI TestClient integration across all mounted routers
```

---

## 2. Test Execution Commands

### Run Complete Offline Suite (No Network Dependency):
```bash
python -m pytest tests/unit tests/security tests/forecasting tests/optimization tests/simulation tests/operational -v
```

### Run Full Test Suite with Integration Endpoints:
```bash
python -m pytest tests/ -v
```

### Run with Coverage Metrics:
```bash
python -m pytest tests/ --cov=src --cov=services --cov=db --cov-report=term-missing
```

