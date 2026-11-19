# PRODUCTION DEPLOYMENT & OPERATION GUIDE

---

## 1. Local Development Setup

### Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/VenkataMadhuSudan/bank-branch-optimizer.git
cd bank-branch-optimizer

# Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Configure your Neon PostgreSQL URL in `.env`:
```ini
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<ep-hostname>.us-east-2.aws.neon.tech/<dbname>?sslmode=require
SECRET_KEY=your-secure-random-32-byte-hex-secret
APP_ENV=development
```
*(If `DATABASE_URL` is left empty, the application will automatically fall back to local SQLite at `data/bank_optimizer.db`)*

### Database Initialization & Seed
```bash
python db/seed.py
```

### Starting the Applications
- **FastAPI Backend (Port 8000):**
  ```bash
  python server.py
  # Or with uvicorn directly:
  uvicorn server:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Streamlit Operations Cockpit (Port 8501):**
  ```bash
  streamlit run app.py --server.port 8501
  ```

---

## 2. Docker & Container Deployment

### Build and Run with Docker Compose
```bash
docker-compose up --build -d
```
Access the application at `http://localhost:8501` and FastAPI docs at `http://localhost:8000/docs`.
