"""
UI Helpers, Custom CSS Styling, and Visual Badge Utilities for Streamlit Application.
Enforces Black Left Sidebar with white text, and Clean White Main Dashboard with dark text.
"""

CUSTOM_CSS = """
<style>
    /* Global Font & Reset */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ========================================================
       1. RIGHT / MAIN DASHBOARD AREA: CRISP WHITE BACKGROUND
       ======================================================== */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    
    /* Main Area Typography & Text */
    [data-testid="stMain"] h1, 
    [data-testid="stMain"] h2, 
    [data-testid="stMain"] h3, 
    [data-testid="stMain"] h4, 
    [data-testid="stMain"] h5, 
    [data-testid="stMain"] h6 {
        color: #0f172a !important;
        font-weight: 700;
    }
    
    [data-testid="stMain"] p, 
    [data-testid="stMain"] span, 
    [data-testid="stMain"] label,
    [data-testid="stMain"] li,
    [data-testid="stMain"] .stMarkdown {
        color: #1e293b !important;
    }
    
    [data-testid="stMain"] .stCaption, 
    [data-testid="stMain"] small {
        color: #64748b !important;
    }

    /* Main Area Dividers */
    [data-testid="stMain"] hr {
        border-color: #e2e8f0 !important;
    }

    /* Main Area Form Controls & Selectboxes: Crisp White with Dark Text */
    [data-testid="stMain"] div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    
    [data-testid="stMain"] div[data-baseweb="select"] div,
    [data-testid="stMain"] div[data-baseweb="select"] span,
    [data-testid="stMain"] div[data-baseweb="select"] p,
    [data-testid="stMain"] div[data-baseweb="select"] svg {
        color: #0f172a !important;
        font-weight: 600 !important;
        fill: #0f172a !important;
    }
    
    /* Dropdown popover menu options */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] ul {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
    }
    
    div[data-baseweb="popover"] li {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-weight: 500 !important;
    }
    
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #eff6ff !important;
        color: #2563eb !important;
    }

    [data-testid="stMain"] input,
    [data-testid="stMain"] textarea {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* ========================================================
       2. LEFT SIDEBAR AREA: SOLID BLACK BACKGROUND
       ======================================================== */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarNav"] {
        background-color: #000000 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Sidebar Typography */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] strong {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #f1f5f9 !important;
    }
    
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {
        color: #94a3b8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #334155 !important;
    }

    /* Sidebar Form Controls & Inputs */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #2563eb !important;
        border-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    
    /* ========================================================
       3. CUSTOM CARDS & COMPONENTS FOR WHITE DASHBOARD
       ======================================================== */
    /* Header / Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f5f3ff 100%);
        border: 1px solid #bae6fd;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(14, 165, 233, 0.08);
    }
    
    .hero-title {
        font-size: 24px;
        font-weight: 800;
        color: #0369a1 !important;
        margin-bottom: 6px;
    }
    
    .hero-subtitle {
        color: #475569 !important;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 0px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.07);
        border-color: #3b82f6;
    }
    .metric-label {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b !important;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a !important;
        line-height: 1.2;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 600;
        margin-top: 6px;
    }
    .delta-green { color: #059669 !important; }
    .delta-red { color: #dc2626 !important; }
    .delta-blue { color: #2563eb !important; }
    
    /* Alert Badges */
    .badge-critical {
        background: #fef2f2;
        color: #b91c1c !important;
        border: 1px solid #fca5a5;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-warning {
        background: #fffbeb;
        color: #b45309 !important;
        border: 1px solid #fcd34d;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-optimal {
        background: #ecfdf5;
        color: #047857 !important;
        border: 1px solid #6ee7b7;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
    }
    
    /* Action Box */
    .action-box {
        background: #f8fafc;
        border-left: 4px solid #2563eb;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 12px 0;
        color: #1e293b !important;
    }

    /* Main Area Native Streamlit Metric overrides */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    
    /* Streamlit Alert / Info Box Styling */
    [data-testid="stAlert"] {
        background-color: #f0fdf4 !important;
        color: #166534 !important;
        border: 1px solid #bbf7d0 !important;
        border-radius: 10px !important;
    }
</style>
"""

def render_metric_card(label: str, value: str, delta: str = "", delta_color: str = "blue"):
    color_class = f"delta-{delta_color}"
    delta_html = f'<div class="metric-delta {color_class}">{delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def get_status_badge(status_text: str):
    lower = status_text.lower()
    if "critical" in lower or "breach" in lower or "surge" in lower or "high" in lower:
        return f'<span class="badge-critical">⚠️ {status_text}</span>'
    elif "moderate" in lower or "warning" in lower:
        return f'<span class="badge-warning">⚡ {status_text}</span>'
    else:
        return f'<span class="badge-optimal">✓ {status_text}</span>'

COUNTER_TEMPLATES = [
    {
        "counter_num": 1,
        "desk_name": "Counter 1 — Express Cash & Deposits",
        "service": "Cash Deposit/Withdrawal",
        "staff_name": "Sarah Jenkins",
        "staff_role": "Senior Teller (Speed Specialist)",
        "active_token": "TKN-1048",
        "customer_name": "Robert Henderson",
        "customer_segment": "High Net Worth (HNI/VIP)",
        "service_timer": "03:42",
        "wait_time_mins": 4.5,
        "amount_note": "Cash Deposit ($4,500) — Priority Desk",
        "today_served": 34,
        "aht_mins": 4.8,
        "csat_score": 4.92,
        "queue_depth": 3,
        "deflectable": True,
        "deflection_channel": "Cash Deposit Machine (CDM)",
        "upcoming_queue": [
            {"token": "TKN-1052", "name": "Elena Torres", "service": "Cash Deposit", "wait": "3.5 min", "segment": "Regular"},
            {"token": "TKN-1055", "name": "Marcus Wright", "service": "Cheque Encashment", "wait": "7.0 min", "segment": "Regular"},
            {"token": "TKN-1059", "name": "Linda Wu", "service": "Cash Withdrawal", "wait": "11.2 min", "segment": "Senior Citizen"}
        ]
    },
    {
        "counter_num": 2,
        "desk_name": "Counter 2 — High-Volume Cash & Bulk Merchant Payments",
        "service": "Cash Deposit/Withdrawal",
        "staff_name": "Michael Chang",
        "staff_role": "Cash Management Officer",
        "active_token": "TKN-1065",
        "customer_name": "David K. Anderson",
        "customer_segment": "Small Business / SME",
        "service_timer": "07:15",
        "wait_time_mins": 9.8,
        "amount_note": "Multi-Cheque Bulk Deposit (12 cheques)",
        "today_served": 26,
        "aht_mins": 6.4,
        "csat_score": 4.78,
        "queue_depth": 6,
        "deflectable": True,
        "deflection_channel": "Smart Bulk Drop-Box / Kiosk",
        "upcoming_queue": [
            {"token": "TKN-1068", "name": "Metro Retail LLC", "service": "Store Cash Float", "wait": "8.5 min", "segment": "Small Business / SME"},
            {"token": "TKN-1071", "name": "Priya Patel", "service": "Cash Deposit", "wait": "14.0 min", "segment": "Regular"},
            {"token": "TKN-1076", "name": "Apex Logix Corp", "service": "Payroll Cheques", "wait": "19.5 min", "segment": "Small Business / SME"}
        ]
    },
    {
        "counter_num": 3,
        "desk_name": "Counter 3 — Account Services & KYC Onboarding",
        "service": "Account Services & KYC",
        "staff_name": "Priya Sharma",
        "staff_role": "KYC & Verification Specialist",
        "active_token": "TKN-1072",
        "customer_name": "Mei-Ling Zhou",
        "customer_segment": "Regular",
        "service_timer": "11:20",
        "wait_time_mins": 14.2,
        "amount_note": "Re-KYC & Biometric Signature Verification",
        "today_served": 18,
        "aht_mins": 13.2,
        "csat_score": 4.85,
        "queue_depth": 4,
        "deflectable": True,
        "deflection_channel": "Video KYC / Mobile App Kiosk",
        "upcoming_queue": [
            {"token": "TKN-1078", "name": "Ahmed Hassan", "service": "Address Update & Nominee", "wait": "12.0 min", "segment": "Regular"},
            {"token": "TKN-1083", "name": "Clara Evans", "service": "Joint Acct Modification", "wait": "21.5 min", "segment": "Senior Citizen"},
            {"token": "TKN-1088", "name": "Jordan Bell", "service": "Tax ID / FATCA Form", "wait": "28.0 min", "segment": "Regular"}
        ]
    },
    {
        "counter_num": 4,
        "desk_name": "Counter 4 — Loan & Mortgage Advisory",
        "service": "Loan & Mortgage Advisory",
        "staff_name": "David Miller",
        "staff_role": "Senior Credit Underwriter",
        "active_token": "TKN-1095",
        "customer_name": "Eleanor Vance",
        "customer_segment": "Senior Citizen",
        "service_timer": "18:40",
        "wait_time_mins": 22.5,
        "amount_note": "Home Mortgage Pre-Approval Assessment",
        "today_served": 8,
        "aht_mins": 27.5,
        "csat_score": 4.90,
        "queue_depth": 2,
        "deflectable": False,
        "deflection_channel": "In-Person Specialist Required",
        "upcoming_queue": [
            {"token": "TKN-1102", "name": "Samuel Jackson", "service": "Auto Loan Restructure", "wait": "18.0 min", "segment": "Regular"},
            {"token": "TKN-1115", "name": "Venture Studio Ltd", "service": "Working Capital Loan", "wait": "42.0 min", "segment": "Small Business / SME"}
        ]
    },
    {
        "counter_num": 5,
        "desk_name": "Counter 5 — Forex & Trade Finance Desk",
        "service": "Forex & Trade Finance",
        "staff_name": "Elena Rostova",
        "staff_role": "Cross-Border FX Specialist",
        "active_token": "TKN-1110",
        "customer_name": "Farhan Siddiqui",
        "customer_segment": "Small Business / SME",
        "service_timer": "14:12",
        "wait_time_mins": 16.0,
        "amount_note": "Import Letter of Credit (LC) & EUR Wire",
        "today_served": 12,
        "aht_mins": 17.8,
        "csat_score": 4.88,
        "queue_depth": 2,
        "deflectable": False,
        "deflection_channel": "In-Person Specialist Required",
        "upcoming_queue": [
            {"token": "TKN-1122", "name": "Global Traders Inc", "service": "Foreign Inward Remittance", "wait": "15.0 min", "segment": "Small Business / SME"},
            {"token": "TKN-1128", "name": "Tanya Becker", "service": "Travel Forex Card Reload", "wait": "28.0 min", "segment": "Regular"}
        ]
    },
    {
        "counter_num": 6,
        "desk_name": "Counter 6 — Wealth & Priority Banking",
        "service": "Wealth & Investment Planning",
        "staff_name": "Marcus Vance",
        "staff_role": "Senior Relationship Manager",
        "active_token": "TKN-1134",
        "customer_name": "Arthur Sterling",
        "customer_segment": "High Net Worth (HNI/VIP)",
        "service_timer": "22:10",
        "wait_time_mins": 6.0,
        "amount_note": "Portfolio Rebalancing & Mutual Fund Allocation",
        "today_served": 7,
        "aht_mins": 34.0,
        "csat_score": 4.98,
        "queue_depth": 1,
        "deflectable": False,
        "deflection_channel": "Virtual Relationship Manager",
        "upcoming_queue": [
            {"token": "TKN-1140", "name": "Dr. Aris Thorne", "service": "Fixed Deposit & Bond Roll", "wait": "12.0 min", "segment": "High Net Worth (HNI/VIP)"}
        ]
    },
    {
        "counter_num": 7,
        "desk_name": "Counter 7 — Card Services & PIN / Kiosk Triage",
        "service": "Card Services & Pin Reset",
        "staff_name": "Anita Desai",
        "staff_role": "Customer Service Associate",
        "active_token": "TKN-1158",
        "customer_name": "Lucas Silva",
        "customer_segment": "Regular",
        "service_timer": "02:35",
        "wait_time_mins": 5.1,
        "amount_note": "Lost Debit Card Replacement & Green PIN",
        "today_served": 38,
        "aht_mins": 4.9,
        "csat_score": 4.70,
        "queue_depth": 5,
        "deflectable": True,
        "deflection_channel": "Lobby Card Kiosk / Mobile App",
        "upcoming_queue": [
            {"token": "TKN-1162", "name": "Emily Watson", "service": "Credit Card Limit Enhancement", "wait": "4.0 min", "segment": "Regular"},
            {"token": "TKN-1166", "name": "George Brown", "service": "Contactless Activation", "wait": "8.5 min", "segment": "Senior Citizen"},
            {"token": "TKN-1170", "name": "Nadia Ali", "service": "PIN Block Reset", "wait": "13.0 min", "segment": "Regular"}
        ]
    },
    {
        "counter_num": 8,
        "desk_name": "Counter 8 — Senior Citizen & Assisted Services",
        "service": "Passbook / Statement Printing",
        "staff_name": "Carlos Gomez",
        "staff_role": "Assisted Banking Greeter",
        "active_token": "TKN-1175",
        "customer_name": "Sophia Martinez",
        "customer_segment": "Senior Citizen",
        "service_timer": "04:50",
        "wait_time_mins": 3.8,
        "amount_note": "Pension Credit Verification & Passbook Print",
        "today_served": 31,
        "aht_mins": 5.2,
        "csat_score": 4.96,
        "queue_depth": 2,
        "deflectable": True,
        "deflection_channel": "Self-Service Passbook Kiosk",
        "upcoming_queue": [
            {"token": "TKN-1180", "name": "Harold Jenkins", "service": "Life Certificate Submission", "wait": "5.0 min", "segment": "Senior Citizen"},
            {"token": "TKN-1185", "name": "Mary O'Sullivan", "service": "Passbook Barcode Scan", "wait": "9.5 min", "segment": "Senior Citizen"}
        ]
    },
    {
        "counter_num": 9,
        "desk_name": "Counter 9 — SME & Commercial Fast-Track",
        "service": "Account Services & KYC",
        "staff_name": "Fatima Al-Sayed",
        "staff_role": "Commercial Banking Associate",
        "active_token": "TKN-1192",
        "customer_name": "Apex Cargo Logistics",
        "customer_segment": "Small Business / SME",
        "service_timer": "08:15",
        "wait_time_mins": 11.4,
        "amount_note": "Current Account Signatory Addition",
        "today_served": 20,
        "aht_mins": 9.5,
        "csat_score": 4.82,
        "queue_depth": 3,
        "deflectable": False,
        "deflection_channel": "In-Person Specialist Required",
        "upcoming_queue": [
            {"token": "TKN-1198", "name": "Green Leaf Organics", "service": "Merchant POS Terminal Onboarding", "wait": "10.0 min", "segment": "Small Business / SME"},
            {"token": "TKN-1204", "name": "TechCraft Solutions", "service": "Corporate NetBanking Token", "wait": "18.5 min", "segment": "Small Business / SME"}
        ]
    },
    {
        "counter_num": 10,
        "desk_name": "Counter 10 — General Inquiries & Escrow Desk",
        "service": "Passbook / Statement Printing",
        "staff_name": "James O'Connor",
        "staff_role": "Operations Floater & Triage",
        "active_token": "TKN-1205",
        "customer_name": "Victor Rossi",
        "customer_segment": "Regular",
        "service_timer": "01:50",
        "wait_time_mins": 2.5,
        "amount_note": "Annual Interest Certificate & Tax Statement",
        "today_served": 44,
        "aht_mins": 3.2,
        "csat_score": 4.90,
        "queue_depth": 1,
        "deflectable": True,
        "deflection_channel": "NetBanking / Email Statement",
        "upcoming_queue": [
            {"token": "TKN-1210", "name": "Hannah Abbott", "service": "Cheque Book Request", "wait": "3.0 min", "segment": "Regular"}
        ]
    }
]

def get_counter_profiles(total_counters: int = 10) -> list:
    """Returns unique sample configuration & live operational state for each counter."""
    profiles = []
    for i in range(1, total_counters + 1):
        idx = (i - 1) % len(COUNTER_TEMPLATES)
        item = dict(COUNTER_TEMPLATES[idx])
        item["counter_id"] = f"Counter {i}"
        item["counter_num"] = i
        profiles.append(item)
    return profiles

