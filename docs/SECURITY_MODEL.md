# ENTERPRISE CYBERSECURITY & THREAT MODEL

**Module:** `services/auth_service.py`, `services/audit_service.py`, `api/dependencies.py`  
**Compliance Standards:** NIST SP 800-63B (Digital Identity Guidelines), OWASP Top 10  
**Reference Benchmark:** `VitalOptima/docs/SECURITY_MODEL.md`  

---

## 1. Threat Vectors & Defense In Depth

| Threat Vector | Potential Impact | Implemented Countermeasure | Verification Test |
| :--- | :--- | :--- | :--- |
| **Credential Cracking / Brute Force** | Unauthorized account takeover | PBKDF2-HMAC-SHA256 (600,000 iterations) + Account Lockout (5 failed attempts locks for 15m) | `test_account_lockout_throttling` |
| **Horizontal Privilege Escalation** | Branch Manager 1 accesses Branch 2 records | Backend-enforced Branch Data Isolation (`check_branch_access`) | `test_branch_level_data_isolation` |
| **Vertical Privilege Escalation** | Teller executes administrative user provisioning | Centralized RBAC matrix (`ROLE_PERMISSIONS`) enforced in API dependency layer | `test_user_roles_and_branch_permissions` |
| **Audit Ledger Tampering** | Malicious insider deletes or modifies historical logs | SHA-256 Forward-Linked Cryptographic Hash Chain | `test_audit_hash_chain_computation` |
| **SQL Injection** | Database compromise or exfiltration | Parameterized Queries exclusively via SQLAlchemy 2.0 ORM | `test_organization_region_branch_hierarchy` |
| **Credential Leakage in Logs** | Secrets exposed in monitoring stdout | `CredentialRedactionFilter` regex scrubbing passwords & tokens | `setup_logger` sanitization filter |
| **Session Hijacking** | Forged authentication tokens | Cryptographically signed JWT tokens with expiration & HS256 secret key | `test_jwt_access_token_lifecycle` |

---

## 2. Multi-Branch Data Isolation Guarantee

A fundamental security invariant is that branch-level data isolation is enforced in backend services, not merely in UI controls:
```python
def check_branch_access(user: Dict[str, Any], branch_id: int, required_capability: str = "can_view") -> bool:
    roles = user.get("roles", [])
    if ROLE_CENTRAL_ADMIN in roles or ROLE_REGIONAL_MANAGER in roles:
        return True
    
    # Strictly require explicit branch permission record
    for bp in user.get("branch_permissions", []):
        if bp.get("branch_id") == branch_id:
            return bool(bp.get(required_capability, False))
    return False
```
Proved by automated tests in `tests/security/test_auth_and_rbac.py`.
