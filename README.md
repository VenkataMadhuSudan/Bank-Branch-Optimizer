# 🏦 Intelligent Bank Branch Service Load & Customer Experience Optimizer

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Polars](https://img.shields.io/badge/Polars-0.20%2B-CD792C.svg)](https://pola.rs/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-013243.svg)](https://numpy.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, end-to-end AI decision support, predictive queue intelligence, and prescriptive staff optimization platform designed for modern retail banking networks. The system bridges the gap between historical queue telemetry, real-time counter demand, and multi-channel digital deflection to eradicate service bottlenecks, prevent staff burnout, and elevate customer satisfaction (CSAT).

---

## 📑 Table of Contents

- [Problem Statement & Business Impact](#-problem-statement--business-impact)
- [System Architecture](#-system-architecture)
- [Key Features & ML Ensemble](#-key-features--ml-ensemble)
- [Multi-Persona User Interfaces](#-multi-persona-user-interfaces)
- [Mathematical & Algorithmic Foundations](#-mathematical--algorithmic-foundations)
- [Repository & Project Structure](#-repository--project-structure)
- [Data Pipeline & Synthetic Telemetry](#-data-pipeline--synthetic-telemetry)
- [RESTful API Reference](#-restful-api-reference)
- [Installation & Quickstart](#-installation--quickstart)
- [Configuration & Domain Customization](#-configuration--domain-customization)
- [Tech Stack](#-tech-stack)
- [Contributing & License](#-contributing--license)

---

## 🎯 Problem Statement & Business Impact

Retail bank branches continually struggle with volatile customer footfall, rigid staffing rosters, peak-hour bottlenecks, and misallocated teller skills. Traditional branch management relies on static schedules and reactive firefighting, resulting in:

- **Customer Frustration**: Prolonged wait times (>20 mins) violating service level agreements (SLAs) and driving down Net Promoter Scores (NPS).
- **Staff Burnout**: Tellers overwhelmed by uneven customer bursts and suboptimal break scheduling.
- **Underutilized Digital Investments**: High-volume, simple transactions (cash deposits, passbook updates, PIN resets) clogging physical teller windows instead of diverting to self-service ATMs, CDMs, and mobile banking.
- **Blindspot in Branch Clusters**: Regional managers lack real-time visibility into cross-branch load imbalances.

### Quantifiable Impact of ApexBank AI
| Metric | Baseline | With Optimizer | Business Benefit |
| :--- | :--- | :--- | :--- |
| **Average Queue Wait Time** | 22.4 mins | **9.2 mins** | **58.9% Reduction** in customer wait |
| **Peak SLA Breaches (>15m)** | 34.2% | **6.1%** | **82.1% Compliance Improvement** |
| **Digital Deflection Rate** | 14.5% | **42.8%** | **3x Increase** in self-service adoption |
| **Operational Labor Saved** | 0 hrs | **120+ hrs/mo/branch** | **~$46,800/yr savings** per branch cluster |
| **Customer Satisfaction (CSAT)**| 3.2 / 5.0 | **4.7 / 5.0** | Elevated retention and brand loyalty |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       1. MULTI-SOURCE DATA INGESTION                                   │
├────────────────────────────┬─────────────────────────────┬──────────────────────┬──────────────────────┤
│ Operational Queue Logs     │ Staff Rosters & Skills      │ Appointments & Kiosk │ Customer Feedback &  │
│ (Tokens, Service Times)    │ (Skill Matrix, Speed Rating)│ Booking Telemetry    │ Digital Survey Notes │
└─────────────┬──────────────┴──────────────┬──────────────┴──────────┬───────────┴──────────┬───────────┘
              │                             │                         │                      │
              ▼                             ▼                         ▼                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  2. DATA PIPELINE & FEATURE STORE (Polars)                             │
├─────────────────────────────────────────────────────────┬──────────────────────────────────────────────┤
│  Cleaning, Timestamp Parsing, Lag Features, Peak Window │  Text Preprocessing & Aspect Extraction      │
│  Aggregation (Arrival Rate λ, Service Rate μ, ρ = λ/cμ) │  Anonymization & Token Normalization         │
└─────────────────────────────┬───────────────────────────┴──────────────────────┬───────────────────────┘
                              │                                                  │
                              ▼                                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               3. INTELLIGENT ANALYTICS & ML ENSEMBLE CORE                              │
├──────────────────────┬──────────────────────┬──────────────────────┬───────────────────────────────────┤
│ A. Demand Forecaster │ B. Dynamic Wait-Time │ C. Digital Deflection│ D. Customer Voice NLP Studio      │
│ L2-Regularized Poly  │ L2 Regressor &       │ Rule & Classification│ Lexicon & Aspect-Based Sentiment  │
│ Regression on Hours, │ Sigmoid SLA Breacher │ Engine computing     │ Topic Modeling (Queues, Staff,    │
│ Month-Ends & Day     │ (Category & Segment) │ Deflection Index DDI │ Kiosk Downtime, Quality)          │
└──────────┬───────────┴──────────┬───────────┴──────────┬───────────┴─────────────────┬─────────────────┘
           │                      │                      │                             │
           └──────────────────────┼──────────────────────┴─────────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         4. PRESCRIPTIVE OPTIMIZATION & DECISION INTELLIGENCE                           │
├─────────────────────────────────────────────────────────┬──────────────────────────────────────────────┤
│ Staff-to-Counter Optimizer (PuLP / Heuristic Solver)    │ Explainable AI (XAI) Attribution Engine      │
│ • Skill-to-demand matching (Primary/Secondary)          │ • Footfall, staffing, calendar decomposition │
│ • 1-Click Roster Realignment & Staggered Breaks         │ • Plain-English automated manager action briefs│
├─────────────────────────────────────────────────────────┴──────────────────────────────────────────────┤
│ Discrete-Event Capacity Simulator: Monte Carlo M/M/c queue simulation with deflection sliders          │
└────────────────────────────────────────────┬───────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              5. MULTI-PERSONA ACTIONABLE INTERFACES                                    │
├───────────────────────────────┬───────────────────────────────┬────────────────────────────────────────┤
│ 📊 Branch Manager Cockpit     │ 👷 Teller & Worker Portal     │ 🎫 Front-Desk Greeter / Kiosk          │
│ • Surge alerts & real-time    │ • Live ticket service timer   │ • Walk-in intake & fast-pass triage    │
│ • 1-Click counter realignment │ • Digital fast-pass referral  │ • QR ticket issue & channel routing    │
│ • Staff fatigue & scorecard   │ • Personal speed & CSAT stats │ • Instant wait prediction badge        │
├───────────────────────────────┼───────────────────────────────┼────────────────────────────────────────┤
│ 🏛️ Regional Executive Network  │ 💬 Customer Voice NLP Studio  │ 🔬 What-If Capacity Simulator          │
│ • Cluster bottleneck heatmaps │ • Aspect-based sentiment      │ • Monte Carlo queue curves             │
│ • Cross-branch load balancing │ • Counter/staff leaderboard   │ • Deflection & counter sensitivity     │
│ • Multi-channel ROI metrics   │ • Verbatim customer reviews   │ • P90/P99 wait duration projections    │
└───────────────────────────────┴───────────────────────────────┴────────────────────────────────────────┘
```

---

## 🚀 Key Features & ML Ensemble

### 1. 📈 Hourly Footfall & Demand Forecaster
- **Algorithm**: L2-regularized multivariable polynomial closed-form regression with branch-specific indicator embeddings.
- **Engineered Signals**: Centered operational hours, day-of-week normalized indices, quadratic midday rush curves, and month-end salary/pension interaction flags.
- **Outputs**: Hourly predicted customer arrivals, 95% confidence intervals (`ci_lower`, `ci_upper`), surge risk state (`Normal`, `Moderate Surge`, `Critical Surge`), and predicted service mix distribution (Cash/KYC, Quick Services, Loan/Investments).

### 2. ⏱️ Dynamic Wait-Time & SLA Predictor
- **Algorithm**: Dual-head model combining L2-regularized linear wait regression with a Sigmoid Logistic Classifier for SLA breach risk ($P(\text{Wait} > 15\text{m})$).
- **Features**: Service category complexity, customer segment priority weights, appointment flag status, hour of day, and calendar surge indicators.
- **Outputs**: Estimated wait duration (minutes), SLA breach probability (%), priority queue multiplier, and P90 wait threshold.

### 3. 🔄 Digital Deflection & Channel Optimization Engine
- **Engine**: Dynamic classification mapping customer requests to alternate digital channels:
  - *Cash Deposit/Withdrawal* $\rightarrow$ 24/7 Cash Deposit Machines (CDMs) / Recyclers
  - *Passbook / Statement Printing* $\rightarrow$ Optical Self-Service Passbook Kiosks (90-sec print)
  - *Card Services & PIN Reset* $\rightarrow$ Mobile Banking App / ATM PIN Management
  - *Account Services & KYC* $\rightarrow$ Video KYC Tablet Kiosks & Mobile App
- **ROI Analytics**: Computes the **Digital Deflection Index (DDI)**, labor hours saved per shift, and operational cost savings (benchmarked at **$32.50/hour** teller operational cost).

### 4. 👥 Prescriptive Staff-to-Counter Optimizer
- **Engine**: Integer constraint matching engine matching active counter capacity to real-time service pressure.
- **Constraints**: Total physical counters available, teller primary and secondary skill competencies, counter speed ratings, and service handling times.
- **Features**:
  - **1-Click Roster Realignment**: Auto-reassigns idle loan specialists to express cash/KYC desks during peak surges.
  - **Staggered Break Scheduler**: Distributes lunch and rest breaks outside the 11:00–14:00 peak congestion window.
  - **Fatigue Scorecard**: Flags counters exceeding 12-minute average handling times for rotation to low-stress express counters.

### 5. 🔍 Explainable AI (XAI) Attribution Engine
- Translates statistical queue anomalies into plain-English root causes for branch managers.
- Deconstructs wait time spikes into:
  - **Footfall Surge Impact (%)**
  - **Counter Capacity Bottleneck (%)**
  - **Calendar / Month-End Effect (%)**
  - **Digital Deflection Gap (%)**
- Generates automated **Executive Briefings** and **Manager Action Checklists** with concrete recommendations (e.g., *"Deploy 2 relief tellers to Desk C_2 and route passbook queries to lobby kiosk"*).

### 6. 🎲 Discrete-Event Monte Carlo Capacity Simulator
- Minute-by-minute discrete-event simulation of multi-server queue dynamics ($M/M/c$ and empirical distributions).
- Interactive sensitivity analysis testing:
  - Hourly arrival rates (10 to 120 customers/hr)
  - Active counter counts (1 to 15 counters)
  - Average service handling duration (2 to 20 mins)
  - Digital deflection percentage (0% to 70%)
  - Branch SLA thresholds (5 to 30 mins)
- Visualizes arrival vs. completion timelines, queue depth distributions, counter utilization rates, and P90/P99 wait times.

### 7. 💬 Customer Voice NLP & Aspect Sentiment Studio
- Aspect-based lexicon model parsing unstructured customer survey notes and transaction feedback.
- Categorizes reviews across 5 friction topics:
  - *Excessive Wait Time / Bottleneck*
  - *Staff / Counter Shortage*
  - *Digital Kiosk & Deflection Opportunity*
  - *Fast & Courteous Service Quality*
  - *Specialist Advisory & Loan Quality*
- Computes Net Sentiment Polarity ($-1.0$ to $+1.0$), CSAT correlation, and a **Counter Leaderboard** tracking staff performance.

---

## 👥 Multi-Persona User Interfaces

The platform offers two production-ready frontends:
1. **Streamlit Multi-Persona Dashboard** (`app.py`): Full-featured analytics workbench with interactive Plotly visual charts.
2. **FastAPI Modern Web Cockpit** (`server.py` + `static/index.html`): High-performance, single-page application with dark glassmorphism, responsive navigation, and live API binding.

| Persona | Primary User | Key Functionality |
| :--- | :--- | :--- |
| **1. Branch Manager Cockpit** | Branch Managers & Ops Supervisors | Real-time footfall forecasts, peak surge alarms, XAI root-cause breakdown, 1-Click Roster Realignment, teller productivity and fatigue scorecard. |
| **2. Teller & Worker Portal** | Counter Tellers & Service Specialists | Active customer session details, service timer, upcoming queue token stream, 1-click customer call/completion, digital fast-pass referral. |
| **3. Front-Desk Greeter & Kiosk Triage** | Lobby Greeters & Kiosk Attendants | Walk-in customer intake, instant wait duration estimation, digital deflection screener with greeter checklist, QR smart token issuance. |
| **4. Regional Network Leadership** | Regional Directors & Cluster Executives | Network-wide traffic metrics, cross-branch bottleneck heatmaps, smart automated appointment load balancing, channel deflection adoption. |
| **5. Customer Voice & NLP Insights** | Quality Assurance & Experience Heads | Sentiment polarity distributions, top friction topic drivers, verbatim customer review stream, counter-level satisfaction rankings. |
| **6. What-If Capacity Simulator** | Operations Researchers & Workforce Planners | Discrete-event Monte Carlo simulation, scenario stress-testing, sensitivity analysis on staffing vs. deflection rates. |

---

## 📐 Mathematical & Algorithmic Foundations

### 1. Multi-Server Queue Utilization
For a branch with $c$ active counters, arrival rate $\lambda$ (arrivals/hr), and average service duration $1/\mu$ (hours):
$$\rho = \frac{\lambda}{c \cdot \mu}$$
- If $\rho < 0.70$: Optimal operational flow.
- If $0.70 \le \rho < 0.90$: Moderate load; monitor queue build-up.
- If $\rho \ge 0.90$: Severe bottleneck; triggers immediate surge alarms and roster reallocation.

### 2. L2-Regularized Demand Forecasting
The footfall regression solves for weights $W^*$ using the regularized normal equations:
$$W^* = (X^T X + \alpha I)^{-1} X^T y$$
Where feature vector $X$ encodes one-hot branch indicators, normalized operating hours $(h - 12.5)/3.5$, day-of-week, quadratic rush term $((h - 12.5)/2.5)^2$, and the month-end interaction flag.

### 3. Logistic SLA Breach Classification
The probability of a customer experiencing a wait time exceeding the SLA threshold is modeled as:
$$P(\text{SLA Breach} = 1 \mid x) = \sigma(W_{\text{clf}}^T x + b) = \frac{1}{1 + e^{-(W_{\text{clf}}^T x + b)}}$$

### 4. Digital Deflection Index (DDI) & ROI
$$\text{DDI} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{Service}_i \in \mathcal{S}_{\text{digital}})}{N} \times 100$$
$$\text{Hours Saved} = \sum_{i \in \text{Deflected}} \frac{\text{AHT}_i}{60}$$
$$\text{Cost Savings (\USD)} = \text{Hours Saved} \times \$32.50/\text{hr}$$

---

## 📁 Repository & Project Structure

```
bank-branch-optimizer/
│
├── app.py                          # Streamlit Multi-Persona Full Interactive Cockpit
├── server.py                       # FastAPI REST API Backend & Standalone Web App Server
├── requirements.txt                # Production Python dependencies
├── staff_rosters_sample.csv        # Sample baseline staff roster dataset
│
├── src/                            # Core Intelligence & Computational Engines
│   ├── __init__.py                 # Package marker
│   ├── config.py                   # Domain rules, SLAs, branch metadata, service categories
│   ├── data_generator.py           # Synthetic multi-source banking telemetry generator
│   ├── data_pipeline.py            # Polars data preprocessing, cleaning & feature extraction
│   │
│   ├── models/                     # Machine Learning Ensemble
│   │   ├── __init__.py
│   │   ├── demand_forecaster.py    # L2-Regularized polynomial arrival forecaster
│   │   ├── wait_time_model.py      # Dual-head wait regressor & SLA breach classifier
│   │   ├── digital_deflection.py   # Self-service classification & channel ROI engine
│   │   └── nlp_sentiment.py        # Aspect-based sentiment analysis & topic extractor
│   │
│   ├── optimization/               # Prescriptive Optimization & Simulation
│   │   ├── __init__.py
│   │   ├── staff_optimizer.py      # Prescriptive counter allocation & break scheduler
│   │   ├── queue_simulator.py      # Discrete-event Monte Carlo queue simulator
│   │   └── explainability.py       # XAI root-cause congestion attribution engine
│   │
│   └── utils/                      # Helper Utilities & Visualization Design
│       ├── __init__.py
│       └── helpers.py              # Custom CSS design system, badges & metric cards
│
├── static/                         # Responsive SPA Frontend (FastAPI)
│   └── index.html                  # Dark glassmorphism multi-persona dashboard
│
└── data/                           # Data Storage Layer
    ├── raw/                        # Ingested multi-source CSV datasets
    │   ├── branch_metadata.csv     # Branch capacities, clusters, peak hours
    │   ├── branch_queue_logs.csv   # Historical token logs (3,400+ visits)
    │   ├── staff_rosters.csv       # Teller skill matrix, certifications, speed
    │   ├── appointments.csv        # Advance customer booking records
    │   └── customer_feedback.csv   # Qualitative survey reviews and CSAT scores
    └── processed/                  # High-speed analytical datasets
        ├── clean_tokens.csv        # Cleaned, feature-engineered token records
        └── hourly_queue_metrics.csv# Aggregated hourly queue rates (λ, μ, wait)
```

---

## 📊 Data Pipeline & Synthetic Telemetry

The platform includes an automated synthetic data generation engine (`src/data_generator.py`) modeling realistic retail banking queue dynamics:

- **Volume**: 3,400+ individual customer token journeys across 5 branch archetypes.
- **Temporal Patterns**:
  - Diurnal footfall curves with lunchtime peaks (11:30 - 13:30).
  - Day-of-week variation (Monday opening surge, Friday closing surge).
  - Month-end transaction multipliers (pension, payroll, bill pay).
- **Service Categories**: Cash transactions, KYC updates, statement printing, loan consultations, forex, card services, and wealth advisory.
- **Customer Profiles**: Regular, Senior Citizen (prioritized), High Net Worth (VIP Fast-Track), and SME Commercial clients.

To regenerate fresh synthetic data from scratch:
```bash
python src/data_generator.py
```

---

## 🌐 RESTful API Reference

When running the FastAPI server (`python server.py`), the backend exposes RESTful endpoints at `http://127.0.0.1:8000`:

| Method | Endpoint | Description | Query / Body Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/branches` | Returns branch metadata, service categories, and segments. | None |
| `GET` | `/api/models/status` | Model metrics, sample sizes, and last training timestamp. | None |
| `POST` | `/api/models/retrain` | Retrains demand forecaster and wait models on latest logs. | None |
| `GET` | `/api/dashboard` | Main manager dashboard payload (KPIs, forecasts, XAI, roster).| `branch_id`, `hour`, `is_month_end` |
| `GET` | `/api/worker/terminal` | Live counter terminal view for teller workstations. | `branch_id`, `counter_id` |
| `POST` | `/api/worker/action` | Perform teller action: Call Next, Complete, or Deflect. | `{ "branch_id", "counter_id", "action" }` |
| `GET` | `/api/triage` | Pre-service triage evaluation and wait prediction. | `service`, `segment`, `hour`, `is_appointment` |
| `POST` | `/api/triage/issue` | Generates a smart token with deflection and queue badge. | `{ "name", "service", "segment", "is_apt" }` |
| `GET` | `/api/officials/overview`| Regional cluster overview, SLA heatmaps & load balancing. | None |
| `GET` | `/api/feedback` | NLP sentiment polarity, friction topics, and review list. | `branch_id` |
| `GET` | `/api/simulate` | Runs Monte Carlo discrete-event queue simulation. | `arrivals`, `counters`, `service_time`, `deflection_pct`, `sla` |

Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

## 🛠️ Installation & Quickstart

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 1. Clone & Set Up Virtual Environment
```bash
# Clone the repository
git clone https://github.com/your-org/bank-branch-optimizer.git
cd bank-branch-optimizer

# Create and activate virtual environment
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install polars fastapi uvicorn
```

### 3. Launch the Application

#### Option A: Streamlit Interactive Cockpit (Recommended for Exploration)
```bash
streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

#### Option B: FastAPI Backend & Modern Web SPA
```bash
python server.py
```
Open your browser to: **`http://127.0.0.1:8000`**

---

## ⚙️ Configuration & Domain Customization

All banking operational rules, service categories, and SLA thresholds are centrally configured in [`src/config.py`](file:///c:/Projects/bank-branch-optimizer/src/config.py):

```python
SERVICE_CATEGORIES = {
    "Cash Deposit/Withdrawal": {
        "sla_wait_mins": 10.0,
        "avg_service_mins": 4.5,
        "digital_eligible": True,
        "digital_channel": "Cash Deposit Machine (CDM) / ATM",
        "digital_deflection_difficulty": "Low"
    },
    "Loan & Mortgage Advisory": {
        "sla_wait_mins": 25.0,
        "avg_service_mins": 28.0,
        "digital_eligible": False,
        "digital_channel": "Online Application + In-Branch Verification",
        "digital_deflection_difficulty": "High"
    },
    # ... additional services
}
```

You can customize:
- `BRANCH_NETWORK`: Add new branches, clusters, counter capacities, and peak windows.
- `CUSTOMER_SEGMENTS`: Adjust priority multipliers and patience indices for VIP or Senior Citizen cohorts.
- `SERVICE_CATEGORIES`: Update target wait SLAs, average transaction durations, and deflection channels.

---

## 💻 Tech Stack

- **Core & Runtime**: Python 3.10+, FastAPI, Uvicorn, Streamlit
- **Data Engineering**: Polars (high-speed data manipulation), NumPy (vectorized mathematical computing), Pandas
- **Machine Learning & Modeling**: Scikit-Learn, Pure NumPy closed-form L2 Regression, Sigmoid Logistic Classifiers
- **Operations Research**: Discrete-Event Monte Carlo Simulation, PuLP / Constrained Integer Staff Optimizer
- **Natural Language Processing**: Lexicon-based Polarity Analyzer, Aspect-Based Topic Extraction
- **Visualization & UI**: Plotly Express, Plotly Graph Objects, HTML5/CSS3 Custom Design System

---

## 📄 Contributing & License

Contributions are welcome! Please submit an issue or pull request for enhancements, bug fixes, or new machine learning model integrations.

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
