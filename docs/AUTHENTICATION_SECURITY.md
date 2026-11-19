# AUTHENTICATION & ACCESS CONTROL SPECIFICATION

**Module:** `services/auth_service.py`  
**Reference Benchmark:** `VitalOptima/services/auth_service.py`  

---

## 1. Password Hashing Specification

All passwords stored in the `users` table are hashed using PBKDF2-HMAC-SHA256 adhering to NIST SP 800-63B standards:
- **Hash Function:** PBKDF2 with HMAC-SHA-256
- **Iteration Count:** 600,000 iterations
- **Salt Generation:** 32 cryptographically random bytes via `secrets.token_bytes(32)`
- **Comparison Function:** Constant-time `hmac.compare_digest` to prevent timing attacks.
- **Serialization Format:**
  `pbkdf2:sha256:600000$<salt_hex>$<derived_hash_hex>`

---

## 2. Role-Based Access Control (RBAC) Matrix

| Permission String | Central Admin | Regional Manager | Branch Manager | Employee / Teller |
| :--- | :---: | :---: | :---: | :---: |
| `network.view` | ✅ | ✅ | ❌ | ❌ |
| `organization.manage` | ✅ | ❌ | ❌ | ❌ |
| `regions.manage` | ✅ | ❌ | ❌ | ❌ |
| `branches.manage` | ✅ | ❌ | ❌ | ❌ |
| `users.manage` | ✅ | ❌ | ❌ | ❌ |
| `audit.view` | ✅ | ✅ | ❌ | ❌ |
| `datasets.import` | ✅ | ❌ | ✅ (assigned branch) | ❌ |
| `forecasting.view` | ✅ | ✅ | ✅ | ❌ |
| `optimization.run` | ✅ | ❌ | ✅ | ❌ |
| `simulation.run` | ✅ | ❌ | ✅ | ❌ |
| `tokens.process` | ❌ | ❌ | ❌ | ✅ |
| `schedule.view` | ✅ | ✅ | ✅ | ✅ (own schedule) |
