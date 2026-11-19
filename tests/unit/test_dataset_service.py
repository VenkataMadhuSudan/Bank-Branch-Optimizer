"""
Unit Tests for Dataset Management, Validation, and Ingestion.
"""
import pytest
import pandas as pd
from services.dataset_service import DatasetService


def test_parse_valid_csv():
    """Verifies that CSV byte streams parse correctly into DataFrames."""
    csv_bytes = b"branch_id,token_number,service_category,arrival_timestamp\nBR_001,T001,Cash Deposit/Withdrawal,2026-11-19 10:00:00\n"
    df, err = DatasetService.parse_file_to_dataframe(csv_bytes, "tokens.csv")
    assert err is None
    assert df is not None
    assert len(df) == 1
    assert "branch_id" in df.columns
    assert df.iloc[0]["token_number"] == "T001"


def test_reject_unsupported_file_extension():
    """Verifies that non-spreadsheet file extensions are rejected."""
    txt_bytes = b"just some text"
    df, err = DatasetService.parse_file_to_dataframe(txt_bytes, "malicious.exe")
    assert df is None
    assert "Unsupported file format" in err


def test_missing_mandatory_columns():
    """Verifies that missing required columns fail validation with structured error."""
    csv_bytes = b"token_number,arrival_timestamp\nT001,2026-11-19 10:00:00\n"
    df, _ = DatasetService.parse_file_to_dataframe(csv_bytes, "incomplete.csv")
    report = DatasetService.validate_dataset(df, "QUEUE_LOGS", "incomplete.csv")
    assert report["is_valid"] is False
    assert "branch_id" in report["missing_columns"]


def test_invalid_negative_wait_time_detection():
    """Verifies that negative wait times are flagged as invalid rows."""
    df = pd.DataFrame([
        {
            "branch_id": "BR_001",
            "token_number": "T001",
            "service_category": "Cash Deposit/Withdrawal",
            "arrival_timestamp": "2026-11-19 10:00:00",
            "wait_time_minutes": -5.0  # Invalid!
        }
    ])
    report = DatasetService.validate_dataset(df, "QUEUE_LOGS", "invalid_wait.csv")
    assert report["is_valid"] is False
    assert report["invalid_rows"] == 1
    assert any("Negative wait time" in e["message"] for e in report["errors"])

