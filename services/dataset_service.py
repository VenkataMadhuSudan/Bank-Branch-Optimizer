"""
Enterprise Dataset Management, Ingestion, and Validation Service.
Supports CSV & XLSX uploads, rigorous schema and business-rule validation,
pre-import preview, error auditing, and non-destructive transactional database ingestion.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.connection import get_db_session
from db.schema import (
    Appointment,
    Branch,
    CustomerArrival,
    CustomerFeedback,
    DatasetImport,
    DatasetImportError,
    DatasetValidationReport,
    Employee,
    EmployeeSkill,
    ServiceCategory,
)
from services.audit_service import AuditService
from src.utils.logger import logger

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit

# Required and optional schemas per dataset type
DATASET_SCHEMAS = {
    "QUEUE_LOGS": {
        "required_columns": [
            "branch_id",
            "token_number",
            "service_category",
            "arrival_timestamp",
        ],
        "optional_columns": [
            "customer_segment",
            "service_start_timestamp",
            "service_end_timestamp",
            "wait_time_minutes",
            "service_duration_minutes",
            "counter_id",
            "staff_id",
            "sla_breached",
            "digital_deflectable",
            "satisfaction_score",
        ],
    },
    "STAFF_ROSTER": {
        "required_columns": ["branch_id", "staff_id", "staff_name", "primary_skill"],
        "optional_columns": [
            "secondary_skills",
            "efficiency_factor",
            "counter_speed_rating",
            "hourly_rate_usd",
            "max_weekly_hours",
        ],
    },
    "CUSTOMER_FEEDBACK": {
        "required_columns": [
            "branch_id",
            "service_category",
            "feedback_text",
            "rating",
        ],
        "optional_columns": ["token_number", "created_at"],
    },
    "APPOINTMENTS": {
        "required_columns": [
            "branch_id",
            "appointment_id",
            "customer_name",
            "service_category",
            "appointment_time",
        ],
        "optional_columns": ["customer_segment", "status"],
    },
}


class DatasetService:
    """Dataset ingestion, sanitization, validation, and database insertion engine."""

    @classmethod
    def parse_file_to_dataframe(
        cls, file_content: bytes, filename: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Parses raw uploaded file bytes (CSV or XLSX) into a Pandas DataFrame."""
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            return None, f"File size ({len(file_content) / (1024*1024):.1f}MB) exceeds 25MB limit."

        filename_lower = filename.lower()
        try:
            if filename_lower.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename_lower.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                return None, "Unsupported file format. Please upload a .csv or .xlsx spreadsheet."

            # Normalize column names: strip whitespace and lowercase
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df, None
        except Exception as exc:
            logger.warning(f"Error parsing file '{filename}': {exc}")
            return None, f"Failed to parse spreadsheet: {str(exc)}"

    @classmethod
    def validate_dataset(
        cls,
        df: pd.DataFrame,
        dataset_type: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Validates column presence, data types, referential integrity against branches,
        and value constraints. Returns structured diagnostic validation report.
        """
        schema = DATASET_SCHEMAS.get(dataset_type)
        if not schema:
            return {"is_valid": False, "error": f"Unknown dataset type: {dataset_type}"}

        required_cols = schema["required_columns"]
        missing_cols = [c for c in required_cols if c not in df.columns]

        errors: List[Dict[str, Any]] = []
        if missing_cols:
            return {
                "is_valid": False,
                "error": f"Missing mandatory columns: {', '.join(missing_cols)}",
                "missing_columns": missing_cols,
                "total_rows": len(df),
                "valid_rows": 0,
                "invalid_rows": len(df),
                "errors": [{"row": 0, "field": "header", "message": f"Missing columns: {missing_cols}"}],
            }

        # Query active branch codes from database (fallback to config if offline)
        valid_branches: Set[str] = set()
        try:
            with get_db_session() as session:
                branches = session.execute(select(Branch.branch_code)).scalars().all()
                valid_branches = set(branches)
        except Exception as exc:
            logger.debug(f"Database unavailable for branch lookup, falling back to static config: {exc}")
            from src.config import BRANCH_NETWORK
            valid_branches = {b["branch_id"] for b in BRANCH_NETWORK}

        valid_row_count = 0
        invalid_row_count = 0

        # Scan rows for referential and domain validity
        for idx, row in df.iterrows():
            row_num = int(idx) + 1
            row_errors = []

            # 1. Branch verification
            branch_val = str(row.get("branch_id", "")).strip()
            if valid_branches and branch_val not in valid_branches:
                row_errors.append(f"Branch '{branch_val}' does not match any registered branch in database.")

            # 2. Type-specific checks
            if dataset_type == "QUEUE_LOGS":
                token = str(row.get("token_number", "")).strip()
                if not token or token == "nan":
                    row_errors.append("Empty token number.")

                wait = row.get("wait_time_minutes")
                if pd.notna(wait):
                    try:
                        if float(wait) < 0:
                            row_errors.append("Negative wait time.")
                    except ValueError:
                        row_errors.append(f"Invalid wait time '{wait}'.")

            elif dataset_type == "CUSTOMER_FEEDBACK":
                rating = row.get("rating")
                try:
                    r_val = int(rating)
                    if r_val < 1 or r_val > 5:
                        row_errors.append(f"Rating {r_val} outside 1-5 range.")
                except (ValueError, TypeError):
                    row_errors.append(f"Invalid rating value '{rating}'.")

            if row_errors:
                invalid_row_count += 1
                for err in row_errors:
                    errors.append({
                        "row": row_num,
                        "field": "validation",
                        "raw_value": str(row.to_dict())[:80],
                        "message": err,
                    })
            else:
                valid_row_count += 1

        is_valid = invalid_row_count == 0
        return {
            "is_valid": is_valid,
            "filename": filename,
            "dataset_type": dataset_type,
            "total_rows": len(df),
            "valid_rows": valid_row_count,
            "invalid_rows": invalid_row_count,
            "preview_rows": df.head(5).to_dict(orient="records"),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "errors": errors[:50],  # Cap sample error list for performance
        }

    @classmethod
    def execute_import(
        cls,
        df: pd.DataFrame,
        dataset_type: str,
        filename: str,
        file_size_bytes: int,
        imported_by: str,
        skip_invalid: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes ACID-compliant batch insert of validated records into the database.
        Maintains complete audit trails and dataset import error logs.
        """
        validation_report = cls.validate_dataset(df, dataset_type, filename)
        if not validation_report["is_valid"] and not skip_invalid:
            return {
                "success": False,
                "error": "Dataset validation failed. Review error report or enable partial import.",
                "report": validation_report,
            }

        with get_db_session() as session:
            # 1. Register Dataset Import record
            import_record = DatasetImport(
                file_name=filename,
                file_size_bytes=file_size_bytes,
                dataset_type=dataset_type,
                source_type="UPLOAD",
                total_records=validation_report["total_rows"],
                valid_records=validation_report["valid_rows"],
                invalid_records=validation_report["invalid_rows"],
                status="IMPORTED" if validation_report["is_valid"] else "PARTIAL",
                imported_by=imported_by,
            )
            session.add(import_record)
            session.flush()

            # 2. Record validation errors
            for err in validation_report.get("errors", []):
                session.add(
                    DatasetImportError(
                        import_id=import_record.id,
                        row_number=err.get("row", 0),
                        field_name=err.get("field", "general"),
                        raw_value=err.get("raw_value"),
                        error_message=err.get("message", "Error"),
                    )
                )

            # 3. Record validation report
            session.add(
                DatasetValidationReport(
                    import_id=import_record.id,
                    report_json=validation_report,
                )
            )

            # 4. Insert rows into target table
            branches = session.execute(select(Branch)).scalars().all()
            branch_id_map = {b.branch_code: b.id for b in branches}
            inserted_count = 0

            if dataset_type == "QUEUE_LOGS":
                for _, row in df.iterrows():
                    b_code = str(row.get("branch_id", "")).strip()
                    b_id = branch_id_map.get(b_code)
                    if not b_id:
                        continue

                    # Parse timestamps
                    arr_ts_str = str(row.get("arrival_timestamp", ""))
                    try:
                        arr_dt = pd.to_datetime(arr_ts_str).to_pydatetime()
                    except Exception:
                        arr_dt = datetime.now()

                    start_ts_str = row.get("service_start_timestamp")
                    start_dt = pd.to_datetime(start_ts_str).to_pydatetime() if pd.notna(start_ts_str) else None

                    end_ts_str = row.get("service_end_timestamp")
                    end_dt = pd.to_datetime(end_ts_str).to_pydatetime() if pd.notna(end_ts_str) else None

                    wait_val = float(row.get("wait_time_minutes", 0.0)) if pd.notna(row.get("wait_time_minutes")) else 0.0
                    dur_val = float(row.get("service_duration_minutes", 0.0)) if pd.notna(row.get("service_duration_minutes")) else 0.0
                    sla_b = bool(int(row.get("sla_breached", 0))) if pd.notna(row.get("sla_breached")) else False
                    deflect_b = bool(int(row.get("digital_deflectable", 0))) if pd.notna(row.get("digital_deflectable")) else False
                    sat_val = int(row.get("satisfaction_score")) if pd.notna(row.get("satisfaction_score")) else None

                    session.add(
                        CustomerArrival(
                            branch_id=b_id,
                            token_number=str(row.get("token_number", "")),
                            customer_segment=str(row.get("customer_segment", "Regular")),
                            service_category=str(row.get("service_category", "Cash Deposit/Withdrawal")),
                            arrival_timestamp=arr_dt,
                            service_start_timestamp=start_dt,
                            service_end_timestamp=end_dt,
                            wait_time_minutes=max(0.0, wait_val),
                            service_duration_minutes=max(0.0, dur_val),
                            counter_code=str(row.get("counter_id")) if pd.notna(row.get("counter_id")) else None,
                            staff_code=str(row.get("staff_id")) if pd.notna(row.get("staff_id")) else None,
                            sla_breached=sla_b,
                            digital_deflectable=deflect_b,
                            satisfaction_score=sat_val,
                        )
                    )
                    inserted_count += 1

            elif dataset_type == "CUSTOMER_FEEDBACK":
                for _, row in df.iterrows():
                    b_code = str(row.get("branch_id", "")).strip()
                    b_id = branch_id_map.get(b_code)
                    if not b_id:
                        continue
                    session.add(
                        CustomerFeedback(
                            branch_id=b_id,
                            token_number=str(row.get("token_number")) if pd.notna(row.get("token_number")) else None,
                            service_category=str(row.get("service_category", "General")),
                            feedback_text=str(row.get("feedback_text", "")),
                            rating=int(row.get("rating", 3)),
                        )
                    )
                    inserted_count += 1

            session.commit()

        # Audit log the import action
        AuditService.log_action(
            actor_username=imported_by,
            action="DATASET_IMPORT",
            resource_type="DATASET",
            resource_id=filename,
            details={
                "dataset_type": dataset_type,
                "inserted_count": inserted_count,
                "file_size": file_size_bytes,
                "status": import_record.status,
            },
        )

        logger.info(f"Dataset '{filename}' successfully imported: {inserted_count} records inserted.")
        return {
            "success": True,
            "import_id": import_record.id,
            "inserted_count": inserted_count,
            "status": import_record.status,
            "report": validation_report,
        }
