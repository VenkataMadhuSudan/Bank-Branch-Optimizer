# DATA GOVERNANCE & INGESTION ARCHITECTURE

**Module:** `services/dataset_service.py`, `src/data_pipeline.py`  
**Supported Formats:** CSV, XLSX  

---

## 1. Principles of Data Integrity

1. **Non-Destructive Processing:** The platform strictly prohibits silent discarding of invalid records or automatic overwriting of operational datasets with synthetic data.
2. **Pre-Import Schema Validation:** Every uploaded spreadsheet undergoes pre-import column matching, data type verification, and referential integrity checks against active branches before any database write occurs.
3. **Downloadable Audit Reports:** Failed or partially imported datasets generate a structured `DatasetValidationReport` and individual `DatasetImportError` records detailing row numbers, rejected fields, and error rationales.
4. **Distinct Source Tagging:** Real uploaded data (`source_type="UPLOAD"`), synthetic telemetry (`source_type="SYNTHETIC"`), and simulated data (`source_type="SIMULATION"`) are explicitly distinguished in metadata tables.

---

## 2. Ingestion Validation Pipeline

```
   Raw Upload (CSV / XLSX)
            │
            ▼
   1. File Size Verification (Max 25MB)
            │
            ▼
   2. Column Detection & Normalization
            │
            ▼
   3. Referential Foreign Key Checks (Branch IDs & Staff Codes)
            │
            ▼
   4. Domain Bound Constraints (Wait times >= 0, Ratings 1-5)
            │
            ├─► If Invalid: Return Diagnostic Report (Zero DB commits)
            │
            ▼
   5. ACID Batch Transaction Commit (CustomerArrivals / Feedback / Roster)
            │
            ▼
   6. Cryptographic Audit Log Emitted (AuditService)
```
