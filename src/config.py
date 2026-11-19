"""
Centralized Configuration and Domain Constants for Bank AI Optimizer.
Loads environment variables, database connections, and operational parameters safely.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DOCS_DIR = BASE_DIR / "docs"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file
load_dotenv(BASE_DIR / ".env", override=True)

# Application Environment & Security Settings
APP_ENV = os.getenv("APP_ENV", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY", "apexbank-super-secure-production-secret-key-2026-xai")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Database Connection Helper
def get_database_url() -> str:
    """
    Retrieves and normalizes DATABASE_URL from environment.
    Converts postgresql:// to postgresql+psycopg2:// for SQLAlchemy 2.0.
    Falls back safely to local SQLite in development mode if URL is empty.
    """
    load_dotenv(BASE_DIR / ".env", override=True)
    raw_url = os.getenv("DATABASE_URL", "").strip()

    # Strip surrounding quotes if present
    if raw_url.startswith(('"', "'")) and raw_url.endswith(('"', "'")):
        raw_url = raw_url[1:-1].strip()

    if not raw_url:
        sqlite_fallback = f"sqlite:///{DATA_DIR / 'bank_optimizer.db'}"
        return sqlite_fallback

    # Convert standard postgresql URLs for psycopg2 driver
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return raw_url

def get_pooled_database_url() -> str:
    """Returns pooled connection URL if configured, otherwise default database URL."""
    pooled = os.getenv("DATABASE_URL_POOLED", "").strip()
    if pooled.startswith(('"', "'")) and pooled.endswith(('"', "'")):
        pooled = pooled[1:-1].strip()
    if pooled:
        if pooled.startswith("postgres://"):
            return pooled.replace("postgres://", "postgresql+psycopg2://", 1)
        elif pooled.startswith("postgresql://") and not pooled.startswith("postgresql+"):
            return pooled.replace("postgresql://", "postgresql+psycopg2://", 1)
        return pooled
    return get_database_url()

# Banking Service Categories & SLAs (in minutes)
SERVICE_CATEGORIES = {
    "Cash Deposit/Withdrawal": {
        "sla_wait_mins": 10.0,
        "avg_service_mins": 4.5,
        "digital_eligible": True,
        "digital_channel": "Cash Deposit Machine (CDM) / ATM",
        "digital_deflection_difficulty": "Low"
    },
    "Account Services & KYC": {
        "sla_wait_mins": 15.0,
        "avg_service_mins": 12.0,
        "digital_eligible": True,
        "digital_channel": "Mobile App / Video KYC Kiosk",
        "digital_deflection_difficulty": "Medium"
    },
    "Passbook / Statement Printing": {
        "sla_wait_mins": 8.0,
        "avg_service_mins": 3.0,
        "digital_eligible": True,
        "digital_channel": "Self-Service Passbook Kiosk",
        "digital_deflection_difficulty": "Very Low"
    },
    "Loan & Mortgage Advisory": {
        "sla_wait_mins": 25.0,
        "avg_service_mins": 28.0,
        "digital_eligible": False,
        "digital_channel": "Online Application + In-Branch Verification",
        "digital_deflection_difficulty": "High"
    },
    "Forex & Trade Finance": {
        "sla_wait_mins": 20.0,
        "avg_service_mins": 18.0,
        "digital_eligible": False,
        "digital_channel": "NetBanking Portal",
        "digital_deflection_difficulty": "High"
    },
    "Card Services & Pin Reset": {
        "sla_wait_mins": 12.0,
        "avg_service_mins": 6.0,
        "digital_eligible": True,
        "digital_channel": "ATM / Mobile App Self-Service",
        "digital_deflection_difficulty": "Very Low"
    },
    "Wealth & Investment Planning": {
        "sla_wait_mins": 20.0,
        "avg_service_mins": 35.0,
        "digital_eligible": False,
        "digital_channel": "Virtual Relationship Manager",
        "digital_deflection_difficulty": "High"
    }
}

# Customer Segment Priority Multipliers
CUSTOMER_SEGMENTS = {
    "Regular": {"priority_weight": 1.0, "patience_index": 1.0},
    "Senior Citizen": {"priority_weight": 1.5, "patience_index": 0.8},
    "High Net Worth (HNI/VIP)": {"priority_weight": 2.5, "patience_index": 0.6},
    "Small Business / SME": {"priority_weight": 1.8, "patience_index": 0.9}
}

# Sample Branch Network
BRANCH_NETWORK = [
    {"branch_id": "BR_001", "name": "Downtown Financial Hub", "cluster": "Metro Central", "total_counters": 10, "peak_window": "11:00-14:00"},
    {"branch_id": "BR_002", "name": "Suburban Tech Park", "cluster": "Metro Central", "total_counters": 8, "peak_window": "12:00-15:00"},
    {"branch_id": "BR_003", "name": "Old Town Commercial", "cluster": "Metro Central", "total_counters": 6, "peak_window": "10:30-13:30"},
    {"branch_id": "BR_004", "name": "Green Valley Residential", "cluster": "East Suburbs", "total_counters": 5, "peak_window": "09:30-12:00"},
    {"branch_id": "BR_005", "name": "Airport Transit Branch", "cluster": "West Suburbs", "total_counters": 7, "peak_window": "14:00-17:30"}
]
